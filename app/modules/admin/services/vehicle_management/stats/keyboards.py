"""
Клавіатури для модуля статистики авто
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_stats_main_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура головної статистики"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📊 Детальна статистика",
                callback_data="detailed_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏷️ Статистика по марках",
                callback_data="brand_stats"
            ),
            InlineKeyboardButton(
                text="💰 Статистика по цінах",
                callback_data="price_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 Місячна статистика",
                callback_data="monthly_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="admin_vehicles"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_detailed_stats_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура детальної статистики"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🏷️ Статистика по марках",
                callback_data="brand_stats"
            ),
            InlineKeyboardButton(
                text="💰 Статистика по цінах",
                callback_data="price_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 Місячна статистика",
                callback_data="monthly_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_stats_main"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_brand_stats_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура статистики по марках"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📊 Детальна статистика",
                callback_data="detailed_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💰 Статистика по цінах",
                callback_data="price_stats"
            ),
            InlineKeyboardButton(
                text="📅 Місячна статистика",
                callback_data="monthly_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_stats_main"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_price_stats_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура статистики по цінах"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📊 Детальна статистика",
                callback_data="detailed_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏷️ Статистика по марках",
                callback_data="brand_stats"
            ),
            InlineKeyboardButton(
                text="📅 Місячна статистика",
                callback_data="monthly_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_stats_main"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_monthly_stats_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура місячної статистики"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📊 Детальна статистика",
                callback_data="detailed_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏷️ Статистика по марках",
                callback_data="brand_stats"
            ),
            InlineKeyboardButton(
                text="💰 Статистика по цінах",
                callback_data="price_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_stats_main"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_stats_export_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура експорту статистики"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📄 Експорт в PDF",
                callback_data="export_stats_pdf"
            ),
            InlineKeyboardButton(
                text="📊 Експорт в Excel",
                callback_data="export_stats_excel"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📧 Надіслати звіт",
                callback_data="send_stats_report"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_stats_main"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_stats_refresh_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура оновлення статистики"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🔄 Оновити статистику",
                callback_data="refresh_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 Детальна статистика",
                callback_data="detailed_stats"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_stats_main"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
