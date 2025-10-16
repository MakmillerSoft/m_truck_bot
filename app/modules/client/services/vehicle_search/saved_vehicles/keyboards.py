"""
Клавіатури для модуля збережених авто
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_saved_vehicle_card_keyboard(vehicle_id: int, current_index: int, total: int) -> InlineKeyboardMarkup:
    """Клавіатура для картки збереженого авто"""
    keyboard = []
    
    # Кнопка видалення зі збережених
    keyboard.append([
        InlineKeyboardButton(
            text="❌ Видалити з обраного",
            callback_data=f"saved_remove_{vehicle_id}"
        )
    ])
    
    # Кнопка залишити заявку (використовуємо той самий callback що в каталозі)
    keyboard.append([
        InlineKeyboardButton(
            text="📝 Залишити заявку",
            callback_data=f"contact_seller_{vehicle_id}"
        )
    ])
    
    # Навігація
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Попереднє", callback_data=f"saved_prev_{vehicle_id}")
        )
    if current_index < total - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="Наступне ➡️", callback_data=f"saved_next_{vehicle_id}")
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопка назад
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_empty_saved_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для порожнього списку збережених"""
    keyboard = [
        [InlineKeyboardButton(text="🚛 Переглянути каталог", callback_data="client_catalog_menu")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

