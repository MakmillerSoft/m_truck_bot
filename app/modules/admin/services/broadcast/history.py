"""
Історія розсилок (адмін)
Перегляд, пагінація, фільтрація та сортування розсилок
"""
import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.modules.admin.core.access_control import AdminAccessFilter
from app.utils.formatting import get_default_parse_mode
from app.modules.database.manager import db_manager
from app.config.settings import settings
from .formatters import format_broadcast_list_header, format_broadcast_card
from .keyboards import get_broadcasts_list_keyboard, get_broadcast_detail_keyboard

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast_history")
router.message.filter(AdminAccessFilter())
router.callback_query.filter(AdminAccessFilter())


@router.callback_query(F.data.startswith("broadcasts_page_"))
async def navigate_broadcasts_page(callback: CallbackQuery, state: FSMContext):
    """Навігація по сторінках розсилок"""
    await callback.answer()
    
    try:
        # Отримуємо номер сторінки з callback_data
        page = int(callback.data.replace("broadcasts_page_", ""))
        
        # Отримуємо дані з стану
        state_data = await state.get_data()
        total_pages = state_data.get('total_pages', 1)
        sort_by = state_data.get('broadcasts_sort', 'created_at_desc')
        status_filter = state_data.get('broadcasts_status_filter', 'all')
        
        # Перевіряємо валідність сторінки
        if page < 1 or page > total_pages:
            await callback.answer("❌ Недійсна сторінка", show_alert=True)
            return
        
        # Отримуємо розсилки для поточної сторінки
        offset = (page - 1) * settings.page_size
        broadcasts = await db_manager.list_broadcasts(limit=settings.page_size, offset=offset, sort_by=sort_by, status_filter=status_filter)
        
        # Отримуємо статистику
        stats = await db_manager.get_broadcasts_statistics()
        
        # Форматуємо заголовок
        header_text = format_broadcast_list_header(
            total_broadcasts=stats['total_broadcasts'],
            sent_broadcasts=stats['sent_broadcasts'],
            draft_broadcasts=stats['draft_broadcasts'],
            current_page=page,
            total_pages=total_pages,
            status_filter=status_filter
        )
        
        # Оновлюємо повідомлення
        await callback.message.edit_text(
            header_text,
            reply_markup=get_broadcasts_list_keyboard(broadcasts, current_page=page, total_pages=total_pages, sort_by=sort_by, status_filter=status_filter),
            parse_mode=get_default_parse_mode(),
        )
        
        # Оновлюємо поточну сторінку в стані
        await state.update_data(broadcasts_page=page)
        
        logger.info(f"📄 Перехід на сторінку {page} розсилок для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка навігації по сторінках розсилок: {e}", exc_info=True)
        await callback.answer("❌ Помилка навігації", show_alert=True)


@router.callback_query(F.data.startswith("sort_broadcasts_"))
async def sort_broadcasts(callback: CallbackQuery, state: FSMContext):
    """Змінити сортування розсилок"""
    await callback.answer()
    
    try:
        # Отримуємо тип сортування та статус фільтр з callback_data
        data_part = callback.data.replace("sort_broadcasts_", "")
        
        # Знаходимо останній підкреслення для розділення сортування та статусу
        if "_" in data_part:
            parts = data_part.rsplit("_", 1)
            if len(parts) == 2:
                sort_type = parts[0]
                status_filter = parts[1]
            else:
                sort_type = data_part
                status_filter = "all"
        else:
            sort_type = data_part
            status_filter = "all"
        
        # Отримуємо дані з стану
        state_data = await state.get_data()
        current_page = state_data.get('broadcasts_page', 1)
        
        # Отримуємо розсилки з урахуванням статус фільтра та сортування
        broadcasts = await db_manager.list_broadcasts(
            limit=settings.page_size, 
            offset=(current_page - 1) * settings.page_size, 
            sort_by=sort_type,
            status_filter=status_filter
        )
        
        total_count = await db_manager.get_broadcasts_count(status_filter)
        total_pages = (total_count + settings.page_size - 1) // settings.page_size if total_count > 0 else 1
        
        # Отримуємо статистику
        stats = await db_manager.get_broadcasts_statistics()
        
        # Форматуємо заголовок
        header_text = format_broadcast_list_header(
            total_broadcasts=stats['total_broadcasts'],
            sent_broadcasts=stats['sent_broadcasts'],
            draft_broadcasts=stats['draft_broadcasts'],
            current_page=current_page,
            total_pages=total_pages,
            status_filter=status_filter
        )
        
        # Оновлюємо повідомлення
        await callback.message.edit_text(
            header_text,
            reply_markup=get_broadcasts_list_keyboard(broadcasts, current_page=current_page, total_pages=total_pages, sort_by=sort_type, status_filter=status_filter),
            parse_mode=get_default_parse_mode(),
        )
        
        # Оновлюємо сортування в стані
        await state.update_data(broadcasts_sort=sort_type, broadcasts_status_filter=status_filter, total_pages=total_pages)
        
        logger.info(f"🔄 Змінено сортування розсилок на {sort_type} для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка зміни сортування розсилок: {e}", exc_info=True)
        await callback.answer("❌ Помилка зміни сортування", show_alert=True)


@router.callback_query(F.data.startswith("filter_broadcasts_status_"))
async def filter_broadcasts_by_status(callback: CallbackQuery, state: FSMContext):
    """Фільтрація розсилок за статусом"""
    await callback.answer()
    
    try:
        # Отримуємо статус та сортування з callback_data
        data_part = callback.data.replace("filter_broadcasts_status_", "")
        
        # Знаходимо перше підкреслення для розділення статусу та сортування
        if "_" in data_part:
            parts = data_part.split("_", 1)
            if len(parts) == 2:
                status_filter = parts[0]
                sort_by = parts[1]
            else:
                status_filter = data_part
                sort_by = "created_at_desc"
        else:
            status_filter = data_part
            sort_by = "created_at_desc"
        
        # Отримуємо дані з стану
        state_data = await state.get_data()
        current_page = 1  # Повертаємося на першу сторінку при зміні фільтра
        
        # Отримуємо розсилки з фільтрацією за статусом
        broadcasts = await db_manager.list_broadcasts(
            limit=settings.page_size, 
            offset=0, 
            sort_by=sort_by,
            status_filter=status_filter
        )
        
        total_count = await db_manager.get_broadcasts_count(status_filter)
        total_pages = (total_count + settings.page_size - 1) // settings.page_size if total_count > 0 else 1
        
        # Отримуємо статистику
        stats = await db_manager.get_broadcasts_statistics()
        
        # Форматуємо заголовок
        header_text = format_broadcast_list_header(
            total_broadcasts=stats['total_broadcasts'],
            sent_broadcasts=stats['sent_broadcasts'],
            draft_broadcasts=stats['draft_broadcasts'],
            current_page=current_page,
            total_pages=total_pages,
            status_filter=status_filter
        )
        
        if not broadcasts:
            header_text += "\n\n❌ <b>Розсилки не знайдені</b>"
        
        # Оновлюємо повідомлення
        await callback.message.edit_text(
            header_text,
            reply_markup=get_broadcasts_list_keyboard(broadcasts, current_page=current_page, total_pages=total_pages, sort_by=sort_by, status_filter=status_filter),
            parse_mode=get_default_parse_mode(),
        )
        
        # Оновлюємо фільтр в стані
        await state.update_data(broadcasts_page=current_page, broadcasts_sort=sort_by, broadcasts_status_filter=status_filter, total_pages=total_pages)
        
        logger.info(f"🔍 Змінено фільтр розсилок на {status_filter} для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка фільтрації розсилок: {e}", exc_info=True)
        await callback.answer("❌ Помилка фільтрації", show_alert=True)


@router.callback_query(F.data.startswith("view_broadcast_"))
async def view_broadcast_detail(callback: CallbackQuery, state: FSMContext):
    """Детальний перегляд розсилки"""
    await callback.answer()
    
    try:
        # Отримуємо ID розсилки
        broadcast_id = int(callback.data.replace("view_broadcast_", ""))
        
        # Отримуємо розсилку з БД
        broadcast = await db_manager.get_broadcast_by_id(broadcast_id)
        
        if not broadcast:
            await callback.answer("❌ Розсилка не знайдена", show_alert=True)
            return
        
        # Форматуємо картку
        card_text = format_broadcast_card(broadcast)
        
        # Відправляємо повідомлення
        await callback.message.edit_text(
            card_text,
            reply_markup=get_broadcast_detail_keyboard(broadcast_id),
            parse_mode=get_default_parse_mode(),
        )
        
        # Зберігаємо ID розсилки в стані для повернення
        await state.update_data(viewing_broadcast_id=broadcast_id)
        
        logger.info(f"👁️ Перегляд розсилки {broadcast_id} для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка перегляду розсилки: {e}", exc_info=True)
        await callback.answer("❌ Помилка перегляду", show_alert=True)


@router.callback_query(F.data == "back_to_broadcasts_list")
async def back_to_broadcasts_list(callback: CallbackQuery, state: FSMContext):
    """Повернення до списку розсилок"""
    await callback.answer()
    
    try:
        # Отримуємо дані з стану
        state_data = await state.get_data()
        current_page = state_data.get('broadcasts_page', 1)
        sort_by = state_data.get('broadcasts_sort', 'created_at_desc')
        status_filter = state_data.get('broadcasts_status_filter', 'all')
        total_pages = state_data.get('total_pages', 1)
        
        # Отримуємо розсилки
        offset = (current_page - 1) * settings.page_size
        broadcasts = await db_manager.list_broadcasts(limit=settings.page_size, offset=offset, sort_by=sort_by, status_filter=status_filter)
        
        # Отримуємо статистику
        stats = await db_manager.get_broadcasts_statistics()
        
        # Форматуємо заголовок
        header_text = format_broadcast_list_header(
            total_broadcasts=stats['total_broadcasts'],
            sent_broadcasts=stats['sent_broadcasts'],
            draft_broadcasts=stats['draft_broadcasts'],
            current_page=current_page,
            total_pages=total_pages,
            status_filter=status_filter
        )
        
        if not broadcasts:
            header_text += "\n\n❌ <b>Розсилки не знайдені</b>"
        
        # Оновлюємо повідомлення
        await callback.message.edit_text(
            header_text,
            reply_markup=get_broadcasts_list_keyboard(broadcasts, current_page=current_page, total_pages=total_pages, sort_by=sort_by, status_filter=status_filter),
            parse_mode=get_default_parse_mode(),
        )
        
        logger.info(f"🔙 Повернення до списку розсилок для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка повернення до списку розсилок: {e}", exc_info=True)
        await callback.answer("❌ Помилка", show_alert=True)


