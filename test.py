import requests
from datetime import datetime, timedelta
from pprint import pprint, pformat

# Создаем имя файла с текущей датой
filename = f"bitrix_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# Открываем файл для записи
with open(filename, 'w', encoding='utf-8') as f:
    # URL вебхука для доступа к Битрикс24
    BITRIX_WEBHOOK_URL = f"https://k127bfl.bitrix24.ru/rest/1/fdwpfvjql4rilnow/crm.category.list"

    # Отправка запроса для категорий
    response = requests.post(BITRIX_WEBHOOK_URL, json={"entityTypeId":2})
    result = response.json()
    
    f.write("=== Категории ===\n")
    for record in result['result']['categories']:
        f.write(f"{pformat(record)}\n")
    f.write("\n")

    # URL вебхука для доступа к статусам
    BITRIX_WEBHOOK_URL = f"https://k127bfl.bitrix24.ru/rest/1/fdwpfvjql4rilnow/crm.status.list"

    # Отправка запроса для статусов
    response = requests.post(BITRIX_WEBHOOK_URL, json={"ENTITY_ID": "STATUS"})
    result = response.json()
    
    f.write("=== Статусы ===\n")
    f.write(pformat(result))

print(f"Результаты записаны в файл: {filename}")