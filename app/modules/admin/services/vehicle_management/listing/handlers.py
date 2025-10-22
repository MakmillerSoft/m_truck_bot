"""
Обробники для блоку "Всі авто"
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.modules.admin.core.access_control import AdminAccessFilter
from app.modules.database.manager import DatabaseManager
from .keyboards import get_vehicles_list_keyboard, get_vehicle_detail_keyboard
from ..stats.statistics import get_vehicles_statistics
from .formatters import format_admin_vehicle_card, format_vehicle_list_item
from ..editing.handlers import show_editing_menu
from ..editing.states import VehicleEditingStates

logger = logging.getLogger(__name__)
router = Router()

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())

# Ініціалізуємо менеджер бази даних
db_manager = DatabaseManager()


@router.callback_query(F.data == "admin_all_vehicles")
async def show_all_vehicles(callback: CallbackQuery, state: FSMContext):
    """Показати всі авто зі статистикою та пагінацією"""
    await callback.answer()
    
    try:
        # Отримуємо статистику
        stats = await get_vehicles_statistics()
        
        # Отримуємо першу сторінку авто (10 штук) з сортуванням за датою (від наймолодших)
        vehicles = await db_manager.get_vehicles(limit=10, offset=0, sort_by="created_at_desc")
        
        # Форматуємо текст зі статистикою
        stats_text = f"""📋 <b>Всі авто</b>

📊 <b>Статистика:</b>
• 🚛 <b>Всього авто:</b> {stats['total_vehicles']}
• 🏷️ <b>Марок:</b> {stats['total_brands']}

🏭 <b>Топ марки:</b>
"""
        
        # Додаємо топ-5 марок
        for i, (brand, count) in enumerate(stats['top_brands'][:5], 1):
            stats_text += f"{i}. <b>{brand}</b> - {count} авто\n"
        
        stats_text += f"\n📄 <b>Сторінка 1 з {stats['total_pages']}</b>"
        
        if not vehicles:
            stats_text += "\n\n❌ <b>Авто не знайдено</b>\nПоки що немає доданих авто."
        
        # Відправляємо повідомлення зі статистикою та списком авто
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_vehicles_list_keyboard(vehicles, current_page=1, total_pages=stats['total_pages'], sort_by="created_at_desc", status_filter="all"),
            parse_mode="HTML"
        )
        
        # Зберігаємо поточну сторінку та сортування в стані
        await state.update_data(vehicles_page=1, vehicles_sort="created_at_desc", vehicles_status_filter="all")
        
        logger.info(f"📋 Показано всі авто для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження авто: {e}")
        await callback.message.edit_text(
            f"❌ <b>Помилка завантаження</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("vehicles_page_"))
async def navigate_vehicles_page(callback: CallbackQuery, state: FSMContext):
    """Навігація по сторінках авто"""
    await callback.answer()
    
    try:
        # Отримуємо номер сторінки з callback_data
        page = int(callback.data.replace("vehicles_page_", ""))
        
        # Отримуємо дані з стану
        state_data = await state.get_data()
        total_pages = state_data.get('total_pages', 1)
        sort_by = state_data.get('sort_by', 'created_at_asc')
        
        # Перевіряємо валідність сторінки
        if page < 1 or page > total_pages:
            await callback.answer("❌ Недійсна сторінка", show_alert=True)
            return
        
        # Отримуємо авто для поточної сторінки
        offset = (page - 1) * 10
        vehicles = await db_manager.get_vehicles(limit=10, offset=offset, sort_by=sort_by)
        
        # Отримуємо статистику для заголовка
        stats = await get_vehicles_statistics()
        
        # Форматуємо текст
        stats_text = f"""📋 <b>Всі авто</b>

📊 <b>Статистика:</b>
• 🚛 <b>Всього авто:</b> {stats['total_vehicles']}
• 🏷️ <b>Марок:</b> {stats['total_brands']}

🏭 <b>Топ марки:</b>
"""
        
        # Додаємо топ-5 марок
        for i, (brand, count) in enumerate(stats['top_brands'][:5], 1):
            stats_text += f"{i}. <b>{brand}</b> - {count} авто\n"
        
        stats_text += f"\n📄 <b>Сторінка {page} з {total_pages}</b>"
        
        # Оновлюємо повідомлення
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_vehicles_list_keyboard(vehicles, current_page=page, total_pages=total_pages, sort_by=sort_by),
            parse_mode="HTML"
        )
        
        # Оновлюємо поточну сторінку в стані
        await state.update_data(current_page=page)
        
        logger.info(f"📄 Перехід на сторінку {page} для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка навігації по сторінках: {e}")
        await callback.answer("❌ Помилка навігації", show_alert=True)


@router.callback_query(F.data.startswith("view_vehicle_"))
async def view_vehicle_detail(callback: CallbackQuery, state: FSMContext):
    """Перегляд деталей конкретного авто"""
    await callback.answer()
    
    try:
        # Отримуємо ID авто з callback_data
        vehicle_id = int(callback.data.replace("view_vehicle_", ""))
        
        # Отримуємо авто з бази даних
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            await callback.answer("❌ Авто не знайдено", show_alert=True)
            return
        
        # Перевіряємо існування повідомлення в групі (якщо авто опубліковано)
        if vehicle.published_in_group and vehicle.group_message_id:
            from app.config.settings import settings
            if settings.group_chat_id:
                message_exists = await check_group_message_exists(callback.bot, settings.group_chat_id, vehicle.group_message_id)
                
                if not message_exists:
                    # Повідомлення не існує - очищаємо дані в БД
                    await db_manager.update_vehicle(vehicle_id, {
                        'group_message_id': None,
                        'published_in_group': False
                    })
                    
                    # Отримуємо оновлене авто
                    vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
                    logger.info(f"🔄 Авто {vehicle_id}: повідомлення в групі не існує, статус оновлено")
        
        # Форматуємо картку авто з умовним відображенням полів
        detail_text, photo_file_id = format_admin_vehicle_card(vehicle)
        
        # Відправляємо детальну інформацію з медіа або без
        if photo_file_id:
            # Визначаємо тип: фото чи відео (префікс video:)
            is_video = isinstance(photo_file_id, str) and photo_file_id.startswith("video:")
            file_id = photo_file_id.split(":", 1)[1] if is_video else photo_file_id
            
            if is_video:
                try:
                    await callback.message.answer_video(
                        video=file_id,
                        caption=detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
                except Exception as video_error:
                    logger.warning(f"⚠️ Не вдалося відправити відео для авто {vehicle_id}: {video_error}")
                    # Якщо відео недійсне, відправляємо тільки текст
                    await callback.message.answer(
                        detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
            else:
                try:
                    await callback.message.answer_photo(
                        photo=file_id,
                        caption=detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
                except Exception as photo_error:
                    logger.warning(f"⚠️ Не вдалося відправити фото для авто {vehicle_id}: {photo_error}")
                    # Якщо фото недійсне, відправляємо тільки текст
                    await callback.message.answer(
                        detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
        else:
            await callback.message.edit_text(
                detail_text,
                reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                parse_mode="HTML"
            )
        
        logger.info(f"👁️ Перегляд авто {vehicle_id} користувачем {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка перегляду авто: {e}")
        await callback.answer("❌ Помилка завантаження авто", show_alert=True)


@router.callback_query(F.data == "back_to_vehicles_list")
async def back_to_vehicles_list(callback: CallbackQuery, state: FSMContext):
    """Повернутися до списку авто"""
    await callback.answer()
    
    try:
        # Отримуємо поточну сторінку та сортування з стану
        state_data = await state.get_data()
        current_page = state_data.get('current_page', 1)
        sort_by = state_data.get('sort_by', 'created_at_asc')
        
        # Якщо дані пагінації відсутні, скидаємо до першої сторінки
        if not state_data.get('total_pages'):
            logger.warning(f"⚠️ Дані пагінації відсутні, скидаємо до першої сторінки")
            current_page = 1
        
        # Отримуємо авто для поточної сторінки
        offset = (current_page - 1) * 10
        vehicles = await db_manager.get_vehicles(limit=10, offset=offset, sort_by=sort_by)
        
        # Отримуємо статистику
        stats = await get_vehicles_statistics()
        
        # Форматуємо текст
        stats_text = f"""📋 <b>Всі авто</b>

📊 <b>Статистика:</b>
• 🚛 <b>Всього авто:</b> {stats['total_vehicles']}
• 🏷️ <b>Марок:</b> {stats['total_brands']}

🏭 <b>Топ марки:</b>
"""
        
        # Додаємо топ-5 марок
        for i, (brand, count) in enumerate(stats['top_brands'][:5], 1):
            stats_text += f"{i}. <b>{brand}</b> - {count} авто\n"
        
        stats_text += f"\n📄 <b>Сторінка {current_page} з {stats['total_pages']}</b>"
        
        # Спробуємо редагувати повідомлення, якщо не вдається - відправимо нове
        try:
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_vehicles_list_keyboard(vehicles, current_page=current_page, total_pages=stats['total_pages'], sort_by=sort_by),
                parse_mode="HTML"
            )
        except Exception as edit_error:
            # Якщо не можемо редагувати (наприклад, повідомлення з фото), відправляємо нове
            await callback.message.answer(
                stats_text,
                reply_markup=get_vehicles_list_keyboard(vehicles, current_page=current_page, total_pages=stats['total_pages'], sort_by=sort_by),
                parse_mode="HTML"
            )
        
        # Зберігаємо дані пагінації в стані
        await state.update_data(
            current_page=current_page,
            total_pages=stats['total_pages'],
            sort_by=sort_by
        )
        
        logger.info(f"🔙 Повернення до списку авто на сторінку {current_page}")
        
    except Exception as e:
        logger.error(f"❌ Помилка повернення до списку: {e}")
        await callback.answer("❌ Помилка повернення", show_alert=True)


@router.callback_query(F.data.startswith("edit_vehicle_"))
async def edit_existing_vehicle(callback: CallbackQuery, state: FSMContext):
    """Редагувати існуюче авто"""
    await callback.answer()
    
    try:
        # Отримуємо ID авто з callback_data
        vehicle_id = int(callback.data.replace("edit_vehicle_", ""))
        
        # Отримуємо авто з бази даних
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            await callback.message.edit_text(
                "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                parse_mode="HTML"
            )
            return
        
        # Отримуємо поточні дані пагінації з FSM
        current_state_data = await state.get_data()
        current_page = current_state_data.get('current_page', 1)
        total_pages = current_state_data.get('total_pages', 1)
        sort_by = current_state_data.get('sort_by', 'created_at_asc')
        
        # Конвертуємо VehicleModel в словник для FSM
        vehicle_data = {
            'vehicle_id': vehicle.id,
            'vehicle_type': vehicle.vehicle_type.value if vehicle.vehicle_type else None,
            'brand': vehicle.brand,
            'model': vehicle.model,
            'vin_code': vehicle.vin_code,
            'body_type': vehicle.body_type,
            'year': vehicle.year,
            'condition': vehicle.condition.value if vehicle.condition else None,
            'price': vehicle.price,
            'mileage': vehicle.mileage,
            'fuel_type': vehicle.fuel_type,
            'engine_volume': vehicle.engine_volume,
            'power_hp': vehicle.power_hp,
            'transmission': vehicle.transmission,
            'wheel_radius': vehicle.wheel_radius,
            'load_capacity': vehicle.load_capacity,
            'total_weight': vehicle.total_weight,
            'cargo_dimensions': vehicle.cargo_dimensions,
            'location': vehicle.location,
            'description': vehicle.description,
            'photos': vehicle.photos,
            'editing_changes': {},  # Ініціалізуємо зміни
            'editing_mode': 'existing',  # Позначаємо що це редагування існуючого авто
            # Зберігаємо дані пагінації
            'current_page': current_page,
            'total_pages': total_pages,
            'sort_by': sort_by
        }
        
        # Зберігаємо дані в FSM
        await state.update_data(**vehicle_data)
        
        # Переходимо до стану редагування
        await state.set_state(VehicleEditingStates.editing_menu)
        
        # Показуємо меню редагування
        await show_editing_menu(callback, state)
        
        logger.info(f"✏️ Запущено редагування авто ID {vehicle_id} для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка запуску редагування: {e}")
        await callback.message.edit_text(
            f"❌ <b>Помилка запуску редагування</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("sort_vehicles_"))
async def sort_vehicles(callback: CallbackQuery, state: FSMContext):
    """Змінити сортування авто"""
    await callback.answer()
    
    try:
        # Отримуємо тип сортування та статус фільтр з callback_data
        # Формат: sort_vehicles_created_at_desc_available
        data_part = callback.data.replace("sort_vehicles_", "")
        
        # Знаходимо останній підкреслення для розділення сортування та статусу
        if "_" in data_part:
            parts = data_part.rsplit("_", 1)  # Розбиваємо з кінця на 2 частини
            if len(parts) == 2:
                sort_type = parts[0]  # created_at_desc
                status_filter = parts[1]  # available
            else:
                sort_type = data_part
                status_filter = "all"
        else:
            # Fallback для старих callback_data
            sort_type = data_part
            status_filter = "all"
        
        # Отримуємо дані з стану
        state_data = await state.get_data()
        current_page = state_data.get('vehicles_page', 1)
        
        # Отримуємо авто з урахуванням статус фільтра та сортування
        if status_filter == "all":
            vehicles = await db_manager.get_vehicles(
                limit=10, 
                offset=(current_page - 1) * 10, 
                sort_by=sort_type
            )
            stats = await get_vehicles_statistics()
            total_count = stats['total_vehicles']
        else:
            vehicles = await db_manager.get_vehicles_by_status(
                status=status_filter,
                page=current_page, 
                per_page=10, 
                sort_by=sort_type
            )
            total_count = await db_manager.get_vehicles_count_by_status(status_filter)
        
        total_pages = (total_count + 9) // 10
        
        # Форматуємо текст з урахуванням статус фільтра
        from ..shared.translations import translate_field_value
        status_text = "Всі авто" if status_filter == "all" else translate_field_value('status', status_filter)
        
        stats_text = f"""📋 <b>Список авто - {status_text}</b>

📊 <b>Статистика:</b>
• 🚛 <b>Знайдено авто:</b> {total_count}
• 🏷️ <b>Марок:</b> {len(set(v.brand for v in vehicles if v.brand))}

🏭 <b>Топ марки:</b>
"""
        
        # Додаємо топ-5 марок з поточного списку
        brand_counts = {}
        for vehicle in vehicles:
            if vehicle.brand:
                brand_counts[vehicle.brand] = brand_counts.get(vehicle.brand, 0) + 1
        
        sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
        for i, (brand, count) in enumerate(sorted_brands[:5], 1):
            stats_text += f"{i}. <b>{brand}</b> - {count} авто\n"
        
        # Додаємо інформацію про сортування
        sort_names = {
            "created_at_desc": "📅 Дата (нові → старі)",
            "created_at_asc": "📅 Дата (старі → нові)",
            "price_desc": "💰 Ціна (висока → низька)",
            "price_asc": "💰 Ціна (низька → висока)",
        }
        
        sort_name = sort_names.get(sort_type, "Невідоме сортування")
        stats_text += f"\n🔄 <b>Сортування:</b> {sort_name}"
        stats_text += f"\n📄 <b>Сторінка {current_page} з {total_pages}</b>"
        
        # Оновлюємо повідомлення
        try:
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_vehicles_list_keyboard(
                    vehicles, 
                    current_page=current_page, 
                    total_pages=total_pages, 
                    sort_by=sort_type,
                    status_filter=status_filter
                ),
                parse_mode="HTML"
            )
        except Exception as edit_error:
            # Якщо не можемо редагувати, відправляємо нове повідомлення
            await callback.message.answer(
                stats_text,
                reply_markup=get_vehicles_list_keyboard(
                    vehicles, 
                    current_page=current_page, 
                    total_pages=total_pages, 
                    sort_by=sort_type,
                    status_filter=status_filter
                ),
                parse_mode="HTML"
            )
        
        # Оновлюємо стан
        await state.update_data(
            vehicles_sort=sort_type,
            vehicles_status_filter=status_filter,
            vehicles_page=current_page
        )
        
        logger.info(f"🔄 Змінено сортування на {sort_type} з фільтром {status_filter} для користувача {callback.from_user.id}")
        logger.debug(f"🔍 Callback data: {callback.data}, parsed: sort_type='{sort_type}', status_filter='{status_filter}'")
        
    except Exception as e:
        logger.error(f"❌ Помилка зміни сортування: {e}")
        await callback.answer("❌ Помилка зміни сортування", show_alert=True)


@router.callback_query(F.data.startswith("publish_vehicle_"))
async def publish_vehicle_to_group(callback: CallbackQuery, state: FSMContext):
    """Опублікувати авто в групу (тільки в групу, дані з БД)"""
    await callback.answer()
    
    try:
        # Отримуємо ID авто з callback_data
        vehicle_id = int(callback.data.replace("publish_vehicle_", ""))
        
        # Отримуємо авто з бази даних
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            try:
                await callback.message.edit_text(
                    "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                    parse_mode="HTML"
                )
            except Exception:
                # Якщо не можемо редагувати (наприклад, повідомлення з фото), відправляємо нове
                await callback.message.answer(
                    "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                    parse_mode="HTML"
                )
            return
        
        # Імпортуємо GroupPublisher
        from ..publication.group_publisher import create_group_publisher
        
        # Створюємо публікатор для групи
        group_publisher = await create_group_publisher(callback.bot)
        
        # Конвертуємо VehicleModel в словник для публікації
        from ..shared.translations import translate_field_value
        
        vehicle_data = {
            'vehicle_id': vehicle_id,  # Додаємо ID авто
            'vehicle_type': translate_field_value('vehicle_type', vehicle.vehicle_type.value) if vehicle.vehicle_type else None,
            'brand': vehicle.brand,
            'model': vehicle.model,
            'vin_code': vehicle.vin_code,
            'body_type': vehicle.body_type,
            'year': vehicle.year,
            'condition': translate_field_value('condition', vehicle.condition.value) if vehicle.condition else None,
            'price': vehicle.price,
            'mileage': vehicle.mileage,
            'fuel_type': translate_field_value('fuel_type', vehicle.fuel_type) if vehicle.fuel_type else None,
            'engine_volume': vehicle.engine_volume,
            'power_hp': vehicle.power_hp,
            'transmission': translate_field_value('transmission', vehicle.transmission) if vehicle.transmission else None,
            'wheel_radius': vehicle.wheel_radius,
            'load_capacity': vehicle.load_capacity,
            'total_weight': vehicle.total_weight,
            'cargo_dimensions': vehicle.cargo_dimensions,
            'location': vehicle.location,
            'description': vehicle.description,
            'photos': vehicle.photos
        }
        
        # Публікуємо авто в групу
        logger.info(f"🚀 Починаємо публікацію авто ID {vehicle_id} в групу")
        logger.info(f"📊 Дані авто: brand={vehicle.brand}, model={vehicle.model}, photos_count={len(vehicle.photos) if vehicle.photos else 0}")
        
        success, error_message, group_message_id = await group_publisher.publish_vehicle_to_group(vehicle_data)
        
        logger.info(f"📤 Результат публікації: success={success}, message={error_message}")
        
        if success:
            # Оновлюємо статус публікації в БД
            await db_manager.update_vehicle(vehicle_id, {
                'published_in_group': True,
                'published_at': None,  # Поки що не зберігаємо дату публікації
                'group_message_id': group_message_id
            })
            
            # Показуємо просте повідомлення про успіх
            success_text = "✅ <b>АВТО УСПІШНО ОПУБЛІКОВАНО В ГРУПУ</b>\n\nОперація завершена успішно!"
            
            try:
                await callback.message.edit_text(
                    success_text,
                    parse_mode="HTML"
                )
            except Exception:
                # Якщо не можемо редагувати (наприклад, повідомлення з фото), відправляємо нове
                await callback.message.answer(
                    success_text,
                    parse_mode="HTML"
                )
            
            # Відправляємо окреме повідомлення з карткою авто
            await send_vehicle_card_message(callback, vehicle_id)
            
            logger.info(f"✅ Авто ID {vehicle_id} успішно опубліковано в групу користувачем {callback.from_user.id}")
            
        else:
            # Показуємо просте повідомлення про помилку
            error_text = f"❌ <b>ПОМИЛКА ПУБЛІКАЦІЇ</b>\n\n{error_message}\n\nСпробуйте ще раз або зверніться до адміністратора."
            
            try:
                await callback.message.edit_text(
                    error_text,
                    parse_mode="HTML"
                )
            except Exception:
                # Якщо не можемо редагувати (наприклад, повідомлення з фото), відправляємо нове
                await callback.message.answer(
                    error_text,
                    parse_mode="HTML"
                )
            
            # Відправляємо окреме повідомлення з карткою авто
            await send_vehicle_card_message(callback, vehicle_id)
            
            logger.error(f"❌ Помилка публікації авто ID {vehicle_id} в групу для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка публікації авто в групу: {e}")
        try:
            await callback.message.edit_text(
                f"❌ <b>Помилка публікації авто в групу</b>\n\n{str(e)}",
                parse_mode="HTML"
            )
        except Exception:
            # Якщо не можемо редагувати (наприклад, повідомлення з фото), відправляємо нове
            await callback.message.answer(
                f"❌ <b>Помилка публікації авто в групу</b>\n\n{str(e)}",
                parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("toggle_status_"))
async def toggle_vehicle_status(callback: CallbackQuery, state: FSMContext):
    """Зміна статусу авто (Наявне ↔ Продане)"""
    await callback.answer()
    
    try:
        # Отримуємо ID авто з callback_data
        vehicle_id = int(callback.data.replace("toggle_status_", ""))
        
        # Отримуємо авто з бази даних
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            await callback.answer("❌ Авто не знайдено", show_alert=True)
            return
        
        # Визначаємо новий статус
        current_status = vehicle.status.value if vehicle.status else "available"
        new_status = "sold" if current_status == "available" else "available"
        
        # Підготовлюємо дані для оновлення
        from datetime import datetime
        from app.modules.database.models import VehicleStatus
        update_data = {
            'status': VehicleStatus(new_status),
            'status_changed_at': datetime.now()
        }
        
        # Якщо змінюємо на "sold", зберігаємо дату продажу
        if new_status == "sold":
            update_data['sold_at'] = datetime.now()
        else:
            # Якщо змінюємо на "available", очищаємо дату продажу
            update_data['sold_at'] = None
        
        # Оновлюємо статус в БД
        success = await db_manager.update_vehicle(vehicle_id, update_data)
        
        if success:
            # Отримуємо оновлене авто
            updated_vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
            
            # Форматуємо картку авто
            detail_text, photo_file_id = format_admin_vehicle_card(updated_vehicle)
            
            # Оновлюємо повідомлення в залежності від типу
            if photo_file_id:
                # Якщо є медіа, редагуємо медіа повідомлення
                try:
                    from aiogram.types import InputMediaPhoto, InputMediaVideo
                    
                    # Визначаємо тип: фото чи відео (префікс video:)
                    is_video = isinstance(photo_file_id, str) and photo_file_id.startswith("video:")
                    file_id = photo_file_id.split(":", 1)[1] if is_video else photo_file_id
                    
                    # Створюємо медіа об'єкт з фото/відео та підписом
                    if is_video:
                        media = InputMediaVideo(
                            media=file_id,
                            caption=detail_text,
                            parse_mode="HTML"
                        )
                    else:
                        media = InputMediaPhoto(
                            media=file_id,
                            caption=detail_text,
                            parse_mode="HTML"
                        )
                    
                    await callback.message.bot.edit_message_media(
                        chat_id=callback.message.chat.id,
                        message_id=callback.message.message_id,
                        media=media,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, new_status, updated_vehicle.group_message_id)
                    )
                    logger.info(f"📷 Картка авто з медіа відредагована в повідомленні {callback.message.message_id}")
                except Exception as edit_error:
                    logger.error(f"❌ Помилка редагування медіа повідомлення: {edit_error}")
                    # Fallback - відправляємо нове повідомлення з медіа
                    if is_video:
                        await callback.message.answer_video(
                            video=file_id,
                            caption=detail_text,
                            reply_markup=get_vehicle_detail_keyboard(vehicle_id, new_status, updated_vehicle.group_message_id),
                            parse_mode="HTML"
                        )
                    else:
                        await callback.message.answer_photo(
                            photo=file_id,
                            caption=detail_text,
                            reply_markup=get_vehicle_detail_keyboard(vehicle_id, new_status, updated_vehicle.group_message_id),
                            parse_mode="HTML"
                        )
            else:
                # Якщо немає фото, редагуємо текст
                try:
                    await callback.message.edit_text(
                        detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, new_status, updated_vehicle.group_message_id),
                        parse_mode="HTML"
                    )
                except Exception:
                    # Якщо не можемо редагувати, відправляємо нове
                    await callback.message.answer(
                        detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, new_status, updated_vehicle.group_message_id),
                        parse_mode="HTML"
                    )
            
            from ..shared.translations import translate_field_value
            status_text = translate_field_value('status', new_status)
            logger.info(f"✅ Статус авто {vehicle_id} змінено на {status_text} користувачем {callback.from_user.id}")
            
        else:
            await callback.answer("❌ Помилка оновлення статусу", show_alert=True)
            
    except Exception as e:
        logger.error(f"❌ Помилка зміни статусу авто: {e}")
        await callback.answer("❌ Помилка зміни статусу", show_alert=True)


@router.callback_query(F.data.startswith("filter_status_"))
async def filter_vehicles_by_status(callback: CallbackQuery, state: FSMContext):
    """Фільтрація авто за статусом"""
    await callback.answer()
    
    try:
        # Отримуємо статус та сортування з callback_data
        # Формат: filter_status_available_created_at_desc
        data_part = callback.data.replace("filter_status_", "")
        
        # Знаходимо перше підкреслення для розділення статусу та сортування
        if "_" in data_part:
            parts = data_part.split("_", 1)  # Розбиваємо на 2 частини з початку
            if len(parts) == 2:
                status_filter = parts[0]  # available
                sort_by = parts[1]  # created_at_desc
            else:
                status_filter = data_part
                sort_by = "created_at_desc"
        else:
            # Fallback для старих callback_data
            status_filter = data_part
            sort_by = "created_at_desc"
        
        # Отримуємо поточні параметри з FSM state
        data = await state.get_data()
        current_page = data.get('vehicles_page', 1)
        
        # Отримуємо авто з фільтрацією за статусом
        if status_filter == "all":
            vehicles = await db_manager.get_vehicles(
                limit=10, 
                offset=(current_page - 1) * 10, 
                sort_by=sort_by
            )
            # Отримуємо статистику для загальної кількості
            stats = await get_vehicles_statistics()
            total_count = stats['total_vehicles']
        else:
            vehicles = await db_manager.get_vehicles_by_status(
                status=status_filter,
                page=current_page, 
                per_page=10, 
                sort_by=sort_by
            )
            total_count = await db_manager.get_vehicles_count_by_status(status_filter)
        
        total_pages = (total_count + 9) // 10  # Округлення вгору
        
        # Форматуємо текст з урахуванням статус фільтра та сортування
        from ..shared.translations import translate_field_value
        status_text = "Всі авто" if status_filter == "all" else translate_field_value('status', status_filter)
        
        stats_text = f"""📋 <b>Список авто - {status_text}</b>

📊 <b>Статистика:</b>
• 🚛 <b>Знайдено авто:</b> {total_count}
• 🏷️ <b>Марок:</b> {len(set(v.brand for v in vehicles if v.brand))}

🏭 <b>Топ марки:</b>
"""
        
        # Додаємо топ-5 марок з поточного списку
        brand_counts = {}
        for vehicle in vehicles:
            if vehicle.brand:
                brand_counts[vehicle.brand] = brand_counts.get(vehicle.brand, 0) + 1
        
        sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
        for i, (brand, count) in enumerate(sorted_brands[:5], 1):
            stats_text += f"{i}. <b>{brand}</b> - {count} авто\n"
        
        # Додаємо інформацію про сортування
        sort_names = {
            "created_at_desc": "📅 Дата (нові → старі)",
            "created_at_asc": "📅 Дата (старі → нові)",
            "price_desc": "💰 Ціна (висока → низька)",
            "price_asc": "💰 Ціна (низька → висока)",
        }
        
        sort_name = sort_names.get(sort_by, "Невідоме сортування")
        stats_text += f"\n🔄 <b>Сортування:</b> {sort_name}"
        stats_text += f"\n📄 <b>Сторінка {current_page} з {total_pages}</b>"
        
        # Оновлюємо повідомлення
        try:
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_vehicles_list_keyboard(
                    vehicles, 
                    current_page, 
                    total_pages, 
                    sort_by, 
                    status_filter
                ),
                parse_mode="HTML"
            )
        except Exception:
            # Якщо не можемо редагувати, відправляємо нове
            await callback.message.answer(
                stats_text,
                reply_markup=get_vehicles_list_keyboard(
                    vehicles, 
                    current_page, 
                    total_pages, 
                    sort_by, 
                    status_filter
                ),
                parse_mode="HTML"
            )
        
        # Зберігаємо поточний фільтр та сортування в FSM state
        await state.update_data(
            vehicles_status_filter=status_filter,
            vehicles_sort=sort_by,
            vehicles_page=current_page
        )
        
        logger.info(f"🔍 Фільтрація авто за статусом: {status_filter} з сортуванням {sort_by} користувачем {callback.from_user.id}")
        logger.debug(f"🔍 Callback data: {callback.data}, parsed: status_filter='{status_filter}', sort_by='{sort_by}'")
        
    except Exception as e:
        logger.error(f"❌ Помилка фільтрації авто за статусом: {e}")
        await callback.answer("❌ Помилка фільтрації", show_alert=True)




async def check_group_message_exists(bot, chat_id: str, message_id: int) -> bool:
    """Перевірити існування повідомлення в групі"""
    try:
        # Спочатку перевіряємо доступність групи
        await bot.get_chat(chat_id)
        await bot.get_chat_member(chat_id, bot.id)
        
        # Отримуємо авто з бази даних
        vehicle = await db_manager.get_vehicle_by_id_from_message_id(message_id)
        if not vehicle:
            logger.info(f"📱 Не знайдено авто для message_id {message_id}")
            return False
        
        # Використовуємо елегантний підхід - спробуємо отримати повідомлення
        # через forward_message в неіснуючий чат (це не створить повідомлення)
        try:
            # Спробуємо переслати повідомлення в неіснуючий чат
            # Це покаже чи існує повідомлення, але не створить його ніде
            await bot.forward_message(
                chat_id=-999999999,  # Неіснуючий чат
                from_chat_id=chat_id,
                message_id=message_id,
                disable_notification=True
            )
            
            logger.info(f"✅ Повідомлення {message_id} з авто #{vehicle.id} існує в групі")
            return True
            
        except Exception as forward_error:
            error_message = str(forward_error).lower()
            if any(phrase in error_message for phrase in [
                "message to get not found",
                "message not found", 
                "bad request: message to forward not found",
                "message to forward not found"
            ]):
                # Повідомлення дійсно не існує
                logger.info(f"📱 Повідомлення {message_id} з авто #{vehicle.id} не існує в групі")
                return False
            elif any(phrase in error_message for phrase in [
                "forbidden: bots can't send messages to bots",
                "bad request: chat not found"
            ]):
                # Це означає що повідомлення існує, але є обмеження на пересилання
                logger.info(f"✅ Повідомлення {message_id} з авто #{vehicle.id} існує в групі (обмеження на пересилання)")
                return True
            else:
                # Інша помилка - логуємо і вважаємо, що повідомлення існує
                logger.warning(f"⚠️ Помилка перевірки повідомлення {message_id}: {forward_error}")
                return True
        
    except Exception as e:
        error_message = str(e).lower()
        if any(phrase in error_message for phrase in [
            "not found", 
            "chat not found",
            "chat not accessible"
        ]):
            logger.info(f"📱 Група {chat_id} не існує або недоступна")
            return False
        else:
            logger.warning(f"⚠️ Помилка перевірки групи {chat_id}: {e}")
            return True




async def update_vehicle_card_after_status_change(callback: CallbackQuery, vehicle_id: int):
    """Оновити картку авто після зміни статусу публікації"""
    try:
        # Отримуємо оновлене авто з бази даних
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            logger.error(f"❌ Авто {vehicle_id} не знайдено після оновлення")
            return
        
        # Форматуємо картку авто
        detail_text, photo_file_id = format_admin_vehicle_card(vehicle)
        
        # Оновлюємо повідомлення в залежності від типу
        if photo_file_id:
            # Якщо є медіа, редагуємо медіа повідомлення
            try:
                from aiogram.types import InputMediaPhoto, InputMediaVideo
                
                # Визначаємо тип: фото чи відео (префікс video:)
                is_video = isinstance(photo_file_id, str) and photo_file_id.startswith("video:")
                file_id = photo_file_id.split(":", 1)[1] if is_video else photo_file_id
                
                # Створюємо медіа об'єкт з фото/відео та підписом
                if is_video:
                    media = InputMediaVideo(
                        media=file_id,
                        caption=detail_text,
                        parse_mode="HTML"
                    )
                else:
                    media = InputMediaPhoto(
                        media=file_id,
                        caption=detail_text,
                        parse_mode="HTML"
                    )
                
                await callback.message.bot.edit_message_media(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    media=media,
                    reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id)
                )
                logger.info(f"📷 Картка авто з медіа оновлена в повідомленні {callback.message.message_id}")
            except Exception as edit_error:
                logger.error(f"❌ Помилка редагування медіа повідомлення: {edit_error}")
                # Fallback - відправляємо нове повідомлення з медіа
                if is_video:
                    await callback.message.answer_video(
                        video=file_id,
                        caption=detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
                else:
                    await callback.message.answer_photo(
                        photo=file_id,
                        caption=detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
        else:
            # Якщо немає фото, редагуємо текст
            try:
                await callback.message.edit_text(
                    detail_text,
                    reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                    parse_mode="HTML"
                )
            except Exception:
                # Якщо не можемо редагувати, відправляємо нове
                await callback.message.answer(
                    detail_text,
                    reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                    parse_mode="HTML"
                )
        
        logger.info(f"🔄 Картка авто {vehicle_id} оновлена після зміни статусу публікації")
        
    except Exception as e:
        logger.error(f"❌ Помилка оновлення картки авто: {e}")


async def send_vehicle_card_message(callback: CallbackQuery, vehicle_id: int):
    """Відправити окреме повідомлення з карткою авто"""
    try:
        # Отримуємо авто з бази даних
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            await callback.message.answer(
                "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                parse_mode="HTML"
            )
            return
        
        # Форматуємо картку авто
        detail_text, photo_file_id = format_admin_vehicle_card(vehicle)
        
        # Відправляємо картку авто
        if photo_file_id:
            # Якщо є медіа, відправляємо медіа з підписом
            # Визначаємо тип: фото чи відео (префікс video:)
            is_video = isinstance(photo_file_id, str) and photo_file_id.startswith("video:")
            file_id = photo_file_id.split(":", 1)[1] if is_video else photo_file_id
            
            if is_video:
                try:
                    await callback.message.answer_video(
                        video=file_id,
                        caption=detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
                except Exception as video_error:
                    logger.warning(f"⚠️ Не вдалося відправити відео для авто {vehicle_id}: {video_error}")
                    # Якщо відео недійсне, відправляємо тільки текст
                    await callback.message.answer(
                        detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
            else:
                try:
                    await callback.message.answer_photo(
                        photo=file_id,
                        caption=detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
                except Exception as photo_error:
                    logger.warning(f"⚠️ Не вдалося відправити фото для авто {vehicle_id}: {photo_error}")
                    # Якщо фото недійсне, відправляємо тільки текст
                    await callback.message.answer(
                        detail_text,
                        reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                        parse_mode="HTML"
                    )
        else:
            # Якщо немає фото, відправляємо тільки текст
            await callback.message.answer(
                detail_text,
                reply_markup=get_vehicle_detail_keyboard(vehicle_id, vehicle.status.value if vehicle.status else "available", vehicle.group_message_id),
                parse_mode="HTML"
            )
        
        logger.info(f"📋 Картка авто ID {vehicle_id} відправлена користувачу {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка відправки картки авто: {e}")
        await callback.message.answer(
            "❌ <b>Помилка відображення картки авто</b>\n\nСпробуйте ще раз.",
            parse_mode="HTML"
        )
