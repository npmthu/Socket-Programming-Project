import socket
import threading
import os
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

UPLOAD_DIR = "uploads"
BUFFER_SIZE = 4096  # Increased buffer size for efficiency


class ServerLogger:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def log(self, message):
        """
        Log messages to the GUI and the console.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.text_widget.insert(tk.END, log_message)
        self.text_widget.see(tk.END)  # Auto-scroll to the latest message
        print(log_message, end="")  # Still log to the console


def sanitize_filename(filename):
    """
    Prevent path traversal by extracting the base name of the file.
    """
    return os.path.basename(filename)


def generate_unique_filename(filename):
    """
    Generate a unique filename by appending a timestamp.
    """
    base, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    unique_name = f"{base}_{timestamp}{ext}"
    return unique_name

def handle_upload(conn, filename, logger):
    filepath = os.path.join(UPLOAD_DIR, generate_unique_filename(filename))
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    conn.send(b"READY")  # Notify the client to start sending the file
    total_received = 0  # Track total bytes received
    try:
        with open(filepath, "wb") as f:
            while True:
                chunk = conn.recv(BUFFER_SIZE)
                chunk_size = len(chunk)
                total_received += chunk_size
                logger.log(f"Received chunk: {chunk_size} bytes (Total: {total_received} bytes)")
                if chunk.endswith(b"DONE"):
                    f.write(chunk[:-4])  # Write everything except the 'DONE' marker
                    break
                f.write(chunk)
        logger.log(f"File {filepath} uploaded successfully.")
        conn.send(b"UPLOAD_SUCCESS")
    except Exception as e:
        logger.log(f"Error during upload: {e}")
        conn.send(b"UPLOAD_FAILED")
def handle_download(conn, filename, logger):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        logger.log(f"File not found for download: {filename}")
        conn.send(b"ERROR: File not found.")
        return

    total_sent = 0  # Track total bytes sent
    try:
        file_size = os.path.getsize(filepath)
        conn.send(f"READY {file_size}".encode())  # Notify client of file size
        with open(filepath, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                chunk_size = len(chunk)
                total_sent += chunk_size
                conn.send(chunk)
                logger.log(f"Sent chunk: {chunk_size} bytes (Total: {total_sent} bytes)")
        conn.send(b"DONE")  # Indicate end of file transfer
        logger.log(f"File {filename} sent successfully.")
    except Exception as e:
        logger.log(f"Error during download: {e}")
        conn.send(b"DOWNLOAD_FAILED")


def handle_client(conn, addr, logger, update_connections):
    """
    Handle a single client connection.
    """
    logger.log(f"[NEW CONNECTION] {addr} connected.")
    update_connections(1)  # Increment active connections
    try:
        while True:
            data = conn.recv(BUFFER_SIZE).decode().strip()
            if not data:
                logger.log(f"[DISCONNECT] {addr} disconnected.")
                break

            command_parts = data.split(" ", 1)
            command = command_parts[0].lower()
            if command == "upload" and len(command_parts) == 2:
                filename = sanitize_filename(command_parts[1])
                handle_upload(conn, filename, logger)
            elif command == "download" and len(command_parts) == 2:
                filename = sanitize_filename(command_parts[1])
                handle_download(conn, filename, logger)
            elif command == "exit":
                logger.log(f"[EXIT] {addr} requested to disconnect.")
                conn.send(b"GOODBYE")
                break
            else:
                conn.send(b"ERROR: Invalid command. Use 'upload <filename>', 'download <filename>', or 'exit'.")
    except Exception as e:
        logger.log(f"Error handling client {addr}: {e}")
    finally:
        conn.close()
        logger.log(f"[CLOSED] Connection with {addr} closed.")
        update_connections(-1)  # Decrement active connections


def start_server_gui(logger, update_connections, host="127.0.0.1", port=9999):
    """
    Start the server and accept incoming client connections.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    def run_server():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow port reuse
        try:
            server.bind((host, port))
            server.listen(100)
            logger.log(f"[LISTENING] Server is listening on {host}:{port}")

            while True:
                conn, addr = server.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr, logger, update_connections), daemon=True)
                thread.start()
                logger.log(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        except Exception as e:
            logger.log(f"[ERROR] Server encountered an error: {e}")
        finally:
            server.close()
            logger.log("[CLOSED] Server socket closed.")

    threading.Thread(target=run_server, daemon=True).start()


def create_gui():
    """
    Create the GUI for the server.
    """
    root = tk.Tk()
    root.title("Server Management")

    # Log display
    log_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
    log_text.pack(padx=10, pady=10)

    # Logger instance
    logger = ServerLogger(log_text)

    # Active connections label
    connections_label = tk.Label(root, text="Active Connections: 0", font=("Helvetica", 12))
    connections_label.pack(pady=5)

    # Server address label
    address_label = tk.Label(root, text="Server Address: Not started", font=("Helvetica", 12))
    address_label.pack(pady=5)

    active_connections = 0

    def update_connections(change):
        nonlocal active_connections
        active_connections += change
        connections_label.config(text=f"Active Connections: {active_connections}")

    # Start the server
    def start_server():
        host = "127.0.0.1"
        port = 9999
        address_label.config(text=f"Server Address: {host}:{port}")
        start_server_gui(logger, update_connections, host, port)

    start_button = tk.Button(root, text="Start Server", command=start_server)
    start_button.pack(pady=10)

    # Exit button
    exit_button = tk.Button(root, text="Exit", command=root.destroy)
    exit_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    create_gui()
