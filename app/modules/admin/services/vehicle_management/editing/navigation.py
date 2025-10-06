"""
Навігація між полями редагування
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.utils.formatting import get_default_parse_mode
from app.modules.admin.core.access_control import AdminAccessFilter
from .states import VehicleEditingStates
from .keyboards import get_editing_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())


async def process_field_edit(callback: CallbackQuery, state: FSMContext, field_name: str, new_value: str):
    """Обробити редагування поля та повернутися до меню"""
    # Отримуємо поточні дані
    data = await state.get_data()
    old_value = data.get(field_name, "Не вказано")
    
    # Логування для діагностики
    logger.info(f"🔧 process_field_edit: {field_name}: {old_value} → {new_value}")
    
    # Оновлюємо дані
    await state.update_data(**{field_name: new_value})
    
    # Оновлюємо зміни
    changes = data.get('editing_changes', {})
    changes[field_name] = (old_value, new_value)
    await state.update_data(editing_changes=changes)
    
    # Логування після оновлення
    updated_data = await state.get_data()
    logger.info(f"🔧 process_field_edit: оновлені дані: {updated_data}")
    
    # Отримуємо оновлені дані
    updated_data = await state.get_data()
    
    # Форматуємо текст меню редагування з оновленнями
    menu_text = "🔧 <b>Редагування картки авто</b>\n\n"
    
    if changes:
        changes_list = []
        for field, (old_val, new_val) in changes.items():
            field_names = {
                "vehicle_type": "Тип авто",
                "brand": "Марка",
                "model": "Модель",
                "vin_code": "VIN код",
                "body_type": "Тип кузова",
                "year": "Рік випуску",
                "condition": "Стан",
                "price": "Вартість",
                "mileage": "Пробіг",
                "fuel_type": "Тип палива",
                "engine_volume": "Об'єм двигуна",
                "power_hp": "Потужність",
                "transmission": "Коробка передач",
                "wheel_radius": "Радіус коліс",
                "load_capacity": "Вантажопідйомність",
                "total_weight": "Загальна маса",
                "cargo_dimensions": "Габарити вантажного відсіку",
                "location": "Місцезнаходження",
                "description": "Опис",
                "photos": "Фото"
            }
            field_display_name = field_names.get(field, field)
            changes_list.append(f"✅ <b>{field_display_name}:</b> {old_val} → {new_val}")
        
        menu_text += "\n".join(changes_list) + "\n\n"
    
    menu_text += "<b>Оберіть поле для редагування:</b>"
    
    # Відправляємо нове повідомлення з оновленим меню
    await callback.message.answer(
        menu_text,
        reply_markup=get_editing_menu_keyboard(updated_data, changes),
        parse_mode=get_default_parse_mode()
    )
    
    # Переходимо до стану меню редагування
    await state.set_state(VehicleEditingStates.editing_menu)
    
    logger.info(f"✅ Поле {field_name} оновлено: {old_value} → {new_value} для користувача {callback.from_user.id}")


# Обробники для кожного поля редагування
@router.message(VehicleEditingStates.waiting_for_vehicle_type_edit)
async def process_vehicle_type_edit(message: Message, state: FSMContext):
    """Обробити редагування типу авто"""
    new_value = message.text.strip()
    
    # Валідація типу авто
    valid_types = [
        "Контейнеровози", "Напівпричепи контейнеровози", "Змінні кузови",
        "Сідельні тягачі", "Причіпи", "Рефрижератори", "Фургони", "Буси"
    ]
    
    if new_value not in valid_types:
        await message.answer(
            "❌ Невірний тип авто. Оберіть з доступних варіантів:",
            reply_markup=get_editing_menu_keyboard(await state.get_data())
        )
        return
    
    # Створюємо фейковий callback для обробки
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "vehicle_type", new_value)


@router.message(VehicleEditingStates.waiting_for_brand_edit)
async def process_brand_edit(message: Message, state: FSMContext):
    """Обробити редагування марки авто"""
    new_value = message.text.strip()
    
    if not new_value or len(new_value) < 2:
        await message.answer("❌ Марка не може бути порожньою або менше 2 символів")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "brand", new_value)


@router.message(VehicleEditingStates.waiting_for_model_edit)
async def process_model_edit(message: Message, state: FSMContext):
    """Обробити редагування моделі авто"""
    new_value = message.text.strip()
    
    if not new_value or len(new_value) < 2:
        await message.answer("❌ Модель не може бути порожньою або менше 2 символів")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "model", new_value)


@router.message(VehicleEditingStates.waiting_for_vin_code_edit)
async def process_vin_code_edit(message: Message, state: FSMContext):
    """Обробити редагування VIN коду"""
    new_value = message.text.strip().upper()
    
    if new_value and len(new_value) != 17:
        await message.answer("❌ VIN код повинен містити 17 символів")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "vin_code", new_value)


@router.message(VehicleEditingStates.waiting_for_body_type_edit)
async def process_body_type_edit(message: Message, state: FSMContext):
    """Обробити редагування типу кузова"""
    new_value = message.text.strip()
    
    if not new_value:
        await message.answer("❌ Тип кузова не може бути порожнім")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "body_type", new_value)


@router.message(VehicleEditingStates.waiting_for_year_edit)
async def process_year_edit(message: Message, state: FSMContext):
    """Обробити редагування року випуску"""
    try:
        new_value = int(message.text.strip())
        current_year = 2025
        
        if new_value < 1900 or new_value > current_year:
            await message.answer(f"❌ Рік повинен бути між 1900 та {current_year}")
            return
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "year", str(new_value))
        
    except ValueError:
        await message.answer("❌ Введіть коректний рік (число)")


@router.message(VehicleEditingStates.waiting_for_condition_edit)
async def process_condition_edit(message: Message, state: FSMContext):
    """Обробити редагування стану авто"""
    new_value = message.text.strip()
    
    valid_conditions = ["Новий", "Вживане"]
    if new_value not in valid_conditions:
        await message.answer("❌ Оберіть з доступних варіантів: Новий, Вживане")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "condition", new_value)


@router.message(VehicleEditingStates.waiting_for_price_edit)
async def process_price_edit(message: Message, state: FSMContext):
    """Обробити редагування вартості"""
    try:
        new_value = float(message.text.strip())
        
        if new_value < 0:
            await message.answer("❌ Вартість не може бути від'ємною")
            return
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "price", str(new_value))
        
    except ValueError:
        await message.answer("❌ Введіть коректну вартість (число)")


@router.message(VehicleEditingStates.waiting_for_mileage_edit)
async def process_mileage_edit(message: Message, state: FSMContext):
    """Обробити редагування пробігу"""
    try:
        new_value = int(message.text.strip())
        
        if new_value < 0:
            await message.answer("❌ Пробіг не може бути від'ємним")
            return
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "mileage", str(new_value))
        
    except ValueError:
        await message.answer("❌ Введіть коректний пробіг (число)")


@router.message(VehicleEditingStates.waiting_for_fuel_type_edit)
async def process_fuel_type_edit(message: Message, state: FSMContext):
    """Обробити редагування типу палива"""
    new_value = message.text.strip()
    
    valid_fuels = ["Дизель", "Бензин", "Газ", "Газ/Бензин", "Електричний"]
    if new_value not in valid_fuels:
        await message.answer("❌ Оберіть з доступних варіантів: Дизель, Бензин, Газ, Газ/Бензин, Електричний")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "fuel_type", new_value)


@router.message(VehicleEditingStates.waiting_for_engine_volume_edit)
async def process_engine_volume_edit(message: Message, state: FSMContext):
    """Обробити редагування об'єму двигуна"""
    try:
        new_value = float(message.text.strip())
        
        if new_value < 0:
            await message.answer("❌ Об'єм двигуна не може бути від'ємним")
            return
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "engine_volume", str(new_value))
        
    except ValueError:
        await message.answer("❌ Введіть коректний об'єм двигуна (число)")


@router.message(VehicleEditingStates.waiting_for_power_hp_edit)
async def process_power_hp_edit(message: Message, state: FSMContext):
    """Обробити редагування потужності"""
    try:
        new_value = int(message.text.strip())
        
        if new_value < 0:
            await message.answer("❌ Потужність не може бути від'ємною")
            return
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "power_hp", str(new_value))
        
    except ValueError:
        await message.answer("❌ Введіть коректну потужність (число)")


@router.message(VehicleEditingStates.waiting_for_transmission_edit)
async def process_transmission_edit(message: Message, state: FSMContext):
    """Обробити редагування коробки передач"""
    new_value = message.text.strip()
    
    valid_transmissions = ["Автоматична", "Механічна", "Робот", "CVT"]
    if new_value not in valid_transmissions:
        await message.answer("❌ Оберіть з доступних варіантів: Автоматична, Механічна, Робот, CVT")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "transmission", new_value)


@router.message(VehicleEditingStates.waiting_for_wheel_radius_edit)
async def process_wheel_radius_edit(message: Message, state: FSMContext):
    """Обробити редагування радіуса коліс"""
    new_value = message.text.strip()
    
    if not new_value:
        await message.answer("❌ Радіус коліс не може бути порожнім")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "wheel_radius", new_value)


@router.message(VehicleEditingStates.waiting_for_load_capacity_edit)
async def process_load_capacity_edit(message: Message, state: FSMContext):
    """Обробити редагування вантажопідйомності"""
    try:
        new_value = int(message.text.strip())
        
        if new_value < 0:
            await message.answer("❌ Вантажопідйомність не може бути від'ємною")
            return
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "load_capacity", str(new_value))
        
    except ValueError:
        await message.answer("❌ Введіть коректну вантажопідйомність (число)")


@router.message(VehicleEditingStates.waiting_for_total_weight_edit)
async def process_total_weight_edit(message: Message, state: FSMContext):
    """Обробити редагування загальної маси"""
    try:
        new_value = int(message.text.strip())
        
        if new_value < 0:
            await message.answer("❌ Загальна маса не може бути від'ємною")
            return
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "total_weight", str(new_value))
        
    except ValueError:
        await message.answer("❌ Введіть коректну загальну масу (число)")


@router.message(VehicleEditingStates.waiting_for_cargo_dimensions_edit)
async def process_cargo_dimensions_edit(message: Message, state: FSMContext):
    """Обробити редагування габаритів"""
    new_value = message.text.strip()
    
    if not new_value:
        await message.answer("❌ Габарити не можуть бути порожніми")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "cargo_dimensions", new_value)


@router.message(VehicleEditingStates.waiting_for_location_edit)
async def process_location_edit(message: Message, state: FSMContext):
    """Обробити редагування місцезнаходження"""
    new_value = message.text.strip()
    
    if not new_value:
        await message.answer("❌ Місцезнаходження не може бути порожнім")
        return
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "location", new_value)


@router.message(VehicleEditingStates.waiting_for_description_edit)
async def process_description_edit(message: Message, state: FSMContext):
    """Обробити редагування опису"""
    new_value = message.text.strip()
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(message)
    await process_field_edit(fake_callback, state, "description", new_value)


@router.message(VehicleEditingStates.waiting_for_photos_edit)
async def process_photos_edit(message: Message, state: FSMContext):
    """Обробити редагування фото"""
    if message.text and (message.text.lower().strip() == "пропустити" or message.text.strip() == "⏭️ Пропустити"):
        # Користувач хоче залишити поточні фото - не змінюємо їх
        data = await state.get_data()
        current_photos = data.get('photos', [])
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        # Залишаємо поточні фото без змін
        await process_field_edit(fake_callback, state, "photos", current_photos)
        return
    
    if message.photo:
        # Перевіряємо, чи це медіа-група (як в створенні авто)
        from ..creation.photo_group_processor import process_media_group_photos
        
        if await process_media_group_photos(message, state):
            # Фото оброблено як медіа-група
            return
        
        # Якщо не медіа-група, обробляємо як одиночне фото
        new_photos = [photo.file_id for photo in message.photo]
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        # Зберігаємо оригінальні file_id, а не текст
        await process_field_edit(fake_callback, state, "photos", new_photos)
    else:
        await message.answer("❌ Надішліть фото або напишіть 'пропустити'")


@router.message(VehicleEditingStates.waiting_for_add_photos)
async def process_add_photos(message: Message, state: FSMContext):
    """Обробити додавання ще фото"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Додаткова перевірка стану для безпеки
    current_state = await state.get_state()
    if current_state != VehicleEditingStates.waiting_for_add_photos:
        logger.warning(f"📷 process_add_photos: неочікуваний стан {current_state}, пропускаємо")
        return
    
    logger.info(f"📷 process_add_photos: отримано повідомлення від користувача {message.from_user.id}")
    logger.info(f"📷 process_add_photos: тип повідомлення: {type(message)}")
    logger.info(f"📷 process_add_photos: текст: {message.text}")
    logger.info(f"📷 process_add_photos: фото: {len(message.photo) if message.photo else 0}")
    
    if message.text and (message.text.lower().strip() == "пропустити" or message.text.strip() == "⏭️ Пропустити"):
        # Користувач хоче залишити поточні фото - не змінюємо їх
        data = await state.get_data()
        current_photos = data.get('photos', [])
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "photos", current_photos)
        return
    
    if message.photo:
        logger.info(f"📷 process_add_photos: обробляємо фото, кількість: {len(message.photo)}")
        
        # Перевіряємо, чи це медіа-група
        if hasattr(message, 'media_group_id') and message.media_group_id:
            # Це медіа-група - обробляємо всі фото разом
            media_group_id = message.media_group_id
            user_id = message.from_user.id
            
            # Зберігаємо фото в тимчасовому сховищі для медіа-групи
            if not hasattr(process_add_photos, '_media_groups'):
                process_add_photos._media_groups = {}
            
            if media_group_id not in process_add_photos._media_groups:
                process_add_photos._media_groups[media_group_id] = {
                    'photos': [],
                    'user_id': user_id,
                    'processed': False
                }
            
            # Перевіряємо, чи це не перше фото з групи ПЕРЕД додаванням
            if len(process_add_photos._media_groups[media_group_id]['photos']) > 0:
                # Це не перше фото - просто додаємо і виходимо
                process_add_photos._media_groups[media_group_id]['photos'].append(message.photo[-1].file_id)
                logger.info(f"📷 process_add_photos: додано фото до медіа-групи {media_group_id}, всього: {len(process_add_photos._media_groups[media_group_id]['photos'])} (не обробляємо)")
                return
            
            # Додаємо перше фото до групи
            process_add_photos._media_groups[media_group_id]['photos'].append(message.photo[-1].file_id)
            
            logger.info(f"📷 process_add_photos: додано перше фото до медіа-групи {media_group_id}, всього: {len(process_add_photos._media_groups[media_group_id]['photos'])}")
            
            # Запускаємо обробку через 2 секунди (щоб зібрати всі фото)
            import asyncio
            asyncio.create_task(process_add_photos_media_group_after_delay(media_group_id, state, message))
            return
        
        # Якщо не медіа-група, обробляємо як одиночне фото
        # Додаємо нові фото до існуючих
        data = await state.get_data()
        current_photos = data.get('photos', [])
        # Беремо тільки найкращий розмір фото (найбільший)
        best_photo = max(message.photo, key=lambda p: p.file_size)
        new_photos = [best_photo.file_id]
        all_photos = current_photos + new_photos
        
        logger.info(f"📷 process_add_photos: поточні фото: {len(current_photos)}, нові фото: {len(new_photos)} (вибрано найкращий розмір з {len(message.photo)} варіантів), всього: {len(all_photos)}")
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "photos", all_photos)
        # process_field_edit вже повертає до меню редагування
    else:
        await message.answer("❌ Надішліть фото або напишіть 'пропустити'")


@router.message(VehicleEditingStates.waiting_for_replace_photos)
async def process_replace_photos(message: Message, state: FSMContext):
    """Обробити заміну всіх фото"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Додаткова перевірка стану для безпеки
    current_state = await state.get_state()
    if current_state != VehicleEditingStates.waiting_for_replace_photos:
        logger.warning(f"🔄 process_replace_photos: неочікуваний стан {current_state}, пропускаємо")
        return
    
    logger.info(f"🔄 process_replace_photos: почато заміну фото для користувача {message.from_user.id}")
    
    if message.text and (message.text.lower().strip() == "пропустити" or message.text.strip() == "⏭️ Пропустити"):
        # Користувач хоче залишити поточні фото - не змінюємо їх
        data = await state.get_data()
        current_photos = data.get('photos', [])
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "photos", current_photos)
        return
    
    if message.photo:
        # ОБРОБЛЯЄМО ФОТО БЕЗ ВИКОРИСТАННЯ process_media_group_photos
        # Оскільки він призначений для створення авто, а не редагування
        
        logger.info(f"🔄 process_replace_photos: отримано фото, кількість: {len(message.photo)}")
        
        # Перевіряємо, чи це медіа-група
        if hasattr(message, 'media_group_id') and message.media_group_id:
            # Це медіа-група - обробляємо всі фото разом
            media_group_id = message.media_group_id
            user_id = message.from_user.id
            
            # Зберігаємо фото в тимчасовому сховищі для медіа-групи
            if not hasattr(process_replace_photos, '_media_groups'):
                process_replace_photos._media_groups = {}
            
            if media_group_id not in process_replace_photos._media_groups:
                process_replace_photos._media_groups[media_group_id] = {
                    'photos': [],
                    'user_id': user_id,
                    'processed': False
                }
            
            # Перевіряємо, чи це не перше фото з групи ПЕРЕД додаванням
            if len(process_replace_photos._media_groups[media_group_id]['photos']) > 0:
                # Це не перше фото - просто додаємо і виходимо
                process_replace_photos._media_groups[media_group_id]['photos'].append(message.photo[-1].file_id)
                logger.info(f"🔄 process_replace_photos: додано фото до медіа-групи {media_group_id}, всього: {len(process_replace_photos._media_groups[media_group_id]['photos'])} (не обробляємо)")
                return
            
            # Додаємо перше фото до групи
            process_replace_photos._media_groups[media_group_id]['photos'].append(message.photo[-1].file_id)
            
            logger.info(f"🔄 process_replace_photos: додано перше фото до медіа-групи {media_group_id}, всього: {len(process_replace_photos._media_groups[media_group_id]['photos'])}")
            
            # Запускаємо обробку через 2 секунди (щоб зібрати всі фото)
            import asyncio
            asyncio.create_task(process_media_group_after_delay(media_group_id, state, message))
            return
        
        # Якщо не медіа-група, обробляємо як одиночне фото
        # ЗАМІНЮЄМО ВСІ ФОТО НОВИМИ (не додаємо до існуючих!)
        # Беремо тільки найкращий розмір фото (найбільший)
        best_photo = max(message.photo, key=lambda p: p.file_size)
        new_photos = [best_photo.file_id]
        
        logger.info(f"🔄 process_replace_photos: одиночне фото, нові фото: {len(new_photos)} шт. (вибрано найкращий розмір з {len(message.photo)} варіантів)")
        logger.info(f"🔄 process_replace_photos: ВАЖЛИВО: Для заміни на кілька фото надішліть їх як медіа-групу (виберіть кілька фото разом)!")
        
        class FakeCallback:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        fake_callback = FakeCallback(message)
        await process_field_edit(fake_callback, state, "photos", new_photos)
        # process_field_edit вже повертає до меню редагування
    else:
        await message.answer("❌ Надішліть фото або напишіть 'пропустити'")


async def process_media_group_after_delay(media_group_id: str, state: FSMContext, original_message: Message):
    """Обробити медіа-групу після затримки"""
    import asyncio
    import logging
    logger = logging.getLogger(__name__)
    
    # Чекаємо 2 секунди, щоб зібрати всі фото
    await asyncio.sleep(2.0)
    
    # Отримуємо фото з групи
    if not hasattr(process_replace_photos, '_media_groups'):
        return
    
    if media_group_id not in process_replace_photos._media_groups:
        return
    
    group_data = process_replace_photos._media_groups[media_group_id]
    
    if group_data['processed']:
        return
    
    # Позначаємо як оброблену
    group_data['processed'] = True
    
    new_photos = group_data['photos']
    user_id = group_data['user_id']
    
    logger.info(f"🔄 process_media_group_after_delay: обробляємо групу {media_group_id} з {len(new_photos)} фото")
    
    # ЗАМІНЮЄМО ВСІ ФОТО НОВИМИ (не додаємо до існуючих!)
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(original_message)
    await process_field_edit(fake_callback, state, "photos", new_photos)
    
    # Очищуємо дані групи
    del process_replace_photos._media_groups[media_group_id]


async def process_add_photos_media_group_after_delay(media_group_id: str, state: FSMContext, original_message: Message):
    """Обробити медіа-групу для додавання фото після затримки"""
    import asyncio
    import logging
    logger = logging.getLogger(__name__)
    
    # Чекаємо 2 секунди, щоб зібрати всі фото
    await asyncio.sleep(2.0)
    
    # Отримуємо фото з групи
    if not hasattr(process_add_photos, '_media_groups'):
        return
    
    if media_group_id not in process_add_photos._media_groups:
        return
    
    group_data = process_add_photos._media_groups[media_group_id]
    
    if group_data['processed']:
        return
    
    # Позначаємо як оброблену
    group_data['processed'] = True
    
    new_photos = group_data['photos']
    user_id = group_data['user_id']
    
    logger.info(f"📷 process_add_photos_media_group_after_delay: обробляємо групу {media_group_id} з {len(new_photos)} фото")
    
    # ДОДАЄМО НОВІ ФОТО ДО ІСНУЮЧИХ
    data = await state.get_data()
    current_photos = data.get('photos', [])
    all_photos = current_photos + new_photos
    
    logger.info(f"📷 process_add_photos_media_group_after_delay: поточні фото: {len(current_photos)}, нові фото: {len(new_photos)}, всього: {len(all_photos)}")
    
    class FakeCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    fake_callback = FakeCallback(original_message)
    await process_field_edit(fake_callback, state, "photos", all_photos)
    
    # Очищуємо дані групи
    del process_add_photos._media_groups[media_group_id]
