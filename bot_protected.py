#!/usr/bin/env python3
# bot_protected.py
"""
Telegram bot: щоденні відео-уроки о 08:00 Europe/Warsaw (5 модулів).
Захист: protect_content + персональний водяний знак (ffmpeg drawtext).
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

MODULE_VIDEOS = [
    "BAACAgIAAxkBAAMzaQZvDpidHWrI0MUOTnnhxx4nWmoAAjR9AAJNHjhIW6XoVH8nChQ2BA",
    "BAACAgIAAxkBAAMpaQYXy_TQyyXaTOE_1mgjtEHHBiwAAoqFAAJNHjBI_VerQIrAM042BA",
    "BAACAgIAAxkBAAMqaQYXy-ZK6WuquXXaSzj2YqON98AAApKFAAJNHjBIE0NGhDaWD_Y2BA",
    "BAACAgIAAxkBAAMmaQYUhpsRFJwzusAWMBsDqck5KO8AAlCFAAJNHjBIJKUJ8OwYcio2BA",
    "BAACAgIAAxkBAAMoaQYXy6Ac3_yR3LIk_jl9uSIvH1wAAn6FAAJNHjBIUiXrOkZhwzw2BA",
]

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

ENABLE_WATERMARK = True
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

DRAWTEXT_TEMPLATE = (
    "fontfile={font}:text='{text}':fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5:"
    "boxborderw=5:x=10:y=H-th-10"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ----------------- КОРИСТУВАЧІ -----------------
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

users = load_users()

# ----------------- ВОДЯНИЙ ЗНАК -----------------
def create_watermarked_video(input_path: Path, user_tag: str) -> Path:
    if not Path(FONT_PATH).exists():
        raise FileNotFoundError(f"Шрифт не знайдено: {FONT_PATH}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    raw_text = f"{user_tag} • {timestamp}"
    safe_text = raw_text.replace(":", "\\:").replace("'", "\\'")
    drawtext = DRAWTEXT_TEMPLATE.format(font=FONT_PATH, text=safe_text)

    tmpf = tempfile.NamedTemporaryFile(prefix="wm_", suffix=".mp4", delete=False)
    out_path = Path(tmpf.name)
    tmpf.close()

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vf", f"drawtext={drawtext}",
        "-c:a", "copy",
        str(out_path),
    ]
    logger.info("Запускаю ffmpeg для %s -> %s", input_path, out_path)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        out_path.unlink(missing_ok=True)
        err = proc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"ffmpeg failed: {err}")
    return out_path

# ----------------- ВІДПРАВКА УРОКУ -----------------
async def send_lesson_to_user(chat_id: int):
    key = str(chat_id)
    if key not in users or not users[key].get("subscribed", False):
        return

    idx = users[key].get("module_idx", 0)
    if idx >= len(MODULE_VIDEOS):
        await bot.send_message(chat_id, "✅ Ви пройшли всі 5 модулів. Щоб почати спочатку — /start.")
        users[key]["subscribed"] = False
        save_users(users)
        return

    video_file = VIDEOS_DIR / MODULE_VIDEOS[idx]
    caption = MODULE_TEXTS[idx]

    if not video_file.exists():
        await bot.send_message(chat_id, f"⚠️ Відео для модуля {idx+1} відсутнє.")
        return

    send_path = video_file
    temp: Optional[Path] = None

    try:
        if ENABLE_WATERMARK:
            try:
                chat = await bot.get_chat(chat_id)
                user_tag = chat.username or f"id{chat_id}"
            except Exception:
                user_tag = f"id{chat_id}"

            try:
                send_path = create_watermarked_video(video_file, user_tag)
                temp = send_path
            except Exception:
                pass

        with open(send_path, "rb") as fp:
            await bot.send_video(
                chat_id=chat_id,
                video=fp,
                caption=caption,
                parse_mode="Markdown",
                protect_content=True,
            )

        users[key]["module_idx"] = idx + 1
        save_users(users)

    finally:
        if temp:
            temp.unlink(missing_ok=True)

# ----------------- ЩОДЕННА РОЗСИЛКА -----------------
async def daily_job():
    tasks = []
    for key, data in users.items():
        if data.get("subscribed", False):
            tasks.append(send_lesson_to_user(int(key)))
    if tasks:
        await asyncio.gather(*tasks)

# ----------------- ХЕНДЛЕРИ -----------------
@dp.message_handler(commands=["start", "subscribe"])
async def cmd_start(message: types.Message):
    key = str(message.chat.id)
    already = key in users and users[key].get("subscribed", False)
    if already:
        await message.answer("Ви вже підписані. /next — надіслати новий урок.")
        return
    users[key] = {"module_idx": users.get(key, {}).get("module_idx", 0), "subscribed": True}
    save_users(users)
    await message.answer(
        "Привіт 👋 Ти підписаний на щоденні відео-уроки.\n\n"
        "Команди:\n/next — отримати урок\n/status — прогрес\n/stop — відписатися"
    )

@dp.message_handler(commands=["stop", "unsubscribe"])
async def cmd_stop(message: types.Message):
    key = str(message.chat.id)
    if key in users:
        users[key]["subscribed"] = False
        save_users(users)
        await message.answer("Ви відписані.")
    else:
        await message.answer("Ви ще не підписані.")

@dp.message_handler(commands=["next"])
async def cmd_next(message: types.Message):
    key = str(message.chat.id)
    if key not in users:
        users[key] = {"module_idx": 0, "subscribed": False}
        save_users(users)
    await message.answer("Надсилаю...")
    await send_lesson_to_user(message.chat.id)

@dp.message_handler(commands=["status"])
async def cmd_status(message: types.Message):
    key = str(message.chat.id)
    if key not in users:
        await message.answer("Ви не підписані.")
        return
    idx = users[key].get("module_idx", 0)
    sub = users[key].get("subscribed", False)
    await message.answer(f"Прогрес: {idx}/{len(MODULE_VIDEOS)}\nПідписка: {'активна' if sub else 'вимкнена'}")

@dp.message_handler(commands=["help"])
async def cmd_help(message: types.Message):
    await message.answer("Команди: /start /next /status /stop /help")

# ----------------- ОТРИМАННЯ file_id -----------------
@dp.message_handler(content_types=['video'])
async def handle_video_file_id(message: types.Message):
    """Коли користувач надсилає відео — повернути file_id."""
    try:
        file_id = message.video.file_id
        file_unique_id = message.video.file_unique_id

        await message.reply(
            f"✅ Відео отримано!\n\n"
            f"🎥 *file_id:* `{file_id}`\n"
            f"🆔 *unique_id:* `{file_unique_id}`",
            parse_mode="Markdown"
        )
    except Exception:
        await message.reply("⚠️ Не вдалося отримати file_id.")

# ----------------- ГЛОБАЛЬНИЙ ERROR HANDLER -----------------
@dp.errors_handler()
async def global_error_handler(update, error):
    logger.exception("Global error: %s", error)
    return True

# ----------------- MAIN -----------------
def main():
    missing = [v for v in MODULE_VIDEOS if not (VIDEOS_DIR / v).exists()]
    if missing:
        logger.warning("Відсутні відео: %s", missing)

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    trigger = CronTrigger(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, timezone=TIMEZONE)
    scheduler.add_job(lambda: asyncio.create_task(daily_job()), trigger=trigger)
    scheduler.start()

    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    main()
