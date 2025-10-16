"""
Стани для модуля повідомлень
"""

from aiogram.fsm.state import State, StatesGroup


class MessageStates(StatesGroup):
    """Стани для залишення заявок"""

    waiting_for_request_details = State()


