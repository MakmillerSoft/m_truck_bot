"""
Модуль профілю (клієнтська частина)
Включає перегляд та редагування профілю
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from app.modules.database.manager import db_manager
from app.utils.formatting import get_default_parse_mode
from .keyboards import get_profile_main_keyboard, get_edit_profile_keyboard
from .states import ProfileStates

logger = logging.getLogger(__name__)

# Створюємо роутер безпосередньо тут
profile_router = Router(name="client_profile")


async def _render_profile(telegram_id: int, target):
    """Відмалювати профіль користувача у вказане повідомлення/чат.
    target: Message об'єкт (callback.message або message)
    """
    try:
        user = await db_manager.get_user_by_telegram_id(telegram_id)
        logger.debug(f"📊 Отримано користувача: {user}")

        if not user:
            logger.warning(f"⚠️ Користувач {telegram_id} не знайдений в БД")
            text = (
                "❌ <b>Профіль не знайдено!</b>\n\n"
                "Спочатку зареєструйтеся командою /start"
            )
            try:
                await target.edit_text(text, parse_mode=get_default_parse_mode())
            except Exception:
                await target.answer(text, parse_mode=get_default_parse_mode())
            return

        text = f"""
👤 <b>Ваш профіль</b>

📋 <b>Основна інформація</b>
• Ім'я: {user.first_name or '—'} {user.last_name or ''}
• Роль: Покупець
• Статус: {"✅ Активний" if user.is_active else "❌ Неактивний"}

📞 <b>Контакти</b>
• Телефон: {user.phone or "❌ Не вказано"}
• Telegram ID: <code>{user.telegram_id}</code>

📖 <b>Як користуватися профілем:</b>
• Натисніть <b>"✏️ Редагувати профіль"</b>, щоб змінити дані
• Оновіть <b>телефон</b> — на нього телефонує менеджер
• Ім'я/прізвище використовуються в заявках
• Зміни застосовуються відразу після збереження

💡 <i>Порада:</i> введіть номер у форматі <code>+380501234567</code> для швидкого дзвінка через кнопку.
"""
        try:
            await target.edit_text(
                text.strip(),
                reply_markup=get_profile_main_keyboard(),
                parse_mode=get_default_parse_mode(),
            )
        except Exception as e:
            logger.warning(f"⚠️ Не вдалося edit_text, використовую answer: {e}")
            await target.answer(
                text.strip(),
                reply_markup=get_profile_main_keyboard(),
                parse_mode=get_default_parse_mode(),
            )
    except Exception as e:
        logger.error(f"❌ Помилка при відображенні профілю: {e}", exc_info=True)


@profile_router.callback_query(F.data == "client_profile")
async def profile_from_menu(callback: CallbackQuery):
    """Показ профілю з головного інлайн-меню (callback)."""
    await callback.answer()
    logger.info(f"👤 [CALLBACK] User ID: {callback.from_user.id}, Username: {callback.from_user.username}, First name: {callback.from_user.first_name}")
    await _render_profile(callback.from_user.id, callback.message)


# Залишаємо хендлер на випадок виклику як функції з інших місць
@profile_router.message(F.text == "👤 Профіль")
async def profile_command(message: Message):
    """Показ профілю через текстову кнопку/команду."""
    # У приватних чатах використовуємо chat.id, бо from_user може бути ботом для Reply Keyboard
    user_id = message.chat.id if message.chat.type == "private" else message.from_user.id
    
    logger.info(f"👤 [MESSAGE] from_user.id: {message.from_user.id}, chat.id: {message.chat.id}, is_bot: {message.from_user.is_bot}")
    logger.info(f"👤 [MESSAGE] Using user_id: {user_id} for profile lookup")
    
    await _render_profile(user_id, message)


# ==================== РЕДАГУВАННЯ ПРОФІЛЮ ====================

@profile_router.callback_query(F.data == "edit_profile")
async def edit_profile_menu(callback: CallbackQuery):
    """Меню редагування профілю"""
    await callback.answer()
    
    text = """
✏️ <b>Редагування профілю</b>

Оберіть, що ви хочете змінити:

• <b>Ім'я</b> - ваше ім'я
• <b>Прізвище</b> - ваше прізвище  
• <b>Телефон</b> - номер телефону для зв'язку
"""
    await callback.message.edit_text(
        text.strip(),
        reply_markup=get_edit_profile_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@profile_router.callback_query(F.data == "edit_first_name")
async def start_edit_first_name(callback: CallbackQuery, state: FSMContext):
    """Початок редагування імені"""
    await callback.answer()
    await state.set_state(ProfileStates.waiting_for_first_name)
    
    text = """
👤 <b>Зміна імені</b>

Введіть ваше нове ім'я:
"""
    await callback.message.edit_text(
        text.strip(),
        parse_mode=get_default_parse_mode(),
    )


@profile_router.message(ProfileStates.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    """Обробка нового імені"""
    new_first_name = message.text.strip()
    
    if len(new_first_name) < 1 or len(new_first_name) > 100:
        await message.answer(
            "❌ Ім'я має бути від 1 до 100 символів. Спробуйте ще раз:",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    # Оновлюємо в БД
    user_id = message.chat.id if message.chat.type == "private" else message.from_user.id
    user = await db_manager.get_user_by_telegram_id(user_id)
    
    if user:
        await db_manager.update_user(user.id, {"first_name": new_first_name})
        await state.clear()
        
        # Отримуємо оновлені дані
        updated_user = await db_manager.get_user_by_telegram_id(user_id)
        
        text = f"""
👤 <b>Ваш профіль</b>

📋 <b>Основна інформація</b>
• Ім'я: {updated_user.first_name or '—'} {updated_user.last_name or ''}
• Роль: Покупець
• Статус: {"✅ Активний" if updated_user.is_active else "❌ Неактивний"}

📞 <b>Контакти</b>
• Телефон: {updated_user.phone or "❌ Не вказано"}
• Telegram ID: <code>{updated_user.telegram_id}</code>

✅ Ім'я успішно змінено!
"""
        
        await message.answer(
            text.strip(),
            reply_markup=get_profile_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )


@profile_router.callback_query(F.data == "edit_last_name")
async def start_edit_last_name(callback: CallbackQuery, state: FSMContext):
    """Початок редагування прізвища"""
    await callback.answer()
    await state.set_state(ProfileStates.waiting_for_last_name)
    
    text = """
👤 <b>Зміна прізвища</b>

Введіть ваше нове прізвище:
"""
    await callback.message.edit_text(
        text.strip(),
        parse_mode=get_default_parse_mode(),
    )


@profile_router.message(ProfileStates.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    """Обробка нового прізвища"""
    new_last_name = message.text.strip()
    
    if len(new_last_name) < 1 or len(new_last_name) > 100:
        await message.answer(
            "❌ Прізвище має бути від 1 до 100 символів. Спробуйте ще раз:",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    # Оновлюємо в БД
    user_id = message.chat.id if message.chat.type == "private" else message.from_user.id
    user = await db_manager.get_user_by_telegram_id(user_id)
    
    if user:
        await db_manager.update_user(user.id, {"last_name": new_last_name})
        await state.clear()
        
        # Отримуємо оновлені дані
        updated_user = await db_manager.get_user_by_telegram_id(user_id)
        
        text = f"""
👤 <b>Ваш профіль</b>

📋 <b>Основна інформація</b>
• Ім'я: {updated_user.first_name or '—'} {updated_user.last_name or ''}
• Роль: Покупець
• Статус: {"✅ Активний" if updated_user.is_active else "❌ Неактивний"}

📞 <b>Контакти</b>
• Телефон: {updated_user.phone or "❌ Не вказано"}
• Telegram ID: <code>{updated_user.telegram_id}</code>

✅ Прізвище успішно змінено!
"""
        
        await message.answer(
            text.strip(),
            reply_markup=get_profile_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )


@profile_router.callback_query(F.data == "edit_phone")
async def start_edit_phone(callback: CallbackQuery, state: FSMContext):
    """Початок редагування телефону"""
    await callback.answer()
    await state.set_state(ProfileStates.waiting_for_phone)
    
    from app.modules.client.services.authentication.registration.keyboards import get_phone_keyboard
    
    text = """
📞 <b>Зміна номера телефону</b>

Ви можете:
• Поділитися номером через кнопку нижче
• Ввести номер вручну у форматі: +380XXXXXXXXX

<i>Приклади форматів: +380501234567, 380501234567, 0501234567</i>
"""
    # Редагуємо попереднє повідомлення
    await callback.message.edit_text(
        text.strip(),
        parse_mode=get_default_parse_mode(),
    )
    
    # Відправляємо Reply клавіатуру окремим повідомленням
    await callback.message.answer(
        "👇 Оберіть спосіб введення:",
        reply_markup=get_phone_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@profile_router.message(ProfileStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Обробка контакту (поділився номером)"""
    from app.modules.client.services.authentication.registration.handlers import normalize_phone_number
    
    phone = message.contact.phone_number
    normalized_phone = normalize_phone_number(phone)
    
    if not normalized_phone:
        await message.answer(
            "❌ Невірний формат номера телефону. Спробуйте ще раз.",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    # Оновлюємо в БД
    user_id = message.chat.id if message.chat.type == "private" else message.from_user.id
    user = await db_manager.get_user_by_telegram_id(user_id)
    
    if user:
        await db_manager.update_user(user.id, {"phone": normalized_phone})
        await state.clear()
        
        # Отримуємо оновлені дані
        updated_user = await db_manager.get_user_by_telegram_id(user_id)
        
        text = f"""
👤 <b>Ваш профіль</b>

📋 <b>Основна інформація</b>
• Ім'я: {updated_user.first_name or '—'} {updated_user.last_name or ''}
• Роль: Покупець
• Статус: {"✅ Активний" if updated_user.is_active else "❌ Неактивний"}

📞 <b>Контакти</b>
• Телефон: {updated_user.phone or "❌ Не вказано"}
• Telegram ID: <code>{updated_user.telegram_id}</code>

✅ Номер телефону успішно змінено!
"""
        
        await message.answer(
            text.strip(),
            reply_markup=get_profile_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )


@profile_router.message(ProfileStates.waiting_for_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    """Обробка текстового введення номера"""
    from app.modules.client.services.authentication.registration.handlers import normalize_phone_number
    
    normalized_phone = normalize_phone_number(message.text.strip())
    
    if not normalized_phone:
        await message.answer(
            "❌ Невірний формат номера телефону. Спробуйте ще раз:\n\n"
            "<i>Приклади правильних форматів:</i>\n"
            "• +380501234567\n"
            "• 380501234567\n"
            "• 0501234567",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    # Оновлюємо в БД
    user_id = message.chat.id if message.chat.type == "private" else message.from_user.id
    user = await db_manager.get_user_by_telegram_id(user_id)
    
    if user:
        await db_manager.update_user(user.id, {"phone": normalized_phone})
        await state.clear()
        
        # Отримуємо оновлені дані
        updated_user = await db_manager.get_user_by_telegram_id(user_id)
        
        text = f"""
👤 <b>Ваш профіль</b>

📋 <b>Основна інформація</b>
• Ім'я: {updated_user.first_name or '—'} {updated_user.last_name or ''}
• Роль: Покупець
• Статус: {"✅ Активний" if updated_user.is_active else "❌ Неактивний"}

📞 <b>Контакти</b>
• Телефон: {updated_user.phone or "❌ Не вказано"}
• Telegram ID: <code>{updated_user.telegram_id}</code>

✅ Номер телефону успішно змінено!
"""
        
        await message.answer(
            text.strip(),
            reply_markup=get_profile_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )


@profile_router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, state: FSMContext):
    """Повернення до профілю"""
    await callback.answer()
    await state.clear()
    await _render_profile(callback.from_user.id, callback.message)



