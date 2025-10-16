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
                text="📊 Статистика", 
                callback_data="admin_stats"
            ),
            InlineKeyboardButton(
                text="📢 Розсилка", 
                callback_data="admin_broadcast"
            ),
        ],
        [
            InlineKeyboardButton(
                text="⚙️ Налаштування", 
                callback_data="admin_settings"
            ),
            InlineKeyboardButton(
                text="📨 Заявки", 
                callback_data="admin_requests"
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
            InlineKeyboardButton(
                text="📝 Чернетки", 
                callback_data="admin_drafts"
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


def get_admin_stats_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура статистики"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📊 Загальна статистика", 
                callback_data="admin_general_stats"
            ),
            InlineKeyboardButton(
                text="🚛 Статистика авто", 
                callback_data="admin_vehicle_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="👥 Статистика користувачів", 
                callback_data="admin_user_stats"
            ),
            InlineKeyboardButton(
                text="📈 Аналітика", 
                callback_data="admin_analytics"
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
            InlineKeyboardButton(
                text="📊 Статистика розсилок", 
                callback_data="admin_broadcast_stats"
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


def get_admin_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура налаштувань"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="⚙️ Загальні налаштування", 
                callback_data="admin_general_settings"
            ),
            InlineKeyboardButton(
                text="🔒 Безпека", 
                callback_data="admin_security_settings"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🤖 Налаштування бота", 
                callback_data="admin_bot_settings"
            ),
            InlineKeyboardButton(
                text="📢 Налаштування групи", 
                callback_data="admin_group_settings"
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


def get_admin_reports_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура звітів"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📊 Щоденний звіт", 
                callback_data="admin_daily_report"
            ),
            InlineKeyboardButton(
                text="📈 Тижневий звіт", 
                callback_data="admin_weekly_report"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 Місячний звіт", 
                callback_data="admin_monthly_report"
            ),
            InlineKeyboardButton(
                text="📋 Кастомний звіт", 
                callback_data="admin_custom_report"
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


