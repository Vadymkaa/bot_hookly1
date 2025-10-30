#!/usr/bin/env python3
# bot_protected.py
"""
Telegram bot: щоденні відео-уроки о 08:00 Europe/Warsaw (5 модулів).
Захист: protect_content + персональний водяний знак (ffmpeg drawtext).

ІНСТРУКЦІЯ:
1. Створи папку "videos" і поклади в неї:
   module1.mp4, module2.mp4, module3.mp4, module4.mp4, module5.mp4
2. Встанови залежності:
   pip install aiogram apscheduler python-dotenv
3. Встанови ffmpeg (має бути в PATH).
4. Вкажи шлях до шрифту TTF у FONT_PATH (нижче).
   Наприклад: /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
5. Створи .env з:
   BOT_TOKEN=ваш_токен_бота
6. Запуск:
   python bot_protected.py
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# ----------------- КОНФІГ -----------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Вкажи BOT_TOKEN в .env файлі")

VIDEOS_DIR = Path("videos")
USERS_FILE = Path("users.json")
TIMEZONE = ZoneInfo("Europe/Warsaw")
SCHEDULE_HOUR = 8
SCHEDULE_MINUTE = 0

# Назви відео (по 5 модулів)
MODULE_VIDEOS = [
    "module1.mp4",
    "module2.mp4",
    "module3.mp4",
    "module4.mp4",
    "module5.mp4",
]

# Тексти для кожного модуля (коротко, професійно)
MODULE_TEXTS = [
    (
        "🎓 *Модуль 1 — Основи дизайну, що продає*\n\n"
        "🔸 Як мислити як маркетолог, а не як дизайнер\n"
        "🔸 Психологія візуального сприйняття: кольори, шрифти, композиція\n"
        "🔸 Типові помилки у візуалах для курсів\n\n"
        "_Підказка:_ почни з бізнес-логіки — красиво має продавати."
    ),
    (
        "🎨 *Модуль 2 — Canva: інструмент для ефективних креативів*\n\n"
        "🔸 Інтерфейс, шаблони, брендинг\n"
        "🔸 Робота з кольоровими схемами та шрифтами\n"
        "🔸 Адаптація шаблонів під нішу\n\n"
        "_Підказка:_ шаблон — стартова платформа, роби його своїм."
    ),
    (
        "🚀 *Модуль 3 — Креатив, який продає*\n\n"
        "🔸 Структура банера: Hook → Value → CTA\n"
        "🔸 Вибір зображення і створення емоційного зв'язку\n"
        "🔸 Приклади робочих креативів\n\n"
        "_Підказка:_ емоція + чіткий CTA = конверсія."
    ),
    (
        "✍️ *Модуль 4 — Практика: створюємо перший продаючий креатив*\n\n"
        "🔸 Покрокова інструкція створення дизайну\n"
        "🔸 Підготовка банера для Meta, Telegram, лендингу\n"
        "🔸 Тестування і аналіз ефективності\n\n"
        "_Підказка:_ тестуй A/B і звужуй аудиторію."
    ),
    (
        "🌟 *Модуль 5 — Професійні фішки та формати*\n\n"
        "🔸 Бренд-пак у Canva\n"
        "🔸 Обкладинки для відео, слайдів, курсів\n"
        "🔸 Автоматизація процесу створення дизайнів\n\n"
        "_Підказка:_ системність економить тисячі годин."
    ),
]

# Захистні налаштування
ENABLE_WATERMARK = True
# Шлях до шрифту TTF (онови під свій сервер)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
# Шаблон drawtext (можеш змінити розмір / позицію)
# {text} буде замінено на user_tag + datetime
DRAWTEXT_TEMPLATE = (
    "fontfile={font}:text='{text}':fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5:"
    "boxborderw=5:x=10:y=H-th-10"
)

# Логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ----------------- КОРИСТУВАЧІ / ЗБЕРІГАННЯ -----------------
def load_users() -> Dict[str, dict]:
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Не вдалося прочитати users.json — створюємо новий.")
            return {}
    return {}

def save_users(data: Dict[str, dict]):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Помилка при записі users.json")

# Структура users: { "<chat_id>": {"module_idx": int, "subscribed": bool} }
users = load_users()

# ----------------- ФУНКЦІЯ: СТВОРИТИ ВІДЕО З ВОДЯНИМ ЗНАКОМ -----------------
def create_watermarked_video(input_path: Path, user_tag: str) -> Path:
    """
    Використовує ffmpeg drawtext для створення тимчасового водяного відео.
    Повертає шлях до тимчасового файлу (не видаляє його) — викликач має видалити після використання.
    Бався обережно: це синхронний виклик ffmpeg (CPU-bound).
    """
    if not Path(FONT_PATH).exists():
        raise FileNotFoundError(f"Шрифт не знайдено: {FONT_PATH}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    raw_text = f"{user_tag} • {timestamp}"
    # ескейп двокрапки та апострофа для ffmpeg
    safe_text = raw_text.replace(":", "\\:").replace("'", "\\'")
    drawtext = DRAWTEXT_TEMPLATE.format(font=FONT_PATH, text=safe_text)

    tmpf = tempfile.NamedTemporaryFile(prefix="wm_", suffix=".mp4", delete=False)
    out_path = Path(tmpf.name)
    tmpf.close()

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        f"drawtext={drawtext}",
        "-c:a",
        "copy",
        str(out_path),
    ]
    logger.info("Запускаю ffmpeg для %s -> %s", input_path, out_path)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        # прибрати файл якщо щось пішло не так
        try:
            out_path.unlink(missing_ok=True)
        except Exception:
            pass
        err = proc.stderr.decode("utf-8", errors="ignore")
        logger.error("ffmpeg помилка: %s", err)
        raise RuntimeError(f"ffmpeg failed: {err}")
    logger.info("ffmpeg завершився успішно для %s", input_path)
    return out_path

# ----------------- ВІДПРАВКА УРОКУ КОРИСТУВАЧУ -----------------
async def send_lesson_to_user(chat_id: int):
    key = str(chat_id)
    if key not in users or not users[key].get("subscribed", False):
        return

    idx = users[key].get("module_idx", 0)
    if idx >= len(MODULE_VIDEOS):
        # Кінець курсу
        try:
            await bot.send_message(chat_id, "✅ Ви пройшли всі 5 модулів курсу. Якщо хочете повторити — натисніть /start.")
        except Exception:
            logger.exception("Не вдалося повідомити користувача про завершення %s", chat_id)
        users[key]["subscribed"] = False
        save_users(users)
        return

    video_file = VIDEOS_DIR / MODULE_VIDEOS[idx]
    caption = MODULE_TEXTS[idx]

    if not video_file.exists():
        await bot.send_message(chat_id, f"⚠️ Відео для модуля {idx+1} тимчасово недоступне. Пишіть адміну.")
        logger.error("Відео відсутнє: %s", video_file)
        return

    send_path: Path = video_file
    temp_to_remove: Optional[Path] = None
    try:
        # Якщо захист ввімкнено — створюємо персональний водяний знак
        if ENABLE_WATERMARK:
            try:
                chat = await bot.get_chat(chat_id)
                user_tag = chat.username or f"id{chat_id}"
            except Exception:
                user_tag = f"id{chat_id}"

            try:
                send_path = create_watermarked_video(video_file, user_tag)
                temp_to_remove = send_path
            except Exception as e:
                logger.exception("Не вдалося створити водяний знак: %s", e)
                # fallback на оригінал без watermark
                send_path = video_file
                temp_to_remove = None

        # Відправка з protect_content=True
        # aiogram у різних версіях може приймати protect_content, пробуємо стандартний виклик
        with open(send_path, "rb") as fp:
            # Якщо бібліотека не підтримує protect_content — це може викликати TypeError.
            # Але зазвичай воно працює. Якщо помилка — можна використовувати bot.api_call("sendVideo", {...})
            await bot.send_video(
                chat_id=chat_id,
                video=fp,
                caption=caption,
                parse_mode="Markdown",
                protect_content=True,
            )

        # Після успіху — підвищуємо індекс
        users[key]["module_idx"] = idx + 1
        save_users(users)
        logger.info("Відправлено модуль %d користувачу %s", idx + 1, chat_id)

    except TypeError as te:
        # Наприклад, якщо aiogram не очікує protect_content — fallback на api_call
        logger.warning("TypeError при send_video (мабуть protect_content не підтримується), використовую api_call: %s", te)
        try:
            # Для api_call потрібно передавати multipart-форми; aiogram.Bot.api_call підтримує передачу files через kwargs
            # Трохи грубий fallback — відправка через sendVideo без protect_content
            with open(send_path, "rb") as fp:
                await bot.send_video(chat_id=chat_id, video=fp, caption=caption, parse_mode="Markdown")
            users[key]["module_idx"] = idx + 1
            save_users(users)
        except Exception:
            logger.exception("Fallback send failed for user %s", chat_id)
    except Exception:
        logger.exception("Помилка відправки відео користувачу %s", chat_id)
        try:
            await bot.send_message(chat_id, "Виникла помилка при відправці уроку. Спробуйте /next або напишіть адміну.")
        except Exception:
            pass
    finally:
        # Видаляємо тимчасовий файл якщо був
        if temp_to_remove:
            try:
                temp_to_remove.unlink(missing_ok=True)
                logger.info("Тимчасовий файл видалено: %s", temp_to_remove)
            except Exception:
                logger.exception("Не вдалося видалити тимчасовий файл %s", temp_to_remove)

# ----------------- ЩОДЕННА РОЗСИЛКА -----------------
async def daily_job():
    logger.info("Розсилка уроків: %d користувачів в пам'яті", len(users))
    tasks = []
    for key, data in users.items():
        if data.get("subscribed", False):
            chat_id = int(key)
            tasks.append(send_lesson_to_user(chat_id))
    if tasks:
        await asyncio.gather(*tasks)
    logger.info("Розсилка завершена")

# ----------------- ХЕНДЛЕРИ -----------------
@dp.message_handler(commands=["start", "subscribe"])
async def cmd_start(message: types.Message):
    key = str(message.chat.id)
    already = (key in users) and users[key].get("subscribed", False)
    if already:
        await message.answer("Ви вже підписані. Щоб отримати наступний урок прямо зараз — /next.")
        return
    users[key] = {"module_idx": users.get(key, {}).get("module_idx", 0), "subscribed": True}
    save_users(users)
    await message.answer(
        "Привіт 👋 Ти підписаний на щоденні відео-уроки. Кожного ранку о 08:00 (Europe/Warsaw) бот надішле наступний модуль.\n\n"
        "Команди:\n"
        "/next - отримати наступний урок зараз\n"
        "/status - подивитись прогрес\n"
        "/stop - відписатись\n"
        "/help - допомога"
    )

@dp.message_handler(commands=["stop", "unsubscribe"])
async def cmd_stop(message: types.Message):
    key = str(message.chat.id)
    if key in users:
        users[key]["subscribed"] = False
        save_users(users)
        await message.answer("Ви відписані від щоденних уроків. Щоб підписатись знову — /start.")
    else:
        await message.answer("Ви ще не підписані. Щоб почати — /start.")

@dp.message_handler(commands=["next"])
async def cmd_next(message: types.Message):
    key = str(message.chat.id)
    if key not in users:
        users[key] = {"module_idx": 0, "subscribed": False}
        save_users(users)
    await message.answer("Надсилаю наступний урок...")
    await send_lesson_to_user(message.chat.id)

@dp.message_handler(commands=["status"])
async def cmd_status(message: types.Message):
    key = str(message.chat.id)
    if key not in users:
        await message.answer("Ви ще не підписані. /start — щоб підписатись.")
        return
    idx = users[key].get("module_idx", 0)
    subscribed = users[key].get("subscribed", False)
    await message.answer(f"Прогрес: модуль {idx} з {len(MODULE_VIDEOS)}.\nПідписка: {'активна' if subscribed else 'вимкнена'}.")

@dp.message_handler(commands=["help"])
async def cmd_help(message: types.Message):
    await message.answer(
        "Цей бот надсилає щоденні відео-уроки о 08:00 Europe/Warsaw.\n"
        "Команди:\n"
        "/start — підписатися\n"
        "/stop — відписатися\n"
        "/next — отримати наступний урок прямо зараз\n"
        "/status — подивитися прогрес\n"
        "/help — це повідомлення"
    )

# Глобальний обробник помилок
@dp.errors_handler()
async def global_error_handler(update, error):
    logger.exception("Global error: %s", error)
    return True

# ----------------- ГОЛОВНА -----------------
def main():
    # Перевірка наявності відео
    missing = [v for v in MODULE_VIDEOS if not (VIDEOS_DIR / v).exists()]
    if missing:
        logger.warning("Відсутні відеофайли у %s: %s", VIDEOS_DIR, missing)
        # Робота продовжується; користувач отримає повідомлення про відсутність відео

    # Запускаємо планувальник
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    trigger = CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, timezone=TIMEZONE)
    scheduler.add_job(lambda: asyncio.create_task(daily_job()), trigger=trigger, id="daily_send")
    scheduler.start()
    logger.info("Планувальник запущено: щодня о %02d:%02d %s", SCHEDULE_HOUR, SCHEDULE_MINUTE, TIMEZONE)

    # Запускаємо long polling
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    main()
