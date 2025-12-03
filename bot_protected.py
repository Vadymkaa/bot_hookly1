from __future__ import annotations
import os
import sqlite3
import logging
import traceback
from datetime import datetime, timezone, time
from typing import List

from logging.handlers import RotatingFileHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, ConversationHandler, filters, CallbackQueryHandler
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

Разом ми створимо декілька різних креативів і подивимось, як вони поводяться “в реальному світі” — які зупиняють увагу, викликають емоцію та приносять результат.

🎨 У цьому уроці ти дізнаєшся:
— як швидко створювати креативи під різні теми та продукти;
— як адаптувати шаблон під свою нішу;
— як перевірити, який дизайн насправді працює на продаж.""",
    """Привіт 👋

Сьогодні — наш останній день курсу “Як створювати креативи, які продають у Canva” 💚

Ти вже навчився мислити як маркетолог, працювати з шаблонами, кольорами, текстами та створювати власні креативи.

І тепер час поставити фінальну крапку — або скоріше, впевнено натиснути “Зберегти” 😉

🎨 У цьому уроці ми розберемо:
— як правильно зберігати креативи у різних форматах, щоб не втрачати якість;
— які формати обрати для реклами, соціальних мереж і лендингів;
— і, звісно, кілька корисних фішок у Canva, які зроблять твою роботу швидшою та зручнішою.

💡 Це ті дрібниці, які відрізняють “початківця” від людини, що справді володіє інструментом.

🎥 Після цього відео ти зможеш самостійно створювати, оформлювати й експортувати будь-який дизайн — від сторіс до рекламного банера.

🚀 Дякую, що пройшов(-ла) цей шлях до кінця!

Пам’ятай: найкращі креативи народжуються не з ідеальних шаблонів, а з твоїх ідей і впевненості у своїй подачі.

💬 І зовсім скоро — бонус: кілька прихованих фішок Canva, про які знають лише досвідчені дизайнери 😉""",
]

# Окремий унікальний фінальний текст (не дублює BEFORE_TEXTS)
FINISH_TEXT = """💚 Вітаю, ти пройшов(ла) курс «Як створювати креативи, які продають у Canva»!

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

🌐 Напиши нам в інстаграм або ж в особисті в телеграм @hookly1_software —
ми підберемо рішення саме для твого проєкту.
Також ти можеш подивитись про нас детальніше на нашому сайті: 🌐 <a href="https://hookly.org/">Hookly</a>


І пам’ятай:
Навіть найкраща ідея потребує правильного креативу, щоб стати успіхом.

🚀 Дякуємо, що був(ла) з нами.
До зустрічі у наступних проєктах від Hookly 💚
"""

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
Переглянь кожен на телефоні, комп’ютері й уTelegram.
Зверни увагу, як змінюється якість — так ти навчишся бачити різницю професійного підходу 👁‍🗨""",
    ""  # фінальний день (немає after)
]

DB_PATH = os.environ.get("DB_PATH", "users.db")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "22042004")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))  # постав свій чат id або 0

COUNT_ASK_PWD = 1
DEBUG_ASK_PWD = 1001

# Telegram caption limit
MAX_CAPTION_LEN = 1024
# chunk size for long messages (safe margin)
MSG_CHUNK_SIZE = 4000

# ===================== ЛОГУВАННЯ =====================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# file rotating handler
file_handler = RotatingFileHandler("bot.log", maxBytes=10_000_000, backupCount=5, encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(file_formatter)
logger.addHandler(console_handler)

# ===================== DB =====================

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL,
    last_index INTEGER NOT NULL DEFAULT -1
);
"""

def get_db_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# ===================== HELPERS =====================

async def send_long_message(bot, chat_id: int, text: str, parse_mode=ParseMode.HTML, chunk_size: int = MSG_CHUNK_SIZE):
    if not text:
        return
    start = 0
    while start < len(text):
        part = text[start:start+chunk_size]
        try:
            await bot.send_message(chat_id=chat_id, text=part, parse_mode=parse_mode)
        except Exception:
            logger.exception("Failed to send chunk as HTML, retrying without parse_mode")
            try:
                await bot.send_message(chat_id=chat_id, text=part)
            except Exception:
                logger.exception("Failed to send message chunk to %s", chat_id)
        start += chunk_size

# ===================== ВІДПРАВКА ВІДЕО =====================

async def send_protected_video(context: ContextTypes.DEFAULT_TYPE, chat_id: int, source, caption: str | None = None):
    """
    Надсилає відео. Якщо caption <= MAX_CAPTION_LEN — надсилаємо як caption.
    Якщо caption > MAX_CAPTION_LEN — надсилаємо відео без caption і потім
    відправляємо caption як окреме (можливо розбиття) повідомлення.
    """
    try:
        if caption and len(caption) <= MAX_CAPTION_LEN:
            await context.bot.send_video(
                chat_id=chat_id,
                video=source,
                caption=caption,
                parse_mode=ParseMode.HTML,
                protect_content=True,
                supports_streaming=True
            )
            return

        # send video without caption
        await context.bot.send_video(
            chat_id=chat_id,
            video=source,
            protect_content=True,
            supports_streaming=True
        )

        # then send caption as one or multiple messages
        if caption:
            await send_long_message(context.bot, chat_id, caption, parse_mode=ParseMode.HTML)

    except Exception:
        logger.exception("Failed to send video to %s", chat_id)
        # повідомлення адміну
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"⚠️ Не вдалося надіслати відео користувачу {chat_id}:\n<pre>{traceback.format_exc()}</pre>",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                logger.exception("Failed to notify admin about send_video failure")

# ===================== ЩОДЕННЕ НАДСИЛАННЯ =====================

async def send_video_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        job = context.job
        chat_id = getattr(job, "chat_id", None)
        if chat_id is None:
            logger.warning("Job without chat_id, skipping")
            return

        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT last_index FROM users WHERE chat_id=?", (chat_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return

        last_index = row[0]
        next_index = last_index + 1

        # День 6 — тільки фінальний текст
        if next_index == 5:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Підпишись на інсту 🎯", url="https://www.instagram.com/hookly.software/")],
                [InlineKeyboardButton("🌐 Перейти на сайт", url="https://hookly.software")]
            ])
            try:
                await send_long_message(context.bot, chat_id, FINISH_TEXT, parse_mode=ParseMode.HTML)
                # send small empty message with buttons (Telegram requires either text or reply_markup)
                await context.bot.send_message(chat_id=chat_id, reply_markup=kb, text=" ")
            except Exception:
                logger.exception("Failed to send finish message to %s", chat_id)
                if ADMIN_CHAT_ID:
                    try:
                        await context.bot.send_message(
                            chat_id=ADMIN_CHAT_ID,
                            text=f"⚠️ Failed to send FINISH_TEXT to {chat_id}\n<pre>{traceback.format_exc()}</pre>",
                            parse_mode=ParseMode.HTML
                        )
                    except Exception:
                        logger.exception("Failed to notify admin about finish message failure")

            conn = get_db_conn()
            with conn:
                conn.execute("UPDATE users SET last_index=? WHERE chat_id=?", (next_index, chat_id))
            conn.close()

            return

        # День 1–5 — відео + BEFORE текст
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

        # AFTER текст
        if AFTER_TEXTS[next_index]:
            try:
                context.job_queue.run_once(
                    send_after_text_job,
                    when=20 * 60,
                    chat_id=chat_id
                )
            except Exception:
                logger.exception("Failed to schedule after_text job for %s", chat_id)

    except Exception:
        logger.exception("Unhandled exception in send_video_job")
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"🔥 Exception in send_video_job:\n<pre>{traceback.format_exc()}</pre>",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                logger.exception("Failed to notify admin about send_video_job exception")

# ===================== AFTER-ТЕКСТ =====================

async def send_after_text_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        job = context.job
        chat_id = getattr(job, "chat_id", None)
        if chat_id is None:
            logger.warning("After-text job without chat_id, skipping")
            return

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT last_index FROM users WHERE chat_id=?", (chat_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return

        idx = row[0]

        if idx < len(AFTER_TEXTS) and AFTER_TEXTS[idx]:
            try:
                await send_long_message(context.bot, chat_id, AFTER_TEXTS[idx], parse_mode=ParseMode.HTML)
            except Exception:
                logger.exception("Failed to send after text to %s", chat_id)
                if ADMIN_CHAT_ID:
                    try:
                        await context.bot.send_message(
                            chat_id=ADMIN_CHAT_ID,
                            text=f"⚠️ Failed to send AFTER_TEXT to {chat_id}\n<pre>{traceback.format_exc()}</pre>",
                            parse_mode=ParseMode.HTML
                        )
                    except Exception:
                        logger.exception("Failed to notify admin about after_text failure")

    except Exception:
        logger.exception("Unhandled exception in send_after_text_job")
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"🔥 Exception in send_after_text_job:\n<pre>{traceback.format_exc()}</pre>",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                logger.exception("Failed to notify admin about after_text exception")

# ===================== КОМАНДИ =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id

        conn = get_db_conn()
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO users(chat_id, started_at, last_index) VALUES(?,?,?)",
                (chat_id, datetime.now(timezone.utc).isoformat(), -1)
            )
        conn.close()

        # День 1: відео + текст
        await send_protected_video(context, chat_id, VIDEO_SOURCES[0], BEFORE_TEXTS[0])

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Підписатися на інсту 🎯", url="https://www.instagram.com/hookly.software/")]
        ])

        try:
            # send text separately (handles long text)
            # send small empty message with buttons
            await context.bot.send_message(chat_id=chat_id, reply_markup=kb, text=" ")
        except Exception:
            logger.exception("Failed to send start message to %s", chat_id)

        conn = get_db_conn()
        with conn:
            conn.execute("UPDATE users SET last_index=? WHERE chat_id=?", (0, chat_id))
        conn.close()

        # AFTER 1-го дня
        try:
            context.job_queue.run_once(send_after_text_job, when=15 * 60, chat_id=chat_id)
        except Exception:
            logger.exception("Failed to schedule after_text for start")

        schedule_user_job(context, chat_id)
    except Exception:
        logger.exception("Unhandled exception in start")
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"🔥 Exception in start handler:\n<pre>{traceback.format_exc()}</pre>",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                logger.exception("Failed to notify admin about start exception")

def schedule_user_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    try:
        # remove existing daily job(s) for this user to avoid duplicates
        for j in context.job_queue.get_jobs_by_name(f"daily_{chat_id}"):
            j.schedule_removal()

        context.job_queue.run_daily(
            send_video_job,
            time=time(7, 1),
            chat_id=chat_id,
            name=f"daily_{chat_id}"
        )
    except Exception:
        logger.exception("Failed to schedule daily job for %s", chat_id)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        for j in context.job_queue.get_jobs_by_name(f"daily_{chat_id}"):
            j.schedule_removal()

        conn = get_db_conn()
        with conn:
            conn.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))
        conn.close()

        await update.message.reply_text("🛑 Розсилка зупинена.")
    except Exception:
        logger.exception("Unhandled exception in stop")
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"🔥 Exception in stop handler:\n<pre>{traceback.format_exc()}</pre>",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                logger.exception("Failed to notify admin about stop exception")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    except Exception:
        logger.exception("Unhandled exception in status_cmd")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — почати\n"
        "/stop — зупинити\n"
        "/status — статус\n"
        "/help — довідка\n"
        "/debug — адмін: програти весь курс\n"
        "/delete_webhook — адмін: видалити webhook (якщо хочеш використовувати polling)"
    )

async def echo_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        m = update.message
        if m.video:
            await m.reply_text(f"<code>{m.video.file_id}</code>", parse_mode="HTML")
        elif m.document:
            await m.reply_text(f"<code>{m.document.file_id}</code>", parse_mode="HTML")
    except Exception:
        logger.exception("Unhandled exception in echo_file")

# ===================== /count =====================

async def count_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Введи пароль:")
    return COUNT_ASK_PWD

async def count_check_pwd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    except Exception:
        logger.exception("Unhandled exception in count_check_pwd")
        await update.message.reply_text("❌ Помилка при підрахунку")
        return ConversationHandler.END

# ===================== DEBUG / ADMINSKA КНОПКА =====================

async def debug_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Введи адмін-пароль:")
    return DEBUG_ASK_PWD

async def debug_check_pwd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pwd = update.message.text.strip()

    if pwd != ADMIN_PASS:
        await update.message.reply_text("❌ Невірний пароль")
        return DEBUG_ASK_PWD

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶ Пройти весь курс (адмін)", callback_data="debug_run_all")]
    ])

    await update.message.reply_text(
        "✅ Адмін-режим увімкнено.\nНатисни кнопку нижче, щоб програти весь курс.",
        reply_markup=kb
    )

    return ConversationHandler.END

async def debug_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data != "debug_run_all":
        return

    chat_id = query.message.chat.id

    await context.bot.send_message(chat_id, "▶ Починаю програвання всіх днів…")

    # День 1–5: відео + BEFORE + AFTER (одразу)
    for i in range(5):
        try:
            await send_protected_video(context, chat_id, VIDEO_SOURCES[i], BEFORE_TEXTS[i])
        except Exception:
            pass

        if AFTER_TEXTS[i]:
            try:
                await send_long_message(context.bot, chat_id, AFTER_TEXTS[i], parse_mode=ParseMode.HTML)
            except Exception:
                logger.exception("Failed to send after text during debug to %s", chat_id)

    # День 6: фінальний текст
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Підпишись на інсту 🎯", url="https://www.instagram.com/hookly.software/")],
        [InlineKeyboardButton("🌐 Перейти на сайт", url="https://hookly.software")]
    ])

    try:
        await send_long_message(context.bot, chat_id, FINISH_TEXT, parse_mode=ParseMode.HTML)
        await context.bot.send_message(chat_id=chat_id, reply_markup=kb, text=" ")
    except Exception:
        logger.exception("Failed to send finish text during debug to %s", chat_id)

    await context.bot.send_message(chat_id, "✅ Перевірка закінчена. Всі етапи пройдені.")

# ===================== WEBHOOK HELPERS =====================

async def delete_webhook_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only admin
    if str(update.effective_user.id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("Немає прав.")
        return
    try:
        await context.bot.delete_webhook(drop_pending_updates=True)
        await update.message.reply_text("Webhook видалено. Тепер бот може працювати через polling.")
    except Exception:
        logger.exception("Failed to delete webhook")
        await update.message.reply_text("Не вдалося видалити webhook. Подивись логи.")

# ===================== APP =====================

async def post_init(app):
    try:
        # DB init
        conn = get_db_conn()
        with conn:
            conn.execute(CREATE_TABLE_SQL)
        conn.close()

        # Check webhook info and warn admin if set (to avoid getUpdates conflict)
        try:
            webhook_info = await app.bot.get_webhook_info()
            url = getattr(webhook_info, "url", None)
            if url:
                msg = f"⚠️ Webhook currently set to: {url}. If you use polling, delete webhook (use /delete_webhook or deleteWebhook)."
                logger.warning(msg)
                if ADMIN_CHAT_ID:
                    try:
                        await app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)
                    except Exception:
                        logger.exception("Failed to notify admin about webhook info")
        except Exception:
            logger.exception("Could not get webhook info")
    except Exception:
        logger.exception("Failed to run post_init")

async def error_handler(update: object | None, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Update caused error")
    if ADMIN_CHAT_ID:
        try:
            text = "🔥 Unhandled exception\n"
            if update:
                text = f"🔥 Unhandled exception for update: {getattr(update, 'update_id', 'n/a')}\n"
            text += f"<pre>{traceback.format_exc()}</pre>"
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode=ParseMode.HTML)
        except Exception:
            logger.exception("Failed to send error to admin")

def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # basic handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("delete_webhook", delete_webhook_cmd))

    # count conversation
    count_conv = ConversationHandler(
        entry_points=[CommandHandler("count", count_cmd)],
        states={COUNT_ASK_PWD: [MessageHandler(filters.TEXT & ~filters.COMMAND, count_check_pwd)]},
        fallbacks=[],
    )
    app.add_handler(count_conv)

    # debug/admin conversation
    debug_conv = ConversationHandler(
        entry_points=[CommandHandler("debug", debug_cmd)],
        states={DEBUG_ASK_PWD: [MessageHandler(filters.TEXT & ~filters.COMMAND, debug_check_pwd)]},
        fallbacks=[],
    )
    app.add_handler(debug_conv)

    # callback for debug button
    app.add_handler(CallbackQueryHandler(debug_callback, pattern="debug_run_all"))

    # file id echo
    app.add_handler(MessageHandler((filters.VIDEO | filters.Document.ALL), echo_file))

    # global error handler
    app.add_error_handler(error_handler)

    # Start polling (ensure only one instance uses this BOT_TOKEN)
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    main()
