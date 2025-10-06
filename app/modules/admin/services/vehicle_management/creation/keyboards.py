"""
Клавіатури для створення авто
"""
from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.modules.database.models import VehicleType

# Роутер не потрібен для клавіатур, тільки для обробників


def get_vehicle_type_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору типу авто"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚛 Контейнеровози", callback_data="select_vehicle_type_container_carrier")],
            [InlineKeyboardButton(text="🚚 Напівпричепи контейнеровози", callback_data="select_vehicle_type_semi_container_carrier")],
            [InlineKeyboardButton(text="🔄 Змінні кузови", callback_data="select_vehicle_type_variable_body")],
            [InlineKeyboardButton(text="🚜 Сідельні тягачі", callback_data="select_vehicle_type_saddle_tractor")],
            [InlineKeyboardButton(text="🚛 Причіпи", callback_data="select_vehicle_type_trailer")],
            [InlineKeyboardButton(text="❄️ Рефрижератори", callback_data="select_vehicle_type_refrigerator")],
            [InlineKeyboardButton(text="🚐 Фургони", callback_data="select_vehicle_type_van")],
            [InlineKeyboardButton(text="🚌 Буси", callback_data="select_vehicle_type_bus")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_vehicle_management")]
        ]
    )


def get_text_input_keyboard(step_name: str, back_callback: str, skip_callback: str = None) -> InlineKeyboardMarkup:
    """Універсальна клавіатура для введення тексту"""
    buttons = []
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)])
    
    # Кнопка "Пропустити" (якщо потрібна)
    if skip_callback:
        buttons.append([InlineKeyboardButton(text="⏭️ Пропустити", callback_data=skip_callback)])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_brand_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення марки авто"""
    return get_text_input_keyboard(
        step_name="brand",
        back_callback="back_to_vehicle_type",
        skip_callback="skip_brand"
    )


def get_model_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення моделі авто"""
    return get_text_input_keyboard(
        step_name="model",
        back_callback="back_to_brand",
        skip_callback="skip_model"
    )


def get_vin_code_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення VIN коду"""
    return get_text_input_keyboard(
        step_name="vin_code",
        back_callback="back_to_model",
        skip_callback="skip_vin_code"
    )


def get_body_type_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення типу кузова"""
    return get_text_input_keyboard(
        step_name="body_type",
        back_callback="back_to_vin_code",
        skip_callback="skip_body_type"
    )


def get_year_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення року випуску"""
    return get_text_input_keyboard(
        step_name="year",
        back_callback="back_to_body_type",
        skip_callback="skip_year"
    )


def get_condition_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору стану авто"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Нове", callback_data="select_condition_new")],
            [InlineKeyboardButton(text="🔄 Вживане", callback_data="select_condition_used")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_year")],
            [InlineKeyboardButton(text="⏭️ Пропустити", callback_data="skip_condition")]
        ]
    )


def get_price_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення вартості авто"""
    return get_text_input_keyboard(
        step_name="price",
        back_callback="back_to_condition",
        skip_callback="skip_price"
    )


def get_mileage_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення пробігу авто"""
    return get_text_input_keyboard(
        step_name="mileage",
        back_callback="back_to_price",
        skip_callback="skip_mileage"
    )


def get_fuel_type_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору типу палива"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⛽ Дизель", callback_data="select_fuel_diesel")],
            [InlineKeyboardButton(text="⛽ Бензин", callback_data="select_fuel_petrol")],
            [InlineKeyboardButton(text="⛽ Газ", callback_data="select_fuel_gas")],
            [InlineKeyboardButton(text="⛽ Газ/Бензин", callback_data="select_fuel_gas_petrol")],
            [InlineKeyboardButton(text="⚡ Електро", callback_data="select_fuel_electric")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_mileage")],
            [InlineKeyboardButton(text="⏭️ Пропустити", callback_data="skip_fuel_type")]
        ]
    )


def get_engine_volume_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення об'єму двигуна"""
    return get_text_input_keyboard(
        step_name="engine_volume",
        back_callback="back_to_fuel_type",
        skip_callback="skip_engine_volume"
    )


def get_power_hp_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення потужності двигуна"""
    return get_text_input_keyboard(
        step_name="power_hp",
        back_callback="back_to_engine_volume",
        skip_callback="skip_power_hp"
    )


def get_transmission_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору коробки передач"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Автоматична", callback_data="select_transmission_automatic")],
            [InlineKeyboardButton(text="🕹️ Механічна", callback_data="select_transmission_manual")],
            [InlineKeyboardButton(text="🤖 Робот", callback_data="select_transmission_robot")],
            [InlineKeyboardButton(text="⚙️ Вариатор", callback_data="select_transmission_cvt")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_power_hp")],
            [InlineKeyboardButton(text="⏭️ Пропустити", callback_data="skip_transmission")]
        ]
    )


def get_wheel_radius_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення радіусу коліс"""
    return get_text_input_keyboard(
        step_name="wheel_radius",
        back_callback="back_to_transmission",
        skip_callback="skip_wheel_radius"
    )


def get_load_capacity_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення вантажопідйомності"""
    return get_text_input_keyboard(
        step_name="load_capacity",
        back_callback="back_to_wheel_radius",
        skip_callback="skip_load_capacity"
    )


def get_total_weight_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення загальної маси авто"""
    return get_text_input_keyboard(
        step_name="total_weight",
        back_callback="back_to_load_capacity",
        skip_callback="skip_total_weight"
    )


def get_cargo_dimensions_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення габаритів вантажного відсіку"""
    return get_text_input_keyboard(
        step_name="cargo_dimensions",
        back_callback="back_to_total_weight",
        skip_callback="skip_cargo_dimensions"
    )


def get_location_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для вибору місцезнаходження"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏙️ Луцьк", callback_data="select_location_lutsk")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_cargo_dimensions")],
            [InlineKeyboardButton(text="⏭️ Пропустити", callback_data="skip_location")]
        ]
    )


def get_description_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для введення опису авто"""
    return get_text_input_keyboard(
        step_name="description",
        back_callback="back_to_location",
        skip_callback="skip_description"
    )


def get_photos_input_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для завантаження фото авто (без кнопки Пропустити)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_description")]
        ]
    )


def get_photos_summary_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура після завантаження фото з кнопкою 'Додати ще'"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Додати ще", callback_data="add_more_photos")],
            [InlineKeyboardButton(text="✅ Завершити", callback_data="finish_vehicle_creation")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_description")]
        ]
    )


def get_additional_photos_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура для додаткових фото"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_photos_summary")]
        ]
    )
