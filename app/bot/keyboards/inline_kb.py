from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.filters.callback_data import CallbackData

def get_subscription_on_chanel_keyboard() -> InlineKeyboardMarkup:
    channel_url = 'https://t.me/arbitrilin' 
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Подписаться", url=channel_url,
    )
    kb.button(
        text="Я подписался, проверь", callback_data="check_subscription"
    )
    return kb.as_markup()

def im_ready() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Я готов!", callback_data="im_ready_to_req",
    )
    return kb.as_markup()

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Ввести промокод",callback_data="promo_code",
    )
    kb.button(
        text="Оплатить",callback_data="payment_sub",
    )
    kb.adjust(2)
    return kb.as_markup()

class StopBancrData(CallbackData, prefix="change_lang"):
    IE:str

def stop(IE:str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Прекратить",callback_data=StopBancrData(IE=IE).pack(),
    )
    return kb.as_markup()

def check_credit() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Проверить кредитную историю",url='https://bkifssptg.netlify.app/',
    )
    kb.button(
        text="Оспорить кредитную историю",callback_data="dispute_credit"
    )
    return kb.as_markup()

class BalanceData(CallbackData, prefix="balance"):
    action:str

def get_balance_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Баланс",callback_data=BalanceData(action="balance").pack()
    )
    kb.button(
        text="Пополнить", callback_data="payment_sub",
    )
    kb.button(
        text="Активировать промо", callback_data="promo_code",
    )
    kb.adjust(1)
    return kb.as_markup()

def get_consent_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Согласен с условиями",
        callback_data="accept_privacy"
    )
    kb.button(
        text="❌ Не согласен",
        callback_data="decline_privacy"
    )
    kb.adjust(1)
    return kb.as_markup()

def referal_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="👥 Порекомендовать друга",
        callback_data="referal"
    )
    kb.adjust(1)
    return kb.as_markup()

def referal_keyboard_v2() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="👥 Пригласить еще",
        callback_data="referal"
    )
    kb.adjust(1)
    return kb.as_markup()