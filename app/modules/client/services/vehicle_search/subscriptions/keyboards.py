"""
Клавіатури для підписок
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_subscriptions_main_keyboard() -> InlineKeyboardMarkup:
    """Головне меню підписок"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Створити підписку", callback_data="create_subscription")],
        [InlineKeyboardButton(text="📋 Мої підписки", callback_data="view_subscriptions")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_vehicle_type_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору типу авто"""
    keyboard = [
        [InlineKeyboardButton(text="🚍 Вантажні фургони та рефрижератори", callback_data="sub_type_vans_and_refrigerators")],
        [InlineKeyboardButton(text="🚚 Контейнеровози (з причепами)", callback_data="sub_type_container_carriers")],
        [InlineKeyboardButton(text="🚛 Сідельні тягачі та напівпричепи", callback_data="sub_type_tractors_and_semi")],
        [InlineKeyboardButton(text="🚞 Змінні кузови", callback_data="sub_type_variable_body")],
        [InlineKeyboardButton(text="➡️ Пропустити", callback_data="sub_skip_type")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="sub_back_to_name")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_condition_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору стану"""
    keyboard = [
        [InlineKeyboardButton(text="✨ Новий", callback_data="sub_cond_new")],
        [InlineKeyboardButton(text="👌 Вживаний", callback_data="sub_cond_used")],
        [InlineKeyboardButton(text="➡️ Пропустити", callback_data="sub_skip_condition")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="sub_back_to_max_price")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_skip_back_keyboard(skip_callback: str, back_callback: str) -> InlineKeyboardMarkup:
    """Клавіатура Пропустити/Назад"""
    keyboard = [
        [InlineKeyboardButton(text="➡️ Пропустити", callback_data=skip_callback)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура підтвердження створення"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Створити підписку", callback_data="confirm_subscription")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="sub_back_to_condition")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_subscription")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_subscriptions_list_keyboard(subscriptions: List[Dict]) -> InlineKeyboardMarkup:
    """Клавіатура зі списком підписок"""
    keyboard = []
    
    for sub in subscriptions:
        status_emoji = "🟢" if sub.get('is_active') else "🔴"
        button_text = f"{status_emoji} {sub.get('subscription_name', 'Без назви')}"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"view_sub_{sub['id']}"
            )
        ])
    
    if not subscriptions:
        keyboard.append([InlineKeyboardButton(
            text="➕ Створити першу підписку",
            callback_data="create_subscription"
        )])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="client_subscriptions")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_subscription_detail_keyboard(subscription_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Клавіатура для деталей підписки"""
    toggle_text = "⏸️ Призупинити" if is_active else "▶️ Активувати"
    toggle_callback = f"toggle_sub_{subscription_id}"
    
    keyboard = [
        [InlineKeyboardButton(text=toggle_text, callback_data=toggle_callback)],
        [InlineKeyboardButton(text="🗑️ Видалити", callback_data=f"delete_sub_{subscription_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="view_subscriptions")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_delete_confirmation_keyboard(subscription_id: int) -> InlineKeyboardMarkup:
    """Клавіатура підтвердження видалення"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Так, видалити", callback_data=f"confirm_delete_sub_{subscription_id}")],
        [InlineKeyboardButton(text="❌ Ні, залишити", callback_data=f"view_sub_{subscription_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



