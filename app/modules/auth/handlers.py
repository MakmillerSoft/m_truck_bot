"""
Обробники команд аутентифікації
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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
    get_registration_keyboard,
    get_phone_keyboard,
    get_main_menu_keyboard,
    get_profile_keyboard,
)


router = Router()


class RegistrationStates(StatesGroup):
    """Стани реєстрації"""

    waiting_for_phone = State()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Обробник команди /start"""
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)

    if user:
        # Перевіряємо, чи потрібно оновити роль користувача на адміна
        admin_ids = settings.get_admin_ids()
        is_admin = message.from_user.id in admin_ids
        
        if is_admin and user.role != UserRole.ADMIN:
            # Оновлюємо роль користувача на адміна
            await db_manager.update_user(user.id, {"role": UserRole.ADMIN})
            user.role = UserRole.ADMIN
        
        # Користувач вже зареєстрований
        welcome_text = f"""
🎉 <b>Вітаємо, {user.first_name}!</b> 👋

Раді бачити вас знову!
Використовуйте /help для перегляду доступних команд.
"""
        await message.answer(
            welcome_text.strip(),
            reply_markup=get_main_menu_keyboard(
                user.role.value
            ),
            parse_mode=get_default_parse_mode(),
        )
    else:
        # Новий користувач - одразу реєстрація як покупець
        await message.answer(
            WELCOME_MESSAGE.strip(),
            reply_markup=get_phone_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
        # Зберігаємо роль buyer автоматично
        await state.update_data(role="buyer")
        await state.set_state(RegistrationStates.waiting_for_phone)


# Видалений обробник вибору ролі - всі користувачі автоматично buyers


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Обробка отримання номера телефону через контакт"""
    phone = message.contact.phone_number
    await state.update_data(phone=phone)

    # Одразу завершуємо реєстрацію
    await complete_registration(message, state)


@router.message(RegistrationStates.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    """Обробка номера телефону як текст"""
    phone = message.text.strip()

    if not phone.startswith("+"):
        await message.answer("❌ Будь ласка, введіть номер у форматі +380XXXXXXXXX")
        return

    await state.update_data(phone=phone)

    # Одразу завершуємо реєстрацію
    await complete_registration(message, state)


async def complete_registration(message: Message, state: FSMContext):
    """Завершення реєстрації"""
    data = await state.get_data()
    
    # Перевіряємо, чи це адміністратор
    admin_ids = settings.get_admin_ids()
    is_admin = message.from_user.id in admin_ids
    
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
        
        # Додаємо повідомлення про роль адміна
        if is_admin:
            success_message += "\n\n🔑 <b>Вам автоматично присвоєно роль адміністратора!</b>"

        await message.answer(
            success_message,
            reply_markup=get_main_menu_keyboard(
                user_role.value
            ),
            parse_mode=get_default_parse_mode(),
        )

        await state.clear()

    except Exception as e:
        await message.answer(
            "❌ <b>Помилка при реєстрації.</b> Спробуйте ще раз пізніше.",
            parse_mode=get_default_parse_mode(),
        )


@router.message(Command("profile"))
async def show_profile(message: Message):
    """Показати профіль користувача"""
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(
            "❌ <b>Ви не зареєстровані.</b> Використовуйте /start для реєстрації.",
            parse_mode=get_default_parse_mode(),
        )
        return

    profile_text = f"""
👤 <b>Ваш профіль</b>

🆔 <b>ID:</b> {user.id}
📱 <b>Ім'я:</b> {user.first_name} {user.last_name or ''}
📞 <b>Телефон:</b> {user.phone}
✅ <b>Верифікований:</b> {'Так' if user.is_verified else 'Ні'}
📅 <b>Дата реєстрації:</b> {user.created_at.strftime('%d.%m.%Y')}
"""

    await message.answer(
        profile_text.strip(),
        reply_markup=get_profile_keyboard(),
        parse_mode=get_default_parse_mode(),
    )
