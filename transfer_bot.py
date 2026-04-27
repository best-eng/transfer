#!/usr/bin/env python3
"""
Telegram бот для заказа трансфера Йошкар-Ола <-> Казань
"""

import logging
from datetime import datetime
from config import BOT_TOKEN, ADMIN_CHAT_IDS

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

(
    STEP_ROUTE,
    STEP_DATE,
    STEP_TIME,
    STEP_SEATS,
    STEP_PHONE,
    STEP_CONFIRM,
) = range(6)

ROUTES = [
    "🚗 Йошкар-Ола → Казань (Саид Галеева 4)",
    "✈️ Йошкар-Ола → Казань Аэропорт",
    "✈️ Казань Аэропорт → Йошкар-Ола",
    "🚗 Казань (Саид Галеева 4) → Йошкар-Ола",
]

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def route_keyboard():
    return ReplyKeyboardMarkup([[r] for r in ROUTES], resize_keyboard=True, one_time_keyboard=True)

def seats_keyboard():
    return ReplyKeyboardMarkup([["1", "2", "3"], ["4", "5", "6+"]], resize_keyboard=True, one_time_keyboard=True)

def confirm_keyboard():
    return ReplyKeyboardMarkup([["✅ Подтвердить", "❌ Отменить"]], resize_keyboard=True, one_time_keyboard=True)

def phone_keyboard():
    btn = KeyboardButton("📱 Поделиться номером", request_contact=True)
    return ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True)

def format_order(data: dict, user) -> str:
    username = f"@{user.username}" if user.username else "нет username"
    tg_link = f"tg://user?id={user.id}"
    route_clean = data["route"].split(" ", 1)[1] if " " in data["route"] else data["route"]
    return (
        "🆕 <b>НОВАЯ ЗАЯВКА ПАССАЖИРА</b>

"
        f"🛣 <b>Маршрут:</b> {route_clean}
"
        f"📅 <b>Дата:</b> {data['date']} ({data['time']})
"
        f"👥 <b>Мест:</b> {data['seats']}
"
        f"📞 <b>Телефон:</b> {data['phone']}
"
        f"👤 <b>Пассажир:</b> <a href='{tg_link}'>{username}</a>"
    )


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "👋 Привет! Я помогу оформить заявку на трансфер.

Выберите <b>направление</b>:",
        parse_mode="HTML", reply_markup=route_keyboard(),
    )
    return STEP_ROUTE

async def step_route(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ROUTES:
        await update.message.reply_text("Пожалуйста, выберите маршрут из списка 👇", reply_markup=route_keyboard())
        return STEP_ROUTE
    ctx.user_data["route"] = text
    await update.message.reply_text(
        "📅 Введите <b>дату поездки</b> в формате <code>ДД.ММ.ГГГГ</code>
Например: <code>26.04.2026</code>",
        parse_mode="HTML", reply_markup=ReplyKeyboardRemove(),
    )
    return STEP_DATE

async def step_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        dt = datetime.strptime(text, "%d.%m.%Y")
        ctx.user_data["date"] = dt.strftime("%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("❗ Неверный формат. Введите дату как <code>26.04.2026</code>:", parse_mode="HTML")
        return STEP_DATE
    await update.message.reply_text(
        "🕐 Введите <b>время выезда</b> в формате <code>ЧЧ:ММ</code>
Например: <code>07:30</code>",
        parse_mode="HTML",
    )
    return STEP_TIME

async def step_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        t = datetime.strptime(text, "%H:%M")
        ctx.user_data["time"] = t.strftime("%H:%M")
    except ValueError:
        await update.message.reply_text("❗ Неверный формат. Введите время как <code>07:30</code>:", parse_mode="HTML")
        return STEP_TIME
    await update.message.reply_text("👥 Сколько <b>мест</b> нужно?", parse_mode="HTML", reply_markup=seats_keyboard())
    return STEP_SEATS

async def step_seats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text not in ["1", "2", "3", "4", "5", "6+"]:
        await update.message.reply_text("Выберите количество мест 👇", reply_markup=seats_keyboard())
        return STEP_SEATS
    ctx.user_data["seats"] = text
    await update.message.reply_text(
        "📞 Введите ваш <b>номер телефона</b> или нажмите кнопку ниже:",
        parse_mode="HTML", reply_markup=phone_keyboard(),
    )
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
            await update.message.reply_text(
                "❗ Некорректный номер. Введите телефон, например: <code>+79161234567</code>",
                parse_mode="HTML", reply_markup=phone_keyboard(),
            )
            return STEP_PHONE
        ctx.user_data["phone"] = phone
    d = ctx.user_data
    route_clean = d["route"].split(" ", 1)[1] if " " in d["route"] else d["route"]
    summary = (
        "📋 <b>Ваша заявка:</b>

"
        f"🛣 <b>Маршрут:</b> {route_clean}
"
        f"📅 <b>Дата:</b> {d['date']} ({d['time']})
"
        f"👥 <b>Мест:</b> {d['seats']}
"
        f"📞 <b>Телефон:</b> {d['phone']}

Всё верно?"
    )
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
    order_text = format_order(ctx.user_data, user)
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await ctx.bot.send_message(chat_id=admin_id, text=order_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось отправить заявку администратору {admin_id}: {e}")
    await update.message.reply_text(
        "✅ <b>Заявка принята!</b>

Ожидайте подтверждения от диспетчера.

Чтобы оформить новую заявку — /start",
        parse_mode="HTML", reply_markup=ReplyKeyboardRemove(),
    )
    ctx.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Оформление отменено. Напишите /start чтобы начать заново.", reply_markup=ReplyKeyboardRemove())
    ctx.user_data.clear()
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STEP_ROUTE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_route)],
            STEP_DATE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_date)],
            STEP_TIME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_time)],
            STEP_SEATS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_seats)],
            STEP_PHONE:   [
                MessageHandler(filters.CONTACT, step_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, step_phone),
            ],
            STEP_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

