"""
Клавіатури для контактної інформації (клієнт)
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_contacts_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="🗺️ Показати на карті",
                url="https://maps.app.goo.gl/ZHxCwvruYTxhMJV46",
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


