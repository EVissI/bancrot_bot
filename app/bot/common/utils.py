from datetime import datetime, timedelta
import requests
from loguru import logger
from typing import Optional

from app.config import settings

async def create_bitrix_deal(
    title: str,
    comment: Optional[str] = None,
    category_id: Optional[str] = None,
    stage_id: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """
    Создает сделку в Битрикс24
    
    Args:
        title: Название сделки (обязательный параметр)
        comment: Комментарий к сделке
        category_id: ID категории сделки
        deal_type: Тип сделки
        stage_id: ID этапа сделки
    
    Returns:
        tuple[bool, Optional[str]]: (успех операции, ID сделки или текст ошибки)
    """
    deal_data = {
        'fields': {
            'TITLE': title,
            'BEGINDATE': datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'),
            'CLOSEDATE': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S%z'),
            'OPENED': 'Y',
            'SOURCE_ID': 'WEB',
        }
    }
    
    if comment:
        deal_data['fields']['COMMENTS'] = comment
    if category_id:
        deal_data['fields']['CATEGORY_ID'] = category_id
    if stage_id:
        deal_data['fields']['STAGE_ID'] = stage_id

    try:
        response = requests.post(f"{settings.BITRIKS_WEBHOOK_URL}crm.deal.add", json=deal_data)
        result = response.json()
        
        if 'result' in result:
            logger.info(f"Сделка успешно создана с ID: {result['result']}")
            return True, str(result['result'])
        else:
            error_msg = result.get('error_description', 'Неизвестная ошибка')
            logger.error(f"Ошибка при создании сделки: {error_msg}")
            return False, error_msg
            
    except Exception as e:
        logger.error(f"Ошибка при отправке запроса в Битрикс24: {str(e)}")
        return False, str(e)