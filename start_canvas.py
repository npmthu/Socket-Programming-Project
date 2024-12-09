import socket
import os
import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
import time

class start_canvas:
    def __init__(self, master):
        self.master = master
        self.window_width = 1066
        self.window_height = 600
        
        self.master.title("Socket Programming Project")
        self.master.iconphoto(True, tk.PhotoImage(file='D:\\gitclone\\Socket-Programming-Project\\icon.png'))
        self.master.geometry(f"{self.window_width}x{self.window_height}")

        self.canvas = tk.Canvas(self.master, width=self.window_width, height=self.window_height)
        self.canvas.pack()

        self.load_background_image()
        self.create_start_button()

    def load_background_image(self):
        image_path = "D:\\gitclone\\Socket-Programming-Project\\intro.png"
        try:
            image = Image.open(image_path)
            image = image.resize((self.window_width, self.window_height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            self.canvas.create_image(0, 0, anchor="nw", image=photo)
            self.canvas.image = photo  # Giữ tham chiếu tới ảnh để không bị xóa
        except FileNotFoundError:
            print("Error: Image file not found.")

    def create_start_button(self):
        button1 = self.display_image_button(
            "#953019", 
            "D:\\gitclone\\Socket-Programming-Project\\button1.png", 
            self.window_width // 2, 
            self.window_height // 2 + 150, 
            289, 
            command=lambda: [
                button1.destroy(),
                self.display_pin_input(self.window_width // 2, self.window_height // 2 + 150)
            ]
        )

    def display_image_button(self, bg_color, image_path, x, y, new_width, command=None):
        try:
            image = Image.open(image_path)
            original_width, original_height = image.size
            aspect_ratio = original_height / original_width
            new_height = int(new_width * aspect_ratio)
            image = image.resize((new_width, new_height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            button = tk.Button(
                self.master,
                image=photo,
                command=command,
                borderwidth=0,
                highlightthickness=0,
                relief="flat",
                bg="white",
                activebackground=bg_color
            )
            button.image = photo  # Giữ tham chiếu tới ảnh để không bị xóa
            self.canvas.create_window(x, y, window=button, anchor="center")
            return button
        except FileNotFoundError:
            print(f"Error: Hình ảnh '{image_path}' không tìm thấy.")

    def display_pin_input(self, width, height):
        entries = []
        for i in range(6):
            entry = tk.Entry(
                self.master,
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
            self.canvas.create_window(width - 125 + i * 50, height, window=entry, anchor="center")
            entries.append(entry)

        for i in range(5):
            entries[i].bind("<KeyRelease>", lambda event, cur=entries[i], next=entries[i + 1]: self.focus_next_entry(cur, next, 1))

        entries[5].bind("<KeyRelease>", lambda event: self.check_pin(entries))

        entries[0].focus_set()

    def focus_next_entry(self, current_entry, next_entry, num_digit):
        if len(current_entry.get()) == num_digit:
            next_entry.focus_set()

    def check_pin(self, entries):
        pin = ''.join(entry.get() for entry in entries)
        if pin == "123456":
            messagebox.showinfo("Đăng nhập thành công", "Chào mừng bạn đến với hệ thống!")
            for entry in entries:
                entry.destroy()  # Xóa ô nhập PIN
            self.display_ip_port_input(self.window_width // 2, self.window_height // 2)  # Hiển thị nhập IP/Port
        else:
            for entry in entries:
                entry.delete(0, 'end')  # Xóa nội dung các ô nhập
            messagebox.showerror("Đăng nhập thất bại", "Mã PIN không đúng!")
            entries[0].focus_set()

    def display_ip_port_input(self, width, height):
        IP_height = height + 110
        port_height = height + 160

        label_ip = tk.Label(self.master, text="IP:", font=("Courier New", 16, "bold"), bg="#953019", fg="#ffffff")
        self.canvas.create_window(width - 100, IP_height, window=label_ip, anchor="e")

        ip_entries = []
        for i in range(4):
            entry = tk.Entry(
                self.master,
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
            self.canvas.create_window(width - 30 + i * 60, IP_height, window=entry, anchor="center")
            ip_entries.append(entry)
        
        for i in range(3):
            ip_entries[i].bind("<KeyRelease>", lambda event, cur=ip_entries[i], next=ip_entries[i + 1]: self.focus_next_entry(cur, next, 3))

        for i in range(3):
            dot_label = tk.Label(self.master, text=".", font=("Courier New", 14, "bold"), bg="#953019", fg="#ffffff")
            self.canvas.create_window(width + i * 60, IP_height, window=dot_label, anchor="center")

        label_port = tk.Label(self.master, text="Port:", font=("Courier New", 16, "bold"), bg="#953019", fg="#ffffff")
        self.canvas.create_window(width - 80, port_height, window=label_port, anchor="e")

        entry_port = tk.Entry(
            self.master,
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
        self.canvas.create_window(width - 50, port_height, window=entry_port, anchor="w")

        confirm_button = self.display_image_button(
            "#953019", 
            "D:\\gitclone\\Socket-Programming-Project\\confirm.png", 
            width // 2, height // 2, 150, 
            command=lambda: [
                self.connect_to_server(ip_entries, entry_port),
            ]
        )
        self.canvas.create_window(width, height + 230, window=confirm_button, anchor="center")

    def connect_to_server(self, ip_entries, entry_port):
        ip = '.'.join(entry.get() for entry in ip_entries)
        port = entry_port.get()

        if not all(ip.split('.')) or not port.isdigit():
            messagebox.showerror("Lỗi", "Vui lòng nhập đúng IP và Port!")
            return

        messagebox.showinfo("Kết nối", f"Đang kết nối tới {ip}:{port}...")
        # Add more
        

def main():
    root = tk.Tk()
    app = start_canvas(root)
    root.mainloop()

if __name__ == "__main__":
    main()
