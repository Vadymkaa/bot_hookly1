from __future__ import annotations
import os
import sqlite3
import logging
from datetime import datetime, timezone, time
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, ConversationHandler, filters, CallbackContext
)

# ===================== НАЛАШТУВАННЯ =====================

VIDEO_SOURCES: List[str] = [
    "BAACAgIAAxkBAAMzaQZvDpidHWrI0MUOTnnhxx4nWmoAAjR9AAJNHjhIW6XoVH8nChQ2BA",
    "BAACAgIAAxkBAAMpaQYXy_TQyyXaTOE_1mgjtEHHBiwAAoqFAAJNHjBI_VerQIrAM042BA",
    "BAACAgIAAxkBAAMqaQYXy-ZK6WuquXXaSzj2YqON98AAApKFAAJNHjBIE0NGhDaWD_Y2BA",
    "BAACAgIAAxkBAAMmaQYUhpsRFJwzusAWMBsDqck5KO8AAlCFAAJNHjBIJKUJ8OwYcio2BA",
    "BAACAgIAAxkBAAMoaQYXy6Ac3_yR3LIk_jl9uSIvH1wAAn6FAAJNHjBIUiXrOkZhwzw2BA",
]

vadymka, [23.11.2025 15:13]
BEFORE_TEXTS: List[str] = [
    """Привіт 👋

Вітаю тебе на практичному курсі «Як створювати креативи, які продають у Canva» 💚

Ми компанія Hookly, і протягом 5 днів ми разом пройдемо шлях від “не знаю, що робити” до “створюю креативи, які реально приносять продажі”.

💡 План простий:
— кожного дня ти отримуєш коротке відео і завдання на практику;
— дізнаєшся, як мислити як маркетолог, а не просто дизайнер;
— навчишся робити візуали, що зупиняють скрол і викликають бажання купити.

Цей курс — не про «красиві картинки».
Це про стратегію, емоцію і прості дії, які допоможуть будь-кому створювати ефективний візуал навіть без досвіду.

🔥 Вже за кілька днів ти зрозумієш,
— чому більшість креативів не працюють,
— як знайти ідею, яка зачепить емоційно,
— і як зробити дизайн у Canva, який виглядає професійно.

Готовий(-а) перейти від “гарно, але не продає” до “просто і ефективно”?""",
    """Привіт 👋

Вітаю тебе у другому дні курсу “Як створювати креативи, які продають у Canva” 💚

Сьогодні ми зануримось у саме серце дизайну — інтерфейс Canva.

Якщо ти раніше губився серед кнопок і панелей — не хвилюйся.
Після цього уроку Canva стане твоїм зручним і зрозумілим інструментом, який допомагає, а не плутає.

🎨 Ми розберемо:
— як легко орієнтуватися в інтерфейсі Canva;
— як підбирати шрифти та кольори, щоб вони працювали разом і передавали потрібний настрій;
— що таке шаблони, і як обирати той, що ідеально підходить під твою тему.

💡 Ти навчишся бачити, чому одні поєднання кольорів викликають довіру, а інші — відштовхують.
І зрозумієш, як зробити навіть простий дизайн стильним та професійним.""",
    """Привіт 👋

Вітаю тебе на третьому дні курсу “Як створювати креативи, які продають у Canva” 💚

Уяви: у тебе є всього 1,5 секунди, щоб людина зупинилася на твоїй рекламі.
Саме ці секунди вирішують — вона перегорне чи купить.

Тому сьогодні ми розберемо формулу, без якої жоден банер не працює —

👉 Hook → Value → Call to Action.

Це три елементи, які створюють креатив, що чіпляє, пояснює й мотивує діяти.

🎯 У цьому уроці ти дізнаєшся:
— як придумати гачок, який одразу зупиняє скрол;
— як показати вигоду просто і зрозуміло;
— як написати заклик до дії, який дійсно спрацьовує.""",
    """Привіт 👋

Вітаю тебе у четвертому дні курсу “Як створювати креативи, які продають у Canva” 💚

Сьогодні — найцікавіший етап, адже настав час переходити від теорії до дії.

Разом ми створимо декілька різних креативів і подивимося, як вони поводяться “в реальному світі” — які зупиняють увагу, викликають емоцію та приносять результат.

🎨 У цьому уроці ти дізнаєшся:
— як швидко створювати креативи під різні теми та продукти;
— як адаптувати шаблон під свою нішу;
— як перевірити, який дизайн насправді працює на продаж.""",
    """💚 Вітаю, ти пройшов(ла) курс «Як створювати креативи, які продають у Canva»!

Тепер ти не просто вмієш натискати кнопки — ти розумієш логіку маркетингового мислення,
знаєш, як створити візуал, який викликає емоцію, і можеш упевнено робити креативи, що реально продають.

🔥 Але це тільки початок.

Ми — Hookly — команда, яка допомагає бізнесам і експертам зростати через дизайн і стратегію.

💼 Ми створюємо:
— сайти та лендінги, які продають ще до того, як ти зняв перше відео;
— Telegram-боти, які автоматизують продажі та навчання;
— фірмові айдентики, бренд-паки й маркетингові системи під ключ.

Якщо після цього курсу ти хочеш:
— розвинути свій курс або бізнес візуально;
— масштабуватися через автоматизацію;
— або просто довірити дизайн професіоналам —

👉 Hookly допоможе зробити це якісно, швидко й зі смаком.

🌐 Напиши нам в інстаграм або ж в особисті в телеграм @hookly_software —
ми підберемо рішення саме для твого проєкту.
Також ти можеш подивитись про нас детальніше на нашому сайті: 🌐 <a href='https://hookly.org/'>Hookly</a>


І пам’ятай:
Навіть найкраща ідея потребує правильного креативу, щоб стати успіхом.

🚀 Дякуємо, що був(ла) з нами.
До зустрічі у наступних проєктах від Hookly 💚
"""
]

AFTER_TEXTS: List[str] = [
    """💭 Згадай останній креатив, який тебе зачепив у рекламі.
Поміркуй — що в ньому спрацювало: колір, текст чи відчуття, яке він викликав?
Запиши це. Це перший крок до власного продаючого мислення.""",
    """💭 Створи маленький тестовий дизайн із двома різними кольоровими схемами.
Відчуй різницю — який передає твій настрій і емоцію бренду краще?""",
    """💭 Подивись на будь-який банер у стрічці сьогодні.
Спробуй визначити в ньому три частини: гачок, вигоду, дію.
Якщо хоча б однієї бракує — зрозумієш, чому він “не працює”.""",
    """💭 Створи два креативи на одну тему — один мінімалістичний, другий яскравий.
Покажи їх друзям або підписникам і спитай:
“Який із них більше захотілося натиснути?”
Інколи найкращий фідбек — це чесна реакція аудиторії.""",
    """💭Вибери один зі своїх готових креативів і збережи його в трьох форматах (PNG, JPG, PDF).
Переглянь кожен на телефоні, комп’ютері й у Telegram.
Зверни увагу, як змінюється якість — так ти навчишся бачити різницю професійного підходу 👁‍🗨""",
    ""  # фінальний день
]

FINISH_TEXT = BEFORE_TEXTS[-1]

DB_PATH = os.environ.get("DB_PATH", "users.db")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "22042004")

COUNT_ASK_PWD = 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== DB =====================

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

# ===================== ВІДПРАВКА ВІДЕО =====================

async def send_protected_video(context, chat_id, source, caption=None):
    await context.bot.send_video(
        chat_id=chat_id,
        video=source,
        caption=caption,
        parse_mode=ParseMode.HTML,
        protect_content=True,
        supports_streaming=True
    )

# ===================== ЩОДЕННЕ НАДСИЛАННЯ =====================

async def send_video_job(context: CallbackContext):
    job = context.job
    chat_id = job.chat_id

    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT last_index FROM users WHERE chat_id=?", (chat_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return

    last_index = row[0]
    next_index = last_index + 1

    # --- ДЕНЬ 6: тільки фінальний текст ---
    if next_index == len(VIDEO_SOURCES):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Підпишись на інсту 🎯", url="https://www.instagram.com/hookly.software/")],
            [InlineKeyboardButton("🌐 Перейти на сайт", url="https://hookly.software")]
        ])

        await context.bot.send_message(
            chat_id=chat_id,
            text=FINISH_TEXT,
            reply_markup=kb,
            parse_mode=ParseMode.HTML
        )

        conn = get_db_conn()
        with conn:
            conn.execute("UPDATE users SET last_index=? WHERE chat_id=?", (next_index, chat_id))
        conn.close()
        return

    # --- ДЕНІ 1–5: відео + текст ---
    await send_protected_video(
        context=context,
        chat_id=chat_id,
        source=VIDEO_SOURCES[next_index],
        caption=BEFORE_TEXTS[next_index]
    )

    conn = get_db_conn()
    with conn:
        conn.execute("UPDATE users SET last_index=? WHERE chat_id=?", (next_index, chat_id))
    conn.close()

    # AFTER текст (якщо є)
    if next_index < len(AFTER_TEXTS) and AFTER_TEXTS[next_index]:
        context.job_queue.run_once(
            send_after_text_job,
            when=20 * 60,
            chat_id=chat_id
        )

# ===================== AFTER-ТЕКСТ =====================

async def send_after_text_job(context):
    chat_id = context.job.chat_id

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT last_index FROM users WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return

    idx = row[0]

    if idx < len(AFTER_TEXTS) and AFTER_TEXTS[idx]:
        await context.bot.send_message(
            chat_id=chat_id,
            text=AFTER_TEXTS[idx],
            parse_mode=ParseMode.HTML
        )

# ===================== КОМАНДИ =====================

async def start(update: Update, context):
    chat_id = update.effective_chat.id

    conn = get_db_conn()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO users(chat_id, started_at, last_index) VALUES(?,?,?)",
            (chat_id, datetime.now(timezone.utc).isoformat(), -1)
        )
    conn.close()

    # День 1
    await send_protected_video(context, chat_id, VIDEO_SOURCES[0])

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Підписатися на інсту 🎯", url="https://www.instagram.com/hookly.software/")]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text=BEFORE_TEXTS[0],
        parse_mode=ParseMode.HTML,
        reply_markup=kb
    )

    conn = get_db_conn()
    with conn:
        conn.execute("UPDATE users SET last_index=? WHERE chat_id=?", (0, chat_id))
    conn.close()

    # AFTER 1-го дня
    context.job_queue.run_once(send_after_text_job, when=15 * 60, chat_id=chat_id)

    schedule_user_job(context, chat_id)

def schedule_user_job(context, chat_id):
    # очищаємо старі задачі юзера
    for j in context.job_queue.get_jobs_by_name(f"daily_{chat_id}"):
        j.schedule_removal()

    # щоденна задача
    context.job_queue.run_daily(
        send_video_job,
        time=time(7, 1),
        chat_id=chat_id,
        name=f"daily_{chat_id}"
    )

async def stop(update: Update, context):
    chat_id = update.effective_chat.id
    for j in context.job_queue.get_jobs_by_name(f"daily_{chat_id}"):
        j.schedule_removal()

    conn = get_db_conn()
    with conn:
        conn.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))
    conn.close()

    await update.message.reply_text("🛑 Розсилка зупинена.")

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

    start_at, idx = row
    await update.message.reply_text(
        f"📅 Старт: {start_at}\n"
        f"📦 Пройдено: {idx + 1} із {len(VIDEO_SOURCES)}"
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

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    count_conv = ConversationHandler(
        entry_points=[CommandHandler("count", count_cmd)],
        states={COUNT_ASK_PWD: [MessageHandler(filters.TEXT & ~filters.COMMAND, count_check_pwd)]},
        fallbacks=[],
    )
    app.add_handler(count_conv)

    app.add_handler(MessageHandler((filters.VIDEO | filters.Document.ALL), echo_file))

    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    main()
