"""
Клавіатури для модуля профілю користувача (клієнтська частина)
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_profile_main_keyboard() -> InlineKeyboardMarkup:
    """Головна клавіатура профілю"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✏️ Редагувати профіль", callback_data="edit_profile"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад", callback_data="client_back_to_main"
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_edit_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура редагування профілю"""
    keyboard = [
        [
            InlineKeyboardButton(text="👤 Ім'я", callback_data="edit_first_name"),
            InlineKeyboardButton(text="👤 Прізвище", callback_data="edit_last_name"),
        ],
        [InlineKeyboardButton(text="📞 Телефон", callback_data="edit_phone")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="client_profile")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_profile_keyboard() -> InlineKeyboardMarkup:
    """Універсальна клавіатура для повернення до профілю"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="client_profile")]
        ]
    )



