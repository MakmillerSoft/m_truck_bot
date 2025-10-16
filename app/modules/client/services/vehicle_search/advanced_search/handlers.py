"""
Клієнтський розширений пошук: роки, ціна, VIN, ID, марка+модель
"""
import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from . import advanced_search_router as router
from app.modules.database.manager import DatabaseManager
from ..quick_search.handlers import show_vehicle_card_message

logger = logging.getLogger(__name__)
db_manager = DatabaseManager()


class ClientSearchStates(StatesGroup):
    """Стани для пошуку клієнта"""
    waiting_for_brand = State()
    waiting_for_model = State()
    waiting_for_year_from = State()
    waiting_for_year_to = State()
    waiting_for_price_from = State()
    waiting_for_price_to = State()
    waiting_for_vin = State()
    waiting_for_id = State()


# ===== Марка + Модель (послідовно) =====
@router.callback_query(F.data == "client_advanced_search")
async def client_search_start(callback: CallbackQuery, state: FSMContext):
    """Крок 1: Запит марки авто"""
    await callback.answer()
    try:
        text = """🏷️ <b>Пошук авто</b>

<b>Крок 1 з 2:</b> Введіть марку авто

<i>Наприклад: Mercedes, Volvo, Scania, MAN</i>"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="client_search")]]
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await state.set_state(ClientSearchStates.waiting_for_brand)
        
        logger.info(f"🏷️ Клієнт {callback.from_user.id}: Крок 1 - запит марки")
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(ClientSearchStates.waiting_for_brand)
async def client_brand_input(message: Message, state: FSMContext):
    """Крок 2: Отримали марку, запитуємо модель"""
    try:
        brand = message.text.strip()
        await state.update_data(brand=brand)
        
        text = f"""🚗 <b>Пошук авто</b>

<b>Марка:</b> {brand}
<b>Крок 2 з 2:</b> Тепер введіть модель

<i>Наприклад: Actros, FH16, R500</i>"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="client_search")]]
        )

        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        await state.set_state(ClientSearchStates.waiting_for_model)
        
        logger.info(f"🚗 Клієнт {message.from_user.id}: Крок 2 - марка '{brand}', запит моделі")
    except Exception as e:
        logger.error(f"❌ Помилка обробки марки: {e}")
        await message.answer("❌ <b>Помилка</b>\n\nСпробуйте ще раз.", parse_mode="HTML")


@router.message(ClientSearchStates.waiting_for_model)
async def client_search_execute(message: Message, state: FSMContext):
    """Крок 3: Отримали модель, виконуємо пошук"""
    try:
        model = message.text.strip()
        data = await state.get_data()
        brand = data.get('brand', '')
        
        vehicles = await db_manager.search_vehicles_by_brand_and_model(brand, model)

        if vehicles:
            await state.update_data(all_vehicles=vehicles, current_index=0)
            user = await db_manager.get_user_by_telegram_id(message.from_user.id)
            user_id = user.id if user else None
            await show_vehicle_card_message(message, vehicles[0], 0, len(vehicles), user_id)
            logger.info(f"✅ Клієнт {message.from_user.id}: Знайдено {len(vehicles)} авто (марка: '{brand}', модель: '{model}')")
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="client_search")]]
            )
            await message.answer(
                f"❌ <b>Авто не знайдено</b>\n\nАвто з маркою '{brand}' та моделлю '{model}' не знайдено.",
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logger.info(f"❌ Клієнт {message.from_user.id}: Авто не знайдено (марка: '{brand}', модель: '{model}')")
    except Exception as e:
        logger.error(f"❌ Помилка пошуку: {e}")
        await message.answer("❌ <b>Помилка пошуку</b>", parse_mode="HTML")


# ===== Роки =====
@router.callback_query(F.data == "client_search_years")
async def client_years_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    text = """📅 <b>Пошук по роках випуску</b>

Введіть рік початку діапазону:

<i>Наприклад: 2015</i>"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="client_search")]])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await state.set_state(ClientSearchStates.waiting_for_year_from)


@router.message(ClientSearchStates.waiting_for_year_from)
async def client_years_from(message: Message, state: FSMContext):
    try:
        year_from = int(message.text.strip())
    except ValueError:
        await message.answer("❌ <b>Помилка</b>\n\nРік має бути числом.", parse_mode="HTML")
        return
    await state.update_data(year_from=year_from)
    await message.answer(
        f"📅 <b>Пошук по роках випуску</b>\n\nВведіть рік кінця діапазону:\n\n<i>Поточний діапазон: від {year_from}</i>",
        parse_mode="HTML",
    )
    await state.set_state(ClientSearchStates.waiting_for_year_to)


@router.message(ClientSearchStates.waiting_for_year_to)
async def client_years_to(message: Message, state: FSMContext):
    try:
        year_to = int(message.text.strip())
    except ValueError:
        await message.answer("❌ <b>Помилка</b>\n\nРік має бути числом.", parse_mode="HTML")
        return
    data = await state.get_data()
    year_from = data.get("year_from")
    if year_from > year_to:
        await message.answer(
            f"❌ <b>Помилка</b>\n\nРік початку ({year_from}) не може бути більше року кінця ({year_to}).",
            parse_mode="HTML",
        )
        return
    vehicles = await db_manager.search_vehicles_by_years(year_from, year_to)
    if not vehicles:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="client_search")]])
        await message.answer(
            f"❌ <b>Авто не знайдено</b>\n\nАвто в діапазоні років {year_from}-{year_to} не знайдено.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return
    await state.update_data(all_vehicles=vehicles, current_index=0)
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    user_id = user.id if user else None
    await show_vehicle_card_message(message, vehicles[0], 0, len(vehicles), user_id)


# ===== Вартість =====
@router.callback_query(F.data == "client_search_price")
async def client_price_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    text = """💰 <b>Пошук по вартості</b>

Введіть мінімальну вартість, $:

<i>Наприклад: 10000</i>"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="client_search")]])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await state.set_state(ClientSearchStates.waiting_for_price_from)


@router.message(ClientSearchStates.waiting_for_price_from)
async def client_price_from(message: Message, state: FSMContext):
    try:
        price_from = float(message.text.strip())
    except ValueError:
        await message.answer("❌ <b>Помилка</b>\n\nВартість має бути числом.", parse_mode="HTML")
        return
    await state.update_data(price_from=price_from)
    await message.answer(
        f"💰 <b>Пошук по вартості</b>\n\nВведіть максимальну вартість:\n\n<i>Поточний діапазон: від ${price_from:,.0f}</i>",
        parse_mode="HTML",
    )
    await state.set_state(ClientSearchStates.waiting_for_price_to)


@router.message(ClientSearchStates.waiting_for_price_to)
async def client_price_to(message: Message, state: FSMContext):
    try:
        price_to = float(message.text.strip())
    except ValueError:
        await message.answer("❌ <b>Помилка</b>\n\nВартість має бути числом.", parse_mode="HTML")
        return
    data = await state.get_data()
    price_from = data.get("price_from")
    if price_from > price_to:
        await message.answer(
            f"❌ <b>Помилка</b>\n\nМінімальна вартість ({price_from:,.0f}) не може бути більше максимальної ({price_to:,.0f}).",
            parse_mode="HTML",
        )
        return
    vehicles = await db_manager.search_vehicles_by_price_range(price_from, price_to)
    if not vehicles:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="client_search")]])
        await message.answer(
            f"❌ <b>Авто не знайдено</b>\n\nАвто в діапазоні вартості ${price_from:,.0f}-${price_to:,.0f} не знайдено.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return
    await state.update_data(all_vehicles=vehicles, current_index=0)
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    user_id = user.id if user else None
    await show_vehicle_card_message(message, vehicles[0], 0, len(vehicles), user_id)


# (Видалено клієнтський пошук по VIN та по ID на вимогу)
