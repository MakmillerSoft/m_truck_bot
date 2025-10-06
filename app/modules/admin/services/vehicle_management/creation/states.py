"""
FSM стани для створення авто
"""
from aiogram.fsm.state import StatesGroup, State


class VehicleCreationStates(StatesGroup):
    """Стани для створення авто"""
    
    # Основні дані (перші 5 кроків)
    waiting_for_vehicle_type = State()      # 1. Тип авто
    waiting_for_brand = State()             # 2. Марка авто
    waiting_for_model = State()             # 3. Модель авто
    waiting_for_vin_code = State()          # 4. VIN код авто
    waiting_for_body_type = State()         # 5. Тип кузова авто
    waiting_for_year = State()              # 6. Рік випуску авто
    
    # Додаткові стани (будуть додані пізніше)
    waiting_for_condition = State()         # 7. Стан авто
    waiting_for_price = State()             # 8. Вартість авто
    waiting_for_mileage = State()           # 9. Пробіг авто
    waiting_for_fuel_type = State()         # 10. Тип палива
    waiting_for_engine_volume = State()     # 11. Об'єм двигуна
    waiting_for_power_hp = State()          # 12. Потужність двигуна
    waiting_for_transmission = State()      # 13. Коробка передач
    waiting_for_wheel_radius = State()      # 14. Радіус коліс
    waiting_for_load_capacity = State()     # 15. Вантажопідйомність
    waiting_for_total_weight = State()      # 16. Загальна маса
    waiting_for_cargo_dimensions = State()  # 17. Габарити вантажного відсіку
    waiting_for_location = State()          # 18. Місцезнаходження
    waiting_for_description = State()       # 19. Опис авто
    waiting_for_photos = State()            # 20. Фото авто
    waiting_for_additional_photos = State() # Додаткові фото авто
    
    # Підсумкова картка
    summary_card = State()                  # Підсумкова картка
