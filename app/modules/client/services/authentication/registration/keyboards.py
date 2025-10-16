"""
Клавіатури для модуля реєстрації користувачів
"""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура для отримання номера телефону"""
    keyboard = [[KeyboardButton(text="📱 Поділитися номером", request_contact=True)]]
    return ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
    )


def get_main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    """Інлайн головне меню клієнта (без адмін опцій)"""
    keyboard = [
        [InlineKeyboardButton(text="🚛 Каталог авто", callback_data="client_catalog_menu")],
        [
            InlineKeyboardButton(text="📋 Мої збережені", callback_data="client_saved"),
            InlineKeyboardButton(text="🔔 Підписки", callback_data="client_subscriptions"),
        ],
        [
            InlineKeyboardButton(text="💬 Повідомлення", callback_data="client_messages"),
            InlineKeyboardButton(text="📞 Контакти", callback_data="client_contacts"),
        ],
        [
            InlineKeyboardButton(text="🏢 Про компанію", callback_data="client_company"),
            InlineKeyboardButton(text="❓ Допомога", callback_data="client_help"),
        ],
        [
            InlineKeyboardButton(text="👤 Профіль", callback_data="client_profile"),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_registration_start_keyboard() -> InlineKeyboardMarkup:
    """Інлайн клавіатура для початку реєстрації"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📱 Поділитися номером", callback_data="start_registration"
            )
        ],
        [
            InlineKeyboardButton(
                text="✍️ Ввести номер вручну", callback_data="manual_phone_input"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Скасувати", callback_data="cancel_registration"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
