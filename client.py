import socket
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter import Tk, Canvas, Button
from PIL import Image, ImageTk, ImageDraw
from io import BytesIO

window_width = 1066
window_height = 600
BUFFER_SIZE = 4096


# ---------------------------- Shared Logic ---------------------------- #

from threading import Thread
import time
import hashlib
import struct
from threading import Event
import sys
import json

# Add the directory containing application_message.py to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import application_message
import upload_gui
# import temp_download_gui
import start_canvas

CHUNK_SIZE = 4096  # 4 KB chunks

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

def connect_to_server(host, port, retries=3, delay=5):
    """
    Establish a connection to the server with retries.
    Returns the socket if successful, otherwise None.
    """
    for attempt in range(retries):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
            return client_socket
        except ConnectionError as e:
            if attempt < retries - 1:
                print(f"Connection failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                messagebox.showerror("Connection Error", "Unable to connect to the server.")
                return None
    
def calculate_file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def authenticate_user(client_socket, pin):
    try:
        # Create authentication message
        auth_msg = application_message.Message(
            msg_type=application_message.MessageType.REQUEST,
            action_code=application_message.ActionCode.LOGIN,
            status_code=application_message.StatusCode.SUCCESS,
            payload=pin.encode()
        )
        client_socket.send(auth_msg.to_bytes())
        
        # Receive authentication response
        response_msg = application_message.Message.from_bytes(client_socket.recv(1024))
        
        if response_msg.status_code == application_message.StatusCode.SUCCESS:
            return True
        else:
            messagebox.showerror("Authentication Failed", 
                                  response_msg.payload.decode('utf-8', errors='replace'))
            return False
    except Exception as e:
        messagebox.showerror("Error", f"Authentication error: {e}")
        return False

def create_folder_structure(folder_path):
    folder_structure = {}
    for root, dirs, filenames in os.walk(folder_path):
        # Calculate relative path from the given folder path
        relative_path = os.path.relpath(root, folder_path)
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

def upload_folder_sequential(client_socket, folder_path, save_path):
    """
    Uploads all files in the given folder structure dictionary to the server.
    """
    #send mesage to server to check if folder exist on server or not
    foldername = os.path.basename(folder_path)
    # Prepare folder metadata
    metadata = {
        'foldername': foldername,
        'save_path' : save_path
    }
    # Send upload metadata
    metadata_msg = application_message.Message(
        msg_type=application_message.MessageType.REQUEST.value,
        action_code=application_message.ActionCode.UPLOAD_FOLDER.value,
        status_code=application_message.StatusCode.SUCCESS.value,
        payload=json.dumps(metadata).encode()
    )
    client_socket.sendall(metadata_msg.to_bytes())

    # Receive response
    try:
        response_msg = receive_message(client_socket)
        decoded_payload = response_msg.payload.decode('utf-8')
        decoded_payload = decoded_payload.replace("'", '"')
        folder_metadata = json.loads(decoded_payload)
        new_foldername = folder_metadata.get('foldername', '')
        if foldername != new_foldername:
            foldername = new_foldername
    except (ConnectionResetError, BrokenPipeError) as e:
        print(f"Connection lost during upload: {e}")
        return
    save_path = os.path.join(save_path, foldername)

    # Create the folder structure dictionary
    folder_structure = create_folder_structure(folder_path)
    # Helper function to process the folder structure recursively and upload files
    def process_folder_structure(current_structure, current_folder_path, current_save_path):
        for key, value in current_structure.items():
            if value is None:  # This is a file
                # Construct the full path to the file
                file_path = os.path.join(current_folder_path, key)
                upload_files(client_socket, [file_path], current_save_path)
            else:  # This is a subfolder                
                subfolder_path = os.path.join(current_folder_path, key)
                subfolder_save_path = os.path.join(current_save_path, key)
                process_folder_structure(value, subfolder_path, subfolder_save_path)
    # Start processing subfolders from the root of the folder structure
    process_folder_structure(folder_structure, folder_path, save_path)

def upload_files(client_socket, files, save_path):
    try:
        for file_path in files:
            # Validate file existence
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Calculate file metadata
            filesize = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            file_hash = calculate_file_hash(file_path)

            # Prepare file metadata
            metadata = {
                'filename': filename,
                'filesize': filesize,
                'save_path' : save_path,
                'hash': file_hash
            }

            # Send upload metadata
            metadata_msg = application_message.Message(
                msg_type=application_message.MessageType.REQUEST.value,
                action_code=application_message.ActionCode.UPLOAD.value,
                status_code=application_message.StatusCode.SUCCESS.value,
                payload=json.dumps(metadata).encode()
            )
            client_socket.sendall(metadata_msg.to_bytes())

            # Send file in chunks
            with open(file_path, 'rb') as file:
                while chunk := file.read(CHUNK_SIZE):
                    chunk_msg = application_message.Message(
                        msg_type=application_message.MessageType.REQUEST.value,
                        action_code=application_message.ActionCode.UPLOAD.value,
                        status_code=application_message.StatusCode.SUCCESS.value,
                        payload=chunk
                    )
                    client_socket.sendall(chunk_msg.to_bytes())

            # Receive upload success confirmation
            try:
                response_msg = receive_message(client_socket)
                if response_msg.status_code == application_message.StatusCode.SUCCESS.value:
                    upload_details = json.loads(response_msg.payload.decode())
                    print(f"Uploaded: {upload_details['filename']} (Size: {upload_details['filesize']} bytes)")
                else:
                    print(f"Upload failed for {filename}")
            except (ConnectionResetError, BrokenPipeError) as e:
                print(f"Connection lost during upload: {e}")
                return

    except Exception as e:
        print(f"Error uploading files: {e}")

def download_folder(client_socket, foldername, save_path=""):
    """
    Downloads all files in the specified folder from the server,
    using the `download_files` function for file downloads.

    Args:
        client_socket: The socket to communicate with the server.
        foldername: The name of the folder on the server to download.
        save_path: The local base path to save the downloaded files and folders.
    """
    try:
        # Retrieve the folder structure for the specified folder
        folder_structure = list_files(client_socket, foldername)

        # Create the local base path for the folder
        local_save_path = os.path.join(save_path, foldername)
        # Make new foldername if folder exits in save_path
        if os.path.exists(local_save_path) and os.path.isdir(local_save_path):
            timestamp = int(time.time())  
            new_foldername = f"{foldername}_{timestamp}"  
            local_save_path = os.path.join(save_path, new_foldername)
        os.makedirs(local_save_path, exist_ok=True)  # Ensure the base save path exists

        # Helper function to process the folder structure recursively
        def process_folder_structure(current_structure, current_save_path, parent_path=""):
            files_to_download = []  # Collect files for the current folder level

            for key, value in current_structure.items():
                if value is None:  # This is a file
                    # Append the file with its parent path relative to the server
                    relative_path = os.path.join(parent_path, key)
                    files_to_download.append(relative_path)
                else:  # This is a subfolder
                    subfolder_path = os.path.join(current_save_path, key)
                    os.makedirs(subfolder_path, exist_ok=True)  # Ensure the subfolder exists locally
                    # Recursively process the subfolder with updated parent path
                    process_folder_structure(value, subfolder_path, os.path.join(parent_path, key))

            # Download all files for the current folder
            if files_to_download:
                download_files(client_socket, files_to_download, save_path=current_save_path)

        # Start processing the folder's structure
        process_folder_structure(folder_structure, local_save_path, parent_path=foldername)
    except Exception as e:
        messagebox.showerror("Error", f"Error downloading folder '{foldername}': {e}")

def download_files(client_socket, files, save_path=""):
    """
    Downloads files from the server to the specified local path.

    Args:
        client_socket: The socket to communicate with the server.
        files: List of files to download from the server.
        save_path: The local path to save the downloaded files.
    """
    try:
        for filename in files:
            # Send download request with filename
            download_msg = application_message.Message(
                msg_type=application_message.MessageType.REQUEST.value,
                action_code=application_message.ActionCode.DOWNLOAD.value,
                status_code=application_message.StatusCode.SUCCESS.value,
                payload=filename.encode('utf-8')
            )
            client_socket.sendall(download_msg.to_bytes())

            # Receive file metadata
            try:
                metadata_msg = receive_message(client_socket)
                decoded_payload = metadata_msg.payload.decode('utf-8')
                file_metadata = json.loads(decoded_payload)
                filename = file_metadata.get('filename', 'downloaded_file')
                filesize = file_metadata.get('filesize', 0)
                expected_hash = file_metadata.get('hash', '')
            except (ConnectionResetError, BrokenPipeError) as e:
                print(f"Connection lost during upload: {e}")
                return

            # Prepare file for writing
            filepath = os.path.join(save_path, filename)
            file_hash = hashlib.sha256()

            with open(filepath, 'wb') as file:
                bytes_received = 0
                while bytes_received < filesize:
                    try:
                        chunk_msg = receive_message(client_socket)
                        file.write(chunk_msg.payload)
                        file_hash.update(chunk_msg.payload)
                        bytes_received += len(chunk_msg.payload)
                    except (ConnectionResetError, BrokenPipeError) as e:
                        print(f"Connection lost during upload: {e}")
                        os.remove(filepath)
                        return

            received_hash = file_hash.hexdigest()

            # Verify file integrity
            if received_hash != expected_hash:
                os.remove(filepath)
                raise ValueError(f"File '{filename}' download corrupted: Hash mismatch")

            print("Download Success",
                                f"File {filename} downloaded successfully.\n"
                                f"Size: {bytes_received} bytes")

    except Exception as e:
        messagebox.showerror("Download Error", f"Error downloading file: {e}")

def list_files(client_socket, directory=""):
    """
    Requests the list of files and folders from the server for a specified directory.

    Args:
        client_socket: The socket to communicate with the server.
        directory: The directory on the server to list files from.
    
    Returns:
        A dictionary representing the folder hierarchy.
    """
    try:
        # Send list files request
        list_msg = application_message.Message(
            msg_type=application_message.MessageType.REQUEST.value,
            action_code=application_message.ActionCode.LIST_FILES.value,
            status_code=application_message.StatusCode.SUCCESS.value,
            payload=directory.encode('utf-8')
        )
        client_socket.sendall(list_msg.to_bytes())

        # Receive file list
        try:
            file_list_msg = receive_message(client_socket)
            if file_list_msg.status_code == application_message.StatusCode.SUCCESS.value:
                try:
                    files = json.loads(file_list_msg.payload.decode('utf-8'))
                    return files
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON received: {e}")
            else:
                error_message = file_list_msg.payload.decode('utf-8', errors='replace')
                raise ValueError(f"Server returned error: {error_message}")
        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"Connection lost during upload: {e}")
            return
        
    except Exception as e:
        messagebox.showerror("Error", f"Error listing files: {e}")
        return {}


def upload_folder_parallel(host, port, folder_path):
    """
    Upload all files in a folder in parallel using independent connections.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory.")
        return

    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    threads = []
    for file in files:
        thread = threading.Thread(target=upload_files, args=(host, port, file))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    print("All files uploaded in parallel.")


# ---------------------------- CLI Interface ---------------------------- #

def cli_interface():
    """
    CLI interface for interacting with the server.
    """
    host = input("Enter server host (e.g., 127.0.0.1): ").strip()
    port = int(input("Enter server port (e.g., 9999): ").strip())

    
    try:
        # Add main socket for client-server communication
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        while True:
            command = input("Enter command (upload <filename/folder>, download <filename>, exit): ").strip()

            if command == "exit":
                print("Exiting...")
                break

            elif command.startswith("upload"):
                _, filepath = command.split(" ", 1)

                if os.path.isdir(filepath):
                    print(f"Detected folder: {filepath}")
                    mode = input("Choose upload mode: sequential or parallel? ").strip().lower()
                    if mode == "sequential":
                        upload_folder_sequential(host, port, filepath)
                    elif mode == "parallel":
                        upload_folder_parallel(host, port, filepath)
                    else:
                        print("Invalid mode. Use 'sequential' or 'parallel'.")
                else:
                    upload_files(host, port, filepath)

            elif command.startswith("download"):
                _, filename = command.split(" ", 1)
                print(f"Downloading file: {filename}")
                # Add download logic here
            else:
                print("Invalid command. Use 'upload <filename/folder>', 'download <filename>', or 'exit'.")
    except Exception as e:
            print(f"Error: {e}")
            if 'sock' in locals():
                sock.close()


# ---------------------------- Main ---------------------------- #
def main():
    root = tk.Tk()
    app = start_canvas.StartCanvas(root)  # Start the start_canvas
    root.mainloop()

if __name__ == "__main__":
    main()
