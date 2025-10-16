"""
Клавіатури для блоку "Пошук користувачів"
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

from app.modules.database.models import UserModel


def get_search_users_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для пошуку користувачів"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🆔 По ID користувача",
                    callback_data="search_user_by_id"
                ),
                InlineKeyboardButton(
                    text="📱 По Telegram ID",
                    callback_data="search_user_by_telegram_id"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 По імені/прізвищу",
                    callback_data="search_user_by_name"
                ),
                InlineKeyboardButton(
                    text="📞 По телефону",
                    callback_data="search_user_by_phone"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏷️ По ролі",
                    callback_data="search_user_by_role"
                ),
                InlineKeyboardButton(
                    text="👤 По username",
                    callback_data="search_user_by_username"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="back_to_user_management"
                )
            ]
        ]
    )


def get_search_results_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для результатів пошуку"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 Новий пошук",
                    callback_data="admin_search_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin_search_users"
                )
            ]
        ]
    )


def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору ролі для пошуку"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Покупці",
                    callback_data="search_role_buyer"
                ),
                InlineKeyboardButton(
                    text="👑 Адміністратори",
                    callback_data="search_role_admin"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin_search_users"
                )
            ]
        ]
    )


def get_users_search_results_keyboard(users: List[UserModel]) -> InlineKeyboardMarkup:
    """Клавіатура з результатами пошуку користувачів"""
    buttons = []
    
    # Додаємо кнопки з користувачами
    for user in users:
        # Форматуємо текст кнопки: Ім'я + Прізвище + Роль + Статус
        button_text = f"👤 {user.first_name or 'Без імені'}"
        
        if user.last_name:
            button_text += f" {user.last_name}"
        
        # Додаємо роль
        role_emoji = "🛒" if user.role == "buyer" else "🏪" if user.role == "seller" else "👑"
        button_text += f" {role_emoji}"
        
        # Додаємо статус
        if not user.is_active:
            button_text += " 🚫"
        
        # Обмежуємо довжину тексту кнопки
        if len(button_text) > 50:
            button_text = button_text[:47] + "..."
        
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_user_{user.id}"
        )])
    
    # Кнопки управління
    buttons.append([
        InlineKeyboardButton(
            text="🔍 Новий пошук",
            callback_data="admin_search_users"
        ),
        InlineKeyboardButton(
            text="🔙 Назад до пошуку",
            callback_data="admin_search_users"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
