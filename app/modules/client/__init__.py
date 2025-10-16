"""
Клієнтська частина Telegram бота
Модульна архітектура з сервісами та спільними компонентами
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery

# Створюємо головний роутер для клієнтської частини
router = Router()

# Імпортуємо сервіси (підключаємо першими для вищого пріоритету)
from .services.authentication import router as authentication_router
from .services.vehicle_search import router as vehicle_search_router
from .services.messages import messages_router
from .services.information import router as information_router

# Включаємо сервіси (вищий пріоритет)
router.include_router(authentication_router)
router.include_router(messages_router)  # Повідомлення перед пошуком авто
router.include_router(vehicle_search_router)
router.include_router(information_router)

# Обробник для ігнорування адмінських callback'ів (щоб не спричиняти попередження)
@router.callback_query(F.data.startswith("admin_"))
async def ignore_admin_callbacks(callback: CallbackQuery):
    """Ігноруємо адмінські callback'и в клієнтській частині"""
    # Перевіряємо, чи користувач є адміном
    from app.config.settings import settings
    if callback.from_user.id in settings.get_admin_ids():
        # Якщо адмін - не обробляємо, дозволяємо передати далі до адмінського роутера
        return
    
    # Якщо не адмін - показуємо повідомлення
    await callback.answer("❌ Ця функція доступна лише адміністраторам", show_alert=True)

# Імпортуємо головні обробники (підключаємо після сервісів)
# from .core.main_handlers import router as main_handlers_router  # Тимчасово закоментовано
# from .core.access_control import router as access_control_router  # Тимчасово закоментовано

# Включаємо головні обробники (нижчий пріоритет)
# router.include_router(main_handlers_router)  # Тимчасово закоментовано
# router.include_router(access_control_router)  # Тимчасово закоментовано
