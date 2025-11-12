"""
Генератор Excel файлів з даних БД
"""
import logging
from datetime import datetime
from typing import List, Optional
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.modules.database.manager import db_manager

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Клас для експорту даних в Excel"""
    
    def __init__(self):
        self.wb = Workbook()
        # Видаляємо дефолтний лист
        if "Sheet" in self.wb.sheetnames:
            del self.wb["Sheet"]
    
    def _style_header(self, ws, max_col: int):
        """Стилізувати заголовок таблиці"""
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        
        for col in range(1, max_col + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
    
    def _auto_size_columns(self, ws):
        """Автоматично підібрати ширину колонок"""
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    async def export_users(self) -> None:
        """Експортувати користувачів"""
        ws = self.wb.create_sheet("Користувачі")
        
        # Заголовки
        headers = [
            "ID", "Telegram ID", "Ім'я", "Username", "Телефон", 
            "Роль", "Заблокований", "Дата реєстрації", "Останній вхід"
        ]
        ws.append(headers)
        
        # Отримуємо користувачів
        users = await db_manager.get_all_users()
        
        for user in users:
            # Безпечне отримання з словника
            ws.append([
                user.get('id', ''),
                user.get('telegram_id', ''),
                user.get('first_name', '') or user.get('name', '') or "",
                user.get('username', '') or "",
                user.get('phone', '') or "",
                user.get('role', '') or "",
                "Так" if user.get('is_banned') or user.get('is_blocked') else "Ні",
                user.get('created_at', '') or "",
                user.get('last_login', '') or ""
            ])
        
        self._style_header(ws, len(headers))
        self._auto_size_columns(ws)
        
        logger.info(f"✅ Експортовано {len(users)} користувачів")
    
    async def export_vehicles(self) -> None:
        """Експортувати авто"""
        ws = self.wb.create_sheet("Авто")
        
        # Заголовки
        headers = [
            "ID", "Тип", "Марка", "Модель", "VIN", "Рік", "Стан", 
            "Ціна", "Пробіг", "Паливо", "Коробка", "Локація", 
            "Статус", "Активність", "Продавець ID", "Створено", "Оновлено"
        ]
        ws.append(headers)
        
        # Отримуємо авто
        vehicles = await db_manager.get_all_vehicles()
        
        for vehicle in vehicles:
            # Безпечне отримання з словника
            ws.append([
                vehicle.get('id', ''),
                vehicle.get('vehicle_type', '') or "",
                vehicle.get('brand', '') or "",
                vehicle.get('model', '') or "",
                vehicle.get('vin_code', '') or "",
                vehicle.get('year', '') or "",
                vehicle.get('condition', '') or "",
                vehicle.get('price', '') or "",
                vehicle.get('mileage', '') or "",
                vehicle.get('fuel_type', '') or "",
                vehicle.get('transmission', '') or "",
                vehicle.get('location', '') or "",
                vehicle.get('status', '') or "",
                "Активне" if vehicle.get('is_active') else "Неактивне",
                vehicle.get('seller_id', '') or "",
                vehicle.get('created_at', '') or "",
                vehicle.get('updated_at', '') or ""
            ])
        
        self._style_header(ws, len(headers))
        self._auto_size_columns(ws)
        
        logger.info(f"✅ Експортовано {len(vehicles)} авто")
    
    async def export_requests(self) -> None:
        """Експортувати заявки"""
        ws = self.wb.create_sheet("Заявки")
        
        # Заголовки (додано колонки для логування)
        headers = [
            "ID", "Користувач ID", "Авто ID", "Тип заявки", "Деталі", 
            "Статус", "ID адміна", "Оброблено", "Створено", "Оновлено"
        ]
        ws.append(headers)
        
        # Отримуємо заявки
        requests = await db_manager.get_all_requests()
        
        for request in requests:
            # request - це словник
            ws.append([
                request.get('id', ''),
                request.get('user_id', ''),
                request.get('vehicle_id', ''),
                request.get('request_type', ''),
                request.get('details', ''),
                request.get('status', ''),
                request.get('processed_by_admin_id', ''),  # Новий стовпець
                request.get('processed_at', ''),  # Новий стовпець
                request.get('created_at', ''),
                request.get('updated_at', '')
            ])
        
        self._style_header(ws, len(headers))
        self._auto_size_columns(ws)
        
        logger.info(f"✅ Експортовано {len(requests)} заявок")
    
    async def export_broadcasts(self) -> None:
        """Експортувати розсилки"""
        ws = self.wb.create_sheet("Розсилки")
        
        # Заголовки
        headers = [
            "ID", "Текст", "Кнопка (текст)", "Кнопка (URL)", 
            "Тип медіа", "Статус", "Створено", "Заплановано"
        ]
        ws.append(headers)
        
        # Отримуємо розсилки
        broadcasts = await db_manager.get_all_broadcasts_raw()
        
        for broadcast in broadcasts:
            # Безпечне отримання з словника
            text = broadcast.get('text', '') or ""
            text_short = (text[:50] + "...") if text and len(text) > 50 else text
            
            ws.append([
                broadcast.get('id', ''),
                text_short,
                broadcast.get('button_text', '') or "",
                broadcast.get('button_url', '') or "",
                broadcast.get('media_type', '') or "",
                broadcast.get('status', '') or "",
                broadcast.get('created_at', '') or "",
                broadcast.get('scheduled_at', '') or ""
            ])
        
        self._style_header(ws, len(headers))
        self._auto_size_columns(ws)
        
        logger.info(f"✅ Експортовано {len(broadcasts)} розсилок")
    
    async def export_all(self) -> None:
        """Експортувати всі дані"""
        await self.export_users()
        await self.export_vehicles()
        await self.export_requests()
        await self.export_broadcasts()
        
        logger.info("✅ Експортовано всі дані")
    
    def save(self, filename: str) -> str:
        """Зберегти файл"""
        self.wb.save(filename)
        logger.info(f"📁 Файл збережено: {filename}")
        return filename


async def generate_excel_export(export_type: str) -> str:
    """
    Генерувати Excel файл з експортом даних
    
    Args:
        export_type: Тип експорту (users, vehicles, requests, broadcasts, all)
    
    Returns:
        str: Шлях до згенерованого файлу
    """
    exporter = ExcelExporter()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"export_{export_type}_{timestamp}.xlsx"
    
    if export_type == "users":
        await exporter.export_users()
    elif export_type == "vehicles":
        await exporter.export_vehicles()
    elif export_type == "requests":
        await exporter.export_requests()
    elif export_type == "broadcasts":
        await exporter.export_broadcasts()
    elif export_type == "all":
        await exporter.export_all()
    else:
        raise ValueError(f"Невідомий тип експорту: {export_type}")
    
    return exporter.save(filename)
