"""
Обробники для додаткових кроків створення авто (7-16)
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.utils.formatting import get_default_parse_mode
from app.modules.admin.core.access_control import AdminAccessFilter
from .states import VehicleCreationStates
from .keyboards import (
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
    get_photos_input_keyboard,
    get_photos_summary_keyboard,
    get_additional_photos_keyboard
)

logger = logging.getLogger(__name__)
router = Router()

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())


# ===== КРОК 7: СТАН АВТО =====

@router.callback_query(F.data.startswith("select_condition_"))
async def process_condition_selection(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору стану авто"""
    await callback.answer()
    condition = callback.data.replace("select_condition_", "")
    await state.update_data(condition=condition)
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


@router.message(VehicleCreationStates.waiting_for_price)
async def process_price_input(message: Message, state: FSMContext):
    """Обробка введення вартості авто"""
    try:
        price = float(message.text.strip().replace(',', '.'))
        
        if price <= 0:
            await message.answer(
                "❌ Вартість повинна бути більше 0",
                reply_markup=get_price_input_keyboard()
            )
            return
        
        await state.update_data(price=price)
        await state.set_state(VehicleCreationStates.waiting_for_mileage)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 9 з 20:</b> Введіть пробіг авто

Введіть пробіг вантажного авто в км:
"""
        
        await message.answer(
            text,
            reply_markup=get_mileage_input_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        
    except ValueError:
        await message.answer(
            "❌ Вартість повинна бути числом",
            reply_markup=get_price_input_keyboard()
        )


@router.message(VehicleCreationStates.waiting_for_mileage)
async def process_mileage_input(message: Message, state: FSMContext):
    """Обробка введення пробігу авто"""
    try:
        mileage = int(message.text.strip())
        
        if mileage < 0:
            await message.answer(
                "❌ Пробіг не може бути від'ємним",
                reply_markup=get_mileage_input_keyboard()
            )
            return
        
        await state.update_data(mileage=mileage)
        await state.set_state(VehicleCreationStates.waiting_for_fuel_type)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 10 з 20:</b> Оберіть тип палива

Оберіть тип палива вантажного авто:
"""
        
        await message.answer(
            text,
            reply_markup=get_fuel_type_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        
    except ValueError:
        await message.answer(
            "❌ Пробіг повинен бути числом",
            reply_markup=get_mileage_input_keyboard()
        )


@router.callback_query(F.data.startswith("select_fuel_"))
async def process_fuel_type_selection(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору типу палива"""
    await callback.answer()
    fuel_type = callback.data.replace("select_fuel_", "")
    await state.update_data(fuel_type=fuel_type)
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


@router.message(VehicleCreationStates.waiting_for_engine_volume)
async def process_engine_volume_input(message: Message, state: FSMContext):
    """Обробка введення об'єму двигуна"""
    try:
        engine_volume = float(message.text.strip().replace(',', '.'))
        
        if engine_volume <= 0:
            await message.answer(
                "❌ Об'єм двигуна повинен бути більше 0",
                reply_markup=get_engine_volume_input_keyboard()
            )
            return
        
        await state.update_data(engine_volume=engine_volume)
        await state.set_state(VehicleCreationStates.waiting_for_power_hp)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 12 з 20:</b> Введіть потужність двигуна

Введіть потужність двигуна в кВт:
"""
        
        await message.answer(
            text,
            reply_markup=get_power_hp_input_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        
    except ValueError:
        await message.answer(
            "❌ Об'єм двигуна повинен бути числом",
            reply_markup=get_engine_volume_input_keyboard()
        )


@router.message(VehicleCreationStates.waiting_for_power_hp)
async def process_power_hp_input(message: Message, state: FSMContext):
    """Обробка введення потужності двигуна"""
    try:
        power_hp = int(message.text.strip())
        
        if power_hp <= 0:
            await message.answer(
                "❌ Потужність повинна бути більше 0",
                reply_markup=get_power_hp_input_keyboard()
            )
            return
        
        await state.update_data(power_hp=power_hp)
        await state.set_state(VehicleCreationStates.waiting_for_transmission)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 13 з 20:</b> Оберіть коробку передач

Оберіть тип коробки передач:
"""
        
        await message.answer(
            text,
            reply_markup=get_transmission_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        
    except ValueError:
        await message.answer(
            "❌ Потужність повинна бути числом",
            reply_markup=get_power_hp_input_keyboard()
        )


@router.callback_query(F.data.startswith("select_transmission_"))
async def process_transmission_selection(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору коробки передач"""
    await callback.answer()
    transmission = callback.data.replace("select_transmission_", "")
    await state.update_data(transmission=transmission)
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


@router.message(VehicleCreationStates.waiting_for_wheel_radius)
async def process_wheel_radius_input(message: Message, state: FSMContext):
    """Обробка введення радіусу коліс"""
    try:
        wheel_radius = message.text.strip()
        
        if not wheel_radius:
            await message.answer(
                "❌ Радіус коліс не може бути порожнім",
                reply_markup=get_wheel_radius_input_keyboard()
            )
            return
        
        await state.update_data(wheel_radius=wheel_radius)
        await state.set_state(VehicleCreationStates.waiting_for_load_capacity)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 15 з 20:</b> Введіть вантажопідйомність

Введіть вантажопідйомність в кг:
"""
        
        await message.answer(
            text,
            reply_markup=get_load_capacity_input_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        
    except Exception:
        await message.answer(
            "❌ Помилка введення радіусу коліс",
            reply_markup=get_wheel_radius_input_keyboard()
        )


@router.message(VehicleCreationStates.waiting_for_load_capacity)
async def process_load_capacity_input(message: Message, state: FSMContext):
    """Обробка введення вантажопідйомності"""
    try:
        load_capacity = int(message.text.strip())
        
        if load_capacity <= 0:
            await message.answer(
                "❌ Вантажопідйомність повинна бути більше 0",
                reply_markup=get_load_capacity_input_keyboard()
            )
            return
        
        await state.update_data(load_capacity=load_capacity)
        await state.set_state(VehicleCreationStates.waiting_for_total_weight)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 16 з 20:</b> Введіть загальну масу авто

Введіть загальну масу вантажного авто в кг:
"""
        
        await message.answer(
            text,
            reply_markup=get_total_weight_input_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        
    except ValueError:
        await message.answer(
            "❌ Вантажопідйомність повинна бути числом",
            reply_markup=get_load_capacity_input_keyboard()
        )


@router.message(VehicleCreationStates.waiting_for_total_weight)
async def process_total_weight_input(message: Message, state: FSMContext):
    """Обробка введення загальної маси авто"""
    try:
        total_weight = int(message.text.strip())
        
        if total_weight <= 0:
            await message.answer(
                "❌ Загальна маса повинна бути більше 0",
                reply_markup=get_total_weight_input_keyboard()
            )
            return
        
        await state.update_data(total_weight=total_weight)
        await state.set_state(VehicleCreationStates.waiting_for_cargo_dimensions)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 17 з 20:</b> Введіть габарити вантажного відсіку

Введіть габарити вантажного відсіку (довжина x ширина x висота):
"""
        
        await message.answer(
            text,
            reply_markup=get_cargo_dimensions_input_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        
    except ValueError:
        await message.answer(
            "❌ Загальна маса повинна бути числом",
            reply_markup=get_total_weight_input_keyboard()
        )


# ===== КРОК 17: ГАБАРИТИ ВАНТАЖНОГО ВІДСІКУ =====

@router.message(VehicleCreationStates.waiting_for_cargo_dimensions)
async def process_cargo_dimensions_input(message: Message, state: FSMContext):
    """Обробка введення габаритів вантажного відсіку"""
    try:
        cargo_dimensions = message.text.strip()
        
        if not cargo_dimensions:
            await message.answer(
                "❌ Габарити не можуть бути порожніми",
                reply_markup=get_cargo_dimensions_input_keyboard()
            )
            return
        
        await state.update_data(cargo_dimensions=cargo_dimensions)
        await state.set_state(VehicleCreationStates.waiting_for_location)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 18 з 20:</b> Оберіть місцезнаходження авто

Оберіть місцезнаходження вантажного авто:
"""
        
        await message.answer(
            text,
            reply_markup=get_location_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        
    except Exception:
        await message.answer(
            "❌ Помилка введення габаритів",
            reply_markup=get_cargo_dimensions_input_keyboard()
        )


# ===== КРОК 18: МІСЦЕЗНАХОДЖЕННЯ АВТО =====

@router.callback_query(F.data.startswith("select_location_"))
async def process_location_selection(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору місцезнаходження"""
    await callback.answer()
    location = callback.data.replace("select_location_", "")
    await state.update_data(location=location)
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


# ===== КРОК 19: ОПИС АВТО =====

@router.message(VehicleCreationStates.waiting_for_description)
async def process_description_input(message: Message, state: FSMContext):
    """Обробка введення опису авто"""
    try:
        description = message.text.strip()
        
        if not description:
            await message.answer(
                "❌ Опис не може бути порожнім",
                reply_markup=get_description_input_keyboard()
            )
            return
        
        await state.update_data(description=description)
        await state.set_state(VehicleCreationStates.waiting_for_main_photo)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 20 з 21:</b> Головне медіа авто

📸/🎥 Завантажте <b>ОДНЕ</b> головне фото або відео, яке буде відображатися на картці авто в боті.

<i>Це медіа побачать клієнти при перегляді каталогу.</i>
"""
        
        # Створюємо повідомлення та зберігаємо його ID
        new_message = await message.answer(
            text,
            reply_markup=get_photos_input_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        await state.update_data(last_main_photo_message_id=new_message.message_id)
        
    except Exception:
        await message.answer(
            "❌ Помилка введення опису",
            reply_markup=get_description_input_keyboard()
        )


# ===== КРОК 20: ГОЛОВНЕ ФОТО АВТО =====

@router.message(VehicleCreationStates.waiting_for_main_photo, F.photo)
async def process_main_photo_input(message: Message, state: FSMContext):
    """Обробка завантаження головного медіа авто (фото або відео)"""
    try:
        # Перевіряємо чи це не медіагрупа
        if hasattr(message, 'media_group_id') and message.media_group_id:
            await message.answer(
                "❌ Будь ласка, завантажте <b>ОДНЕ</b> медіа, а не кілька одночасно.\n\n"
                "Головне медіа має бути одне - найкраще зображення або відео для картки авто.",
                parse_mode=get_default_parse_mode()
            )
            return
        
        logger.info(f"📷 process_main_photo_input: обробляємо головне медіа")
        
        # Отримуємо file_id фото (найбільший розмір)
        photo = message.photo[-1]
        file_id = photo.file_id
        
        # Зберігаємо головне медіа окремо (фото без префіксу)
        await state.update_data(main_photo=file_id)
        
        # Переходимо до завантаження фото для групи
        await state.set_state(VehicleCreationStates.waiting_for_group_photos)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 21 з 21:</b> Медіа для публікації в групу

✅ Головне медіа завантажено!

📸/🎥 Тепер завантажте всі фото/відео авто для публікації в Telegram групу (можна медіагрупу).

<i>Ці медіа будуть показані в каналі продажів. Рекомендуємо завантажити 3-10 якісних матеріалів з різних ракурсів.</i>
"""
        
        new_message = await message.answer(
            text,
            reply_markup=get_photos_input_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        await state.update_data(last_group_photos_message_id=new_message.message_id)
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження головного медіа: {e}")
        await message.answer(
            "❌ Помилка завантаження медіа. Спробуйте ще раз.",
            reply_markup=get_photos_input_keyboard()
        )


# Підтримка відео як головного медіа
@router.message(VehicleCreationStates.waiting_for_main_photo, F.video)
async def process_main_video_input(message: Message, state: FSMContext):
    """Обробка завантаження головного відео авто"""
    try:
        # Забороняємо медіагрупу для головного медіа
        if hasattr(message, 'media_group_id') and message.media_group_id:
            await message.answer(
                "❌ Будь ласка, завантажте <b>ОДНЕ</b> відео, а не кілька одночасно.",
                parse_mode=get_default_parse_mode()
            )
            return
        
        logger.info(f"📹 process_main_video_input: обробляємо головне відео")
        file_id = message.video.file_id
        
        # Зберігаємо з префіксом для визначення типу без змін БД
        await state.update_data(main_photo=f"video:{file_id}")
        
        # Переходимо до завантаження медіа для групи
        await state.set_state(VehicleCreationStates.waiting_for_group_photos)
        
        text = """
🚛 <b>Створення картки авто</b>

<b>Крок 21 з 21:</b> Медіа для публікації в групу

✅ Головне відео завантажено!

📸/🎥 Тепер завантажте всі фото/відео авто для публікації в Telegram групу (можна медіагрупу).

<i>Ці медіа будуть показані в каналі продажів. Рекомендуємо завантажити 3-10 якісних матеріалів з різних ракурсів.</i>
"""
        new_message = await message.answer(
            text,
            reply_markup=get_photos_input_keyboard(),
            parse_mode=get_default_parse_mode()
        )
        await state.update_data(last_group_photos_message_id=new_message.message_id)
    except Exception as e:
        logger.error(f"❌ Помилка завантаження головного відео: {e}")
        await message.answer(
            "❌ Помилка завантаження медіа. Спробуйте ще раз.",
            reply_markup=get_photos_input_keyboard()
        )


# ===== КРОК 21: МЕДІА ДЛЯ ГРУПИ =====

@router.message(VehicleCreationStates.waiting_for_group_photos, F.photo | F.video)
async def process_group_photos_input(message: Message, state: FSMContext):
    """Обробка завантаження медіа для групи (включаючи медіагрупи)"""
    try:
        # Імпортуємо обробник медіагруп
        from .photo_group_processor import process_media_group_photos
        
        # Спочатку намагаємося обробити як медіагрупу
        if await process_media_group_photos(message, state):
            logger.info(f"📷 process_group_photos_input: медіа оброблено як медіагрупа")
            return
        
        # Якщо не медіагрупа, обробляємо як одиночне фото/відео
        logger.info(f"📷 process_group_photos_input: обробляємо як одиночне медіа")
        
        # Отримуємо file_id медіа
        if message.photo:
            file_id = message.photo[-1].file_id  # Найбільший розмір
        elif message.video:
            file_id = f"video:{message.video.file_id}"
        else:
            await message.answer("❌ Підтримуються тільки фото та відео")
            return
        
        # Отримуємо поточні фото зі стану
        data = await state.get_data()
        group_photos = data.get('group_photos', [])
        
        # Додаємо нове фото
        group_photos.append(file_id)
        await state.update_data(group_photos=group_photos)
        
        # Показуємо кількість завантажених медіа
        count = len(group_photos)
        text = f"""
🚛 <b>Створення картки авто</b>

<b>Крок 21 з 21:</b> Медіа для публікації в групу

✅ Завантажено медіа: {count}
📸/🎥 Можете додати ще фото/відео або завершити створення картки

Завантажте ще медіа або натисніть "Завершити":
"""
        
        # Після першого завантаження фото переходимо до стану підсумку
        await state.set_state(VehicleCreationStates.waiting_for_additional_group_photos)
        
        # Використовуємо клавіатуру з кнопкою "Додати ще"
        keyboard = get_photos_summary_keyboard()
        
        # Відправляємо повідомлення з ГОЛОВНИМ фото і текстом як підписом
        main_photo = (await state.get_data()).get('main_photo')
        try:
            if main_photo:
                # Визначаємо тип: фото чи відео (префікс video:)
                is_video = isinstance(main_photo, str) and main_photo.startswith("video:")
                file_id = main_photo.split(":", 1)[1] if is_video else main_photo
                
                if is_video:
                    try:
                        new_message = await message.answer_video(
                            video=file_id,
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode=get_default_parse_mode()
                        )
                    except Exception as video_error:
                        logger.warning(f"⚠️ Не вдалося відправити відео: {video_error}")
                        # Якщо відео недійсне, відправляємо тільки текст
                        new_message = await message.answer(
                            text,
                            reply_markup=keyboard,
                            parse_mode=get_default_parse_mode()
                        )
                else:
                    try:
                        new_message = await message.answer_photo(
                            photo=file_id,
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode=get_default_parse_mode()
                        )
                    except Exception as photo_error:
                        logger.warning(f"⚠️ Не вдалося відправити фото: {photo_error}")
                        # Якщо фото недійсне, відправляємо тільки текст
                        new_message = await message.answer(
                            text,
                            reply_markup=keyboard,
                            parse_mode=get_default_parse_mode()
                        )
            else:
                try:
                    new_message = await message.answer_photo(
                        photo=file_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode=get_default_parse_mode()
                    )
                except Exception as photo_error:
                    logger.warning(f"⚠️ Не вдалося відправити фото: {photo_error}")
                    # Якщо фото недійсне, відправляємо тільки текст
                    new_message = await message.answer(
                        text,
                        reply_markup=keyboard,
                        parse_mode=get_default_parse_mode()
                    )
        except Exception:
            new_message = await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode()
            )
        await state.update_data(last_group_photos_message_id=new_message.message_id)
        logger.info(f"📷 process_group_photos_input: створено нове повідомлення з медіа {new_message.message_id}")
        
    except Exception as e:
        logger.error(f"❌ process_photos_input: помилка обробки медіа: {e}", exc_info=True)
        await message.answer(
            "❌ Помилка завантаження медіа",
            reply_markup=get_photos_input_keyboard()
        )


# ===== ОБРОБНИК ДОДАТКОВИХ МЕДІА ДЛЯ ГРУПИ =====

@router.message(VehicleCreationStates.waiting_for_additional_group_photos, F.photo | F.video)
async def process_additional_group_photos_input(message: Message, state: FSMContext):
    """Обробка завантаження додаткових медіа для групи (включаючи медіагрупи)"""
    try:
        # Імпортуємо обробник медіагруп
        from .photo_group_processor import process_media_group_photos
        
        # Спочатку намагаємося обробити як медіагрупу
        if await process_media_group_photos(message, state):
            logger.info(f"📷 process_additional_group_photos_input: медіа оброблено як медіагрупа")
            return
        
        # Якщо не медіагрупа, обробляємо як одиночне фото/відео
        logger.info(f"📷 process_additional_group_photos_input: обробляємо як одиночне медіа")
        
        # Отримуємо file_id медіа
        if message.photo:
            file_id = message.photo[-1].file_id  # Найбільший розмір
        elif message.video:
            file_id = f"video:{message.video.file_id}"
        else:
            await message.answer("❌ Підтримуються тільки фото та відео")
            return
        
        # Отримуємо поточні фото зі стану
        data = await state.get_data()
        group_photos = data.get('group_photos', [])
        
        # Додаємо нове фото
        group_photos.append(file_id)
        await state.update_data(group_photos=group_photos)
        
        # Показуємо оновлену інформацію
        count = len(group_photos)
        text = f"""
🚛 <b>Створення картки авто</b>

<b>Крок 21 з 21:</b> Медіа для публікації в групу

✅ Завантажено медіа: {count}
📸/🎥 Можете додати ще фото/відео або завершити створення картки

Завантажте ще медіа або натисніть "Завершити":
"""
        
        # Використовуємо клавіатуру з кнопкою "Додати ще"
        keyboard = get_photos_summary_keyboard()
        
        # Відправляємо повідомлення з ГОЛОВНИМ фото і текстом як підписом
        main_photo = (await state.get_data()).get('main_photo')
        try:
            if main_photo:
                # Визначаємо тип: фото чи відео (префікс video:)
                is_video = isinstance(main_photo, str) and main_photo.startswith("video:")
                file_id = main_photo.split(":", 1)[1] if is_video else main_photo
                
                if is_video:
                    try:
                        new_message = await message.answer_video(
                            video=file_id,
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode=get_default_parse_mode()
                        )
                    except Exception as video_error:
                        logger.warning(f"⚠️ Не вдалося відправити відео: {video_error}")
                        # Якщо відео недійсне, відправляємо тільки текст
                        new_message = await message.answer(
                            text,
                            reply_markup=keyboard,
                            parse_mode=get_default_parse_mode()
                        )
                else:
                    try:
                        new_message = await message.answer_photo(
                            photo=file_id,
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode=get_default_parse_mode()
                        )
                    except Exception as photo_error:
                        logger.warning(f"⚠️ Не вдалося відправити фото: {photo_error}")
                        # Якщо фото недійсне, відправляємо тільки текст
                        new_message = await message.answer(
                            text,
                            reply_markup=keyboard,
                            parse_mode=get_default_parse_mode()
                        )
            else:
                try:
                    new_message = await message.answer_photo(
                        photo=file_id,
                        caption=text,
                        reply_markup=keyboard,
                        parse_mode=get_default_parse_mode()
                    )
                except Exception as photo_error:
                    logger.warning(f"⚠️ Не вдалося відправити фото: {photo_error}")
                    # Якщо фото недійсне, відправляємо тільки текст
                    new_message = await message.answer(
                        text,
                        reply_markup=keyboard,
                        parse_mode=get_default_parse_mode()
                    )
        except Exception:
            new_message = await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode()
            )
        await state.update_data(last_additional_group_photos_message_id=new_message.message_id)
        logger.info(f"📷 process_additional_group_photos_input: створено нове повідомлення з медіа {new_message.message_id}")
        
    except Exception as e:
        logger.error(f"❌ process_additional_photos_input: помилка обробки медіа: {e}", exc_info=True)
        await message.answer(
            "❌ Помилка завантаження медіа",
            reply_markup=get_additional_photos_keyboard()
        )


# ===== ОБРОБНИКИ ДЛЯ ДОДАТКОВИХ ФОТО =====

@router.callback_query(F.data == "add_more_photos")
async def add_more_photos(callback: CallbackQuery, state: FSMContext):
    """Обробка кнопки 'Додати ще' фото"""
    await callback.answer()
    await state.set_state(VehicleCreationStates.waiting_for_additional_group_photos)
    
    text = """
🚛 <b>Створення картки авто</b>

<b>Додаткові фото:</b> Завантажте ще фото для групи

Завантажте додаткові фото вантажного авто (можна кілька фото):
"""
    
    # Створюємо повідомлення та зберігаємо його ID
    new_message = await callback.message.answer(
        text,
        reply_markup=get_additional_photos_keyboard(),
        parse_mode=get_default_parse_mode()
    )
    await state.update_data(last_additional_group_photos_message_id=new_message.message_id)


@router.callback_query(F.data == "back_to_photos_summary")
async def back_to_photos_summary(callback: CallbackQuery, state: FSMContext):
    """Повернення до підсумку фото"""
    await callback.answer()
    
    # Отримуємо дані
    data = await state.get_data()
    group_photos = data.get('group_photos', [])
    
    # Показуємо підсумок фото
    count = len(group_photos)
    text = f"""
🚛 <b>Створення картки авто</b>

<b>Крок 21 з 21:</b> Фото для публікації в групу

✅ Завантажено фото: {count}
📸 Можете додати ще фото або завершити створення картки

Завантажте ще фото або натисніть "Завершити":
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_photos_summary_keyboard(),
        parse_mode=get_default_parse_mode()
    )
    await state.set_state(VehicleCreationStates.waiting_for_additional_group_photos)


# Обробник finish_vehicle_creation перенесено в summary_card.py

