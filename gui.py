import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
from tkinter import messagebox
from PIL import ImageTk, Image
import queue
import os
import time
import socket

class MenuFrame(ctk.CTkFrame):
    def __init__(self, parent,
                 function_name_queue: queue.Queue,
                 function_args_queue: queue.Queue,
                 folder_structure: queue.Queue):
        super().__init__(parent, fg_color='#953019')
        self.place(x=0, y=0, relwidth=1, relheight=1)
        self.parent = parent
        self.function_name_queue = function_name_queue
        self.function_args_queue = function_args_queue
        self.folder_structure = folder_structure

        self.create_widgets()

    def create_widgets(self):
        #pine image
        self.left_panel = tk.Frame(self, width=200, background='#953019')
        self.left_panel.pack(side='left', fill='y')
        self.image_label = tk.Label(self.left_panel, bg='#953019')
        self.image_label.pack(padx = 30, pady=10)
        image = Image.open('pine.png')
        image = image.resize((150, 150))
        photo = ImageTk.PhotoImage(image)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

        download_icon = Image.open('download_icon.png')
        upload_icon = Image.open('upload_icon.png')
        help_icon = Image.open('help_icon.png')
        exit_icon = Image.open('exit_icon.png')

        download_icon = download_icon.resize((40, 40)) 
        upload_icon = upload_icon.resize((50, 50)) 
        help_icon = help_icon.resize((50, 50)) 
        exit_icon = exit_icon.resize((50, 50)) 

        download_photo = ImageTk.PhotoImage(download_icon)
        upload_photo = ImageTk.PhotoImage(upload_icon) 
        help_photo = ImageTk.PhotoImage(help_icon)
        exit_photo = ImageTk.PhotoImage(exit_icon)

        download_button = ctk.CTkButton(self,
                                        text='DOWNLOAD',
                                        fg_color='#f4ebd5',
                                        hover_color='#778966',
                                        text_color='#3f5a33',
                                        font=('League Spartan', 18, 'bold'),
                                        image = download_photo,
                                        compound='left',
                                        command=self.show_download_frame)
        upload_button = ctk.CTkButton(self,
                                      text='UPLOAD',
                                      fg_color='#f4ebd5',
                                      hover_color='#778966',
                                      text_color='#3f5a33',
                                      font=('League Spartan', 18, 'bold'),
                                      image = upload_photo,
                                      compound='left',
                                      command=self.show_upload_frame)
        help_button = ctk.CTkButton(self,
                                    text='HELP',
                                    fg_color='#f4ebd5',
                                    hover_color='#778966',
                                    text_color='#3f5a33',
                                    font=('League Spartan', 18, 'bold'),
                                    image = help_photo,
                                    compound='left',
                                    command=self.clicked_help_button)
        exit_button = ctk.CTkButton(self,
                                    text='EXIT',
                                    fg_color='#f4ebd5',
                                    hover_color='#778966',
                                    text_color='#3f5a33',
                                    font=('League Spartan', 18, 'bold'),
                                    image = exit_photo,
                                    compound='left',
                                    command=self.clicked_exit_button)
        self.switchable_frame = ctk.CTkFrame(self, fg_color='#f4ebd5', corner_radius=15)

        download_button.place(relx=0.01, rely=0.3, relwidth=0.17, relheight=0.1)
        upload_button.place(relx=0.01, rely=0.45, relwidth=0.17, relheight=0.1)
        help_button.place(relx=0.01, rely=0.6, relwidth=0.17, relheight=0.1)
        exit_button.place(relx=0.01, rely=0.75, relwidth=0.17, relheight=0.1)
        self.switchable_frame.place(relx=0.2, rely=0.1, relwidth=0.77, relheight=0.85)

        download_button.image = download_photo
        upload_button.image = upload_photo
        help_button.image = help_photo
        exit_button.image = exit_photo

        self.placeholder_frame = ctk.CTkFrame(self.switchable_frame,
                                              fg_color='#f4ebd5',
                                              corner_radius=35)
        self.placeholder_frame.pack(expand=True, fill='both')

    def show_download_frame(self):
        # Clear the switchable frame content
        for widget in self.switchable_frame.winfo_children():
            widget.destroy()

        # Create and display the download frame
        download_frame = DownloadFrame(self.switchable_frame, self.function_name_queue, self.function_args_queue, self.folder_structure)
        download_frame.pack(expand=True, fill='both')

    def show_upload_frame(self):
        # Clear the switchable frame content
        for widget in self.switchable_frame.winfo_children():
            widget.destroy()

        # Create and display the upload frame
        upload_frame = UploadFrame(self.switchable_frame, self.function_name_queue, self.function_args_queue, self.folder_structure)
        upload_frame.pack(expand=True, fill='both')
    
    def clicked_help_button(self):
    # Clear the upload display frame
        for widget in self.switchable_frame.winfo_children():
            widget.destroy()

        # Create a help title
        help_title = ctk.CTkLabel(
            self.switchable_frame,
            text="Help Instructions",
            font=("League Spartan", 24, "bold"),
            fg_color="#f4ebd5",
            text_color="#953019"
        )
        help_title.pack(pady=10)

        # Add help content
        help_text = """
        Welcome to the Help Section!
        
        1. **Upload Button**: Select and upload files to the server.
        2. **Download Button**: Browse and download available files.
        3. **Back Button**: Navigate back to the previous folder.
        4. **Refresh Button**: Reload the current folder's file list.
        5. **Exit Button**: Close the application.

        For further assistance, contact support@yourdomain.com.
        """
        help_content = ctk.CTkLabel(
            self.switchable_frame,
            text=help_text,
            font=("Arial", 14),
            justify="left",
            fg_color="#f4ebd5",
            text_color="#333333",
            wraplength=700
        )
        help_content.pack(pady=20)

    def clicked_exit_button(self):
        self.parent.destroy()

class DownloadFrame(ctk.CTkFrame):
    def __init__(self, parent,
                 function_name_queue:queue.Queue,
                 function_args_queue:queue.Queue,
                 folder_structure:queue.Queue):
        super().__init__(parent,
                         fg_color='#f4ebd5',
                         corner_radius=30,  
                         border_width=2,
                         border_color='#f4ebd5')
        self.function_name_queue = function_name_queue
        self.function_args_queue = function_args_queue
        self.folder_structure = folder_structure
        self.history = []
        self.path = "/"
        self.file_dictionary_variable = ctk.StringVar()
        self.file_dictionary_variable.set('')

        self.function_name_queue.put('list_files')
        self.function_args_queue.put((''))
        self.root_folder_structure = self.folder_structure.get()

        self.create_widgets()

    def create_widgets(self):
        # Function frame
        self.download_function_frame = ctk.CTkFrame(self,
                                                    corner_radius=20,
                                                    fg_color='#4b663a',
                                                    height=60)
        self.download_function_frame.pack(fill='x', padx=7, pady=7 )
        
        # Refresh button
        refresh_button = ctk.CTkButton(self.download_function_frame,
                                       text="Refresh",
                                       font=("Arial", 14, "bold"),
                                       text_color='#4b663a',
                                       fg_color='#f4ebd5',
                                       hover_color='#e9d2b0',
                                       command=self.clicked_refresh_button)
        refresh_button.pack(side="left", padx=10, pady = 15)

        #back button
        back_button = ctk.CTkButton(self.download_function_frame,
                                    text="Back",
                                    font=("Arial", 14, "bold"),
                                    text_color='#4b663a',
                                    fg_color='#f4ebd5',
                                    hover_color='#e9d2b0',
                                    command=self.go_back)
        back_button.pack(side="left", padx=10, pady = 15)

        #download_button
        download_button = ctk.CTkButton(self.download_function_frame,
                                        hover_color='#e9d2b0',
                                        text="Download",
                                        font=("Arial", 14, "bold"),
                                        text_color='#4b663a',
                                        fg_color='#f4ebd5',
                                        command=self.clicked_download_button)
        download_button.pack(side="left", padx=20, pady = 15)

        #Directory button
        directory_button = ctk.CTkButton(self.download_function_frame,
                                         font=("Arial", 14, "bold"),
                                         textvariable=self.file_dictionary_variable, text_color='#4b663a',
                                         fg_color='#f4ebd5',
                                         hover_color='#e9d2b0')
        directory_button.pack(side="left", fill='both', padx=20, pady = 15)

        # Scrollable frame
        self.download_display_frame = ctk.CTkScrollableFrame(self,
                                                             
                                                             fg_color='#f4ebd5')
        self.download_display_frame.pack(expand=True, fill="both")

        self.create_buttons()

    def create_buttons(self, file_structure=None, parent=""):
        # Nếu không cung cấp file_structure, sử dụng root_folder_structure mặc định
        if file_structure is None:
            file_structure = self.root_folder_structure

        # Xóa các widget cũ trong frame
        for widget in self.download_display_frame.winfo_children():
            widget.destroy()

        row, col = 0, 0
        max_columns = 4

        # Điều chỉnh cấu hình grid cho các hàng và cột
        for i in range(max_columns):
            self.download_display_frame.grid_columnconfigure(i, weight=1, uniform="equal")
        self.download_display_frame.grid_rowconfigure(row, weight=1, uniform="equal")

        file_icon = Image.open("file_button.png")  
        file_icon = file_icon.resize((100, 100))     
        file_photo = ImageTk.PhotoImage(file_icon)

        # Nếu path là thư mục gốc (root), tạo nút cho thư mục root
        if self.file_dictionary_variable.get() == '':
            button = ctk.CTkButton(self.download_display_frame,
                                   text="Root/",
                                   width=200,
                                   height=150,
                                   corner_radius=10,
                                   fg_color="#ffd18e",
                                   text_color="#1f1347",
                                   command=lambda: self.clicked_folder_button(self.root_folder_structure, "", "/"))
            
            button.grid(row=row, column=col, padx=10, pady=10, sticky="nsew", rowspan=3, columnspan=3)

            col += 3  
            row += 3  
        else:
            # Tạo các nút cho thư mục và file con
            for name, content in file_structure.items():
                if col >= max_columns:
                    col = 0
                    row += 1
                if isinstance(content, dict):  # Nếu là thư mục
                    button = ctk.CTkButton(self.download_display_frame,
                                           text=f"{name}/",
                                           width=200,
                                           height=150,
                                           corner_radius=10,
                                           fg_color="#ffd18e",
                                           text_color="#000000",
                                           image = file_photo,
                                           compound = 'top',
                                           command=lambda sub_structure=content, folder_name=name: self.clicked_folder_button(sub_structure, parent, folder_name))
                else:  # Nếu là file
                    button = ctk.CTkButton(self.download_display_frame,
                                           text=name,
                                           width=200,
                                           height=150,
                                           corner_radius=10,
                                           fg_color="#e9d2b0",
                                           text_color="#000000",
                                           image = file_photo,
                                           compound = 'top',
                                           command=lambda file_name=name: self.clicked_file_button(file_name))

                #button.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")      
                button.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                button.image = file_photo          
                col += 1

    def clicked_refresh_button(self):
        self.function_name_queue.put('list_files')
        self.function_args_queue.put((''))
        self.path = "/"
        self.history = []
        self.file_dictionary_variable.set('')
        self.root_folder_structure = self.folder_structure.get()
        
        self.create_buttons()

    def clicked_download_button(self):
        save_path = filedialog.askdirectory() 
        if save_path == "":
            print("cancel")
            return
        else:
            if self.file_dictionary_variable.get() == '':
                self.function_name_queue.put('download_folder')
                self.function_args_queue.put(('', f'{save_path}'))
            else:
                path = self.file_dictionary_variable.get()[1:]
                if path.endswith('/'):
                    self.function_name_queue.put('download_folder')
                    self.function_args_queue.put((f'{path}', f'{save_path}'))
                else:
                    self.function_name_queue.put('download_files')
                    self.function_args_queue.put(([f'{path}'], f'{save_path}'))
        print(f"Download button clicked, current path: {self.path}")
        print(f"Download button clicked, current file_dictionary_variable: {self.file_dictionary_variable.get()}")
        print(f'save_path: {save_path}')

    def clicked_file_button(self, file_name):
        if not self.path.endswith('/'):
            last_slash_index = self.path.rfind('/')
            if last_slash_index != -1:
                self.path = self.path[:last_slash_index + 1]
            else:
                self.path = '/'
        self.path = self.path + file_name
        self.file_dictionary_variable.set(self.path)
        print(f"File clicked: {self.path}")

    def clicked_folder_button(self, file_structure, parent, current_folder):
        if parent != '':
            self.history.append(parent)
        if not self.path.endswith('/'):
            last_slash_index = self.path.rfind('/')
            if last_slash_index != -1:
                self.path = self.path[:last_slash_index + 1]
            else:
                self.path = '/'
        self.path = self.path + current_folder + '/'
        if self.file_dictionary_variable.get() == '':
            self.path = '/'
        print(f"file_dic: {self.file_dictionary_variable.get()}")
        print(f"Folder {parent} clicked, current path: {self.path}")
        self.file_dictionary_variable.set(self.path)
        self.create_buttons(file_structure, current_folder)

    def go_back(self):
        if len(self.history) > 0:
            previous_folder = self.history.pop()

            # Quay lại thư mục trước đó
            self.delete_to_penultimate_slash()
            self.file_dictionary_variable.set(self.path)

            if len(self.history) == 0:
                self.create_buttons(self.root_folder_structure)
            else:
                previous_structure = self.get_folder_structure(self.root_folder_structure, previous_folder)
                self.create_buttons(previous_structure, previous_folder)
        else:
            self.path = '/'
            self.file_dictionary_variable.set('')
            self.create_buttons()

    def get_folder_structure(self, file_dictionary, folder):
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
    
    def delete_to_penultimate_slash(self):
        last_slash_index = self.path.rfind('/')
        if last_slash_index != -1:
            self.path = self.path[:last_slash_index]
            penultimate_slash_index = self.path.rfind('/')
            if penultimate_slash_index != -1:
                self.path = self.path[:penultimate_slash_index + 1]
            else:
                self.path = '/'

class UploadFrame(ctk.CTkFrame):
    def __init__(self, parent,
                 function_name_queue:queue.Queue,
                 function_args_queue:queue.Queue,
                 folder_structure:queue.Queue):
        super().__init__(parent,
                         fg_color='#f4ebd5',
                         corner_radius=30,  
                         border_width=2,
                         border_color='#f4ebd5')
        self.function_name_queue = function_name_queue
        self.function_args_queue = function_args_queue
        self.folder_structure = folder_structure
        self.history = []
        self.path = "/"
        self.file_dictionary_variable = ctk.StringVar()
        self.file_dictionary_variable.set('/')
        self.function_name_queue.put('list_files')
        self.function_args_queue.put((''))
        self.root_folder_structure = self.folder_structure.get()

        self.create_widgets()

    def create_widgets(self):
        # Function frame
        self.upload_function_frame = ctk.CTkFrame(self,
                                                  fg_color='#4b663a',
                                                  corner_radius=20,
                                                  height=60)
        self.upload_function_frame.pack(fill='x', padx=7, pady=7 )
        
        # Refresh button
        refresh_button = ctk.CTkButton(self.upload_function_frame,
                                       text="Refresh",
                                       font=("Arial", 14, "bold"),
                                       text_color='#4b663a',
                                       fg_color='#f4ebd5',
                                       hover_color='#e9d2b0',
                                       command=self.clicked_refresh_button)
        refresh_button.pack(side="left", padx=10, pady = 15)

        #back button
        back_button = ctk.CTkButton(self.upload_function_frame,
                                    text="Back",
                                    font=("Arial", 14, "bold"),
                                    text_color='#4b663a',
                                    fg_color='#f4ebd5',
                                    hover_color='#e9d2b0',
                                    command=self.go_back)
        back_button.pack(side="left", padx=10, pady = 15)

        #Directory button
        directory_button = ctk.CTkButton(self.upload_function_frame,
                                         font=("Arial", 14, "bold"),
                                         textvariable=self.file_dictionary_variable, text_color='#4b663a',
                                         fg_color='#f4ebd5',
                                         hover_color='#e9d2b0')
        directory_button.pack(side="left", fill='both', padx=20, pady = 15)

        # Scrollable frame
        self.upload_display_frame = ctk.CTkScrollableFrame(self, fg_color='#f4ebd5')
        self.upload_display_frame.pack(expand=True, fill="both")

        self.create_buttons()

    def extract_folder_path(self, full_path):
       path = full_path
       # Loại bỏ ký tự '/' ở đầu và cuối nếu có
       trimmed_path = path.strip("/")

       # Tách các phần tử theo dấu '/'
       parts = trimmed_path.split("/")

       # Nếu chỉ có 1 phần tử và nó là một file (có đuôi file), trả về phần thư mục đầu tiên
       if len(parts) == 1 and '.' in parts[0]:
           return ""

       # Trích xuất tất cả phần tử trừ phần tử cuối cùng, nếu phần tử cuối là file, bỏ qua
       if '.' in parts[-1]:
           return "/".join(parts[:-1])

       # Trả về đường dẫn thư mục nếu không có file
       return "/".join(parts)
    
    def clicked_refresh_button(self):
        self.function_name_queue.put('list_files')
        self.function_args_queue.put((''))
        self.history = []
        self.path = "/"
        self.file_dictionary_variable.set('/')
        self.root_folder_structure = self.folder_structure.get()
        
        self.create_buttons()

    def clicked_upload_file_button(self):
        save_path = self.extract_folder_path(self.path)
        filenames = filedialog.askopenfilenames()
        filelist = list(filenames)
        self.function_name_queue.put('upload_files')
        self.function_args_queue.put((filelist, f'{save_path}'))

        print(f"clicked upload file button, file list: {filelist}")
        print(f"clicked upload file button, self.path {self.path} save path: {save_path}")

    def clicked_upload_folder_button(self):
        save_path = self.extract_folder_path(self.path)
        foldernames = filedialog.askdirectory()
        self.function_name_queue.put('upload_folder_sequential')
        self.function_args_queue.put((f'{foldernames}', f'{save_path}'))
        print("clicked upload folder button")
        pass
       
    def clicked_file_button(self, file_name):
        if not self.path.endswith('/'):
            last_slash_index = self.path.rfind('/')
            if last_slash_index != -1:
                self.path = self.path[:last_slash_index + 1]
            else:
                self.path = '/'
        self.path = self.path + file_name
        self.file_dictionary_variable.set(self.path)
        print(f"File clicked: {self.path}")

    def clicked_folder_button(self, file_structure, parent, current_folder):
        self.history.append(parent)
        if not self.path.endswith('/'):
            last_slash_index = self.path.rfind('/')
            if last_slash_index != -1:
                self.path = self.path[:last_slash_index + 1]
            else:
                self.path = '/'
        self.path = self.path + current_folder + '/'
        if self.file_dictionary_variable.get() == '':
            self.path = '/'
        print(f"folder {parent} clicked ")
        print(f"file_dic: {self.file_dictionary_variable.get()}")
        print(f"path: {self.path}")
        self.file_dictionary_variable.set(self.path)
        self.create_buttons(file_structure, current_folder)

    def create_buttons(self, file_structure=None, parent=""):
        # Nếu không cung cấp file_structure, sử dụng root_folder_structure mặc định
        if file_structure is None:
            file_structure = self.root_folder_structure

        # Xóa các widget cũ trong frame
        for widget in self.upload_display_frame.winfo_children():
            widget.destroy()

        row, col = 0, 0
        max_columns = 4

        # Điều chỉnh cấu hình grid cho các hàng và cột
        for i in range(max_columns):
            self.upload_display_frame.grid_columnconfigure(i, weight=1, uniform="equal")
        self.upload_display_frame.grid_rowconfigure(row, weight=1, uniform="equal")

        file_icon = Image.open("file_button.png")  
        file_icon = file_icon.resize((100, 100))     
        file_photo = ImageTk.PhotoImage(file_icon)

        upload_icon = Image.open("upload_button.png")  
        upload_icon = upload_icon.resize((100, 100))     
        upload_photo = ImageTk.PhotoImage(upload_icon)

        # Tạo hai nút "Upload File" và "Upload Folder"
        upload_file_button = ctk.CTkButton(
            self.upload_display_frame,
            text="Upload File",
            width=200,
            height=150,
            corner_radius=10,
            fg_color="#8ecae6",
            text_color="white",
            font=('League Spartan', 18, 'bold'),
            image = upload_photo,
            compound = 'top',
            command=self.clicked_upload_file_button
        )
        upload_file_button.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        upload_file_button.image = upload_photo
        col += 1

        upload_folder_button = ctk.CTkButton(
            self.upload_display_frame,
            text="Upload Folder",
            width=200,
            height=150,
            corner_radius=10,
            fg_color="#219ebc",
            text_color="white",
            font=('League Spartan', 18, 'bold'),
            image = upload_photo,
            compound = 'top',
            command=self.clicked_upload_folder_button
        )
        upload_folder_button.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        upload_folder_button.image = upload_photo
        col += 1

        # Tạo các nút cho thư mục và file con
        for name, content in file_structure.items():
            if col >= max_columns:
                col = 0
                row += 1
            if isinstance(content, dict):  # Nếu là thư mục
                button = ctk.CTkButton(
                    self.upload_display_frame,
                    text=f"{name}/",
                    width=200,
                    height=150,
                    corner_radius=10,
                    fg_color="#ffd18e",
                    text_color="#000000",
                    image = file_photo,
                    compound = 'top',
                    command=lambda sub_structure=content, folder_name=name: self.clicked_folder_button(sub_structure, parent, folder_name)
                )
            else:  # Nếu là file
                button = ctk.CTkButton(
                    self.upload_display_frame,
                    text=name,
                    width=200,
                    height=150,
                    corner_radius=10,
                    fg_color="#e9d2b0",
                    text_color="#000000",
                    image = file_photo,
                    compound = 'top',
                    command=lambda file_name=name: self.clicked_file_button(file_name)
                )
            button.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            button.image = file_photo
            col += 1

    def go_back(self):
        if len(self.history) > 0:
            previous_folder = self.history.pop()

            # Quay lại thư mục trước đó
            self.delete_to_penultimate_slash()
            self.file_dictionary_variable.set(self.path)

            if len(self.history) == 0:
                self.create_buttons(self.root_folder_structure)
            else:
                previous_structure = self.get_folder_structure(self.root_folder_structure, previous_folder)
                self.create_buttons(previous_structure, previous_folder)
                print(f"previous folder structre: {previous_structure}")
                print(f"previous folder : {previous_folder}")
                print(f"histoey: {self.history}")
                print(f"dile_dic {self.file_dictionary_variable}" )
                print(f"path {self.path}")
        else:
            self.path = '/'
            self.file_dictionary_variable.set('/')
            self.history = []
            self.create_buttons()

    def get_folder_structure(self, file_dictionary, folder):
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
    
    def delete_to_penultimate_slash(self):
        last_slash_index = self.path.rfind('/')
        if last_slash_index != -1:
            self.path = self.path[:last_slash_index]
            penultimate_slash_index = self.path.rfind('/')
            if penultimate_slash_index != -1:
                self.path = self.path[:penultimate_slash_index + 1]
            else:
                self.path = '/'

class StartCanvas(tk.Canvas):
    def __init__(self, master, width, height, socket_container):
        super().__init__(master, width=width, height=height)
        
        self.window_width = width
        self.window_height = height
        self.socket_container = socket_container
        
        self.pack()

        self.load_background_image()
        self.create_start_button()

    def load_background_image(self):
        image_path = "intro.png"
        try:
            image = Image.open(image_path)
            image = image.resize((self.window_width, self.window_height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            self.create_image(0, 0, anchor="nw", image=photo)
            self.image = photo  # Giữ tham chiếu tới ảnh để không bị xóa
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
            self.create_window(x, y, window=button, anchor="center")
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
            self.create_window(width - 125 + i * 50, height, window=entry, anchor="center")
            entries.append(entry)

        for i in range(5):
            entries[i].bind("<KeyRelease>", lambda event, cur=entries[i], next=entries[i + 1]: self.focus_next_entry(cur, next, 1))

        entries[5].bind("<KeyRelease>", lambda event: self.check_pin(entries))

        entries[0].focus_set()

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

    def focus_next_entry(self, current_entry, next_entry, num_digit):
        if len(current_entry.get()) == num_digit:  # Khi người dùng đã nhập đủ số ký tự
            next_entry.focus_set()

    def display_ip_port_input(self, width, height):
        IP_height = height + 110
        port_height = height + 160

        label_ip = tk.Label(self.master, text="IP:", font=("Courier New", 16, "bold"), bg="#953019", fg="#ffffff")
        self.create_window(width - 100, IP_height, window=label_ip, anchor="e")

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
            self.create_window(width - 30 + i * 60, IP_height, window=entry, anchor="center")
            ip_entries.append(entry)

        # Bind KeyRelease để kiểm tra khi người dùng nhập đủ số ký tự và di chuyển tới entry tiếp theo
        for i in range(3):  # Chỉ bind cho 3 ô đầu (tới ô thứ 3 là dot sẽ xuất hiện)
            ip_entries[i].bind("<KeyRelease>", lambda event, cur=ip_entries[i], next=ip_entries[i + 1]: self.focus_next_entry(cur, next, 3))

        # Bind phím mũi tên phải (Right arrow) để di chuyển focus
        for i in range(3):  # Chỉ bind cho 3 ô đầu
            ip_entries[i].bind("<Right>", lambda event, cur=ip_entries[i], next=ip_entries[i + 1]: self.focus_next_entry(cur, next, 3))

        # Thêm dấu "." giữa các entry IP
        for i in range(3):
            dot_label = tk.Label(self.master, text=".", font=("Courier New", 14, "bold"), bg="#953019", fg="#ffffff")
            self.create_window(width + i * 60, IP_height, window=dot_label, anchor="center")

        # Label và entry port
        label_port = tk.Label(self.master, text="Port:", font=("Courier New", 16, "bold"), bg="#953019", fg="#ffffff")
        self.create_window(width - 80, port_height, window=label_port, anchor="e")

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
        self.create_window(width - 50, port_height, window=entry_port, anchor="w")

        confirm_button = self.display_image_button(
            "#953019", 
            "confirm.png", 
            width // 2, height // 2, 150, 
            command=lambda: [
                self.connect_to_server(ip_entries, entry_port),
            ]
        )
        self.create_window(width, height + 230, window=confirm_button, anchor="center")

    def connect_to_server(self, ip_entries, entry_port):
        global global_socket
        ip = '.'.join(entry.get() for entry in ip_entries)
        port = entry_port.get()

        if not all(ip.split('.')) or not port.isdigit():
            messagebox.showerror("Lỗi", "Vui lòng nhập đúng IP và Port!")
            return

        messagebox.showinfo("Kết nối", f"Đang kết nối tới {ip}:{port}...")
        # Add more

        for attempt in range(3):
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((ip, int(port)))
                self.socket_container['socket'] = client
                return
            except ConnectionError as e:
                if attempt < 3 - 1:
                    print(f"Connection failed: {e}. Retrying in 1 seconds...")
                    time.sleep(1)
                else:
                    messagebox.showerror("Connection Error", "Unable to connect to the server.")
                    return None

