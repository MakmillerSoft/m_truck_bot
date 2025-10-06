"""
FSM стани для модуля повідомлень
"""

from aiogram.fsm.state import State, StatesGroup


class ManagerRequestStates(StatesGroup):
    """Стани заявок менеджеру"""

    waiting_for_details = State()
