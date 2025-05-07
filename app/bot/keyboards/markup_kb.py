from typing import Dict
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from loguru import logger


class BackKeyboard:
    __button_text = "Назад"
    
    @staticmethod
    def get_button_text() -> str:
        """
        Возвращает текст кнопки 'Назад'.
        """
        return BackKeyboard.__button_text

    @staticmethod
    def build_back_kb() -> ReplyKeyboardMarkup:
        """
        Создает клавиатуру с кнопкой 'Назад'.
        """
        kb = ReplyKeyboardBuilder()
        kb.button(text=BackKeyboard.__button_text)
        kb.adjust(1)  # Одна кнопка в строке
        return kb.as_markup()


class MainKeyboard:
    __user_kb_texts_dict_ru = {
        'check_isp':'Проверить исполнительные производства',
        'check_credit':'Проверить кредитную историю',
        'referal':'Порекомендовать друга'
    }
    
    @staticmethod
    def get_user_kb_texts(key = None) -> Dict[str, str] | None:
        """
        'referal',
        'check_credit'
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
            len(MainKeyboard.get_user_kb_texts())-1,1
        )

        return kb.as_markup(resize_keyboard=True)
