"""
Адмін панель для Telegram бота
Модульна архітектура з сервісами та спільними компонентами
"""

from aiogram import Router

# Створюємо головний роутер для адмін панелі
router = Router()

# Імпортуємо сервіси (підключаємо першими для вищого пріоритету)
from .services.vehicle_management import router as vehicle_management_router
from .services.user_management import user_management_router
from .services.requests import router as requests_router
from .services.broadcast import broadcast_router
from .services.export import export_router
# from .services.analytics import router as analytics_router
# from .services.communication import router as communication_router
# from .services.settings import router as settings_router

# Включаємо сервіси (вищий пріоритет)
router.include_router(vehicle_management_router)
router.include_router(user_management_router)
router.include_router(requests_router)
router.include_router(broadcast_router)
router.include_router(export_router)
# router.include_router(analytics_router)
# router.include_router(communication_router)
# router.include_router(settings_router)

# Імпортуємо головні обробники (підключаємо після сервісів)
from .core.main_handlers import router as main_handlers_router
from .core.access_denied import router as access_denied_router

# Включаємо головні обробники (нижчий пріоритет)
router.include_router(main_handlers_router)
router.include_router(access_denied_router)
