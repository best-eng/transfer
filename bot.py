#!/usr/bin/env python3
import json, logging
from config import BOT_TOKEN, ADMIN_CHAT_IDS, WEBAPP_URL
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📦 Отправить посылку  Й-Ола ➡️ Казань",                      web_app=WebAppInfo(url=WEBAPP_URL+"/parcel.html"))],
        [KeyboardButton("🔍 Найти поездку  Й-Ола ➡️ Казань",                          web_app=WebAppInfo(url=WEBAPP_URL+"/trip.html"))],
        [KeyboardButton("✈️ Трансфер в аэропорт  Й-Ола ➡️ Казань",                    web_app=WebAppInfo(url=WEBAPP_URL+"/airport.html"))],
        [KeyboardButton("🚌 Индивидуальный трансфер минивэн  Й-Ола ➡️ Казань",        web_app=WebAppInfo(url=WEBAPP_URL+"/rent.html"))],
        [KeyboardButton("🌍 Трансфер в любой город РФ минивэн",                        web_app=WebAppInfo(url=WEBAPP_URL+"/transfer_rf.html"))],
    ], resize_keyboard=True)

async def post_init(app):
    await app.bot.delete_webhook(drop_pending_updates=True)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Выберите тип заявки:",
        reply_markup=main_menu()
    )

async def webapp(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    raw = update.message.web_app_data.data
    logger.info("data: %s", raw)
    try:
        d = json.loads(raw)
    except Exception:
        await update.message.reply_text("❌ Ошибка данных.", reply_markup=main_menu())
        return

    user = update.effective_user
    un   = "@" + user.username if user.username else "нет username"
    lnk  = f"tg://user?id={user.id}"
    t    = d.get("type", "")

    if t == "parcel":
        lines = [
            "📦 <b>НОВАЯ ЗАЯВКА — Посылка</b>", "",
            f"🛣 <b>Маршрут:</b> {d.get('route','')}",
            f"📅 <b>Дата/время:</b> {d.get('date','')} {d.get('time','')}",
            f"📦 <b>Содержимое:</b> {d.get('what','')}",
            f"📞 <b>Телефон:</b> {d.get('phone','')}",
        ]
        if d.get("details"): lines.append(f"📝 <b>Детали:</b> {d['details']}")

    elif t == "trip":
        lines = [
            "🔍 <b>НОВАЯ ЗАЯВКА — Поездка</b>", "",
            f"🛣 <b>Маршрут:</b> {d.get('route','')}",
            f"📅 <b>Дата/время:</b> {d.get('date','')} {d.get('time','')}",
            f"👥 <b>Мест:</b> {d.get('seats','')}",
            f"📞 <b>Телефон:</b> {d.get('phone','')}",
        ]
        if d.get("comment"): lines.append(f"💬 {d['comment']}")

    elif t == "airport":
        lines = [
            "✈️ <b>НОВАЯ ЗАЯВКА — Трансфер в аэропорт</b>", "",
            f"🛣 <b>Маршрут:</b> {d.get('route','')}",
            f"📅 <b>Дата/время:</b> {d.get('date','')} {d.get('time','')}",
            f"👥 <b>Мест:</b> {d.get('seats','')}",
            f"📞 <b>Телефон:</b> {d.get('phone','')}",
        ]
        if d.get("comment"): lines.append(f"💬 {d['comment']}")

    elif t == "rent":
        lines = [
            "🚌 <b>НОВАЯ ЗАЯВКА — Индивидуальный трансфер</b>", "",
            f"🚗 <b>Класс:</b> {d.get('car_class','')}",
            f"🛣 <b>Маршрут:</b> {d.get('route','')}",
            f"📅 <b>Дата/время:</b> {d.get('date','')} {d.get('time','')}",
            f"👥 <b>Пассажиров:</b> {d.get('seats','')}",
            f"📞 <b>Телефон:</b> {d.get('phone','')}",
        ]
        if d.get("comment"): lines.append(f"💬 {d['comment']}")

    elif t == "transfer_rf":
        lines = [
            "🌍 <b>НОВАЯ ЗАЯВКА — Трансфер по РФ</b>", "",
            f"🚗 <b>Класс:</b> {d.get('car_class','')}",
            f"🛣 <b>Откуда:</b> {d.get('from','')}",
            f"🛣 <b>Куда:</b> {d.get('to','')}",
            f"📅 <b>Дата/время:</b> {d.get('date','')} {d.get('time','')}",
            f"👥 <b>Пассажиров:</b> {d.get('seats','')}",
            f"📞 <b>Телефон:</b> {d.get('phone','')}",
        ]
        if d.get("comment"): lines.append(f"💬 {d['comment']}")

    else:
        await update.message.reply_text("❌ Неизвестный тип.", reply_markup=main_menu())
        return

    lines.append(f"\n👤 <b>От:</b> <a href=\'{lnk}\'>{un}</a>")
    msg = "\n".join(lines)

    ok = False
    for aid in ADMIN_CHAT_IDS:
        try:
            await ctx.bot.send_message(chat_id=aid, text=msg, parse_mode="HTML")
            ok = True
        except Exception as e:
            logger.error("❌ admin %s: %s", aid, e)

    reply = (
        "✅ <b>Заявка принята!</b>\n\nДиспетчер свяжется с вами в ближайшее время."
        if ok else
        "⚠️ Ошибка отправки. Позвоните нам напрямую."
    )
    await update.message.reply_text(reply, parse_mode="HTML", reply_markup=main_menu())

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp))
    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
