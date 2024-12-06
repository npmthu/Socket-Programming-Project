import socket
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter import Tk, Canvas, Button
from PIL import Image, ImageTk, ImageDraw
from io import BytesIO

window_width = 1066
window_height = 600
BUFFER_SIZE = 4096


# ---------------------------- Shared Logic ---------------------------- #

def upload_file(host, port, filepath):
    """
    Upload a single file to the server.
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return
    filename = os.path.basename(filepath)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            command = f"upload {filename}"
            sock.sendall(command.encode())
            response = sock.recv(BUFFER_SIZE).decode()
            if response == "READY":
                print(f"Uploading {filename}...")
                with open(filepath, 'rb') as f:
                    while True:
                        chunk = f.read(BUFFER_SIZE)
                        if not chunk:
                            break
                        sock.sendall(chunk)
                sock.sendall(b"DONE")
                final_response = sock.recv(BUFFER_SIZE).decode()
                print(f"Server response: {final_response}")
            else:
                print(f"Server response: {response}")
    except Exception as e:
        print(f"Error uploading {filename}: {e}")

def download_file(host, port, filename):
    """
    Download a single file from the server.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            command = f"download {filename}"
            sock.sendall(command.encode())
            response = sock.recv(BUFFER_SIZE).decode()
            if response.startswith("READY"):
                _, file_size = response.split()
                file_size = int(file_size)
                filepath = os.path.join(".", filename)
                with open(filepath, 'wb') as f:
                    bytes_received = 0
                    while True:
                        chunk = sock.recv(BUFFER_SIZE)
                        if not chunk:
                            break
                        if chunk.endswith(b"DONE"):
                            f.write(chunk[:-4])
                            break
                        f.write(chunk)
                        bytes_received += len(chunk)
                messagebox.showinfo("Download Complete", f"File {filename} downloaded successfully.")
            else:
                messagebox.showerror("Server Error", f"Server response: {response}")
    except Exception as e:
        messagebox.showerror("Error", f"Error downloading {filename}: {e}")


def upload_folder_sequential(host, port, folder_path):
    """
    Upload all files in a folder sequentially.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory.")
        return

    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    for file in files:
        print(f"Uploading file: {file}")
        upload_file(host, port, file)


def upload_folder_parallel(host, port, folder_path):
    """
    Upload all files in a folder in parallel using independent connections.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory.")
        return

    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    threads = []
    for file in files:
        thread = threading.Thread(target=upload_file, args=(host, port, file))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    print("All files uploaded in parallel.")


# ---------------------------- CLI Interface ---------------------------- #

def cli_interface():
    """
    CLI interface for interacting with the server.
    """
    host = input("Enter server host (e.g., 127.0.0.1): ").strip()
    port = int(input("Enter server port (e.g., 9999): ").strip())

    
    try:
        # Add main socket for client-server communication
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        while True:
            command = input("Enter command (upload <filename/folder>, download <filename>, exit): ").strip()

            if command == "exit":
                print("Exiting...")
                break

            elif command.startswith("upload"):
                _, filepath = command.split(" ", 1)

                if os.path.isdir(filepath):
                    print(f"Detected folder: {filepath}")
                    mode = input("Choose upload mode: sequential or parallel? ").strip().lower()
                    if mode == "sequential":
                        upload_folder_sequential(host, port, filepath)
                    elif mode == "parallel":
                        upload_folder_parallel(host, port, filepath)
                    else:
                        print("Invalid mode. Use 'sequential' or 'parallel'.")
                else:
                    upload_file(host, port, filepath)

            elif command.startswith("download"):
                _, filename = command.split(" ", 1)
                print(f"Downloading file: {filename}")
                # Add download logic here
            else:
                print("Invalid command. Use 'upload <filename/folder>', 'download <filename>', or 'exit'.")
    except Exception as e:
            print(f"Error: {e}")
            if 'sock' in locals():
                sock.close()

# ---------------------------- Helper Functions ---------------------------- #

def load_image(file_path, width=None, height=None):
    """
    Load and resize an image using Pillow.
    """
    try:
        image = Image.open(file_path)
        if width and height:
            image = image.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(image)
    except FileNotFoundError:
        print(f"Error: Image '{file_path}' not found.")
        return None

def focus_next_entry(current_entry, next_entry):
    """
    Move focus to the next entry when a digit is entered.
    """
    if len(current_entry.get()) == 1:
        next_entry.focus_set()

def connect_to_server(host, port, root):
    """
    Connect to the server and transition to the main app if successful.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, int(port)))
        messagebox.showinfo("Connection", f"Connected to {host}:{port}")
        # Clear the root and launch the main app
        for widget in root.winfo_children():
            widget.destroy()
        create_main_app(root, host, port)
    except Exception as e:
        messagebox.showerror("Connection Error", str(e))

# ---------------------------- Screens ---------------------------- #

def display_pin_input(root, canvas):
    """
    Display PIN input fields for validation.
    """
    entries = []
    for i in range(6):
        entry = tk.Entry(
            root,
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
        canvas.create_window(window_width // 2 - 125 + i * 50, window_height // 2, window=entry, anchor="center")
        entries.append(entry)

    for i in range(5):
        entries[i].bind("<KeyRelease>", lambda event, cur=entries[i], next=entries[i + 1]: focus_next_entry(cur, next))

    entries[5].bind("<KeyRelease>", lambda event: check_pin(root, entries, canvas))
    entries[0].focus_set()

def check_pin(root, entries, canvas):
    """
    Check PIN and transition to IP/Port input if valid.
    """
    pin = ''.join(entry.get() for entry in entries)
    if pin == "123456":  # Replace this with actual PIN validation logic
        messagebox.showinfo("Access Granted", "Welcome!")
        for entry in entries:
            entry.destroy()
        display_ip_port_input(root, canvas)
    else:
        for entry in entries:
            entry.delete(0, tk.END)
        messagebox.showerror("Access Denied", "Incorrect PIN!")
        entries[0].focus_set()

def display_ip_port_input(root, canvas):
    """
    Display input fields for server IP and port.
    """
    # Clear canvas for new content
    for widget in root.winfo_children():
        if isinstance(widget, tk.Entry) or isinstance(widget, tk.Button):
            widget.destroy()

    ip_label = tk.Label(root, text="IP:", font=("Courier New", 14, "bold"), fg="#333333", bg="white")
    canvas.create_window(window_width // 2 - 100, window_height // 2 - 50, window=ip_label, anchor="e")

    ip_entry = tk.Entry(root, font=("Courier New", 14), bg="#f5f5f5", fg="#333333")
    canvas.create_window(window_width // 2, window_height // 2 - 50, window=ip_entry, anchor="w")

    port_label = tk.Label(root, text="Port:", font=("Courier New", 14, "bold"), fg="#333333", bg="white")
    canvas.create_window(window_width // 2 - 100, window_height // 2, window=port_label, anchor="e")

    port_entry = tk.Entry(root, font=("Courier New", 14), bg="#f5f5f5", fg="#333333")
    canvas.create_window(window_width // 2, window_height // 2, window=port_entry, anchor="w")

    connect_button = tk.Button(
        root,
        text="Connect",
        font=("Courier New", 14),
        bg="#953019",
        fg="white",
        command=lambda: connect_to_server(ip_entry.get(), port_entry.get(), root),
    )
    canvas.create_window(window_width // 2, window_height // 2 + 50, window=connect_button)


## ---------------------------- GUI Interface ---------------------------- ##
def upload_action(host, port):
    """
    Action for uploading a file or folder.
    """
    file_path = filedialog.askopenfilename()
    folder_path = filedialog.askdirectory()
    
    mode = messagebox.askquestion("Upload Mode", "Upload sequentially?")
    if mode == "yes":
            upload_folder_sequential(host, port, folder_path)
    else:
            upload_folder_parallel(host, port, folder_path)


def download_action(host, port):
    """
    Action for downloading a file.
    """
    filename = filedialog.askopenfilename()
    if filename:
        download_file(host, port, filename)


def question_action():
    """
    Display a question dialog.
    """
    messagebox.showinfo("Question", "This is a placeholder for your questions.")


def upload_selected(tree, host, port):
    """
    Upload the selected file from the treeview.
    """
    selected_item = tree.selection()
    if selected_item:
        filename = tree.item(selected_item[0], "text")
        upload_file(host, port, filename)


def download_selected(tree, host, port):
    """
    Download the selected file from the treeview.
    """
    selected_item = tree.selection()
    if selected_item:
        filename = tree.item(selected_item[0], "text")
        download_file(host, port, filename)

def create_transparent_image(size, corner_radius, color, alpha):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))  # Fully transparent canvas
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (0, 0, size, size), radius=corner_radius, fill=(*color, alpha)
    )
    return ImageTk.PhotoImage(img) 
def blend_color(bg_color, fg_color, alpha):
        return tuple(
            int(bg * (1 - alpha) + fg * alpha) for bg, fg in zip(bg_color, fg_color)
        )
def create_squircle_hover_button(parent, image_path, x, y, size, corner_radius, command=None):
    """
    Create a squircle button with hover effect and an image inside.

    Parameters:
    - parent: Parent widget (e.g., a Frame or Canvas)
    - image_path: Path to the button's image
    - x, y: Coordinates for the button's placement
    - size: Size of the squircle (width and height, as it's square)
    - corner_radius: Radius of the squircle corners
    - command: Command to execute on click
    """

    # Initial colors and transparency
    color = (119, 137, 102)  # RGB color for #778966
    semi_transparent_alpha = 128  # 50% transparency
    opaque_alpha = 255  # Fully opaque
    
    # Create canvas to hold the squircle and image
    canvas = tk.Canvas(parent, width=size, height=size, bg="#893f34", highlightthickness=0)
    canvas.place(x=x, y=y, anchor="center")

    # Create semi-transparent and opaque squircle images
    semi_transparent_image = create_transparent_image(size, corner_radius, color, semi_transparent_alpha)
    opaque_image = create_transparent_image(size, corner_radius, color, opaque_alpha)

    # Add the squircle to the canvas
    squircle_id = canvas.create_image(0, 0, anchor="nw", image=semi_transparent_image)

    # Load and resize the button image
    try:
        img = Image.open(image_path).resize((size - 20, size - 20), Image.LANCZOS)
        button_image = ImageTk.PhotoImage(img)
    except FileNotFoundError:
        print(f"Error: Image '{image_path}' not found.")
        return None

    # Add the button with the image
    button = tk.Button(
        canvas,
        image=button_image,
        command=command,
        borderwidth=0,
        highlightthickness=0,
        relief="flat",
        bg="#778966",
        activebackground="#893f34",
    )
    button.image = button_image  # Prevent garbage collection
    button.place(relx=0.5, rely=0.5, anchor="center")

    # Hover effect
    def on_enter(event):
        canvas.itemconfig(squircle_id, image=opaque_image)  # Switch to opaque image

    def on_leave(event):
        canvas.itemconfig(squircle_id, image=semi_transparent_image)  # Revert to semi-transparent

    # Bind hover events
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

    # Save references to prevent garbage collection
    canvas.semi_transparent_image = semi_transparent_image
    canvas.opaque_image = opaque_image

    return canvas

def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    points = [
        x1 + radius, y1,
        x1 + radius, y1,
        x2 - radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1 + radius,
        x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

def create_main_app(root, host, port):
    """
    Create the main app with functionality to upload/download files.
    """
    root.title("Main Application")
    root.geometry("1066x600")
    root.configure(bg="#f4ebd5")  # Set the background color for the main app

    # Create the canvas for rounded rectangle
    canvas = tk.Canvas(root, bg="#f4ebd5", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # Draw the rounded rectangle for the right column
    x1, y1, x2, y2 = 150, 50, 1100, 600
    create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=30, fill="#893f34")

    #Create a frame outside the rounded rectangle to place widgets
    left_frame = tk.Frame(root, bg="#f4ebd5")
    left_frame.place(x=20, y=50, width=100, height=560)

    # Create a frame inside the rounded rectangle to place widgets
    right_frame = tk.Frame(root, bg="#893f34")
    right_frame.place(x=150, y=50, width=850, height=500)

    # Load button icons
    upload_icon = tk.PhotoImage(file="upload.png")  # Replace with actual icon paths
    download_icon = tk.PhotoImage(file="download.png")
    question_icon = tk.PhotoImage(file="question.png")
    exit_icon = tk.PhotoImage(file="exit.png")

    # Add buttons in the frame, spaced vertically
    button_upload = tk.Button(
        left_frame, image=upload_icon, command=lambda: upload_action(host, port),
        borderwidth=0, highlightthickness=0, relief="flat", bg="#893f34", activebackground="#893f34"
    )
    button_upload.pack(anchor="w", pady=30)  # Align buttons to the left and space vertically

    button_download = tk.Button(
        left_frame, image=download_icon, command=lambda: download_action(host, port),
        borderwidth=0, highlightthickness=0, relief="flat", bg="#893f34", activebackground="#893f34"
    )
    button_download.pack(anchor="w", pady=30)

    button_question = tk.Button(
        left_frame, image=question_icon, command=question_action,
        borderwidth=0, highlightthickness=0, relief="flat", bg="#893f34", activebackground="#893f34"
    )
    button_question.pack(anchor="w", pady=30)

    button_exit = tk.Button(
        left_frame, image=exit_icon, command=root.destroy,
        borderwidth=0, highlightthickness=0, relief="flat", bg="#893f34", activebackground="#893f34"
    )
    button_exit.pack(anchor="w", pady=30)

    # Add the squircle button to the frame
    create_squircle_hover_button(
        right_frame,
        "upload_hover.png",
        x=120,
        y=120,
        size=200,
        corner_radius=25,
        command=lambda: upload_action(host, port),
    )

    # Keep the reference for images to avoid garbage collection
    root.image_refs = [upload_icon, download_icon, question_icon, exit_icon]

    root.mainloop()



# ---------------------------- Main ---------------------------- #

def main():
    """
    Entry point for the application.
    """
    root = tk.Tk()
    root.title("Socket Programming Project")
    root.geometry(f"{window_width}x{window_height}")

    # Load intro background image
    canvas = tk.Canvas(root, width=window_width, height=window_height)
    canvas.pack()

    bg_image = load_image("intro.png", window_width, window_height)
    if bg_image:
        canvas.create_image(0, 0, anchor="nw", image=bg_image)
        root.image_refs = [bg_image]

    # Add confirm button for PIN entry
    confirm_button = tk.Button(
        root,
        text="Confirm",
        font=("Courier New", 16),
        bg="#953019",
        fg="white",
        command=lambda: display_pin_input(root, canvas),
    )
    canvas.create_window(window_width//2, window_height//2, window=confirm_button)

    root.mainloop()

if __name__ == "__main__":
    cli_interface()
    #main()