"""
Клавіатури для модуля пошуку
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_search_keyboard() -> InlineKeyboardMarkup:
    """Головна клавіатура пошуку"""
    keyboard = [
        [
            InlineKeyboardButton(text="🚛 Всі авто", callback_data="quick_search"),
            InlineKeyboardButton(text="🎛️ З фільтрами", callback_data="filter_search"),
        ],
        [
            InlineKeyboardButton(text="💾 Мої пошуки", callback_data="saved_searches"),
            InlineKeyboardButton(
                text="🔔 Сповіщення про нові авто", callback_data="search_subscriptions"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура фільтрів"""
    keyboard = [
        [
            InlineKeyboardButton(text="🚛 Тип авто", callback_data="filter_type"),
            InlineKeyboardButton(text="🏷️ Марка", callback_data="filter_brand"),
        ],
        [
            InlineKeyboardButton(text="💰 Ціна", callback_data="filter_price"),
            InlineKeyboardButton(text="📅 Рік", callback_data="filter_year"),
        ],
        [
            InlineKeyboardButton(text="🛣️ Пробіг", callback_data="filter_mileage"),
            InlineKeyboardButton(text="📍 Місце", callback_data="filter_location"),
        ],
        [
            InlineKeyboardButton(text="🔧 Двигун", callback_data="filter_engine"),
            InlineKeyboardButton(text="⛽ Паливо", callback_data="filter_fuel"),
        ],
        [
            InlineKeyboardButton(
                text="📦 Вантажопідйомність", callback_data="filter_capacity"
            ),
            InlineKeyboardButton(text="⭐ Стан", callback_data="filter_condition"),
        ],
        [
            InlineKeyboardButton(text="📊 Сортування", callback_data="filter_sort"),
            InlineKeyboardButton(
                text="🎯 Швидкі фільтри", callback_data="filter_quick"
            ),
        ],
        [
            InlineKeyboardButton(
                text="✅ Застосувати фільтри", callback_data="filter_apply"
            ),
            InlineKeyboardButton(text="🔄 Скинути", callback_data="filter_reset"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_search")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_search_results_keyboard(vehicles: list, page: int = 0) -> InlineKeyboardMarkup:
    """Клавіатура результатів пошуку"""
    keyboard = []

    # Кнопки перегляду авто (по 3 в ряд)
    for i in range(0, len(vehicles), 3):
        row = []
        for j in range(i, min(i + 3, len(vehicles))):
            vehicle = vehicles[j]
            row.append(
                InlineKeyboardButton(
                    text=f"{j+1}. {vehicle.brand} {vehicle.model}",
                    callback_data=f"vehicle_details_{vehicle.id}",
                )
            )
        keyboard.append(row)

    # Кнопки дій
    action_buttons = [
        InlineKeyboardButton(text="💾 Зберегти пошук", callback_data="save_search"),
        InlineKeyboardButton(
            text="🔔 Отримувати сповіщення", callback_data="subscribe_search"
        ),
    ]
    keyboard.append(action_buttons)

    # Навігація
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Попередні", callback_data=f"search_page_{page-1}"
            )
        )
    nav_buttons.append(
        InlineKeyboardButton(text="🔍 Новий пошук", callback_data="back_to_search")
    )
    if len(vehicles) >= 10:  # Показувати кнопку "Далі" якщо є ще результати
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Наступні", callback_data=f"search_page_{page+1}"
            )
        )

    keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_vehicle_detail_keyboard(vehicle_id: int) -> InlineKeyboardMarkup:
    """Клавіатура детального перегляду авто"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📞 Зв'язатись з продавцем",
                callback_data=f"contact_seller_{vehicle_id}",
            ),
            InlineKeyboardButton(
                text="❤️ Додати в обране", callback_data=f"favorite_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 Порівняти", callback_data=f"compare_{vehicle_id}"
            ),
            InlineKeyboardButton(
                text="📱 Поділитися", callback_data=f"share_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📋 Звіт про авто", callback_data=f"vehicle_report_{vehicle_id}"
            ),
            InlineKeyboardButton(
                text="⚠️ Поскаржитися", callback_data=f"report_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Повернутись назад", callback_data="back_to_results"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_vehicle_card_keyboard(
    vehicle_id: int,
    is_first: bool = False,
    is_last: bool = False,
    is_saved: bool = False,
) -> InlineKeyboardMarkup:
    """Клавіатура для картки авто в режимі 'Всі авто'"""
    # Динамічна кнопка збереження
    save_button_text = "💔 Видалити з обраного" if is_saved else "❤️ Зберегти"
    save_button_callback = (
        f"unsave_vehicle_{vehicle_id}" if is_saved else f"favorite_vehicle_{vehicle_id}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                text=save_button_text, callback_data=save_button_callback
            ),
            InlineKeyboardButton(
                text="📝 Залишити заявку", callback_data=f"contact_seller_{vehicle_id}"
            ),
        ]
    ]

    # Кнопки навігації
    nav_buttons = []
    if not is_first:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Попереднє авто", callback_data=f"prev_vehicle_{vehicle_id}"
            )
        )
    if not is_last:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Наступне авто", callback_data=f"next_vehicle_{vehicle_id}"
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🔙 Повернутись назад", callback_data="back_to_search"
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_saved_searches_keyboard(searches: list) -> InlineKeyboardMarkup:
    """Клавіатура збережених пошуків"""
    keyboard = []

    for search in searches:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"🔍 {search.get('name', 'Пошук')} ({search.get('count', 0)} результатів)",
                    callback_data=f"run_saved_search_{search['id']}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="🗑️ Видалити мої пошуки", callback_data="delete_saved_searches"
            ),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_search"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_sort_options_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура опцій сортування"""
    keyboard = [
        [
            InlineKeyboardButton(text="💰 За ціною ↑", callback_data="sort_price_asc"),
            InlineKeyboardButton(text="💰 За ціною ↓", callback_data="sort_price_desc"),
        ],
        [
            InlineKeyboardButton(text="📅 За роком ↑", callback_data="sort_year_asc"),
            InlineKeyboardButton(text="📅 За роком ↓", callback_data="sort_year_desc"),
        ],
        [
            InlineKeyboardButton(
                text="🛣️ За пробігом ↑", callback_data="sort_mileage_asc"
            ),
            InlineKeyboardButton(
                text="🛣️ За пробігом ↓", callback_data="sort_mileage_desc"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 За датою додавання", callback_data="sort_date_desc"
            ),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_results"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_filter_quick_keyboard() -> InlineKeyboardMarkup:
    """Швидкі фільтри"""
    keyboard = [
        [
            InlineKeyboardButton(text="🆕 Нові авто", callback_data="quick_filter_new"),
            InlineKeyboardButton(text="💰 До $30k", callback_data="quick_filter_cheap"),
        ],
        [
            InlineKeyboardButton(
                text="⭐ Преміум", callback_data="quick_filter_premium"
            ),
            InlineKeyboardButton(
                text="🇺🇦 В Україні", callback_data="quick_filter_ukraine"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🚛 Тільки вантажівки", callback_data="quick_filter_trucks"
            ),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_search"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_engine_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура фільтру двигуна"""
    keyboard = [
        [
            InlineKeyboardButton(text="⛽ Дизель", callback_data="engine_diesel"),
            InlineKeyboardButton(text="⛽ Бензин", callback_data="engine_gasoline"),
        ],
        [
            InlineKeyboardButton(text="⚡ Гібрид", callback_data="engine_hybrid"),
            InlineKeyboardButton(text="🔋 Електро", callback_data="engine_electric"),
        ],
        [
            InlineKeyboardButton(text="🔧 Газ", callback_data="engine_gas"),
            InlineKeyboardButton(text="❌ Будь-який", callback_data="engine_any"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_filters")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_fuel_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура фільтру палива"""
    keyboard = [
        [
            InlineKeyboardButton(text="⛽ Дизель", callback_data="fuel_diesel"),
            InlineKeyboardButton(text="⛽ Бензин", callback_data="fuel_gasoline"),
        ],
        [
            InlineKeyboardButton(text="⚡ Гібрид", callback_data="fuel_hybrid"),
            InlineKeyboardButton(text="🔋 Електро", callback_data="fuel_electric"),
        ],
        [
            InlineKeyboardButton(text="🔧 Газ", callback_data="fuel_gas"),
            InlineKeyboardButton(text="❌ Будь-який", callback_data="fuel_any"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_filters")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_condition_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура фільтру стану авто"""
    keyboard = [
        [
            InlineKeyboardButton(text="🆕 Новий", callback_data="condition_new"),
            InlineKeyboardButton(
                text="⭐ Відмінний", callback_data="condition_excellent"
            ),
        ],
        [
            InlineKeyboardButton(text="👍 Хороший", callback_data="condition_good"),
            InlineKeyboardButton(text="⚠️ Задовільний", callback_data="condition_fair"),
        ],
        [
            InlineKeyboardButton(
                text="🔧 На запчастини", callback_data="condition_parts"
            ),
            InlineKeyboardButton(text="❌ Будь-який", callback_data="condition_any"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_filters")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_capacity_filter_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура фільтру вантажопідйомності"""
    keyboard = [
        [
            InlineKeyboardButton(text="📦 До 3.5т", callback_data="capacity_light"),
            InlineKeyboardButton(text="🚛 3.5-7.5т", callback_data="capacity_medium"),
        ],
        [
            InlineKeyboardButton(text="🚚 7.5-16т", callback_data="capacity_heavy"),
            InlineKeyboardButton(text="🚛 16т+", callback_data="capacity_extra_heavy"),
        ],
        [
            InlineKeyboardButton(text="❌ Будь-яка", callback_data="capacity_any"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_filters"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_saved_vehicles_keyboard(vehicles: list, page: int = 0) -> InlineKeyboardMarkup:
    """Клавіатура збережених авто"""
    keyboard = []

    # Кнопки перегляду авто (по 2 в ряд)
    for i in range(0, len(vehicles), 2):
        row = []
        for j in range(i, min(i + 2, len(vehicles))):
            vehicle = vehicles[j]
            row.append(
                InlineKeyboardButton(
                    text=f"{j+1}. {vehicle['brand']} {vehicle['model']}",
                    callback_data=f"saved_vehicle_{vehicle['id']}",
                )
            )
        keyboard.append(row)

    # Кнопки дій
    action_buttons = [
        InlineKeyboardButton(text="📝 Додати нотатки", callback_data="add_notes"),
        InlineKeyboardButton(text="📂 Категорії", callback_data="manage_categories"),
    ]
    keyboard.append(action_buttons)

    # Навігація
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Попередні", callback_data=f"saved_page_{page-1}"
            )
        )
    nav_buttons.append(
        InlineKeyboardButton(text="🔍 Новий пошук", callback_data="back_to_search")
    )
    if len(vehicles) >= 10:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Наступні", callback_data=f"saved_page_{page+1}"
            )
        )

    keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_saved_vehicle_detail_keyboard(
    vehicle_id: int, is_saved: bool = True
) -> InlineKeyboardMarkup:
    """Клавіатура детального перегляду збереженого авто"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📝 Редагувати нотатки", callback_data=f"edit_notes_{vehicle_id}"
            ),
            InlineKeyboardButton(
                text="📂 Змінити категорію",
                callback_data=f"change_category_{vehicle_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 Порівняти", callback_data=f"compare_{vehicle_id}"
            ),
            InlineKeyboardButton(
                text="📱 Поділитися", callback_data=f"share_{vehicle_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔔 Налаштувати сповіщення",
                callback_data=f"notifications_{vehicle_id}",
            ),
            InlineKeyboardButton(
                text="💔 Видалити з збережених",
                callback_data=f"unsave_vehicle_{vehicle_id}",
            ),
        ],
        [InlineKeyboardButton(text="🔙 До збережених", callback_data="back_to_saved")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_keyboard() -> InlineKeyboardMarkup:
    """Клавіатура категорій збережених авто"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="⭐ Улюблені", callback_data="category_favorites"
            ),
            InlineKeyboardButton(text="💰 Для покупки", callback_data="category_buy"),
        ],
        [
            InlineKeyboardButton(
                text="🔍 Розглядаю", callback_data="category_considering"
            ),
            InlineKeyboardButton(
                text="📊 Порівняння", callback_data="category_comparison"
            ),
        ],
        [
            InlineKeyboardButton(
                text="❌ Відхилені", callback_data="category_rejected"
            ),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_saved"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_search_history_keyboard(searches: list) -> InlineKeyboardMarkup:
    """Клавіатура історії пошуків"""
    keyboard = []

    # Кнопки пошуків (по 2 в ряд)
    for i in range(0, len(searches), 2):
        row = []
        for j in range(i, min(i + 2, len(searches))):
            search = searches[j]
            row.append(
                InlineKeyboardButton(
                    text=f"🔍 {search['search_name'][:20]}{'...' if len(search['search_name']) > 20 else ''}",
                    callback_data=f"repeat_search_{search['id']}",
                )
            )
        keyboard.append(row)

    # Кнопки дій
    keyboard.append(
        [
            InlineKeyboardButton(
                text="🗑️ Очистити історію", callback_data="clear_search_history"
            ),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_search"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_subscriptions_keyboard(subscriptions: list) -> InlineKeyboardMarkup:
    """Клавіатура підписок"""
    keyboard = []

    if not subscriptions:
        # Якщо підписок немає
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="➕ Створити підписку", callback_data="create_subscription"
                )
            ]
        )
    else:
        # Кнопки підписок
        for sub in subscriptions:
            status_icon = "✅" if sub["is_active"] else "❌"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"{status_icon} {sub['subscription_name']}",
                        callback_data=f"subscription_toggle_{sub['id']}",
                    )
                ]
            )

        # Кнопки дій
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="➕ Створити підписку", callback_data="create_subscription"
                ),
                InlineKeyboardButton(
                    text="🗑️ Видалити всі", callback_data="delete_all_subscriptions"
                ),
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_search")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
