"""
Модуль публікації авто для адмін панелі
"""
from aiogram import Router

# Створюємо роутер для модуля публікації авто
router = Router()

# Імпортуємо обробники
from .bot_publisher import BotPublisher, create_bot_publisher
from .group_publisher import GroupPublisher, create_group_publisher
from .group_templates import (
    format_group_vehicle_card,
    get_topic_id_for_vehicle_type,
    format_media_group_caption,
    get_group_publication_keyboard,
    validate_vehicle_data_for_publication
)

# Включаємо обробники (якщо будуть)
# router.include_router(handlers_router)



