"""
Обробники для модуля реєстрації користувачів
"""

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
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
            "👋 <b>Вітаємо!</b>\n\n"
            "Для використання усіх можливостей бота, вам необхідно зареєструватися.\n\n"
            "📱 <b>Введіть свій номер телефону</b> нижче, або скористайтеся кнопкою 👇"
        )

        # Додаємо відладочний текст для власника навіть при реєстрації
        if is_founder:
            registration_text += f"\n\n🔑 <b>DEBUG:</b> Ви є власником бота (ID: {message.from_user.id})"
        
        logger.info(f"📝 Початок реєстрації для користувача {message.from_user.id}")
        
        # Спочатку видаляємо стару Reply keyboard (якщо є)
        await message.answer(
            "🔄 <b>Підготовка до реєстрації...</b>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=get_default_parse_mode(),
        )
        
        # Потім показуємо форму реєстрації
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
async def go_to_profile(callback: CallbackQuery, state: FSMContext):
    """Перехід до профілю з інлайн-меню"""
    await callback.answer()
    
    if state:
        try:
            await state.clear()
        except Exception:
            pass
    
    from app.modules.client.services.authentication.profile.handlers import (
        profile_command,
    )
    # Викликаємо існуючий показ профілю
    await profile_command(callback.message)


@router.callback_query(F.data == "client_help")
async def go_to_help(callback: CallbackQuery):
    await callback.answer()
    
    help_text = """
❓ <b>Довідка</b>

Коротко про головне:

🚛 <b>Каталог авто</b>
• Відкрийте каталог і гортайте авто ⬅️ ➡️
• Зберегти авто: натисніть <b>"❤️ Зберегти"</b>
• Поставити запитання: <b>"📝 Залишити заявку"</b> під карткою

📋 <b>Мої збережені</b>
• Тут ваші обрані авто
• Відкрийте картку, щоб переглянути або поділитися

💬 <b>Повідомлення</b>
• Натисніть <b>"📝 Залишити заявку"</b>
• Опишіть, що потрібно (бренд, рік, бюджет)
• Менеджер відповість у робочий час

🔎 <b>Швидкий пошук</b>
• Використовуйте фільтри (тип, рік, ціна)
• Перегляньте результати і збережіть цікаві авто

👤 <b>Профіль</b>
• Оновіть ім'я і телефон (важливо для зв'язку)

🏢 <b>Про компанію</b>
• Асортимент, фінансування, супровід, корисні посилання

📞 <b>Контакти</b>
• Телефон: +380502311339
• Telegram: @mtruck_sales
• Графік: Пн–Пт, 9:00–18:00

💡 <b>Порада:</b> Знайшли авто? Надішліть заявку — допоможемо з фінансуванням і оформленням.
"""
    
    await callback.message.edit_text(
        help_text.strip(),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")]
            ]
        ),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "client_back_to_main")
async def client_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Повернення до головного інлайн-меню клієнта"""
    await callback.answer()
    
    # Скидаємо стан, щоб вийти з можливих режимів редагування
    if state:
        try:
            await state.clear()
        except Exception:
            pass
    
    # Намагаємось edit, якщо не вийде - видаляємо та створюємо нове
    try:
        await callback.message.edit_text(
            "🏠 <b>Головне меню</b>\n\nОберіть розділ:",
            reply_markup=get_main_menu_inline_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
    except TelegramBadRequest:
        # Повідомлення має фото - видаляємо та створюємо нове
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer(
            "🏠 <b>Головне меню</b>\n\nОберіть розділ:",
            reply_markup=get_main_menu_inline_keyboard(),
            parse_mode=get_default_parse_mode(),
        )




@router.callback_query(RegistrationStates.waiting_for_phone)
async def block_callbacks_during_registration(callback: CallbackQuery):
    """Блокування callback кнопок під час реєстрації"""
    logger.warning(f"⚠️ Користувач {callback.from_user.id} намагається використати кнопки під час реєстрації")
    await callback.answer(
        "⚠️ Спочатку завершіть реєстрацію!",
        show_alert=True
    )
    await callback.message.answer(
        "📱 <b>Будь ласка, надішліть номер телефону</b>\n\n"
        "Використайте кнопку нижче або введіть номер вручну:",
        reply_markup=get_phone_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    """Обробка отримання номера телефону через контакт"""
    phone = message.contact.phone_number
    logger.info(f"📞 Користувач {message.from_user.id} поділився контактом: {phone}")
    
    # Нормалізуємо номер з контакту так само, як і ручний ввід
    normalized_phone = normalize_phone_number(phone)
    if not normalized_phone:
        await message.answer(
            "❌ <b>Невірний формат номера з контакту</b>\nСпробуйте ввести номер вручну.",
            reply_markup=get_phone_keyboard(),
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
    
    logger.info(f"📞 Користувач {message.from_user.id} надіслав текст: {phone[:20]}...")

    normalized_phone = normalize_phone_number(phone)
    if not normalized_phone:
        await message.answer(
            "❌ <b>Невірний формат номера</b>\n\n"
            "Приклади коректних форматів:\n"
            "• +380XXXXXXXXX\n"
            "• +38XXXXXXXXX\n"
            "• 380XXXXXXXXX\n"
            "• 38XXXXXXXXX\n"
            "• 0XXXXXXXXX",
            reply_markup=get_phone_keyboard(),
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
        logger.info(f"✅ Користувач {message.from_user.id} успішно зареєстрований! DB ID: {user_id}")

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
        logger.info(f"🏁 Реєстрація завершена для {message.from_user.id}")

    except Exception as e:
        logger.error(f"❌ Помилка реєстрації користувача {message.from_user.id}: {e}", exc_info=True)
        await message.answer(
            "❌ <b>Помилка при реєстрації.</b> Спробуйте ще раз пізніше.",
            parse_mode=get_default_parse_mode(),
        )
