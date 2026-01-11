# -*- coding: utf-8 -*-
"""
Бот-консультант для сбора технического задания на персональную настройку бота записи
"""

import os
import base64
import json
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

# === ЗАГРУЗКА НАСТРОЕК ===
load_dotenv()

BOT_TOKEN = os.getenv("CONSULTANT_BOT_TOKEN")
SPREADSHEET_ID = os.getenv("TZ_SPREADSHEET_ID")
GOOGLE_CREDENTIALS_B64 = os.getenv("GOOGLE_CREDENTIALS")

if not all([BOT_TOKEN, SPREADSHEET_ID, GOOGLE_CREDENTIALS_B64]):
    raise ValueError("❌ Не заданы переменные окружения в .env файле!")

# Декодируем Google Credentials из base64
try:
    b64_clean = GOOGLE_CREDENTIALS_B64.strip()
    padding_needed = len(b64_clean) % 4
    if padding_needed:
        b64_clean += '=' * (4 - padding_needed)
    credentials_json = base64.b64decode(b64_clean).decode('utf-8')
    creds_dict = json.loads(credentials_json)
except Exception as e:
    raise ValueError("❌ Ошибка при декодировании GOOGLE_CREDENTIALS: " + str(e))

# Настройка доступа к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
tz_sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# === FSM СОСТОЯНИЯ ===
class ConsultationStates(StatesGroup):
    brand_name = State()
    logo_url = State()
    business_type = State()
    address = State()
    phones = State()
    socials = State()
    services = State()
    service_duration = State()
    work_schedule = State()
    specialists_count = State()
    style = State()
    tech_contact = State()
    hosting_needed = State()
    extra_features = State()

# === ИНИЦИАЛИЗАЦИЯ ===
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# === СТАРТ ===
@router.message(Command("start"))
async def start_consultation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Привет! Я помогу собрать техническое задание для настройки персонального бота записи.\n\n"
        "Готовы? Ответьте на несколько простых вопросов — это займёт 2 минуты!"
    )
    await message.answer(
        "🏢 **Название бренда или компании**\n"
        "Как вас зовут в бизнесе?\n"
        "Пример: *Salon «LUMIÈRE»*, *Studio Nails Pro*"
    )
    await state.set_state(ConsultationStates.brand_name)

# === 1. Название бренда ===
@router.message(ConsultationStates.brand_name)
async def handle_brand(message: Message, state: FSMContext):
    await state.update_data(brand_name=message.text.strip())
    await message.answer(
        "🖼️ **Логотип или товарный знак (ссылка)**\n"
        "Отправьте прямую ссылку на изображение.\n"
        "❗ Можно пропустить — напишите «Нет»."
    )
    await state.set_state(ConsultationStates.logo_url)

# === 2. Логотип ===
@router.message(ConsultationStates.logo_url)
async def handle_logo(message: Message, state: FSMContext):
    url = message.text.strip() if message.text else "Не указан"
    await state.update_data(logo_url=url)
    await message.answer(
        "💼 **Вид деятельности**\n"
        "Чем вы занимаетесь?\n"
        "Пример: *салон красоты, репетитор по математике, фитнес-тренер*"
    )
    await state.set_state(ConsultationStates.business_type)

# === 3. Вид деятельности ===
@router.message(ConsultationStates.business_type)
async def handle_business(message: Message, state: FSMContext):
    await state.update_data(business_type=message.text.strip())
    await message.answer(
        "📍 **Полный адрес**\n"
        "Где вы находитесь?\n"
        "Пример: *г. Минск, ул. Независимости, д. 15*"
    )
    await state.set_state(ConsultationStates.address)

# === 4. Адрес ===
@router.message(ConsultationStates.address)
async def handle_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await message.answer(
        "📞 **Контактные телефоны**\n"
        "По какому номеру клиенты могут с вами связаться?\n"
        "Пример: *+375 (29) 123-45-67*"
    )
    await state.set_state(ConsultationStates.phones)

# === 5. Телефоны ===
@router.message(ConsultationStates.phones)
async def handle_phones(message: Message, state: FSMContext):
    await state.update_data(phones=message.text.strip())
    await message.answer(
        "📱 **Социальные сети**\n"
        "Ссылки на ваши соцсети (Instagram, VK и т.д.)\n"
        "Пример: *instagram.com/lumiere_salon*"
    )
    await state.set_state(ConsultationStates.socials)

# === 6. Соцсети ===
@router.message(ConsultationStates.socials)
async def handle_socials(message: Message, state: FSMContext):
    await state.update_data(socials=message.text.strip())
    await message.answer(
        "✂️ **Список услуг**\n"
        "Перечислите все услуги через запятую:\n"
        "Пример: *Стрижка, Окрашивание, Маникюр*"
    )
    await state.set_state(ConsultationStates.services)

# === 7. Услуги ===
@router.message(ConsultationStates.services)
async def handle_services(message: Message, state: FSMContext):
    await state.update_data(services=message.text.strip())
    await message.answer(
        "⏱️ **Длительность каждой услуги (в минутах)**\n"
        "Укажите в том же порядке, что и услуги:\n"
        "Пример: *60, 90, 45*"
    )
    await state.set_state(ConsultationStates.service_duration)

# === 8. Длительность ===
@router.message(ConsultationStates.service_duration)
async def handle_duration(message: Message, state: FSMContext):
    await state.update_data(service_duration=message.text.strip())
    await message.answer(
        "📅 **Режим работы**\n"
        "Когда вы работаете?\n"
        "Пример: *Пн–Сб: 10:00–20:00, Вс — выходной*"
    )
    await state.set_state(ConsultationStates.work_schedule)

# === 9. Режим работы ===
@router.message(ConsultationStates.work_schedule)
async def handle_schedule(message: Message, state: FSMContext):
    await state.update_data(work_schedule=message.text.strip())
    await message.answer(
        "👥 **Количество специалистов**\n"
        "Сколько мастеров/специалистов в вашей команде?"
    )
    await state.set_state(ConsultationStates.specialists_count)

# === 10. Специалисты ===
@router.message(ConsultationStates.specialists_count)
async def handle_specialists(message: Message, state: FSMContext):
    await state.update_data(specialists_count=message.text.strip())
    await message.answer(
        "🎨 **Стиль оформления бота**\n"
        "Каким должен быть внешний вид?\n"
        "- Цвета: *красный, пастель*\n"
        "- Эмодзи: *снежинки ❄️, искры ✨*\n"
        "- Шрифт: *жирный, обычный*\n"
        "Пример: *«Красные кнопки, снежинки ❄️, жирный шрифт»*"
    )
    await state.set_state(ConsultationStates.style)

# === 11. Стиль ===
@router.message(ConsultationStates.style)
async def handle_style(message: Message, state: FSMContext):
    await state.update_data(style=message.text.strip())
    await message.answer(
        "👨‍💻 **Ответственный за техподдержку**\n"
        "Кто будет решать технические вопросы после запуска?\n"
        "Укажите имя, должность и телефон:\n"
        "Пример: *Анна, администратор, +375 (29) 987-65-43*"
    )
    await state.set_state(ConsultationStates.tech_contact)

# === 12. Техподдержка ===
@router.message(ConsultationStates.tech_contact)
async def handle_tech_contact(message: Message, state: FSMContext):
    await state.update_data(tech_contact=message.text.strip())
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="hosting_yes")
    kb.button(text="❌ Нет", callback_data="hosting_no")
    await message.answer(
        "⚙️ **Нужна ли помощь с хостингом?**\n"
        "Мы можем бесплатно развернуть бота на надёжном хостинге.",
        reply_markup=kb.as_markup()
    )
    await state.set_state(ConsultationStates.hosting_needed)

# === 13. Хостинг ===
@router.callback_query(ConsultationStates.hosting_needed, F.data.startswith("hosting_"))
async def handle_hosting(callback: CallbackQuery, state: FSMContext):
    choice = "Да" if callback.data == "hosting_yes" else "Нет"
    await state.update_data(hosting_needed=choice)
    await callback.message.edit_text(
        "🎁 **Дополнительные функции**\n"
        "Что ещё важно для вас? Перечислите через запятую:\n"
        "Пример: *напоминания, аналитика, несколько мастеров, мультиязычность*"
    )
    await state.set_state(ConsultationStates.extra_features)

# === 14. Доп. функции ===
@router.message(ConsultationStates.extra_features)
async def handle_extra(message: Message, state: FSMContext):
    await state.update_data(extra_features=message.text.strip())
    
    # Сохраняем в Google Таблицу (без заголовков в сообщении)
    data = await state.get_data()
    try:
        tz_sheet.append_row([
            data.get("brand_name", ""),
            data.get("logo_url", ""),
            data.get("business_type", ""),
            data.get("address", ""),
            data.get("phones", ""),
            data.get("socials", ""),
            data.get("services", ""),
            data.get("service_duration", ""),
            data.get("work_schedule", ""),
            data.get("specialists_count", ""),
            data.get("style", ""),
            data.get("tech_contact", ""),
            data.get("hosting_needed", ""),
            data.get("extra_features", ""),
            str(message.from_user.id),
            message.from_user.username or "",
            str(message.date)
        ])
        await message.answer(
            "✅ **Готово!**\n\n"
            "Ваше техническое задание успешно сохранено.\n"
            "В ближайшее время мы свяжемся с вами для согласования деталей и запуска бота."
        )
    except Exception as e:
        logging.error(f"Ошибка сохранения ТЗ: {e}")
        await message.answer("❌ Не удалось сохранить ТЗ. Попробуйте позже.")
    
    await state.clear()

# === ЗАПУСК ===
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
