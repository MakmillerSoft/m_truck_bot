"""
Обробники модуля повідомлень та комунікації
"""

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from app.modules.database.manager import db_manager
from app.utils.formatting import get_default_parse_mode
from .states import ManagerRequestStates

# Імпортуємо функцію для показу картки авто
from app.modules.search.handlers import show_vehicle_card

router = Router()


def format_request_display(
    request: dict, index: int, show_user_info: bool = False
) -> str:
    """Уніфіковане форматування заявки для відображення"""
    status_names = {
        "new": "Нова",
        "in_progress": "В роботі",
        "completed": "Виконана",
        "cancelled": "Скасована",
    }
    status_name = status_names.get(request["status"], request["status"])

    type_names = {
        "buy": "Покупка авто",
        "finance": "Фінансування",
        "service": "Сервіс",
        "consultation": "Консультація",
        "other": "Інше",
        "vehicle_inquiry": "Запит щодо авто",
    }
    type_name = type_names.get(request["request_type"], request["request_type"])

    # Форматування дати
    created_at = request["created_at"]
    if isinstance(created_at, str):
        date_str = created_at[:16].replace("T", " ")
    else:
        date_str = created_at.strftime("%Y-%m-%d %H:%M")

    # Форматування деталей з обробкою vehicle_inquiry
    details = request["details"]
    if request["request_type"] == "vehicle_inquiry" and "Запит щодо авто:" in details:
        # Розбираємо деталі для vehicle_inquiry
        lines = details.split("\n")
        if len(lines) >= 2:
            vehicle_info = lines[0]  # "Запит щодо авто: Volvo Actros (ID: 69)"
            user_message = "\n".join(lines[1:])  # Повідомлення користувача

            # Витягуємо назву авто та ID
            if "ID:" in vehicle_info:
                vehicle_name = (
                    vehicle_info.split("ID:")[0].replace("Запит щодо авто:", "").strip()
                )
                # Прибираємо дужки з назви авто
                if vehicle_name.endswith(" ("):
                    vehicle_name = vehicle_name[:-2]
                vehicle_id = vehicle_info.split("ID:")[1].strip().replace(")", "")

                # Формуємо деталі з повним текстом (без обрізання)
                formatted_details = f"   <b>Авто:</b> {vehicle_name}\n   <b>Деталі:</b> {user_message}"
            else:
                formatted_details = f"   <b>Деталі:</b> {details[:60]}{'...' if len(details) > 60 else ''}"
        else:
            formatted_details = (
                f"   <b>Деталі:</b> {details[:60]}{'...' if len(details) > 60 else ''}"
            )
    else:
        formatted_details = (
            f"   <b>Деталі:</b> {details[:60]}{'...' if len(details) > 60 else ''}"
        )

    # Базове форматування
    result = f"<b>{index}.</b> <b>{type_name}</b>\n"
    result += f"   <b>Дата:</b> {date_str} | <b>Статус:</b> {status_name}\n"

    # Додаємо інформацію про користувача для адмін панелі
    if show_user_info:
        first_name = request.get("first_name", "N/A")
        last_name = request.get("last_name", "")
        phone = request.get("phone", "N/A")
        req_id = request.get("id", "N/A")

        result += f"   <b>Користувач:</b> {first_name} {last_name}\n"
        result += f"   <b>Телефон:</b> {phone} | <b>ID:</b> {req_id}\n"

    result += f"{formatted_details}"

    return result


def get_requests_pagination_keyboard(
    requests: list,
    page: int = 0,
    per_page: int = 10,
    back_callback: str = "back_to_messages",
) -> InlineKeyboardMarkup:
    """Клавіатура з пагінацією для заявок"""
    total_pages = (len(requests) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(requests))

    keyboard = []

    # Кнопки навігації
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"requests_page_{page-1}")
            )
        nav_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop")
        )
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(text="➡️", callback_data=f"requests_page_{page+1}")
            )

        if nav_buttons:
            keyboard.append(nav_buttons)

    # Кнопки дій
    keyboard.append(
        [
            InlineKeyboardButton(
                text="📋 Нова заявка", callback_data="request_manager"
            ),
            InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_vehicle_requests_keyboard(
    requests: list, page: int = 0, per_page: int = 10
) -> InlineKeyboardMarkup:
    """Клавіатура для заявок з кнопками переходу до авто"""
    total_pages = (len(requests) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(requests))
    page_requests = requests[start_idx:end_idx]

    keyboard = []

    # Кнопки "Перейти до..." видалено за запитом користувача

    # Кнопки навігації
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"requests_page_{page-1}")
            )
        nav_buttons.append(
            InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop")
        )
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton(text="➡️", callback_data=f"requests_page_{page+1}")
            )

        if nav_buttons:
            keyboard.append(nav_buttons)

    # Кнопки дій
    keyboard.append(
        [
            InlineKeyboardButton(
                text="📋 Нова заявка", callback_data="request_manager"
            ),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_messages"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text == "💬 Повідомлення", StateFilter(None))
async def show_messages_menu(message: Message):
    """Показати меню повідомлень"""
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    # Отримати заявки користувача
    user_requests = await db_manager.get_manager_requests(user_id=user.id)

    active_requests = len(
        [r for r in user_requests if r["status"] in ["new", "in_progress"]]
    )
    completed_requests = len([r for r in user_requests if r["status"] == "completed"])

    text = f"""
💬 <b>Ваші повідомлення та запити</b>

📊 <b>Статистика:</b>
• Активних заявок: {active_requests}
• Виконаних заявок: {completed_requests}  
• Всього заявок: {len(user_requests)}

📋 <b>Останні заявки:</b>
"""

    # Показати останні 3 заявки
    recent_requests = sorted(
        user_requests, key=lambda x: x["created_at"], reverse=True
    )[:3]

    if recent_requests:
        for i, req in enumerate(recent_requests, 1):
            text += f"\n{format_request_display(req, i)}"
    else:
        text += "\n❌ У вас поки немає заявок."

    text += f"""

💡 <b>Швидкі дії:</b>
"""

    keyboard = [
        [
            InlineKeyboardButton(
                text="📋 Нова заявка", callback_data="request_manager"
            ),
            InlineKeyboardButton(
                text="📜 Всі заявки", callback_data="show_all_requests"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💬 Чат з менеджером", callback_data="chat_manager"
            )
        ],
    ]

    await message.answer(
        text.strip(),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "show_all_requests")
async def show_all_user_requests(callback: CallbackQuery, page: int = 0):
    """Показати всі заявки користувача з пагінацією"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("❌ Помилка! Користувач не знайдений.")
        return

    await callback.answer()

    user_requests = await db_manager.get_manager_requests(user_id=user.id)

    if not user_requests:
        await callback.message.edit_text(
            "📜 <b>Ваші заявки</b>\n\n"
            "❌ У вас поки немає заявок.\n\n"
            "💡 Створіть першу заявку через кнопку нижче.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📋 Нова заявка", callback_data="request_manager"
                        ),
                        InlineKeyboardButton(
                            text="🔙 Назад", callback_data="back_to_messages"
                        ),
                    ]
                ]
            ),
            parse_mode=get_default_parse_mode(),
        )
        return

    # Сортувати за датою (нові зверху)
    sorted_requests = sorted(user_requests, key=lambda x: x["created_at"], reverse=True)

    # Пагінація
    per_page = 10
    total_pages = (len(sorted_requests) + per_page - 1) // per_page
    page = min(page, total_pages - 1) if total_pages > 0 else 0

    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(sorted_requests))
    page_requests = sorted_requests[start_idx:end_idx]

    text = f"📜 <b>Всі ваші заявки ({len(sorted_requests)})</b>\n"
    if total_pages > 1:
        text += f"📄 <b>Сторінка {page + 1} з {total_pages}</b>\n"
    text += "\n"

    for i, req in enumerate(page_requests, start_idx + 1):
        text += f"\n{format_request_display(req, i)}"

    await callback.message.edit_text(
        text.strip(),
        reply_markup=get_vehicle_requests_keyboard(sorted_requests, page, per_page),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data.startswith("requests_page_"))
async def handle_requests_pagination(callback: CallbackQuery):
    """Обробка пагінації заявок"""
    page = int(callback.data.split("_")[2])
    await show_all_user_requests(callback, page)


# Обробник go_to_vehicle_ видалено - кнопки більше не генеруються


@router.callback_query(F.data == "back_to_messages")
async def back_to_messages_menu(callback: CallbackQuery):
    """Повернутися до меню повідомлень"""
    await callback.answer()

    # Перевіряємо реєстрацію користувача
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    # Отримати заявки користувача
    user_requests = await db_manager.get_manager_requests(user_id=user.id)

    active_requests = len(
        [r for r in user_requests if r["status"] in ["new", "in_progress"]]
    )
    completed_requests = len([r for r in user_requests if r["status"] == "completed"])

    text = f"""
💬 <b>Ваші повідомлення та запити</b>

📊 <b>Статистика:</b>
• Активних заявок: {active_requests}
• Виконаних заявок: {completed_requests}  
• Всього заявок: {len(user_requests)}

📋 <b>Останні заявки:</b>
"""

    # Показати останні 3 заявки
    recent_requests = sorted(
        user_requests, key=lambda x: x["created_at"], reverse=True
    )[:3]

    if recent_requests:
        for i, req in enumerate(recent_requests, 1):
            text += f"\n{format_request_display(req, i)}"
    else:
        text += "\n❌ У вас поки немає заявок."

    text += f"""

💡 <b>Швидкі дії:</b>
"""

    keyboard = [
        [
            InlineKeyboardButton(
                text="📋 Нова заявка", callback_data="request_manager"
            ),
            InlineKeyboardButton(
                text="📜 Всі заявки", callback_data="show_all_requests"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💬 Чат з менеджером", callback_data="chat_manager"
            )
        ],
    ]

    await callback.message.edit_text(
        text.strip(),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "request_manager")
async def start_request_creation(callback: CallbackQuery, state: FSMContext):
    """Почати створення заявки менеджеру"""
    await callback.answer()

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.edit_text(
            "❌ <b>Помилка!</b> Спочатку зареєструйтеся командою /start",
            parse_mode=get_default_parse_mode(),
        )
        return

    # Показуємо типи заявок
    keyboard = [
        [
            InlineKeyboardButton(
                text="🚛 Покупка авто", callback_data="request_type_buy"
            ),
            InlineKeyboardButton(
                text="💰 Фінансування", callback_data="request_type_finance"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔧 Сервіс", callback_data="request_type_service"
            ),
            InlineKeyboardButton(
                text="📋 Консультація", callback_data="request_type_consultation"
            ),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_messages")],
    ]

    await callback.message.edit_text(
        "📋 <b>Створення заявки</b>\n\n" "Оберіть тип заявки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data.startswith("request_type_"))
async def process_request_type(callback: CallbackQuery, state: FSMContext):
    """Обробити вибір типу заявки"""
    await callback.answer()

    request_type = callback.data.replace("request_type_", "")
    type_names = {
        "buy": "Покупка авто",
        "finance": "Фінансування",
        "service": "Сервіс",
        "consultation": "Консультація",
        "other": "Інше",
    }
    type_name = type_names.get(request_type, request_type)

    await state.update_data(request_type=request_type)
    await state.set_state(ManagerRequestStates.waiting_for_details)

    await callback.message.edit_text(
        f"📝 <b>Заявка: {type_name}</b>\n\n"
        "Опишіть детально ваш запит:\n"
        "• Що саме вас цікавить?\n"
        "• Які у вас вимоги?\n"
        "• Коли потрібна допомога?\n\n"
        "Напишіть повідомлення:",
        parse_mode=get_default_parse_mode(),
    )


@router.message(ManagerRequestStates.waiting_for_details)
async def process_request_details(message: Message, state: FSMContext):
    """Обробити деталі заявки"""
    data = await state.get_data()
    request_type = data.get("request_type", "other")

    # Отримуємо користувача з БД
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("❌ Помилка! Користувач не знайдений.")
        await state.clear()
        return

    # Створюємо заявку
    await db_manager.create_manager_request(
        user_id=user.id, request_type=request_type, details=message.text
    )

    await state.clear()

    await message.answer(
        "✅ <b>Заявка створена!</b>\n\n"
        "Ваш запит передано менеджеру. Ми зв'яжемося з вами найближчим часом.\n\n"
        "💡 Ви можете переглянути всі заявки в розділі 'Всі заявки'",
        parse_mode=get_default_parse_mode(),
    )


@router.callback_query(F.data == "chat_manager")
async def start_chat_with_manager(callback: CallbackQuery):
    """Почати чат з менеджером"""
    await callback.answer()

    await callback.message.edit_text(
        "💬 <b>Чат з менеджером</b>\n\n"
        "Для швидкого зв'язку з менеджером:\n\n"
        "📞 <b>Телефон:</b> +380 66 372 69 41\n"
        "📧 <b>Email:</b> it.dev.mtruck@gmail.com\n"
        "⏰ <b>Час роботи:</b> Пн-Пт 9:00-18:00\n\n"
        "💡 <b>Або створіть заявку</b> через кнопку 'Нова заявка' для детального опису вашого запиту.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 Створити заявку", callback_data="request_manager"
                    ),
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data="back_to_messages"
                    ),
                ]
            ]
        ),
        parse_mode=get_default_parse_mode(),
    )


@router.message(F.text == "❓ Допомога", StateFilter(None))
async def show_help_menu(message: Message):
    """Показати детальне меню допомоги"""
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)

    help_text = f"""
❓ <b>Довідка M-Truck Bot</b>

🚛 <b>Ваш помічник у пошуку вантажних автомобілів</b>

🔍 <b>Пошук авто:</b>
• <b>Всі авто</b> - перегляд всіх доступних автомобілів картками
• <b>З фільтрами</b> - детальний пошук за параметрами
• <b>Мої пошуки</b> - збережені пошукові запити
• <b>Сповіщення про нові авто</b> - налаштування підписок

📋 <b>Мої збережені:</b>
• Перегляд збережених автомобілів у вигляді карток
• <b>Зберегти/Видалити</b> - кнопки на картках авто
• <b>Навігація</b> - кнопки "Наступне/Попереднє авто"
• <b>Залишити заявку</b> - швидкий зв'язок з продавцем

💬 <b>Повідомлення:</b>
• <b>Нова заявка</b> - створити запит менеджеру
• <b>Всі заявки</b> - перегляд ваших запитів
• <b>Чат з менеджером</b> - прямий зв'язок

👤 <b>Профіль:</b>
• <b>Редагувати профіль</b> - змінити ім'я, прізвище, телефон
• <b>Налаштування</b> - сповіщення та мова інтерфейсу

🆘 <b>Технічна підтримка:</b>
• Телефон: +380 99 569 04 33
• Email: it.dev.mtruck@gmail.com
• Telegram: @mtruck_support

💡 <b>Корисні поради:</b>
• Використовуйте фільтри для точного пошуку
• Зберігайте цікаві авто для порівняння
• Залишайте заявки для швидкого зв'язку
• Підписуйтесь на сповіщення про нові авто

📱 <b>Команди бота:</b>
• /start - Головне меню
• /help - Ця довідка
• /profile - Ваш профіль
• /cancel - Скасувати операцію
"""

    await message.answer(help_text.strip(), parse_mode=get_default_parse_mode())
