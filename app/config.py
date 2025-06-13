
import os
from typing import List
from urllib.parse import quote
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    CHAT_TO_SUB: str
    WORK_CHAT_ID: int
    REG_PROMO_CODE:str = 'TEST'
    BOT_USERNAME:str

    YO_KASSA_TEL_API_KEY:str
    BITRIKS_WEBHOOK_URL:str

    EFRSB_TOKEN:str
    STEP:int = 2000

    POSTGRES_USER:str
    POSTGRES_PASSWORD:str
    POSTGRES_DB:str
    EFRSB_DB_HOST: str = "localhost" 
    EFRSB_DB_PORT: str = "5432"
    
    @property
    def efrsb_database_url(self) -> str:
        """Формируем URL для подключения к БД ЕФРСБ"""
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.EFRSB_DB_HOST}:{self.EFRSB_DB_PORT}/"
            f"{self.POSTGRES_DB}"
        )
    
    model_config = SettingsConfigDict(env_file=".env")

    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"
    DB_URL: str = 'sqlite+aiosqlite:///data/db.sqlite3'


    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )


# Инициализация конфигурации
settings = Settings()

def setup_logger(app_name: str):
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")
    os.makedirs(log_dir, exist_ok=True)
    logger.add(
        os.path.join(log_dir, f"log_{app_name}.txt"),
        format=settings.FORMAT_LOG,
        level="INFO",
        rotation=settings.LOG_ROTATION
    )
    logger.add(
        os.path.join(log_dir, f"log_{app_name}_error.txt"),
        format=settings.FORMAT_LOG,
        level="ERROR",
        rotation=settings.LOG_ROTATION
    )

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
admins = settings.ADMIN_IDS