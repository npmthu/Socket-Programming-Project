import tkinter as tk
import os
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import filedialog

history = []
path = "/"

class UploadGUI:
    def __init__(self, parent):
        # Parent layout for the upload functionality
        self.upload_frame = tk.Frame(parent, background='#953019')
        self.upload_frame.pack(expand=True)  # Main parent frame
        # Left panel with image and buttons
        self.left_panel = tk.Frame(self.upload_frame, width=200, background='#953019')
        self.left_panel.pack(side='left', fill='y')
        
        # Add image to the left panel
        self.image_label = tk.Label(self.left_panel, bg='#953019')
        self.image_label.pack(pady=10)
        
        self.load_image('pine.png')  # Replace with your image path
        icon_paths = ['upload_icon.png', 'download_icon.png', 'help_icon.png', 'exit_icon.png']  # Replace with actual icon paths
        button_names = ['UPLOAD', 'DOWNLOAD', 'HELP', 'EXIT']
        for btn_text, icon_path in zip(button_names, icon_paths):
            btn = ctk.CTkButton(
                self.left_panel, 
                text=btn_text,
                fg_color='#f4ebd5',
                hover_color='#778966',
                text_color='#3f5a33',
                font = ('League Spartan', 20, 'bold'),
                image=self.load_button_icon(icon_path),
                command=lambda t=btn_text: self.handle_left_button(t),
                height=60  # Make buttons thicker
            )
            btn.pack(pady=10, padx=10, fill='x')

        # Function frame (top of the parent frame)
        self.upload_function_frame = ctk.CTkFrame(self.upload_frame, fg_color='#4b663a', height=50)
        self.upload_function_frame.pack(side='top', fill='x')
        self.upload_function_frame.pack_propagate(False)  # Prevent resizing based on children

        # Scrollable frame for dynamic content (below the function frame)
        self.upload_display_frame = ctk.CTkScrollableFrame(
            self.upload_frame, fg_color='#f4ebd5', width=950, height=450
        )
        self.upload_display_frame.pack(side='top', expand=True)

        
        # Add static buttons
        self.back_button = ctk.CTkButton(
            self.upload_function_frame,
            text="BACK",
            text_color='#778966',
            fg_color='#f4ebd5',
            hover_color='#e9d2b0',
            font=('League Spartan', 20, 'bold'),
            command=self.clicked_back_button,
        )
        self.back_button.pack(side='left', padx=10)

        self.refresh_button = ctk.CTkButton(
            self.upload_function_frame,
            text="REFRESH",
            text_color='#778966',
            fg_color='#f4ebd5',
            font=('League Spartan', 20, 'bold'),
            hover_color='#e9d2b0',
            command=self.clicked_refresh_button,
        )
        self.refresh_button.pack(side='left', padx=10)

        # Directory and file labels
        self.file_dictionary_variable = ctk.StringVar()
        self.file_dictionary_variable.set('/')
        directory_label = ctk.CTkLabel(
            self.upload_function_frame, textvariable=self.file_dictionary_variable
        )
        directory_label.pack(side='left', fill='x', padx=20)

        self.selected_file_label = ctk.CTkLabel(
            self.upload_function_frame, text="No file selected"
        )
        self.selected_file_label.pack(side='left', padx=10)
        create_buttons(self.upload_display_frame, file_dictionary, '/')

        
    def load_image(self, path):
        """Load and display an image in the left panel."""
        try:
            image = Image.open(path)
            image = image.resize((150, 150))
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
        except Exception as e:
            print(f"Error loading image: {e}")

    def load_button_icon(self, path):
        """Load an image for the button icon."""
        try:
            img = Image.open(path)
            img = img.resize((40, 40))  # Adjust icon size inside the button
            return ImageTk.PhotoImage(img)
        except FileNotFoundError:
            print(f"Error loading icon image: {path}")
            return None
        
    def handle_left_button(self, button_name):
        """Handle actions for buttons on the left panel."""
        if button_name == 'Exit':
            print("Exiting application...")
            exit()
        elif button_name == 'Help':
            print("Displaying help...")
        elif button_name == 'Download':
            clicked_download_button()
        elif button_name == 'Upload':
            self.clicked_upload_button()

    def show(self):
        """Display the upload frame."""
        self.upload_frame.pack(expand=True, fill='both')

    def hide(self):
        """Hide the upload frame."""
        self.upload_frame.pack_forget()
    def clicked_upload_button(self):
        folder_path = self.browse_folder()
        if folder_path:
            # Ask user to choose upload mode (sequential or parallel)
            upload_mode = self.ask_upload_mode()
            
            if upload_mode == "Sequential":
                # Sequential upload
                save_path = '/desired/save/path'  # Define save path on server or local
               # upload_folder_sequential(folder_path, save_path)
            elif upload_mode == "Parallel":
                # Parallel upload
                host = "127.0.0.1"  # Example: Replace with actual server host
                port = 9999          # Example: Replace with actual server port
                # upload_folder_parallel(host, port, folder_path)

    def ask_upload_mode(self):
        """Ask the user to choose the upload mode: sequential or parallel."""
        modes = ["Sequential", "Parallel"]
        mode = filedialog.askstring("Select Upload Mode", "Choose upload mode:\n1. Sequential\n2. Parallel")
        if mode in modes:
            return mode
        else:
            print("Invalid mode selected")
            return None

    def clicked_back_button(self):
        go_back(self.upload_display_frame, file_dictionary)

    def clicked_refresh_button(self):
        print("Refresh button clicked")
    
    # Reset or reload the file display (for instance, clearing selected file label)
        self.selected_file_label.configure(text="No file selected")
    
    # Here you can implement additional logic to reload the files for upload.
    # For example, refresh the file list (if the file structure is dynamic):
        self.refresh_file_list()

def refresh_file_list(self):
    """Logic to reload or refresh the file list for uploading."""
    print("Refreshing file list...")
    
    # Clear current file display content
    for widget in self.upload_display_frame.winfo_children():
        widget.destroy()

    # Re-create file/folder buttons (or any dynamic UI elements)
    create_buttons(self.upload_display_frame, file_dictionary, '/')

def clicked_download_button():
    print(f"download button clicked, path now is: {path}")

def delete_to_penultimate_slash():
    global path
    # Find the index of the last '/'
    last_slash_index = path.rfind('/')
    
    if last_slash_index != -1:
        # Slice the path up to the penultimate '/'
        path = path[:last_slash_index]
        # Find the new last '/'
        penultimate_slash_index = path.rfind('/')
        if penultimate_slash_index != -1:
            # Slice the path up to and including the penultimate '/'
            path = path[:penultimate_slash_index + 1]
        else:
            # If there's no more '/', reset path to root '/'
            path = '/'  

def clicked_folder_button(scrollable_frame, file_structure, parent, current_folder):
    global history
    global path
    global file_dictionary_variable

    history += [parent]

     # Check if the path ends with '/'
    if not path.endswith('/'):
        # Find the last '/' in the path
        last_slash_index = path.rfind('/')
        # Retain only the part of the path up to the last '/'
        if last_slash_index != -1:
            path = path[:last_slash_index + 1]
        else:
            # If no '/' is found, reset the path to just '/'
            path = '/'
    path = path + current_folder + '/'
    print(f"folder {parent} clicked, history now is: {history}")
    file_dictionary_variable.set(path)
    create_buttons(scrollable_frame, file_structure, current_folder)

def clicked_file_button(file_name):
    global path
    global file_dictionary_variable
    global path
     # Check if the path ends with '/'
    if not path.endswith('/'):
        # Find the last '/' in the path
        last_slash_index = path.rfind('/')
        # Retain only the part of the path up to the last '/'
        if last_slash_index != -1:
            path = path[:last_slash_index + 1]
        else:
            # If no '/' is found, reset the path to just '/'
            path = '/'
    path = path + file_name
    file_dictionary_variable.set(path)
    print(f"File clicked: {path}")

def create_root_button(scrollable_frame, file_dictionary):
    for widget in scrollable_frame.winfo_children():
        widget.destroy()
    button = ctk.CTkButton(
                scrollable_frame,
                text=f"ROOT/",
                width=200,
                height=150,
                corner_radius=10,
                fg_color="lightblue",
                text_color="white",
                command=lambda sub_structure=file_dictionary: create_buttons(scrollable_frame, sub_structure, parent = "")  
            )
    button.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

def create_buttons(scrollable_frame, file_structure, parent = ""):
    # Clear previous content from scrollable frame
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    row, col, max_cols = 0, 0, 4  # Display 4 items per row

    # Create buttons for files and folders
    for name, content in file_structure.items():
        if col >= max_cols:
            col = 0
            row += 1

        # If it's a file, create a file button
        if content is None:
            button = ctk.CTkButton(
                scrollable_frame,
                text=name,
                width=200,
                height=150,
                corner_radius=10,
                fg_color="lightgreen",
                text_color="white",
                command=lambda file_name = name : clicked_file_button(file_name), 
            )
        
        # If it's a folder, create a folder button
        elif isinstance(content, dict):
            button = ctk.CTkButton(
                scrollable_frame,
                text=f"{name}/",
                width=200,
                height=150,
                corner_radius=10,
                fg_color="lightblue",
                text_color="white",
                command=lambda sub_structure=content: clicked_folder_button(scrollable_frame, sub_structure, parent, current_folder = name)  
            )

        button.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        col += 1

def go_back(scrollable_frame, file_dictionary):
    global history
    global path
    global file_dictionary_variable
    global history
    global path

    delete_to_penultimate_slash()
    file_dictionary_variable.set(path)

    if len(history) > 0:  # Ensure there is something to go back to
        previous_folder = history.pop()  # Remove the last folder from history
        if len(history) == 0:
            # If history is empty, we should show the root structure
            create_buttons(scrollable_frame, file_dictionary)
        else:
            # Get the previous folder structure and display it
            previous_structure = get_folder_structure(file_dictionary, previous_folder)
            create_buttons(scrollable_frame, previous_structure, previous_folder)
    print(f"back clicked, history now is: {history}")
    print(f"back clicked, path now is: {path}")
    

# Function to get the folder's structure based on the folder name
def get_folder_structure(file_dictionary, folder):
    def find_folder_structure(current_dict, target_folder):
        for key, value in current_dict.items():
            if key == target_folder:
                return value
            if isinstance(value, dict):
                result = find_folder_structure(value, target_folder)
                if result is not None:
                    return result
        return None
    
    return find_folder_structure(file_dictionary, folder)

def browse_file(self):
    return filedialog.askopenfilename()


def build_file_dictionary(directory):
    """
    Recursively builds a dictionary of files and directories from a given directory path.
    """
    file_dict = {}
    for root, dirs, files in os.walk(directory):
        # Create a dictionary for each folder in the path
        folder_name = os.path.basename(root)
        if folder_name not in file_dict:
            file_dict[folder_name] = {}

        # Add files inside this folder to the dictionary
        for file in files:
            file_dict[folder_name][file] = None

    return file_dict
# Example usage:

# Main application window
window = tk.Tk()
window.geometry("1000x600")
uploads_folder = 'uploads'
file_dictionary = build_file_dictionary(uploads_folder)
upload_gui = UploadGUI(window)
upload_gui.show()

window.mainloop()
