"""
Обробники для видалення авто
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.modules.admin.core.access_control import AdminAccessFilter
from app.modules.admin.shared.utils.callback_utils import safe_callback_answer
from app.modules.database.manager import DatabaseManager
from app.config.settings import settings
from .keyboards import (
    get_deletion_confirmation_keyboard,
    get_deletion_success_keyboard,
    get_deletion_cancelled_keyboard
)
from ..listing.formatters import format_admin_vehicle_card

logger = logging.getLogger(__name__)
router = Router()

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())

# Ініціалізуємо менеджер бази даних
db_manager = DatabaseManager()


@router.callback_query(F.data.startswith("delete_vehicle_"))
async def confirm_vehicle_deletion(callback: CallbackQuery, state: FSMContext):
    """Підтвердження видалення авто"""
    await safe_callback_answer(callback)
    
    try:
        # Отримуємо ID авто з callback_data
        vehicle_id = int(callback.data.replace("delete_vehicle_", ""))
        
        # Отримуємо авто з бази даних
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            try:
                await callback.message.edit_text(
                    "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.answer(
                    "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                    parse_mode="HTML"
                )
            return
        
        # Форматуємо картку авто для показу
        detail_text, photo_file_id = format_admin_vehicle_card(vehicle)
        
        # Додаємо попередження про видалення
        warning_text = f"""⚠️ <b>ПІДТВЕРДЖЕННЯ ВИДАЛЕННЯ</b>

{detail_text}

🚨 <b>УВАГА!</b> Ви дійсно хочете видалити це авто?

<b>Ця дія є незворотною!</b>
• Авто буде повністю видалено з бази даних
• Всі фото будуть втрачені
• Відновити дані буде неможливо

<b>Оберіть дію:</b>"""
        
        # Відправляємо попередження з фото або без
        if photo_file_id:
            try:
                await callback.message.answer_photo(
                    photo=photo_file_id,
                    caption=warning_text,
                    reply_markup=get_deletion_confirmation_keyboard(vehicle_id),
                    parse_mode="HTML"
                )
            except Exception as photo_error:
                logger.warning(f"⚠️ Не вдалося відправити фото для авто {vehicle_id}: {photo_error}")
                # Якщо фото недійсне, відправляємо тільки текст
                await callback.message.answer(
                    warning_text,
                    reply_markup=get_deletion_confirmation_keyboard(vehicle_id),
                    parse_mode="HTML"
                )
        else:
            try:
                await callback.message.edit_text(
                    warning_text,
                    reply_markup=get_deletion_confirmation_keyboard(vehicle_id),
                    parse_mode="HTML"
                )
            except Exception as edit_error:
                # Якщо не можемо редагувати (повідомлення з медіа), відправляємо нове
                await callback.message.answer(
                    warning_text,
                    reply_markup=get_deletion_confirmation_keyboard(vehicle_id),
                    parse_mode="HTML"
                )
        
        # Зберігаємо ID авто в стані для подальшого використання
        await state.update_data(vehicle_to_delete_id=vehicle_id)
        
        logger.info(f"⚠️ Підтвердження видалення авто ID {vehicle_id} для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка підтвердження видалення: {e}")
        try:
            await callback.message.edit_text(
                f"❌ <b>Помилка підтвердження видалення</b>\n\n{str(e)}",
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.answer(
                f"❌ <b>Помилка підтвердження видалення</b>\n\n{str(e)}",
                parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("confirm_delete_vehicle_"))
async def delete_vehicle(callback: CallbackQuery, state: FSMContext):
    """Видалити авто"""
    await safe_callback_answer(callback)
    
    try:
        # Отримуємо ID авто з callback_data
        vehicle_id = int(callback.data.replace("confirm_delete_vehicle_", ""))
        
        # Отримуємо дані з стану
        state_data = await state.get_data()
        stored_vehicle_id = state_data.get('vehicle_to_delete_id')
        
        # Перевіряємо чи ID співпадають
        if vehicle_id != stored_vehicle_id:
            try:
                await callback.message.edit_text(
                    "❌ <b>Помилка безпеки</b>\n\nID авто не співпадають. Операція скасована.",
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.answer(
                    "❌ <b>Помилка безпеки</b>\n\nID авто не співпадають. Операція скасована.",
                    parse_mode="HTML"
                )
            return
        
        # Отримуємо авто перед видаленням для логування
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            try:
                await callback.message.edit_text(
                    "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.answer(
                    "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                    parse_mode="HTML"
                )
            return
        
        # Видаляємо авто з бази даних
        success = await db_manager.delete_vehicle(vehicle_id)
        
        if success:
            # Форматуємо повідомлення про успішне видалення
            price_text = f"{vehicle.price:,.0f} $" if vehicle.price is not None else "Не вказана"
            success_text = f"""✅ <b>АВТО УСПІШНО ВИДАЛЕНО</b>

🚛 <b>Видалено авто:</b> {vehicle.brand or 'Без марки'} {vehicle.model or 'Без моделі'}
📅 <b>Рік:</b> {vehicle.year or 'Не вказано'}
💰 <b>Ціна:</b> {price_text}

🗑️ <b>Видалено:</b>
• Авто з бази даних
• {len(vehicle.photos) if vehicle.photos else 0} фото
• Всі пов'язані дані

<b>Операція завершена успішно!</b>"""
            
            try:
                await callback.message.edit_text(
                    success_text,
                    reply_markup=get_deletion_success_keyboard(),
                    parse_mode="HTML"
                )
            except Exception as edit_error:
                # Якщо не можемо редагувати (наприклад, повідомлення з фото), відправляємо нове
                await callback.message.answer(
                    success_text,
                    reply_markup=get_deletion_success_keyboard(),
                    parse_mode="HTML"
                )
            
            # Очищуємо дані з стану
            await state.update_data(vehicle_to_delete_id=None)
            
            logger.info(f"✅ Авто ID {vehicle_id} успішно видалено користувачем {callback.from_user.id}")
            
        else:
            try:
                await callback.message.edit_text(
                    "❌ <b>Помилка видалення</b>\n\nНе вдалося видалити авто з бази даних. Спробуйте ще раз.",
                    parse_mode="HTML"
                )
            except Exception as edit_error:
                # Якщо не можемо редагувати, відправляємо нове повідомлення
                await callback.message.answer(
                    "❌ <b>Помилка видалення</b>\n\nНе вдалося видалити авто з бази даних. Спробуйте ще раз.",
                    parse_mode="HTML"
                )
            
            logger.error(f"❌ Помилка видалення авто ID {vehicle_id} для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка видалення авто: {e}")
        try:
            await callback.message.edit_text(
                f"❌ <b>Помилка видалення авто</b>\n\n{str(e)}",
                parse_mode="HTML"
            )
        except Exception as edit_error:
            # Якщо не можемо редагувати, відправляємо нове повідомлення
            await callback.message.answer(
                f"❌ <b>Помилка видалення авто</b>\n\n{str(e)}",
                parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("cancel_delete_vehicle_"))
async def cancel_vehicle_deletion(callback: CallbackQuery, state: FSMContext):
    """Скасувати видалення авто"""
    await safe_callback_answer(callback)
    
    try:
        # Отримуємо ID авто з callback_data
        vehicle_id = int(callback.data.replace("cancel_delete_vehicle_", ""))
        
        # Отримуємо авто з бази даних
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            try:
                await callback.message.edit_text(
                    "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.answer(
                    "❌ <b>Помилка</b>\n\nАвто не знайдено в базі даних.",
                    parse_mode="HTML"
                )
            return
        
        # Форматуємо картку авто
        detail_text, photo_file_id = format_admin_vehicle_card(vehicle)
        
        # Додаємо повідомлення про скасування
        cancelled_text = f"""✅ <b>ВИДАЛЕННЯ СКАСОВАНО</b>

{detail_text}

<b>Авто залишається в базі даних.</b>
Ви можете продовжити роботу з цим авто."""
        
        # Відправляємо повідомлення про скасування
        if photo_file_id:
            try:
                await callback.message.answer_photo(
                    photo=photo_file_id,
                    caption=cancelled_text,
                    reply_markup=get_deletion_cancelled_keyboard(vehicle_id),
                    parse_mode="HTML"
                )
            except Exception as photo_error:
                logger.warning(f"⚠️ Не вдалося відправити фото для авто {vehicle_id}: {photo_error}")
                # Якщо фото недійсне, відправляємо тільки текст
                await callback.message.answer(
                    cancelled_text,
                    reply_markup=get_deletion_cancelled_keyboard(vehicle_id),
                    parse_mode="HTML"
                )
        else:
            try:
                await callback.message.edit_text(
                    cancelled_text,
                    reply_markup=get_deletion_cancelled_keyboard(vehicle_id),
                    parse_mode="HTML"
                )
            except Exception as edit_error:
                # Якщо не можемо редагувати (повідомлення з медіа), відправляємо нове повідомлення
                await callback.message.answer(
                    cancelled_text,
                    reply_markup=get_deletion_cancelled_keyboard(vehicle_id),
                    parse_mode="HTML"
                )
        
        # Очищуємо дані з стану
        await state.update_data(vehicle_to_delete_id=None)
        
        logger.info(f"✅ Видалення авто ID {vehicle_id} скасовано користувачем {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка скасування видалення: {e}")
        try:
            await callback.message.edit_text(
                f"❌ <b>Помилка скасування видалення</b>\n\n{str(e)}",
                parse_mode="HTML"
            )
        except Exception as edit_error:
            # Якщо не можемо редагувати, відправляємо нове повідомлення
            await callback.message.answer(
                f"❌ <b>Помилка скасування видалення</b>\n\n{str(e)}",
                parse_mode="HTML"
            )


@router.callback_query(F.data == "back_to_vehicles_after_deletion")
async def back_to_vehicles_after_deletion(callback: CallbackQuery, state: FSMContext):
    """Повернутися до списку авто після видалення"""
    await safe_callback_answer(callback)
    
    try:
        # Отримуємо дані пагінації з стану
        state_data = await state.get_data()
        current_page = state_data.get('current_page', 1)
        sort_by = state_data.get('sort_by', 'created_at_asc')
        
        # Якщо дані пагінації відсутні, скидаємо до першої сторінки
        if not state_data.get('total_pages'):
            logger.warning(f"⚠️ Дані пагінації відсутні, скидаємо до першої сторінки")
            current_page = 1
        
        # Отримуємо авто для поточної сторінки
        offset = (current_page - 1) * settings.page_size
        vehicles = await db_manager.get_vehicles(limit=settings.page_size, offset=offset, sort_by=sort_by)
        
        # Отримуємо статистику
        from ..listing.handlers import get_vehicles_statistics
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
        
        # Відправляємо повідомлення
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
        
        logger.info(f"🔙 Повернення до списку авто після видалення на сторінку {current_page}")
        
    except Exception as e:
        logger.error(f"❌ Помилка повернення до списку після видалення: {e}")
        await safe_callback_answer(callback, "❌ Помилка повернення", show_alert=True)


# Імпортуємо функцію для клавіатури списку авто
from ..listing.keyboards import get_vehicles_list_keyboard
