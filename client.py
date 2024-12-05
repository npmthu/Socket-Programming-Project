import socket
import os
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image
from io import BytesIO

window_width = 1066
window_height = 600

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
    

def focus_next_entry(current_entry, next_entry):
    if len(current_entry.get()) == 1:
        next_entry.focus_set()

def display_pin_input(canvas, width, height):
    entries = []
    for i in range(6):
        entry = tk.Entry(
            canvas.master,
            width=2, 
            font=("Courier New", 30),
            justify="center",
            bg="#f5f5f5",
            fg="#333333",
            highlightthickness=2,
            highlightbackground="#cccccc",
            highlightcolor="#007BFF",
            relief="flat",
        )
        canvas.create_window(width - 125 + i * 50, height, window=entry, anchor="center")
        entries.append(entry)

    for i in range(5):
        entries[i].bind("<KeyRelease>", lambda event, cur=entries[i], next=entries[i + 1]: focus_next_entry(cur, next))

    entries[5].bind("<KeyRelease>", lambda event: check_pin(entries, canvas))

    entries[0].focus_set()

def display_image_button(canvas, bg_color, image_path, x, y, width, height, command=None):
    try:
        # Tải và chỉnh kích thước hình ảnh
        image = Image.open(image_path)
        image = image.resize((width, height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        
        # Tạo nút là hình ảnh
        button = tk.Button(
            canvas.master,
            image=photo,
            command=command,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            bg="white",  # Nền có thể tùy chỉnh
            activebackground=bg_color  # Màu nền khi nhấn nút
        )
        button.image = photo  # Giữ tham chiếu tới ảnh để không bị xóa
        
        # Vẽ nút trên canvas
        canvas.create_window(x, y, window=button, anchor="center")
        return button

    except FileNotFoundError:
        print(f"Error: Hình ảnh '{image_path}' không tìm thấy.")
 
def connect_to_server(entry_ip, entry_port):
    """Kết nối tới server với IP và Port người dùng nhập."""
    ip = entry_ip.get()
    port = entry_port.get()

    if not ip or not port.isdigit():
        messagebox.showerror("Lỗi", "Vui lòng nhập đúng IP và Port!")
        return

    messagebox.showinfo("Kết nối", f"Đang kết nối tới {ip}:{port}...")
    # Thêm logic kết nối socket vao day
        
def display_ip_port_input(canvas, width, height):
    # IP Label
    label_ip = tk.Label(canvas.master, text="IP:", font=("Courier New", 14, "bold"), fg="#333333")
    canvas.create_window(width - 80, height - 50, window=label_ip, anchor="e")

    # IP Entry
    entry_ip = tk.Entry(
        canvas.master,
        width=20,
        font=("Courier New", 14),
        justify="left",
        bg="#f5f5f5",
        fg="#333333",
        highlightthickness=2,
        highlightbackground="#cccccc",
        highlightcolor="#007BFF",
        relief="flat",
    )
    canvas.create_window(width - 30, height - 50, window=entry_ip, anchor="w")

    # Port Label
    label_port = tk.Label(canvas.master, text="Port:", font=("Courier New", 14, "bold"), fg="#333333")
    canvas.create_window(width - 80, height, window=label_port, anchor="e")

    # Port Entry
    entry_port = tk.Entry(
        canvas.master,
        width=20,
        font=("Courier New", 14),
        justify="left",
        bg="#f5f5f5",
        fg="#333333",
        highlightthickness=2,
        highlightbackground="#cccccc",
        highlightcolor="#007BFF",
        relief="flat",
    )
    canvas.create_window(width - 30, height, window=entry_port, anchor="w")

    # Confirm Button
    confirm_button = tk.Button(
        canvas.master,
        text="CONFIRM",
        font=("Courier New", 14, "bold"),
        fg="white",
        bg="#007BFF",
        activebackground="#0056b3",
        activeforeground="white",
        relief="flat",
        command=lambda: connect_to_server(entry_ip, entry_port),
    )
    canvas.create_window(width, height + 70, window=confirm_button, anchor="center")
        
def check_pin(entries, canvas):
    pin = ''.join(entry.get() for entry in entries)
    if pin == "123456":
        messagebox.showinfo("Đăng nhập thành công", "Chào mừng bạn đến với hệ thống!")
        for entry in entries:
            entry.destroy()  # Xóa ô nhập PIN
        display_ip_port_input(canvas, window_width // 2, window_height // 2)  # Hiển thị nhập IP/Port
    else:
        for entry in entries:
            entry.delete(0, 'end')  # Xóa nội dung các ô nhập
        messagebox.showerror("Đăng nhập thất bại", "Mã PIN không đúng!")
        entries[0].focus_set()
  
    
def main():
    window = tk.Tk()
    window.title("Socket Programming Project")
    window.iconphoto(True, tk.PhotoImage(file='D:\\gitclone\\Socket-Programming-Project\\icon.png'))
    window.geometry("1066x600")
    
    canvas = tk.Canvas(window, width=window_width, height=window_height)
    canvas.pack()

    # Tải hình nền
    image_path = "D:\\gitclone\\Socket-Programming-Project\\intro.png"
    try:
        image = Image.open(image_path)
        image = image.resize((window_width, window_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.image = photo  # Giữ tham chiếu tới ảnh để không bị xóa

    except FileNotFoundError:
        print("Error: Image file not found.")
        
    button1 = display_image_button(
        canvas, "#953019", 
        "D:\\gitclone\\Socket-Programming-Project\\button1.png", 
        window_width//2, window_height//2 + 150, 289, 101, 
        command=lambda: [
            button1.destroy(),  
            display_pin_input(canvas, window_width//2, window_height//2 + 150)
        ]
    )
    
    # Kết nối socket
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
