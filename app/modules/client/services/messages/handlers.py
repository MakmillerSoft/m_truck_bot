"""
Модуль повідомлень та заявок
Інформація про систему зв'язку з менеджерами
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext

from app.utils.formatting import get_default_parse_mode
from app.modules.database.manager import db_manager
from .states import MessageStates

logger = logging.getLogger(__name__)

messages_router = Router(name="client_messages")


@messages_router.callback_query(F.data == "client_messages")
async def show_messages_info(callback: CallbackQuery):
    """Показати інформацію про систему повідомлень"""
    await callback.answer()
    
    text = """
💬 <b>Повідомлення та заявки</b>

📝 <b>Як залишити заявку:</b>

<b>Варіант 1 - Загальна заявка:</b>
• Натисніть кнопку <b>"📝 Залишити заявку"</b> нижче
• Опишіть вашу потребу у вільній формі
• Вкажіть бажання, питання або особливі вимоги

<b>Варіант 2 - Заявка на конкретне авто:</b>
• Перейдіть до <b>Каталогу авто</b>
• Оберіть автомобіль, який вас цікавить
• Натисніть <b>"📝 Залишити заявку"</b> під карткою авто

✅ <b>Після відправки заявки:</b>
• Повідомлення автоматично надіслається нашим менеджерам
• Ми зв'яжемося з вами найближчим часом
• Відповідь надійде через Telegram або за вказаним номером телефону

📞 <b>Контактні дані:</b>
Використовується номер телефону, вказаний у вашому профілі
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Залишити заявку", callback_data="create_request")],
            [InlineKeyboardButton(text="🚛 Переглянути каталог", callback_data="client_catalog_menu")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="client_back_to_main")]
        ]
    )
    
    await callback.message.edit_text(
        text.strip(),
        reply_markup=keyboard,
        parse_mode=get_default_parse_mode(),
    )


@messages_router.callback_query(F.data == "create_request")
async def start_create_request(callback: CallbackQuery, state: FSMContext):
    """Початок створення заявки"""
    await callback.answer()
    await state.set_state(MessageStates.waiting_for_request_details)
    logger.info(f"🔄 Встановлено стан MessageStates.waiting_for_request_details для користувача {callback.from_user.id}")
    
    text = """
📝 <b>Створення заявки</b>

Опишіть вашу потребу у вільній формі:

• Який тип транспорту вас цікавить?
• Які характеристики важливі?
• Бюджет або інші побажання?
• Будь-які додаткові питання

<i>Наприклад: "Шукаю сідельний тягач Volvo, рік не старше 2018, пробіг до 500 тис. км, бюджет до $25000"</i>

✍️ Напишіть ваш запит:
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_request")]
        ]
    )
    
    await callback.message.edit_text(
        text.strip(),
        reply_markup=keyboard,
        parse_mode=get_default_parse_mode(),
    )


@messages_router.callback_query(F.data == "cancel_request")
async def cancel_request(callback: CallbackQuery, state: FSMContext):
    """Скасування створення заявки"""
    await callback.answer("Створення заявки скасовано")
    await state.clear()
    
    # Повертаємося до блоку повідомлень
    await show_messages_info(callback)


@messages_router.message(MessageStates.waiting_for_request_details, F.text)
async def process_request_details(message: Message, state: FSMContext):
    """Обробка деталей заявки"""
    logger.info(f"📝 Отримано текст повідомлення від користувача {message.from_user.id}")
    logger.info(f"📝 Обробка загальної заявки в MessageStates.waiting_for_request_details")
    
    logger.info(f"📝 Текст заявки: {message.text[:100]}...")
    
    request_text = message.text.strip()
    
    if len(request_text) < 10:
        await message.answer(
            "❌ Опис заявки занадто короткий. Будь ласка, опишіть вашу потребу детальніше (мінімум 10 символів):",
            parse_mode=get_default_parse_mode(),
        )
        return
    
    # Отримуємо користувача
    user_id = message.chat.id if message.chat.type == "private" else message.from_user.id
    user = await db_manager.get_user_by_telegram_id(user_id)
    
    if not user:
        await message.answer(
            "❌ Помилка: користувач не знайдений. Спробуйте /start",
            parse_mode=get_default_parse_mode(),
        )
        await state.clear()
        return
    
    # Зберігаємо заявку в БД (загальна заявка, без прив'язки до авто)
    try:
        await db_manager.create_manager_request(
            user_id=user.id,
            request_type="general",
            details=request_text,
            vehicle_id=None
        )
        logger.info(f"✅ Заявку від користувача {user.id} успішно збережено в БД")
    except Exception as e:
        logger.error(f"❌ Помилка збереження заявки: {e}")
        await message.answer(
            "❌ Помилка при збереженні заявки. Спробуйте пізніше.",
            parse_mode=get_default_parse_mode(),
        )
        await state.clear()
        return
    
    # Отримуємо всіх адміністраторів
    admins = await db_manager.get_admins()
    logger.info(f"📊 Знайдено {len(admins)} адміністраторів для сповіщення")
    
    # Відправляємо сповіщення адміністраторам
    for admin in admins:
        try:
            admin_text = f"""
🔔 <b>Нова заявка від клієнта</b>

👤 <b>Клієнт:</b>
• Ім'я: {user.first_name or '—'} {user.last_name or ''}
• Телефон: {user.phone or '—'}
• Telegram ID: <code>{user.telegram_id}</code>

📝 <b>Опис потреби:</b>
{request_text}

<b>Тип:</b> Загальна заявка
"""
            
            await message.bot.send_message(
                admin.telegram_id,
                admin_text.strip(),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="📨 Перейти до заявок", callback_data="admin_requests")]
                    ]
                ),
                parse_mode=get_default_parse_mode(),
            )
        except Exception as e:
            logger.error(f"Не вдалося відправити сповіщення адміну {admin.telegram_id}: {e}")
    
    await state.clear()
    logger.info(f"🧹 Стан FSM очищено для користувача {message.from_user.id}")
    
    # Підтвердження для користувача
    text = """
✅ <b>Заявку успішно відправлено!</b>

📞 Наші менеджери зв'яжуться з вами найближчим часом за вказаним номером телефону або через Telegram.

Дякуємо за звернення!
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Залишити ще одну заявку", callback_data="create_request")],
            [InlineKeyboardButton(text="🚛 Переглянути каталог", callback_data="client_catalog_menu")],
            [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="client_back_to_main")]
        ]
    )
    
    logger.info(f"💬 Відправка підтвердження користувачу {message.from_user.id}")
    
    await message.answer(
        text.strip(),
        reply_markup=keyboard,
        parse_mode=get_default_parse_mode(),
    )
    
    logger.info(f"✅ Обробка заявки завершена для користувача {message.from_user.id}")
