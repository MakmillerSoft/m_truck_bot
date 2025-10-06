"""
Клієнтська частина Telegram бота
Модульна архітектура з сервісами та спільними компонентами
"""

from aiogram import Router

# Створюємо головний роутер для клієнтської частини
router = Router()

# Імпортуємо сервіси (підключаємо першими для вищого пріоритету)
from .services.authentication import router as authentication_router
# from .services.vehicle_search import router as vehicle_search_router  # Тимчасово закоментовано
# from .services.communication import router as communication_router  # Тимчасово закоментовано
# from .services.information import router as information_router  # Тимчасово закоментовано

# Включаємо сервіси (вищий пріоритет)
router.include_router(authentication_router)
# router.include_router(vehicle_search_router)  # Тимчасово закоментовано
# router.include_router(communication_router)  # Тимчасово закоментовано
# router.include_router(information_router)  # Тимчасово закоментовано

# Імпортуємо головні обробники (підключаємо після сервісів)
# from .core.main_handlers import router as main_handlers_router  # Тимчасово закоментовано
# from .core.access_control import router as access_control_router  # Тимчасово закоментовано

# Включаємо головні обробники (нижчий пріоритет)
# router.include_router(main_handlers_router)  # Тимчасово закоментовано
# router.include_router(access_control_router)  # Тимчасово закоментовано
