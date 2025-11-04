from __future__ import annotations
import os
import sqlite3
import logging
from datetime import datetime, timezone, time
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

# ===================== НАЛАШТУВАННЯ =====================
VIDEO_SOURCES: List[str] = [
    "BAACAgIAAxkBAAMzaQZvDpidHWrI0MUOTnnhxx4nWmoAAjR9AAJNHjhIW6XoVH8nChQ2BA",
    "BAACAgIAAxkBAAMpaQYXy_TQyyXaTOE_1mgjtEHHBiwAAoqFAAJNHjBI_VerQIrAM042BA",
    "BAACAgIAAxkBAAMqaQYXy-ZK6WuquXXaSzj2YqON98AAApKFAAJNHjBIE0NGhDaWD_Y2BA",
    "BAACAgIAAxkBAAMmaQYUhpsRFJwzusAWMBsDqck5KO8AAlCFAAJNHjBIJKUJ8OwYcio2BA",
    "BAACAgIAAxkBAAMoaQYXy6Ac3_yR3LIk_jl9uSIvH1wAAn6FAAJNHjBIUiXrOkZhwzw2BA",
]

BEFORE_TEXTS: List[str] = [
    """Привіт 👋

Вітаю тебе на практичному курсі «Як створювати креативи, які продають у Canva» 💚

🎥 У цьому уроці ти дізнаєшся, чому головне не дизайн, а мислення маркетолога.
""",
    "Привіт! Це другий день інтенсиву...",
    "Привіт! Це третій день...",
    "Привіт! Це четвертий день...",
    "Привіт! Це п’ятий день..."
]

AFTER_TEXTS = [
    "🎯 Сьогодні протягом дня...",
    "🎯 За 10 хвилин сформулюй одну річну ціль...",
    "🎯 Візьми одну проблему...",
    "🎯 Обери одну подію...",
    "🎯 Згадай ситуацію..."
]

EXTRA_FILES = {}

DB_PATH = "users.db"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "22042004")

COUNT_ASK_PWD = 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== БАЗА ДАНИХ =====================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    last_index INTEGER NOT NULL DEFAULT -1
);
"""

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


# ===================== ВІДЕО =====================
async def send_protected_video(context, chat_id, source, caption=None):
    await context.bot.send_video(
        chat_id=chat_id,
        video=source,
        caption=caption,
        parse_mode=ParseMode.HTML,
        protect_content=True,
        supports_streaming=True
    )


# ===================== JOBS =====================
async def send_video_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT last_index FROM users WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()

    if not row:
        job.schedule_removal()
        conn.close()
        return

    last_index = row[0]
    next_index = last_index + 1

    if next_index >= len(VIDEO_SOURCES):
        job.schedule_removal()
        conn.close()
        return

    # BEFORE TEXT
    if next_index < len(BEFORE_TEXTS):
        await context.bot.send_message(
            chat_id=chat_id,
            text=BEFORE_TEXTS[next_index],
            parse_mode=ParseMode.HTML
        )

    # VIDEO
    await send_protected_video(
        context=context,
        chat_id=chat_id,
        source=VIDEO_SOURCES[next_index],
        caption=f"🎬 Відео {next_index + 1} з {len(VIDEO_SOURCES)}"
    )

    with conn:
        conn.execute("UPDATE users SET last_index=? WHERE chat_id=?", (next_index, chat_id))

    conn.close()

    # SCHEDULE AFTER TEXT
    context.job_queue.run_once(
        send_after_text_job,
        when=20 * 60,
        chat_id=chat_id
    )


async def send_after_text_job(context):
    chat_id = context.job.chat_id
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("SELECT last_index FROM users WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return

    last_index = row[0]

    if last_index < len(AFTER_TEXTS):
        await context.bot.send_message(
            chat_id=chat_id,
            text=AFTER_TEXTS[last_index],
            parse_mode=ParseMode.HTML
        )


def schedule_user_job(context, chat_id):
    for j in context.job_queue.get_jobs_by_name(f"daily_{chat_id}"):
        j.schedule_removal()

    context.job_queue.run_daily(
        send_video_job,
        time=time(7, 1),
        chat_id=chat_id,
        name=f"daily_{chat_id}"
    )


# ===================== КОМАНДИ =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    conn = get_db_conn()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO users(chat_id, started_at, last_index) VALUES(?,?,?)",
            (chat_id, datetime.now(timezone.utc).isoformat(), 0)
        )
    conn.close()

    # ✅ ПЕРШЕ ВІДЕО
    await update.message.reply_text(BEFORE_TEXTS[0])
    await send_protected_video(
        context=context,
        chat_id=chat_id,
        source=VIDEO_SOURCES[0],
        caption="🎬 Відео 1 з 5"
    )

    # ✅ Кнопка Instagram
    keyboard = [
        [InlineKeyboardButton("Instagram 📸", url="https://instagram.com/hookly.software")]
    ]
    await update.message.reply_text(
        "Привіт! 👋\nОсь мої соцмережі:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # ✅ AFTER TEXT через 15 хв
    context.job_queue.run_once(send_after_text_job, when=15 * 60, chat_id=chat_id)

    # ✅ Запланувати наступний день
    schedule_user_job(context, chat_id)


async def stop(update, context):
    chat_id = update.effective_chat.id

    for j in context.job_queue.get_jobs_by_name(f"daily_{chat_id}"):
        j.schedule_removal()

    conn = get_db_conn()
    with conn:
        conn.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))
    conn.close()

    await update.message.reply_text("🛑 Розсилку зупинено.")


async def status_cmd(update, context):
    chat_id = update.effective_chat.id
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT started_at, last_index FROM users WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("❗ Ти ще не почав. Натисни /start")
        return

    started, index = row
    await update.message.reply_text(
        f"📅 Старт: {started}\n📦 Пройдено: {index + 1} із {len(VIDEO_SOURCES)}"
    )


async def help_cmd(update, context):
    await update.message.reply_text(
        "/start — почати\n"
        "/stop — зупинити\n"
        "/status — статус\n"
        "/help — довідка\n"
    )


async def echo_file(update, context):
    m = update.message
    if m.video:
        await m.reply_text(f"<code>{m.video.file_id}</code>", parse_mode="HTML")
    elif m.document:
        await m.reply_text(f"<code>{m.document.file_id}</code>", parse_mode="HTML")


# ===================== /count =====================
async def count_cmd(update, context):
    await update.message.reply_text("🔐 Введи пароль:")
    return COUNT_ASK_PWD


async def count_check_pwd(update, context):
    if update.message.text.strip() != ADMIN_PASS:
        await update.message.reply_text("❌ Невірний пароль")
        return COUNT_ASK_PWD

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    conn.close()

    await update.message.reply_text(f"👥 Користувачів: {total}")
    return ConversationHandler.END


# ===================== APP =====================
async def post_init(app):
    conn = get_db_conn()
    with conn:
        conn.execute(CREATE_TABLE_SQL)
    conn.close()


async def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    count_conv = ConversationHandler(
        entry_points=[CommandHandler("count", count_cmd)],
        states={COUNT_ASK_PWD: [MessageHandler(filters.TEXT & ~filters.COMMAND, count_check_pwd)]},
        fallbacks=[]
    )
    app.add_handler(count_conv)

    app.add_handler(MessageHandler((filters.VIDEO | filters.Document.ALL), echo_file))

    await app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
