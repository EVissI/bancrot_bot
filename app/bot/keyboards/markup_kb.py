from typing import Dict
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, ReplyKeyboardRemove,KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from loguru import logger
from app.config import settings

def get_agreement_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ознакомиться с соглашением", web_app=WebAppInfo(url="https://www.google.com/search?q=cats&newwindow=1&sca_esv=c00251c694cd13aa&udm=2&biw=1920&bih=919&sxsrf=AE3TifOG8UlKCXfBvQWcPsww6_dQm5-phQ%3A1750252570151&ei=GrxSaNT-CIDhvr0P7JDQsAY&ved=0ahUKEwjU89f1hvuNAxWAsK8BHWwIFGYQ4dUDCBE&uact=5&oq=cats&gs_lp=EgNpbWciBGNhdHMyChAAGIAEGEMYigUyChAAGIAEGEMYigUyDRAAGIAEGLEDGEMYigUyCxAAGIAEGLEDGIMBMgoQABiABBhDGIoFMggQABiABBixAzIIEAAYgAQYsQMyCxAAGIAEGLEDGIMBMgUQABiABDIOEAAYgAQYsQMYgwEYigVI9htQAFiAGnAFeACQAQGYAeEDoAH-HKoBAzQtOLgBA8gBAPgBAZgCC6AC1xmoAgCYAwCSBwU0LjQtN6AHoSmyBwM0LTe4B8cZwgcGMC4xLjEwyAcp&sclient=img"))],
            [KeyboardButton(text="Поделиться номером", request_contact=True)],
        ],
        resize_keyboard=True,
    )

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
        "check_isp": "Проверить исполнительные производства",
        "check_credit": "Проверить кредитную историю",
        "balance":"Баланс",
        "referal": "Порекомендовать друга",

    }

    __admin_kb_texts_dict_ru = {"promocods": "Промокоды"}

    @staticmethod
    def get_user_kb_texts(key=None) -> Dict[str, str] | None:
        """
        'referal',
        'check_credit'
        'check_isp'
        """
        if key is not None:
            return MainKeyboard.__user_kb_texts_dict_ru.get(key)
        return MainKeyboard.__user_kb_texts_dict_ru

    @staticmethod
    def get_admin_kb_texts(key=None) -> Dict[str, str] | None:
        if key is not None:
            return MainKeyboard.__admin_kb_texts_dict_ru.get(key)
        return MainKeyboard.__admin_kb_texts_dict_ru

    @staticmethod
    def build_main_kb(tg_id: int) -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()

        for val in MainKeyboard.get_user_kb_texts().values():
            kb.button(text=val)
        kb.adjust(2, 1)

        if tg_id in settings.ADMIN_IDS:
            for val in MainKeyboard.get_admin_kb_texts().values():
                kb.button(text=val)
            kb.adjust(2, 1, 1)
        return kb.as_markup(resize_keyboard=True)


class PromocodeKeyboard:
    __promocode_kb_texts_dict_ru = {
        "create_promocode": "Создать промокод",
        "view_promocodes": "Просмотреть промокоды",
        "deactivate_promocode": "Деактивировать промокод",
        "back": "Назад",
    }

    @staticmethod
    def get_promocode_kb_texts(key=None) -> Dict[str, str] | None:
        """
        Возвращает тексты кнопок для промокодов

        Args:
            key: 'create_promocode', 'view_promocodes', 'deactivate_promocode', 'back'
        """
        if key is not None:
            return PromocodeKeyboard.__promocode_kb_texts_dict_ru.get(key)
        return PromocodeKeyboard.__promocode_kb_texts_dict_ru

    @staticmethod
    def build_promocode_kb() -> ReplyKeyboardMarkup:
        """
        Создает клавиатуру для управления промокодами
        """
        kb = ReplyKeyboardBuilder()

        for val in PromocodeKeyboard.get_promocode_kb_texts().values():
            kb.button(text=val)

        kb.adjust(3, 1) 
        return kb.as_markup(resize_keyboard=True)
