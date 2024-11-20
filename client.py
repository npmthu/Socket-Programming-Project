import socket
import os

def upload_file(sock, filepath):
    if not os.path.exists(filepath):
        print("Error: File not found.")
        return
    sock.send(f"upload {os.path.basename(filepath)}".encode())
    with open(filepath, 'rb') as f:
        while chunk := f.read(1024):
            sock.send(chunk)
    sock.send(b"DONE")
    response = sock.recv(1024).decode()
    print(response)

def download_file(sock, filename):
    sock.send(f"download {filename}".encode())
    with open(filename, 'wb') as f:
        while True:
            chunk = sock.recv(1024)
            if chunk == b"DONE":
                break
            f.write(chunk)
    print("Download complete.")

def main():
    host, port = "127.0.0.1", 9999
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))
        while True:
            command = input("> ")
            if command.startswith("upload "):
                upload_file(client, command.split()[1])
            elif command.startswith("download "):
                download_file(client, command.split()[1])
            elif command == "exit":
                break
            else:
                print("Unknown command.")

main()