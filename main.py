import gspread
from google.oauth2.service_account import Credentials

# Настройка доступа
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
client = gspread.authorize(creds)

# Укажите точное имя вашей таблицы
sheet = client.open("boxing_data").sheet1

# Проверка: читаем первую строку
data = sheet.row_values(1)
print("Подключение успешно! Первая строка таблицы:")
print(data)