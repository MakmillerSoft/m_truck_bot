"""
Клієнтські сервіси

Цей модуль містить всі клієнтські сервіси включаючи:
- authentication: Аутентифікація та управління профілем
- vehicle_search: Пошук та робота з авто
- communication: Комунікація з менеджерами
- information: Інформаційні сторінки
"""

from .authentication import router as authentication_router
# from .vehicle_search import router as vehicle_search_router  # Тимчасово закоментовано
# from .communication import router as communication_router  # Тимчасово закоментовано
# from .information import router as information_router  # Тимчасово закоментовано

__all__ = [
    'authentication_router',
    # 'vehicle_search_router',  # Тимчасово закоментовано
    # 'communication_router',  # Тимчасово закоментовано
    # 'information_router'  # Тимчасово закоментовано
]
