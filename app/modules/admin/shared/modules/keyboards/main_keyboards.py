"""
Головні клавіатури адмін панелі
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Головна клавіатура адмін панелі"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🚛 Управління авто", 
                callback_data="admin_vehicles"
            ),
            InlineKeyboardButton(
                text="👥 Користувачі", 
                callback_data="admin_users"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📢 Розсилка", 
                callback_data="admin_broadcast"
            ),
            InlineKeyboardButton(
                text="📨 Заявки", 
                callback_data="admin_requests"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📤 Експорт даних", 
                callback_data="admin_export"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад", 
                callback_data="back_to_bot"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_vehicles_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура управління авто"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="➕ Додати авто", 
                callback_data="add_vehicle"
            ),
            InlineKeyboardButton(
                text="📋 Всі авто", 
                callback_data="admin_all_vehicles"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔍 Швидкий пошук", 
                callback_data="admin_quick_search"
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


def get_admin_users_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура управління користувачами"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="👥 Всі користувачі", 
                callback_data="admin_all_users"
            ),
            InlineKeyboardButton(
                text="🔍 Пошук користувачів", 
                callback_data="admin_search_users"
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


def get_admin_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура розсилки"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📢 Створити розсилку", 
                callback_data="admin_create_broadcast"
            ),
            InlineKeyboardButton(
                text="📋 Історія розсилок", 
                callback_data="admin_broadcast_history"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🧵 Управління топіками", 
                callback_data="admin_topics"
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


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура повернення до головного меню"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔙 Назад", 
                callback_data="admin_main"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


