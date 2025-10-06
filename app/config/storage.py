"""
Конфігурація FSM Storage
"""

from typing import Optional
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage

try:
    from aiogram.fsm.storage.redis import RedisStorage

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .settings import settings


def create_storage() -> BaseStorage:
    """
    Створити FSM storage в залежності від конфігурації
    """
    storage_type = getattr(settings, "fsm_storage_type", "memory").lower()

    if storage_type == "redis" and REDIS_AVAILABLE:
        try:
            redis_url = getattr(settings, "redis_url", "redis://localhost:6379/1")
            storage = RedisStorage.from_url(redis_url)
            print(f"✅ Використовуємо Redis storage: {redis_url}")
            return storage
        except Exception as e:
            print(f"⚠️ Помилка підключення до Redis: {e}")
            print("🔄 Використовуємо MemoryStorage")
            return MemoryStorage()

    elif storage_type == "redis" and not REDIS_AVAILABLE:
        print("⚠️ Redis недоступний (встановіть: pip install redis)")
        print("🔄 Використовуємо MemoryStorage")
        return MemoryStorage()

    else:
        print("📝 Використовуємо MemoryStorage")
        return MemoryStorage()


def get_storage_info() -> dict:
    """Отримати інформацію про поточний storage"""
    storage = create_storage()

    return {
        "type": storage.__class__.__name__,
        "persistent": storage.__class__.__name__ != "MemoryStorage",
        "description": {
            "MemoryStorage": "Зберігає дані в пам'яті (втрачаються при перезапуску)",
            "RedisStorage": "Зберігає дані в Redis (персистентні)",
        }.get(storage.__class__.__name__, "Невідомий тип storage"),
    }
