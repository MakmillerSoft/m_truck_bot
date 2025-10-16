"""
FSM стани для швидкого пошуку авто (клієнтська частина)
"""
from aiogram.fsm.state import State, StatesGroup


class ClientSearchStates(StatesGroup):
    """Стани для швидкого пошуку та заявок на авто"""
    
    waiting_for_application_details = State()  # Очікування деталей заявки
