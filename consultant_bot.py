# -*- coding: utf-8 -*-
"""
Бот-консультант для сбора ТЗ на персональную настройку бота записи
"""

import os
import re
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("CONSULTANT_BOT_TOKEN")
SPREADSHEET_ID = os.getenv("TZ_SPREADSHEET_ID")
GOOGLE_CREDENTIALS_B64 = os.getenv("GOOGLE_CREDENTIALS")

if not all([BOT_TOKEN, SPREADSHEET_ID, GOOGLE_CREDENTIALS_B64]):
    raise ValueError("❌ Не заданы переменные окружения!")

# Настройка Google Sheets
import base64, json
b64_clean = GOOGLE_CREDENTIALS_B64.strip()
padding = len(b64_clean) % 4
if padding: b64_clean += '=' * (4 - padding)
creds_dict = json.loads(base64.b64decode(b64_clean).decode('utf-8'))

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
tz_sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Состояния опроса
class ConsultationStates(StatesGroup):
    brand_name = State()
    business_type = State()
    city = State()
    services = State()
    service_duration = State()
    work_days = State()
    work_hours = State()
    specialists_count = State()
    logo_url = State()
    colors_emojis = State()
    contact_info = State()
    tech_contact = State()
    hosting_needed = State()
    extra_features = State()
    final_confirm = State()

router = Router()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Запуск опроса
@router.message(Command("start"))
async def start_consultation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Привет! Я помогу собрать техническое задание для настройки персонального бота записи.\n\n"
        "Готовы начать? Напишите название вашего бренда или компании:"
    )
    await state.set_state(ConsultationStates.brand_name)

# Последовательные шаги
@router.message(ConsultationStates.brand_name)
async def handle_brand(message: Message, state: FSMContext):
    await state.update_data(brand_name=message.text.strip())
    await message.answer("🏢 Какой у вас вид деятельности? (салон, репетитор, тренер, массаж и т.д.)")
    await state.set_state(ConsultationStates.business_type)

@router.message(ConsultationStates.business_type)
async def handle_business(message: Message, state: FSMContext):
    await state.update_data(business_type=message.text.strip())
    await message.answer("📍 В каком городе вы находитесь?")
    await state.set_state(ConsultationStates.city)

@router.message(ConsultationStates.city)
async def handle_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await message.answer(
        "✂️ Перечислите услуги через запятую:\n"
        "Пример: Стрижка, Окрашивание, Маникюр"
    )
    await state.set_state(ConsultationStates.services)

@router.message(ConsultationStates.services)
async def handle_services(message: Message, state: FSMContext):
    await state.update_data(services=message.text.strip())
    await message.answer(
        "⏱️ Укажите время выполнения каждой услуги (в минутах):\n"
        "Пример: 60, 90, 45"
    )
    await state.set_state(ConsultationStates.service_duration)

@router.message(ConsultationStates.service_duration)
async def handle_duration(message: Message, state: FSMContext):
    await state.update_data(service_duration=message.text.strip())
    await message.answer(
        "📅 Рабочие дни:\n"
        "1 — будни, 2 — выходные, 3 — ежедневно"
    )
    await state.set_state(ConsultationStates.work_days)

@router.message(ConsultationStates.work_days)
async def handle_work_days(message: Message, state: FSMContext):
    await state.update_data(work_days=message.text.strip())
    await message.answer("🕗 Часы работы (например: 10:00–20:00)")
    await state.set_state(ConsultationStates.work_hours)

@router.message(ConsultationStates.work_hours)
async def handle_work_hours(message: Message, state: FSMContext):
    await state.update_data(work_hours=message.text.strip())
    await message.answer("👥 Сколько специалистов в вашей команде?")
    await state.set_state(ConsultationStates.specialists_count)

@router.message(ConsultationStates.specialists_count)
async def handle_specialists(message: Message, state: FSMContext):
    await state.update_data(specialists_count=message.text.strip())
    await message.answer(
        "🖼️ Есть ли у вас логотип? Отправьте ссылку или файл.\n"
        "Если нет — напишите «Нет»."
    )
    await state.set_state(ConsultationStates.logo_url)

@router.message(ConsultationStates.logo_url)
async def handle_logo(message: Message, state: FSMContext):
    url = message.text.strip() if message.text else "Файл отправлен отдельно"
    await state.update_data(logo_url=url)
    await message.answer(
        "🎨 Предпочтительные цвета / эмодзи для бота?\n"
        "Пример: красный, снежинки ❄️, золото ✨"
    )
    await state.set_state(ConsultationStates.colors_emojis)

@router.message(ConsultationStates.colors_emojis)
async def handle_colors(message: Message, state: FSMContext):
    await state.update_data(colors_emojis=message.text.strip())
    await message.answer(
        "📞 Контактная информация для клиентов:\n"
        "Телефон, соцсети, адрес"
    )
    await state.set_state(ConsultationStates.contact_info)

@router.message(ConsultationStates.contact_info)
async def handle_contacts(message: Message, state: FSMContext):
    await state.update_data(contact_info=message.text.strip())
    await message.answer(
        "👨‍💻 Кто будет отвечать за техподдержку после запуска?\n"
        "(Ваше имя / сотрудник / агентство)"
    )
    await state.set_state(ConsultationStates.tech_contact)

@router.message(ConsultationStates.tech_contact)
async def handle_tech_contact(message: Message, state: FSMContext):
    await state.update_data(tech_contact=message.text.strip())
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data="hosting_yes")
    kb.button(text="Нет", callback_data="hosting_no")
    await message.answer("⚙️ Нужна ли помощь с размещением бота на хостинге (Railway/Render)?", reply_markup=kb.as_markup())
    await state.set_state(ConsultationStates.hosting_needed)

@router.callback_query(ConsultationStates.hosting_needed, F.data.startswith("hosting_"))
async def handle_hosting(callback: CallbackQuery, state: FSMContext):
    choice = "Да" if callback.data == "hosting_yes" else "Нет"
    await state.update_data(hosting_needed=choice)
    await callback.message.edit_text(
        "🎁 Дополнительные функции (через запятую):\n"
        "Напоминания, аналитика, мультиязычность, несколько мастеров"
    )
    await state.set_state(ConsultationStates.extra_features)

@router.message(ConsultationStates.extra_features)
async def handle_extra(message: Message, state: FSMContext):
    await state.update_data(extra_features=message.text.strip())
    
    # Сохраняем в Google Таблицу
    data = await state.get_data()
    try:
        tz_sheet.append_row([
            data.get("brand_name", ""),
            data.get("business_type", ""),
            data.get("city", ""),
            data.get("services", ""),
            data.get("service_duration", ""),
            data.get("work_days", ""),
            data.get("work_hours", ""),
            data.get("specialists_count", ""),
            data.get("logo_url", ""),
            data.get("colors_emojis", ""),
            data.get("contact_info", ""),
            data.get("tech_contact", ""),
            data.get("hosting_needed", ""),
            data.get("extra_features", ""),
            str(message.from_user.id),
            message.from_user.username or "",
            str(message.date)
        ])
        await message.answer(
            "✅ Спасибо! Ваше техническое задание сохранено.\n\n"
            "В ближайшее время мы свяжемся с вами для уточнения деталей и оплаты ($99).\n"
            "Срок настройки: 1–2 дня."
        )
    except Exception as e:
        logging.error(f"Ошибка сохранения ТЗ: {e}")
        await message.answer("❌ Не удалось сохранить ТЗ. Попробуйте позже.")
    
    await state.clear()

# Запуск
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())