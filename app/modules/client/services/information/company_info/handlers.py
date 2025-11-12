"""
Обробники для інформації про компанію (клієнтська частина)
"""
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter

from app.utils.formatting import get_default_parse_mode

from .keyboards import get_company_info_keyboard
from . import company_info_router as router



@router.message(F.text == "🏢 Про компанію", StateFilter(None))
async def show_company_info_message(message: Message):
    info_text = (
        """
<a href="https://t.me/mtruck_sales"><b>Продаж та фінансування техніки для бізнесу.</b></a>

🚘 <b>Наш асортимент:</b>

• <a href="https://t.me/mtruck_sales/14">Вантажні фургони та рефрижератори (3,5-20 т)</a>
• <a href="https://t.me/mtruck_sales/4">Контейнеровози (з причепами)</a>
• <a href="http://t.me/mtruck_sales/18">Сідельні тягачі та напівпричепи</a>
• <a href="https://t.me/mtruck_sales/12">Змінні кузови</a>

Усі авто — власні, офіційно імпортовані, від перевірених постачальників ЄС. 

💰 <b>Фінансування:</b>
<blockquote>
• Прямі партнери банків та лізингових компаній.
• Програма “Доступні кредити 5-7-9%”.
• Індивідуальні умови для кожного клієнта.
• Можливий старт з 0% внеску.
</blockquote>

📈 <b>Повний супровід:</b>
<blockquote>
• Підбір авто (з наявних або під замовлення).
• Оформлення фінансування.
• Своєчасне ПДВ.
• Реєстрація в СЦ МВС, доставка по Україні.
</blockquote>

<a href="https://t.me/mtruck_sales">⚙️ M-TRUCK — швидкий старт для вашого бізнесу.</a>
"""
    ).strip()

    await message.answer(
        info_text,
        reply_markup=get_company_info_keyboard(),
        parse_mode=get_default_parse_mode(),
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "client_company")
async def show_company_info_callback(callback: CallbackQuery):
    await callback.answer()
    info_text = (
        """
<a href="https://t.me/mtruck_sales"><b>Продаж та фінансування техніки для бізнесу.</b></a>

🚘 <b>Наш асортимент:</b>

• <a href="https://t.me/mtruck_sales/14">Вантажні фургони та рефрижератори (3,5-20 т)</a>
• <a href="https://t.me/mtruck_sales/4">Контейнеровози (з причепами)</a>
• <a href="http://t.me/mtruck_sales/18">Сідельні тягачі та напівпричепи</a>
• <a href="https://t.me/mtruck_sales/12">Змінні кузови</a>

Усі авто — власні, офіційно імпортовані, від перевірених постачальників ЄС. 

💰 <b>Фінансування:</b>
<blockquote>
• Прямі партнери банків та лізингових компаній.
• Програма “Доступні кредити 5-7-9%”.
• Індивідуальні умови для кожного клієнта.
• Можливий старт з 0% внеску.
</blockquote>

📈 <b>Повний супровід:</b>
<blockquote>
• Підбір авто (з наявних або під замовлення).
• Оформлення фінансування.
• Своєчасне ПДВ.
• Реєстрація в СЦ МВС, доставка по Україні.
</blockquote>

<a href="https://t.me/mtruck_sales">⚙️ M-TRUCK — швидкий старт для вашого бізнесу.</a>
"""
    ).strip()
    from .keyboards import get_company_info_keyboard
    await callback.message.edit_text(
        info_text,
        reply_markup=get_company_info_keyboard(),
        parse_mode=get_default_parse_mode(),
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "website_placeholder")
async def website_under_development(callback: CallbackQuery):
    """Повідомлення про те, що сайт у розробці"""
    await callback.answer(
        "🌐 Сайт наразі в розробці.\n\n"
        "📢 Слідкуйте за новинами!",
        show_alert=True
    )


