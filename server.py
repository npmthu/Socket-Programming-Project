import socket
import threading
import os
import logging
import json
from datetime import datetime
import tkinter as tk
import sys
import hashlib
import struct
import secrets

import customtkinter as ctk
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import application_message

# Constants for file transfer
CHUNK_SIZE = 4096  # 4 KB chunks
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1 GB max file size
DEFAULT_SAVE_PATH = 'server_files/'
DEFAULT_PORT = 9999
DEFAULT_HOST =  socket.gethostbyname(socket.gethostname()) #"127.0.0.1"
DEFAULT_LOG_FILE = 'server_logs.txt'

log_lock = threading.Lock()
file_lock = threading.Lock()
folder_lock = threading.Lock()
data_lock = threading.Lock()

# Global thread-safe logger (will be initialized in create_gui)
global_logger = None
active_connections = 0


class ThreadSafeLogger:
    def __init__(self, log_file, log_text_widget):
        self._lock = threading.Lock()
        self._log_file = log_file
        self._log_text_widget = log_text_widget
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self._log_file) or '.', exist_ok=True)
        
        # Create the log file if it doesn't exist
        self._initialize_log_file()

    def _initialize_log_file(self):
        """
        Create the log file if it doesn't exist, with a startup message.
        Ensures the file is created and ready for appending.
        """
        with self._lock:
            # Open the file in append mode (creates the file if it doesn't exist)
            try:
                with open(self._log_file, 'a') as f:
                    # Write a startup message with clear timestamp
                    startup_message = f"\n{'='*50}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - LOG STARTED\n{'='*50}\n"
                    f.write(startup_message)
            except Exception as e:
                print(f"Error initializing log file {self._log_file}: {e}")

    def _write_log(self, level, message):
        """
        Internal method to write log message to file and GUI
        """
        with self._lock:
            # Prepare log message with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            full_log_message = f"{timestamp} - {level}: {message}\n"

            # Write to file in append mode
            try:
                with open(self._log_file, 'a') as f:
                    f.write(full_log_message)
            except Exception as e:
                print(f"Error writing to log file: {e}")

            # Update GUI log text widget (thread-safe)
            if self._log_text_widget:
                try:
                    self._log_text_widget.config(state=tk.NORMAL)
                    self._log_text_widget.insert(tk.END, full_log_message)
                    self._log_text_widget.yview(tk.END)  # Auto-scroll
                    self._log_text_widget.config(state=tk.DISABLED)
                except Exception as e:
                    print(f"Error updating log widget: {e}")

    def info(self, message):
        """Log an info message"""
        self._write_log("INFO", message)

    def error(self, message, exception=None):
        """Log an error message, optionally with exception details"""
        full_error_message = message
        if exception:
            full_error_message += f"\n{traceback.format_exc()}"
        self._write_log("ERROR", full_error_message)

    def warning(self, message):
        """Log a warning message"""
        self._write_log("WARNING", message)

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

        global_logger.info(f"Server receive FILE: {filename} at {datetime.now()}")

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
                global_logger.info(f"Server change file name to {filename} at {datetime.now()}")

            # Receive file in chunks
            with open(filepath, 'wb') as file:
                try:
                    bytes_received = 0
                    file_hash = hashlib.sha256()
                    while bytes_received < filesize:
                        chunk_msg = receive_message(client_socket)
                        # Write chunk and update hash
                        file.write(chunk_msg.payload)
                        file_hash.update(chunk_msg.payload)
                        bytes_received += len(chunk_msg.payload)
                except (ConnectionResetError, BrokenPipeError) as e:
                    file.close()
                    os.remove(filepath)
                    with log_lock:
                        global_logger.error(f"Connection error while receiving message: {e}")

            # Verify file integrity
            received_hash = file_hash.hexdigest()
            if received_hash != expected_hash:
                os.remove(filepath)
                raise ValueError("File transfer corrupted: Hash mismatch")
        
        with log_lock:
            global_logger.info(f"File {filename} received successfully. Size: {bytes_received} bytes")

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
            global_logger.error(f"Error receiving file: {e}")
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

        global_logger.info(f"Server send FILE: {filename} at {datetime.now()}")

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
            global_logger.info(f"File {filename} sent successfully. Size: {filesize} bytes")
        return True
    
    except (ConnectionResetError, BrokenPipeError) as e:
        with log_lock:
            global_logger.error(f"Connection error while sending file: {e}")
        return False
    
    except Exception as e:
        with log_lock:
            global_logger.error(f"Error sending file: {e}")
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
        global_logger.info(f"New client connection from {client_socket.getpeername()}")
        # Server operations: upload, download, list files
        while True:
            try:
                # Receive action message
                action_msg = receive_message(client_socket)
                if action_msg.action_code == application_message.ActionCode.HEART_BEAT.value:
                    # Send success message
                    response_msg = application_message.Message(
                        msg_type=application_message.MessageType.RESPONSE.value, 
                        action_code=application_message.ActionCode.HEART_BEAT.value, 
                        status_code=application_message.StatusCode.SUCCESS.value, 
                        payload=b"successful"
                    )
                    client_socket.sendall(response_msg.to_bytes())

                elif action_msg.action_code == application_message.ActionCode.LOGIN.value:
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

                    global_logger.info(f"Server receive request UPLOAD_FOLDER: {foldername} at {datetime.now()}")

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

                    global_logger.info(f"Server receive request LIST folder: {directory} at {datetime.now()}")


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
                    global_logger.error(f"Connection lost with client {client_socket.getpeername()}", e)
                break
            except Exception as e:
                with log_lock:
                    global_logger.error(f"Error with client {client_socket.getpeername()}", e)
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
            global_logger.info(f"Closing connection with client {client_socket.getpeername()}")
        client_socket.close()

def start_server(host, port, log_text_widget, update_connection_callback):
    global global_logger, active_connections
    if global_logger is None:
        global_logger = ThreadSafeLogger(DEFAULT_LOG_FILE, log_text_widget)

    server_socket = None
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)

        global_logger.info(f"Server started on {host}:{port} at {datetime.now()}")

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                global_logger.info(f"Connection from {client_address} at {datetime.now()}")
                
                # Tăng số lượng kết nối
                active_connections += 1
                update_connection_callback(active_connections)
                
                # Tạo một hàm wrapper để giảm số lượng kết nối khi client ngắt kết nối
                def handle_client_wrapper(sock):
                    try:
                        handle_client(sock)
                    finally:
                        global active_connections
                        active_connections -= 1
                        update_connection_callback(active_connections)
                
                # Implement IP-based connection limits and logging
                client_thread = threading.Thread(
                    target=handle_client_wrapper, 
                    args=(client_socket,), 
                    daemon=True
                )
                client_thread.start()
            except socket.error as socket_err:
                global_logger.error(f"Socket error while accepting connection: {socket_err}")
            except Exception as e:
                global_logger.error(f"Error in server accept loop: {e}")
    
    except Exception as e:
        global_logger.error(f"Server initialization error: {e}")
    
    finally:
        if server_socket:
            try:
                server_socket.close()
                global_logger.info("Server socket closed")
            except Exception as close_err:
                global_logger.error(f"Error closing server socket: {close_err}")
                global_logger.error(f"Error closing server socket: {close_err}")

def create_gui():
    global global_logger, active_connections
    
    # Initialize root window
    root = ctk.CTk()
    root.title("Server Management")
    root.geometry("1200x600") 
    root.config(bg="white")

    # Variables for tracking host, port, and connections
    host_var = tk.StringVar(value=DEFAULT_HOST)
    port_var = tk.StringVar(value=str(DEFAULT_PORT))
    connection_var = tk.StringVar(value="0")
    active_connections = 0

    # Main container frame
    main_frame = ctk.CTkFrame(root, width=1200, height=600, corner_radius=10)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    main_frame.grid_rowconfigure(0, weight=1)  # Cho phép mở rộng hàng 0
    main_frame.grid_rowconfigure(1, weight=0)  # Hàng nút giữ cố định
    main_frame.grid_columnconfigure(0, weight=0)  # Cột info giữ cố định
    main_frame.grid_columnconfigure(1, weight=1)  # Cột log mở rộng

    # Log Display Frame (central focus) using CTkScrollableFrame
    log_frame = ctk.CTkScrollableFrame(main_frame, width=900, height=500, corner_radius=10)
    log_frame.grid(row=0, column=1, rowspan=2, padx=20, pady=20, sticky="nsew")

    log_text = tk.Text(log_frame, wrap=tk.WORD, font=("Arial", 20), state=tk.DISABLED, bg="light gray")
    log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    global_logger = ThreadSafeLogger(DEFAULT_LOG_FILE, log_text)

    # Information Frame for Host, Port, and Connection Details
    info_frame = ctk.CTkFrame(main_frame, width=300, height=180, corner_radius=10)
    info_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

    # Host Entry
    ctk.CTkLabel(info_frame, text="Host's IP:", font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    host_entry = ctk.CTkEntry(info_frame, textvariable=host_var, font=("Arial", 14))
    host_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    # Port Entry
    ctk.CTkLabel(info_frame, text="Port:", font=("Arial", 14, "bold")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
    port_entry = ctk.CTkEntry(info_frame, textvariable=port_var, font=("Arial", 14))
    port_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

    # Active Connections Entry
    ctk.CTkLabel(info_frame, text="Active Connections:", font=("Arial", 14, "bold")).grid(row=2, column=0, padx=10, pady=10, sticky="w")
    connection_entry = ctk.CTkEntry(info_frame, textvariable=connection_var, font=("Arial", 14), state="readonly")
    connection_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

    # Function to update connection count
    def update_connection_count(count):
        connection_var.set(str(count))

    # Button Frame for Start and Exit Buttons
    button_frame = ctk.CTkFrame(main_frame, width=300, height=80, corner_radius=10)
    button_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

    # Start Server Button
    ctk.CTkButton(
        button_frame, text="Start Server", width=150, height=40, font=("Arial", 14), 
        command=lambda: start_server_with_config(host_entry, port_entry)
    ).grid(row=0, column=0, padx=20, pady=10)

    # Exit Button
    ctk.CTkButton(
        button_frame, text="Exit", width=150, height=40, font=("Arial", 14), 
        command=root.quit
    ).grid(row=0, column=1, padx=20, pady=10)

    # Start server with provided configuration
    def start_server_with_config(host_entry, port_entry):
        host = host_var.get()
        port = int(port_var.get())

        # Disable entries while server is running
        host_entry.configure(state='disabled')
        port_entry.configure(state='disabled')

        # Start the server in a separate thread
        threading.Thread(
            target=start_server, 
            args=(host, port, log_text, update_connection_count), 
            daemon=True
        ).start()

    root.mainloop()


if __name__ == "__main__":    
    # Run the GUI
    create_gui()