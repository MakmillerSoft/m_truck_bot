"""
Система контролю доступу для адмін панелі
"""
import logging
from typing import List, Optional, Union
from aiogram.types import User, Message, CallbackQuery
from aiogram.filters import BaseFilter

from app.config.settings import settings
from app.modules.database.manager import db_manager
from app.modules.database.models import UserRole

logger = logging.getLogger(__name__)


class AdminAccessFilter(BaseFilter):
    """Фільтр для перевірки доступу до адмін панелі"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.admin_ids = settings.get_admin_ids()
            if self.admin_ids:
                logger.info(f"Завантажено {len(self.admin_ids)} адміністраторів: {self.admin_ids}")
            else:
                logger.warning("Список адміністраторів порожній")
            self._initialized = True
    
    async def __call__(self, obj: Union[Message, CallbackQuery]) -> bool:
        """Перевірити чи користувач є адміністратором і чи не заблокований"""
        logger.debug(f"Перевіряємо доступ для об'єкта типу: {type(obj)}")
        
        # Отримуємо користувача з об'єкта
        user = obj.from_user
        if not user:
            logger.warning("Не вдалося отримати користувача з об'єкта")
            return False
        
        # Ідентифікатор користувача
        user_id = user.id
        
        logger.debug(f"Користувач: {user.id}, список owner'ів з env: {self.admin_ids}")
        
        # 1) Дозволити якщо користувач є owner з .env
        if user.id in self.admin_ids:
            logger.debug(f"Owner {user.id} отримав доступ")
            return True
        
        # 2) Інакше перевірити роль у БД (ADMIN)
        try:
            db_user = await db_manager.get_user_by_telegram_id(user.id)
            is_admin = bool(db_user and getattr(db_user, "role", None) == UserRole.ADMIN)
        except Exception as e:
            logger.error(f"Помилка отримання користувача з БД: {e}")
            is_admin = False
        
        if is_admin:
            logger.debug(f"Користувач {user.id} ({user.username}) отримав доступ до адмін панелі")
        else:
            logger.warning(f"Користувач {user.id} ({user.username}) спробував отримати доступ до адмін панелі")
        
        return is_admin


def is_admin(user_id: int) -> bool:
    """Перевірити чи користувач є адміністратором"""
    try:
        # Owner з .env або ADMIN у БД
        if user_id in settings.get_admin_ids():
            return True
        user = db_manager.get_user_by_telegram_id_sync(user_id) if hasattr(db_manager, 'get_user_by_telegram_id_sync') else None
        if user and getattr(user, 'role', None) == UserRole.ADMIN:
            return True
        return False
        
    except Exception as e:
        logger.error(f"Помилка перевірки адміністратора: {e}")
        return False


def get_admin_ids() -> List[int]:
    """Отримати список ID адміністраторів"""
    return settings.get_admin_ids()
