"""
Клавіатури для модуля аутентифікації
"""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)


# Видалена клавіатура вибору ролі - всі користувачі автоматично buyers


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Клавіатура для отримання номера телефону"""
    keyboard = [[KeyboardButton(text="📱 Поділитися номером", request_contact=True)]]
    return ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
    )


def get_main_menu_keyboard(role: str = "buyer") -> ReplyKeyboardMarkup:
    """Головне меню для покупців (всі користувачі тепер buyers)"""
    if role == "admin":
        # Адмін меню залишається як було
        keyboard = [
            [KeyboardButton(text="👥 Користувачі"), KeyboardButton(text="🚛 Авто")],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="⚙️ Налаштування"),
            ],
            [KeyboardButton(text="📢 Розсилка"), KeyboardButton(text="📋 Звіти")],
        ]
    else:
        # Меню покупця (за замовчуванням для всіх)
        keyboard = [
            [KeyboardButton(text="🔍 Пошук авто")],
            [
                KeyboardButton(text="📋 Мої збережені"),
                KeyboardButton(text="💬 Повідомлення"),
            ],
            [
                KeyboardButton(text="🏢 Про компанію"),
                KeyboardButton(text="📞 Контакти"),
            ],
            [KeyboardButton(text="👤 Профіль"), KeyboardButton(text="❓ Допомога")],
        ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для профілю"""
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Редагувати", callback_data="edit_profile"),
            InlineKeyboardButton(text="🔄 Оновити", callback_data="refresh_profile"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_registration_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура початкової реєстрації"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📝 Зареєструватися", callback_data="start_registration"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
