"""
FSM стани для модуля пошуку
"""

from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    """Стани пошуку авто"""

    waiting_for_brand = State()
    waiting_for_min_price = State()
    waiting_for_max_price = State()
    waiting_for_year = State()
    waiting_for_mileage = State()
    waiting_for_location = State()
    waiting_for_type = State()
    waiting_for_contact_details = State()


class SavedVehiclesStates(StatesGroup):
    """Стани для роботи з збереженими авто"""

    waiting_for_notes = State()
    waiting_for_category = State()
    waiting_for_edit_notes = State()
