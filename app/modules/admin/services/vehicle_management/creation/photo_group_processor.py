"""
Професійний обробник медіагруп для створення авто
"""
import asyncio
import logging
from typing import Dict, List, Set
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from .states import VehicleCreationStates
from .keyboards import get_photos_input_keyboard, get_photos_summary_keyboard, get_additional_photos_keyboard
from app.utils.formatting import get_default_parse_mode

logger = logging.getLogger(__name__)

# Глобальний словник для зберігання медіагруп
media_groups: Dict[str, Dict] = {}

# Множина для відстеження оброблених медіагруп
processed_groups: Set[str] = set()


async def process_media_group_photos(
    message: Message, 
    state: FSMContext
) -> bool:
    """
    Обробити фото з медіагрупи
    
    Args:
        message: Повідомлення з фото
        state: FSM контекст
        
    Returns:
        bool: True якщо фото оброблено як медіагрупа
    """
    try:
        # Перевіряємо, чи є media_group_id
        if not hasattr(message, 'media_group_id') or not message.media_group_id:
            return False

        # КРИТИЧНО: Перевіряємо, чи користувач знаходиться в стані створення авто
        current_state = await state.get_state()
        if not current_state or not current_state.startswith('VehicleCreationStates'):
            logger.info(f"📷 process_media_group_photos: користувач не в стані створення авто (стан: {current_state}), пропускаємо")
            return False

        media_group_id = message.media_group_id
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        logger.info(f"📷 process_media_group_photos: обробляємо медіагрупу {media_group_id} для користувача {user_id} в стані {current_state}")

        # Якщо це перше фото з групи
        if media_group_id not in media_groups:
            logger.info(f"📷 process_media_group_photos: створюємо нову групу {media_group_id}")
            media_groups[media_group_id] = {
                'photos': [],
                'processed_count': 0,
                'user_id': user_id,
                'chat_id': chat_id,
                'state': state,
                'last_message_id': None,
                'bot': message.bot
            }

            # Запускаємо таймер для обробки групи (2.5 секунди)
            asyncio.create_task(
                process_group_after_delay(media_group_id, 2.5)
            )

        # Telegram обмежує медіагрупи до 10 елементів
        MAX_MEDIA_GROUP_SIZE = 10
        
        # Перевіряємо, чи не перевищено ліміт
        current_count = len(media_groups[media_group_id]['photos'])
        if current_count >= MAX_MEDIA_GROUP_SIZE:
            logger.warning(f"⚠️ Медіагрупа {media_group_id} вже містить {current_count} фото (ліміт {MAX_MEDIA_GROUP_SIZE}), ігноруємо додаткові")
            return True  # Повертаємо True, щоб не обробляти як одиночне фото
        
        # Додаємо фото до групи
        if message.photo:
            photo = max(message.photo, key=lambda p: p.file_size)
            media_groups[media_group_id]['photos'].append(photo.file_id)
        elif message.video:
            media_groups[media_group_id]['photos'].append(f"video:{message.video.file_id}")
        media_groups[media_group_id]['processed_count'] += 1

        logger.info(f"📷 process_media_group_photos: додано фото {media_groups[media_group_id]['processed_count']} до групи {media_group_id} (всього: {len(media_groups[media_group_id]['photos'])})")

        return True

    except Exception as e:
        logger.error(f"❌ process_media_group_photos: помилка: {e}", exc_info=True)
        return False


async def process_group_after_delay(media_group_id: str, delay: float):
    """
    Обробити групу фото після затримки
    
    Args:
        media_group_id: ID медіагрупи
        delay: Затримка в секундах
    """
    try:
        # Затримка
        await asyncio.sleep(delay)
        
        # Перевіряємо, чи група ще існує
        if media_group_id not in media_groups:
            logger.warning(f"📷 process_group_after_delay: група {media_group_id} не знайдена")
            return
            
        # Перевіряємо, чи група вже оброблена
        if media_group_id in processed_groups:
            logger.warning(f"📷 process_group_after_delay: група {media_group_id} вже оброблена")
            return

        group_data = media_groups[media_group_id]
        photos = group_data['photos']
        state = group_data['state']
        bot = group_data['bot']
        chat_id = group_data['chat_id']
        user_id = group_data['user_id']

        logger.info(f"📷 process_group_after_delay: обробляємо групу {media_group_id} з {len(photos)} фото")

        # Позначаємо групу як оброблену
        processed_groups.add(media_group_id)

        # Отримуємо поточні фото зі стану
        current_data = await state.get_data()
        existing_photos = current_data.get('group_photos', [])

        # Telegram обмежує медіагрупи до 10 елементів
        MAX_MEDIA_GROUP_SIZE = 10
        
        # Обмежуємо нові фото до ліміту
        if len(photos) > MAX_MEDIA_GROUP_SIZE:
            logger.warning(f"⚠️ Медіагрупа містить {len(photos)} фото, обмежуємо до {MAX_MEDIA_GROUP_SIZE}")
            photos = photos[:MAX_MEDIA_GROUP_SIZE]

        # Додаємо всі фото з групи (для публікації в групу Telegram)
        all_photos = existing_photos + photos
        
        # Перевіряємо загальний ліміт
        if len(all_photos) > MAX_MEDIA_GROUP_SIZE:
            logger.warning(f"⚠️ Загальна кількість фото ({len(all_photos)}) перевищує ліміт, обмежуємо до {MAX_MEDIA_GROUP_SIZE}")
            all_photos = all_photos[:MAX_MEDIA_GROUP_SIZE]
        
        await state.update_data(group_photos=all_photos)
        
        logger.info(f"📷 process_group_after_delay: існуючі фото: {len(existing_photos)}, нові фото: {len(photos)}, всього: {len(all_photos)}")

        # Визначаємо поточний стан для вибору клавіатури
        current_state = await state.get_state()
        
        logger.info(f"📷 process_group_after_delay: поточний стан: {current_state}")
        logger.info(f"📷 process_group_after_delay: існуючі фото: {len(existing_photos)}, нові фото: {len(photos)}, всього: {len(all_photos)}")
        
        # Показуємо оновлену інформацію
        count = len(all_photos)
        
        # Визначаємо текст залежно від стану
        if current_state in [VehicleCreationStates.waiting_for_group_photos, VehicleCreationStates.waiting_for_additional_group_photos]:
            # Стан створення авто
            text = f"""
🚛 <b>Створення картки авто</b>

<b>Крок 21 з 21:</b> Медіа для публікації в групу

✅ Завантажено медіа: {count}
📸/🎥 Можете додати ще фото/відео або завершити створення картки

Завантажте ще медіа або натисніть "Завершити":
"""
        else:
            # Стан редагування - повертаємося до меню редагування
            text = f"""
📷 <b>Медіа оновлено</b>

✅ Завантажено медіа: {count}
📸/🎥 Медіа успішно додано до картки авто

Повертаємося до меню редагування...
"""

        # Визначаємо клавіатуру залежно від стану
        if current_state == VehicleCreationStates.waiting_for_group_photos:
            # Перше завантаження фото - переходимо до стану підсумку
            await state.set_state(VehicleCreationStates.waiting_for_additional_group_photos)
            keyboard = get_photos_summary_keyboard(count)
        elif current_state == VehicleCreationStates.waiting_for_additional_group_photos:
            # Додаткові фото - залишаємося в тому ж стані
            keyboard = get_photos_summary_keyboard(count)
        else:
            # Перевіряємо, чи це стан редагування
            from ..editing.states import VehicleEditingStates
            
            if current_state in [VehicleEditingStates.waiting_for_add_photos, VehicleEditingStates.waiting_for_replace_photos]:
                # Стан редагування фото - повертаємося до меню редагування
                logger.info(f"📷 process_group_after_delay: стан редагування фото, повертаємося до меню редагування")
                try:
                    # Отримуємо дані з FSM для показу меню редагування
                    data = await state.get_data()
                    
                    # Створюємо текст меню редагування
                    from ..editing.keyboards import get_editing_menu_keyboard
                    from ..shared.translations import translate_field_value
                    
                    # Формуємо текст меню
                    menu_text = "🔧 <b>Редагування картки авто</b>\n\n"
                    menu_text += "Оберіть поле для редагування:\n\n"
                    
                    # Додаємо поля для редагування
                    fields = [
                        ("vehicle_type", "Тип авто"),
                        ("brand", "Марка"),
                        ("model", "Модель"),
                        ("vin_code", "VIN код"),
                        ("body_type", "Тип кузова"),
                        ("year", "Рік випуску"),
                        ("condition", "Стан"),
                        ("price", "Вартість"),
                        ("mileage", "Пробіг"),
                        ("fuel_type", "Тип палива"),
                        ("engine_volume", "Об'єм двигуна"),
                        ("power_hp", "Потужність"),
                        ("transmission", "Коробка передач"),
                        ("wheel_radius", "Радіус коліс"),
                        ("load_capacity", "Вантажопідйомність"),
                        ("total_weight", "Загальна маса"),
                        ("cargo_dimensions", "Габарити"),
                        ("location", "Місцезнаходження"),
                        ("description", "Опис"),
                        ("photos", "Фото")
                    ]
                    
                    for field_key, field_name in fields:
                        value = data.get(field_key, 'Не вказано')
                        if value and value != 'Не вказано':
                            if field_key in ["vehicle_type", "condition", "fuel_type", "transmission", "location"]:
                                value = translate_field_value(field_key, str(value))
                            menu_text += f"✅ <b>{field_name}:</b> {value}\n"
                    
                    # Додаємо інформацію про зміни
                    changes = data.get('editing_changes', {})
                    if changes:
                        menu_text += "\n✅ <b>Внесені зміни:</b>\n"
                        for field, (old_val, new_val) in changes.items():
                            field_names = {
                                "vehicle_type": "Тип авто", "brand": "Марка", "model": "Модель",
                                "vin_code": "VIN код", "body_type": "Тип кузова", "year": "Рік випуску",
                                "condition": "Стан", "price": "Вартість", "mileage": "Пробіг",
                                "fuel_type": "Тип палива", "engine_volume": "Об'єм двигуна", "power_hp": "Потужність",
                                "transmission": "Коробка передач", "wheel_radius": "Радіус коліс", "load_capacity": "Вантажопідйомність",
                                "total_weight": "Загальна маса", "cargo_dimensions": "Габарити", "location": "Місцезнаходження",
                                "description": "Опис", "photos": "Фото"
                            }
                            field_display_name = field_names.get(field, field)
                            menu_text += f"• {field_display_name}: {old_val} → {new_val}\n"
                    
                    # Отримуємо клавіатуру
                    keyboard = get_editing_menu_keyboard(data)
                    
                    # Відправляємо повідомлення з меню редагування
                    await bot.send_message(
                        chat_id=chat_id,
                        text=menu_text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    
                    # Встановлюємо стан меню редагування
                    from ..editing.states import VehicleEditingStates
                    await state.set_state(VehicleEditingStates.editing_menu)
                    
                    return
                except Exception as e:
                    logger.error(f"❌ process_group_after_delay: помилка повернення до меню редагування: {e}")
                    # Fallback - відправляємо просте повідомлення
                    await bot.send_message(chat_id, f"📷 Фото оновлено! Кількість: {count}")
                    return
            else:
                # Fallback - використовуємо стару логіку
                keyboard = get_photos_input_keyboard()

        # Відправляємо повідомлення з ГОЛОВНИМ фото як прев'ю
        main_photo = (await state.get_data()).get('main_photo')
        preview_photo = main_photo or (all_photos[0] if all_photos else None)
        
        if preview_photo:
            # Визначаємо тип: фото чи відео (префікс video:)
            is_video = isinstance(preview_photo, str) and preview_photo.startswith("video:")
            file_id = preview_photo.split(":", 1)[1] if is_video else preview_photo
            
            if is_video:
                new_message = await bot.send_video(
                    chat_id=chat_id,
                    video=file_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=get_default_parse_mode()
                )
            else:
                new_message = await bot.send_photo(
                    chat_id=chat_id,
                    photo=file_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=get_default_parse_mode()
                )
        else:
            # Якщо немає фото, відправляємо тільки текст
            new_message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode()
            )
        
        # Зберігаємо ID залежно від стану
        if current_state == VehicleCreationStates.waiting_for_group_photos:
            await state.update_data(last_group_photos_message_id=new_message.message_id)
        elif current_state == VehicleCreationStates.waiting_for_additional_group_photos:
            await state.update_data(last_additional_group_photos_message_id=new_message.message_id)
        
        logger.info(f"📷 process_group_after_delay: створено нове повідомлення {new_message.message_id} для групи {media_group_id}")

        # Очищаємо дані групи
        del media_groups[media_group_id]
        
        # Видаляємо з оброблених через 5 хвилин (очищення пам'яті)
        asyncio.create_task(cleanup_processed_group(media_group_id, 300))

    except Exception as e:
        logger.error(f"❌ process_group_after_delay: помилка обробки групи {media_group_id}: {e}", exc_info=True)
        # Очищаємо дані групи навіть при помилці
        if media_group_id in media_groups:
            del media_groups[media_group_id]


async def cleanup_processed_group(media_group_id: str, delay: float):
    """
    Очистити оброблену групу з пам'яті
    
    Args:
        media_group_id: ID медіагрупи
        delay: Затримка в секундах
    """
    try:
        await asyncio.sleep(delay)
        processed_groups.discard(media_group_id)
        logger.debug(f"📷 cleanup_processed_group: очищено групу {media_group_id}")
    except Exception as e:
        logger.error(f"❌ cleanup_processed_group: помилка очищення групи {media_group_id}: {e}")


def cleanup_media_groups():
    """Очистити всі медіагрупи (для тестування)"""
    global media_groups, processed_groups
    media_groups.clear()
    processed_groups.clear()
    logger.info("📷 cleanup_media_groups: всі медіагрупи очищено")
