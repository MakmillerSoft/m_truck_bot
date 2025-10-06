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
🏷️ <b>По марці</b> - пошук по марці авто
🚗 <b>По моделі</b> - пошук по моделі авто
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
                        text="🔙 До параметрів",
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
                await message.answer_photo(
                    photo=photo_file_id,
                    caption=detail_text,
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
                        text="🔙 До параметрів",
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
        # Очищуємо стан
        await state.clear()
        
        vin_code = message.text.strip().upper()
        
        # Шукаємо авто
        vehicles = await db_manager.search_vehicles_by_vin(vin_code)
        
        if vehicles:
            # Якщо знайдено одне авто - показуємо повну картку
            if len(vehicles) == 1:
                vehicle = vehicles[0]
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
                    await message.answer_photo(
                        photo=photo_file_id,
                        caption=detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await message.answer(
                        detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                # Якщо знайдено кілька авто - показуємо список з можливістю вибору
                from .formatters import format_search_results
                
                results_text = format_search_results(vehicles, f"VIN код: {vin_code}")
                
                await message.answer(
                    results_text,
                    parse_mode="HTML",
                    reply_markup=get_search_results_keyboard()
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


# Пошук по марці
@router.callback_query(F.data == "search_by_brand")
async def search_by_brand_start(callback: CallbackQuery, state: FSMContext):
    """Початок пошуку по марці"""
    await callback.answer()
    
    try:
        text = """🏷️ <b>Пошук по марці</b>

Введіть марку авто для пошуку:

<i>Наприклад: Mercedes, Volvo, Scania, MAN</i>"""
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 До параметрів",
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
        
        await state.set_state(QuickSearchStates.waiting_for_brand)
        
        logger.info(f"🏷️ Початок пошуку по марці для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по марці: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(QuickSearchStates.waiting_for_brand)
async def search_by_brand_process(message: Message, state: FSMContext):
    """Обробка пошуку по марці"""
    try:
        # Очищуємо стан
        await state.clear()
        
        brand = message.text.strip()
        
        # Шукаємо авто
        vehicles = await db_manager.search_vehicles_by_brand(brand)
        
        if vehicles:
            # Якщо знайдено одне авто - показуємо повну картку
            if len(vehicles) == 1:
                vehicle = vehicles[0]
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
                    await message.answer_photo(
                        photo=photo_file_id,
                        caption=detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await message.answer(
                        detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                # Якщо знайдено кілька авто - показуємо список з можливістю вибору
                from .formatters import format_search_results
                
                results_text = format_search_results(vehicles, f"Марка: {brand}")
                
                await message.answer(
                    results_text,
                    parse_mode="HTML",
                    reply_markup=get_search_results_keyboard()
                )
            
            logger.info(f"✅ Знайдено {len(vehicles)} авто марки {brand} для користувача {message.from_user.id}")
        else:
            await message.answer(
                f"❌ <b>Авто не знайдено</b>\n\nАвто марки {brand} не знайдено в системі.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            
            logger.info(f"❌ Авто марки {brand} не знайдено для користувача {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по марці: {e}")
        await message.answer(
            "❌ <b>Помилка пошуку</b>\n\nСталася помилка при пошуку авто. Спробуйте ще раз.",
            parse_mode="HTML"
        )


# Пошук по моделі
@router.callback_query(F.data == "search_by_model")
async def search_by_model_start(callback: CallbackQuery, state: FSMContext):
    """Початок пошуку по моделі"""
    await callback.answer()
    
    try:
        text = """🚗 <b>Пошук по моделі</b>

Введіть модель авто для пошуку:

<i>Наприклад: Actros, FH16, R500</i>"""
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 До параметрів",
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
        
        await state.set_state(QuickSearchStates.waiting_for_model)
        
        logger.info(f"🚗 Початок пошуку по моделі для користувача {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка початку пошуку по моделі: {e}")
        await callback.answer("❌ Помилка початку пошуку", show_alert=True)


@router.message(QuickSearchStates.waiting_for_model)
async def search_by_model_process(message: Message, state: FSMContext):
    """Обробка пошуку по моделі"""
    try:
        # Очищуємо стан
        await state.clear()
        
        model = message.text.strip()
        
        # Шукаємо авто
        vehicles = await db_manager.search_vehicles_by_model(model)
        
        if vehicles:
            # Якщо знайдено одне авто - показуємо повну картку
            if len(vehicles) == 1:
                vehicle = vehicles[0]
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
                    await message.answer_photo(
                        photo=photo_file_id,
                        caption=detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await message.answer(
                        detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                # Якщо знайдено кілька авто - показуємо список з можливістю вибору
                from .formatters import format_search_results
                
                results_text = format_search_results(vehicles, f"Модель: {model}")
                
                await message.answer(
                    results_text,
                    parse_mode="HTML",
                    reply_markup=get_search_results_keyboard()
                )
            
            logger.info(f"✅ Знайдено {len(vehicles)} авто моделі {model} для користувача {message.from_user.id}")
        else:
            await message.answer(
                f"❌ <b>Авто не знайдено</b>\n\nАвто моделі {model} не знайдено в системі.",
                parse_mode="HTML",
                reply_markup=get_search_results_keyboard()
            )
            
            logger.info(f"❌ Авто моделі {model} не знайдено для користувача {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Помилка пошуку по моделі: {e}")
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
                        text="🔙 До параметрів",
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
        
        # Очищуємо стан
        await state.clear()
        
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
            # Якщо знайдено одне авто - показуємо повну картку
            if len(vehicles) == 1:
                vehicle = vehicles[0]
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
                    await message.answer_photo(
                        photo=photo_file_id,
                        caption=detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await message.answer(
                        detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                # Якщо знайдено кілька авто - показуємо список з можливістю вибору
                from .formatters import format_search_results
                
                results_text = format_search_results(vehicles, f"Роки: {year_from}-{year_to}")
                
                await message.answer(
                    results_text,
                    parse_mode="HTML",
                    reply_markup=get_search_results_keyboard()
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
                        text="🔙 До параметрів",
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
        
        # Очищуємо стан
        await state.clear()
        
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
            # Якщо знайдено одне авто - показуємо повну картку
            if len(vehicles) == 1:
                vehicle = vehicles[0]
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
                    await message.answer_photo(
                        photo=photo_file_id,
                        caption=detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await message.answer(
                        detail_text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                # Якщо знайдено кілька авто - показуємо список з можливістю вибору
                from .formatters import format_search_results
                
                results_text = format_search_results(vehicles, f"Вартість: {price_from:,.0f}-{price_to:,.0f} грн")
                
                await message.answer(
                    results_text,
                    parse_mode="HTML",
                    reply_markup=get_search_results_keyboard()
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
