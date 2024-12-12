import socket
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter import Tk, Canvas, Button
from PIL import Image, ImageTk, ImageDraw
from io import BytesIO
from threading import Thread
import time
import hashlib
import struct
from threading import Event
import sys
import json
import queue 
from datetime import datetime

# Add the directory containing application_message.py to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import application_message
from gui import *

CHUNK_SIZE = 4096  # 4 KB chunks
WINDOW_WIDTH = 1066
WINDOW_HEIGHT = 600
BUFFER_SIZE = 4096
DEFAULT_SAVE_PATH_ON_SERVER = 'server_files'

# Trạng thái toàn cục dưới dạng dict
state = {"CONNECTION_CORRUPTED": False}
folder_structure_queue = queue.Queue()
function_name_queue = queue.Queue()
function_args_queue = queue.Queue()
socket_container = {'socket': None}


class CommunicateToServer():
    def __init__(self, socket):
        self.socket = socket

    def receive_message(self):
        """
        Receives a complete message containing both header and payload.
        Ensures the message has at least the header size and validates that
        the payload length matches the value specified in the header.
        """
        try:
            # Receive the header data
            header_data = self.socket.recv(application_message.Message.HEADER_SIZE)
            if not header_data or len(header_data) < application_message.Message.HEADER_SIZE:
                raise ConnectionResetError("Incomplete or missing header received.")

            # Unpack the header
            msg_type, action_code, status_code, payload_length = struct.unpack(
                application_message.Message.HEADER_FORMAT, header_data
            )

            # Receive the payload based on the payload_length specified in the header
            payload = b""
            while len(payload) < payload_length:
                chunk = self.socket.recv(payload_length - len(payload))
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
            raise ConnectionResetError(f"{e}")
        except Exception as e:
            raise ValueError(f"Error receiving message: {e}")

    def heart_beat(self):
        try:
            #Send hearbeat
            heart_beat_msg = application_message.Message(
                    msg_type=application_message.MessageType.REQUEST.value,
                    action_code=application_message.ActionCode.HEART_BEAT.value,
                    status_code=application_message.StatusCode.SUCCESS.value,
                    payload=''.encode('utf-8')
                )
            self.socket.sendall(heart_beat_msg.to_bytes())

            #Receive response
            response_msg = self.receive_message()
        except (ConnectionResetError, BrokenPipeError) as e:
            raise ConnectionResetError(f"{e}")
        except Exception as e:
            raise(f"Error hearbeating: {e}")

    def calculate_file_hash(self, filepath):
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def authenticate_user(self, pin):
        try:
            # Create authentication message
            auth_msg = application_message.Message(
                msg_type=application_message.MessageType.REQUEST.value,
                action_code=application_message.ActionCode.LOGIN.value,
                status_code=application_message.StatusCode.SUCCESS.value,
                payload=pin.encode()
            )
            self.socket.send(auth_msg.to_bytes())

            # Receive authentication response
            response_msg = application_message.Message.from_bytes(self.socket.recv(1024))

            if response_msg.status_code == application_message.StatusCode.SUCCESS:
                return True
            else:
                messagebox.showerror("Authentication Failed", 
                                      response_msg.payload.decode('utf-8', errors='replace'))
                return False
        except Exception as e:
            messagebox.showerror("Error", f"Authentication error: {e}")
            return False

    def create_folder_structure(self, folder_path):
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

    def upload_folder_sequential(self, folder_path, save_path):
        """
        Uploads all files in the given folder structure dictionary to the server.
        """
        try:
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
            self.socket.sendall(metadata_msg.to_bytes())

            # Receive response
            response_msg = self.receive_message()
            decoded_payload = response_msg.payload.decode('utf-8')
            decoded_payload = decoded_payload.replace("'", '"')
            folder_metadata = json.loads(decoded_payload)
            new_foldername = folder_metadata.get('foldername', '')
            if foldername != new_foldername:
                foldername = new_foldername
        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"Connection lost during upload: {e}")
            raise ConnectionResetError(f"{e}")
            return
    
        save_path = os.path.join(save_path, foldername)

        # Create the folder structure dictionary
        folder_structure = self.create_folder_structure(folder_path)
        # Helper function to process the folder structure recursively and upload files
        def process_folder_structure(current_structure, current_folder_path, current_save_path):
            for key, value in current_structure.items():
                if value is None:  # This is a file
                    # Construct the full path to the file
                    file_path = os.path.join(current_folder_path, key)
                    try:
                        self.upload_files([file_path], current_save_path)
                    except (ConnectionResetError, BrokenPipeError) as e:
                        raise ConnectionResetError(f"{e} - while uploading")
                else:  # This is a subfolder                
                    subfolder_path = os.path.join(current_folder_path, key)
                    subfolder_save_path = os.path.join(current_save_path, key)
                    process_folder_structure(value, subfolder_path, subfolder_save_path)
        # Start processing subfolders from the root of the folder structure
        process_folder_structure(folder_structure, folder_path, save_path)

    def upload_files(self, files, save_path):
        try:
            for file_path in files:
                # Validate file existence
                if not os.path.isfile(file_path):
                    print(file_path)
                    raise FileNotFoundError(f"File not found: {file_path}")

                # Calculate file metadata
                filesize = os.path.getsize(file_path)
                filename = os.path.basename(file_path)
                file_hash = self.calculate_file_hash(file_path)

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
                try:
                    self.socket.sendall(metadata_msg.to_bytes())

                    # Send file in chunks
                    with open(file_path, 'rb') as file:
                        while chunk := file.read(CHUNK_SIZE):
                            chunk_msg = application_message.Message(
                                msg_type=application_message.MessageType.REQUEST.value,
                                action_code=application_message.ActionCode.UPLOAD.value,
                                status_code=application_message.StatusCode.SUCCESS.value,
                                payload=chunk
                            )
                            self.socket.sendall(chunk_msg.to_bytes())

                    # Receive upload success confirmation
                    response_msg = self.receive_message()
                    if response_msg.status_code == application_message.StatusCode.SUCCESS.value:
                        upload_details = json.loads(response_msg.payload.decode())
                        print(f"Uploaded: {upload_details['filename']} (Size: {upload_details['filesize']} bytes)")
                    else:
                        print(f"Upload failed for {filename}")
                except (ConnectionResetError, BrokenPipeError) as e:
                    print(f"Connection lost during upload: {e}")
                    raise ConnectionResetError(f"{e} - while uploading file")
        except Exception as e:
            print(f"Error uploading files: {e}")

    def download_folder(self, foldername, save_path=""):
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
            folder_structure = self.list_files_for_download(foldername)

            if foldername == '':
                foldername = DEFAULT_SAVE_PATH_ON_SERVER
            # Create the local base path for the folder
            local_save_path = os.path.join(save_path, foldername)
            print(f'local_save_path before check: {local_save_path}')
            # Make new foldername if folder exits in save_path
            if os.path.exists(local_save_path) and os.path.isdir(local_save_path):
                timestamp = int(time.time())  
                new_foldername = f"{foldername}_{timestamp}"  
                local_save_path = os.path.join(save_path, new_foldername)
            local_save_path.replace('\\', '/')
            print(f'local_save_path after check: {local_save_path}')
            print(f'save_path: {save_path}')

            os.makedirs(local_save_path, exist_ok=True)  # Ensure the base save path exists
            
            if foldername == DEFAULT_SAVE_PATH_ON_SERVER:
                foldername = ''
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
                    print(files_to_download)
                    try:
                        self.download_files(files_to_download, save_path=current_save_path)
                    except (ConnectionResetError, BrokenPipeError) as e:
                        raise ConnectionResetError(f"{e} - while download")

            # Start processing the folder's structure
            process_folder_structure(folder_structure, local_save_path, parent_path=foldername)
        except Exception as e:
            messagebox.showerror("Error", f"Error downloading folder '{foldername}': {e}")

    def download_files(self, files, save_path=""):
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
                try:
                    self.socket.sendall(download_msg.to_bytes())

                    # Receive file metadata
                    metadata_msg = self.receive_message()
                    decoded_payload = metadata_msg.payload.decode('utf-8')
                    file_metadata = json.loads(decoded_payload)
                    filename = file_metadata.get('filename', 'downloaded_file')
                    filesize = file_metadata.get('filesize', 0)
                    expected_hash = file_metadata.get('hash', '')
                except (ConnectionResetError, BrokenPipeError) as e:
                    print(f"Connection lost during download: {e}")
                    raise ConnectionResetError(f"{e} - while dowloading file")
                    return
                
                # Prepare file for writing
                # Prepare the full file path including the filename
                filepath = os.path.join(save_path, filename)
                # Ensure the directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                # Check if the file exists and modify the filename if needed
                if os.path.exists(filepath):
                    base, ext = os.path.splitext(filename)
                    timestamp = int(datetime.now().timestamp())
                    filename = f"{base}_{timestamp}{ext}"
                    filepath = os.path.join(save_path, filename)
                file_hash = hashlib.sha256()

                with open(filepath, 'wb') as file:
                    bytes_received = 0
                    while bytes_received < filesize:
                        try:
                            chunk_msg = self.receive_message()
                            file.write(chunk_msg.payload)
                            file_hash.update(chunk_msg.payload)
                            bytes_received += len(chunk_msg.payload)
                        except (ConnectionResetError, BrokenPipeError) as e:
                            print(f"Connection lost during download: {e}")
                            file.close()
                            os.remove(filepath)
                            raise ConnectionResetError(f"{e} - while downloading file")

                received_hash = file_hash.hexdigest()

                # Verify file integrity
                if received_hash != expected_hash:
                    os.remove(filepath)
                    raise ValueError(f"File '{filename}' download corrupted: Hash mismatch")

                print("Download Success",
                                    f"File {filename} downloaded successfully.\n"
                                    f"Size: {bytes_received} bytes")

        except Exception as e:
            raise e

    def list_files_for_download(self, directory=""):
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
            try:
                self.socket.sendall(list_msg.to_bytes())

                # Receive file list
                file_list_msg = self.receive_message()
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
                print(f"Connection lost during list: {e}")
                raise ConnectionResetError(f"{e} - while listing files")

        except Exception as e:
            messagebox.showerror("Error", f"Error listing files: {e}")
            return {}

    def list_files(self, directory=''):
        directory_structure = self.list_files_for_download(directory)
        folder_structure_queue.put(directory_structure)

    def upload_folder_parallel(self, folder_path):
        """
        Upload all files in a folder in parallel using independent connections.
        """
        if not os.path.isdir(folder_path):
            print(f"Error: {folder_path} is not a valid directory.")
            return

        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        threads = []
        for file in files:
            thread = threading.Thread(target=self.upload_files, args=( file))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        print("All files uploaded in parallel.")

#-----------------------------CONNECTION HANDLER-----------------------

def communicate_to_server(client):
    communication = CommunicateToServer(client)
    while True:
        time.sleep(0.05)
        try:
            if not function_name_queue.empty() and not function_args_queue.empty():
                # Take arguments and function's name from queue
                method_name = function_name_queue.get()
                method_args = function_args_queue.get()

                # Check function and call it
                if hasattr(communication, method_name):
                    method = getattr(communication, method_name)
                    # Gọi hàm với các arguments
                    method(*method_args)
                else:
                    print(f"Method '{method_name}' does not exist.")
            else:
                communication.heart_beat()

        except (ConnectionResetError, BrokenPipeError) as e:
                print(f"Connection corupted: {e}")
                state['CONNECTION_CORRUPTED'] = True
                communication.socket.close()
                return

# ---------------------------- MainApp ---------------------------- #

class App(tk.Tk):
    def __init__(self, title, size):
        
        #Create window
        super().__init__()
        self.title(title)
        self.width = size[0]
        self.height = size[1]
        self.geometry(f'{size[0]}x{size[1]}')
        self.minsize(size[0], size[1])
        self.title("Socket Programming Project")
        self.iconphoto(True, tk.PhotoImage(file='icon.png'))

        start_canvas = StartCanvas(self, self.width, self.height, socket_container)
        start_canvas.pack(fill="both", expand=True)
        
        '''test menu
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("192.168.1.4", 9999))
        self.MenuFrame = MenuFrame(self, function_name_queue, function_args_queue, folder_structure_queue)
        # Run communication thread
        self.communicate_thread = threading.Thread(
            target=communicate_to_server,
            args=(client,),
            daemon=True
        )
        self.communicate_thread.start()
        '''

        # Kiểm tra trạng thái kết nối
        self.check_connection_state()

        # Kiểm tra sự thay đổi của socket
        self.check_socket_change()

    def check_socket_change(self):
        # Kiểm tra nếu socket đã được kết nối
        if socket_container['socket']:
            print(f"Socket is ready: {socket_container['socket']}")
            self.on_socket_ready()
        else:
            print("cec")
            self.after(1000, self.check_socket_change)  # Lặp lại kiểm tra sau 100ms

    def on_socket_ready(self):
        print("Socket is now ready!")
        client_socket = socket_container['socket']
        if client_socket:
            print("Client socket is ready")
            
            self.MenuFrame = MenuFrame(self, function_name_queue, function_args_queue, folder_structure_queue)

            # Run communication thread
            self.communicate_thread = threading.Thread(
                target=communicate_to_server,
                args=(client_socket,),
                daemon=True
            )
            self.communicate_thread.start()

            # Kiểm tra trạng thái kết nối
            self.check_connection_state()

    def check_connection_state(self):
        if state['CONNECTION_CORRUPTED']:
            for widget in self.winfo_children():
                widget.destroy()
            
            time.sleep(2)
            #Display the start canvas
            canvas = tk.Canvas(self, bg="#f4ebd5", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
        else:
            # Lặp lại kiểm tra sau 100ms
            self.after(100, self.check_connection_state)


if __name__ == "__main__":
    #root = tk.Tk()
    #cv = StartCanvas(root)
    root = App('Socket', (WINDOW_WIDTH, WINDOW_HEIGHT))
    root.mainloop()
    #client_socket = connect_to_server('localhost', 6578)
    #communication = CommunicateToServer(client_socket)
    #communication.download_folder('folder1','C:\\Users\\thai\\Downloads\\testing')

        