"""
FSM стани для модуля аутентифікації
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Стани реєстрації користувача"""

    waiting_for_phone = State()
