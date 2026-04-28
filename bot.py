#!/usr/bin/env python3
"""Telegram бот для заказа трансфера Йошкар-Ола <-> Казань"""

import logging
from datetime import datetime
from config import BOT_TOKEN, ADMIN_CHAT_IDS

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes,
)

(
    MENU, STEP_ROUTE, STEP_DATE, STEP_TIME, STEP_SEATS, STEP_PHONE, STEP_CONFIRM,
    RENT_SIZE, RENT_DATE, RENT_TIME, RENT_SEATS, RENT_PHONE, RENT_CONFIRM,
) = range(13)

ROUTES = [
    "🚗 Йошкар-Ола → Казань (Саид Галеева 4)",
    "✈️ Йошкар-Ола → Казань Аэропорт",
    "✈️ Казань Аэропорт → Йошкар-Ола",
    "🚗 Казань (Саид Галеева 4) → Йошкар-Ола",
]

RENT_OPTIONS = {
    "🚐 4 места — 4 000 ₽": (4, 4000),
    "🚌 6 мест — 6 000 ₽": (6, 6000),
    "🚌 8 мест — 8 000 ₽": (8, 8000),
}

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def main_menu_keyboard():
    return ReplyKeyboardMarkup([["🚗 Заказать трансфер"], ["🚐 Арендовать машину"]], resize_keyboard=True, one_time_keyboard=True)

def route_keyboard():
    return ReplyKeyboardMarkup([[r] for r in ROUTES], resize_keyboard=True, one_time_keyboard=True)

def rent_keyboard():
    return ReplyKeyboardMarkup([[r] for r in RENT_OPTIONS], resize_keyboard=True, one_time_keyboard=True)

def transfer_seats_keyboard():
    return ReplyKeyboardMarkup([["1", "2", "3"], ["4", "5", "6+"]], resize_keyboard=True, one_time_keyboard=True)

def rent_seats_keyboard():
    return ReplyKeyboardMarkup([["4", "6", "8"]], resize_keyboard=True, one_time_keyboard=True)

def confirm_keyboard():
    return ReplyKeyboardMarkup([["✅ Подтвердить", "❌ Отменить"]], resize_keyboard=True, one_time_keyboard=True)

def phone_keyboard():
    btn = KeyboardButton("📱 Поделиться номером", request_contact=True)
    return ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)


def format_transfer(data, user):
    username = "@" + user.username if user.username else "нет username"
    tg_link = "tg://user?id=" + str(user.id)
    route_clean = data["route"].split(" ", 1)[1] if " " in data["route"] else data["route"]
    lines = [
        "🆕 <b>НОВАЯ ЗАЯВКА</b>",
        "📌 <b>Тип:</b> Трансфер",
        "",
        "🛣 <b>Маршрут:</b> " + route_clean,
        "📅 <b>Дата:</b> " + data["date"] + " (" + data["time"] + ")",
        "👥 <b>Мест:</b> " + data["seats"],
        "📞 <b>Телефон:</b> " + data["phone"],
        "👤 <b>Пассажир:</b> <a href='" + tg_link + "'>" + username + "</a>",
    ]
    return "\n".join(lines)


def format_rent(data, user):
    username = "@" + user.username if user.username else "нет username"
    tg_link = "tg://user?id=" + str(user.id)
    lines = [
        "🆕 <b>НОВАЯ ЗАЯВКА</b>",
        "📌 <b>Тип:</b> Аренда машины",
        "",
        "🚐 <b>Вариант:</b> " + data["rent_option"],
        "💰 <b>Стоимость:</b> " + str(data["rent_price"]) + " ₽",
        "📅 <b>Дата:</b> " + data["date"] + " (" + data["time"] + ")",
        "👥 <b>Пассажиров:</b> " + data["seats"],
        "📞 <b>Телефон:</b> " + data["phone"],
        "👤 <b>Клиент:</b> <a href='" + tg_link + "'>" + username + "</a>",
    ]
    return "\n".join(lines)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("👋 Привет! Выберите тип заявки:", reply_markup=main_menu_keyboard())
    return MENU

async def menu_choice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🚗 Заказать трансфер":
        await update.message.reply_text("Выберите <b>маршрут</b>:", parse_mode="HTML", reply_markup=route_keyboard())
        return STEP_ROUTE
    elif text == "🚐 Арендовать машину":
        await update.message.reply_text("Выберите <b>вариант аренды</b>:", parse_mode="HTML", reply_markup=rent_keyboard())
        return RENT_SIZE
    else:
        await update.message.reply_text("Пожалуйста, выберите действие 👇", reply_markup=main_menu_keyboard())
        return MENU


async def step_route(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ROUTES:
        await update.message.reply_text("Пожалуйста, выберите маршрут из списка 👇", reply_markup=route_keyboard())
        return STEP_ROUTE
    ctx.user_data["route"] = text
    await update.message.reply_text("📅 Введите <b>дату поездки</b> в формате <code>ДД.ММ.ГГГГ</code>\nНапример: <code>26.04.2026</code>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    return STEP_DATE

async def step_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        dt = datetime.strptime(text, "%d.%m.%Y")
        ctx.user_data["date"] = dt.strftime("%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("❗ Неверный формат. Введите дату как <code>26.04.2026</code>:", parse_mode="HTML")
        return STEP_DATE
    await update.message.reply_text("🕐 Введите <b>время выезда</b> в формате <code>ЧЧ:ММ</code>\nНапример: <code>07:30</code>", parse_mode="HTML")
    return STEP_TIME

async def step_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        t = datetime.strptime(text, "%H:%M")
        ctx.user_data["time"] = t.strftime("%H:%M")
    except ValueError:
        await update.message.reply_text("❗ Неверный формат. Введите время как <code>07:30</code>:", parse_mode="HTML")
        return STEP_TIME
    await update.message.reply_text("👥 Сколько <b>мест</b> нужно?", parse_mode="HTML", reply_markup=transfer_seats_keyboard())
    return STEP_SEATS

async def step_seats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text not in ["1", "2", "3", "4", "5", "6+"]:
        await update.message.reply_text("Выберите количество мест 👇", reply_markup=transfer_seats_keyboard())
        return STEP_SEATS
    ctx.user_data["seats"] = text
    await update.message.reply_text("📞 Введите ваш <b>номер телефона</b> или нажмите кнопку ниже:", parse_mode="HTML", reply_markup=phone_keyboard())
    return STEP_PHONE

async def step_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith("+"): phone = "+" + phone
        ctx.user_data["phone"] = phone
    else:
        phone = update.message.text.strip()
        digits = phone.replace("+", "").replace(" ", "").replace("-", "")
        if not digits.isdigit() or len(digits) < 10:
            await update.message.reply_text("❗ Некорректный номер. Например: <code>+79161234567</code>", parse_mode="HTML", reply_markup=phone_keyboard())
            return STEP_PHONE
        ctx.user_data["phone"] = phone
    d = ctx.user_data
    route_clean = d["route"].split(" ", 1)[1] if " " in d["route"] else d["route"]
    summary = "\n".join([
        "📋 <b>Ваша заявка (трансфер):</b>", "",
        "🛣 <b>Маршрут:</b> " + route_clean,
        "📅 <b>Дата:</b> " + d["date"] + " (" + d["time"] + ")",
        "👥 <b>Мест:</b> " + d["seats"],
        "📞 <b>Телефон:</b> " + d["phone"], "", "Всё верно?",
    ])
    await update.message.reply_text(summary, parse_mode="HTML", reply_markup=confirm_keyboard())
    return STEP_CONFIRM

async def step_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Отменить" in text:
        await update.message.reply_text("❌ Заявка отменена. Чтобы начать заново — /start", reply_markup=ReplyKeyboardRemove())
        ctx.user_data.clear()
        return ConversationHandler.END
    if "Подтвердить" not in text:
        await update.message.reply_text("Пожалуйста, нажмите одну из кнопок:", reply_markup=confirm_keyboard())
        return STEP_CONFIRM
    user = update.effective_user
    logger.info("=== ТРАНСФЕР | admin_ids=%s | user_id=%s ===", ADMIN_CHAT_IDS, user.id)
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await ctx.bot.send_message(chat_id=admin_id, text=format_transfer(ctx.user_data, user), parse_mode="HTML")
            logger.info("✅ Отправлено администратору %s", admin_id)
        except Exception as e:
            logger.error("❌ Ошибка отправки %s: %s", admin_id, e)
    await update.message.reply_text("✅ <b>Заявка принята!</b>\n\nОжидайте подтверждения от диспетчера.\n\nЧтобы оформить новую заявку — /start", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    ctx.user_data.clear()
    return ConversationHandler.END


async def rent_size(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in RENT_OPTIONS:
        await update.message.reply_text("Пожалуйста, выберите вариант из списка 👇", reply_markup=rent_keyboard())
        return RENT_SIZE
    seats_count, price = RENT_OPTIONS[text]
    ctx.user_data["rent_option"] = text
    ctx.user_data["rent_price"] = price
    ctx.user_data["rent_seats_max"] = seats_count
    await update.message.reply_text("📅 Введите <b>дату аренды</b> в формате <code>ДД.ММ.ГГГГ</code>\nНапример: <code>26.04.2026</code>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    return RENT_DATE

async def rent_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        dt = datetime.strptime(text, "%d.%m.%Y")
        ctx.user_data["date"] = dt.strftime("%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("❗ Неверный формат. Введите дату как <code>26.04.2026</code>:", parse_mode="HTML")
        return RENT_DATE
    await update.message.reply_text("🕐 Введите <b>время подачи</b> в формате <code>ЧЧ:ММ</code>\nНапример: <code>07:30</code>", parse_mode="HTML")
    return RENT_TIME

async def rent_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        t = datetime.strptime(text, "%H:%M")
        ctx.user_data["time"] = t.strftime("%H:%M")
    except ValueError:
        await update.message.reply_text("❗ Неверный формат. Введите время как <code>07:30</code>:", parse_mode="HTML")
        return RENT_TIME
    await update.message.reply_text("👥 Сколько <b>пассажиров</b>?", parse_mode="HTML", reply_markup=rent_seats_keyboard())
    return RENT_SEATS

async def rent_seats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text not in ["4", "6", "8"]:
        await update.message.reply_text("Выберите количество пассажиров 👇", reply_markup=rent_seats_keyboard())
        return RENT_SEATS
    ctx.user_data["seats"] = text
    await update.message.reply_text("📞 Введите ваш <b>номер телефона</b> или нажмите кнопку ниже:", parse_mode="HTML", reply_markup=phone_keyboard())
    return RENT_PHONE

async def rent_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith("+"): phone = "+" + phone
        ctx.user_data["phone"] = phone
    else:
        phone = update.message.text.strip()
        digits = phone.replace("+", "").replace(" ", "").replace("-", "")
        if not digits.isdigit() or len(digits) < 10:
            await update.message.reply_text("❗ Некорректный номер. Например: <code>+79161234567</code>", parse_mode="HTML", reply_markup=phone_keyboard())
            return RENT_PHONE
        ctx.user_data["phone"] = phone
    d = ctx.user_data
    summary = "\n".join([
        "📋 <b>Ваша заявка (аренда):</b>", "",
        "🚐 <b>Вариант:</b> " + d["rent_option"],
        "💰 <b>Стоимость:</b> " + str(d["rent_price"]) + " ₽",
        "📅 <b>Дата:</b> " + d["date"] + " (" + d["time"] + ")",
        "👥 <b>Пассажиров:</b> " + d["seats"],
        "📞 <b>Телефон:</b> " + d["phone"], "", "Всё верно?",
    ])
    await update.message.reply_text(summary, parse_mode="HTML", reply_markup=confirm_keyboard())
    return RENT_CONFIRM

async def rent_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Отменить" in text:
        await update.message.reply_text("❌ Заявка отменена. Чтобы начать заново — /start", reply_markup=ReplyKeyboardRemove())
        ctx.user_data.clear()
        return ConversationHandler.END
    if "Подтвердить" not in text:
        await update.message.reply_text("Пожалуйста, нажмите одну из кнопок:", reply_markup=confirm_keyboard())
        return RENT_CONFIRM
    user = update.effective_user
    logger.info("=== АРЕНДА | admin_ids=%s | user_id=%s ===", ADMIN_CHAT_IDS, user.id)
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await ctx.bot.send_message(chat_id=admin_id, text=format_rent(ctx.user_data, user), parse_mode="HTML")
            logger.info("✅ Отправлено администратору %s", admin_id)
        except Exception as e:
            logger.error("❌ Ошибка отправки %s: %s", admin_id, e)
    await update.message.reply_text("✅ <b>Заявка на аренду принята!</b>\n\nОжидайте подтверждения от диспетчера.\n\nЧтобы оформить новую заявку — /start", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    ctx.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Оформление отменено. Напишите /start чтобы начать заново.", reply_markup=ReplyKeyboardRemove())
    ctx.user_data.clear()
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MENU:         [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_choice)],
            STEP_ROUTE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_route)],
            STEP_DATE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_date)],
            STEP_TIME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_time)],
            STEP_SEATS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_seats)],
            STEP_PHONE:   [MessageHandler(filters.CONTACT, step_phone), MessageHandler(filters.TEXT & ~filters.COMMAND, step_phone)],
            STEP_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_confirm)],
            RENT_SIZE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, rent_size)],
            RENT_DATE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, rent_date)],
            RENT_TIME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, rent_time)],
            RENT_SEATS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, rent_seats)],
            RENT_PHONE:   [MessageHandler(filters.CONTACT, rent_phone), MessageHandler(filters.TEXT & ~filters.COMMAND, rent_phone)],
            RENT_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, rent_confirm)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv)
    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
