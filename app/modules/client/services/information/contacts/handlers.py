"""
Обробники для контактної інформації (клієнтська частина)
"""
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter

from app.utils.formatting import get_default_parse_mode

from .keyboards import get_contacts_keyboard
from . import contacts_router as router



@router.message(F.text == "📞 Контакти", StateFilter(None))
async def show_contacts_message(message: Message):
    contacts_text = (
        """
📞 <b>Контакти M-Truck Company</b>

🏢 <b>Головний офіс:</b>
📍 вул. Зв'язківців, 1Б, Луцьк, Волинська область, 43000

🚚 <b>Торговий майданчик:</b>
📍 вул. Об'їздна, 20, Волинська область

📞 <b>Телефони:</b>
• 👨‍💼 <b>Менеджер:</b> <a href="tel:+380502311339">+380502311339</a>
• 🔧 <b>Техпідтримка:</b> <a href="tel:+380995690433">+380995690433</a>

📧 <b>Email:</b>
• 📨 <a href="mailto:it.dev.mtruck@gmail.com">it.dev.mtruck@gmail.com</a>
"""
    ).strip()

    await message.answer(
        contacts_text,
        reply_markup=get_contacts_keyboard(),
        parse_mode=get_default_parse_mode(),
        disable_web_page_preview=False,
    )


@router.callback_query(F.data == "client_contacts")
async def show_contacts_callback(callback: CallbackQuery):
    await callback.answer()
    contacts_text = (
        """
📞 <b>Контакти M-Truck Company</b>

🏢 <b>Головний офіс:</b>
📍 вул. Зв'язківців, 1Б, Луцьк, Волинська область, 43000

🚚 <b>Торговий майданчик:</b>
📍 вул. Об'їздна, 20, Волинська область

📞 <b>Телефони:</b>
• 👨‍💼 <b>Менеджер:</b> <a href="tel:+380502311339">+380502311339</a>
• 🔧 <b>Техпідтримка:</b> <a href="tel:+380995690433">+380995690433</a>

📧 <b>Email:</b>
• 📨 <a href="mailto:it.dev.mtruck@gmail.com">it.dev.mtruck@gmail.com</a>
"""
    ).strip()
    from .keyboards import get_contacts_keyboard
    await callback.message.edit_text(
        contacts_text,
        reply_markup=get_contacts_keyboard(),
        parse_mode=get_default_parse_mode(),
        disable_web_page_preview=False,
    )


