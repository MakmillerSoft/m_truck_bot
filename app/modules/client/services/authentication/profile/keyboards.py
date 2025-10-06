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
            InlineKeyboardButton(
                text="⚙️ Налаштування", callback_data="profile_settings"
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
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура налаштувань профілю"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔔 Сповіщення", callback_data="edit_notifications"
            ),
            InlineKeyboardButton(text="🌐 Мова", callback_data="language_settings"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_profile")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_notifications_settings_keyboard(
    notifications_enabled: bool = True,
) -> InlineKeyboardMarkup:
    """Клавіатура налаштувань сповіщень"""
    status_text = "❌ Вимкнути" if notifications_enabled else "✅ Увімкнути"

    keyboard = [
        [InlineKeyboardButton(text=status_text, callback_data="toggle_notifications")],
        [
            InlineKeyboardButton(
                text="🚛 Нові авто", callback_data="toggle_new_vehicles_notifications"
            ),
            InlineKeyboardButton(
                text="📋 Заявки", callback_data="toggle_requests_notifications"
            ),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_language_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура налаштувань мови"""
    keyboard = [
        [
            InlineKeyboardButton(text="🇺🇦 Українська", callback_data="language_uk"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="language_en"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="profile_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура скасування"""
    keyboard = [
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_edit")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



