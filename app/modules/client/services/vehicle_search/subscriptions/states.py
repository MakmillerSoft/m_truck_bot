"""
FSM стани для підписок на авто
"""
from aiogram.fsm.state import State, StatesGroup


class SubscriptionStates(StatesGroup):
    """Стани для створення підписки"""
    
    waiting_for_subscription_name = State()  # Очікування назви підписки
    waiting_for_brand = State()  # Очікування бренду
    waiting_for_min_year = State()  # Очікування мінімального року
    waiting_for_max_year = State()  # Очікування максимального року
    waiting_for_min_price = State()  # Очікування мінімальної ціни
    waiting_for_max_price = State()  # Очікування максимальної ціни







