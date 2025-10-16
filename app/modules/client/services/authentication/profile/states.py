"""
Стани для модуля профілю (клієнтська частина)
"""

from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """Стани для редагування профілю"""

    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_phone = State()


