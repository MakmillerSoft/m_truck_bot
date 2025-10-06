"""
Стани для пошуку користувачів
"""
from aiogram.fsm.state import State, StatesGroup


class UserSearchStates(StatesGroup):
    """Стани для пошуку користувачів"""
    
    waiting_for_id = State()
    waiting_for_telegram_id = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_username = State()
