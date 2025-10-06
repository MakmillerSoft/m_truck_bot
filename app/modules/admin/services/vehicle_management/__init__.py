"""
Сервіс управління авто для адмін панелі
"""
from aiogram import Router

# Створюємо роутер для сервісу управління авто
router = Router()

# Імпортуємо модулі
from .creation import router as creation_router
from .listing import router as listing_router
from .stats import router as stats_router
from .editing import router as editing_router
from .deletion import router as deletion_router
from .quick_search import router as quick_search_router

# Включаємо модулі
router.include_router(creation_router)
router.include_router(listing_router)
router.include_router(stats_router)
router.include_router(editing_router)
router.include_router(deletion_router)
router.include_router(quick_search_router)

