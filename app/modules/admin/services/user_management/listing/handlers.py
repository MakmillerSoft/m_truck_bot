"""
Обробники для блоку "Всі користувачі"
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.modules.admin.core.access_control import AdminAccessFilter
from app.modules.database.manager import DatabaseManager
from app.config.settings import settings
from .keyboards import get_users_list_keyboard, get_user_detail_keyboard, get_user_confirmation_keyboard
from .formatters import format_admin_user_card, format_users_list_header

logger = logging.getLogger(__name__)

# Імпортуємо роутер з __init__.py
from . import listing_router as router

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())

# Ініціалізуємо менеджер бази даних
db_manager = DatabaseManager()


@router.callback_query(F.data == "admin_all_users")
async def show_all_users(callback: CallbackQuery, state: FSMContext):
    """Показати всіх користувачів зі статистикою та пагінацією"""
    await callback.answer()
    
    try:
        # Отримуємо статистику
        stats = await db_manager.get_users_statistics()
        
        # Отримуємо першу сторінку користувачів з сортуванням за датою
        users = await db_manager.get_users(limit=settings.page_size, offset=0, sort_by="created_at_desc")
        
        # Отримуємо загальну кількість сторінок
        total_users = stats['total_users']
        total_pages = (total_users + settings.page_size - 1) // settings.page_size  # Округлення вгору
        
        # Форматуємо заголовок
        header_text = format_users_list_header(
            total_users=stats['total_users'],
            active_users=stats['active_users'],
            blocked_users=stats['blocked_users'],
            verified_users=0,  # Видалено верифікацію
            current_page=1,
            total_pages=total_pages,
            status_filter="all"
        )
        
        if not users:
            header_text += "\n❌ <b>Користувачі не знайдені</b>\nПоки що немає зареєстрованих користувачів."
        
        # Відправляємо повідомлення зі статистикою та списком користувачів
        await callback.message.edit_text(
            header_text,
            reply_markup=get_users_list_keyboard(users, current_page=1, total_pages=total_pages, sort_by="created_at_desc", status_filter="all"),
            parse_mode="HTML"
        )
        
        # Зберігаємо поточну сторінку та сортування в стані
        await state.update_data(users_page=1, users_sort="created_at_desc", users_status_filter="all", total_pages=total_pages)
        
        logger.info(f"👥 Показано всіх користувачів для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка завантаження користувачів: {e}")
        await callback.message.edit_text(
            f"❌ <b>Помилка завантаження</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("users_page_"))
async def navigate_users_page(callback: CallbackQuery, state: FSMContext):
    """Навігація по сторінках користувачів"""
    await callback.answer()
    
    try:
        # Отримуємо номер сторінки з callback_data
        page = int(callback.data.replace("users_page_", ""))
        
        # Отримуємо дані з стану
        state_data = await state.get_data()
        total_pages = state_data.get('total_pages', 1)
        sort_by = state_data.get('users_sort', 'created_at_desc')
        status_filter = state_data.get('users_status_filter', 'all')
        
        # Перевіряємо валідність сторінки
        if page < 1 or page > total_pages:
            await callback.answer("❌ Недійсна сторінка", show_alert=True)
            return
        
        # Отримуємо користувачів для поточної сторінки
        offset = (page - 1) * settings.page_size
        users = await db_manager.get_users(limit=settings.page_size, offset=offset, sort_by=sort_by, status_filter=status_filter)
        
        # Отримуємо статистику
        stats = await db_manager.get_users_statistics()
        
        # Форматуємо заголовок
        header_text = format_users_list_header(
            total_users=stats['total_users'],
            active_users=stats['active_users'],
            blocked_users=stats['blocked_users'],
            verified_users=0,  # Видалено верифікацію
            current_page=page,
            total_pages=total_pages,
            status_filter=status_filter
        )
        
        # Оновлюємо повідомлення
        await callback.message.edit_text(
            header_text,
            reply_markup=get_users_list_keyboard(users, current_page=page, total_pages=total_pages, sort_by=sort_by, status_filter=status_filter),
            parse_mode="HTML"
        )
        
        # Оновлюємо поточну сторінку в стані
        await state.update_data(users_page=page)
        
        logger.info(f"📄 Перехід на сторінку {page} користувачів для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка навігації по сторінках: {e}")
        await callback.answer("❌ Помилка навігації", show_alert=True)


@router.callback_query(F.data.startswith("view_user_"))
async def view_user_details(callback: CallbackQuery, state: FSMContext):
    """Переглянути детальну інформацію про користувача"""
    await callback.answer()
    
    try:
        # Отримуємо ID користувача з callback_data
        user_id = int(callback.data.replace("view_user_", ""))
        
        # Отримуємо користувача
        user = await db_manager.get_user_by_id(user_id)
        
        if not user:
            await callback.answer("❌ Користувач не знайдений", show_alert=True)
            return
        
        # Визначаємо контекст прав
        founder_ids = settings.get_admin_ids()
        admin_is_owner = callback.from_user.id in founder_ids
        
        # Форматуємо картку користувача з урахуванням обмежень
        is_self = False
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user.id:
            is_self = True
        user_text, _ = format_admin_user_card(user, admin_is_owner=admin_is_owner, is_self=is_self)

        # Отримуємо поточного адміна з БД, щоб мати його внутрішній user.id
        admin_db_id = admin_user.id if admin_user else None
        
        # Створюємо клавіатуру (передаємо також telegram_id цілі)
        keyboard = get_user_detail_keyboard(
            user_id=user.id,
            is_active=user.is_active,
            user_role=user.role.value,
            admin_user_id=admin_db_id,
            founder_ids=founder_ids,
            user_telegram_id=user.telegram_id,
            admin_is_owner=admin_is_owner,
        )
        
        # Відправляємо картку користувача
        await callback.message.edit_text(
            user_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"👤 Переглянуто користувача {user_id} адміном {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка перегляду користувача: {e}")
        await callback.answer("❌ Помилка завантаження", show_alert=True)


@router.callback_query(F.data.startswith("sort_users_"))
async def sort_users(callback: CallbackQuery, state: FSMContext):
    """Змінити сортування користувачів"""
    await callback.answer()
    
    try:
        # Отримуємо тип сортування та статус фільтр з callback_data
        data_part = callback.data.replace("sort_users_", "")
        
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
        current_page = state_data.get('users_page', 1)
        
        # Отримуємо користувачів з урахуванням статус фільтра та сортування
        users = await db_manager.get_users(
            limit=settings.page_size, 
            offset=(current_page - 1) * settings.page_size, 
            sort_by=sort_type,
            status_filter=status_filter
        )
        
        total_count = await db_manager.get_users_count(status_filter)
        total_pages = (total_count + settings.page_size - 1) // settings.page_size
        
        # Отримуємо статистику
        stats = await db_manager.get_users_statistics()
        
        # Форматуємо заголовок
        header_text = format_users_list_header(
            total_users=stats['total_users'],
            active_users=stats['active_users'],
            blocked_users=stats['blocked_users'],
            verified_users=0,  # Видалено верифікацію
            current_page=current_page,
            total_pages=total_pages,
            status_filter=status_filter
        )
        
        # Оновлюємо повідомлення
        await callback.message.edit_text(
            header_text,
            reply_markup=get_users_list_keyboard(users, current_page=current_page, total_pages=total_pages, sort_by=sort_type, status_filter=status_filter),
            parse_mode="HTML"
        )
        
        # Оновлюємо сортування в стані
        await state.update_data(users_sort=sort_type, users_status_filter=status_filter, total_pages=total_pages)
        
        logger.info(f"🔄 Змінено сортування користувачів на {sort_type} для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка зміни сортування: {e}")
        await callback.answer("❌ Помилка зміни сортування", show_alert=True)


@router.callback_query(F.data.startswith("filter_users_status_"))
async def filter_users_by_status(callback: CallbackQuery, state: FSMContext):
    """Фільтрація користувачів за статусом"""
    await callback.answer()
    
    try:
        # Отримуємо статус та сортування з callback_data
        data_part = callback.data.replace("filter_users_status_", "")
        
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
        
        # Отримуємо користувачів з фільтрацією за статусом
        users = await db_manager.get_users(
            limit=settings.page_size, 
            offset=0, 
            sort_by=sort_by,
            status_filter=status_filter
        )
        
        total_count = await db_manager.get_users_count(status_filter)
        total_pages = (total_count + settings.page_size - 1) // settings.page_size
        
        # Отримуємо статистику
        stats = await db_manager.get_users_statistics()
        
        # Форматуємо заголовок
        header_text = format_users_list_header(
            total_users=stats['total_users'],
            active_users=stats['active_users'],
            blocked_users=stats['blocked_users'],
            verified_users=0,  # Видалено верифікацію
            current_page=current_page,
            total_pages=total_pages,
            status_filter=status_filter
        )
        
        # Оновлюємо повідомлення
        await callback.message.edit_text(
            header_text,
            reply_markup=get_users_list_keyboard(users, current_page=current_page, total_pages=total_pages, sort_by=sort_by, status_filter=status_filter),
            parse_mode="HTML"
        )
        
        # Оновлюємо стан
        await state.update_data(users_page=current_page, users_sort=sort_by, users_status_filter=status_filter, total_pages=total_pages)
        
        logger.info(f"🔍 Застосовано фільтр статусу {status_filter} для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка фільтрації: {e}")
        await callback.answer("❌ Помилка фільтрації", show_alert=True)


@router.callback_query(F.data.startswith("block_user_"))
async def block_user(callback: CallbackQuery, state: FSMContext):
    """Заблокувати користувача"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("block_user_", ""))
        
        # Перевіряємо, чи адмін не намагається заблокувати самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете заблокувати самого себе!", show_alert=True)
            return
        
        # Отримуємо користувача
        user = await db_manager.get_user_by_id(user_id)
        
        if not user:
            await callback.answer("❌ Користувач не знайдений", show_alert=True)
            return
        
        # Блокуємо користувача без підтвердження
        success = await db_manager.block_user(user_id)
        
        if success:
            # Оновлюємо картку користувача
            updated_user = await db_manager.get_user_by_id(user_id)
            user_card_text, _ = format_admin_user_card(updated_user)
            # Поточний адмін (DB id) для коректної самоперевірки
            admin_db_id = admin_user.id if admin_user else None
            await callback.message.edit_text(
                user_card_text,
                reply_markup=get_user_detail_keyboard(
                    user_id=updated_user.id,
                    is_active=updated_user.is_active,
                    user_role=updated_user.role.value,
                    admin_user_id=admin_db_id,
                    founder_ids=settings.get_admin_ids(),
                    user_telegram_id=updated_user.telegram_id,
                    admin_is_owner=(callback.from_user.id in settings.get_admin_ids()),
                ),
                parse_mode="HTML"
            )
            await callback.answer("🚫 Користувача заблоковано", show_alert=True)
            logger.info(f"🚫 Заблоковано користувача {user_id} адміном {callback.from_user.id}")
        else:
            await callback.answer("❌ Помилка блокування користувача", show_alert=True)
        
    except Exception as e:
        logger.error(f"❌ Помилка блокування користувача: {e}")
        await callback.answer("❌ Помилка блокування", show_alert=True)


@router.callback_query(F.data.startswith("unblock_user_"))
async def unblock_user(callback: CallbackQuery, state: FSMContext):
    """Розблокувати користувача"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("unblock_user_", ""))
        
        # Перевіряємо, чи адмін не намагається розблокувати самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете розблокувати самого себе!", show_alert=True)
            return
        
        # Отримуємо користувача
        user = await db_manager.get_user_by_id(user_id)
        
        if not user:
            await callback.answer("❌ Користувач не знайдений", show_alert=True)
            return
        
        # Розблоковуємо користувача без підтвердження
        success = await db_manager.unblock_user(user_id)
        
        if success:
            # Оновлюємо картку користувача
            updated_user = await db_manager.get_user_by_id(user_id)
            user_card_text, _ = format_admin_user_card(updated_user)
            # Поточний адмін (DB id) для коректної самоперевірки
            admin_db_id = admin_user.id if admin_user else None
            await callback.message.edit_text(
                user_card_text,
                reply_markup=get_user_detail_keyboard(
                    user_id=updated_user.id,
                    is_active=updated_user.is_active,
                    user_role=updated_user.role.value,
                    admin_user_id=admin_db_id,
                    founder_ids=settings.get_admin_ids(),
                    user_telegram_id=updated_user.telegram_id,
                    admin_is_owner=(callback.from_user.id in settings.get_admin_ids()),
                ),
                parse_mode="HTML"
            )
            await callback.answer("✅ Користувача розблоковано", show_alert=True)
            logger.info(f"✅ Розблоковано користувача {user_id} адміном {callback.from_user.id}")
        else:
            await callback.answer("❌ Помилка розблокування користувача", show_alert=True)
        
    except Exception as e:
        logger.error(f"❌ Помилка розблокування користувача: {e}")
        await callback.answer("❌ Помилка розблокування", show_alert=True)


@router.callback_query(F.data.startswith("delete_user_"))
async def delete_user(callback: CallbackQuery, state: FSMContext):
    """Видалити користувача"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("delete_user_", ""))
        
        # Перевіряємо, чи адмін не намагається видалити самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете видалити самого себе!", show_alert=True)
            return
        
        # Отримуємо користувача
        user = await db_manager.get_user_by_id(user_id)
        
        if not user:
            await callback.answer("❌ Користувач не знайдений", show_alert=True)
            return
        
        # Показуємо підтвердження
        confirmation_text = f"""⚠️ <b>Підтвердження видалення</b>

👤 <b>Користувач:</b> {user.first_name or 'Без імені'} {user.last_name or ''}
🆔 <b>ID:</b> {user.id}
📱 <b>Telegram ID:</b> {user.telegram_id}

❓ <b>Ви впевнені, що хочете видалити цього користувача?</b>

<i>⚠️ Ця дія незворотна! Всі дані користувача будуть втрачені.</i>"""
        
        await callback.message.edit_text(
            confirmation_text,
            reply_markup=get_user_confirmation_keyboard("delete", user_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"❌ Помилка видалення користувача: {e}")
        await callback.answer("❌ Помилка видалення", show_alert=True)


@router.callback_query(F.data.startswith("confirm_block_user_"))
async def confirm_block_user(callback: CallbackQuery, state: FSMContext):
    """Підтвердити блокування користувача"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("confirm_block_user_", ""))
        
        # Перевіряємо, чи адмін не намагається заблокувати самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете заблокувати самого себе!", show_alert=True)
            return
        
        # Блокуємо користувача
        success = await db_manager.block_user(user_id)
        
        if success:
            await callback.message.edit_text(
                "✅ <b>Користувач успішно заблокований</b>",
                parse_mode="HTML"
            )
            # Повертаємося до списку користувачів
            await show_all_users(callback, state)
            logger.info(f"🚫 Заблоковано користувача {user_id} адміном {callback.from_user.id}")
        else:
            await callback.message.edit_text(
                "❌ <b>Помилка блокування користувача</b>",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"❌ Помилка підтвердження блокування: {e}")
        await callback.answer("❌ Помилка блокування", show_alert=True)


@router.callback_query(F.data.startswith("confirm_unblock_user_"))
async def confirm_unblock_user(callback: CallbackQuery, state: FSMContext):
    """Підтвердити розблокування користувача"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("confirm_unblock_user_", ""))
        
        # Перевіряємо, чи адмін не намагається розблокувати самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете розблокувати самого себе!", show_alert=True)
            return
        
        # Розблоковуємо користувача
        success = await db_manager.unblock_user(user_id)
        
        if success:
            await callback.message.edit_text(
                "✅ <b>Користувач успішно розблокований</b>",
                parse_mode="HTML"
            )
            # Повертаємося до списку користувачів
            await show_all_users(callback, state)
            logger.info(f"✅ Розблоковано користувача {user_id} адміном {callback.from_user.id}")
        else:
            await callback.message.edit_text(
                "❌ <b>Помилка розблокування користувача</b>",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"❌ Помилка підтвердження розблокування: {e}")
        await callback.answer("❌ Помилка розблокування", show_alert=True)


@router.callback_query(F.data.startswith("confirm_delete_user_"))
async def confirm_delete_user(callback: CallbackQuery, state: FSMContext):
    """Підтвердити видалення користувача"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("confirm_delete_user_", ""))
        
        # Перевіряємо, чи адмін не намагається видалити самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете видалити самого себе!", show_alert=True)
            return
        
        # Видаляємо користувача
        success = await db_manager.delete_user(user_id)
        
        if success:
            # UX: без проміжного повідомлення одразу показуємо оновлений список в цьому ж повідомленні
            await show_all_users(callback, state)
            logger.info(f"🗑️ Видалено користувача {user_id} адміном {callback.from_user.id}")
        else:
            await callback.message.edit_text(
                "❌ <b>Помилка видалення користувача</b>",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"❌ Помилка підтвердження видалення: {e}")
        await callback.answer("❌ Помилка видалення", show_alert=True)


@router.callback_query(F.data.startswith("cancel_user_action_"))
async def cancel_user_action(callback: CallbackQuery, state: FSMContext):
    """Скасувати дію з користувачем"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("cancel_user_action_", ""))
        
        # Повертаємося до картки користувача
        user = await db_manager.get_user_by_id(user_id)
        
        if user:
            user_text, _ = format_admin_user_card(user)
            # Поточний адмін (DB id) для коректної самоперевірки
            admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
            admin_db_id = admin_user.id if admin_user else None
            keyboard = get_user_detail_keyboard(
                user_id=user.id,
                is_active=user.is_active,
                user_role=user.role.value,
                admin_user_id=admin_db_id,
                founder_ids=settings.get_admin_ids(),
                user_telegram_id=user.telegram_id,
                admin_is_owner=(callback.from_user.id in settings.get_admin_ids()),
            )
            
            await callback.message.edit_text(
                user_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ <b>Користувач не знайдений</b>",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"❌ Помилка скасування дії: {e}")
        await callback.answer("❌ Помилка скасування", show_alert=True)


@router.callback_query(F.data == "back_to_users_list")
async def back_to_users_list(callback: CallbackQuery, state: FSMContext):
    """Повернутися до списку користувачів"""
    await callback.answer()
    
    try:
        # Отримуємо дані з стану
        state_data = await state.get_data()
        current_page = state_data.get('users_page', 1)
        sort_by = state_data.get('users_sort', 'created_at_desc')
        status_filter = state_data.get('users_status_filter', 'all')
        
        # Отримуємо користувачів
        users = await db_manager.get_users(
            limit=settings.page_size, 
            offset=(current_page - 1) * settings.page_size, 
            sort_by=sort_by,
            status_filter=status_filter
        )
        
        # Отримуємо статистику
        stats = await db_manager.get_users_statistics()
        
        # Отримуємо загальну кількість сторінок
        total_count = await db_manager.get_users_count(status_filter)
        total_pages = (total_count + 9) // 10
        
        # Форматуємо заголовок
        header_text = format_users_list_header(
            total_users=stats['total_users'],
            active_users=stats['active_users'],
            blocked_users=stats['blocked_users'],
            verified_users=0,  # Видалено верифікацію
            current_page=current_page,
            total_pages=total_pages,
            status_filter=status_filter
        )
        
        # Повертаємося до списку
        await callback.message.edit_text(
            header_text,
            reply_markup=get_users_list_keyboard(users, current_page=current_page, total_pages=total_pages, sort_by=sort_by, status_filter=status_filter),
            parse_mode="HTML"
        )
        
        logger.info(f"🔙 Повернення до списку користувачів для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка повернення до списку: {e}")
        await callback.answer("❌ Помилка повернення", show_alert=True)


@router.callback_query(F.data == "back_to_user_management")
async def back_to_user_management(callback: CallbackQuery, state: FSMContext):
    """Повернення до меню управління користувачами"""
    await callback.answer()
    await state.clear()
    
    try:
        # Викликаємо callback напряму
        from app.modules.admin.shared.modules.keyboards.main_keyboards import get_admin_users_keyboard
        
        users_text = """
👥 <b>Управління користувачами</b>

<b>Доступні дії:</b>
• 👥 <b>Всі користувачі</b> - переглянути всіх користувачів з пагінацією та фільтрами
• 🔍 <b>Пошук користувачів</b> - знайти користувачів за різними параметрами

Оберіть дію:
"""
        
        await callback.message.edit_text(
            users_text,
            reply_markup=get_admin_users_keyboard(),
            parse_mode="HTML"
        )
        logger.info(f"🔙 Адмін {callback.from_user.id} повернувся до управління користувачами")
        
    except Exception as e:
        logger.error(f"❌ Помилка повернення до управління користувачами: {e}")
        await callback.answer("❌ Помилка навігації", show_alert=True)


@router.callback_query(F.data == "back_to_admin_panel")
async def back_to_admin_panel(callback: CallbackQuery, state: FSMContext):
    """Повернення до головної адмін панелі"""
    await callback.answer()
    await state.clear()
    
    try:
        # Викликаємо callback напряму
        from app.modules.admin.shared.modules.keyboards.main_keyboards import get_admin_main_keyboard
        
        main_text = """
🏠 <b>Адмін панель M-Truck</b>

Вітаємо в панелі управління ботом!

<b>Доступні розділи:</b>
• 🚛 <b>Управління авто</b> - додавання, редагування, публікація авто
• 👥 <b>Користувачі</b> - управління користувачами бота
• 📊 <b>Статистика</b> - аналітика та метрики
• 📢 <b>Розсилка</b> - масові повідомлення користувачам
• ⚙️ <b>Налаштування</b> - конфігурація бота
• 📋 <b>Звіти</b> - детальні звіти по роботі

Оберіть розділ для роботи:
"""
        
        await callback.message.edit_text(
            main_text,
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )
        logger.info(f"🔙 Адмін {callback.from_user.id} повернувся до головної адмін панелі")
        
    except Exception as e:
        logger.error(f"❌ Помилка повернення до адмін панелі: {e}")
        await callback.answer("❌ Помилка навігації", show_alert=True)


@router.callback_query(F.data.startswith("promote_to_admin_"))
async def promote_to_admin(callback: CallbackQuery, state: FSMContext):
    """Підвищити користувача до адміністратора"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("promote_to_admin_", ""))
        
        # Перевіряємо, чи адмін не намагається підвищити самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете змінити роль самого себе!", show_alert=True)
            return
        
        # Отримуємо користувача
        user = await db_manager.get_user_by_id(user_id)
        
        if not user:
            await callback.answer("❌ Користувач не знайдений", show_alert=True)
            return
        
        # Показуємо підтвердження
        confirmation_text = f"""⚠️ <b>Підтвердження підвищення до адміністратора</b>

👤 <b>Користувач:</b> {user.first_name or 'Без імені'} {user.last_name or ''}
🆔 <b>ID:</b> {user.id}
📱 <b>Telegram ID:</b> {user.telegram_id}
🏷️ <b>Поточна роль:</b> {user.role.value.capitalize()}

❓ <b>Ви впевнені, що хочете надати цьому користувачу права адміністратора?</b>

<i>⚠️ Адміністратор отримає доступ до всіх функцій управління ботом.</i>"""
        
        await callback.message.edit_text(
            confirmation_text,
            reply_markup=get_user_confirmation_keyboard("promote_to_admin", user_id),
            parse_mode="HTML"
        )
        
        logger.info(f"👑 Адмін {callback.from_user.id} запитує підтвердження підвищення користувача {user_id} до адміна")
        
    except Exception as e:
        logger.error(f"❌ Помилка підвищення до адміна: {e}")
        await callback.answer("❌ Помилка підвищення", show_alert=True)


@router.callback_query(F.data.startswith("demote_from_admin_"))
async def demote_from_admin(callback: CallbackQuery, state: FSMContext):
    """Знизити користувача з адміністратора"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("demote_from_admin_", ""))
        
        # Перевіряємо, чи адмін не намагається знизити самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете змінити роль самого себе!", show_alert=True)
            return
        
        # Перевіряємо, чи це не засновник (головний адміністратор)
        founder_ids = settings.get_admin_ids()
        if user_id in founder_ids:
            await callback.answer("❌ Не можна зняти права адміна у засновника!", show_alert=True)
            return
        
        # Отримуємо користувача
        user = await db_manager.get_user_by_id(user_id)
        
        if not user:
            await callback.answer("❌ Користувач не знайдений", show_alert=True)
            return
        
        # Показуємо підтвердження
        confirmation_text = f"""⚠️ <b>Підтвердження зняття прав адміністратора</b>

👤 <b>Користувач:</b> {user.first_name or 'Без імені'} {user.last_name or ''}
🆔 <b>ID:</b> {user.id}
📱 <b>Telegram ID:</b> {user.telegram_id}
🏷️ <b>Поточна роль:</b> {user.role.value.capitalize()}

❓ <b>Ви впевнені, що хочете зняти права адміністратора у цього користувача?</b>

<i>⚠️ Користувач втратить доступ до функцій управління ботом.</i>"""
        
        await callback.message.edit_text(
            confirmation_text,
            reply_markup=get_user_confirmation_keyboard("demote_from_admin", user_id),
            parse_mode="HTML"
        )
        
        logger.info(f"⬇️ Адмін {callback.from_user.id} запитує підтвердження зняття прав адміна у користувача {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка зняття прав адміна: {e}")
        await callback.answer("❌ Помилка зняття прав", show_alert=True)


@router.callback_query(F.data.startswith("confirm_promote_to_admin_"))
async def confirm_promote_to_admin(callback: CallbackQuery, state: FSMContext):
    """Підтвердити підвищення до адміністратора"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("confirm_promote_to_admin_", ""))
        
        # Перевіряємо, чи адмін не намагається підвищити самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете змінити роль самого себе!", show_alert=True)
            return
        
        # Підвищуємо користувача до адміна
        success = await db_manager.update_user(user_id, {"role": "admin"})
        
        if success:
            # Отримуємо оновленого користувача
            updated_user = await db_manager.get_user_by_id(user_id)
            if updated_user:
                user_card_text, _ = format_admin_user_card(updated_user)
                # Поточний адмін (DB id) для коректної самоперевірки
                admin_db_id = admin_user.id if admin_user else None
                await callback.message.edit_text(
                    user_card_text,
                    reply_markup=get_user_detail_keyboard(
                        user_id=updated_user.id,
                        is_active=updated_user.is_active,
                        user_role=updated_user.role.value,
                        admin_user_id=admin_db_id,
                        founder_ids=settings.get_admin_ids(),
                        user_telegram_id=updated_user.telegram_id,
                        admin_is_owner=(callback.from_user.id in settings.get_admin_ids()),
                    ),
                    parse_mode="HTML"
                )
                await callback.answer("👑 Користувача підвищено до адміністратора", show_alert=True)
            else:
                await callback.message.edit_text(
                    "❌ <b>Помилка отримання оновлених даних користувача</b>",
                    parse_mode="HTML"
                )
            logger.info(f"👑 Підвищено користувача {user_id} до адміна адміном {callback.from_user.id}")
        else:
            await callback.message.edit_text(
                "❌ <b>Помилка підвищення користувача</b>",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"❌ Помилка підтвердження підвищення: {e}")
        await callback.answer("❌ Помилка підвищення", show_alert=True)


@router.callback_query(F.data.startswith("confirm_demote_from_admin_"))
async def confirm_demote_from_admin(callback: CallbackQuery, state: FSMContext):
    """Підтвердити зняття прав адміністратора"""
    await callback.answer()
    
    try:
        user_id = int(callback.data.replace("confirm_demote_from_admin_", ""))
        
        # Перевіряємо, чи адмін не намагається знизити самого себе
        admin_user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if admin_user and admin_user.id == user_id:
            await callback.answer("❌ Ви не можете змінити роль самого себе!", show_alert=True)
            return
        
        # Перевіряємо, чи це не засновник (головний адміністратор)
        founder_ids = settings.get_admin_ids()
        if user_id in founder_ids:
            await callback.answer("❌ Не можна зняти права адміна у засновника!", show_alert=True)
            return
        
        # Знижуємо користувача до покупця
        success = await db_manager.update_user(user_id, {"role": "buyer"})
        
        if success:
            # Очищаємо FSM стани демотованого користувача
            from app.modules.database.models import UserModel
            demoted_user = await db_manager.get_user_by_id(user_id)
            if demoted_user:
                # Очищаємо кеш ролі в middleware
                from app.middleware.role_change_guard import role_change_guard
                role_change_guard.clear_user_cache(demoted_user.telegram_id)
                logger.info(f"🧹 Очищено кеш ролі для демотованого користувача {demoted_user.telegram_id}")
            
            # Отримуємо оновленого користувача
            updated_user = await db_manager.get_user_by_id(user_id)
            if updated_user:
                user_card_text, _ = format_admin_user_card(updated_user)
                # Поточний адмін (DB id) для коректної самоперевірки
                admin_db_id = admin_user.id if admin_user else None
                await callback.message.edit_text(
                    user_card_text,
                    reply_markup=get_user_detail_keyboard(
                        user_id=updated_user.id,
                        is_active=updated_user.is_active,
                        user_role=updated_user.role.value,
                        admin_user_id=admin_db_id,
                        founder_ids=settings.get_admin_ids(),
                        user_telegram_id=updated_user.telegram_id,
                        admin_is_owner=(callback.from_user.id in settings.get_admin_ids()),
                    ),
                    parse_mode="HTML"
                )
                await callback.answer("⬇️ Права адміністратора знято", show_alert=True)
            else:
                await callback.message.edit_text(
                    "❌ <b>Помилка отримання оновлених даних користувача</b>",
                    parse_mode="HTML"
                )
            logger.info(f"⬇️ Знято права адміна у користувача {user_id} адміном {callback.from_user.id}")
        else:
            await callback.message.edit_text(
                "❌ <b>Помилка зняття прав адміністратора</b>",
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"❌ Помилка підтвердження зняття прав: {e}")
        await callback.answer("❌ Помилка зняття прав", show_alert=True)
