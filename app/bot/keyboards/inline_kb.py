from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_subscription_on_chanel_keyboard() -> InlineKeyboardMarkup:
    channel_url = 'https://t.me/asfgagagagagaag' 
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
        text="Оплатить",callback_data="payment_sub",
    )
    return kb.as_markup()

def stop() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Прекратить",callback_data="stop",
    )
    return kb.as_markup()