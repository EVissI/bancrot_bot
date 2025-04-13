from datetime import datetime
from loguru import logger
import json
from app.bot.keyboards.inline_kb import stop
from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.db.schemas import UserFilterModel,TelegramIDModel
from app.config import bot

async def check_db_and_send_notification():
    """
    Сравнивает записи из базы данных с записями в JSON.
    """
    logger.info("Запуск задачи сравнения записей из базы данных и JSON.")
    
    # Загружаем данные из JSON
    with open('all_data.json', 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    async with async_session_maker() as session:
        # Получаем все записи из базы данных
        db_records = await UserDAO.find_all(session, filters=UserFilterModel())
        json_entrys = []
        for db_record in db_records:
            # Формируем ключ для поиска в JSON
            db_record.data_of_birth = db_record.data_of_birth.replace("-", ".")
            key = f"{db_record.user_enter_last_name} {db_record.user_enter_first_name} {db_record.user_enter_otchestvo or ''}_{db_record.data_of_birth}".strip()

            
            for json_data_arr in json_data:
                json_data_lower = {key.lower(): value for key, value in json_data_arr[1].items()}
                json_entry = json_data_lower.get(key.lower())
                if json_entry:
                    json_entrys.append(json_entry)
                    break

            for json_entry in json_entrys:
                logger.info(f"Найдена запись в JSON для ключа: {key}")
                
                try:
                    json_sum_to_pay = int(json_entry[0][0][10].replace('Сумма к оплате: ', ''))
                    if json_sum_to_pay > 0:
                        await bot.send_message(db_record.telegram_id,text='Обнаружено исполнительное производство! Нажмите кнопку',
                                               reply_markup=stop())

                    else:
                        logger.info("Сумма к оплате равна 0. Логика не выполняется.")
                except IndexError:
                    logger.error(f"Ошибка доступа к элементу массива для ключа: {key}")
                    continue
            else:
                logger.info(f"Запись для ключа {key} не найдена в JSON.")

async def check_user_and_send_notification(telegram_id: int):
    """
    Сравнивает запись одного пользователя из базы данных с записями в JSON.
    """
    logger.info(f"Запуск задачи проверки для пользователя с telegram_id: {telegram_id}")
    
    # Загружаем данные из JSON
    with open('all_data.json', 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    
    async with async_session_maker() as session:
        # Получаем запись пользователя из базы данных
        db_record = await UserDAO.find_one_or_none(session,filters=TelegramIDModel(telegram_id=telegram_id))
        
        if not db_record:
            logger.info(f"Пользователь с telegram_id {telegram_id} не найден в базе данных.")
            return
        formatted_date = datetime.strptime(db_record.data_of_birth, "%Y-%m-%d").strftime("%d.%m.%Y")
        key = f"{db_record.user_enter_last_name} {db_record.user_enter_first_name} {db_record.user_enter_otchestvo or ''}_{formatted_date}".strip()
        logger.info(key)
        json_entrys = []
        for json_data_arr in json_data:
                json_data_lower = {key.lower(): value for key, value in json_data_arr[1].items()}
                json_entry = json_data_lower.get(key.lower())
                if json_entry:
                    json_entrys.append(json_entry)
                    break
        for json_entry in json_entrys:
            logger.info(f"Найдена запись в JSON для ключа: {key}")
            
            try:
                try:
                    for json_1 in json_entry:
                        for json_2 in json_1:
                            json_sum_to_pay = int(json_2[10].replace('Сумма к оплате: ', ''))
                            if json_sum_to_pay > 0:
                                await bot.send_message(
                                    db_record.telegram_id,
                                    text='Обнаружено исполнительное производство! Нажмите кнопку',
                                    reply_markup=stop()
                                )
                            return
                    else:
                        logger.info("Сумма к оплате равна 0. Логика не выполняется.")
                except:
                    pass
            except IndexError:
                logger.error(f"Ошибка доступа к элементу массива для ключа: {key}")
            return
        
        # Если запись не найдена
        logger.info(f"Запись для ключа {key} не найдена в JSON.")
        await bot.send_message(
                            db_record.telegram_id,
                            text='Исполнительные производства не найдены'
                        )