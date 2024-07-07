import os
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime, timedelta
from model import get_classes
import csv

def split_list_by_time_difference(item_list, time_difference_minutes=30):
    """Функция для разбиения списка на подсписки по заданной разнице времени"""
    sublists = []
    current_sublist = []

    for i in range(len(item_list) - 1):
        current_sublist.append(item_list[i])

        if (item_list[i+1][1] - item_list[i][1]) > timedelta(minutes=time_difference_minutes):
            sublists.append(current_sublist)
            current_sublist = []

    current_sublist.append(item_list[-1])
    sublists.append(current_sublist)

    return sublists

def execute_path(path, safe_to_file = True):
    """Функция для обработки папки с изображениями"""
    file_list = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
    files_data = []
    detections = get_classes(path)
    for file in detections:
        file_name = file[0]
        animal_class = file[1]
        animal_count = file[2]
        capacity = file[3]
        image_path = os.path.join(path, file_name)
        image = Image.open(image_path)
        exif_data = image._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTime':
                    date_object = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    new_tuple = (image_path, date_object, animal_class, animal_count, capacity)
                    files_data.append(new_tuple)
        else:
            print("Данные EXIF не найдены в изображении.")
    
    #Обработка краевых значений начала
    updated_data = []
    for i in range(len(files_data)-1):
        current_item = files_data[i]
        next_item = files_data[i+1]

        if current_item[2] != next_item[2] and (next_item[1] - current_item[1] < timedelta(seconds=120)) and next_item[4] > current_item[4]:
            updated_item = (current_item[0], current_item[1], next_item[2], next_item[3], next_item[4])
            updated_data.append(updated_item)
        else:
            updated_data.append(current_item)
    updated_data.append(files_data[-1])
    files_data = updated_data
    
    #Обработка краевых значений конца
    updated_data = []
    for i in range(len(files_data)-1):
        current_item = files_data[i]
        previous_item = files_data[i-1]
        if (current_item[1] - previous_item[1] < timedelta(minutes=2) and
                previous_item[4] > current_item[4] and
                previous_item[2] != current_item[2]):
            updated_item = (current_item[0], current_item[1], previous_item[2], previous_item[3], previous_item[4])
            updated_data.append(updated_item)
        else:
            updated_data.append(current_item)
    updated_data.append(files_data[-1])
    files_data = updated_data
    
    #Получения списков фотографий с разбиением на животных
    animal_lists = {}
    for item in files_data:
        animal = item[2]
        if animal not in animal_lists:
            animal_lists[animal] = []
        animal_lists[animal].append(item)
    
    sorted_animal_lists = {}
    for animal in animal_lists:
        if animal not in sorted_animal_lists:
            sorted_animal_lists[animal] = []
        sorted_animal_lists[animal].append(sorted(animal_lists[animal], key=lambda x: x[1]))
    
    # Вычисление регистрации 
    data = []
    time_minute = 30 
    for animal in sorted_animal_lists:
        sorted_animal_list = sorted_animal_lists[animal][0]
        result_sublists = split_list_by_time_difference(sorted_animal_list, time_minute)
        for result_sublist in result_sublists:
            min_date = min(item[1] for item in result_sublist).strftime("%Y-%m-%d %H:%M:%S")
            max_date = max(item[1] for item in result_sublist).strftime("%Y-%m-%d %H:%M:%S")
            max_values = []
            for i in range(len(result_sublist)):
                if i == len(result_sublist):
                    max_values.append(None)
                else:
                    max_value = max(result_sublist[i][3] for item in result_sublist[i:])
                    max_values.append(max_value)
            max_count = max(max_values)
            if max_count> 5:
                max_count = 5
            folder_name = os.path.basename(os.path.dirname(result_sublist[0][0]))
            if animal != 'Empty':
                data.append((folder_name, animal, min_date, max_date, max_count))
    
    #Запись регистраций в файл или передача на выход
    if safe_to_file:
        final_file_name = 'submission.csv'
        with open(final_file_name, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
    else:
        return data

if __name__ == '__main__':
    #Путь к датасету, который необходимо обработать
    folder_path = "E:\\Hack\\test_dataset_test_data_Minprirodi\\test_data_Minprirodi\\traps"
    all_items = os.listdir(folder_path)
    folders = [item for item in all_items if os.path.isdir(os.path.join(folder_path, item))]

    for folder in folders:
        path = os.path.join(folder_path, folder)
        print(f"Processing folder: {path}")
        execute_path(path)     
