"""
Модуль "Мої збережені авто"
Перегляд та управління збереженими автомобілями
"""
import logging
import json
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.modules.database.manager import db_manager
from app.modules.database.models import VehicleModel
from app.utils.formatting import get_default_parse_mode
from ..quick_search.formatters import format_client_vehicle_card
from .keyboards import get_saved_vehicle_card_keyboard, get_empty_saved_keyboard

logger = logging.getLogger(__name__)

saved_vehicles_router = Router(name="saved_vehicles")


def _process_vehicle_dict(vehicle_dict: dict) -> VehicleModel:
    """Обробити словник авто - розпарсити JSON поля"""
    v_dict = vehicle_dict.copy() if vehicle_dict else {}
    
    # Розпарсюємо photos
    if v_dict.get('photos') and isinstance(v_dict['photos'], str):
        try:
            v_dict['photos'] = json.loads(v_dict['photos'])
        except:
            v_dict['photos'] = []
    
    return VehicleModel(**v_dict)


@saved_vehicles_router.callback_query(F.data == "client_saved")
async def show_saved_vehicles(callback: CallbackQuery, state: FSMContext):
    """Показати збережені авто користувача"""
    await callback.answer()
    
    # Отримуємо ID користувача (для приватних чатів використовуємо chat.id)
    user_id = callback.message.chat.id if callback.message.chat.type == "private" else callback.from_user.id
    
    # Отримуємо користувача з БД
    user = await db_manager.get_user_by_telegram_id(user_id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    # Отримуємо збережені авто (повертаються як словники)
    saved_vehicles_dicts = await db_manager.get_saved_vehicles(user.id)
    
    if not saved_vehicles_dicts:
        await callback.message.edit_text(
            "📋 <b>Мої збережені</b>\n\n"
            "У вас поки немає збережених автомобілів.\n\n"
            "📖 <b>Як зберегти авто:</b>\n"
            "• Перейдіть до <b>Каталогу авто</b>\n"
            "• Знайдіть потрібне авто\n"
            "• Натисніть <b>\"❤️ Зберегти\"</b> на картці авто\n"
            "• Збережені авто з'являться тут\n\n"
            "💡 <b>Навіщо зберігати:</b>\n"
            "• Швидкий доступ до обраних авто\n"
            "• Зручний перегляд та порівняння\n"
            "• Можливість залишити заявку прямо з картки",
            reply_markup=get_empty_saved_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
        return
    
    # Якщо є авто, показуємо меню з інструкцією та кнопкою перегляду
    text = (
        "📋 <b>Мої збережені</b>\n\n"
        f"У вас збережено авто: <b>{len(saved_vehicles_dicts)}</b>\n\n"
        "📖 <b>Як користуватися:</b>\n"
        "• Гортайте збережені авто стрілками ⬅️ ➡️\n"
        "• Видалити з обраного: натисніть <b>\"❌ Видалити з обраного\"</b>\n"
        "• Залишити заявку: натисніть <b>\"📝 Залишити заявку\"</b>\n"
        "• Переглянути деталі авто в каталозі групи\n\n"
        "<i>Натисніть нижче, щоб переглянути ваші збережені авто:</i>"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👀 Переглянути збережені", callback_data="show_saved_vehicles_list")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")]
        ]
    )
    
    # Зберігаємо дані в стані для майбутнього використання
    await state.update_data(
        saved_vehicles=[v['id'] for v in saved_vehicles_dicts],
        current_saved_index=0,
        saved_vehicles_dicts=saved_vehicles_dicts
    )
    
    try:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode=get_default_parse_mode(),
        )
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode=get_default_parse_mode(),
        )


@saved_vehicles_router.callback_query(F.data == "show_saved_vehicles_list")
async def show_saved_vehicles_list(callback: CallbackQuery, state: FSMContext):
    """Показати список збережених авто (перша картка)"""
    await callback.answer()
    
    # Отримуємо дані зі стану
    data = await state.get_data()
    saved_vehicles_dicts = data.get('saved_vehicles_dicts', [])
    
    if not saved_vehicles_dicts:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Не знайдено збережених авто.\n\n"
            "Поверніться до головного меню.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")]
                ]
            ),
            parse_mode=get_default_parse_mode(),
        )
        return
    
    # Конвертуємо перший словник в VehicleModel з обробкою JSON полів
    first_vehicle = _process_vehicle_dict(saved_vehicles_dicts[0])
    
    # Оновлюємо стан
    await state.update_data(
        current_saved_index=0
    )
    
    # Показуємо першу картку
    await render_saved_vehicle_card(callback.message, first_vehicle, 0, len(saved_vehicles_dicts), state)


async def render_saved_vehicle_card(message: Message, vehicle, index: int, total: int, state: FSMContext):
    """Відмалювати картку збереженого авто"""
    # Форматуємо картку авто (повертає tuple: text, photo_file_id)
    card_text, photo_file_id = format_client_vehicle_card(vehicle)
    
    # Додаємо інформацію про позицію
    card_text += f"\n\n📍 Автомобіль <b>{index + 1}</b> з <b>{total}</b> збережених"
    
    # Отримуємо клавіатуру
    keyboard = get_saved_vehicle_card_keyboard(vehicle.id, index, total)
    
    # Якщо є фото/відео - показуємо з медіа
    if photo_file_id:
        # Визначаємо тип: фото чи відео (префікс video:)
        is_video = isinstance(photo_file_id, str) and photo_file_id.startswith("video:")
        file_id = photo_file_id.split(":", 1)[1] if is_video else photo_file_id
        media_type = "video" if is_video else "photo"
        
        try:
            await message.edit_media(
                media={"type": media_type, "media": file_id, "caption": card_text, "parse_mode": get_default_parse_mode()},
                reply_markup=keyboard
            )
        except Exception as e:
            # Якщо не вдалося edit_media, видаляємо і створюємо нове
            logger.warning(f"Не вдалося edit_media: {e}")
            await message.delete()
            
            if is_video:
                try:
                    await message.answer_video(
                        video=file_id,
                        caption=card_text,
                        reply_markup=keyboard,
                        parse_mode=get_default_parse_mode(),
                    )
                except Exception as video_error:
                    logger.warning(f"⚠️ Не вдалося відправити відео для збереженого авто: {video_error}")
                    # Якщо відео недійсне, відправляємо тільки текст
                    await message.answer(
                        card_text,
                        reply_markup=keyboard,
                        parse_mode=get_default_parse_mode(),
                    )
            else:
                try:
                    await message.answer_photo(
                        photo=file_id,
                        caption=card_text,
                        reply_markup=keyboard,
                        parse_mode=get_default_parse_mode(),
                    )
                except Exception as photo_error:
                    logger.warning(f"⚠️ Не вдалося відправити фото для збереженого авто: {photo_error}")
                    # Якщо фото недійсне, відправляємо тільки текст
                    await message.answer(
                        card_text,
                        reply_markup=keyboard,
                        parse_mode=get_default_parse_mode(),
                    )
    else:
        # Без фото
        try:
            await message.edit_text(
                card_text,
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode(),
            )
        except Exception as e:
            logger.warning(f"Не вдалося edit_text: {e}")
            await message.delete()
            await message.answer(
                card_text,
                reply_markup=keyboard,
                parse_mode=get_default_parse_mode(),
            )


@saved_vehicles_router.callback_query(F.data.startswith("saved_prev_"))
async def prev_saved_vehicle(callback: CallbackQuery, state: FSMContext):
    """Попереднє збережене авто"""
    await callback.answer()
    
    data = await state.get_data()
    saved_ids = data.get("saved_vehicles", [])
    current_index = data.get("current_saved_index", 0)
    
    if current_index > 0:
        new_index = current_index - 1
        await state.update_data(current_saved_index=new_index)
        
        # Отримуємо авто з БД
        vehicle = await db_manager.get_vehicle_by_id(saved_ids[new_index])
        await render_saved_vehicle_card(callback.message, vehicle, new_index, len(saved_ids), state)
    else:
        await callback.answer("⚠️ Це перший автомобіль у списку", show_alert=True)


@saved_vehicles_router.callback_query(F.data.startswith("saved_next_"))
async def next_saved_vehicle(callback: CallbackQuery, state: FSMContext):
    """Наступне збережене авто"""
    await callback.answer()
    
    data = await state.get_data()
    saved_ids = data.get("saved_vehicles", [])
    current_index = data.get("current_saved_index", 0)
    
    if current_index < len(saved_ids) - 1:
        new_index = current_index + 1
        await state.update_data(current_saved_index=new_index)
        
        # Отримуємо авто з БД
        vehicle = await db_manager.get_vehicle_by_id(saved_ids[new_index])
        await render_saved_vehicle_card(callback.message, vehicle, new_index, len(saved_ids), state)
    else:
        await callback.answer("⚠️ Це останній автомобіль у списку", show_alert=True)


@saved_vehicles_router.callback_query(F.data.startswith("saved_remove_"))
async def remove_from_saved(callback: CallbackQuery, state: FSMContext):
    """Видалити авто зі збережених"""
    await callback.answer()
    
    vehicle_id = int(callback.data.split("_")[-1])
    
    # Отримуємо ID користувача
    user_id = callback.message.chat.id if callback.message.chat.type == "private" else callback.from_user.id
    user = await db_manager.get_user_by_telegram_id(user_id)
    
    if not user:
        await callback.answer("❌ Помилка отримання користувача", show_alert=True)
        return
    
    # Видаляємо зі збережених
    await db_manager.remove_saved_vehicle(user.id, vehicle_id)
    
    # Оновлюємо список
    data = await state.get_data()
    saved_ids = data.get("saved_vehicles", [])
    
    if vehicle_id in saved_ids:
        saved_ids.remove(vehicle_id)
    
    if not saved_ids:
        # Список порожній - видаляємо старе повідомлення і створюємо нове
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer(
            "📋 <b>Мої збережені</b>\n\n"
            "У вас більше немає збережених автомобілів.",
            reply_markup=get_empty_saved_keyboard(),
            parse_mode=get_default_parse_mode(),
        )
        await state.clear()
        return
    
    # Оновлюємо стан
    current_index = data.get("current_saved_index", 0)
    
    # Якщо видалили останній елемент, переходимо до попереднього
    if current_index >= len(saved_ids):
        current_index = len(saved_ids) - 1
    
    await state.update_data(
        saved_vehicles=saved_ids,
        current_saved_index=current_index
    )
    
    # Показуємо поточне авто
    vehicle = await db_manager.get_vehicle_by_id(saved_ids[current_index])
    await render_saved_vehicle_card(callback.message, vehicle, current_index, len(saved_ids), state)
    
    await callback.answer("✅ Видалено зі збережених", show_alert=False)
