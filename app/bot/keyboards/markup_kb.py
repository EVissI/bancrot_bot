from typing import Dict
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from loguru import logger



class MainKeyboard:
    __user_kb_texts_dict_ru = {
        'check_isp':'Проверить исполнительные производства',
        'referal':'Порекомендовать друга'
    }
    
    @staticmethod
    def get_user_kb_texts(key = None) -> Dict[str, str] | None:
        """
        'referal',
        'check_isp'
        """
        if key is not None:
            return MainKeyboard.__user_kb_texts_dict_ru.get(key)
        return MainKeyboard.__user_kb_texts_dict_ru


    @staticmethod
    def build_main_kb() -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()

        for val in MainKeyboard.get_user_kb_texts().values():
            kb.button(text=val)

        kb.adjust(
            len(MainKeyboard.get_user_kb_texts()),
        )

        return kb.as_markup(resize_keyboard=True)
