"""
Клавіатури для інформаційного модуля
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_company_info_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура з інформацією про компанію та соцмережами"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🎵 TikTok",
                url="https://www.tiktok.com/@truckimports_ua?_t=ZM-8zkYjQlxaQH",
            ),
            InlineKeyboardButton(text="💬 Telegram", url="https://t.me/mtruck_sales"),
        ],
        [InlineKeyboardButton(text="🌐 Веб-сайт", callback_data="website_placeholder")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_contacts_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура з контактами"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🗺️ Показати на карті",
                url="https://maps.app.goo.gl/ZHxCwvruYTxhMJV46",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
