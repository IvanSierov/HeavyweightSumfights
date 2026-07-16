import gspread
import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from google.oauth2.service_account import Credentials

# Настройка подключения к Google Таблицам
print("Подключаюсь к Google Таблице...")
creds = Credentials.from_service_account_file('credentials.json', scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
client = gspread.authorize(creds)
sheet = client.open("boxing_data")

fighters_dict = {row[0]: row[1] for row in sheet.worksheet("Fighters_List").get_all_values() if len(row) > 1}

TEXT_DIR = "fighters_data"
if not os.path.exists(TEXT_DIR):
    os.makedirs(TEXT_DIR)

print("\nЗапускаю браузер (в режиме анти-обнаружения)...")
# Запускаем "невидимый" для Cloudflare драйвер
options = uc.ChromeOptions()
driver = uc.Chrome(options=options, version_main=143)

# Открываем страницу логина
driver.get("https://boxrec.com/en/login")

print("\n" + "="*50)
print("ВНИМАНИЕ! В открывшемся браузере введи свой логин и пароль от BoxRec.")
print("Когда успешно войдешь и увидишь главную страницу, возвращайся сюда.")
print("="*50 + "\n")

# Ждем, пока ты не нажмешь Enter
input("Нажми ENTER здесь, когда залогинишься в браузере...")

print("\nНачинаю скачивание файлов...")

# Перебираем всех боксеров из словаря
for name, boxer_id in fighters_dict.items():
    # Пропускаем, если ID пустой или заголовок таблицы
    if not boxer_id or str(boxer_id).lower() == 'id' or str(boxer_id).lower() == 'boxrec_id':
        continue
        
    file_path = os.path.join(TEXT_DIR, f"{boxer_id}.txt")
    
    # Если файл уже скачан (например, те три, что ты сделал вручную), пропускаем
    if os.path.exists(file_path):
        print(f"  [-] Пропуск: {name} (ID {boxer_id}) — файл уже существует.")
        continue

    print(f"  [+] Скачиваю: {name} (ID: {boxer_id})")
    
    # Переходим на страницу боксера
    driver.get(f"https://boxrec.com/en/box-pro/{boxer_id}")
    
    # Случайная пауза, чтобы BoxRec не понял, что мы бот, и не забанил аккаунт (от 4 до 7 секунд)
    time.sleep(random.uniform(4.0, 7.0))
    
    try:
        # Берем весь видимый текст на странице (аналог Ctrl+A -> Ctrl+C)
        body_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Сохраняем в текстовый файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(body_text)
            
    except Exception as e:
        print(f"  [!] Ошибка при скачивании {name}: {e}")

# Закрываем браузер после завершения
driver.quit()
print("\n✅ Все недостающие файлы скачаны!")