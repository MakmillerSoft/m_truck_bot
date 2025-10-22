"""
Обробники для швидкого пошуку авто
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.modules.database.manager import DatabaseManager
from .keyboards import (
    get_quick_search_keyboard,
    get_search_parameters_keyboard,
    get_search_results_keyboard
)

logger = logging.getLogger(__name__)
router = Router()
db_manager = DatabaseManager()


class QuickSearchStates(StatesGroup):
    """Стани для швидкого пошуку"""
    waiting_for_id = State()
    waiting_for_vin = State()
    waiting_for_brand = State()
    waiting_for_model = State()
    waiting_for_year_from = State()
    waiting_for_year_to = State()
    waiting_for_price_from = State()
    waiting_for_price_to = State()


@router.callback_query(F.data == "quick_search")
async def show_quick_search_menu(callback: CallbackQuery):
    """Показати меню швидкого пошуку"""
    await callback.answer()
    
    try:
        text = """🔍 <b>Швидкий пошук авто</b>

Оберіть тип пошуку:

🔍 <b>По параметрам</b> - швидкий пошук по ID, VIN, марці, моделі, роках, вартості
📝 <b>По фільтру</b> - детальний пошук з заповненням всіх параметрів"""
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_quick_search_keyboard()
        )
        
        logger.info(f"🔍 Показано меню швидкого пошуку для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка показу меню швидкого пошуку: {e}")
        await callback.answer("❌ Помилка відображення меню", show_alert=True)


@router.callback_query(F.data == "search_by_parameters")
async def show_search_parameters(callback: CallbackQuery):
    """Показати параметри пошуку"""
    await callback.answer()
    
    try:
        text = """🔍 <b>Пошук по параметрам</b>

Оберіть параметр для пошуку:

🆔 <b>По ID авто</b> - точний пошук по ідентифікатору
🔢 <b>По VIN коду</b> - пошук по VIN коду
🏷️🚗 <b>По марці або моделі</b> - пошук одночасно
📅 <b>По роках випуску</b> - пошук в діапазоні років
💰 <b>По вартості</b> - пошук в діапазоні цін

<i>Кожен параметр працює окремо</i>"""
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_search_parameters_keyboard()
        )
        
        logger.info(f"🔍 Показано параметри пошуку для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка показу параметрів пошуку: {e}")
        await callback.answer("❌ Помилка відображення параметрів", show_alert=True)


@router.callback_query(F.data == "back_to_quick_search")
async def back_to_quick_search(callback: CallbackQuery):
    """Повернення до меню швидкого пошуку"""
    await callback.answer()
    
    try:
        text = """🔍 <b>Швидкий пошук авто</b>

Оберіть тип пошуку:

🔍 <b>По параметрам</b> - швидкий пошук по ID, VIN, марці, моделі, роках, вартості
📝 <b>По фільтру</b> - детальний пошук з заповненням всіх параметрів"""
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_quick_search_keyboard()
        )
        
        logger.info(f"🔙 Повернення до меню швидкого пошуку для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка повернення до меню пошуку: {e}")
        await callback.answer("❌ Помилка повернення", show_alert=True)


# Пошук по ID
@router.callback_query(F.data == "search_by_id")
async def search_by_id_start(callback: CallbackQuery, state: FSMContext):
    """Початок пошуку по ID"""
    await callback.answer()
    
    try:
        text = """🆔 <b>Пошук по ID авто</b>

Введіть ID авто для пошуку:

<i>ID - це числовий ідентифікатор авто в системі</i>"""
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="search_by_parameters"
                    )
                ]
            ]
        )
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        await state.set_state(QuickSearchStates.waiting_for_id)
        
        logger.info(f"🆔 Початок пошуку по ID для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по ID: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(QuickSearchStates.waiting_for_id)
async def search_by_id_process(message: Message, state: FSMContext):
    """Обробка пошуку по ID"""
    try:
        # Очищуємо стан
        await state.clear()
        
        # Перевіряємо чи це число
        try:
            vehicle_id = int(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ <b>Помилка</b>\n\nID повинен бути числом. Спробуйте ще раз.",
                parse_mode="HTML"
            )
            await state.set_state(QuickSearchStates.waiting_for_id)
            return
        
        # Шукаємо авто
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if vehicle:
            # Форматуємо результат як повну картку авто
            from ..listing.formatters import format_admin_vehicle_card
            from ..listing.keyboards import get_vehicle_detail_keyboard
            
            detail_text, photo_file_id = format_admin_vehicle_card(vehicle)
            
            # Створюємо клавіатуру як у блоці "Всі авто"
            keyboard = get_vehicle_detail_keyboard(
                vehicle_id=vehicle.id,
                status=vehicle.status if hasattr(vehicle, 'status') else 'available',
                group_message_id=vehicle.group_message_id if hasattr(vehicle, 'group_message_id') else None
            )
            
            # Відправляємо результат
            if photo_file_id:
                # Визначаємо тип: фото чи відео (префікс video:)
                is_video = isinstance(photo_file_id, str) and photo_file_id.startswith("video:")
                file_id = photo_file_id.split(":", 1)[1] if is_video else photo_file_id
                
                if is_video:
                    try:
                        await message.answer_video(
                            video=file_id,
                            caption=detail_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                    except Exception as video_error:
                        logger.warning(f"⚠️ Не вдалося відправити відео для авто: {video_error}")
                        # Якщо відео недійсне, відправляємо тільки текст
                        await message.answer(
                            detail_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                else:
                    try:
                        await message.answer_photo(
                            photo=file_id,
                            caption=detail_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
                    except Exception as photo_error:
                        logger.warning(f"⚠️ Не вдалося відправити фото для авто: {photo_error}")
                        # Якщо фото недійсне, відправляємо тільки текст
                        await message.answer(
                            detail_text,
                            parse_mode="HTML",
                            reply_markup=keyboard
                        )
            else:
                await message.answer(
                    detail_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            
            logger.info(f"✅ Знайдено авто ID {vehicle_id} для користувача {message.from_user.id}")
        else:
            await message.answer(
                f"❌ <b>Авто не знайдено</b>\n\nАвто з ID {vehicle_id} не існує в системі.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            
            logger.info(f"❌ Авто ID {vehicle_id} не знайдено для користувача {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по ID: {e}")
        await message.answer(
            "❌ <b>Помилка пошуку</b>\n\nСталася помилка при пошуку авто. Спробуйте ще раз.",
            parse_mode="HTML"
        )


# Пошук по VIN
@router.callback_query(F.data == "search_by_vin")
async def search_by_vin_start(callback: CallbackQuery, state: FSMContext):
    """Початок пошуку по VIN"""
    await callback.answer()
    
    try:
        text = """🔢 <b>Пошук по VIN коду</b>

Введіть VIN код авто для пошуку:

<i>VIN код - це унікальний ідентифікатор авто</i>"""
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="search_by_parameters"
                    )
                ]
            ]
        )
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        await state.set_state(QuickSearchStates.waiting_for_vin)
        
        logger.info(f"🔢 Початок пошуку по VIN для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по VIN: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(QuickSearchStates.waiting_for_vin)
async def search_by_vin_process(message: Message, state: FSMContext):
    """Обробка пошуку по VIN"""
    try:
        vin_code = message.text.strip().upper()
        
        # Шукаємо авто
        vehicles = await db_manager.search_vehicles_by_vin(vin_code)
        
        if vehicles:
            # Уніфікована навігація по результатах
            await _process_search_results(
                vehicles,
                message,
                state,
                f"VIN: {vin_code}"
            )
            
            logger.info(f"✅ Знайдено {len(vehicles)} авто по VIN {vin_code} для користувача {message.from_user.id}")
        else:
            await message.answer(
                f"❌ <b>Авто не знайдено</b>\n\nАвто з VIN кодом {vin_code} не знайдено в системі.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            
            logger.info(f"❌ Авто з VIN {vin_code} не знайдено для користувача {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по VIN: {e}")
        await message.answer(
            "❌ <b>Помилка пошуку</b>\n\nСталася помилка при пошуку авто. Спробуйте ще раз.",
            parse_mode="HTML"
        )


# Пошук по роках
@router.callback_query(F.data == "search_by_years")
async def search_by_years_start(callback: CallbackQuery, state: FSMContext):
    """Початок пошуку по роках"""
    await callback.answer()
    
    try:
        text = """📅 <b>Пошук по роках випуску</b>

Введіть рік початку діапазону:

<i>Наприклад: 2010</i>"""
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="search_by_parameters"
                    )
                ]
            ]
        )
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        await state.set_state(QuickSearchStates.waiting_for_year_from)
        
        logger.info(f"📅 Початок пошуку по роках для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по роках: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(QuickSearchStates.waiting_for_year_from)
async def search_by_years_from_process(message: Message, state: FSMContext):
    """Обробка року початку"""
    try:
        # Перевіряємо чи це число
        try:
            year_from = int(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ <b>Помилка</b>\n\nРік повинен бути числом. Спробуйте ще раз.",
                parse_mode="HTML"
            )
            return
        
        # Зберігаємо рік початку
        await state.update_data(year_from=year_from)
        
        await message.answer(
            f"📅 <b>Пошук по роках випуску</b>\n\nВведіть рік кінця діапазону:\n\n<i>Поточний діапазон: від {year_from}</i>",
            parse_mode="HTML"
        )
        
        await state.set_state(QuickSearchStates.waiting_for_year_to)
        
    except Exception as e:
        logger.error(f"❌ Помилка обробки року початку: {e}")
        await message.answer(
            "❌ <b>Помилка</b>\n\nСталася помилка. Спробуйте ще раз.",
            parse_mode="HTML"
        )


@router.message(QuickSearchStates.waiting_for_year_to)
async def search_by_years_to_process(message: Message, state: FSMContext):
    """Обробка року кінця та пошук"""
    try:
        # Перевіряємо чи це число
        try:
            year_to = int(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ <b>Помилка</b>\n\nРік повинен бути числом. Спробуйте ще раз.",
                parse_mode="HTML"
            )
            return
        
        # Отримуємо дані зі стану
        data = await state.get_data()
        year_from = data.get('year_from')
        
        # Перевіряємо логіку діапазону
        if year_from > year_to:
            await message.answer(
                f"❌ <b>Помилка</b>\n\nРік початку ({year_from}) не може бути більше року кінця ({year_to}).",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            return
        
        # Шукаємо авто
        vehicles = await db_manager.search_vehicles_by_years(year_from, year_to)
        
        if vehicles:
            # Уніфікована навігація по результатах
            await _process_search_results(
                vehicles,
                message,
                state,
                f"Роки: {year_from}-{year_to}"
            )
            
            logger.info(f"✅ Знайдено {len(vehicles)} авто в діапазоні {year_from}-{year_to} для користувача {message.from_user.id}")
        else:
            await message.answer(
                f"❌ <b>Авто не знайдено</b>\n\nАвто в діапазоні років {year_from}-{year_to} не знайдено в системі.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            
            logger.info(f"❌ Авто в діапазоні {year_from}-{year_to} не знайдено для користувача {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по роках: {e}")
        await message.answer(
            "❌ <b>Помилка пошуку</b>\n\nСталася помилка при пошуку авто. Спробуйте ще раз.",
            parse_mode="HTML"
        )


# Пошук по вартості
@router.callback_query(F.data == "search_by_price")
async def search_by_price_start(callback: CallbackQuery, state: FSMContext):
    """Початок пошуку по вартості"""
    await callback.answer()
    
    try:
        text = """💰 <b>Пошук по вартості</b>

Введіть мінімальну вартість:

<i>Наприклад: 50000</i>"""
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="search_by_parameters"
                    )
                ]
            ]
        )
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        await state.set_state(QuickSearchStates.waiting_for_price_from)
        
        logger.info(f"💰 Початок пошуку по вартості для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по вартості: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(QuickSearchStates.waiting_for_price_from)
async def search_by_price_from_process(message: Message, state: FSMContext):
    """Обробка мінімальної вартості"""
    try:
        # Перевіряємо чи це число
        try:
            price_from = float(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ <b>Помилка</b>\n\nВартість повинна бути числом. Спробуйте ще раз.",
                parse_mode="HTML"
            )
            return
        
        # Зберігаємо вартість початку
        await state.update_data(price_from=price_from)
        
        await message.answer(
            f"💰 <b>Пошук по вартості</b>\n\nВведіть максимальну вартість:\n\n<i>Поточний діапазон: від {price_from:,.0f} грн</i>",
            parse_mode="HTML"
        )
        
        await state.set_state(QuickSearchStates.waiting_for_price_to)
        
    except Exception as e:
        logger.error(f"❌ Помилка обробки мінімальної вартості: {e}")
        await message.answer(
            "❌ <b>Помилка</b>\n\nСталася помилка. Спробуйте ще раз.",
            parse_mode="HTML"
        )


@router.message(QuickSearchStates.waiting_for_price_to)
async def search_by_price_to_process(message: Message, state: FSMContext):
    """Обробка максимальної вартості та пошук"""
    try:
        # Перевіряємо чи це число
        try:
            price_to = float(message.text.strip())
        except ValueError:
            await message.answer(
                "❌ <b>Помилка</b>\n\nВартість повинна бути числом. Спробуйте ще раз.",
                parse_mode="HTML"
            )
            return
        
        # Отримуємо дані зі стану
        data = await state.get_data()
        price_from = data.get('price_from')
        
        # Перевіряємо логіку діапазону
        if price_from > price_to:
            await message.answer(
                f"❌ <b>Помилка</b>\n\nМінімальна вартість ({price_from:,.0f}) не може бути більше максимальної ({price_to:,.0f}).",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            return
        
        # Шукаємо авто
        vehicles = await db_manager.search_vehicles_by_price_range(price_from, price_to)
        
        if vehicles:
            # Уніфікована навігація по результатах
            await _process_search_results(
                vehicles,
                message,
                state,
                f"Вартість: {price_from:,.0f}-{price_to:,.0f} грн"
            )
            
            logger.info(f"✅ Знайдено {len(vehicles)} авто в діапазоні {price_from}-{price_to} грн для користувача {message.from_user.id}")
        else:
            await message.answer(
                f"❌ <b>Авто не знайдено</b>\n\nАвто в діапазоні вартості {price_from:,.0f}-{price_to:,.0f} грн не знайдено в системі.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            
            logger.info(f"❌ Авто в діапазоні {price_from}-{price_to} грн не знайдено для користувача {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по вартості: {e}")
        await message.answer(
            "❌ <b>Помилка пошуку</b>\n\nСталася помилка при пошуку авто. Спробуйте ще раз.",
            parse_mode="HTML"
        )


# Об'єднаний пошук по марці та моделі
@router.callback_query(F.data == "search_by_brand_model")
async def search_by_brand_model_start(callback: CallbackQuery, state: FSMContext):
    """Крок 1: Запит марки авто"""
    await callback.answer()
    try:
        text = """🏷️ <b>Пошук по марці та моделі</b>

<b>Крок 1 з 2:</b> Введіть марку авто

<i>Наприклад: Mercedes, Volvo, Scania, MAN</i>"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="search_by_parameters")]]
        )

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        await state.set_state(QuickSearchStates.waiting_for_brand)
        
        logger.info(f"🏷️ Крок 1: Запит марки для користувача {callback.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(QuickSearchStates.waiting_for_brand)
async def search_by_brand_input(message: Message, state: FSMContext):
    """Крок 2: Отримали марку, запитуємо модель"""
    try:
        brand = message.text.strip()
        
        # Зберігаємо марку в стані
        await state.update_data(brand=brand)
        
        text = f"""🚗 <b>Пошук по марці та моделі</b>

<b>Марка:</b> {brand}
<b>Крок 2 з 2:</b> Тепер введіть модель

<i>Наприклад: Actros, FH16, R500</i>"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="search_by_parameters")]]
        )

        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        await state.set_state(QuickSearchStates.waiting_for_model)
        
        logger.info(f"🚗 Крок 2: Марка '{brand}' збережена, запит моделі для користувача {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Помилка обробки марки: {e}")
        await message.answer("❌ <b>Помилка</b>\n\nСпробуйте ще раз.", parse_mode="HTML")


@router.message(QuickSearchStates.waiting_for_model)
async def search_by_brand_and_model_execute(message: Message, state: FSMContext):
    """Крок 3: Отримали модель, виконуємо пошук"""
    try:
        model = message.text.strip()
        
        # Отримуємо марку зі стану
        data = await state.get_data()
        brand = data.get('brand', '')
        
        # Шукаємо авто по марці І моделі
        vehicles = await db_manager.search_vehicles_by_brand_and_model(brand, model)

        if vehicles:
            # Зберігаємо результати пошуку в стані для навігації
            vehicle_ids = [v.id for v in vehicles]
            await state.update_data(
                search_results=vehicle_ids,
                search_filter=f"Марка: {brand}, Модель: {model}",
                current_search_index=0
            )
            
            # Показуємо перше авто
            vehicle = vehicles[0]
            await _show_search_result_vehicle(message, vehicle, 0, len(vehicles), state, f"Марка: {brand}, Модель: {model}")

            logger.info(f"✅ Знайдено {len(vehicles)} авто (марка: '{brand}', модель: '{model}')")
        else:
            await state.clear()
            await message.answer(
                f"❌ <b>Авто не знайдено</b>\n\nАвто з маркою '{brand}' та моделлю '{model}' не знайдено.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard(),
            )
            logger.info(f"❌ Авто не знайдено: марка '{brand}', модель '{model}'")
    except Exception as e:
        logger.error(f"❌ Помилка пошуку: {e}")
        await message.answer("❌ <b>Помилка пошуку</b>", parse_mode="HTML")


async def _process_search_results(vehicles: list, message: Message, state: FSMContext, filter_desc: str):
    """Універсальна обробка результатів пошуку з навігацією"""
    if len(vehicles) == 0:
        return False
    
    # Зберігаємо результати пошуку в стані для навігації
    vehicle_ids = [v.id for v in vehicles]
    await state.update_data(
        search_results=vehicle_ids,
        search_filter=filter_desc,
        current_search_index=0
    )
    
    # Показуємо перше авто
    vehicle = vehicles[0]
    await _show_search_result_vehicle(message, vehicle, 0, len(vehicles), state, filter_desc)
    return True


async def _show_search_result_vehicle(message: Message, vehicle, index: int, total: int, state: FSMContext, filter_desc: str):
    """Показати авто з результатів пошуку з навігацією"""
    from ..listing.formatters import format_admin_vehicle_card
    
    detail_text, photo_file_id = format_admin_vehicle_card(vehicle)
    
    # Додаємо інформацію про пошук
    header = f"🔍 <b>Результати пошуку</b>\n<i>{filter_desc}</i>\n\n📍 Авто {index + 1} з {total}\n\n"
    detail_text = header + detail_text
    
    # Створюємо клавіатуру з навігацією
    keyboard = _get_search_navigation_keyboard(vehicle.id, index, total, vehicle.status if hasattr(vehicle, 'status') else 'available', vehicle.group_message_id if hasattr(vehicle, 'group_message_id') else None)
    
    if photo_file_id:
        # Визначаємо тип: фото чи відео (префікс video:)
        is_video = isinstance(photo_file_id, str) and photo_file_id.startswith("video:")
        file_id = photo_file_id.split(":", 1)[1] if is_video else photo_file_id
        
        if is_video:
            try:
                await message.answer_video(video=file_id, caption=detail_text, parse_mode="HTML", reply_markup=keyboard)
            except Exception as video_error:
                logger.warning(f"⚠️ Не вдалося відправити відео для авто: {video_error}")
                # Якщо відео недійсне, відправляємо тільки текст
                await message.answer(detail_text, parse_mode="HTML", reply_markup=keyboard)
        else:
            try:
                await message.answer_photo(photo=file_id, caption=detail_text, parse_mode="HTML", reply_markup=keyboard)
            except Exception as photo_error:
                logger.warning(f"⚠️ Не вдалося відправити фото для авто: {photo_error}")
                # Якщо фото недійсне, відправляємо тільки текст
                await message.answer(detail_text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(detail_text, parse_mode="HTML", reply_markup=keyboard)


def _get_search_navigation_keyboard(vehicle_id: int, index: int, total: int, status: str, group_message_id: int = None) -> InlineKeyboardMarkup:
    """Клавіатура для навігації по результатах пошуку"""
    from ..listing.keyboards import get_vehicle_detail_keyboard
    
    # Базова клавіатура з деталей авто
    base_keyboard = get_vehicle_detail_keyboard(vehicle_id, status, group_message_id)
    
    # Додаємо кнопки навігації
    nav_buttons = []
    if index > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Попереднє", callback_data=f"search_prev_{index}"))
    if index < total - 1:
        nav_buttons.append(InlineKeyboardButton(text="Наступне ▶️", callback_data=f"search_next_{index}"))
    
    # Вставляємо навігацію перед кнопкою "Назад"
    keyboard_rows = list(base_keyboard.inline_keyboard)
    if nav_buttons:
        keyboard_rows.insert(-1, nav_buttons)  # Додаємо перед останнім рядком (Назад)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


@router.callback_query(F.data.startswith("search_prev_"))
async def navigate_search_prev(callback: CallbackQuery, state: FSMContext):
    """Навігація до попереднього авто в результатах пошуку"""
    await callback.answer()
    try:
        data = await state.get_data()
        search_results = data.get('search_results', [])
        search_filter = data.get('search_filter', '')
        current_index = data.get('current_search_index', 0)
        
        if not search_results or current_index <= 0:
            await callback.answer("❌ Це перше авто", show_alert=True)
            return
        
        # Переходимо до попереднього
        new_index = current_index - 1
        await state.update_data(current_search_index=new_index)
        
        # Отримуємо авто з БД
        vehicle_id = search_results[new_index]
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            await callback.answer("❌ Авто не знайдено", show_alert=True)
            return
        
        # Показуємо авто
        from ..listing.formatters import format_admin_vehicle_card
        
        detail_text, photo_file_id = format_admin_vehicle_card(vehicle)
        header = f"🔍 <b>Результати пошуку</b>\n<i>{search_filter}</i>\n\n📍 Авто {new_index + 1} з {len(search_results)}\n\n"
        detail_text = header + detail_text
        
        keyboard = _get_search_navigation_keyboard(vehicle.id, new_index, len(search_results), vehicle.status if hasattr(vehicle, 'status') else 'available', vehicle.group_message_id if hasattr(vehicle, 'group_message_id') else None)
        
        if photo_file_id:
            await callback.message.delete()
            try:
                await callback.message.answer_photo(photo=photo_file_id, caption=detail_text, parse_mode="HTML", reply_markup=keyboard)
            except Exception as photo_error:
                logger.warning(f"⚠️ Не вдалося відправити фото для авто: {photo_error}")
                # Якщо фото недійсне, відправляємо тільки текст
                await callback.message.answer(detail_text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback.message.edit_text(detail_text, parse_mode="HTML", reply_markup=keyboard)
        
        logger.info(f"◀️ Навігація: авто {new_index + 1}/{len(search_results)}")
    except Exception as e:
        logger.error(f"❌ Помилка навігації: {e}")
        await callback.answer("❌ Помилка навігації", show_alert=True)


@router.callback_query(F.data.startswith("search_next_"))
async def navigate_search_next(callback: CallbackQuery, state: FSMContext):
    """Навігація до наступного авто в результатах пошуку"""
    await callback.answer()
    try:
        data = await state.get_data()
        search_results = data.get('search_results', [])
        search_filter = data.get('search_filter', '')
        current_index = data.get('current_search_index', 0)
        
        if not search_results or current_index >= len(search_results) - 1:
            await callback.answer("❌ Це останнє авто", show_alert=True)
            return
        
        # Переходимо до наступного
        new_index = current_index + 1
        await state.update_data(current_search_index=new_index)
        
        # Отримуємо авто з БД
        vehicle_id = search_results[new_index]
        vehicle = await db_manager.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            await callback.answer("❌ Авто не знайдено", show_alert=True)
            return
        
        # Показуємо авто
        from ..listing.formatters import format_admin_vehicle_card
        
        detail_text, photo_file_id = format_admin_vehicle_card(vehicle)
        header = f"🔍 <b>Результати пошуку</b>\n<i>{search_filter}</i>\n\n📍 Авто {new_index + 1} з {len(search_results)}\n\n"
        detail_text = header + detail_text
        
        keyboard = _get_search_navigation_keyboard(vehicle.id, new_index, len(search_results), vehicle.status if hasattr(vehicle, 'status') else 'available', vehicle.group_message_id if hasattr(vehicle, 'group_message_id') else None)
        
        if photo_file_id:
            await callback.message.delete()
            try:
                await callback.message.answer_photo(photo=photo_file_id, caption=detail_text, parse_mode="HTML", reply_markup=keyboard)
            except Exception as photo_error:
                logger.warning(f"⚠️ Не вдалося відправити фото для авто: {photo_error}")
                # Якщо фото недійсне, відправляємо тільки текст
                await callback.message.answer(detail_text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback.message.edit_text(detail_text, parse_mode="HTML", reply_markup=keyboard)
        
        logger.info(f"▶️ Навігація: авто {new_index + 1}/{len(search_results)}")
    except Exception as e:
        logger.error(f"❌ Помилка навігації: {e}")
        await callback.answer("❌ Помилка навігації", show_alert=True)
