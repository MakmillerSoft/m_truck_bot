"""
Middleware для очищення FSM станів при зміні ролей користувача
"""
import logging
from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.modules.database.manager import db_manager
from app.modules.database.models import UserRole
from app.config.settings import settings

logger = logging.getLogger(__name__)


class RoleChangeGuardMiddleware(BaseMiddleware):
    """
    Middleware для очищення FSM станів при зміні ролей користувача.
    Перевіряє поточну роль користувача і очищає стани, якщо вона змінилася.
    """
    
    def __init__(self):
        super().__init__()
        self._user_roles_cache = {}  # Кеш ролей користувачів
    
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        
        # Пропускаємо /start команду
        if isinstance(event, Message) and event.text == "/start":
            return await handler(event, data)
        
        # Отримуємо поточну роль користувача
        db_user = await db_manager.get_user_by_telegram_id(user_id)
        current_role = db_user.role if db_user else UserRole.BUYER
        
        # Перевіряємо, чи змінилася роль
        cached_role = self._user_roles_cache.get(user_id)
        
        if cached_role is not None and cached_role != current_role:
            logger.info(f"🔄 Роль користувача {user_id} змінилася з {cached_role.value} на {current_role.value}")
            
            # Очищаємо FSM стан
            state: FSMContext = data.get('state')
            if state:
                await state.clear()
                logger.info(f"🧹 Очищено FSM стан для користувача {user_id}")
            
            # Якщо користувач втратив права адміна, відправляємо повідомлення
            if cached_role == UserRole.ADMIN and current_role == UserRole.BUYER:
                founder_ids = settings.get_admin_ids()
                if user_id not in founder_ids:  # Не засновник
                    if isinstance(event, Message):
                        await event.answer(
                            "⚠️ <b>Ваші права адміністратора були відкликані</b>\n\n"
                            "Ви більше не маєте доступу до адміністративних функцій.",
                            parse_mode="HTML"
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer(
                            "⚠️ Ваші права адміністратора були відкликані",
                            show_alert=True
                        )
                        # Перенаправляємо на головне меню клієнта
                        from app.modules.client.services.authentication.registration.keyboards import get_main_menu_inline_keyboard
                        await event.message.edit_text(
                            "🔙 <b>Повернення до головного меню</b>\n\n"
                            "Ваші права адміністратора були відкликані.",
                            reply_markup=get_main_menu_inline_keyboard(),
                            parse_mode="HTML"
                        )
        
        # Оновлюємо кеш
        self._user_roles_cache[user_id] = current_role
        
        return await handler(event, data)
    
    def clear_user_cache(self, user_id: int):
        """Очистити кеш конкретного користувача"""
        if user_id in self._user_roles_cache:
            del self._user_roles_cache[user_id]
            logger.debug(f"Очищено кеш ролі для користувача {user_id}")
    
    def clear_all_cache(self):
        """Очистити весь кеш ролей"""
        self._user_roles_cache.clear()
        logger.debug("Очищено весь кеш ролей")


# Глобальний екземпляр middleware для доступу з інших частин коду
role_change_guard = RoleChangeGuardMiddleware()
