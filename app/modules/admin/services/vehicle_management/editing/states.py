"""
FSM стани для редагування авто
"""
from aiogram.fsm.state import StatesGroup, State


class VehicleEditingStates(StatesGroup):
    """Стани для редагування авто"""
    
    # Головний стан редагування
    editing_menu = State()                    # Меню вибору поля для редагування
    
    # Стани редагування полів (використовуємо існуючі з creation)
    waiting_for_vehicle_type_edit = State()   # Редагування типу авто
    waiting_for_brand_edit = State()          # Редагування марки
    waiting_for_model_edit = State()          # Редагування моделі
    waiting_for_vin_code_edit = State()       # Редагування VIN коду
    waiting_for_body_type_edit = State()      # Редагування типу кузова
    waiting_for_year_edit = State()           # Редагування року випуску
    waiting_for_condition_edit = State()      # Редагування стану авто
    waiting_for_price_edit = State()          # Редагування вартості
    waiting_for_mileage_edit = State()        # Редагування пробігу
    waiting_for_fuel_type_edit = State()      # Редагування типу палива
    waiting_for_engine_volume_edit = State()  # Редагування об'єму двигуна
    waiting_for_power_hp_edit = State()       # Редагування потужності
    waiting_for_transmission_edit = State()   # Редагування коробки передач
    waiting_for_wheel_radius_edit = State()   # Редагування радіуса коліс
    waiting_for_load_capacity_edit = State()  # Редагування вантажопідйомності
    waiting_for_total_weight_edit = State()   # Редагування загальної маси
    waiting_for_cargo_dimensions_edit = State()  # Редагування габаритів
    waiting_for_location_edit = State()       # Редагування місцезнаходження
    waiting_for_description_edit = State()    # Редагування опису
    waiting_for_photos_edit = State()         # Редагування фото для групи
    waiting_for_main_photo_edit = State()     # Редагування головного фото
    waiting_for_add_photos = State()          # Додавання ще фото
    waiting_for_replace_photos = State()      # Заміна всіх фото
