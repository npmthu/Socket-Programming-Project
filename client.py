import socket
import os
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image
from rembg import remove
from io import BytesIO


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


def button_function():
    print("Button clicked! Start doing something...")


def focus_next_entry(current_entry, next_entry):
    """Di chuyển con trỏ sang ô tiếp theo nếu người dùng đã nhập một ký tự."""
    if len(current_entry.get()) == 1:
        next_entry.focus_set()

def display_pin_input(canvas, window_width, window_height):
    # Tọa độ trung tâm màn hình
    center_x, center_y = window_width // 2, window_height // 2 - 50

    # Tạo danh sách các ô nhập liệu
    entries = []
    for i in range(6):
        entry = tk.Entry(
            canvas.master,
            width=2,
            font=("Courier New", 24),
            justify="center",
            bg="#f5f5f5",
            fg="#333333",
            highlightthickness=2,
            highlightbackground="#cccccc",
            highlightcolor="#007BFF",
            relief="flat",
        )
        canvas.create_window(center_x - 150 + i * 50, center_y, window=entry, anchor="center")
        entries.append(entry)

    # Liên kết các ô nhập liệu
    for i in range(5):
        entries[i].bind("<KeyRelease>", lambda event, cur=entries[i], next=entries[i + 1]: focus_next_entry(cur, next))

    # Kiểm tra mã PIN sau khi nhập đủ
    entries[5].bind("<KeyRelease>", lambda event: check_pin(entries, canvas))

    # Đặt con trỏ vào ô đầu tiên
    entries[0].focus_set()
    
def connect_to_server(entry_ip, entry_port):
    """Kết nối tới server với IP và Port người dùng nhập."""
    ip = entry_ip.get()
    port = entry_port.get()

    if not ip or not port.isdigit():
        messagebox.showerror("Lỗi", "Vui lòng nhập đúng IP và Port!")
        return

    messagebox.showinfo("Kết nối", f"Đang kết nối tới {ip}:{port}...")
    # Ở đây bạn có thể thêm logic kết nối socket
        
def display_ip_port_input(canvas, window_width, window_height):
    center_x, center_y = window_width // 2, window_height // 2

    # IP
    label_ip = tk.Label(canvas.master, text="IP:", font=("Courier New", 14, "bold"), fg="#333333")
    canvas.create_window(center_x - 80, center_y - 50, window=label_ip, anchor="e")

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
    canvas.create_window(center_x - 30, center_y - 50, window=entry_ip, anchor="w")

    label_port = tk.Label(canvas.master, text="Port:", font=("Courier New", 14, "bold"), fg="#333333")
    canvas.create_window(center_x - 80, center_y, window=label_port, anchor="e")

    # Port
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
    canvas.create_window(center_x - 30, center_y, window=entry_port, anchor="w")

    # Nút xác nhận
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
    canvas.create_window(center_x, center_y + 70, window=confirm_button, anchor="center")
        
def check_pin(entries, canvas):
    pin = ''.join(entry.get() for entry in entries)
    if pin == "123456":
        messagebox.showinfo("Đăng nhập thành công", "Chào mừng bạn đến với hệ thống!")
        # Xóa giao diện mã PIN
        for entry in entries:
            entry.destroy()  

        # Hiển thị giao diện nhập IP và Port
        display_ip_port_input(canvas, 1000, 600)
    else:
        # Xóa các ký tự đã nhập và thông báo lỗi
        for entry in entries:
            entry.delete(0, 'end')  # Xóa nội dung các ô nhập
        messagebox.showerror("Đăng nhập thất bại", "Mã PIN không đúng!")
        entries[0].focus_set()
        
    
def main():

    window = tk.Tk()
    window.title("Socket Programming Project")
    window.iconphoto(True, tk.PhotoImage(file='D:\\gitclone\\Socket-Programming-Project\\icon.png'))
    window.geometry("1000x600")
    
    # Sử dụng canvas để tạo nền và đặt các widget lên trên
    canvas = tk.Canvas(window, width=1000, height=600)
    canvas.pack()

    # Tải hình nền
    image_path = "D:\\gitclone\\Socket-Programming-Project\\wallpaper.jpg"
    try:
        image = Image.open(image_path)
        image = image.resize((1000, 600), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)

        # Vẽ nền lên canvas
        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.image = photo  # Giữ tham chiếu tới ảnh để không bị xóa

    except FileNotFoundError:
        print("Error: Image file not found.")
    
    display_pin_input(canvas, 1000, 600)
    
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
