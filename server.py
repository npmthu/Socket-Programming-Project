import socket
import threading
import os
import logging
import json
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import sys
import hashlib
import struct
import secrets
import signal
import time
import queue

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import application_message

# Constants for file transfer
CHUNK_SIZE = 4096  # 4 KB chunks
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1 GB max file size
DEFAULT_SAVE_PATH = 'server_files/'

log_lock = threading.Lock()
file_lock = threading.Lock()
folder_lock = threading.Lock()

data_lock = threading.Lock()


def random_pin():
    return secrets.randbelow(90000000) + 10000000

def receive_message(client_socket):
    """
    Receives a complete message containing both header and payload.
    Ensures the message has at least the header size and validates that
    the payload length matches the value specified in the header.
    """
    try:
        # Receive the header data
        header_data = client_socket.recv(application_message.Message.HEADER_SIZE)
        if not header_data or len(header_data) < application_message.Message.HEADER_SIZE:
            raise ConnectionResetError("Incomplete or missing header received.")

        # Unpack the header
        msg_type, action_code, status_code, payload_length = struct.unpack(
            application_message.Message.HEADER_FORMAT, header_data
        )

        # Receive the payload based on the payload_length specified in the header
        payload = b""
        while len(payload) < payload_length:
            chunk = client_socket.recv(payload_length - len(payload))
            if not chunk:  # If no data is received, the connection might be closed
                raise ValueError("Connection closed before receiving full payload.")
            payload += chunk

        # If the payload length is still mismatched after receiving, raise an error
        if len(payload) != payload_length:
            raise ValueError(f"Payload length mismatch. Expected {payload_length}, got {len(payload)}.")

        # Attempt to decode the payload as a UTF-8 string for JSON metadata
        try:
            decoded_payload = payload.decode('utf-8')  # Try to decode as UTF-8 string
            
            # Try to parse it as JSON (metadata)
            try:
                payload_data = json.loads(decoded_payload)  # Expecting JSON data (metadata)
            except json.JSONDecodeError:
                # If JSON decoding fails, treat it as binary (file data)
                payload_data = payload  # Raw binary data (file content)
        except UnicodeDecodeError:
            # If decoding as UTF-8 fails, treat as binary data (file content)
            payload_data = payload  # Raw binary data (file content)

        # Combine header and payload into one message
        full_message = header_data + payload

        # Return the Message object with either JSON or raw binary data
        return application_message.Message.from_bytes(full_message)

    except (ConnectionResetError, BrokenPipeError) as e:
        raise ConnectionResetError(f"Connection error while receiving message: {e}")
    except Exception as e:
        raise ValueError(f"Error receiving message: {e}")

def calculate_file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def receive_file(client_socket, action_msg):
    try:
        # Receive metadata message
        metadata_msg = action_msg
        # Decode the payload from bytes to a UTF-8 string
        decoded_payload = metadata_msg.payload.decode('utf-8')
        decoded_payload = decoded_payload.replace("'", '"')
        file_metadata = json.loads(decoded_payload)

        filename = file_metadata.get('filename', 'unknown_file')
        filesize = file_metadata.get('filesize', 0)
        save_path = file_metadata.get('save_path', '')
        expected_hash = file_metadata.get('hash', '')

        # Validate file size
        if filesize > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum limit: {filesize} bytes")
        
        with file_lock:
            # Prepare the full file path including the filename
            filepath = os.path.join(DEFAULT_SAVE_PATH, save_path, filename)
            # Ensure the directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            # Check if the file exists and modify the filename if needed
            if os.path.exists(filepath):
                base, ext = os.path.splitext(filename)
                timestamp = int(datetime.now().timestamp())
                filename = f"{base}_{timestamp}{ext}"
                filepath = os.path.join(DEFAULT_SAVE_PATH, save_path, filename)
        
            # Receive file in chunks
            with open(filepath, 'wb') as file:
                bytes_received = 0
                file_hash = hashlib.sha256()
                while bytes_received < filesize:
                    chunk_msg = receive_message(client_socket)
                    # Write chunk and update hash
                    file.write(chunk_msg.payload)
                    file_hash.update(chunk_msg.payload)
                    bytes_received += len(chunk_msg.payload)

            # Verify file integrity
            received_hash = file_hash.hexdigest()
            if received_hash != expected_hash:
                os.remove(filepath)
                raise ValueError("File transfer corrupted: Hash mismatch")
        
        with log_lock:
            logging.info(f"File {filename} received successfully. Size: {bytes_received} bytes")

        # Send success message
        success_msg = application_message.Message(
        msg_type=application_message.MessageType.RESPONSE.value,
        action_code=application_message.ActionCode.UPLOAD.value,
        status_code=application_message.StatusCode.SUCCESS.value,
        payload=json.dumps({
            'filename': filename,
            'filesize': bytes_received,
            'hash': received_hash
        }).encode('utf-8')
        )
        client_socket.sendall(success_msg.to_bytes())
        return filename
    
    except Exception as e:
        with log_lock:
            logging.error(f"Error receiving file: {e}")
        error_msg = application_message.Message(
            msg_type=application_message.MessageType.RESPONSE.value,
            action_code=application_message.ActionCode.UPLOAD.value,
            status_code=application_message.StatusCode.ERROR.value,
            payload=str(e).encode()
        )
        client_socket.sendall(error_msg.to_bytes())
        return None
    
def send_file(client_socket, filepath):
    try:
        with file_lock:
            # Check if the file exists
            if not os.path.isfile(filepath):
                raise FileNotFoundError("File not found")
            # Calculate file metadata
            filesize = os.path.getsize(filepath)
            filename = os.path.basename(filepath)
            file_hash = calculate_file_hash(filepath)

        # Send file metadata
        metadata = {
            'filename': filename,
            'filesize': filesize,
            'hash': file_hash
        }
        metadata_msg = application_message.Message(
            msg_type=application_message.MessageType.RESPONSE.value,
            action_code=application_message.ActionCode.DOWNLOAD.value,
            status_code=application_message.StatusCode.SUCCESS.value,
            payload=json.dumps(metadata).encode()
        )
        client_socket.sendall(metadata_msg.to_bytes())

        with file_lock:
            # Send file in chunks
            with open(filepath, 'rb') as file:
                while chunk := file.read(CHUNK_SIZE):
                    try:
                        chunk_msg = application_message.Message(
                            msg_type=application_message.MessageType.RESPONSE.value,
                            action_code=application_message.ActionCode.DOWNLOAD.value,
                            status_code=application_message.StatusCode.SUCCESS.value,
                            payload=chunk
                        )
                        client_socket.sendall(chunk_msg.to_bytes())
                    except (BrokenPipeError, ConnectionResetError):
                        raise ConnectionResetError("Connection lost while sending file.")

        with log_lock:
            logging.info(f"File {filename} sent successfully. Size: {filesize} bytes")
        return True
    
    except (ConnectionResetError, BrokenPipeError) as e:
        with log_lock:
            logging.error(f"Connection error while sending file: {e}")
        return False
    
    except Exception as e:
        with log_lock:
            logging.error(f"Error sending file: {e}")
        error_msg = application_message.Message(
            msg_type=application_message.MessageType.RESPONSE.value, 
            action_code=application_message.ActionCode.DOWNLOAD.value, 
            status_code=application_message.StatusCode.ERROR.value, 
            payload=str(e).encode()
        )
        client_socket.sendall(error_msg.to_bytes())
        return False
    
def authenticate_user(pin):
    # This is a simple authentication; modify for production use (e.g., a database)
    correct_pin = 1234  # Replace with a secure method for actual use
    return int(pin) == correct_pin

def list_files_in_directory(directory):
    with data_lock:
        try: 
            """Create a dictionary structure representing the folder hierarchy."""
            folder_structure = {}
            for root, dirs, filenames in os.walk(directory):
                # Calculate relative path from the given folder path
                relative_path = os.path.relpath(root, directory)
                path_parts = relative_path.split(os.sep)

                # Navigate into the nested structure and build the dictionary
                current_dict = folder_structure
                for part in path_parts:
                    if part != '.':
                        if part not in current_dict:
                            current_dict[part] = {}
                        current_dict = current_dict[part]

                # Add files to the current dictionary
                for filename in filenames:
                    current_dict[filename] = None

            return folder_structure
        
        except Exception as e:
            with log_lock:  # Log any errors in a thread-safe manner
                logging.error(f"Error listing files in directory '{directory}': {e}")
            raise

def handle_client(client_socket):
    try:
        # Server operations: upload, download, list files
        while True:
            try:
                # Receive action message
                action_msg = receive_message(client_socket)
                if action_msg.action_code == application_message.ActionCode.LOGIN.value:
                    pin = action_msg.payload.decode()

                    if not authenticate_user(pin):
                        # Send authentication failure message
                        response_msg = application_message.Message(
                            msg_type=application_message.MessageType.RESPONSE.value, 
                            action_code=application_message.ActionCode.LOGIN.value, 
                            status_code=application_message.StatusCode.ERROR.value, 
                            payload=b"Authentication failed"
                        )
                        client_socket.send(response_msg.to_bytes())
                        return
                    # Send authentication success message
                    response_msg = application_message.Message(
                        msg_type=application_message.MessageType.RESPONSE.value, 
                        action_code=application_message.ActionCode.LOGIN.value, 
                        status_code=application_message.StatusCode.SUCCESS.value, 
                        payload=b"Authentication successful"
                    )
                    client_socket.send(response_msg.to_bytes())

                elif action_msg.action_code == application_message.ActionCode.UPLOAD_FOLDER.value:
                    # Decode the payload from bytes to a UTF-8 string
                    decoded_payload = action_msg.payload.decode('utf-8')
                    decoded_payload = decoded_payload.replace("'", '"')
                    folder_metadata = json.loads(decoded_payload)
                    foldername = folder_metadata.get('foldername', '')
                    save_path = folder_metadata.get('save_path', '')
                    save_path = os.path.join(DEFAULT_SAVE_PATH, save_path)

                    with folder_lock:
                        # Full path of folder
                        folder_path = os.path.join(save_path, foldername)
                        # check if folder exists
                        if os.path.exists(folder_path):
                            # If it exists, create a new folder name with timestamp
                            timestamp = int(datetime.now().timestamp())
                            foldername = f"{foldername}_{timestamp}"

                    # Send response to client
                    response_msg = application_message.Message(
                    msg_type=application_message.MessageType.RESPONSE.value,
                    action_code=application_message.ActionCode.UPLOAD_FOLDER.value,
                    status_code=application_message.StatusCode.SUCCESS.value,
                    payload=json.dumps({
                        'foldername': foldername 
                    }).encode('utf-8')
                    )
                    client_socket.sendall(response_msg.to_bytes())

                elif action_msg.action_code == application_message.ActionCode.UPLOAD.value:
                    receive_file(client_socket, action_msg)  

                elif action_msg.action_code == application_message.ActionCode.DOWNLOAD.value:
                    # Receive file to download
                    file_msg = action_msg
                    file_to_send = file_msg.payload.decode()
                    filepath = os.path.join(DEFAULT_SAVE_PATH, file_to_send)
                    send_file(client_socket, filepath)

                elif action_msg.action_code == application_message.ActionCode.LIST_FILES.value:
                    # List all files in the server directory
                    directory = action_msg.payload.decode('utf-8')
                    if(directory == ''):
                        directory = DEFAULT_SAVE_PATH
                    else:
                        directory = os.path.join(DEFAULT_SAVE_PATH, directory)
                    files = list_files_in_directory(directory)
                    files_msg = application_message.Message(
                        msg_type=application_message.MessageType.RESPONSE.value, 
                    action_code=application_message.ActionCode.LIST_FILES.value, 
                    status_code=application_message.StatusCode.SUCCESS.value, 
                    payload=json.dumps(files).encode('utf-8')
                    )   
                    client_socket.sendall(files_msg.to_bytes())

                else:
                    # Send invalid command message
                    invalid_msg = application_message.Message(
                        msg_type=application_message.MessageType.RESPONSE.value, 
                        action_code=action_msg.action_code, 
                        status_code=application_message.StatusCode.ERROR.value, 
                        payload=b"Invalid command"
                    )
                    client_socket.send(invalid_msg.to_bytes())

            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                with log_lock:
                    logging.error(f"Connection lost with client {client_socket.getpeername()}")
                break
            except Exception as e:
                with log_lock:
                    logging.error(f"Error with client {client_socket.getpeername()}: {e}")
                error_msg = application_message.Message(
                msg_type=application_message.MessageType.RESPONSE.value, 
                action_code=0,  # No specific action 
                status_code=application_message.StatusCode.ERROR.value, 
                payload=str(e).encode()
                )
                client_socket.send(error_msg.to_bytes())
                break
 
    finally:
        with log_lock:
            logging.info(f"Closing connection with client {client_socket.getpeername()}")
        client_socket.close()

def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)

    with log_lock:
        logging.info(f"Server started on {host}:{port} at {datetime.now()}")

    def signal_handler(signum, frame):
        with log_lock:
            logging.info("Server shutting down.")
        server_socket.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            with log_lock:
                logging.info(f"Connection from {client_address} at {datetime.now()}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()
    except Exception as e:
        with log_lock:
            logging.error(f"Server error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
    start_server('localhost', 6578) 