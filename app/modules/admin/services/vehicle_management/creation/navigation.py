"""
Обробники навігації (кнопки "Назад" та "Пропустити")
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.utils.formatting import get_default_parse_mode
from app.modules.admin.core.access_control import AdminAccessFilter
from .states import VehicleCreationStates
from .keyboards import (
    get_vehicle_type_keyboard,
    get_brand_input_keyboard,
    get_model_input_keyboard,
    get_vin_code_input_keyboard,
    get_body_type_input_keyboard,
    get_year_input_keyboard,
    get_condition_keyboard,
    get_price_input_keyboard,
    get_mileage_input_keyboard,
    get_fuel_type_keyboard,
    get_engine_volume_input_keyboard,
    get_power_hp_input_keyboard,
    get_transmission_keyboard,
    get_wheel_radius_input_keyboard,
    get_load_capacity_input_keyboard,
    get_total_weight_input_keyboard,
    get_cargo_dimensions_input_keyboard,
    get_location_keyboard,
    get_description_input_keyboard,
    get_photos_input_keyboard
)

logger = logging.getLogger(__name__)
router = Router()

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())


# ===== КНОПКИ "НАЗАД" =====

@router.callback_query(F.data == "back_to_vehicle_management")
async def back_to_vehicle_management(callback: CallbackQuery, state: FSMContext):
    """Повернення до управління авто"""
    await callback.answer()
    await state.clear()
    
    from app.modules.admin.shared.modules.keyboards.main_keyboards import get_admin_vehicles_keyboard
    
    vehicles_text = """
🚛 <b>Управління авто</b>

<b>Доступні дії:</b>
• ➕ <b>Додати авто</b> - створити нове оголошення
• 📋 <b>Всі авто</b> - переглянути всі авто
• 🔍 <b>Швидкий пошук</b> - пошук по параметрах
• 📊 <b>Статистика</b> - аналітика по авто
• ⚡ <b>Швидкі дії</b> - масові операції

Оберіть дію:
"""
    
    await callback.message.edit_text(
        vehicles_text,
        reply_markup=get_admin_vehicles_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_vehicle_type")
async def back_to_vehicle_type(callback: CallbackQuery, state: FSMContext):
    """Повернення до вибору типу авто"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_vehicle_type)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 1 з 20:</b> Оберіть тип вантажного авто

Виберіть тип авто зі списку нижче:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_vehicle_type_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_brand")
async def back_to_brand(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення марки"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_brand)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 2 з 20:</b> Введіть марку авто

Введіть марку вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_brand_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_model")
async def back_to_model(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення моделі"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_model)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 3 з 20:</b> Введіть модель авто

Введіть модель вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_model_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_vin_code")
async def back_to_vin_code(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення VIN коду"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_vin_code)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 4 з 20:</b> Введіть VIN код авто

Введіть VIN код вантажного авто (опціонально):
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_vin_code_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_body_type")
async def back_to_body_type(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення типу кузова"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_body_type)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 5 з 20:</b> Введіть тип кузова авто

Введіть тип кузова вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_body_type_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_year")
async def back_to_year(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення року"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_year)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 6 з 20:</b> Введіть рік випуску авто

Введіть рік випуску вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_year_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


# ===== КНОПКИ "ПРОПУСТИТИ" =====

@router.callback_query(F.data == "skip_brand")
async def skip_brand(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення марки"""
    await callback.answer("Марку пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_model)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 3 з 20:</b> Введіть модель авто

Введіть модель вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_model_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_model")
async def skip_model(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення моделі"""
    await callback.answer("Модель пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_vin_code)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 4 з 20:</b> Введіть VIN код авто

Введіть VIN код вантажного авто (опціонально):
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_vin_code_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_vin_code")
async def skip_vin_code(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення VIN коду"""
    await callback.answer("VIN код пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_body_type)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 5 з 20:</b> Введіть тип кузова авто

Введіть тип кузова вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_body_type_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_body_type")
async def skip_body_type(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення типу кузова"""
    await callback.answer("Тип кузова пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_year)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 6 з 20:</b> Введіть рік випуску авто

Введіть рік випуску вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_year_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_year")
async def skip_year(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення року"""
    await callback.answer("Рік пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_condition)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 7 з 20:</b> Оберіть стан авто

Оберіть стан вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_condition_keyboard(),
        parse_mode=get_default_parse_mode()
    )


# ===== КНОПКИ "НАЗАД" ДЛЯ КРОКІВ 7-16 =====

@router.callback_query(F.data == "back_to_condition")
async def back_to_condition(callback: CallbackQuery, state: FSMContext):
    """Повернення до вибору стану авто"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_condition)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 7 з 20:</b> Оберіть стан авто

Оберіть стан вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_condition_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_price")
async def back_to_price(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення вартості"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_price)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 8 з 20:</b> Введіть вартість авто

Введіть вартість вантажного авто в USD:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_price_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_mileage")
async def back_to_mileage(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення пробігу"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_mileage)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 9 з 20:</b> Введіть пробіг авто

Введіть пробіг вантажного авто в км:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_mileage_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_fuel_type")
async def back_to_fuel_type(callback: CallbackQuery, state: FSMContext):
    """Повернення до вибору типу палива"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_fuel_type)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 10 з 20:</b> Оберіть тип палива

Оберіть тип палива вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_fuel_type_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_engine_volume")
async def back_to_engine_volume(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення об'єму двигуна"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_engine_volume)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 11 з 20:</b> Введіть об'єм двигуна

Введіть об'єм двигуна вантажного авто в літрах:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_engine_volume_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_power_hp")
async def back_to_power_hp(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення потужності двигуна"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_power_hp)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 12 з 20:</b> Введіть потужність двигуна

Введіть потужність двигуна в кВт:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_power_hp_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_transmission")
async def back_to_transmission(callback: CallbackQuery, state: FSMContext):
    """Повернення до вибору коробки передач"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_transmission)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 13 з 20:</b> Оберіть коробку передач

Оберіть тип коробки передач:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_transmission_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_wheel_radius")
async def back_to_wheel_radius(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення радіусу коліс"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_wheel_radius)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 14 з 20:</b> Введіть радіус коліс

Введіть радіус коліс вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wheel_radius_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_load_capacity")
async def back_to_load_capacity(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення вантажопідйомності"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_load_capacity)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 15 з 20:</b> Введіть вантажопідйомність

Введіть вантажопідйомність в кг:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_load_capacity_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


# ===== КНОПКИ "ПРОПУСТИТИ" ДЛЯ КРОКІВ 7-16 =====

@router.callback_query(F.data == "skip_condition")
async def skip_condition(callback: CallbackQuery, state: FSMContext):
    """Пропуск вибору стану авто"""
    await callback.answer("Стан авто пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_price)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 8 з 20:</b> Введіть вартість авто

Введіть вартість вантажного авто в USD:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_price_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_price")
async def skip_price(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення вартості"""
    await callback.answer("Вартість пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_mileage)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 9 з 20:</b> Введіть пробіг авто

Введіть пробіг вантажного авто в км:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_mileage_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_mileage")
async def skip_mileage(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення пробігу"""
    await callback.answer("Пробіг пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_fuel_type)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 10 з 20:</b> Оберіть тип палива

Оберіть тип палива вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_fuel_type_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_fuel_type")
async def skip_fuel_type(callback: CallbackQuery, state: FSMContext):
    """Пропуск вибору типу палива"""
    await callback.answer("Тип палива пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_engine_volume)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 11 з 20:</b> Введіть об'єм двигуна

Введіть об'єм двигуна вантажного авто в літрах:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_engine_volume_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_engine_volume")
async def skip_engine_volume(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення об'єму двигуна"""
    await callback.answer("Об'єм двигуна пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_power_hp)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 12 з 20:</b> Введіть потужність двигуна

Введіть потужність двигуна в кВт:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_power_hp_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_power_hp")
async def skip_power_hp(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення потужності двигуна"""
    await callback.answer("Потужність двигуна пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_transmission)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 13 з 20:</b> Оберіть коробку передач

Оберіть тип коробки передач:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_transmission_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_transmission")
async def skip_transmission(callback: CallbackQuery, state: FSMContext):
    """Пропуск вибору коробки передач"""
    await callback.answer("Коробка передач пропущена")
    await state.set_state(VehicleCreationStates.waiting_for_wheel_radius)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 14 з 20:</b> Введіть радіус коліс

Введіть радіус коліс вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wheel_radius_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_wheel_radius")
async def skip_wheel_radius(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення радіусу коліс"""
    await callback.answer("Радіус коліс пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_load_capacity)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 15 з 20:</b> Введіть вантажопідйомність

Введіть вантажопідйомність в кг:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_load_capacity_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_load_capacity")
async def skip_load_capacity(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення вантажопідйомності"""
    await callback.answer("Вантажопідйомність пропущена")
    await state.set_state(VehicleCreationStates.waiting_for_total_weight)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 16 з 20:</b> Введіть загальну масу авто

Введіть загальну масу вантажного авто в кг:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_total_weight_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_total_weight")
async def skip_total_weight(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення загальної маси авто"""
    await callback.answer("Загальна маса авто пропущена")
    await state.set_state(VehicleCreationStates.waiting_for_cargo_dimensions)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 17 з 20:</b> Введіть габарити вантажного відсіку

Введіть габарити вантажного відсіку (довжина x ширина x висота):
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cargo_dimensions_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


# ===== КНОПКИ "НАЗАД" ДЛЯ КРОКІВ 17-20 =====

@router.callback_query(F.data == "back_to_cargo_dimensions")
async def back_to_cargo_dimensions(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення габаритів вантажного відсіку"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_cargo_dimensions)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 17 з 20:</b> Введіть габарити вантажного відсіку

Введіть габарити вантажного відсіку (довжина x ширина x висота):
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_cargo_dimensions_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_location")
async def back_to_location(callback: CallbackQuery, state: FSMContext):
    """Повернення до вибору місцезнаходження"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_location)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 18 з 20:</b> Оберіть місцезнаходження авто

Оберіть місцезнаходження вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_location_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_total_weight")
async def back_to_total_weight(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення загальної ваги"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_total_weight)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 17 з 20:</b> Введіть загальну вагу авто

Введіть загальну вагу вантажного авто в кілограмах:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_total_weight_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "back_to_description")
async def back_to_description(callback: CallbackQuery, state: FSMContext):
    """Повернення до введення опису авто"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_description)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 19 з 20:</b> Введіть опис авто

Введіть детальний опис вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_description_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


# ===== КНОПКИ "ПРОПУСТИТИ" ДЛЯ КРОКІВ 17-19 =====

@router.callback_query(F.data == "skip_cargo_dimensions")
async def skip_cargo_dimensions(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення габаритів вантажного відсіку"""
    await callback.answer("Габарити вантажного відсіку пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_location)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 18 з 20:</b> Оберіть місцезнаходження авто

Оберіть місцезнаходження вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_location_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_location")
async def skip_location(callback: CallbackQuery, state: FSMContext):
    """Пропуск вибору місцезнаходження"""
    await callback.answer("Місцезнаходження пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_description)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 19 з 20:</b> Введіть опис авто

Введіть детальний опис вантажного авто:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_description_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "skip_description")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск введення опису авто"""
    await callback.answer("Опис авто пропущено")
    await state.set_state(VehicleCreationStates.waiting_for_photos)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 20 з 20:</b> Додайте фото авто

Завантажте фото вантажного авто (можна кілька фото):
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_photos_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )
