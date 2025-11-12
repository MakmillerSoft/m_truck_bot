"""
Клавіатури для видалення авто
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_deletion_confirmation_keyboard(vehicle_id: int) -> InlineKeyboardMarkup:
    """Клавіатура підтвердження видалення авто"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🗑️ ТАК, ВИДАЛИТИ",
                callback_data=f"confirm_delete_vehicle_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌ СКАСУВАТИ",
                callback_data=f"cancel_delete_vehicle_{vehicle_id}"
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


def get_deletion_success_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура після успішного видалення авто"""
    buttons = [
        [
            InlineKeyboardButton(
                text="📋 Повернутися до списку авто",
                callback_data="back_to_vehicles_after_deletion"
            ),
        ],
        [
            InlineKeyboardButton(
                text="➕ Додати нове авто",
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


def get_deletion_cancelled_keyboard(vehicle_id: int) -> InlineKeyboardMarkup:
    """Клавіатура після скасування видалення авто"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✏️ Редагувати авто",
                callback_data=f"edit_vehicle_{vehicle_id}"
            ),
            InlineKeyboardButton(
                text="📤 Опублікувати авто",
                callback_data=f"publish_vehicle_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_vehicles_list"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_bulk_deletion_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для масового видалення авто"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🗑️ Видалити всі авто",
                callback_data="bulk_delete_all_vehicles"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Видалити неактивні авто",
                callback_data="bulk_delete_inactive_vehicles"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Видалити авто без фото",
                callback_data="bulk_delete_vehicles_without_photos"
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


def get_bulk_deletion_confirmation_keyboard(operation_type: str) -> InlineKeyboardMarkup:
    """Клавіатура підтвердження масового видалення"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🗑️ ТАК, ВИКОНАТИ МАСОВЕ ВИДАЛЕННЯ",
                callback_data=f"confirm_bulk_delete_{operation_type}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌ СКАСУВАТИ",
                callback_data="cancel_bulk_deletion"
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


def get_deletion_preview_keyboard(vehicle_id: int) -> InlineKeyboardMarkup:
    """Клавіатура для попереднього перегляду перед видаленням"""
    buttons = [
        [
            InlineKeyboardButton(
                text="👁️ Переглянути деталі",
                callback_data=f"view_vehicle_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🗑️ Продовжити видалення",
                callback_data=f"delete_vehicle_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌ Скасувати видалення",
                callback_data=f"cancel_delete_vehicle_{vehicle_id}"
            ),
        ],
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
