#!/usr/bin/env python3
import json, logging
from config import BOT_TOKEN, ADMIN_CHAT_IDS, WEBAPP_URL
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📦 Отправить посылку\nЙ-Ола ↔ Казань",                          web_app=WebAppInfo(url=WEBAPP_URL+"/parcel.html"))],
        [KeyboardButton("🔍 Найти поездку\nЙ-Ола ↔ Казань (центр и аэропорт)",            web_app=WebAppInfo(url=WEBAPP_URL+"/trip.html"))],
        [KeyboardButton("✈️ Заказать трансфер в аэропорт\nЙ-Ола ↔ Казань Аэропорт",       web_app=WebAppInfo(url=WEBAPP_URL+"/airport.html"))],
        [KeyboardButton("🚐 Индивидуальный трансфер минивэн\nЙ-Ола ↔ Казань Аэропорт",    web_app=WebAppInfo(url=WEBAPP_URL+"/rent.html"))],
        [KeyboardButton("🌍 Трансфер в любой город РФ минивэн",                             web_app=WebAppInfo(url=WEBAPP_URL+"/transfer_rf.html"))],
    ], resize_keyboard=True)

async def post_init(app):
    await app.bot.delete_webhook(drop_pending_updates=True)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Выберите тип заявки:", reply_markup=kb())

async def webapp(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    raw = update.message.web_app_data.data
    logger.info("data: %s", raw)
    try: d = json.loads(raw)
    except: await update.message.reply_text("❌ Ошибка данных.", reply_markup=kb()); return

    user = update.effective_user
    un = "@"+user.username if user.username else "нет username"
    lnk = "tg://user?id="+str(user.id)
    t = d.get("type","")

    if t == "parcel":
        lines = ["🆕 <b>НОВАЯ ЗАЯВКА</b>", "📌 <b>Тип:</b> Посылка", "",
                 "🛣 <b>Маршрут:</b> "+d.get("route",""),
                 "📅 <b>Дата/время:</b> "+d.get("date","")+" "+d.get("time",""),
                 "📦 <b>Содержимое:</b> "+d.get("what",""),
                 "📞 <b>Телефон:</b> "+d.get("phone","")]
        if d.get("details"): lines.append("📝 <b>Детали:</b> "+d["details"])
        lines.append("👤 <b>От:</b> <a href=\'"+lnk+"\'>"+un+"</a>")

    elif t == "trip":
        lines = ["🆕 <b>НОВАЯ ЗАЯВКА</b>", "📌 <b>Тип:</b> Поездка (попутчики)", "",
                 "🛣 <b>Маршрут:</b> "+d.get("route",""),
                 "📅 <b>Дата/время:</b> "+d.get("date","")+" "+d.get("time",""),
                 "👥 <b>Мест:</b> "+d.get("seats",""),
                 "📞 <b>Телефон:</b> "+d.get("phone","")]
        if d.get("comment"): lines.append("💬 "+d["comment"])
        lines.append("👤 <b>От:</b> <a href=\'"+lnk+"\'>"+un+"</a>")

    elif t == "airport":
        lines = ["🆕 <b>НОВАЯ ЗАЯВКА</b>", "📌 <b>Тип:</b> Трансфер в аэропорт", "",
                 "🛣 <b>Маршрут:</b> "+d.get("route",""),
                 "📅 <b>Дата/время:</b> "+d.get("date","")+" "+d.get("time",""),
                 "👥 <b>Мест:</b> "+d.get("seats",""),
                 "📞 <b>Телефон:</b> "+d.get("phone","")]
        if d.get("comment"): lines.append("💬 "+d["comment"])
        lines.append("👤 <b>От:</b> <a href=\'"+lnk+"\'>"+un+"</a>")

    elif t == "rent":
        lines = ["🆕 <b>НОВАЯ ЗАЯВКА</b>", "📌 <b>Тип:</b> Индивидуальный трансфер минивэн", "",
                 "🚐 <b>Класс:</b> "+d.get("car_class",""),
                 "🛣 <b>Маршрут:</b> "+d.get("route",""),
                 "📅 <b>Дата/время:</b> "+d.get("date","")+" "+d.get("time",""),
                 "👥 <b>Пассажиров:</b> "+d.get("seats",""),
                 "📞 <b>Телефон:</b> "+d.get("phone","")]
        if d.get("comment"): lines.append("💬 "+d["comment"])
        lines.append("👤 <b>От:</b> <a href=\'"+lnk+"\'>"+un+"</a>")

    elif t == "transfer_rf":
        lines = ["🆕 <b>НОВАЯ ЗАЯВКА</b>", "📌 <b>Тип:</b> Трансфер по РФ минивэн", "",
                 "🚐 <b>Класс:</b> "+d.get("car_class",""),
                 "🛣 <b>Откуда:</b> "+d.get("from",""),
                 "🛣 <b>Куда:</b> "+d.get("to",""),
                 "📅 <b>Дата/время:</b> "+d.get("date","")+" "+d.get("time",""),
                 "👥 <b>Пассажиров:</b> "+d.get("seats",""),
                 "📞 <b>Телефон:</b> "+d.get("phone","")]
        if d.get("comment"): lines.append("💬 "+d["comment"])
        lines.append("👤 <b>От:</b> <a href=\'"+lnk+"\'>"+un+"</a>")

    else:
        await update.message.reply_text("❌ Неизвестный тип.", reply_markup=kb()); return

    msg = "\n".join(lines)
    ok = False
    for aid in ADMIN_CHAT_IDS:
        try:
            await ctx.bot.send_message(chat_id=aid, text=msg, parse_mode="HTML")
            ok = True
        except Exception as e: logger.error("❌ %s: %s", aid, e)

    txt = "✅ <b>Заявка принята!</b>\n\nДиспетчер свяжется с вами." if ok else "⚠️ Ошибка. Позвоните нам."
    await update.message.reply_text(txt, parse_mode="HTML", reply_markup=kb())

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp))
    logger.info("Бот запущен (5 кнопок)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
