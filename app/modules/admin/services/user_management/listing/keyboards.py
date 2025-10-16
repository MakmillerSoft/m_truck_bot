"""
Клавіатури для блоку "Всі користувачі"
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

from app.modules.database.models import UserModel


def get_users_list_keyboard(
    users: List[UserModel], 
    current_page: int = 1, 
    total_pages: int = 1,
    sort_by: str = "created_at_desc",
    status_filter: str = "all"
) -> InlineKeyboardMarkup:
    """Клавіатура зі списком користувачів та пагінацією"""
    buttons = []
    
    # Додаємо кнопки сортування (3 кнопки в 1 рядок)
    status_text = "Всі користувачі" if status_filter == "all" else "Активні" if status_filter == "active" else "Заблоковані"
    
    # Визначаємо наступний статус для циклічного перемикання
    if status_filter == "all":
        next_status = "active"
    elif status_filter == "active":
        next_status = "blocked"
    else:  # blocked
        next_status = "all"
    
    sort_buttons = [
        InlineKeyboardButton(
            text="📅 Дата ↓" if sort_by == "created_at_desc" else "📅 Дата ↑" if sort_by == "created_at_asc" else "📅 Дата",
            callback_data=f"sort_users_created_at_desc_{status_filter}" if sort_by != "created_at_desc" else f"sort_users_created_at_asc_{status_filter}"
        ),
        InlineKeyboardButton(
            text="👤 Ім'я ↓" if sort_by == "name_desc" else "👤 Ім'я ↑" if sort_by == "name_asc" else "👤 Ім'я",
            callback_data=f"sort_users_name_desc_{status_filter}" if sort_by != "name_desc" else f"sort_users_name_asc_{status_filter}"
        ),
        InlineKeyboardButton(
            text=f"📋 {status_text}",
            callback_data=f"filter_users_status_{next_status}_{sort_by}"
        ),
    ]
    buttons.append(sort_buttons)
    
    # Додаємо кнопки з користувачами (максимум 10 на сторінку)
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
    
    # Додаємо пагінацію якщо є більше однієї сторінки
    if total_pages > 1:
        pagination_buttons = []
        
        # Кнопка "Попередня"
        if current_page > 1:
            pagination_buttons.append(InlineKeyboardButton(
                text="⬅️ Попередня",
                callback_data=f"users_page_{current_page - 1}"
            ))
        
        # Кнопка з номером поточної сторінки
        pagination_buttons.append(InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}",
            callback_data="current_page_info"
        ))
        
        # Кнопка "Наступна"
        if current_page < total_pages:
            pagination_buttons.append(InlineKeyboardButton(
                text="Наступна ➡️",
                callback_data=f"users_page_{current_page + 1}"
            ))
        
        buttons.append(pagination_buttons)
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_user_management"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_detail_keyboard(
    user_id: int,
    is_active: bool = True,
    user_role: str = "buyer",
    admin_user_id: int = None,  # поточний адміністратор (DB id)
    founder_ids: list = None,   # список Telegram ID власників
    user_telegram_id: int | None = None,  # Telegram ID користувача картки
    admin_is_owner: bool = False,  # чи є поточний адміністратор власником
) -> InlineKeyboardMarkup:
    """Клавіатура для детального перегляду користувача"""
    buttons = []
    
    # Перевіряємо, чи це не сам адмін (DB id)
    is_self = admin_user_id and admin_user_id == user_id
    
    # Перевіряємо, чи це засновник (за Telegram ID)
    is_founder = bool(founder_ids and user_telegram_id and user_telegram_id in founder_ids)
    
    # Якщо цільовий користувач — засновник, жодних маніпуляцій
    if is_founder:
        pass
    else:
        # Якщо цільовий — адмін і поточний не власник, заборонити маніпуляції
        if user_role == "admin" and not admin_is_owner:
            pass
        else:
            # Кнопки управління статусом (тільки якщо не сам себе)
            if not is_self:
                if is_active:
                    buttons.append([InlineKeyboardButton(
                        text="🚫 Заблокувати користувача",
                        callback_data=f"block_user_{user_id}"
                    )])
                else:
                    buttons.append([InlineKeyboardButton(
                        text="✅ Розблокувати користувача",
                        callback_data=f"unblock_user_{user_id}"
                    )])
    
    # Кнопки управління роллю (лише власник може призначати/знімати адміна; не для self і не для засновника)
    if not is_self and not is_founder and admin_is_owner:
        if user_role != "admin":
            buttons.append([InlineKeyboardButton(
                text="👑 Надати права адміністратора",
                callback_data=f"promote_to_admin_{user_id}"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text="⬇️ Зняти права адміністратора",
                callback_data=f"demote_from_admin_{user_id}"
            )])
    
    # Кнопка видалення (тільки якщо не self; якщо ціль — адмін, дозволено лише власнику)
    if not is_self:
        if user_role == "admin" and not admin_is_owner:
            pass
        else:
            buttons.append([InlineKeyboardButton(
                text="🗑️ Видалити користувача",
                callback_data=f"delete_user_{user_id}"
            )])
    
    # Кнопка "Назад до списку"
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_users_list"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_confirmation_keyboard(
    action: str,
    user_id: int
) -> InlineKeyboardMarkup:
    """Клавіатура підтвердження дії з користувачем"""
    buttons = []
    
    if action == "block":
        buttons.append([InlineKeyboardButton(
            text="✅ Так, заблокувати",
            callback_data=f"confirm_block_user_{user_id}"
        )])
    elif action == "unblock":
        buttons.append([InlineKeyboardButton(
            text="✅ Так, розблокувати",
            callback_data=f"confirm_unblock_user_{user_id}"
        )])
    elif action == "delete":
        buttons.append([InlineKeyboardButton(
            text="✅ Так, видалити",
            callback_data=f"confirm_delete_user_{user_id}"
        )])
    elif action == "promote_to_admin":
        buttons.append([InlineKeyboardButton(
            text="✅ Так, надати права адміна",
            callback_data=f"confirm_promote_to_admin_{user_id}"
        )])
    elif action == "demote_from_admin":
        buttons.append([InlineKeyboardButton(
            text="✅ Так, зняти права адміна",
            callback_data=f"confirm_demote_from_admin_{user_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="❌ Скасувати",
        callback_data=f"cancel_user_action_{user_id}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_users_search_keyboard() -> InlineKeyboardMarkup:
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
                    text="👤 По імені",
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
                    text="✅ По верифікації",
                    callback_data="search_user_by_verification"
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


def get_user_management_main_keyboard() -> InlineKeyboardMarkup:
    """Основна клавіатура управління користувачами"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Всі користувачі",
                    callback_data="admin_all_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Пошук користувачів",
                    callback_data="admin_search_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="back_to_admin_panel"
                )
            ]
        ]
    )
