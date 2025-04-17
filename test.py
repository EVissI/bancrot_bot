import requests
from datetime import datetime, timedelta

# Пример данных для сделки
deal_data = {
    'fields': {
        'TITLE': 'Сделка с клиентом Иван Иванов',  # Название сделки
        'TYPE_ID': 'SALE',  # Тип сделки
        'STAGE_ID': 'NEW',  # Этап сделки
        'CATEGORY_ID': '7',  # Категория сделки
        'BEGINDATE': datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'),  # Дата начала
        'CLOSEDATE': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S%z'),  # Дата завершения
        'COMMENTS': 'Комментарий к сделке',  # Комментарий
        'OPENED': 'Y',  # Сделка открыта для всех
        'SOURCE_ID': 'WEB',  # Источник сделки
    }
}

# URL вебхука для доступа к Битрикс24
BITRIX_WEBHOOK_URL = f"https://k127bfl.bitrix24.ru/rest/1/fdwpfvjql4rilnow/crm.deal.add"

# Отправка запроса
response = requests.post(BITRIX_WEBHOOK_URL, json=deal_data)

# Обработка ответа
result = response.json()
if 'result' in result:
    print(f"Сделка успешно создана. ID сделки: {result['result']}")
else:
    print(f"Ошибка при создании сделки: {result}")