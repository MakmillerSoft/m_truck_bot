"""
Клавіатури для інформації про компанію (клієнт)
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_company_info_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="🎵 TikTok",
                url="https://www.tiktok.com/@truckimports_ua?_t=ZM-8zkYjQlxaQH",
            ),
            InlineKeyboardButton(text="💬 Telegram", url="https://t.me/mtruck_sales"),
        ],
        [InlineKeyboardButton(text="🌐 Веб-сайт", callback_data="website_placeholder")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


