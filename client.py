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
    

def focus_next_entry(current_entry, next_entry, num_digit):
    if len(current_entry.get()) == num_digit:
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
        entries[i].bind("<KeyRelease>", lambda event, cur=entries[i], next=entries[i + 1]: focus_next_entry(cur, next,1))

    entries[5].bind("<KeyRelease>", lambda event: check_pin(entries, canvas))

    entries[0].focus_set()

def display_image_button(canvas, bg_color, image_path, x, y, new_width, command=None):
    try:
        image = Image.open(image_path)
        
        original_width, original_height = image.size
        aspect_ratio = original_height / original_width
        new_height = int(new_width * aspect_ratio)
        
        image = image.resize((new_width, new_height), Image.LANCZOS)
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
 
def connect_to_server(ip_entries, entry_port):
    # Kết hợp các giá trị từ các trường nhập IP
    ip = '.'.join(entry.get() for entry in ip_entries)
    port = entry_port.get()

    # Kiểm tra tính hợp lệ của IP và Port
    if not all(ip.split('.')) or not port.isdigit():
        messagebox.showerror("Lỗi", "Vui lòng nhập đúng IP và Port!")
        return

    # Hiển thị thông báo kết nối
    messagebox.showinfo("Kết nối", f"Đang kết nối tới {ip}:{port}...")
    # Thêm logic kết nối socket tại đây
    
def display_ip_port_input(canvas, width, height):
    IP_height = height + 110
    port_height = height + 160
    def get_full_ip(entries):
        return '.'.join(entry.get() for entry in entries)
    
    # IP Label
    label_ip = tk.Label(canvas.master, text="IP:", font=("Courier New",16, "bold"), bg = "#953019", fg="#ffffff")
    canvas.create_window(width - 100, IP_height, window=label_ip, anchor="e")
    
    # Tạo các ô nhập cho địa chỉ IP
    ip_entries = []
    for i in range(4):
        entry = tk.Entry(
            canvas.master,
            width=3, 
            font=("Courier New", 14),
            justify="center",
            bg="#f5f5f5",
            fg="#333333",
            highlightthickness=2,
            highlightbackground="#cccccc",
            highlightcolor="#007BFF",
            relief="flat",
        )
        canvas.create_window(width - 30 + i * 60, IP_height, window=entry, anchor="center")
        ip_entries.append(entry)
    
    # Tự động chuyển qua ô tiếp theo khi nhập đủ 3 chữ số
    for i in range(3):
        ip_entries[i].bind("<KeyRelease>", lambda event, cur=ip_entries[i], next=ip_entries[i + 1]: focus_next_entry(cur, next,3))
    
    # Tạo dấu chấm giữa các ô nhập IP
    for i in range(3):
        dot_label = tk.Label(canvas.master, text=".", font=("Courier New", 14, "bold"), bg="#953019", fg="#ffffff")
        canvas.create_window(width + i * 60, IP_height, window=dot_label, anchor="center")
        
    # Port label
    label_port = tk.Label(canvas.master, text="Port:", font=("Courier New",16, "bold"), bg = "#953019", fg="#ffffff")
    canvas.create_window(width - 80, port_height, window=label_port, anchor="e")
    
    # Port insert
    entry_port = tk.Entry(
        canvas.master,
        width=19,
        font=("Courier New", 14),
        justify="left",
        bg="#f5f5f5",
        fg="#333333",
        highlightthickness=2,
        highlightbackground="#cccccc",
        highlightcolor="#007BFF",
        relief="flat",
    )
    canvas.create_window(width -50, port_height, window=entry_port, anchor="w")
    
    # Confirm Button
    confirm_button = display_image_button(
        canvas, "#953019", 
        "D:\\gitclone\\Socket-Programming-Project\\confirm.png", 
        window_width//2, window_height//2, 150, 
        command=lambda: connect_to_server(ip_entries, entry_port)
    )
    canvas.create_window(width, height + 230, window=confirm_button, anchor="center")
        
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
        window_width//2, window_height//2 + 150, 289, 
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
