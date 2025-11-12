"""
Клавіатури для блоку "Історія розсилок"
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from app.modules.database.models import BroadcastModel


def get_broadcasts_list_keyboard(
    broadcasts: List[BroadcastModel], 
    current_page: int = 1, 
    total_pages: int = 1,
    sort_by: str = "created_at_desc",
    status_filter: str = "all"
) -> InlineKeyboardMarkup:
    """Клавіатура зі списком розсилок та пагінацією"""
    buttons = []
    
    # Додаємо кнопки сортування (2 кнопки в 1 рядок)
    status_text = "Всі" if status_filter == "all" else "Відправлені" if status_filter == "sent" else "Чернетки"
    
    # Визначаємо наступний статус для циклічного перемикання
    if status_filter == "all":
        next_status = "sent"
    elif status_filter == "sent":
        next_status = "draft"
    else:  # draft
        next_status = "all"
    
    sort_buttons = [
        InlineKeyboardButton(
            text="📅 Дата ↓" if sort_by == "created_at_desc" else "📅 Дата ↑" if sort_by == "created_at_asc" else "📅 Дата",
            callback_data=f"sort_broadcasts_created_at_desc_{status_filter}" if sort_by != "created_at_desc" else f"sort_broadcasts_created_at_asc_{status_filter}"
        ),
        InlineKeyboardButton(
            text=f"📋 {status_text}",
            callback_data=f"filter_broadcasts_status_{next_status}_{sort_by}"
        ),
    ]
    buttons.append(sort_buttons)
    
    # Додаємо кнопки з розсилками (максимум 10 на сторінку)
    for broadcast in broadcasts:
        from .formatters import format_broadcast_list_item
        button_text = format_broadcast_list_item(broadcast)
        
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_broadcast_{broadcast.id}"
        )])
    
    # Додаємо пагінацію якщо є більше однієї сторінки
    if total_pages > 1:
        pagination_buttons = []
        
        # Кнопка "Попередня"
        if current_page > 1:
            pagination_buttons.append(InlineKeyboardButton(
                text="⬅️ Попередня",
                callback_data=f"broadcasts_page_{current_page - 1}"
            ))
        
        # Кнопка з номером поточної сторінки
        pagination_buttons.append(InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}",
            callback_data="current_broadcasts_page_info"
        ))
        
        # Кнопка "Наступна"
        if current_page < total_pages:
            pagination_buttons.append(InlineKeyboardButton(
                text="Наступна ➡️",
                callback_data=f"broadcasts_page_{current_page + 1}"
            ))
        
        buttons.append(pagination_buttons)
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_broadcast"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_detail_keyboard(broadcast_id: int) -> InlineKeyboardMarkup:
    """Клавіатура для детального перегляду розсилки"""
    buttons = []
    
    # Кнопка "Назад до списку"
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_broadcasts_list"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)



