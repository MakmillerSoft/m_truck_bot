"""
Клавіатури для блоку "Всі авто"
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional

from app.modules.database.models import VehicleModel
from ..shared.translations import translate_field_value


def get_vehicles_list_keyboard(
    vehicles: List[VehicleModel], 
    current_page: int = 1, 
    total_pages: int = 1,
    sort_by: str = "created_at_desc",
    status_filter: str = "all"
) -> InlineKeyboardMarkup:
    """Клавіатура зі списком авто та пагінацією"""
    buttons = []
    
    # Додаємо кнопки сортування (3 кнопки в 1 рядок)
    from ..shared.translations import translate_field_value
    status_text = "Всі авто" if status_filter == "all" else translate_field_value('status', status_filter)
    
    # Визначаємо наступний статус для циклічного перемикання
    if status_filter == "all":
        next_status = "available"
    elif status_filter == "available":
        next_status = "sold"
    else:  # sold
        next_status = "all"
    
    sort_buttons = [
        InlineKeyboardButton(
            text="📅 Дата ↓" if sort_by == "created_at_desc" else "📅 Дата ↑" if sort_by == "created_at_asc" else "📅 Дата",
            callback_data=f"sort_vehicles_created_at_desc_{status_filter}" if sort_by != "created_at_desc" else f"sort_vehicles_created_at_asc_{status_filter}"
        ),
        InlineKeyboardButton(
            text="💰 Ціна ↓" if sort_by == "price_desc" else "💰 Ціна ↑" if sort_by == "price_asc" else "💰 Ціна",
            callback_data=f"sort_vehicles_price_desc_{status_filter}" if sort_by != "price_desc" else f"sort_vehicles_price_asc_{status_filter}"
        ),
        InlineKeyboardButton(
            text=f"📋 {status_text}",
            callback_data=f"filter_status_{next_status}_{sort_by}"
        ),
    ]
    buttons.append(sort_buttons)
    
    # Додаємо кнопки з авто (максимум 10 на сторінку)
    for vehicle in vehicles:
        # Форматуємо текст кнопки: Марка + Модель + Рік + Ціна
        button_text = f"🚛 {vehicle.brand or 'Без марки'}"
        
        if vehicle.model:
            button_text += f" {vehicle.model}"
        
        if vehicle.year:
            button_text += f" ({vehicle.year})"
        
        if vehicle.price:
            button_text += f" - {vehicle.price:,.0f}$"
        
        # Обмежуємо довжину тексту кнопки
        if len(button_text) > 50:
            button_text = button_text[:47] + "..."
        
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_vehicle_{vehicle.id}"
        )])
    
    # Додаємо пагінацію якщо є більше однієї сторінки
    if total_pages > 1:
        pagination_buttons = []
        
        # Кнопка "Попередня"
        if current_page > 1:
            pagination_buttons.append(InlineKeyboardButton(
                text="⬅️ Попередня",
                callback_data=f"vehicles_page_{current_page - 1}"
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
                callback_data=f"vehicles_page_{current_page + 1}"
            ))
        
        buttons.append(pagination_buttons)
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_vehicles"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vehicle_detail_keyboard(vehicle_id: int, status: str = "available", group_message_id: int = None) -> InlineKeyboardMarkup:
    """Клавіатура для детального перегляду авто"""
    from ..shared.translations import translate_field_value
    from app.config.settings import settings
    
    # Визначаємо текст кнопки статусу
    status_text = translate_field_value('status', status)
    status_callback = f"toggle_status_{vehicle_id}"
    
    buttons = [
        [
            InlineKeyboardButton(
                text="✏️ Редагувати",
                callback_data=f"edit_vehicle_{vehicle_id}"
            ),
            InlineKeyboardButton(
                text="📤 Опублікувати",
                callback_data=f"publish_vehicle_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Видалити",
                callback_data=f"delete_vehicle_{vehicle_id}"
            ),
            InlineKeyboardButton(
                text=f"📋 {status_text}",
                callback_data=status_callback
            ),
        ],
    ]
    
    # Додаємо кнопку "Перейти в групу" якщо авто опубліковано в групі
    if group_message_id and settings.group_chat_id:
        group_chat_id = settings.group_chat_id.replace('@', '')
        group_link = f"https://t.me/{group_chat_id}/{group_message_id}"
        buttons.append([
            InlineKeyboardButton(
                text="👥 Перейти в групу",
                url=group_link
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_vehicles_list"
        ),
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vehicle_edit_keyboard(vehicle_id: int) -> InlineKeyboardMarkup:
    """Клавіатура для редагування авто"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📝 Редагувати дані",
                callback_data=f"edit_vehicle_data_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📷 Редагувати фото",
                callback_data=f"edit_vehicle_photos_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=f"view_vehicle_{vehicle_id}"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vehicle_delete_confirmation_keyboard(vehicle_id: int) -> InlineKeyboardMarkup:
    """Клавіатура підтвердження видалення авто"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Так, видалити",
                callback_data=f"confirm_delete_vehicle_{vehicle_id}"
            ),
            InlineKeyboardButton(
                text="❌ Скасувати",
                callback_data=f"view_vehicle_{vehicle_id}"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_vehicle_stats_keyboard(vehicle_id: int) -> InlineKeyboardMarkup:
    """Клавіатура для статистики авто"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📈 Перегляди",
                callback_data=f"vehicle_views_{vehicle_id}"
            ),
            InlineKeyboardButton(
                text="💾 Збереження",
                callback_data=f"vehicle_saves_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 Історія",
                callback_data=f"vehicle_history_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=f"view_vehicle_{vehicle_id}"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_empty_vehicles_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура коли немає авто"""
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ Додати перше авто",
                callback_data="add_vehicle"
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
