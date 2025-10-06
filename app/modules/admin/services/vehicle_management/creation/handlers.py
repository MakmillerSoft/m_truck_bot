"""
Головний файл обробників для створення авто
Імпортує всі підмодулі для організації коду
"""
import logging
from aiogram import Router

from .basic_steps import router as basic_steps_router
from .navigation import router as navigation_router
from .additional_steps import router as additional_steps_router
from .summary_card import router as summary_card_router

logger = logging.getLogger(__name__)

# Створюємо головний роутер
router = Router()

# Включаємо всі підмодулі
router.include_router(basic_steps_router)
router.include_router(navigation_router)
router.include_router(additional_steps_router)
router.include_router(summary_card_router)
