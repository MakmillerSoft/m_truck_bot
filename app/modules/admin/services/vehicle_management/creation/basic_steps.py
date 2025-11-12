"""
Обробники для основних кроків створення авто (1-6)
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
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
    get_condition_keyboard
)

logger = logging.getLogger(__name__)
router = Router()

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())


@router.callback_query(F.data == "add_vehicle")
async def start_vehicle_creation(callback: CallbackQuery, state: FSMContext):
    """Початок створення авто - вибір типу авто"""
    await callback.answer()
    await state.clear()
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


@router.callback_query(F.data.startswith("select_vehicle_type_"))
async def process_vehicle_type_selection(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору типу авто"""
    await callback.answer()
    vehicle_type_name = callback.data.replace("select_vehicle_type_", "")

    # 4 категорії для відображення в картці
    vehicle_type_mapping = {
        "tractors_and_semi": "Сідельні тягачі та напівпричепи",
        "vans_and_refrigerators": "Вантажні фургони та рефрижератори",
        "variable_body": "Змінні кузови",
        "container_carriers": "Контейнеровози (з причепами)",
    }

    vehicle_type_ukrainian = vehicle_type_mapping.get(vehicle_type_name, vehicle_type_name)
    await state.update_data(vehicle_type=vehicle_type_ukrainian)
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


@router.message(VehicleCreationStates.waiting_for_brand)
async def process_brand_input(message: Message, state: FSMContext):
    """Обробка введення марки авто"""
    brand = message.text.strip()
    
    if len(brand) < 2:
        await message.answer(
            "❌ Марка повинна містити мінімум 2 символи",
            reply_markup=get_brand_input_keyboard()
        )
        return
    
    await state.update_data(brand=brand)
    await state.set_state(VehicleCreationStates.waiting_for_model)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 3 з 20:</b> Введіть модель авто

Введіть модель вантажного авто:
"""
    
    await message.answer(
        text,
        reply_markup=get_model_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.message(VehicleCreationStates.waiting_for_model)
async def process_model_input(message: Message, state: FSMContext):
    """Обробка введення моделі авто"""
    model = message.text.strip()
    
    if len(model) < 2:
        await message.answer(
            "❌ Модель повинна містити мінімум 2 символи",
            reply_markup=get_model_input_keyboard()
        )
        return
    
    await state.update_data(model=model)
    await state.set_state(VehicleCreationStates.waiting_for_vin_code)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 4 з 20:</b> Введіть VIN код авто

Введіть VIN код вантажного авто (опціонально):
"""
    
    await message.answer(
        text,
        reply_markup=get_vin_code_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.message(VehicleCreationStates.waiting_for_vin_code)
async def process_vin_code_input(message: Message, state: FSMContext):
    """Обробка введення VIN коду"""
    vin_code = message.text.strip()
    
    if len(vin_code) < 17:
        await message.answer(
            "❌ VIN код повинен містити мінімум 17 символів",
            reply_markup=get_vin_code_input_keyboard()
        )
        return
    
    await state.update_data(vin_code=vin_code)
    await state.set_state(VehicleCreationStates.waiting_for_body_type)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 5 з 20:</b> Введіть тип кузова авто

Введіть тип кузова вантажного авто:
"""
    
    await message.answer(
        text,
        reply_markup=get_body_type_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.message(VehicleCreationStates.waiting_for_body_type)
async def process_body_type_input(message: Message, state: FSMContext):
    """Обробка введення типу кузова"""
    body_type = message.text.strip()
    
    if len(body_type) < 2:
        await message.answer(
            "❌ Тип кузова повинен містити мінімум 2 символи",
            reply_markup=get_body_type_input_keyboard()
        )
        return
    
    await state.update_data(body_type=body_type)
    await state.set_state(VehicleCreationStates.waiting_for_year)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Крок 6 з 20:</b> Введіть рік випуску авто

Введіть рік випуску вантажного авто:
"""
    
    await message.answer(
        text,
        reply_markup=get_year_input_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.message(VehicleCreationStates.waiting_for_year)
async def process_year_input(message: Message, state: FSMContext):
    """Обробка введення року випуску"""
    current_year = datetime.now().year
    
    try:
        year = int(message.text.strip())
        
        if year < 1900 or year > current_year + 1:
            await message.answer(
                f"❌ Рік повинен бути в діапазоні від 1900 до {current_year + 1}",
                reply_markup=get_year_input_keyboard()
            )
            return
        
        await state.update_data(year=year)
        await state.set_state(VehicleCreationStates.waiting_for_condition)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 7 з 20:</b> Оберіть стан авто

Оберіть стан вантажного авто:
"""
        
        await message.answer(
            text,
            reply_markup=get_condition_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        
    except ValueError:
        await message.answer(
            "❌ Рік повинен бути числом",
            reply_markup=get_year_input_keyboard()
        )
