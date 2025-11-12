"""
Функції перекладу для адмін панелі
"""

def translate_field_value(field_key: str, value: str) -> str:
    """Переклад значень полів з англійської на українську"""
    translations = {
        "vehicle_type": {
            # Показуємо 4 об'єднані категорії
            "saddle_tractor": "Сідельні тягачі та напівпричепи",
            "semi_container_carrier": "Сідельні тягачі та напівпричепи",
            "van": "Вантажні фургони та рефрижератори",
            "refrigerator": "Вантажні фургони та рефрижератори",
            "variable_body": "Змінні кузови",
            "container_carrier": "Контейнеровози (з причепами)",
            "trailer": "Контейнеровози (з причепами)",
            "bus": "Сідельні тягачі та напівпричепи"
        },
        "condition": {
            "new": "Новий",
            "used": "Вживане"
        },
        "status": {
            "available": "Наявне",
            "sold": "Продане"
        },
        "fuel_type": {
            "diesel": "Дизель",
            "petrol": "Бензин",
            "gas": "Газ",
            "gas_petrol": "Газ/Бензин",
            "electric": "Електричний"
        },
        "transmission": {
            "automatic": "Автоматична",
            "manual": "Механічна",
            "robot": "Робот",
            "cvt": "CVT"
        },
        "location": {
            "lutsk": "Луцьк"
        },
        # === НОВІ ПЕРЕКЛАДИ ДЛЯ ІНШИХ ТАБЛИЦЬ ===
        "role": {
            "buyer": "Покупець",
            "admin": "Адміністратор"
        },
        "request_type": {
            "general": "Загальна заявка",
            "vehicle_application": "Заявка на авто"
        },
        "request_status": {
            "new": "Нова",
            "in_progress": "В обробці",
            "completed": "Виконана",
            "cancelled": "Скасована"
        },
        "broadcast_status": {
            "draft": "Чернетка",
            "sent": "Відправлено",
            "scheduled": "Заплановано"
        },
        "schedule_period": {
            "none": "Не повторювати",
            "daily": "Щоденно",
            "weekly": "Щотижня"
        },
        "media_type": {
            "photo": "Фото",
            "video": "Відео",
            "media_group": "Медіагрупа"
        }
    }
    
    field_translations = translations.get(field_key, {})
    return field_translations.get(value, value)


def reverse_translate_field_value(field_key: str, value: str) -> str:
    """Зворотний переклад значень полів з української на англійську"""
    reverse_translations = {
        "vehicle_type": {
            # 4 об'єднані категорії -> представницькі значення EN
            "Сідельні тягачі та напівпричепи": "saddle_tractor",
            "Вантажні фургони та рефрижератори": "van",
            "Змінні кузови": "variable_body",
            "Контейнеровози (з причепами)": "container_carrier",
            # Зворотна сумісність зі старими підписами
            "Контейнеровози": "container_carrier",
            "Напівпричепи контейнеровози": "semi_container_carrier",
            "Сідельні тягачі": "saddle_tractor",
            "Причіпи": "trailer",
            "Рефрижератори": "refrigerator",
            "Фургони": "van",
            "Буси": "bus"
        },
        "condition": {
            "Новий": "new",
            "Вживане": "used"
        },
        "status": {
            "Наявне": "available",
            "Продане": "sold"
        },
        "fuel_type": {
            "Дизель": "diesel",
            "Бензин": "petrol",
            "Газ": "gas",
            "Газ/Бензин": "gas_petrol",
            "Електричний": "electric"
        },
        "transmission": {
            "Автоматична": "automatic",
            "Механічна": "manual",
            "Робот": "robot",
            "CVT": "cvt"
        },
        "location": {
            "Луцьк": "lutsk"
        }
    }
    
    field_reverse_translations = reverse_translations.get(field_key, {})
    return field_reverse_translations.get(value, value)




