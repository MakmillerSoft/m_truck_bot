"""
Обробники для редагування авто
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.utils.formatting import get_default_parse_mode
from app.modules.admin.core.access_control import AdminAccessFilter
from .states import VehicleEditingStates
from .keyboards import (
    get_editing_menu_keyboard,
    get_field_editing_keyboard,
    get_editing_confirmation_keyboard,
    get_changes_info_keyboard
)
from .navigation import process_field_edit
from ..shared.translations import translate_field_value, reverse_translate_field_value

logger = logging.getLogger(__name__)
router = Router()

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())


@router.callback_query(F.data == "edit_vehicle_card")
async def show_editing_menu(callback: CallbackQuery, state: FSMContext):
    """Показати меню редагування (НОВЕ повідомлення)"""
    await callback.answer()
    
    # Отримуємо дані з FSM
    data = await state.get_data()
    
    # Логування для діагностики
    logger.info(f"🔧 show_editing_menu: дані з FSM: {data}")
    
    # Ініціалізуємо зміни якщо їх немає
    changes = data.get('editing_changes', {})
    
    # Форматуємо текст меню редагування
    menu_text = "🔧 <b>Редагування картки авто</b>\n\n"
    
    if changes:
        changes_list = []
        for field, (old_value, new_value) in changes.items():
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
                "photos": "Фото для групи",
                "main_photo": "Головне фото"
            }
            field_name = field_names.get(field, field)
            changes_list.append(f"✅ <b>{field_name}:</b> {old_value} → {new_value}")
        
        menu_text += "\n".join(changes_list) + "\n\n"
    
    menu_text += "<b>Оберіть поле для редагування:</b>"
    
    # Відправляємо нове повідомлення з меню редагування
    await callback.message.answer(
        menu_text,
        reply_markup=get_editing_menu_keyboard(data, changes),
        parse_mode=get_default_parse_mode()
    )
    
    # Переходимо до стану меню редагування
    await state.set_state(VehicleEditingStates.editing_menu)
    
    logger.info(f"🔧 Показано меню редагування для користувача {callback.from_user.id}")


@router.callback_query(F.data.startswith("edit_field_"))
async def edit_specific_field(callback: CallbackQuery, state: FSMContext):
    """Редагувати конкретне поле (НОВЕ повідомлення)"""
    await callback.answer()
    
    # Отримуємо назву поля
    field_name = callback.data.replace("edit_field_", "")
    
    # Отримуємо поточні дані
    data = await state.get_data()
    current_value = data.get(field_name, "Не вказано")
    
    # Форматуємо текст для редагування поля
    field_display_names = {
        "vehicle_type": "типу авто",
        "brand": "марки",
        "model": "моделі",
        "vin_code": "VIN коду",
        "body_type": "типу кузова",
        "year": "року випуску",
        "condition": "стану",
        "price": "вартості",
        "mileage": "пробігу",
        "fuel_type": "типу палива",
        "engine_volume": "об'єму двигуна",
        "power_hp": "потужності",
        "transmission": "коробки передач",
        "wheel_radius": "радіуса коліс",
        "load_capacity": "вантажопідйомності",
        "total_weight": "загальної маси",
        "cargo_dimensions": "габаритів",
        "location": "місцезнаходження",
        "description": "опису",
        "photos": "фото"
    }
    
    display_name = field_display_names.get(field_name, field_name)
    
    field_text = f"✏️ <b>Редагування {display_name}</b>\n\n"
    field_text += f"Поточне значення: <b>{current_value}</b>\n\n"
    
    if field_name == "photos":
        field_text += "Надішліть нові фото для групи або напишіть 'пропустити' щоб залишити поточні:"
    elif field_name == "main_photo":
        field_text += "Надішліть нове головне фото або напишіть 'пропустити' щоб залишити поточне:"
    else:
        field_text += f"Введіть нове значення для {display_name}:"
    
    # Відправляємо нове повідомлення з полем для редагування
    await callback.message.answer(
        field_text,
        reply_markup=get_field_editing_keyboard(field_name, current_value),
        parse_mode=get_default_parse_mode()
    )
    
    # Переходимо до відповідного стану редагування
    state_mapping = {
        "vehicle_type": VehicleEditingStates.waiting_for_vehicle_type_edit,
        "brand": VehicleEditingStates.waiting_for_brand_edit,
        "model": VehicleEditingStates.waiting_for_model_edit,
        "vin_code": VehicleEditingStates.waiting_for_vin_code_edit,
        "body_type": VehicleEditingStates.waiting_for_body_type_edit,
        "year": VehicleEditingStates.waiting_for_year_edit,
        "condition": VehicleEditingStates.waiting_for_condition_edit,
        "price": VehicleEditingStates.waiting_for_price_edit,
        "mileage": VehicleEditingStates.waiting_for_mileage_edit,
        "fuel_type": VehicleEditingStates.waiting_for_fuel_type_edit,
        "engine_volume": VehicleEditingStates.waiting_for_engine_volume_edit,
        "power_hp": VehicleEditingStates.waiting_for_power_hp_edit,
        "transmission": VehicleEditingStates.waiting_for_transmission_edit,
        "wheel_radius": VehicleEditingStates.waiting_for_wheel_radius_edit,
        "load_capacity": VehicleEditingStates.waiting_for_load_capacity_edit,
        "total_weight": VehicleEditingStates.waiting_for_total_weight_edit,
        "cargo_dimensions": VehicleEditingStates.waiting_for_cargo_dimensions_edit,
        "location": VehicleEditingStates.waiting_for_location_edit,
        "description": VehicleEditingStates.waiting_for_description_edit,
        "photos": VehicleEditingStates.waiting_for_photos_edit,
        "main_photo": VehicleEditingStates.waiting_for_main_photo_edit,
    }
    
    target_state = state_mapping.get(field_name)
    if target_state:
        await state.set_state(target_state)
        # Зберігаємо назву поля для подальшого використання
        await state.update_data(editing_field=field_name)
    
    logger.info(f"✏️ Почато редагування поля {field_name} для користувача {callback.from_user.id}")


@router.callback_query(F.data == "back_to_editing_menu")
async def back_to_editing_menu(callback: CallbackQuery, state: FSMContext):
    """Повернутися до меню редагування"""
    await callback.answer()
    
    # Отримуємо дані з FSM
    data = await state.get_data()
    changes = data.get('editing_changes', {})
    
    # Форматуємо текст меню редагування
    menu_text = "🔧 <b>Редагування картки авто</b>\n\n"
    
    if changes:
        changes_list = []
        for field, (old_value, new_value) in changes.items():
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
                "photos": "Фото для групи",
                "main_photo": "Головне фото"
            }
            field_name = field_names.get(field, field)
            changes_list.append(f"✅ <b>{field_name}:</b> {old_value} → {new_value}")
        
        menu_text += "\n".join(changes_list) + "\n\n"
    
    menu_text += "<b>Оберіть поле для редагування:</b>"
    
    # Відправляємо нове повідомлення з меню редагування
    await callback.message.answer(
        menu_text,
        reply_markup=get_editing_menu_keyboard(data, changes),
        parse_mode=get_default_parse_mode()
    )
    
    # Переходимо до стану меню редагування
    await state.set_state(VehicleEditingStates.editing_menu)
    
    logger.info(f"🔙 Повернутося до меню редагування для користувача {callback.from_user.id}")


@router.callback_query(F.data == "finish_editing")
async def finish_editing(callback: CallbackQuery, state: FSMContext):
    """Завершити редагування (НОВЕ повідомлення з підсумковою карткою)"""
    await callback.answer()
    
    # Отримуємо дані з FSM
    data = await state.get_data()
    changes = data.get('editing_changes', {})
    
    if not changes:
        # Якщо змін не було, просто повертаємося до підсумкової картки
        await back_to_summary_card(callback, state)
        return
    
    # Показуємо підтвердження
    confirmation_text = "✅ <b>Підтвердження завершення редагування</b>\n\n"
    confirmation_text += "<b>Внесені зміни:</b>\n"
    
    for field, (old_value, new_value) in changes.items():
        field_names = {
            "vehicle_type": "Тип авто",
            "brand": "Марка",
            "model": "Модель",
            "vin_code": "VIN код",
            "body_type": "Тип кузова",
            "year": "Рік",
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
            "cargo_dimensions": "Габарити",
            "location": "Місцезнаходження",
            "description": "Опис",
            "photos": "Фото"
        }
        field_name = field_names.get(field, field)
        confirmation_text += f"• <b>{field_name}:</b> {old_value} → {new_value}\n"
    
    confirmation_text += "\n<b>Завершити редагування?</b>"
    
    await callback.message.answer(
        confirmation_text,
        reply_markup=get_editing_confirmation_keyboard(),
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "edit_photos_add")
async def edit_photos_add(callback: CallbackQuery, state: FSMContext):
    """Додати ще фото"""
    await callback.answer()
    
    # Переходимо до стану додавання фото
    await state.set_state(VehicleEditingStates.waiting_for_add_photos)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Створюємо inline клавіатуру з кнопкою "Пропустити"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустити", callback_data="skip_photos_add")]
        ]
    )
    
    await callback.message.answer(
        "📷 <b>Додавання фото</b>\n\n"
        "Надішліть нові фото (одне або кілька разом). "
        "Вони будуть додані до існуючих.\n\n"
        "Або натисніть кнопку <b>Пропустити</b>, щоб залишити поточні фото.",
        reply_markup=keyboard,
        parse_mode=get_default_parse_mode()
    )


@router.callback_query(F.data == "edit_photos_replace")
async def edit_photos_replace(callback: CallbackQuery, state: FSMContext):
    """Змінити всі фото"""
    await callback.answer()
    
    # Переходимо до стану заміни фото
    await state.set_state(VehicleEditingStates.waiting_for_replace_photos)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Створюємо inline клавіатуру з кнопкою "Пропустити"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустити", callback_data="skip_photos_replace")]
        ]
    )
    
    await callback.message.answer(
        "📷 <b>Заміна всіх фото</b>\n\n"
        "Надішліть нові фото (одне або кілька разом). "
        "Вони замінять всі поточні фото.\n\n"
        "Або натисніть кнопку <b>Пропустити</b>, щоб залишити поточні фото.",
        reply_markup=keyboard,
        parse_mode=get_default_parse_mode()
    )


# Обробники повідомлень для фото перенесені в navigation.py


@router.callback_query(F.data == "skip_photos_add")
async def skip_photos_add(callback: CallbackQuery, state: FSMContext):
    """Пропустити додавання фото"""
    await callback.answer()
    
    # Залишаємо поточні фото без змін
    data = await state.get_data()
    current_photos = data.get('photos', [])
    
    # Повертаємося до меню редагування
    await show_editing_menu(callback, state)


@router.callback_query(F.data == "skip_photos_replace")
async def skip_photos_replace(callback: CallbackQuery, state: FSMContext):
    """Пропустити заміну фото"""
    await callback.answer()
    
    # Залишаємо поточні фото без змін
    data = await state.get_data()
    current_photos = data.get('photos', [])
    
    # Повертаємося до меню редагування
    await show_editing_menu(callback, state)


@router.callback_query(F.data == "confirm_finish_editing")
async def confirm_finish_editing(callback: CallbackQuery, state: FSMContext):
    """Підтвердити завершення редагування"""
    await callback.answer()
    
    # Переходимо до підсумкової картки
    await back_to_summary_card(callback, state)


async def back_to_summary_card(callback: CallbackQuery, state: FSMContext):
    """Повернутися до підсумкової картки з оновленими даними"""
    from ..creation.summary_card import format_vehicle_summary, get_summary_card_keyboard
    from ..listing.formatters import format_admin_vehicle_card
    from app.modules.database.manager import DatabaseManager
    import logging
    logger = logging.getLogger(__name__)
    
    # Отримуємо дані з FSM
    data = await state.get_data()
    changes = data.get('editing_changes', {})
    editing_mode = data.get('editing_mode', 'creation')
    
    logger.info(f"🔧 back_to_summary_card: дані з FSM: {data}")
    logger.info(f"🔧 back_to_summary_card: зміни: {changes}")
    logger.info(f"🔧 back_to_summary_card: режим редагування: {editing_mode}")
    
    # Якщо це редагування існуючого авто, зберігаємо зміни в БД
    if editing_mode == 'existing' and changes:
        vehicle_id = data.get('vehicle_id')
        if vehicle_id:
            # Підготовлюємо дані для збереження в БД
            update_data = {}
            for field, (old_value, new_value) in changes.items():
                if field == 'vehicle_type' and new_value:
                    from app.modules.database.models import VehicleType
                    # Перекладаємо з української на англійську для enum
                    english_value = reverse_translate_field_value('vehicle_type', new_value)
                    update_data[field] = VehicleType(english_value)
                elif field == 'condition' and new_value:
                    from app.modules.database.models import VehicleCondition
                    # Перекладаємо з української на англійську для enum
                    english_value = reverse_translate_field_value('condition', new_value)
                    update_data[field] = VehicleCondition(english_value)
                elif field == 'photos':
                    update_data[field] = new_value
                else:
                    update_data[field] = new_value
            
            # Зберігаємо зміни в БД
            db_manager = DatabaseManager()
            success = await db_manager.update_vehicle(vehicle_id, update_data)
            
            if success:
                logger.info(f"✅ Зміни збережено в БД для авто ID {vehicle_id}")
            else:
                logger.error(f"❌ Помилка збереження змін в БД для авто ID {vehicle_id}")
    
    # Очищуємо зміни редагування (але основні дані залишаються оновленими)
    await state.update_data(editing_changes={})
    
    # ПЕРЕВІРЯЄМО, ЧИ ДАНІ НЕ ВТРАЧЕНІ
    updated_data = await state.get_data()
    logger.info(f"🔧 back_to_summary_card: дані після очищення змін: {updated_data}")
    
    # Форматуємо оновлену підсумкову картку
    if editing_mode == 'existing':
        # Для існуючого авто показуємо детальну картку
        vehicle_id = updated_data.get('vehicle_id')
        if vehicle_id:
            # Ініціалізуємо DatabaseManager
            db_manager = DatabaseManager()
            vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
            if vehicle:
                summary_text, photo_file_id = format_admin_vehicle_card(vehicle)
            else:
                summary_text = "❌ Авто не знайдено в базі даних"
                photo_file_id = None
        else:
            summary_text = "❌ ID авто не знайдено"
            photo_file_id = None
    else:
        # Для нового авто використовуємо старий формат
        summary_text = format_vehicle_summary(updated_data)
        photo_file_id = None
    
    # Додаємо інформацію про зміни якщо вони були (з обмеженням довжини)
    if changes:
        changes_info = "\n\n<b>✅ Внесені зміни:</b>\n"
        for field, (old_value, new_value) in changes.items():
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
                "photos": "Фото для групи",
                "main_photo": "Головне фото"
            }
            field_name = field_names.get(field, field)
            
            # Обмежуємо довжину значень для фото (file_id дуже довгі)
            if field == "photos":
                old_display = f"{len(old_value) if isinstance(old_value, list) else 0} шт."
                new_display = f"{len(new_value) if isinstance(new_value, list) else 0} шт."
            else:
                old_display = str(old_value)[:50] + "..." if len(str(old_value)) > 50 else str(old_value)
                new_display = str(new_value)[:50] + "..." if len(str(new_value)) > 50 else str(new_value)
            
            changes_info += f"• <b>{field_name}:</b> {old_display} → {new_display}\n"
        
        # Перевіряємо загальну довжину тексту (Telegram обмеження 1024 символи)
        if len(summary_text + changes_info) > 1000:  # Залишаємо запас
            changes_info = "\n\n<b>✅ Внесені зміни:</b>\n"
            changes_count = len(changes)
            changes_info += f"• Оновлено {changes_count} полів\n"
        
        summary_text += changes_info
    
    # Відправляємо оновлену підсумкову картку
    if editing_mode == 'existing':
        # Для існуючого авто показуємо детальну картку з кнопками
        vehicle_id = updated_data.get('vehicle_id')
        if vehicle_id:
            from ..listing.keyboards import get_vehicle_detail_keyboard
            
            if photo_file_id:
                try:
                    await callback.message.answer_photo(
                        photo=photo_file_id,
                        caption=summary_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id),
                        parse_mode=get_default_parse_mode()
                    )
                except Exception as photo_error:
                    logger.warning(f"⚠️ Не вдалося відправити фото для авто {vehicle_id}: {photo_error}")
                    # Якщо фото недійсне, відправляємо тільки текст
                    await callback.message.answer(
                        summary_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id),
                        parse_mode=get_default_parse_mode()
                    )
            else:
                await callback.message.answer(
                    summary_text,
                    reply_markup=get_vehicle_detail_keyboard(vehicle_id),
                    parse_mode=get_default_parse_mode()
                )
        else:
            await callback.message.answer(
                summary_text,
                parse_mode=get_default_parse_mode()
            )
        
        # Очищуємо тільки дані редагування, зберігаючи дані пагінації
        await state.update_data(
            editing_changes={},
            editing_mode=None,
            vehicle_id=None,
            editing_field=None
        )
    else:
        # Для нового авто використовуємо старий формат
        photos = data.get('photos', [])
        
        # Перевіряємо, чи photos є масивом file_id
        if isinstance(photos, list) and photos and isinstance(photos[0], str) and photos[0].startswith('AgAC'):
            # Це масив file_id - все добре
            pass
        else:
            # Якщо photos не є масивом file_id, встановлюємо порожній масив
            photos = []
        
        if photos:
            # Відправляємо нове повідомлення з фото та оновленою карткою
            try:
                await callback.message.answer_photo(
                    photo=photos[0],
                    caption=summary_text,
                    reply_markup=get_summary_card_keyboard(),
                    parse_mode=get_default_parse_mode()
                )
            except Exception as photo_error:
                logger.warning(f"⚠️ Не вдалося відправити фото для нового авто: {photo_error}")
                # Якщо фото недійсне, відправляємо тільки текст
                await callback.message.answer(
                    summary_text,
                    reply_markup=get_summary_card_keyboard(),
                    parse_mode=get_default_parse_mode()
                )
        else:
            # Відправляємо нове повідомлення тільки з текстом
            await callback.message.answer(
                text=summary_text,
                reply_markup=get_summary_card_keyboard(),
                parse_mode=get_default_parse_mode()
            )
        
        # Переходимо до стану підсумкової картки (НЕ очищуємо дані!)
        from ..creation.states import VehicleCreationStates
        await state.set_state(VehicleCreationStates.summary_card)
    
    logger.info(f"✅ Завершено редагування для користувача {callback.from_user.id}")
    logger.info(f"🔧 back_to_summary_card: режим редагування: {editing_mode}")


@router.callback_query(F.data == "show_changes_info")
async def show_changes_info(callback: CallbackQuery, state: FSMContext):
    """Показати детальну інформацію про зміни"""
    await callback.answer()
    
    # Отримуємо дані з FSM
    data = await state.get_data()
    changes = data.get('editing_changes', {})
    
    if not changes:
        await callback.answer("Немає змін для відображення", show_alert=True)
        return
    
    changes_text = "📝 <b>Детальна інформація про зміни</b>\n\n"
    
    for field, (old_value, new_value) in changes.items():
        field_names = {
            "vehicle_type": "Тип авто",
            "brand": "Марка",
            "model": "Модель",
            "vin_code": "VIN код",
            "body_type": "Тип кузова",
            "year": "Рік",
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
            "cargo_dimensions": "Габарити",
            "location": "Місцезнаходження",
            "description": "Опис",
            "photos": "Фото"
        }
        field_name = field_names.get(field, field)
        changes_text += f"<b>{field_name}:</b>\n"
        changes_text += f"  Було: {old_value}\n"
        changes_text += f"  Стало: {new_value}\n\n"
    
    await callback.message.answer(
        changes_text,
        reply_markup=get_changes_info_keyboard(),
        parse_mode=get_default_parse_mode()
    )


# Обробники для inline кнопок редагування
@router.callback_query(F.data.startswith("edit_condition_"))
async def edit_condition_via_button(callback: CallbackQuery, state: FSMContext):
    """Редагування стану через кнопку"""
    await callback.answer()
    
    condition_value = callback.data.replace("edit_condition_", "")
    condition_map = {
        "new": "Новий",
        "used": "Вживане"
    }
    
    new_value = condition_map.get(condition_value, condition_value)
    
    # Створюємо фейковий callback для обробки
    class FakeCallback:
        def __init__(self, callback):
            self.message = callback.message
            self.from_user = callback.from_user
    
    fake_callback = FakeCallback(callback)
    await process_field_edit(fake_callback, state, "condition", new_value)


@router.callback_query(F.data.startswith("edit_fuel_"))
async def edit_fuel_type_via_button(callback: CallbackQuery, state: FSMContext):
    """Редагування типу палива через кнопку"""
    await callback.answer()
    
    fuel_value = callback.data.replace("edit_fuel_", "")
    fuel_map = {
        "diesel": "Дизель",
        "petrol": "Бензин",
        "gas": "Газ",
        "gas_petrol": "Газ/Бензин",
        "electric": "Електричний"
    }
    
    new_value = fuel_map.get(fuel_value, fuel_value)
    
    class FakeCallback:
        def __init__(self, callback):
            self.message = callback.message
            self.from_user = callback.from_user
    
    fake_callback = FakeCallback(callback)
    await process_field_edit(fake_callback, state, "fuel_type", new_value)


@router.callback_query(F.data.startswith("edit_transmission_"))
async def edit_transmission_via_button(callback: CallbackQuery, state: FSMContext):
    """Редагування коробки передач через кнопку"""
    await callback.answer()
    
    transmission_value = callback.data.replace("edit_transmission_", "")
    transmission_map = {
        "automatic": "Автоматична",
        "manual": "Механічна",
        "robot": "Робот",
        "cvt": "CVT"
    }
    
    new_value = transmission_map.get(transmission_value, transmission_value)
    
    class FakeCallback:
        def __init__(self, callback):
            self.message = callback.message
            self.from_user = callback.from_user
    
    fake_callback = FakeCallback(callback)
    await process_field_edit(fake_callback, state, "transmission", new_value)


@router.callback_query(F.data.startswith("clear_field_"))
async def clear_field(callback: CallbackQuery, state: FSMContext):
    """Очистити поле"""
    await callback.answer()
    
    # Отримуємо назву поля
    field_name = callback.data.replace("clear_field_", "")
    
    # Отримуємо поточні дані
    data = await state.get_data()
    current_value = data.get(field_name, "Не вказано")
    
    # Очищаємо поле (встановлюємо порожнє значення)
    new_value = ""
    
    # Оновлюємо дані в FSM
    await state.update_data(**{field_name: new_value})
    
    # Додаємо зміну до списку змін
    changes = data.get('editing_changes', {})
    changes[field_name] = (current_value, "[Очищено]")
    await state.update_data(editing_changes=changes)
    
    # Форматуємо повідомлення про очистку
    field_display_names = {
        "vehicle_type": "типу авто",
        "brand": "марки",
        "model": "моделі",
        "vin_code": "VIN коду",
        "body_type": "типу кузова",
        "year": "року випуску",
        "condition": "стану",
        "price": "вартості",
        "mileage": "пробігу",
        "fuel_type": "типу палива",
        "engine_volume": "об'єму двигуна",
        "power_hp": "потужності",
        "transmission": "коробки передач",
        "wheel_radius": "радіуса коліс",
        "load_capacity": "вантажопідйомності",
        "total_weight": "загальної маси",
        "cargo_dimensions": "габаритів",
        "location": "місцезнаходження",
        "description": "опису",
        "photos": "фото"
    }
    
    display_name = field_display_names.get(field_name, field_name)
    
    # Показуємо підтвердження очистки
    confirmation_text = f"🗑️ <b>Поле очищено</b>\n\n"
    confirmation_text += f"<b>{display_name}</b> було очищено.\n"
    confirmation_text += f"Було: <b>{current_value}</b>\n"
    confirmation_text += f"Стало: <b>[Очищено]</b>\n\n"
    confirmation_text += "Повертаємося до меню редагування..."
    
    await callback.message.answer(
        confirmation_text,
        parse_mode=get_default_parse_mode()
    )
    
    # Повертаємося до меню редагування
    await back_to_editing_menu(callback, state)
    
    logger.info(f"🗑️ Очищено поле {field_name} для користувача {callback.from_user.id}")


@router.callback_query(F.data.startswith("edit_location_"))
async def edit_location_via_button(callback: CallbackQuery, state: FSMContext):
    """Редагування місцезнаходження через кнопку"""
    await callback.answer()
    
    location_value = callback.data.replace("edit_location_", "")
    location_map = {
        "lutsk": "Луцьк"
    }
    
    new_value = location_map.get(location_value, location_value)
    
    class FakeCallback:
        def __init__(self, callback):
            self.message = callback.message
            self.from_user = callback.from_user
    
    fake_callback = FakeCallback(callback)
    await process_field_edit(fake_callback, state, "location", new_value)
