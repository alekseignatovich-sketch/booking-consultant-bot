# -*- coding: utf-8 -*-
"""
Бот-консультант для сбора ТЗ на персональную настройку бота записи
Поддержка: RU, EN, ES
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

# === ЛОКАЛИЗАЦИЯ ===
TEXTS = {
    "ru": {
        "start": "👋 Привет! Выберите язык:",
        "lang_selected": "✅ Выбран русский язык.",
        "brand_name": "🏢 **Название бренда или компании**\nКак вас зовут в бизнесе?\nПример: *Salon «LUMIÈRE»*",
        "logo_url": "🖼️ **Логотип (ссылка)**\nОтправьте прямую ссылку на изображение.\n❗ Можно пропустить — напишите «Нет».",
        "business_type": "💼 **Вид деятельности**\nЧем вы занимаетесь?\nПример: *салон красоты, репетитор*",
        "address": "📍 **Полный адрес**\nГде вы находитесь?\nПример: *г. Минск, ул. Независимости, д. 15*",
        "phones": "📞 **Контактные телефоны**\nПо какому номеру клиенты могут с вами связаться?",
        "socials": "📱 **Социальные сети**\nСсылки на Instagram, VK и т.д.",
        "services": "✂️ **Список услуг**\nПеречислите через запятую:\nПример: *Стрижка, Окрашивание*",
        "service_duration": "⏱️ **Длительность (в минутах)**\nУкажите в том же порядке:\nПример: *60, 90*",
        "work_schedule": "📅 **Режим работы**\nКогда вы работаете?\nПример: *Пн–Сб: 10:00–20:00*",
        "specialists_count": "👥 **Количество специалистов**\nСколько мастеров в команде?",
        "style": "🎨 **Стиль оформления бота**\nЦвета, эмодзи, шрифт?\nПример: *Красные кнопки, снежинки ❄️*",
        "tech_contact": "👨‍💻 **Ответственный за техподдержку**\nИмя, должность, телефон:\nПример: *Анна, админ, +37529...*",
        "hosting": "⚙️ **Нужна ли помощь с хостингом?**\nМы можем бесплатно развернуть бота.",
        "extra_features": "🎁 **Дополнительные функции**\nЧто важно? Через запятую:\nПример: *напоминания, аналитика*",
        "done": "✅ **Готово!**\nВаше ТЗ сохранено. Мы свяжемся с вами в ближайшее время.",
        "btn_ru": "🇷🇺 Русский",
        "btn_en": "🇬🇧 English",
        "btn_es": "🇪🇸 Español",
        "yes": "✅ Да",
        "no": "❌ Нет"
    },
    "en": {
        "start": "👋 Hi! Please choose your language:",
        "lang_selected": "✅ English selected.",
        "brand_name": "🏢 **Brand or company name**\nHow is your business called?\nExample: *Salon «LUMIÈRE»*",
        "logo_url": "🖼️ **Logo (link)**\nSend a direct image link.\n❗ Skip by typing «No».",
        "business_type": "💼 **Business type**\nWhat do you do?\nExample: *beauty salon, tutor*",
        "address": "📍 **Full address**\nWhere are you located?\nExample: *Minsk, Nezavisimosti St., 15*",
        "phones": "📞 **Contact phones**\nHow can clients reach you?",
        "socials": "📱 **Social media**\nLinks to Instagram, VK, etc.",
        "services": "✂️ **List of services**\nComma-separated:\nExample: *Haircut, Coloring*",
        "service_duration": "⏱️ **Duration (in minutes)**\nIn the same order:\nExample: *60, 90*",
        "work_schedule": "📅 **Working hours**\nWhen are you open?\nExample: *Mon–Sat: 10:00–20:00*",
        "specialists_count": "👥 **Number of specialists**\nHow many staff members?",
        "style": "🎨 **Bot styling**\nColors, emojis, font?\nExample: *Red buttons, snowflakes ❄️*",
        "tech_contact": "👨‍💻 **Tech support contact**\nName, role, phone:\nExample: *Anna, admin, +37529...*",
        "hosting": "⚙️ **Need hosting help?**\nWe can deploy the bot for free.",
        "extra_features": "🎁 **Extra features**\nWhat’s important? Comma-separated:\nExample: *reminders, analytics*",
        "done": "✅ **Done!**\nYour brief is saved. We’ll contact you soon.",
        "btn_ru": "🇷🇺 Русский",
        "btn_en": "🇬🇧 English",
        "btn_es": "🇪🇸 Español",
        "yes": "✅ Yes",
        "no": "❌ No"
    },
    "es": {
        "start": "👋 ¡Hola! Por favor, elige tu idioma:",
        "lang_selected": "✅ Idioma español seleccionado.",
        "brand_name": "🏢 **Nombre de la marca o empresa**\n¿Cómo se llama tu negocio?\nEjemplo: *Salón «LUMIÈRE»*",
        "logo_url": "🖼️ **Logotipo (enlace)**\nEnvía un enlace directo a la imagen.\n❗ Para omitir, escribe «No».",
        "business_type": "💼 **Tipo de negocio**\n¿A qué te dedicas?\nEjemplo: *salón de belleza, tutor*",
        "address": "📍 **Dirección completa**\n¿Dónde estás ubicado?\nEjemplo: *Minsk, Calle Nezavisimosti, 15*",
        "phones": "📞 **Teléfonos de contacto**\n¿Cómo pueden contactarte los clientes?",
        "socials": "📱 **Redes sociales**\nEnlaces a Instagram, VK, etc.",
        "services": "✂️ **Lista de servicios**\nSeparados por comas:\nEjemplo: *Corte de pelo, Tinte*",
        "service_duration": "⏱️ **Duración (en minutos)**\nEn el mismo orden:\nEjemplo: *60, 90*",
        "work_schedule": "📅 **Horario de trabajo**\n¿Cuándo estás abierto?\nEjemplo: *Lun–Sáb: 10:00–20:00*",
        "specialists_count": "👥 **Número de especialistas**\n¿Cuántos empleados tienes?",
        "style": "🎨 **Estilo del bot**\nColores, emojis, fuente?\nEjemplo: *Botones rojos, copos de nieve ❄️*",
        "tech_contact": "👨‍💻 **Contacto de soporte técnico**\nNombre, cargo, teléfono:\nEjemplo: *Ana, administradora, +37529...*",
        "hosting": "⚙️ **¿Necesitas ayuda con el alojamiento?**\nPodemos desplegar el bot gratis.",
        "extra_features": "🎁 **Funciones adicionales**\n¿Qué es importante? Separado por comas:\nEjemplo: *recordatorios, analítica*",
        "done": "✅ **¡Listo!**\nTu solicitud ha sido guardada. Nos pondremos en contacto contigo pronto.",
        "btn_ru": "🇷🇺 Русский",
        "btn_en": "🇬🇧 English",
        "btn_es": "🇪🇸 Español",
        "yes": "✅ Sí",
        "no": "❌ No"
    }
}

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
    language = State()
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

# === ВЫБОР ЯЗЫКА ===
@router.message(Command("start"))
async def start_consultation(message: Message, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text=TEXTS["ru"]["btn_ru"], callback_data="lang:ru")
    kb.button(text=TEXTS["en"]["btn_en"], callback_data="lang:en")
    kb.button(text=TEXTS["es"]["btn_es"], callback_data="lang:es")
    kb.adjust(1)
    await message.answer(TEXTS["en"]["start"], reply_markup=kb.as_markup())
    await state.set_state(ConsultationStates.language)

@router.callback_query(ConsultationStates.language, F.data.startswith("lang:"))
async def select_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":")[1]
    await state.update_data(language=lang)
    await callback.message.edit_text(TEXTS[lang]["lang_selected"])
    await callback.message.answer(TEXTS[lang]["brand_name"])
    await state.set_state(ConsultationStates.brand_name)

# === ВСЕ ОБРАБОТЧИКИ С ЛОКАЛИЗАЦИЕЙ ===
def get_lang(state_data):
    return state_data.get("language", "en")

@router.message(ConsultationStates.brand_name)
async def handle_brand(message: Message, state: FSMContext):
    await state.update_data(brand_name=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["logo_url"])
    await state.set_state(ConsultationStates.logo_url)

@router.message(ConsultationStates.logo_url)
async def handle_logo(message: Message, state: FSMContext):
    url = message.text.strip() if message.text else "No"
    await state.update_data(logo_url=url)
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["business_type"])
    await state.set_state(ConsultationStates.business_type)

@router.message(ConsultationStates.business_type)
async def handle_business(message: Message, state: FSMContext):
    await state.update_data(business_type=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["address"])
    await state.set_state(ConsultationStates.address)

@router.message(ConsultationStates.address)
async def handle_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["phones"])
    await state.set_state(ConsultationStates.phones)

@router.message(ConsultationStates.phones)
async def handle_phones(message: Message, state: FSMContext):
    await state.update_data(phones=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["socials"])
    await state.set_state(ConsultationStates.socials)

@router.message(ConsultationStates.socials)
async def handle_socials(message: Message, state: FSMContext):
    await state.update_data(socials=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["services"])
    await state.set_state(ConsultationStates.services)

@router.message(ConsultationStates.services)
async def handle_services(message: Message, state: FSMContext):
    await state.update_data(services=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["service_duration"])
    await state.set_state(ConsultationStates.service_duration)

@router.message(ConsultationStates.service_duration)
async def handle_duration(message: Message, state: FSMContext):
    await state.update_data(service_duration=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["work_schedule"])
    await state.set_state(ConsultationStates.work_schedule)

@router.message(ConsultationStates.work_schedule)
async def handle_schedule(message: Message, state: FSMContext):
    await state.update_data(work_schedule=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["specialists_count"])
    await state.set_state(ConsultationStates.specialists_count)

@router.message(ConsultationStates.specialists_count)
async def handle_specialists(message: Message, state: FSMContext):
    await state.update_data(specialists_count=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["style"])
    await state.set_state(ConsultationStates.style)

@router.message(ConsultationStates.style)
async def handle_style(message: Message, state: FSMContext):
    await state.update_data(style=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    await message.answer(TEXTS[lang]["tech_contact"])
    await state.set_state(ConsultationStates.tech_contact)

@router.message(ConsultationStates.tech_contact)
async def handle_tech_contact(message: Message, state: FSMContext):
    await state.update_data(tech_contact=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    kb = InlineKeyboardBuilder()
    kb.button(text=TEXTS[lang]["yes"], callback_data="hosting_yes")
    kb.button(text=TEXTS[lang]["no"], callback_data="hosting_no")
    await message.answer(TEXTS[lang]["hosting"], reply_markup=kb.as_markup())
    await state.set_state(ConsultationStates.hosting_needed)

@router.callback_query(ConsultationStates.hosting_needed, F.data.startswith("hosting_"))
async def handle_hosting(callback: CallbackQuery, state: FSMContext):
    choice = "Yes" if callback.data == "hosting_yes" else "No"
    await state.update_data(hosting_needed=choice)
    data = await state.get_data()
    lang = get_lang(data)
    await callback.message.edit_text(TEXTS[lang]["extra_features"])
    await state.set_state(ConsultationStates.extra_features)

@router.message(ConsultationStates.extra_features)
async def handle_extra(message: Message, state: FSMContext):
    await state.update_data(extra_features=message.text.strip())
    data = await state.get_data()
    lang = get_lang(data)
    
    # Сохраняем в Google Таблицу
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
            data.get("language", "en"),  # ← язык!
            str(message.from_user.id),
            message.from_user.username or "",
            str(message.date)
        ])
        await message.answer(TEXTS[lang]["done"])
    except Exception as e:
        logging.error(f"Ошибка сохранения ТЗ: {e}")
        await message.answer("❌ Error saving brief. Please try again.")
    
    await state.clear()

# === ЗАПУСК ===
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
