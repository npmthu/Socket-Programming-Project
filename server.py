import socket
import threading
import os

UPLOAD_DIR = "uploads"

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            command, *args = data.split()

            if command == "upload":
                filename = args[0]
                unique_name = generate_unique_filename(filename)
                with open(os.path.join(UPLOAD_DIR, unique_name), 'wb') as f:
                    while True:
                        chunk = conn.recv(1024)
                        if chunk == b"DONE":
                            break
                        f.write(chunk)
                conn.send(b"Upload complete.")
            elif command == "download":
                filename = args[0]
                filepath = os.path.join(UPLOAD_DIR, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        while chunk := f.read(1024):
                            conn.send(chunk)
                    conn.send(b"DONE")
                else:
                    conn.send(b"Error: File not found.")
            else:
                conn.send(b"Error: Invalid command.")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

def generate_unique_filename(filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    unique_name = filename
    while os.path.exists(os.path.join(UPLOAD_DIR, unique_name)):
        unique_name = f"{base}_{counter}{ext}"
        counter += 1
    return unique_name

def start_server(host, port):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[LISTENING] Server is listening on {host}:{port}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

start_server("127.0.0.1", 9999)
