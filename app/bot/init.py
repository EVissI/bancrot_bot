﻿import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.bot.midlewares.message_history import MessageCleanerMiddleware
from app.bot.routers.main_router import main_router
from app.bot.sheldured_task.send_notification import check_db_and_send_notification, second_retry_tasks_launch, last_retry_tasks_launch
from app.bot.sheldured_task.update_succes_fccp import update_success_fccp
from app.config import setup_logger

setup_logger("bot")
from loguru import logger
from app.db.models import TelegramUser
from app.config import bot, admins, dp
from app.db.dao import UserDAO
from app.db.database import async_session_maker
from app.db.schemas import UserFilterModel
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat


async def set_commands():
    commands = [
        BotCommand(command="start", description="кнопка старт"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())



async def start_bot():
    await set_commands()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, f"Я запущен🥳.")
        except:
            pass
    logger.info("Бот успешно запущен.")


async def stop_bot():
    try:
        for admin_id in admins:
            await bot.send_message(admin_id, "Бот остановлен. За что?😔")
    except:
        pass
    logger.error("Бот остановлен!")



def start_scheduler():
    """
    Запуск планировщика задач.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_db_and_send_notification, "cron", day_of_week="mon", hour=0, minute=0)
    scheduler.add_job(second_retry_tasks_launch, "cron", day_of_week="mon", hour=1, minute=0)
    scheduler.add_job(last_retry_tasks_launch, "cron", day_of_week="tue", hour=0, minute=0)

    scheduler.add_job(update_success_fccp, "cron", day_of_week="mon", hour=0, minute=0)
    scheduler.start()
    logger.info("Планировщик задач запущен.")

async def main():
    # регистрация middleware
    dp.message.middleware(MessageCleanerMiddleware())
    # регистрация роутеров
    dp.include_router(main_router)

    # регистрация функций
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
