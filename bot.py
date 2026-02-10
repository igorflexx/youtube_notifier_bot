import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from apscheduler.schedulers.background import BackgroundScheduler

from db import cursor, conn
from youtube import resolve_channel, get_channel_info
from scheduler import check_updates

TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()
scheduler = BackgroundScheduler()
scheduler.add_job(check_updates, "interval", minutes=5, args=[app.bot])
scheduler.start()

states = {}

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить канал", callback_data="add")],
        [InlineKeyboardButton("📋 Мои каналы", callback_data="list")],
        [InlineKeyboardButton("⏱ Интервал проверки", callback_data="interval")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 YouTube Notifier", reply_markup=menu())

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "add":
        states[uid] = "add"
        await q.message.reply_text("Пришли ссылку на YouTube-канал")

    elif q.data == "list":
        cursor.execute("""
        SELECT c.channel_name, c.channel_id
        FROM channels c
        JOIN subscriptions s ON c.channel_id=s.channel_id
        WHERE s.user_id=?
        """, (uid,))
        rows = cursor.fetchall()

        if not rows:
            await q.message.reply_text("Список пуст")
            return

        for name, cid in rows:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Удалить", callback_data=f"del:{cid}")]
            ])
            await q.message.reply_text(f"📺 {name}", reply_markup=kb)

    elif q.data.startswith("del:"):
        cid = q.data.split(":")[1]
        cursor.execute(
            "DELETE FROM subscriptions WHERE user_id=? AND channel_id=?",
            (uid, cid)
        )
        conn.commit()
        await q.message.reply_text("❌ Канал удалён")

    elif q.data == "interval":
        states[uid] = "interval"
        await q.message.reply_text("Отправь интервал в минутах (например 5)")

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    if states.get(uid) == "add":
        cid = resolve_channel(text)
        if not cid:
            await update.message.reply_text("❌ Не удалось определить канал")
            return

        name, last = get_channel_info(cid)
        cursor.execute(
            "INSERT OR IGNORE INTO channels VALUES (?, ?, ?)",
            (cid, name, last)
        )
        cursor.execute(
            "INSERT INTO subscriptions VALUES (?, ?)",
            (uid, cid)
        )
        conn.commit()

        states.pop(uid)
        await update.message.reply_text(f"✅ Канал добавлен: {name}")

    elif states.get(uid) == "interval":
        try:
            minutes = int(text)
            scheduler.remove_all_jobs()
            scheduler.add_job(
                check_updates, "interval",
                minutes=minutes, args=[app.bot]
            )
            await update.message.reply_text(
                f"⏱ Интервал установлен: {minutes} мин"
            )
            states.pop(uid)
        except:
            await update.message.reply_text("❌ Введи число")

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

app.run_polling()
