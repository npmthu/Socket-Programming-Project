import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import ttkbootstrap as ttk
from PIL import Image

menu_image = Image.open("menu_icon.png")

class SlidePanel(ctk.CTkFrame):
    def __init__(self, parent, start_pos, end_pos):
        super().__init__(master = parent)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.width = abs(start_pos-end_pos)

        self.pos = self.start_pos
        self.in_start_pos = True

        self.place(relx = self.start_pos, rely = 0.05, relwidth = self.width, relheight = 0.9)

    def animate(self):
        if self.in_start_pos:
            self.animate_forward()
        else:
            self.animate_backward()

    def animate_forward(self):
        if self.pos > self.end_pos:
            self.pos -= 0.001
            self.place(relx = self.pos, rely = 0.05, relwidth = self.width, relheight = 0.9)
            self.after(2, self.animate_forward)
        else:
            self.in_start_pos = False
    
    def animate_backward(self):
        if self.pos < self.start_pos:
            self.pos += 0.001
            self.place(relx = self.pos, rely = 0.05, relwidth = self.width, relheight = 0.9)
            self.after(2, self.animate_backward)
        else:
            self.in_start_pos = True



root = tk.Tk()
root.title("Socket programming project")
root.iconphoto(True, tk.PhotoImage(file = 'icon.png'))
root.geometry('1000x600')

#LEVEL0: root_frame to swith connection page and up/down page
root_frame = tk.Frame(root)
root_frame.pack(expand=True, fill='both')

#LEVEL1: main_frame to display up/down page
main_frame = tk.Frame(root_frame, background='red')
main_frame.pack(expand = True, fill='both')

#LEVEL2: indicate_frame has menu button, indicate 'function' that user is using
indicate_frame = tk.Frame(main_frame, background='blue', height=60)
indicate_frame.pack(fill='x')

#animated_panel = SlidePanel(root_frame, 0.3, 0.0)
#ctk.CTkLabel(animated_panel, text = 'Label 1').pack(expand = True, fill = 'both', padx = 2, pady = 10)
#ctk.CTkLabel(animated_panel, text = 'Label 2').pack(expand = True, fill = 'both', padx = 2, pady = 10)
#ctk.CTkButton(animated_panel, text = 'Button', corner_radius = 0).pack(expand = True, fill = 'both', pady = 10)
#ctk.CTkTextbox(animated_panel, fg_color = ('#dbdbdb','#2b2b2b')).pack(expand = True, fill = 'both', pady = 10)
#
#menu_button = ctk.CTkButton(indicate_frame, text='', image=ctk.CTkImage(menu_image), command = animated_panel.animate)
#menu_button.place(x=10, y=5)

#LEVEL2:
upload_frame = tk.Frame(main_frame, background='green')
download_frame = tk.Frame(main_frame, background='yellow')
download_frame.pack(expand = True, fill='both')

#LEVEL3:
download_function_frame = tk.Frame(download_frame, bg='green', height=50)
download_function_frame.pack(expand = True, fill='x')
refresh_button = ctk.CTkButton(download_function_frame, text="refresh", width=len('refresh'))
refresh_button.pack(side = 'left', padx = 10)
download_button = ctk.CTkButton(download_function_frame,
                                text="download",
                                width=len('download'),
                                command=lambda : clicked_download_button)
download_button.pack(side = 'left', padx = 20)

file_dictionary_variable = ctk.StringVar()
file_dictionary_variable.set('/')
directory_label = ctk.CTkLabel(download_function_frame, textvariable = file_dictionary_variable)
directory_label.pack(side = 'left', fill = 'x', padx = 20)


download_display_frame = ctk.CTkScrollableFrame(download_frame,
                                                fg_color='red',
                                                width=950,
                                                height=450)
download_display_frame.pack(expand=True)

file_dictionary = {'HDTH5.pdf': None, 'HDTH5_1733077847.pdf': None, 'test2': {'04instructions2.pptx': None, '04instructions2_1733078125.pptx': None, 'khtn.png': None, 'khtn_1733078125.png': None, 'Report.docx': None, 'Report_1733078125.docx': None, 'test3': {'close.png': None, 'close_1733078125.png': None, 'test4': {'abc.png': None}}}}

history = []
path = "/"

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

# Function to go back to the previous folder
def go_back(scrollable_frame, file_dictionary):
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

# Go back button
go_back_button = ctk.CTkButton(
    download_function_frame,
    text="Back",
    width=200,
    height=50,
    corner_radius=10,
    fg_color="lightcoral",
    text_color="white",
    command=lambda: go_back(download_display_frame, file_dictionary)
)
go_back_button.pack(side='left', padx=10)



# Initial call to create the buttons for the root structure
create_buttons(download_display_frame, file_dictionary, "/")


root.mainloop()