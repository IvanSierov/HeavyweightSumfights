import gspread
import os
import re
import time
import random
from datetime import datetime
from google.oauth2.service_account import Credentials

# Настройка подключения к Google Таблицам
print("Подключаюсь к Google Таблице...")
creds = Credentials.from_service_account_file('credentials.json', scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
client = gspread.authorize(creds)
sheet = client.open("boxing_data")

# Получаем словари и листы
fighters_dict = {row[0]: row[1] for row in sheet.worksheet("Fighters_List").get_all_values() if len(row) > 1}
main_sheet = sheet.worksheet("Лист1")
fights = main_sheet.get_all_records()

TEXT_DIR = "fighters_data"

def get_opponent_record_on_date(file_owner_id, target_date_str):
    """
    Ищет дату боя в файле одного боксера, чтобы забрать рекорд его оппонента.
    Сканирует строку и ищет ПЕРВУЮ последовательность из 3 или 4 чистых чисел подряд.
    Именно в этой группе всегда скрыт рекорд (и иногда вес).
    """
    if not file_owner_id:
        return None
        
    file_path = os.path.join(TEXT_DIR, f"{file_owner_id}.txt")
    if not os.path.exists(file_path):
        return None
        
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Ищем строку, которая начинается с нужной даты
            if line.startswith(target_date_str):
                if 'debut' in line.lower():
                    return 0
                    
                tokens = line.split()
                current_sequence = []
                valid_sequences = []
                
                # Идем по словам в строке (пропуская саму дату)
                for token in tokens[1:]:
                    if token.isdigit():
                        # Если это чистое число (без букв и спецсимволов ½), добавляем в цепочку
                        current_sequence.append(int(token))
                    else:
                        # Если цепочка прервалась текстом, проверяем её длину
                        if len(current_sequence) >= 3:
                            valid_sequences.append(current_sequence)
                        current_sequence = [] # обнуляем цепочку
                        
                # Проверка на случай, если строка заканчивалась числами
                if len(current_sequence) >= 3:
                    valid_sequences.append(current_sequence)
                    
                if valid_sequences:
                    # Берем самую первую найденную группу (это и есть оппонент)
                    seq = valid_sequences[0]
                    # Возвращаем сумму последних трех чисел (W L D) из этой группы
                    return seq[-3] + seq[-2] + seq[-1]
                    
    return None

def count_previous_fights_own_file(boxer_id, target_date_str):
    """
    Резервный метод: считаем количество строк с датами боев в собственном файле боксера
    строго до даты чемпионского поединка.
    """
    if not boxer_id:
        return 0
        
    file_path = os.path.join(TEXT_DIR, f"{boxer_id}.txt")
    if not os.path.exists(file_path):
        return 0
        
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    count = 0
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            if date_pattern.match(line):
                tokens = line.split()
                if len(tokens) < 3:
                    continue
                    
                date_str = tokens[0]
                try:
                    fight_date = datetime.strptime(date_str, '%Y-%m-%d')
                    if fight_date < target_date:
                        count += 1
                except:
                    continue
    return count

print("Начинаю расчет и запись в Google Таблицу...")

for i, row in enumerate(fights, start=2):
    name1 = str(row.get('Боксер1', '')).strip()
    name2 = str(row.get('Боксер2', '')).strip()
    date_fight = str(row.get('Дата', '')).strip()
    
    if not name1 or not name2 or not date_fight:
        continue

    id1 = fighters_dict.get(name1)
    id2 = fighters_dict.get(name2)
    
    print(f"\n[{i}] Обработка: {name1} vs {name2} ({date_fight})")
    
    # --- СЧИТАЕМ БОИ ДЛЯ БОКСЕРА 1 ---
    count1 = get_opponent_record_on_date(id2, date_fight)
    if count1 is not None:
        print(f"  [Кросс-чек] {name1}: {count1} боев (извлечено из файла соперника)")
    else:
        count1 = count_previous_fights_own_file(id1, date_fight)
        print(f"  [Собственный файл] {name1}: {count1} боев (резервный подсчет)")

    # --- СЧИТАЕМ БОИ ДЛЯ БОКСЕРА 2 ---
    count2 = get_opponent_record_on_date(id1, date_fight)
    if count2 is not None:
        print(f"  [Кросс-чек] {name2}: {count2} боев (извлечено из файла соперника)")
    else:
        count2 = count_previous_fights_own_file(id2, date_fight)
        print(f"  [Собственный файл] {name2}: {count2} боев (резервный подсчет)")

    # Записываем данные только в колонки D и E
    try:
        main_sheet.update(f'D{i}:E{i}', [[count1, count2]])
        time.sleep(random.uniform(1.0, 2.5))
    except Exception as e:
        print(f"  [!] Ошибка записи на строке {i}: {e}")

print("\n✅ Все данные успешно пересчитаны и обновлены в таблице!")