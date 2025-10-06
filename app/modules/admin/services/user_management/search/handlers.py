"""
Обробники для блоку "Пошук користувачів"
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.modules.admin.core.access_control import AdminAccessFilter
from app.modules.database.manager import DatabaseManager
from .keyboards import (
    get_search_users_keyboard, 
    get_search_results_keyboard,
    get_role_selection_keyboard,
    get_users_search_results_keyboard
)
from .formatters import (
    format_user_search_results,
    format_search_instructions,
    format_role_search_results
)
from .states import UserSearchStates

logger = logging.getLogger(__name__)

# Імпортуємо роутер з __init__.py
from . import search_router as router

# Застосовуємо фільтр доступу
router.callback_query.filter(AdminAccessFilter())
router.message.filter(AdminAccessFilter())

# Ініціалізуємо менеджер бази даних
db_manager = DatabaseManager()


@router.callback_query(F.data == "admin_search_users")
async def show_search_users_menu(callback: CallbackQuery):
    """Показати меню пошуку користувачів"""
    await callback.answer()
    
    try:
        text = """🔍 <b>Пошук користувачів</b>

Оберіть параметр для пошуку:

🆔 <b>По ID користувача</b> - точний пошук по ідентифікатору
📱 <b>По Telegram ID</b> - пошук по Telegram ID
👤 <b>По імені</b> - пошук по імені, прізвищу або username
📞 <b>По телефону</b> - пошук по номеру телефону
🏷️ <b>По ролі</b> - пошук по ролі користувача
✅ <b>По верифікації</b> - пошук по статусу верифікації

<i>Кожен параметр працює окремо</i>"""
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_search_users_keyboard()
        )
        
        logger.info(f"🔍 Показано меню пошуку користувачів для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка показу меню пошуку: {e}")
        await callback.answer("❌ Помилка відображення меню", show_alert=True)


@router.callback_query(F.data == "search_user_by_id")
async def search_by_id_start(callback: CallbackQuery, state: FSMContext):
    """Почати пошук по ID користувача"""
    await callback.answer()
    
    try:
        instructions = format_search_instructions("id")
        
        await callback.message.edit_text(
            instructions,
            parse_mode="HTML",
            reply_markup=get_search_results_keyboard()
        )
        
        await state.set_state(UserSearchStates.waiting_for_id)
        
        logger.info(f"🆔 Почато пошук по ID для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по ID: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(UserSearchStates.waiting_for_id)
async def search_by_id_process(message: Message, state: FSMContext):
    """Обробка пошуку по ID користувача"""
    try:
        # Очищуємо стан
        await state.clear()
        
        # Перевіряємо чи це число
        try:
            user_id = int(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ <b>Помилка</b>\n\nID повинен бути числом. Спробуйте ще раз.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            return
        
        # Шукаємо користувача
        users = await db_manager.search_users_by_id(user_id)
        
        if users:
            # Якщо знайдено користувача - показуємо повну картку
            user = users[0]
            from ..listing.formatters import format_admin_user_card
            from ..listing.keyboards import get_user_detail_keyboard
            
            user_text, _ = format_admin_user_card(user)
            
            from app.config.settings import settings
            keyboard = get_user_detail_keyboard(
                user_id=user.id,
                is_active=user.is_active,
                user_role=user.role.value,
                admin_user_id=message.from_user.id,
                founder_ids=settings.get_admin_ids()
            )
            
            await message.answer(
                user_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            # Якщо не знайдено - показуємо повідомлення
            result_text = format_user_search_results(users, "ID користувача", str(user_id))
            
            await message.answer(
                result_text,
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
        
        logger.info(f"🆔 Виконано пошук по ID {user_id} для адміна {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по ID: {e}")
        await message.answer(
            "❌ <b>Помилка пошуку</b>\n\nСпробуйте ще раз.",
            parse_mode="HTML",
            reply_markup=get_search_results_keyboard()
        )


@router.callback_query(F.data == "search_user_by_telegram_id")
async def search_by_telegram_id_start(callback: CallbackQuery, state: FSMContext):
    """Почати пошук по Telegram ID"""
    await callback.answer()
    
    try:
        instructions = format_search_instructions("telegram_id")
        
        await callback.message.edit_text(
            instructions,
            parse_mode="HTML",
            reply_markup=get_search_results_keyboard()
        )
        
        await state.set_state(UserSearchStates.waiting_for_telegram_id)
        
        logger.info(f"📱 Почато пошук по Telegram ID для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по Telegram ID: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(UserSearchStates.waiting_for_telegram_id)
async def search_by_telegram_id_process(message: Message, state: FSMContext):
    """Обробка пошуку по Telegram ID"""
    try:
        # Очищуємо стан
        await state.clear()
        
        # Перевіряємо чи це число
        try:
            telegram_id = int(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ <b>Помилка</b>\n\nTelegram ID повинен бути числом. Спробуйте ще раз.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            return
        
        # Шукаємо користувача
        users = await db_manager.search_users_by_telegram_id(telegram_id)
        
        if users:
            # Якщо знайдено користувача - показуємо повну картку
            user = users[0]
            from ..listing.formatters import format_admin_user_card
            from ..listing.keyboards import get_user_detail_keyboard
            
            user_text, _ = format_admin_user_card(user)
            
            from app.config.settings import settings
            keyboard = get_user_detail_keyboard(
                user_id=user.id,
                is_active=user.is_active,
                user_role=user.role.value,
                admin_user_id=message.from_user.id,
                founder_ids=settings.get_admin_ids()
            )
            
            await message.answer(
                user_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            # Якщо не знайдено - показуємо повідомлення
            result_text = format_user_search_results(users, "Telegram ID", str(telegram_id))
            
            await message.answer(
                result_text,
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
        
        logger.info(f"📱 Виконано пошук по Telegram ID {telegram_id} для адміна {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по Telegram ID: {e}")
        await message.answer(
            "❌ <b>Помилка пошуку</b>\n\nСпробуйте ще раз.",
            parse_mode="HTML",
            reply_markup=get_search_results_keyboard()
        )


@router.callback_query(F.data == "search_user_by_name")
async def search_by_name_start(callback: CallbackQuery, state: FSMContext):
    """Почати пошук по імені"""
    await callback.answer()
    
    try:
        instructions = format_search_instructions("name")
        
        await callback.message.edit_text(
            instructions,
            parse_mode="HTML",
            reply_markup=get_search_results_keyboard()
        )
        
        await state.set_state(UserSearchStates.waiting_for_name)
        
        logger.info(f"👤 Почато пошук по імені для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по імені: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(UserSearchStates.waiting_for_name)
async def search_by_name_process(message: Message, state: FSMContext):
    """Обробка пошуку по імені"""
    try:
        # Очищуємо стан
        await state.clear()
        
        name = message.text.strip()
        
        # Шукаємо користувачів
        users = await db_manager.search_users_by_name(name)
        
        if users:
            # Якщо знайдено одного користувача - показуємо повну картку
            if len(users) == 1:
                user = users[0]
                from ..listing.formatters import format_admin_user_card
                from ..listing.keyboards import get_user_detail_keyboard
                
                user_text, _ = format_admin_user_card(user)
                
                from app.config.settings import settings
                keyboard = get_user_detail_keyboard(
                    user_id=user.id,
                    is_active=user.is_active,
                    user_role=user.role.value,
                    admin_user_id=message.from_user.id,
                    founder_ids=settings.get_admin_ids()
                )
                
                await message.answer(
                    user_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                # Якщо знайдено кілька користувачів - показуємо список
                result_text = format_user_search_results(users, "Ім'я", name)
                
                await message.answer(
                    result_text,
                    parse_mode="HTML",
                    reply_markup=get_users_search_results_keyboard(users)
                )
        else:
            # Якщо не знайдено - показуємо повідомлення
            result_text = format_user_search_results(users, "Ім'я", name)
            
            await message.answer(
                result_text,
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
        
        logger.info(f"👤 Виконано пошук по імені '{name}' для адміна {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по імені: {e}")
        await message.answer(
            "❌ <b>Помилка пошуку</b>\n\nСпробуйте ще раз.",
            parse_mode="HTML",
            reply_markup=get_search_results_keyboard()
        )


@router.callback_query(F.data == "search_user_by_phone")
async def search_by_phone_start(callback: CallbackQuery, state: FSMContext):
    """Почати пошук по телефону"""
    await callback.answer()
    
    try:
        instructions = format_search_instructions("phone")
        
        await callback.message.edit_text(
            instructions,
            parse_mode="HTML",
            reply_markup=get_search_results_keyboard()
        )
        
        await state.set_state(UserSearchStates.waiting_for_phone)
        
        logger.info(f"📞 Почато пошук по телефону для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по телефону: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(UserSearchStates.waiting_for_phone)
async def search_by_phone_process(message: Message, state: FSMContext):
    """Обробка пошуку по телефону"""
    try:
        # Очищуємо стан
        await state.clear()
        
        phone = message.text.strip()
        
        # Шукаємо користувачів
        users = await db_manager.search_users_by_phone(phone)
        
        if users:
            # Якщо знайдено одного користувача - показуємо повну картку
            if len(users) == 1:
                user = users[0]
                from ..listing.formatters import format_admin_user_card
                from ..listing.keyboards import get_user_detail_keyboard
                
                user_text, _ = format_admin_user_card(user)
                
                from app.config.settings import settings
                keyboard = get_user_detail_keyboard(
                    user_id=user.id,
                    is_active=user.is_active,
                    user_role=user.role.value,
                    admin_user_id=message.from_user.id,
                    founder_ids=settings.get_admin_ids()
                )
                
                await message.answer(
                    user_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                # Якщо знайдено кілька користувачів - показуємо список
                result_text = format_user_search_results(users, "Телефон", phone)
                
                await message.answer(
                    result_text,
                    parse_mode="HTML",
                    reply_markup=get_users_search_results_keyboard(users)
                )
        else:
            # Якщо не знайдено - показуємо повідомлення
            result_text = format_user_search_results(users, "Телефон", phone)
            
            await message.answer(
                result_text,
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
        
        logger.info(f"📞 Виконано пошук по телефону '{phone}' для адміна {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по телефону: {e}")
        await message.answer(
            "❌ <b>Помилка пошуку</b>\n\nСпробуйте ще раз.",
            parse_mode="HTML",
            reply_markup=get_search_results_keyboard()
        )


@router.callback_query(F.data == "search_user_by_role")
async def search_by_role_start(callback: CallbackQuery):
    """Почати пошук по ролі"""
    await callback.answer()
    
    try:
        text = """🏷️ <b>Пошук по ролі</b>

Оберіть роль для пошуку:

🛒 <b>Покупці</b> - користувачі з роллю buyer
🏪 <b>Продавці</b> - користувачі з роллю seller
👑 <b>Адміністратори</b> - користувачі з роллю admin"""
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_role_selection_keyboard()
        )
        
        logger.info(f"🏷️ Показано вибір ролі для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка показу вибору ролі: {e}")
        await callback.answer("❌ Помилка відображення", show_alert=True)


@router.callback_query(F.data.startswith("search_role_"))
async def search_by_role_process(callback: CallbackQuery):
    """Обробка пошуку по ролі"""
    await callback.answer()
    
    try:
        role = callback.data.replace("search_role_", "")
        
        # Шукаємо користувачів
        users = await db_manager.search_users_by_role(role)
        
        if users:
            # Форматуємо результати
            result_text = format_role_search_results(users, role)
            
            await callback.message.edit_text(
                result_text,
                parse_mode="HTML",
                reply_markup=get_users_search_results_keyboard(users)
            )
        else:
            # Якщо не знайдено
            result_text = format_role_search_results(users, role)
            
            await callback.message.edit_text(
                result_text,
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
        
        logger.info(f"🏷️ Виконано пошук по ролі '{role}' для адміна {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по ролі: {e}")
        await callback.answer("❌ Помилка пошуку", show_alert=True)


@router.callback_query(F.data == "search_user_by_username")
async def search_by_username_start(callback: CallbackQuery, state: FSMContext):
    """Початок пошуку користувачів за username"""
    await callback.answer()
    await state.set_state(UserSearchStates.waiting_for_username)
    
    try:
        await callback.message.edit_text(
            "👤 <b>Введіть username користувача:</b>\n\n"
            "Введіть username без символу @ (наприклад: username123)",
            parse_mode="HTML",
            reply_markup=get_search_results_keyboard()
        )
        logger.info(f"🔍 Адмін {callback.from_user.id} почав пошук користувачів за username")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку за username: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(UserSearchStates.waiting_for_username)
async def search_by_username_process(message: Message, state: FSMContext):
    """Обробка пошуку за username користувача"""
    try:
        username = message.text.strip()
        await state.clear()
        
        users = await db_manager.search_users_by_username(username)
        
        if users:
            # Якщо знайдено одного користувача - показуємо повну картку
            if len(users) == 1:
                user = users[0]
                from ..listing.formatters import format_admin_user_card
                from ..listing.keyboards import get_user_detail_keyboard
                
                user_text, _ = format_admin_user_card(user)
                
                from app.config.settings import settings
                keyboard = get_user_detail_keyboard(
                    user_id=user.id,
                    is_active=user.is_active,
                    user_role=user.role.value,
                    admin_user_id=message.from_user.id,
                    founder_ids=settings.get_admin_ids()
                )
                
                await message.answer(
                    user_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                # Якщо знайдено декілька користувачів - показуємо список
                text = format_user_search_results(users, "username", username)
                await message.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=get_users_search_results_keyboard(users)
                )
        else:
            await message.answer(
                f"❌ Користувачів з username '{username}' не знайдено.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
        logger.info(f"🔍 Адмін {message.chat.id} завершив пошук користувачів за username: {username}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку користувачів за username: {e}")
        await message.answer("❌ Помилка пошуку", parse_mode="HTML", reply_markup=get_search_results_keyboard())


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
