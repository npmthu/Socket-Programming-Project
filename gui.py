import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
from tkinter import messagebox
from PIL import ImageTk, Image
import queue
import time
import socket

DEFAULT_PIN = "123456"

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
        self.left_panel = ctk.CTkFrame(self, width=200, fg_color='#953019')
        self.left_panel.pack(side='left', fill='y')
        self.image_label = ctk.CTkLabel(self.left_panel,text ='', bg_color='#953019')
        self.image_label.pack(padx = 30, pady=10)
        image = Image.open('pine.png')
        image = image.resize((250, 250))
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
        # Auto-scroll to the top of the frame

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
        if(filenames != ""):
            filelist = list(filenames)
            self.function_name_queue.put('upload_files')
            self.function_args_queue.put((filelist, f'{save_path}'))

            print(f"clicked upload file button, file list: {filelist}")
            print(f"clicked upload file button, self.path {self.path} save path: {save_path}")

    def clicked_upload_folder_button(self):
        save_path = self.extract_folder_path(self.path)
        foldernames = filedialog.askdirectory()
        if (foldernames != ""):
            self.function_name_queue.put('upload_folder_sequential')
            self.function_args_queue.put((f'{foldernames}', f'{save_path}'))
            print("clicked upload folder button")
       
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

class StartCanvas(ctk.CTkFrame):
    def __init__(self, master, width, height, socket_container):
        super().__init__(master, width=width, height=height, corner_radius=0)

        self.window_width = width
        self.window_height = height
        self.socket_container = socket_container

        self.pack(fill="both", expand=True)

        self.load_background_image()
        self.create_start_button()

    def load_background_image(self):
        image_path = "intro.png"
        try:
            original_image = Image.open(image_path)
            self.photo = ImageTk.PhotoImage(original_image)

            self.bg_label = ctk.CTkLabel(self, image=self.photo, text="")
            self.bg_label.pack(fill="both", expand=True)

            # Bind the resize event to update the image size
            self.bg_label.bind("<Configure>", self.resize_image)

        except FileNotFoundError:
            print("Error: Image file not found.")

    def resize_image(self, event):
        new_width = event.width
        new_height = event.height

        image_path = "intro.png"
        original_image = Image.open(image_path)
        
        resized_image = original_image.resize((new_width, new_height), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(resized_image)

        self.bg_label.configure(image=self.photo)

    def create_start_button(self):
        button_width = 200
        button_height = 60
        border_width = 3
        corner_radius = 30  # Adjust for desired roundness

        self.button1 = ctk.CTkButton(
            self,
            text="START",
            font=("Arial Rounded MT Bold", 20),  # Similar font to the image
            text_color="#1C1427",  # Dark text color
            fg_color="#F7D791",  # Light yellow from the image
            hover_color="#E1C581",  # Slightly darker yellow for hover
            bg_color="#8A3722",
            border_color="#1C1427",
            border_width=border_width,
            corner_radius=corner_radius,
            width=button_width,
            height=button_height,
            command=lambda: [
                self.button1.destroy(),
                self.display_pin_input(
                    self.window_width // 2, self.window_height // 2 + 150
                )
            ]
        )
        self.button1.place(
            relx=0.5,
            rely=(self.window_height // 2 + 150) / self.window_height,
            anchor="center"
        )

    def display_ip_port_input(self, width, height):
        IP_height = height + 110
        port_height = height + 160
        label_font = ctk.CTkFont("Courier New", 16, "bold")
        entry_font = ctk.CTkFont("Courier New", 14)

        label_ip = ctk.CTkLabel(self, text="IP:", font=label_font, text_color="#43291f",
                                bg_color='#f4ebd5')
        label_ip.place(relx=(width - 100)/self.window_width, rely=IP_height/self.window_height, anchor="e")

        ip_entries = []
        for i in range(4):
            entry = ctk.CTkEntry(
                self,
                width=50,
                font=entry_font,
                justify="center",
                fg_color="#f4ebd5",
                text_color="#43291f",
                border_width=2,
                border_color="#f4ebd5",
                bg_color='#f4ebd5',
                corner_radius=8
            )
            entry.place(relx=(width - 30 + i * 60)/self.window_width, rely=IP_height/self.window_height, anchor="center")
            ip_entries.append(entry)

        for i in range(3):
            ip_entries[i].bind("<KeyRelease>", lambda event, cur=ip_entries[i], next=ip_entries[i + 1]: self.focus_next_entry(cur, next, 3))
            ip_entries[i].bind("<Right>", lambda event, cur=ip_entries[i], next=ip_entries[i + 1]: self.focus_next_entry(cur, next, 3))

        for i in range(3):
            dot_label = ctk.CTkLabel(self, text=".", font=label_font, text_color="#43291f",bg_color='#f4ebd5')
            dot_label.place(relx=(width + i * 60)/self.window_width, rely=IP_height/self.window_height, anchor="center")

        label_port = ctk.CTkLabel(self, text="Port:", font=label_font, text_color="#43291f",
                                  bg_color='#f4ebd5')
        label_port.place(relx=(width - 80)/self.window_width, rely=port_height/self.window_height, anchor="e")

        entry_port = ctk.CTkEntry(
            self,
            width=120,
            font=entry_font,
            justify="center",
            fg_color="#f4ebd5",
            text_color="#43291f",
            border_width=2,
            border_color="#f4ebd5",
            bg_color='#f4ebd5',
            corner_radius=8
        )
        entry_port.place(relx=(width - 50)/self.window_width, rely=port_height/self.window_height, anchor="w")

        # --- Confirm Button ---
        button_width = 150
        button_height = 40  # Adjust height as needed
        border_width = 3
        corner_radius = 20  # More rounded corners
        
        confirm_button = ctk.CTkButton(
            self,
            text="CONFIRM",
            font=("Arial Rounded MT Bold", 16),  # Use a more visually appealing font
            text_color="#1C1427", # Dark text color from your image
            fg_color="#F7D791",  # Light yellow from your image
            hover_color="#E1C581",  # Slightly darker yellow for hover effect
            bg_color="#8A3722",  # Ensure transparent background
            border_color="#1C1427", # Dark color from your image
            border_width=border_width,
            corner_radius=corner_radius,
            width=button_width,
            height=button_height,
            command=lambda: self.connect_to_server(ip_entries, entry_port)
        )
        confirm_button.place(
            relx=0.5,  # Center horizontally
            rely=(height + 230) / self.window_height,
            anchor="center"
        )
      
    def display_pin_input(self, width, height):
        entries = []
        entry_font = ctk.CTkFont("Courier New", 30)
        for i in range(6):
            entry = ctk.CTkEntry(
                self,
                width=50,
                font=entry_font,
                justify="center",
                fg_color="#f4ebd5",
                text_color="#43291f",
                border_width=2,
                border_color="#f4ebd5",
                bg_color='#f4ebd5',
                corner_radius=8,
                show="*"
            )
            entry.place(relx=(width - 125 + i * 50)/self.window_width, rely=height/self.window_height, anchor="center")
            entries.append(entry)

        for i in range(5):
            entries[i].bind("<KeyRelease>", lambda event, cur=entries[i], next=entries[i + 1]: self.focus_next_entry(cur, next, 1))

        entries[5].bind("<KeyRelease>", lambda event: self.check_pin(entries))

        entries[0].focus_set()

    def check_pin(self, entries):
        pin = ''.join(entry.get() for entry in entries)
        if pin == DEFAULT_PIN:
            messagebox.showinfo("Success", "Welcome to the system!")
            for entry in entries:
                entry.destroy()
            self.display_ip_port_input(self.window_width // 2, self.window_height // 2)
        else:
            for entry in entries:
                entry.delete(0, 'end')
            messagebox.showerror("Error", "Incorrect PIN!")
            entries[0].focus_set()

    def focus_next_entry(self, current_entry, next_entry, num_digit):
        if len(current_entry.get()) == num_digit:
            next_entry.focus_set()
  
    def connect_to_server(self, ip_entries, entry_port):
        ip = '.'.join(entry.get() for entry in ip_entries)
        try:
            port = int(entry_port.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port number!")
            return

        if not all(ip.split('.')) or not (0 <= port <= 65535):
            messagebox.showerror("Error", "Please enter a valid IP and Port!")
            return

        messagebox.showinfo("Connecting", f"Connecting to {ip}:{port}...")

        for attempt in range(3):
                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((ip, port))
                    self.socket_container['socket'] = client
                    messagebox.showinfo("Success", "Successfully connected to the server!")
                    return
                except ConnectionRefusedError:
                    if attempt < 2:
                        messagebox.showwarning("Connection Failed", f"Connection refused. Retrying in 1 second... (Attempt {attempt + 2})")
                        time.sleep(1)
                    else:
                        messagebox.showerror("Connection Error", "Unable to connect to the server after multiple attempts.")
                        return None
                except OSError as e:
                    if e.errno == 10049: # incorrect IP address
                        messagebox.showerror("Error", "Invalid IP address. Please check and try again.")
                        return None
                    else:
                        messagebox.showerror("Connection Error", f"An unexpected error occurred: {e}")
                        return None
                except Exception as e:
                    messagebox.showerror("Connection Error", f"An unexpected error occurred: {e}")
                    return None