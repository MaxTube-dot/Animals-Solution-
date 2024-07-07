import tkinter as tk
from tkinter import filedialog
import os
import sys
import asyncio
from tkinter import *
from tkinter import ttk
from tkinter.ttk import Style
from algoritm import execute_path
import threading
from datetime import datetime, timedelta
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS

class GalleryApp:
    def __init__(self, root):
        self.root = root
        self.images = []
        self.current_image = 0
        
        self.canvas = tk.Canvas(root, width=400, height=400)
        self.canvas.pack()
        
        next_button = tk.Button(root, text="Next", command=self.next_image)
        next_button.pack()

        prev_button = tk.Button(root, text="Previous", command=self.prev_image)
        prev_button.pack()
        
    def display_image(self):
        image_path = self.images[self.current_image]
        image = Image.open(image_path)
        image = image.resize((400, 400))
        photo = ImageTk.PhotoImage(image)
        
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo
    
    def clear_images(self):
        self.canvas.delete("all")
    
    def next_image(self):
        self.current_image = (self.current_image + 1) % len(self.images)
        self.canvas.delete("all")
        self.display_image()
    
    def prev_image(self):
        self.current_image = (self.current_image - 1) % len(self.images)
        self.canvas.delete("all")
        self.display_image()

def run_async_function_in_thread(folder_path):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    registrations = loop.run_until_complete(external_method(folder_path))
    labelWait.config(text="")
    labelWait.update()
    
    for registration in registrations:
        data = [registration[1], registration[2], registration[3], registration[4]]
        tree.insert("", END, values=data)

def select_folder():
    root.filename = filedialog.askdirectory()
    if root.filename:
        file_path = root.filename
        tree.delete(*tree.get_children())
        labelWait.config(text="Подождите пожалуйста, идет обработка данных...")
        labelWait.update()
        app.clear_images()
        t = threading.Thread(target=run_async_function_in_thread, args=(root.filename,))
        t.start()

async def external_method(folder_path):
    return await asyncio.get_event_loop().run_in_executor(None, execute_path, folder_path, False)

def item_selected(event):
    for selected_item in tree.selection():
        item = tree.item(selected_item)
        cell = item["values"]
        files_data=[]
        files = os.listdir(root.filename)
        for file_name in files:
            image_path = os.path.join(root.filename, file_name)
            image = Image.open(image_path)
            exif_data = image._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'DateTime':
                        date_object = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        files_data.append((image_path, date_object))
        min_date =  datetime.strptime(cell[1], "%Y-%m-%d %H:%M:%S")
        max_date =  datetime.strptime(cell[2], "%Y-%m-%d %H:%M:%S")
        filtered_data = [item for item in files_data if min_date <= item[1] <= max_date]
        app.clear_images()
        app.images = [item[0] for item in filtered_data]
        app.display_image()

root = tk.Tk()
root.title("Animals Solution")
style = Style()
style.theme_use("clam")

root.geometry("900x900")
root.resizable(True, True)

label = tk.Label(root, text="Выберите папку, содержащую фото фотоловушки:")
label.pack(pady=10)
select_button = tk.Button(root, text="Выбрать папку", command=select_folder)
select_button.pack(pady=10)
font = ("Helvetica", 12)
style.configure("TLabel", font=font)
style.configure("TButton", font=font, background="#4CAF50", foreground="white")

labelWait = tk.Label(root, text="")
labelWait.pack(pady=10)

columns = ("class", "start", "end", "count")
tree = ttk.Treeview(columns=columns, show="headings")
tree
tree.pack(fill=BOTH, expand=1)
tree.heading("class", text="Класс животного")
tree.heading("start", text="Дата начала регистрации")
tree.heading("end", text="Дата конца регистрации")
tree.heading("count", text="Максимальное кол-во животных")
tree.bind("<<TreeviewSelect>>", item_selected)

app = GalleryApp(root)
root.mainloop()
