"""
Форматери для результатів швидкого пошуку
"""
from typing import List, Optional
from app.modules.database.models import VehicleModel


def format_search_results(vehicles: List[VehicleModel], search_criteria: str) -> str:
    """Форматування результатів пошуку"""
    
    if not vehicles:
        return f"❌ <b>Результати пошуку</b>\n\nПо критерію: {search_criteria}\n\nАвто не знайдено."
    
    # Заголовок
    text = f"🔍 <b>Результати пошуку</b>\n\n"
    text += f"📋 <b>Критерій:</b> {search_criteria}\n"
    text += f"📊 <b>Знайдено авто:</b> {len(vehicles)}\n\n"
    
    # Список авто
    for i, vehicle in enumerate(vehicles, 1):
        text += f"<b>{i}.</b> "
        
        # Основна інформація
        if vehicle.brand and vehicle.model:
            text += f"{vehicle.brand} {vehicle.model}"
        elif vehicle.brand:
            text += f"{vehicle.brand}"
        elif vehicle.model:
            text += f"{vehicle.model}"
        else:
            text += "Авто"
        
        # Рік
        if vehicle.year and vehicle.year > 0:
            text += f" ({vehicle.year} р.)"
        
        # Ціна
        if vehicle.price and vehicle.price > 0:
            text += f" - {vehicle.price:,.0f} грн"
        
        # ID
        text += f" [ID: {vehicle.id}]"
        
        # Статус
        if hasattr(vehicle, 'status'):
            status_text = "Наявне" if vehicle.status == "available" else "Продане"
            text += f" - {status_text}"
        
        text += "\n"
    
    text += f"\n<i>Для детального перегляду використовуйте блок 'Всі авто'</i>"
    
    return text


def format_single_vehicle_result(vehicle: VehicleModel, search_criteria: str) -> str:
    """Форматування результату пошуку одного авто"""
    
    text = f"✅ <b>Знайдено авто</b>\n\n"
    text += f"📋 <b>Критерій пошуку:</b> {search_criteria}\n\n"
    
    # Основна інформація
    if vehicle.brand and vehicle.model:
        text += f"🚗 <b>Авто:</b> {vehicle.brand} {vehicle.model}\n"
    elif vehicle.brand:
        text += f"🚗 <b>Марка:</b> {vehicle.brand}\n"
    elif vehicle.model:
        text += f"🚗 <b>Модель:</b> {vehicle.model}\n"
    
    # Рік
    if vehicle.year and vehicle.year > 0:
        text += f"📅 <b>Рік:</b> {vehicle.year}\n"
    
    # Ціна
    if vehicle.price and vehicle.price > 0:
        text += f"💰 <b>Ціна:</b> {vehicle.price:,.0f} грн\n"
    
    # VIN
    if vehicle.vin_code:
        text += f"🔢 <b>VIN:</b> {vehicle.vin_code}\n"
    
    # Статус
    if hasattr(vehicle, 'status'):
        status_text = "Наявне" if vehicle.status == "available" else "Продане"
        text += f"📋 <b>Статус:</b> {status_text}\n"
    
    # ID
    text += f"🆔 <b>ID:</b> {vehicle.id}\n"
    
    text += f"\n<i>Для детального перегляду використовуйте блок 'Всі авто'</i>"
    
    return text


