from datetime import datetime, timedelta
import requests
from loguru import logger
from typing import Optional
import aiohttp

from app.config import settings


async def create_bitrix_deal(
    title: str,
    comment: Optional[str] = None,
    category_id: Optional[str] = None,
    stage_id: Optional[str] = None,
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
        "fields": {
            "TITLE": title,
            "BEGINDATE": datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
            "CLOSEDATE": (datetime.now() + timedelta(days=7)).strftime(
                "%Y-%m-%dT%H:%M:%S%z"
            ),
            "OPENED": "Y",
            "SOURCE_ID": "WEB",
        }
    }

    if comment:
        deal_data["fields"]["COMMENTS"] = comment
    if category_id:
        deal_data["fields"]["CATEGORY_ID"] = category_id
    if stage_id:
        deal_data["fields"]["STAGE_ID"] = stage_id

    try:
        response = requests.post(
            f"{settings.BITRIKS_WEBHOOK_URL}crm.deal.add", json=deal_data
        )
        result = response.json()

        if "result" in result:
            logger.info(f"Сделка успешно создана с ID: {result['result']}")
            return True, str(result["result"])
        else:
            error_msg = result.get("error_description", "Неизвестная ошибка")
            logger.error(f"Ошибка при создании сделки: {error_msg}")
            return False, error_msg

    except Exception as e:
        logger.error(f"Ошибка при отправке запроса в Битрикс24: {str(e)}")
        return False, str(e)


async def bitrix_add_comment_to_deal(deal_id: str, comment: str) -> bool:
    """
    Добавляет комментарий к сделке в Bitrix24.
    :param deal_id: ID сделки (строка или число)
    :param comment: Текст комментария
    :return: True если успешно, иначе False
    """
    url = f"{settings.BITRIKS_WEBHOOK_URL}/crm.timeline.comment.add.json"
    payload = {
        "fields": {
            "ENTITY_ID": deal_id,
            "ENTITY_TYPE": "deal",
            "COMMENT": comment,
        }
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if "result" in data and data["result"] is not None:
                    logger.info(f"Комментарий успешно добавлен к сделке {deal_id}")
                    return True
                else:
                    logger.error(
                        f"Ошибка при добавлении комментария к сделке {deal_id}: {data}"
                    )
                    return False
    except Exception as e:
        logger.error(
            f"Исключение при добавлении комментария к сделке {deal_id}: {str(e)}"
        )
        return False
