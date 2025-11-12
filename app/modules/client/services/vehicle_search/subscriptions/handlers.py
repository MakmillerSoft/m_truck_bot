"""
Обробники для підписок на авто
"""
import logging
from datetime import datetime
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.utils.formatting import get_default_parse_mode
from app.modules.database.manager import db_manager
from .states import SubscriptionStates
from .keyboards import (
    get_subscriptions_main_keyboard,
    get_vehicle_type_keyboard,
    get_condition_keyboard,
    get_skip_back_keyboard,
    get_confirmation_keyboard,
    get_subscriptions_list_keyboard,
    get_subscription_detail_keyboard,
    get_delete_confirmation_keyboard,
)
from . import subscriptions_router as router

logger = logging.getLogger(__name__)

# Мапінг типів авто
VEHICLE_TYPE_MAP = {
    # 4 об'єднані категорії → представницькі значення EN
    "sub_type_tractors_and_semi": "saddle_tractor",
    "sub_type_vans_and_refrigerators": "van",
    "sub_type_variable_body": "variable_body",
    "sub_type_container_carriers": "container_carrier",
}

VEHICLE_TYPE_NAMES = {
    "saddle_tractor": "Сідельні тягачі та напівпричепи",
    "van": "Вантажні фургони та рефрижератори",
    "variable_body": "Змінні кузови",
    "container_carrier": "Контейнеровози (з причепами)",
}

# Мапінг станів
CONDITION_MAP = {
    "sub_cond_new": "new",
    "sub_cond_used": "used",
}

CONDITION_NAMES = {
    "new": "Новий",
    "used": "Вживаний",
}


@router.callback_query(F.data == "client_subscriptions")
async def show_subscriptions_menu(callback: CallbackQuery):
    """Показати меню підписок"""
    await callback.answer()
    
    text = """
🔔 <b>Підписки на авто</b>

📬 <b>Як це працює:</b>
• Створіть підписку з вашими критеріями пошуку
• Коли з'явиться підходяще авто - ми надішлемо сповіщення
• Ви завжди будете в курсі нових надходжень!

💡 <b>Можна вказати:</b>
• Тип авто (тягач, вантажівка, автобус і т.д.)
• Бренд (Volvo, Mercedes, MAN і т.д.)
• Рік випуску (від - до)
• Ціна (від - до)
• Стан (новий, вживаний)

<i>Створіть підписку прямо зараз!</i>
"""
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_subscriptions_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_subscriptions_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data == "create_subscription")
async def start_create_subscription(callback: CallbackQuery, state: FSMContext):
    """Почати створення підписки"""
    await callback.answer()
    
    # Очищаємо попередній стан
    await state.clear()
    
    # Ініціалізуємо дані підписки
    await state.update_data(subscription_params={})
    
    text = """
📝 <b>Створення підписки</b>

<b>Крок 1 з 6: Назва підписки</b>

Придумайте назву для підписки, щоб легко її впізнати.

<i>Наприклад: "Volvo тягач до $30000" або "Новий автобус 2020+"</i>

💬 <b>Напишіть назву:</b>
"""
    
    await state.set_state(SubscriptionStates.waiting_for_subscription_name)
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_name", "cancel_subscription"),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_name", "cancel_subscription"),
            parse_mode=get_default_parse_mode(),
        )


@router.message(SubscriptionStates.waiting_for_subscription_name, F.text)
async def process_subscription_name(message: Message, state: FSMContext):
    """Обробка назви підписки"""
    subscription_name = message.text.strip()
    
    if len(subscription_name) < 3:
        await message.answer(
            "❌ Назва занадто коротка. Введіть мінімум 3 символи:",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    params['subscription_name'] = subscription_name
    await state.update_data(subscription_params=params)
    
    # Переходимо до вибору типу авто
    await ask_vehicle_type(message, state)


@router.callback_query(F.data == "sub_skip_name")
async def skip_subscription_name(callback: CallbackQuery, state: FSMContext):
    """Пропустити назву підписки"""
    await callback.answer()
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    params['subscription_name'] = "Моя підписка"
    await state.update_data(subscription_params=params)
    
    await ask_vehicle_type_callback(callback, state)


async def ask_vehicle_type(message: Message, state: FSMContext):
    """Запитати тип авто"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 2 з 6: Тип авто</b>

Оберіть тип авто або пропустіть цей крок:
"""
    
    await message.answer(
        text.strip(),
        reply_markup=get_vehicle_type_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


async def ask_vehicle_type_callback(callback: CallbackQuery, state: FSMContext):
    """Запитати тип авто (callback версія)"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 2 з 6: Тип авто</b>

Оберіть тип авто або пропустіть цей крок:
"""
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_vehicle_type_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_vehicle_type_keyboard(),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data.startswith("sub_type_"))
async def process_vehicle_type(callback: CallbackQuery, state: FSMContext):
    """Обробка типу авто"""
    await callback.answer()
    
    vehicle_type = VEHICLE_TYPE_MAP.get(callback.data)
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    params['vehicle_type'] = vehicle_type
    await state.update_data(subscription_params=params)
    
    await ask_brand(callback, state)


@router.callback_query(F.data == "sub_skip_type")
async def skip_vehicle_type(callback: CallbackQuery, state: FSMContext):
    """Пропустити тип авто"""
    await callback.answer()
    await ask_brand(callback, state)


async def ask_brand(callback: CallbackQuery, state: FSMContext):
    """Запитати бренд"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 3 з 7: Бренд</b>

Напишіть бренд авто (наприклад: Volvo, Mercedes, MAN)
або пропустіть цей крок:
"""
    
    await state.set_state(SubscriptionStates.waiting_for_brand)
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_brand", "sub_back_to_type"),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_brand", "sub_back_to_type"),
            parse_mode=get_default_parse_mode(),
        )


@router.message(SubscriptionStates.waiting_for_brand, F.text)
async def process_brand(message: Message, state: FSMContext):
    """Обробка бренду"""
    brand = message.text.strip()
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    params['brand'] = brand
    await state.update_data(subscription_params=params)
    
    await ask_min_year(message, state)


@router.callback_query(F.data == "sub_skip_brand")
async def skip_brand(callback: CallbackQuery, state: FSMContext):
    """Пропустити бренд"""
    await callback.answer()
    await ask_min_year_callback(callback, state)


async def ask_min_year(message: Message, state: FSMContext):
    """Запитати мінімальний рік"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 4 з 7: Рік випуску (мінімальний)</b>

Напишіть мінімальний рік випуску (наприклад: 2015)
або пропустіть цей крок:
"""
    
    await state.set_state(SubscriptionStates.waiting_for_min_year)
    
    await message.answer(
        text.strip(),
        reply_markup=get_skip_back_keyboard("sub_skip_min_year", "sub_back_to_brand"),
        parse_mode=get_default_parse_mode(),
    )


async def ask_min_year_callback(callback: CallbackQuery, state: FSMContext):
    """Запитати мінімальний рік (callback версія)"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 4 з 7: Рік випуску (мінімальний)</b>

Напишіть мінімальний рік випуску (наприклад: 2015)
або пропустіть цей крок:
"""
    
    await state.set_state(SubscriptionStates.waiting_for_min_year)
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_min_year", "sub_back_to_brand"),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_min_year", "sub_back_to_brand"),
            parse_mode=get_default_parse_mode(),
        )


@router.message(SubscriptionStates.waiting_for_min_year, F.text)
async def process_min_year(message: Message, state: FSMContext):
    """Обробка мінімального року"""
    current_year = datetime.now().year
    
    try:
        min_year = int(message.text.strip())
        if min_year < 1980 or min_year > current_year + 1:
            raise ValueError
    except ValueError:
        await message.answer(
            f"❌ Введіть коректний рік (1980-{current_year + 1}):",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    params['min_year'] = min_year
    await state.update_data(subscription_params=params)
    
    await ask_max_year(message, state)


@router.callback_query(F.data == "sub_skip_min_year")
async def skip_min_year(callback: CallbackQuery, state: FSMContext):
    """Пропустити мінімальний рік"""
    await callback.answer()
    await ask_max_year_callback(callback, state)


async def ask_max_year(message: Message, state: FSMContext):
    """Запитати максимальний рік"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 5 з 7: Рік випуску (максимальний)</b>

Напишіть максимальний рік випуску (наприклад: 2023)
або пропустіть цей крок:
"""
    
    await state.set_state(SubscriptionStates.waiting_for_max_year)
    
    await message.answer(
        text.strip(),
        reply_markup=get_skip_back_keyboard("sub_skip_max_year", "sub_back_to_min_year"),
        parse_mode=get_default_parse_mode(),
    )


async def ask_max_year_callback(callback: CallbackQuery, state: FSMContext):
    """Запитати максимальний рік (callback версія)"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 5 з 7: Рік випуску (максимальний)</b>

Напишіть максимальний рік випуску (наприклад: 2023)
або пропустіть цей крок:
"""
    
    await state.set_state(SubscriptionStates.waiting_for_max_year)
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_max_year", "sub_back_to_min_year"),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_max_year", "sub_back_to_min_year"),
            parse_mode=get_default_parse_mode(),
        )


@router.message(SubscriptionStates.waiting_for_max_year, F.text)
async def process_max_year(message: Message, state: FSMContext):
    """Обробка максимального року"""
    current_year = datetime.now().year
    
    try:
        max_year = int(message.text.strip())
        if max_year < 1980 or max_year > current_year + 1:
            raise ValueError
    except ValueError:
        await message.answer(
            f"❌ Введіть коректний рік (1980-{current_year + 1}):",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    
    # Перевіряємо що max_year >= min_year
    if params.get('min_year') and max_year < params['min_year']:
        await message.answer(
            f"❌ Максимальний рік не може бути менше мінімального ({params['min_year']}):",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    params['max_year'] = max_year
    await state.update_data(subscription_params=params)
    
    await ask_min_price(message, state)


@router.callback_query(F.data == "sub_skip_max_year")
async def skip_max_year(callback: CallbackQuery, state: FSMContext):
    """Пропустити максимальний рік"""
    await callback.answer()
    await ask_min_price_callback(callback, state)


async def ask_min_price(message: Message, state: FSMContext):
    """Запитати мінімальну ціну"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 6 з 7: Ціна (мінімальна)</b>

Напишіть мінімальну ціну в доларах (наприклад: 15000)
або пропустіть цей крок:
"""
    
    await state.set_state(SubscriptionStates.waiting_for_min_price)
    
    await message.answer(
        text.strip(),
        reply_markup=get_skip_back_keyboard("sub_skip_min_price", "sub_back_to_max_year"),
        parse_mode=get_default_parse_mode(),
    )


async def ask_min_price_callback(callback: CallbackQuery, state: FSMContext):
    """Запитати мінімальну ціну (callback версія)"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 6 з 7: Ціна (мінімальна)</b>

Напишіть мінімальну ціну в доларах (наприклад: 15000)
або пропустіть цей крок:
"""
    
    await state.set_state(SubscriptionStates.waiting_for_min_price)
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_min_price", "sub_back_to_max_year"),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_min_price", "sub_back_to_max_year"),
            parse_mode=get_default_parse_mode(),
        )


@router.message(SubscriptionStates.waiting_for_min_price, F.text)
async def process_min_price(message: Message, state: FSMContext):
    """Обробка мінімальної ціни"""
    try:
        min_price = float(message.text.strip())
        if min_price < 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Введіть коректну ціну (число більше 0):",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    params['min_price'] = min_price
    await state.update_data(subscription_params=params)
    
    await ask_max_price(message, state)


@router.callback_query(F.data == "sub_skip_min_price")
async def skip_min_price(callback: CallbackQuery, state: FSMContext):
    """Пропустити мінімальну ціну"""
    await callback.answer()
    await ask_max_price_callback(callback, state)


async def ask_max_price(message: Message, state: FSMContext):
    """Запитати максимальну ціну"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 7 з 7: Ціна (максимальна)</b>

Напишіть максимальну ціну в доларах (наприклад: 35000)
або пропустіть цей крок:
"""
    
    await state.set_state(SubscriptionStates.waiting_for_max_price)
    
    await message.answer(
        text.strip(),
        reply_markup=get_skip_back_keyboard("sub_skip_max_price", "sub_back_to_min_price"),
        parse_mode=get_default_parse_mode(),
    )


async def ask_max_price_callback(callback: CallbackQuery, state: FSMContext):
    """Запитати максимальну ціну (callback версія)"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 7 з 7: Ціна (максимальна)</b>

Напишіть максимальну ціну в доларах (наприклад: 35000)
або пропустіть цей крок:
"""
    
    await state.set_state(SubscriptionStates.waiting_for_max_price)
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_max_price", "sub_back_to_min_price"),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_skip_back_keyboard("sub_skip_max_price", "sub_back_to_min_price"),
            parse_mode=get_default_parse_mode(),
        )


@router.message(SubscriptionStates.waiting_for_max_price, F.text)
async def process_max_price(message: Message, state: FSMContext):
    """Обробка максимальної ціни"""
    try:
        max_price = float(message.text.strip())
        if max_price < 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Введіть коректну ціну (число більше 0):",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    
    # Перевіряємо що max_price >= min_price
    if params.get('min_price') and max_price < params['min_price']:
        await message.answer(
            f"❌ Максимальна ціна не може бути менше мінімальної (${params['min_price']:,.0f}):",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    params['max_price'] = max_price
    await state.update_data(subscription_params=params)
    
    await ask_condition(message, state)


@router.callback_query(F.data == "sub_skip_max_price")
async def skip_max_price(callback: CallbackQuery, state: FSMContext):
    """Пропустити максимальну ціну"""
    await callback.answer()
    await ask_condition_callback(callback, state)


async def ask_condition(message: Message, state: FSMContext):
    """Запитати стан авто"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 8 з 8: Стан авто</b>

Оберіть стан авто або пропустіть цей крок:
"""
    
    await message.answer(
        text.strip(),
        reply_markup=get_condition_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


async def ask_condition_callback(callback: CallbackQuery, state: FSMContext):
    """Запитати стан авто (callback версія)"""
    text = """
📝 <b>Створення підписки</b>

<b>Крок 8 з 8: Стан авто</b>

Оберіть стан авто або пропустіть цей крок:
"""
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_condition_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_condition_keyboard(),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data.startswith("sub_cond_"))
async def process_condition(callback: CallbackQuery, state: FSMContext):
    """Обробка стану авто"""
    await callback.answer()
    
    condition = CONDITION_MAP.get(callback.data)
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    params['condition'] = condition
    await state.update_data(subscription_params=params)
    
    await show_confirmation_callback(callback, state)


@router.callback_query(F.data == "sub_skip_condition")
async def skip_condition(callback: CallbackQuery, state: FSMContext):
    """Пропустити стан авто"""
    await callback.answer()
    await show_confirmation_callback(callback, state)


async def show_confirmation(message: Message, state: FSMContext):
    """Показати підтвердження створення"""
    data = await state.get_data()
    params = data.get('subscription_params', {})
    
    text = "✅ <b>Підтвердження створення підписки</b>\n\n"
    text += f"📝 <b>Назва:</b> {params.get('subscription_name', 'Не вказано')}\n"
    
    if params.get('vehicle_type'):
        text += f"🚛 <b>Тип:</b> {VEHICLE_TYPE_NAMES.get(params['vehicle_type'], params['vehicle_type'])}\n"
    
    if params.get('brand'):
        text += f"🏭 <b>Бренд:</b> {params['brand']}\n"
    
    if params.get('min_year') or params.get('max_year'):
        year_range = ""
        if params.get('min_year'):
            year_range += f"від {params['min_year']}"
        if params.get('max_year'):
            if year_range:
                year_range += f" до {params['max_year']}"
            else:
                year_range += f"до {params['max_year']}"
        text += f"📅 <b>Рік:</b> {year_range}\n"
    
    if params.get('min_price') or params.get('max_price'):
        price_range = ""
        if params.get('min_price'):
            price_range += f"від ${params['min_price']:,.0f}"
        if params.get('max_price'):
            if price_range:
                price_range += f" до ${params['max_price']:,.0f}"
            else:
                price_range += f"до ${params['max_price']:,.0f}"
        text += f"💰 <b>Ціна:</b> {price_range}\n"
    
    if params.get('condition'):
        text += f"✨ <b>Стан:</b> {CONDITION_NAMES.get(params['condition'], params['condition'])}\n"
    
    text += "\n<i>Натисніть кнопку нижче щоб створити підписку</i>"
    
    await message.answer(
        text.strip(),
        reply_markup=get_confirmation_keyboard(),
        parse_mode=get_default_parse_mode(),
    )


async def show_confirmation_callback(callback: CallbackQuery, state: FSMContext):
    """Показати підтвердження створення (callback версія)"""
    data = await state.get_data()
    params = data.get('subscription_params', {})
    
    text = "✅ <b>Підтвердження створення підписки</b>\n\n"
    text += f"📝 <b>Назва:</b> {params.get('subscription_name', 'Не вказано')}\n"
    
    if params.get('vehicle_type'):
        text += f"🚛 <b>Тип:</b> {VEHICLE_TYPE_NAMES.get(params['vehicle_type'], params['vehicle_type'])}\n"
    
    if params.get('brand'):
        text += f"🏭 <b>Бренд:</b> {params['brand']}\n"
    
    if params.get('min_year') or params.get('max_year'):
        year_range = ""
        if params.get('min_year'):
            year_range += f"від {params['min_year']}"
        if params.get('max_year'):
            if year_range:
                year_range += f" до {params['max_year']}"
            else:
                year_range += f"до {params['max_year']}"
        text += f"📅 <b>Рік:</b> {year_range}\n"
    
    if params.get('min_price') or params.get('max_price'):
        price_range = ""
        if params.get('min_price'):
            price_range += f"від ${params['min_price']:,.0f}"
        if params.get('max_price'):
            if price_range:
                price_range += f" до ${params['max_price']:,.0f}"
            else:
                price_range += f"до ${params['max_price']:,.0f}"
        text += f"💰 <b>Ціна:</b> {price_range}\n"
    
    if params.get('condition'):
        text += f"✨ <b>Стан:</b> {CONDITION_NAMES.get(params['condition'], params['condition'])}\n"
    
    text += "\n<i>Натисніть кнопку нижче щоб створити підписку</i>"
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_confirmation_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_confirmation_keyboard(),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data == "confirm_subscription")
async def confirm_subscription(callback: CallbackQuery, state: FSMContext):
    """Підтвердити та створити підписку"""
    await callback.answer()
    
    data = await state.get_data()
    params = data.get('subscription_params', {})
    
    # Отримуємо користувача
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ Помилка: користувач не знайдений.",
            parse_mode=get_default_parse_mode(),
        )
        await state.clear()
        return
    
    # Створюємо підписку
    try:
        subscription_id = await db_manager.create_subscription(
            user_id=user.id,
            subscription_name=params.get('subscription_name', 'Моя підписка'),
            search_params=params
        )
        
        await state.clear()
        
        text = """
✅ <b>Підписку успішно створено!</b>

🔔 Ви отримаєте сповіщення, коли з'явиться авто за вашими критеріями.

Керувати підписками можна в меню "🔔 Підписки"
"""
        
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_subscriptions_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
        
    except Exception as e:
        logger.error(f"Помилка створення підписки: {e}")
        await callback.message.edit_text(
            "❌ Помилка при створенні підписки. Спробуйте пізніше.",
            reply_markup=get_subscriptions_main_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
        await state.clear()


@router.callback_query(F.data == "cancel_subscription")
async def cancel_subscription(callback: CallbackQuery, state: FSMContext):
    """Скасувати створення підписки"""
    await callback.answer("Створення підписки скасовано")
    await state.clear()
    
    await show_subscriptions_menu(callback)


@router.callback_query(F.data == "view_subscriptions")
async def view_subscriptions(callback: CallbackQuery):
    """Переглянути список підписок"""
    await callback.answer()
    
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Користувач не знайдений", show_alert=True)
        return
    
    subscriptions = await db_manager.get_user_subscriptions(user.id)
    
    text = f"📋 <b>Мої підписки</b>\n\n"
    
    if subscriptions:
        text += f"📊 Всього підписок: {len(subscriptions)}\n"
        active_count = sum(1 for s in subscriptions if s.get('is_active'))
        text += f"🟢 Активних: {active_count}\n"
        text += f"🔴 Неактивних: {len(subscriptions) - active_count}\n\n"
        text += "<i>Оберіть підписку зі списку нижче:</i>"
    else:
        text += "❌ У вас ще немає підписок.\n\n"
        text += "<i>Створіть першу підписку, щоб отримувати сповіщення про нові авто!</i>"
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_subscriptions_list_keyboard(subscriptions),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_subscriptions_list_keyboard(subscriptions),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data.startswith("view_sub_"))
async def view_subscription_detail(callback: CallbackQuery):
    """Переглянути деталі підписки"""
    await callback.answer()
    
    subscription_id = int(callback.data.split("_")[2])
    
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Користувач не знайдений", show_alert=True)
        return
    
    subscriptions = await db_manager.get_user_subscriptions(user.id)
    subscription = next((s for s in subscriptions if s['id'] == subscription_id), None)
    
    if not subscription:
        await callback.answer("❌ Підписка не знайдена", show_alert=True)
        return
    
    status_emoji = "🟢 Активна" if subscription.get('is_active') else "🔴 Неактивна"
    
    text = f"📋 <b>Деталі підписки</b>\n\n"
    text += f"📝 <b>Назва:</b> {subscription.get('subscription_name', 'Не вказано')}\n"
    text += f"📊 <b>Статус:</b> {status_emoji}\n\n"
    text += "<b>Критерії пошуку:</b>\n"
    
    if subscription.get('vehicle_type'):
        text += f"🚛 Тип: {VEHICLE_TYPE_NAMES.get(subscription['vehicle_type'], subscription['vehicle_type'])}\n"
    
    if subscription.get('brand'):
        text += f"🏭 Бренд: {subscription['brand']}\n"
    
    if subscription.get('min_year') or subscription.get('max_year'):
        year_range = ""
        if subscription.get('min_year'):
            year_range += f"від {subscription['min_year']}"
        if subscription.get('max_year'):
            if year_range:
                year_range += f" до {subscription['max_year']}"
            else:
                year_range += f"до {subscription['max_year']}"
        text += f"📅 Рік: {year_range}\n"
    
    if subscription.get('min_price') or subscription.get('max_price'):
        price_range = ""
        if subscription.get('min_price'):
            price_range += f"від ${subscription['min_price']:,.0f}"
        if subscription.get('max_price'):
            if price_range:
                price_range += f" до ${subscription['max_price']:,.0f}"
            else:
                price_range += f"до ${subscription['max_price']:,.0f}"
        text += f"💰 Ціна: {price_range}\n"
    
    if subscription.get('condition'):
        text += f"✨ Стан: {CONDITION_NAMES.get(subscription['condition'], subscription['condition'])}\n"
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_subscription_detail_keyboard(subscription_id, subscription.get('is_active', True)),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_subscription_detail_keyboard(subscription_id, subscription.get('is_active', True)),
            parse_mode=get_default_parse_mode(),
        )


# ===== ОБРОБНИКИ КНОПОК "НАЗАД" =====

@router.callback_query(F.data == "sub_back_to_name")
async def back_to_name(callback: CallbackQuery, state: FSMContext):
    """Повернутися до введення назви"""
    await callback.answer()
    await start_create_subscription(callback, state)


@router.callback_query(F.data == "sub_back_to_type")
async def back_to_type(callback: CallbackQuery, state: FSMContext):
    """Повернутися до вибору типу"""
    await callback.answer()
    await ask_vehicle_type_callback(callback, state)


@router.callback_query(F.data == "sub_back_to_brand")
async def back_to_brand(callback: CallbackQuery, state: FSMContext):
    """Повернутися до введення бренду"""
    await callback.answer()
    await ask_brand(callback, state)


@router.callback_query(F.data == "sub_back_to_min_year")
async def back_to_min_year(callback: CallbackQuery, state: FSMContext):
    """Повернутися до введення мінімального року"""
    await callback.answer()
    await ask_min_year_callback(callback, state)


@router.callback_query(F.data == "sub_back_to_max_year")
async def back_to_max_year(callback: CallbackQuery, state: FSMContext):
    """Повернутися до введення максимального року"""
    await callback.answer()
    await ask_max_year_callback(callback, state)


@router.callback_query(F.data == "sub_back_to_min_price")
async def back_to_min_price(callback: CallbackQuery, state: FSMContext):
    """Повернутися до введення мінімальної ціни"""
    await callback.answer()
    await ask_min_price_callback(callback, state)


@router.callback_query(F.data == "sub_back_to_max_price")
async def back_to_max_price(callback: CallbackQuery, state: FSMContext):
    """Повернутися до введення максимальної ціни"""
    await callback.answer()
    await ask_max_price_callback(callback, state)


@router.callback_query(F.data == "sub_back_to_condition")
async def back_to_condition(callback: CallbackQuery, state: FSMContext):
    """Повернутися до вибору стану"""
    await callback.answer()
    await ask_condition_callback(callback, state)


# ===== КІНЕЦЬ ОБРОБНИКІВ "НАЗАД" =====

@router.callback_query(F.data.startswith("toggle_sub_"))
async def toggle_subscription(callback: CallbackQuery):
    """Перемкнути статус підписки"""
    subscription_id = int(callback.data.split("_")[2])
    
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Користувач не знайдений", show_alert=True)
        return
    
    subscriptions = await db_manager.get_user_subscriptions(user.id)
    subscription = next((s for s in subscriptions if s['id'] == subscription_id), None)
    
    if not subscription:
        await callback.answer("❌ Підписка не знайдена", show_alert=True)
        return
    
    # Перемикаємо статус
    new_status = not subscription.get('is_active', True)
    await db_manager.update_subscription_status(subscription_id, new_status)
    
    status_text = "активовано" if new_status else "призупинено"
    await callback.answer(f"✅ Підписку {status_text}", show_alert=True)
    
    # Оновлюємо відображення
    await view_subscription_detail(callback)


@router.callback_query(F.data.startswith("delete_sub_"))
async def ask_delete_confirmation(callback: CallbackQuery):
    """Запитати підтвердження видалення"""
    await callback.answer()
    
    subscription_id = int(callback.data.split("_")[2])
    
    text = """
⚠️ <b>Видалення підписки</b>

Ви впевнені, що хочете видалити цю підписку?

<i>Цю дію неможливо скасувати.</i>
"""
    
    try:
        await callback.message.edit_text(
            text.strip(),
            reply_markup=get_delete_confirmation_keyboard(subscription_id),
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        await callback.message.answer(
            text.strip(),
            reply_markup=get_delete_confirmation_keyboard(subscription_id),
            parse_mode=get_default_parse_mode(),
        )


@router.callback_query(F.data.startswith("confirm_delete_sub_"))
async def confirm_delete_subscription(callback: CallbackQuery):
    """Підтвердити видалення підписки"""
    await callback.answer()
    
    subscription_id = int(callback.data.split("_")[3])
    
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Користувач не знайдений", show_alert=True)
        return
    
    try:
        await db_manager.delete_subscription(user.id, subscription_id)
        await callback.answer("✅ Підписку видалено", show_alert=True)
        
        # Повертаємось до списку підписок
        await view_subscriptions(callback)
        
    except Exception as e:
        logger.error(f"Помилка видалення підписки: {e}")
        await callback.answer("❌ Помилка видалення підписки", show_alert=True)
