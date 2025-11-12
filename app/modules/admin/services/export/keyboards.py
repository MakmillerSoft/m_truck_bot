"""
Клавіатури для експорту даних
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_export_main_keyboard() -> InlineKeyboardMarkup:
    """Головна клавіатура експорту"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="👥 Експорт користувачів",
                callback_data="export_users"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🚛 Експорт авто",
                callback_data="export_vehicles"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📨 Експорт заявок",
                callback_data="export_requests"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📢 Експорт розсилок",
                callback_data="export_broadcasts"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📦 Експорт всіх даних",
                callback_data="export_all"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="admin_main"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_export_back_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для повернення"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔙 Назад до експорту",
                callback_data="admin_export"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)





