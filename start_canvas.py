import socket
import os
import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
import time
import upload_gui
import client  # Add this line to import the client module

class StartCanvas:
    def __init__(self, master):
        self.master = master
        self.window_width = 1066
        self.window_height = 600
        
        self.master.title("Socket Programming Project")
        self.master.iconphoto(True, tk.PhotoImage(file='icon.png'))
        self.master.geometry(f"{self.window_width}x{self.window_height}")

        self.canvas = tk.Canvas(self.master, width=self.window_width, height=self.window_height)
        self.canvas.pack()

        self.load_background_image()
        self.create_start_button()

    def load_background_image(self):
        image_path = "intro.png"
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
            "button1.png", 
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
    def create_progress_window(self):
        img_width = 600
        img_height = 350

        self.loading_canvas = tk.Canvas(self.master, width=img_width, height=img_height)
        self.loading_canvas.place(relx=0.5, rely=0.5, anchor="center")

        try:
            self.loading_image = Image.open("D:\\gitclone\\Socket-Programming-Project\\loading.png")
            self.loading_image = self.loading_image.resize((img_width, img_height), Image.LANCZOS)
            self.loading_photo = ImageTk.PhotoImage(self.loading_image)

            self.loading_canvas.create_image(0, 0, anchor="nw", image=self.loading_photo)
            self.loading_canvas.image = self.loading_photo
        except FileNotFoundError:
            print("Error: Hình ảnh 'loading.png' không tìm thấy.")

        canvas_width, canvas_height = 600, 10
        self.progress_canvas = tk.Canvas(self.master, width=canvas_width, height=canvas_height)
        self.progress_canvas.place(relx=0.5, rely=0.8, anchor="center")

        self.percent_label = tk.Label(self.master, text="0%", font=("Courier New", 14, "bold"), bg="#ffffff", fg="#1c2554")
        self.percent_label.place(relx=0.75, rely=0.75, anchor="center")

        self.status_label = tk.Label(self.master, text="Uploading...", font=("Courier New", 14, "bold"), bg="#ffffff", fg="#1c2554")
        self.status_label.place(relx=0.66, rely=0.75, anchor="center")

        self.start_progress(self.progress_canvas, canvas_width, canvas_height)

    def start_progress(self, canvas, canvas_width, canvas_height):
        progress = {"value": 0}  

        def update_progress():
            if progress["value"] < 100: 
                progress["value"] += 1
                percent = progress["value"]
                canvas.delete("progress_bar")
                canvas.create_rectangle(0, 0, (percent * canvas_width) / 100, canvas_height, fill="green", tags="progress_bar")
                self.percent_label.config(text=f"{percent}%")
                canvas.after(50, update_progress) 
            else:
                self.status_label.config(text="Done!")
                self.show_new_image()

        update_progress()

    def show_new_image(self):
        self.loading_canvas.delete("all")

        try:
            new_image = Image.open("D:\\gitclone\\Socket-Programming-Project\\done.png")
            new_image = new_image.resize((600, 350), Image.LANCZOS)
            new_photo = ImageTk.PhotoImage(new_image)

            self.loading_canvas.create_image(0, 0, anchor="nw", image=new_photo)
            self.loading_canvas.image = new_photo
        except FileNotFoundError:
            print("Error: Hình ảnh 'done.png' không tìm thấy.")

        self.master.after(3000, self.clear_loading_canvas)

    def clear_loading_canvas(self):
        self.loading_canvas.destroy()
        self.progress_canvas.destroy()
        self.percent_label.destroy()
        self.status_label.destroy()
        
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
            "confirm.png", 
            width // 2, height // 2, 150, 
            command=lambda: [
                self.connect_to_server(ip_entries, entry_port),
            ]
        )
        self.canvas.create_window(width, height + 230, window=confirm_button, anchor="center")
        
    def connect_to_server(self, ip_entries, entry_port):
        # Get the IP and port values from the entries
        ip = '.'.join(entry.get() for entry in ip_entries)
        port = entry_port.get()

        if not all(ip.split('.')) or not port.isdigit():
            messagebox.showerror("Lỗi", "Vui lòng nhập đúng IP và Port!")
            return

        messagebox.showinfo("Kết nối", f"Đang kết nối tới {ip}:{port}...")

        # Use the connect_to_server from client.py
        client_socket = client.connect_to_server(ip, int(port))  # Ensure port is passed as an integer

        if client_socket:
            messagebox.showinfo("Kết nối thành công", "Kết nối tới server thành công!")
            self.master.destroy()
            # Create a new window for UploadGUI
            upload_window = tk.Tk()  # Create a new Tkinter window for Upload GUI
            upload_gui_instance = upload_gui.UploadGUI(upload_window)  # Create an instance of the UploadGUI
            upload_gui_instance.show()  # Show the Upload GUI
            upload_window.mainloop()  # Start the new window's event loop
        else:
            messagebox.showerror("Kết nối thất bại", "Không thể kết nối tới server.")


        
        
