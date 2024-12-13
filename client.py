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
from tkinter import PhotoImage
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
gui_queue = queue.Queue() 

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

import customtkinter as ctk
import os


import tkinter as tk
from tkinter import ttk
import os


import tkinter as tk
from tkinter import ttk
import os

class ProgressDialog(tk.Toplevel):
    def __init__(self, parent, top_title, mode='file'):
        """
        Create a progress dialog with different modes:
        - 'file': Shows progress for a single file (bytes)
        - 'folder': Shows progress for a folder (file count)
        """
        print(f"display dialog {parent}")
        super().__init__(parent)
        self.title(top_title)
        self.geometry('400x150')
        self.resizable(False, False)
        self.parent = parent
        self.mode = mode
        self.configure(bg="#953019")
        self.transient(parent)
        self.grab_set()
        self.lift()  # Đưa cửa sổ lên trên cùng
        self.attributes('-topmost', True)

        # File/folder name label
        self.name_label = ttk.Label(self, text="", font=('TkDefaultFont', 10), background="#953019", foreground="white")
        self.name_label.pack(pady=(10, 5))

        # Progress bar
        style = ttk.Style(self)
        style.layout('text.Horizontal.TProgressbar',
             [('Horizontal.Progressbar.trough',
               {'children': [('Horizontal.Progressbar.pbar',
                              {'side': 'left', 'sticky': 'ns'})],
                'sticky': 'nswe'}),
              ('Horizontal.Progressbar.label', {'sticky': ''})])
        # Set the custom style for the progress bar
        style.configure("Text.Horizontal.TProgressbar", foreground="white", background="#5cb85c", troughcolor="#953019", bordercolor="#953019")
        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate", style="Text.Horizontal.TProgressbar")
        self.progress.pack(pady=10, padx=10, fill="x")

        # Progress text
        self.progress_text = ttk.Label(self, text="", font=('TkDefaultFont', 9), background="#953019", foreground="white")
        self.progress_text.pack(pady=(0, 10))

        self.total_size = 0
        self.current_size = 0
        self.current_file = ""
        self.is_canceled = False
        self.is_completed = False  # Flag to indicate the task is completed
        self.center_window()

    def center_window(self):
        """Centers the window on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def update_progress(self, current, total, current_file=""):
        if self.is_canceled or self.is_completed:
            return False
        self.total_size = total
        self.current_size = current
        self.current_file = current_file
        # Update labels based on mode
        if self.mode == 'file':
            progress_percent = int((current / total) * 100) if total > 0 else 0
            text = f"{self._format_size(current)} / {self._format_size(total)} ({progress_percent}%)"
            file_name = os.path.basename(current_file) if current_file else ""
        elif self.mode == 'folder':
            progress_percent = int((current / total) * 100) if total > 0 else 0
            text = f"{current} / {total} files ({progress_percent}%)"
            file_name = ""
        # Bỏ dòng self.after ở đây
        self._update_gui(progress_percent, text, file_name)
        return not self.is_canceled
    def _update_gui(self, progress_percent, text, file_name):
        """
        Helper function to update GUI elements in main thread
        """
        self.progress['value'] = progress_percent  # Progress percentage as a fraction
        self.progress_text.config(text=text)
        self.name_label.config(text=file_name)

    def complete(self):
        """Set progress bar to completed and shows 'Done' message"""
        self.is_completed = True
        self.progress['value'] = 100  # Set progress to 100%
        self.progress_text.config(text="Done")
        self.name_label.config(text="")
        self.after(3000, self.destroy)  # Close the dialog after 3 seconds
        self.parent.focus_set()  # Set focus to parent after closing

    @staticmethod
    def _format_size(size_in_bytes):
        """
        Convert bytes to human-readable format
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.1f} TB"

class CommunicateToServer():
    def __init__(self, socket):
        self.socket = socket
        self.progress_dialog_created = False
    
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

    def upload_files(self, files, save_path, is_part_of_folder_upload=False):
        """
        Modified upload_files method to support progress tracking

        :param files: List of file paths or a single file path
        :param save_path: Path to save files on server
        :param is_part_of_folder_upload: Flag to indicate if this is part of a folder upload
        """
        try:
            # If files is a single string, convert to list
            if isinstance(files, str):
                files = [files]

            # Calculate total file size for progress tracking
            total_size = sum(os.path.getsize(file_path) for file_path in files)

            # Create progress dialog only if not part of folder upload
            if not is_part_of_folder_upload:
                gui_queue.put(('create_progress_dialog', "Uploading Files", 'file'))
                self.progress_dialog_created = True
                print("Sent create_progress_dialog command")
            update_interval = 500
            last_update_time = 0

            current_total_size = 0
            uploaded_files_count = 0

            for file_path in files:
                # Validate file existence
                if not os.path.isfile(file_path):
                    print(f"File not found: {file_path}")
                    continue

                # Calculate file metadata
                filesize = os.path.getsize(file_path)
                filename = os.path.basename(file_path)
                file_hash = self.calculate_file_hash(file_path)

                # Prepare file metadata
                metadata = {
                    'filename': filename,
                    'filesize': filesize,
                    'save_path': save_path,
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

                    # Send file in chunks with progress tracking
                    with open(file_path, 'rb') as file:
                        bytes_sent = 0
                        while chunk := file.read(CHUNK_SIZE):
                            chunk_msg = application_message.Message(
                                msg_type=application_message.MessageType.REQUEST.value,
                                action_code=application_message.ActionCode.UPLOAD.value,
                                status_code=application_message.StatusCode.SUCCESS.value,
                                payload=chunk
                            )
                            self.socket.sendall(chunk_msg.to_bytes())

                            # Update progress
                            bytes_sent += len(chunk)
                            current_total_size += len(chunk)

                            # Update progress dialog if not part of folder upload
                            if not is_part_of_folder_upload and self.progress_dialog_created:
                                current_time = time.time() * 1000  # Convert to milliseconds
                                if current_time - last_update_time >= update_interval:
                                    gui_queue.put(('update_progress', current_total_size, total_size, file_path))
                                    print("Sent update_progress command")
                                    last_update_time = current_time

                        # If upload was not canceled
                        if not (not is_part_of_folder_upload and gui_queue.qsize() > 0):
                            # Receive upload success confirmation
                            response_msg = self.receive_message()
                            if response_msg.status_code == application_message.StatusCode.SUCCESS.value:
                                upload_details = json.loads(response_msg.payload.decode())
                                print(f"Uploaded: {upload_details['filename']} (Size: {upload_details['filesize']} bytes)")
                                uploaded_files_count += 1
                            else:
                                print(f"Upload failed for {filename}")

                except (ConnectionResetError, BrokenPipeError) as e:
                    print(f"Connection lost during upload: {e}")
                    if not is_part_of_folder_upload:
                        gui_queue.put('close_progress_dialog')
                        print("send close_progress_dialog command")
                    raise ConnectionResetError(f"{e} - while uploading file")

            # Close progress dialog if it exists and not part of folder upload
            if not is_part_of_folder_upload:
                gui_queue.put('close_progress_dialog')
                print("Send close_progress_dialog command")

            return uploaded_files_count

        except Exception as e:
            if not is_part_of_folder_upload:
                gui_queue.put('close_progress_dialog')
                print("Send close_progress_dialog command")
            print(f"Error uploading files: {e}")
            return 0

    def download_files(self, files, save_path="", is_part_of_folder_download=False):
        """
        Modified download_files method to support progress tracking

        :param files: List of file names or a single file name
        :param save_path: Path to save downloaded files
        :param is_part_of_folder_download: Flag to indicate if this is part of a folder download
        """
        try:
            # If files is a single string, convert to list
            if isinstance(files, str):
                files = [files]

            # Calculate total download size for progress tracking
            total_download_size = 0
            total_files_count = len(files)

            # Create progress dialog if not part of folder download
            if not is_part_of_folder_download:
                gui_queue.put(('create_progress_dialog', "Downloading Files", 'file'))
                self.progress_dialog_created = True
                print("Send create_progress_dialog command")

            update_interval = 500
            last_update_time = 0

            downloaded_files_count = 0
            current_total_downloaded_size = 0

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

                    # Update total download size
                    total_download_size += filesize

                except (ConnectionResetError, BrokenPipeError) as e:
                    print(f"Connection lost during download: {e}")
                    if not is_part_of_folder_download:
                        gui_queue.put('close_progress_dialog')
                        print("send close_progress_dialog command")
                    raise ConnectionResetError(f"{e} - while downloading file")

                # Prepare file for writing
                filepath = os.path.join(save_path, filename)
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
                            chunk_size = len(chunk_msg.payload)
                            bytes_received += chunk_size
                            current_total_downloaded_size += chunk_size

                            # Update progress dialog if not part of folder download
                            if not is_part_of_folder_download and self.progress_dialog_created:
                                current_time = time.time() * 1000  # Convert to milliseconds
                                if current_time - last_update_time >= update_interval:
                                    if not is_part_of_folder_download and self.progress_dialog_created:
                                        gui_queue.put(('update_progress', current_total_downloaded_size, total_download_size, filepath))
                                        print("send update_progress command")
                                        last_update_time = current_time

                        except (ConnectionResetError, BrokenPipeError) as e:
                            print(f"Connection lost during download: {e}")
                            file.close()
                            os.remove(filepath)
                            if not is_part_of_folder_download:
                                gui_queue.put('close_progress_dialog')
                                print("send close_progress_dialog command")

                            raise ConnectionResetError(f"{e} - while downloading file")

                    # If download was not canceled
                    if not (not is_part_of_folder_download and gui_queue.qsize() > 0):
                        received_hash = file_hash.hexdigest()

                        # Verify file integrity
                        if received_hash != expected_hash:
                            os.remove(filepath)
                            raise ValueError(f"File '{filename}' download corrupted: Hash mismatch")

                        downloaded_files_count += 1
                        print("Download Success",
                              f"File {filename} downloaded successfully.\n"
                              f"Size: {bytes_received} bytes")

            # Close progress dialog if it exists and not part of folder download
            if not is_part_of_folder_download:
                gui_queue.put('close_progress_dialog')
                print("send close_progress_dialog command")

            return downloaded_files_count

        except Exception as e:
            if not is_part_of_folder_download:
                gui_queue.put('close_progress_dialog')
                print("send close_progress_dialog command")

            raise e
        
    def upload_folder_sequential(self, folder_path, save_path):
        """
        Uploads all files in the given folder structure to the server.
        """
        try:
            # Validate folder path
            if not os.path.isdir(folder_path):
                messagebox.showerror("Error", f"{folder_path} is not a valid directory.")
                return False

            # Create progress dialog for folder upload
            
            gui_queue.put(('create_progress_dialog', "Uploading Folder", 'folder'))
            self.progress_dialog_created = True
            print("send create_progress_dialog command")


            # Send message to server to check if folder exists
            foldername = os.path.basename(folder_path)

            # Prepare folder metadata
            metadata = {
                'foldername': foldername,
                'save_path': save_path
            }

            # Send upload metadata
            metadata_msg = application_message.Message(
                msg_type=application_message.MessageType.REQUEST.value,
                action_code=application_message.ActionCode.UPLOAD_FOLDER.value,
                status_code=application_message.StatusCode.SUCCESS.value,
                payload=json.dumps(metadata).encode()
            )

            try:
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
                gui_queue.put('close_progress_dialog')
                print("send close_progress_dialog command")
                print(f"Connection lost during upload: {e}")
                raise ConnectionResetError(f"{e}")

            # Update save path with new folder name
            save_path = os.path.join(save_path, foldername)

            # Create the folder structure dictionary
            folder_structure = self.create_folder_structure(folder_path)

            # Count total number of files for progress tracking
            total_files = 0
            for root, dirs, files in os.walk(folder_path):
                total_files += len(files)
            uploaded_files = 0

            # Helper function to process the folder structure recursively and upload files
            def process_folder_structure(current_structure, current_folder_path, current_save_path):
                update_interval = 500
                last_update_time = 0
                nonlocal uploaded_files
                for key, value in current_structure.items():
                     if value is None:  # This is a file
                        # Construct the full path to the file
                        file_path = os.path.join(current_folder_path, key)
                        try:
                            # Upload individual file
                            result = self.upload_files([file_path], current_save_path, is_part_of_folder_upload=True)
                            uploaded_files += result

                            # Update folder progress dialog
                            if self.progress_dialog_created:
                                current_time = time.time() * 1000
                                if current_time - last_update_time >= update_interval:
                                    gui_queue.put(('update_progress', uploaded_files, total_files))
                                    print("send update_progress command")
                                    last_update_time = current_time

                        except (ConnectionResetError, BrokenPipeError) as e:
                            gui_queue.put('close_progress_dialog')
                            print("send close_progress_dialog command")

                            raise ConnectionResetError(f"{e} - while uploading")
                     else:  # This is a subfolder                
                        subfolder_path = os.path.join(current_folder_path, key)
                        subfolder_save_path = os.path.join(current_save_path, key)
                        process_folder_structure(value, subfolder_path, subfolder_save_path)

            # Start processing subfolders from the root of the folder structure
            process_folder_structure(folder_structure, folder_path, save_path)

            # Close progress dialog
            gui_queue.put('close_progress_dialog')
            print("send close_progress_dialog command")

            return True

        except Exception as e:
            gui_queue.put('close_progress_dialog')
            print("send close_progress_dialog command")
            messagebox.showerror("Error", f"Error uploading folder: {e}")
            return False

    def download_folder(self, foldername, save_path=""):
        """
        Downloads all files in the specified folder from the server.
        """
        try:
            # Create progress dialog for folder download
            gui_queue.put(('create_progress_dialog', "Downloading Folder", 'folder'))
            self.progress_dialog_created = True
            print("send create_progress_dialog command")

            # Retrieve the folder structure for the specified folder
            folder_structure = self.list_files_for_download(foldername)

            # Handle default save path
            if foldername == '':
                foldername = DEFAULT_SAVE_PATH_ON_SERVER

            # Create the local base path for the folder
            local_save_path = os.path.join(save_path, foldername)

            # Make new foldername if folder exists in save_path
            if os.path.exists(local_save_path) and os.path.isdir(local_save_path):
                timestamp = int(time.time())  
                new_foldername = f"{foldername}_{timestamp}"  
                local_save_path = os.path.join(save_path, new_foldername)

            # Ensure path uses forward slashes
            local_save_path = local_save_path.replace('\\', '/')

            # Create base save directory
            os.makedirs(local_save_path, exist_ok=True)

            # Reset foldername for server path if it was default
            if foldername == DEFAULT_SAVE_PATH_ON_SERVER:
                foldername = ''

            # Calculate total files to download
            def count_files(structure):
                total = 0
                for value in structure.values():
                    if value is None:
                        total += 1
                    elif isinstance(value, dict):
                        total += count_files(value)
                return total

            total_files = count_files(folder_structure)
            downloaded_files = 0

            # Helper function to process the folder structure recursively
            def process_folder_structure(current_structure, current_save_path, parent_path=""):
                nonlocal downloaded_files
                update_interval = 500
                last_update_time = 0
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
                    try:
                        result = self.download_files(files_to_download, save_path=current_save_path, is_part_of_folder_download=True)
                        downloaded_files += result

                        # Update folder progress dialog
                        if self.progress_dialog_created:
                            current_time = time.time() * 1000
                        if current_time - last_update_time >= update_interval:
                            gui_queue.put(('update_progress', downloaded_files, total_files))
                            print("send update_progress command")
                            last_update_time = current_time

                    except (ConnectionResetError, BrokenPipeError) as e:
                        gui_queue.put('close_progress_dialog')
                        print("send close_progress_dialog command")

                        raise ConnectionResetError(f"{e} - while downloading")

            # Start processing the folder's structure
            process_folder_structure(folder_structure, local_save_path, parent_path=foldername)

            # Close progress dialog
            gui_queue.put('close_progress_dialog')
            print("send close_progress_dialog command")

            return True

        except Exception as e:
            gui_queue.put('close_progress_dialog')
            print("send close_progress_dialog command")
            
            messagebox.showerror("Error", f"Error downloading folder '{foldername}': {e}")
            return False
        
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

        # Tạo StartCanvas với kích thước cố định và không dùng pack ở đây
        start_canvas = StartCanvas(self, size[0], size[1], socket_container)
        
        
        #test menu
        # client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # client.connect(("192.168.1.4", 9999))
        # self.MenuFrame = MenuFrame(self, function_name_queue, function_args_queue, folder_structure_queue)
        # print(f"self: {self}")
        # # Run communication thread
        # self.communicate_thread = threading.Thread(
        #     target=communicate_to_server,
        #     args=(client,),
        #     daemon=True
        # )
        # self.communicate_thread.start()
        # self.progress_dialog = None
        # self.progress_dialog_created = False

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
            canvas = tk.Canvas(self, bg="#f4ebd5", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
        else:
            # In ra số lượng phần tử trong queue để kiểm tra
            try:
                while not gui_queue.empty():
                    action = gui_queue.get()
                    print(f"Received action: {action}")  # Log chi tiết action

                    if isinstance(action, tuple):
                        if action[0] == 'create_progress_dialog':
                            print("receive create progress command")
                            _, title, mode = action
                            # Truyền self làm parent
                            self.create_progress_dialog(self, title, mode)
                        elif action[0] == 'update_progress':
                            print("receive update progress command")
                            if len(action) == 4:
                                _, current, total, current_file = action
                                self.update_progress(current, total, current_file)
                            elif len(action) == 3:
                                _, current, total = action
                                self.update_progress(current, total)
                    elif action == 'close_progress_dialog':
                        print("receive close process command")
                        self.close_progress_dialog()
            except Exception as e:
                print(f"Error in check_connection_state: {e}")

        # Giảm thời gian kiểm tra xuống để phản hồi nhanh hơn
        self.after(50, self.check_connection_state)

    def create_progress_dialog(self, parent, title, mode):
        # Sử dụng parent thay vì self
        if not self.progress_dialog:
            self.progress_dialog = ProgressDialog(parent, title, mode)
            self.progress_dialog_created = True
            print("created progress dialog")
        # Giảm thời gian kiểm tra xuống để phản hồi nhanh hơn
        self.after(50, self.check_connection_state)
    
    def update_progress(self, current, total, current_file=None):
        if self.progress_dialog:
            self.progress_dialog.update_progress(current, total, current_file)
    
    def close_progress_dialog(self):
        if self.progress_dialog:
            self.progress_dialog.destroy()
            self.progress_dialog = None
            self.progress_dialog_created = False
            self.update()

if __name__ == "__main__":
    #root = tk.Tk()
    #cv = StartCanvas(root)
    root = App('Socket', (WINDOW_WIDTH, WINDOW_HEIGHT))
    root.mainloop()
    #client_socket = connect_to_server('localhost', 6578)
    #communication = CommunicateToServer(client_socket)
    #communication.download_folder('folder1','C:\\Users\\thai\\Downloads\\testing')

        