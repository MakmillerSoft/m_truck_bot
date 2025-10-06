"""
FSM стани для модуля реєстрації користувачів
"""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Стани реєстрації користувача"""

    waiting_for_phone = State()  # Очікування номера телефону (контакт або текст)
    waiting_for_phone_manual = State()  # Очікування ручного вводу номера
