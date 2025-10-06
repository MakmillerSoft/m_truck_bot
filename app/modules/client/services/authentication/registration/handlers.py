"""
Обробники для модуля реєстрації користувачів
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
import logging

from app.modules.database.manager import db_manager
from app.modules.database.models import UserModel, UserRole
from app.config.settings import settings
from app.utils.formatting import (
    WELCOME_MESSAGE,
    REGISTRATION_SUCCESS,
    PHONE_REQUEST_BUYER,
    get_default_parse_mode,
)
from .keyboards import (
    get_phone_keyboard,
    get_main_menu_inline_keyboard,
)
from .states import RegistrationStates

# Імпортуємо роутер з __init__.py
from . import registration_router as router

# Ініціалізація логера модуля
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Обробник команди /start"""
    # На старті очищаємо будь-які застарілі стани
    try:
        await state.clear()
    except Exception:
        pass
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    admin_ids = settings.get_admin_ids()
    is_admin = message.from_user.id in admin_ids
    is_founder = message.from_user.id in admin_ids  # Власник = адмін з .env

    if user:
        # Перевіряємо, чи потрібно оновити роль користувача на адміна
        if is_admin and user.role != UserRole.ADMIN:
            # Оновлюємо роль користувача на адміна
            await db_manager.update_user(user.id, {"role": UserRole.ADMIN})
            user.role = UserRole.ADMIN
        
        # Користувач вже зареєстрований
        welcome_text = f"""
🎉 <b>Вітаємо, {user.first_name}!</b> 👋

Раді бачити вас знову!
Використовуйте меню для навігації.
"""
        
        # Додаємо відладочний текст для адмінів/власника
        if is_founder:
            welcome_text += f"\n🔑 <b>DEBUG:</b> Ви є власником бота (ID: {message.from_user.id})"
        elif is_admin:
            welcome_text += f"\n👑 <b>DEBUG:</b> Ви є адміністратором (ID: {message.from_user.id})"
        
        await message.answer(
            welcome_text.strip(),
            reply_markup=get_main_menu_inline_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
    else:
        # Новий користувач — просимо номер телефону без інлайн кнопок
        registration_text = (
            "Для використання усіх можливостей бота, вам необхідно зареєструватися.\n"
            "Введіть свій номер телефону нижче, або скористайтеся кнопкою Поділитись номером телефону👇"
        )

        # Додаємо відладочний текст для власника навіть при реєстрації
        if is_founder:
            registration_text += f"\n\n🔑 <b>DEBUG:</b> Ви є власником бота (ID: {message.from_user.id})"

        await message.answer(
            registration_text,
            reply_markup=get_phone_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
        # Якщо це owner з .env — підготуємо роль ADMIN при створенні
        await state.update_data(role="admin" if is_admin else "buyer")
        await state.set_state(RegistrationStates.waiting_for_phone)


# Видалено інлайн кроки реєстрації: старт/ручний ввід/скасування — використовуємо лише текст + reply-клавіатуру


# Інлайн переходи з головного меню
@router.callback_query(F.data == "client_profile")
async def go_to_profile(callback: CallbackQuery):
    """Перехід до профілю з інлайн-меню"""
    await callback.answer()
    from app.modules.client.services.authentication.profile.handlers import (
        profile_command,
    )
    # Викликаємо існуючий показ профілю
    await profile_command(callback.message)


@router.callback_query(F.data == "client_help")
async def go_to_help(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🆘 <b>Допомога</b>\n\nВикористовуйте меню для навігації. Для повернення скористайтеся кнопками назад.",
        parse_mode=get_default_parse_mode(),
    )


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Обробка отримання номера телефону через контакт"""
    phone = message.contact.phone_number
    # Нормалізуємо номер з контакту так само, як і ручний ввід
    normalized_phone = normalize_phone_number(phone)
    if not normalized_phone:
        await message.answer(
            "❌ <b>Невірний формат номера з контакту</b>\nСпробуйте ввести номер вручну.",
            parse_mode=get_default_parse_mode(),
        )
        return
    await state.update_data(phone=normalized_phone)

    # Одразу завершуємо реєстрацію
    await complete_registration(message, state)


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    """Обробка номера телефону як текст із розширеною валідацією"""
    phone = message.text.strip()

    normalized_phone = normalize_phone_number(phone)
    if not normalized_phone:
        await message.answer(
            "❌ <b>Невірний формат номера</b>\n\n"
            "Приклади коректних форматів: +380XXXXXXXXX, +38XXXXXXXXX, 380XXXXXXXXX, 38XXXXXXXXX, 0XXXXXXXXX",
            parse_mode=get_default_parse_mode(),
        )
        return

    await state.update_data(phone=normalized_phone)

    # Одразу завершуємо реєстрацію
    await complete_registration(message, state)


@router.message(RegistrationStates.waiting_for_phone_manual)
async def process_phone_manual(message: Message, state: FSMContext):
    """Обробка ручного вводу номера телефону з розширеною валідацією"""
    phone = message.text.strip()
    
    # Нормалізуємо номер телефону
    normalized_phone = normalize_phone_number(phone)
    
    if not normalized_phone:
        await message.answer(
            "❌ <b>Невірний формат номера</b>\n\n"
            "Приймаються формати:\n"
            "• +380XXXXXXXXX\n"
            "• +38XXXXXXXXX\n"
            "• 380XXXXXXXXX\n"
            "• 38XXXXXXXXX\n"
            "• 0XXXXXXXXX\n\n"
            "Спробуйте ще раз:",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    await state.update_data(phone=normalized_phone)
    
    # Показуємо підтвердження
    await message.answer(
        f"✅ <b>Номер підтверджено</b>\n\n"
        f"📱 <b>Ваш номер:</b> {normalized_phone}\n\n"
        f"Завершуємо реєстрацію...",
        parse_mode=get_default_parse_mode(),
    )
    
    # Завершуємо реєстрацію
    await complete_registration(message, state)


def normalize_phone_number(phone: str) -> str:
    """Нормалізація номера телефону до формату +380XXXXXXXXX"""
    # Видаляємо всі символи крім цифр та +
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Видаляємо + якщо є
    digits_only = cleaned.replace('+', '')
    
    # Обробляємо різні формати
    if digits_only.startswith('380') and len(digits_only) == 12:
        # 380XXXXXXXXX -> +380XXXXXXXXX
        return '+' + digits_only
    elif digits_only.startswith('38') and len(digits_only) == 11:
        # 38XXXXXXXXX -> +380XXXXXXXXX
        return '+380' + digits_only[2:]  # Виправлено: +380 + решта цифр
    elif digits_only.startswith('0') and len(digits_only) == 10:
        # 0XXXXXXXXX -> +380XXXXXXXXX
        return '+380' + digits_only[1:]  # Виправлено: +380 + решта цифр
    elif cleaned.startswith('+380') and len(digits_only) == 12:
        # +380XXXXXXXXX -> +380XXXXXXXXX
        return '+' + digits_only
    elif cleaned.startswith('+38') and len(digits_only) == 11:
        # +38XXXXXXXXX -> +380XXXXXXXXX
        return '+380' + digits_only[2:]  # Виправлено: +380 + решта цифр
    
    return None


async def complete_registration(message: Message, state: FSMContext):
    """Завершення реєстрації"""
    data = await state.get_data()
    
    # Перевіряємо, чи це адміністратор
    admin_ids = settings.get_admin_ids()
    is_admin = message.from_user.id in admin_ids
    is_founder = message.from_user.id in admin_ids  # Власник = адмін з .env
    
    # Визначаємо роль користувача
    user_role = UserRole.ADMIN if is_admin else UserRole(data["role"])

    user = UserModel(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        phone=data["phone"],
        role=user_role,
    )

    try:
        user_id = await db_manager.create_user(user)

        success_message = REGISTRATION_SUCCESS.format(phone=data["phone"])
        
        # Додаємо повідомлення про роль адміна/власника
        if is_founder:
            success_message += f"\n\n🔑 <b>Вам автоматично присвоєно роль власника бота!</b>"
            success_message += f"\n🔍 <b>DEBUG:</b> Ви є власником (ID: {message.from_user.id})"
        elif is_admin:
            success_message += f"\n\n👑 <b>Вам автоматично присвоєно роль адміністратора!</b>"
            success_message += f"\n🔍 <b>DEBUG:</b> Ви є адміністратором (ID: {message.from_user.id})"

        await message.answer(
            success_message,
            reply_markup=get_main_menu_inline_keyboard(),
            parse_mode=get_default_parse_mode(),
        )

        await state.clear()

    except Exception as e:
        logger.error(f"❌ Помилка реєстрації користувача {message.from_user.id}: {e}")
        await message.answer(
            "❌ <b>Помилка при реєстрації.</b> Спробуйте ще раз пізніше.",
            parse_mode=get_default_parse_mode(),
        )
