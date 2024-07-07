import tkinter as tk
from tkinter import filedialog, ttk, BOTH, END
from tkinter.ttk import Style
import os
import asyncio
import threading
from datetime import datetime
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
from algorithm import execute_path

class GalleryApp:
    def __init__(self, root):
        self.root = root
        self.images = []
        self.current_image = 0
        
        # Создаем холст для отображения изображений
        self.canvas = tk.Canvas(root, width=400, height=400)
        self.canvas.pack()
        
        # Кнопки для навигации по изображениям
        tk.Button(root, text="Next", command=self.next_image).pack()
        tk.Button(root, text="Previous", command=self.prev_image).pack()
        
    def display_image(self):
        """Отображает текущее изображение на холсте"""
        if self.images:
            image_path = self.images[self.current_image]
            image = Image.open(image_path).resize((400, 400))
            photo = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas.image = photo
    
    def clear_images(self):
        """Очищает холст"""
        self.canvas.delete("all")
    
    def next_image(self):
        """Переходит к следующему изображению"""
        if self.images:
            self.current_image = (self.current_image + 1) % len(self.images)
            self.clear_images()
            self.display_image()
    
    def prev_image(self):
        """Переходит к предыдущему изображению"""
        if self.images:
            self.current_image = (self.current_image - 1) % len(self.images)
            self.clear_images()
            self.display_image()

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.gallery_app = GalleryApp(root)

    def setup_ui(self):
        """Настраивает пользовательский интерфейс"""
        self.root.title("Animals Solution")
        self.root.geometry("900x900")
        self.root.resizable(True, True)

        style = Style()
        style.theme_use("clam")
        font = ("Helvetica", 12)
        style.configure("TLabel", font=font)
        style.configure("TButton", font=font, background="#4CAF50", foreground="white")

        tk.Label(self.root, text="Выберите папку, содержащую фото фотоловушки:").pack(pady=10)
        tk.Button(self.root, text="Выбрать папку", command=self.select_folder).pack(pady=10)

        self.label_wait = tk.Label(self.root, text="")
        self.label_wait.pack(pady=10)

        self.setup_tree()

    def setup_tree(self):
        """Настраивает таблицу для отображения данных"""
        columns = ("class", "start", "end", "count")
        self.tree = ttk.Treeview(columns=columns, show="headings")
        self.tree.pack(fill=BOTH, expand=1)

        headers = ["Класс животного", "Дата начала регистрации", "Дата конца регистрации", "Максимальное кол-во животных"]
        for col, header in zip(columns, headers):
            self.tree.heading(col, text=header)

        self.tree.bind("<<TreeviewSelect>>", self.item_selected)

    def select_folder(self):
        """Обрабатывает выбор папки с изображениями"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.root.filename = folder_path
            self.tree.delete(*self.tree.get_children())
            self.label_wait.config(text="Подождите пожалуйста, идет обработка данных...")
            self.label_wait.update()
            self.gallery_app.clear_images()
            threading.Thread(target=self.run_async_function_in_thread, args=(folder_path,)).start()

    def run_async_function_in_thread(self, folder_path):
        """Запускает асинхронную функцию обработки изображений"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        registrations = loop.run_until_complete(self.external_method(folder_path))
        self.label_wait.config(text="")
        self.label_wait.update()
        
        for registration in registrations:
            self.tree.insert("", END, values=registration[1:5])

    async def external_method(self, folder_path):
        """Асинхронный метод для обработки папки с изображениями"""
        return await asyncio.get_event_loop().run_in_executor(None, execute_path, folder_path, False)

    def item_selected(self, event):
        """Обрабатывает выбор элемента в таблице"""
        for selected_item in self.tree.selection():
            item = self.tree.item(selected_item)
            cell = item["values"]
            filtered_data = self.filter_images_by_date(self.root.filename, cell[1], cell[2])
            self.gallery_app.clear_images()
            self.gallery_app.images = [item[0] for item in filtered_data]
            self.gallery_app.display_image()

    def filter_images_by_date(self, folder_path, start_date, end_date):
        """Фильтрует изображения по дате"""
        files_data = []
        for file_name in os.listdir(folder_path):
            image_path = os.path.join(folder_path, file_name)
            image = Image.open(image_path)
            exif_data = image._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    if TAGS.get(tag_id, tag_id) == 'DateTime':
                        date_object = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        files_data.append((image_path, date_object))
        
        min_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        max_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        return [item for item in files_data if min_date <= item[1] <= max_date]

if __name__ == '__main__':
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
