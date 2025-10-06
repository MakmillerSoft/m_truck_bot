"""
Функції перекладу для адмін панелі
"""

def translate_field_value(field_key: str, value: str) -> str:
    """Переклад значень полів з англійської на українську"""
    translations = {
        "vehicle_type": {
            "container_carrier": "Контейнеровози",
            "semi_container_carrier": "Напівпричепи контейнеровози",
            "variable_body": "Змінні кузови",
            "saddle_tractor": "Сідельні тягачі",
            "trailer": "Причіпи",
            "refrigerator": "Рефрижератори",
            "van": "Фургони",
            "bus": "Буси"
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
        }
    }
    
    field_translations = translations.get(field_key, {})
    return field_translations.get(value, value)


def reverse_translate_field_value(field_key: str, value: str) -> str:
    """Зворотний переклад значень полів з української на англійську"""
    reverse_translations = {
        "vehicle_type": {
            "Контейнеровози": "container_carrier",
            "Напівпричепи контейнеровози": "semi_container_carrier",
            "Змінні кузови": "variable_body",
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




