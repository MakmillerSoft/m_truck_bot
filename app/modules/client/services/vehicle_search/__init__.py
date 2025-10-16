"""
Сервіс пошуку авто

Цей модуль надає функціональність пошуку та роботи з авто для клієнтів.
Включає швидкий пошук, розширений пошук, збережені авто та підписки.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from .quick_search import quick_search_router
from .advanced_search import advanced_search_router
from .saved_vehicles import saved_vehicles_router
from .subscriptions import subscriptions_router

# Створюємо головний роутер для пошуку авто
router = Router()

# Включаємо підроутери
router.include_router(quick_search_router)
router.include_router(advanced_search_router)
router.include_router(saved_vehicles_router)
router.include_router(subscriptions_router)

# Головний обробник пошуку
@router.message(Command("search"))
async def search_command(message: Message):
    """Команда для початку пошуку"""
    # Це буде оброблено модулем quick_search
    pass

__all__ = [
    'router',
    'quick_search_router',
    'advanced_search_router',
    'saved_vehicles_router',
    'subscriptions_router'
]

