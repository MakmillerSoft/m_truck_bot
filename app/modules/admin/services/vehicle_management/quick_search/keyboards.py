"""
Клавіатури для швидкого пошуку авто
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_quick_search_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура головного меню швидкого пошуку"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 По параметрам",
                    callback_data="search_by_parameters"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 По фільтру",
                    callback_data="search_by_filter"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="back_to_vehicle_management"
                )
            ]
        ]
    )


def get_search_parameters_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура вибору параметрів пошуку"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🆔 По ID авто",
                    callback_data="search_by_id"
                ),
                InlineKeyboardButton(
                    text="🔢 По VIN коду",
                    callback_data="search_by_vin"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏷️ По марці",
                    callback_data="search_by_brand"
                ),
                InlineKeyboardButton(
                    text="🚗 По моделі",
                    callback_data="search_by_model"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 По роках випуску",
                    callback_data="search_by_years"
                ),
                InlineKeyboardButton(
                    text="💰 По вартості",
                    callback_data="search_by_price"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="back_to_quick_search"
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
                    callback_data="search_by_parameters"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 До пошуку",
                    callback_data="back_to_quick_search"
                )
            ]
        ]
    )


def get_back_to_parameters_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура повернення до параметрів пошуку"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 До параметрів",
                    callback_data="search_by_parameters"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 До пошуку",
                    callback_data="back_to_quick_search"
                )
            ]
        ]
    )
