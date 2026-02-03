#!/usr/bin/env python3
import asyncio
import os
import random
import logging
from datetime import date
from typing import Optional, Dict, Any, Set, List

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv("gcgK3oxK7-RgzpU-99dnMOnz6vzrmujsbClaujuXK40")

if not TOKEN:
    logger.error("BOT_TOKEN не задан. Установи переменную окружения BOT_TOKEN.")
    raise SystemExit("BOT_TOKEN не задан")
if not UNSPLASH_ACCESS_KEY:
    logger.error("UNSPLASH_ACCESS_KEY не задан. Установи переменную окружения UNSPLASH_ACCESS_KEY.")
    raise SystemExit("UNSPLASH_ACCESS_KEY не задан")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# user_id -> дата последнего предсказания
user_last_request: Dict[int, date] = {}

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔮 Получить предсказание")]],
    resize_keyboard=True
)

# 🔮 Набор визуальных якорей
UNSPLASH_QUERIES: List[str] = [
    "fog",
    "shadow",
    "reflection",
    "empty room",
    "window light",
    "silhouette",
    "abandoned place",
    "lonely chair",
    "doorway",
    "stairs",
    "water surface",
    "forest path",
    "night light",
    "blurred motion",
    "quiet street",
    "dark room",
    "mirror",
    "corridor",
    # Добавим ещё немного вариантов, для разнообразия
    "misty forest",
    "old house",
    "vintage interior",
    "soft light",
    "lonely bench",
    "deserted pier",
]

# Чтобы не присылать один и тот же id в рамках одного запуска
recent_image_ids: Set[str] = set()
RECENT_CACHE_LIMIT = 200  # держать максимум N id в памяти

UNSPLASH_RANDOM_URL = "https://api.unsplash.com/photos/random"
UNSPLASH_HEADERS = {
    "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
}

# Хендлер /start
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🔮 Хочешь узнать, что приготовила судьба?\nНажми кнопку ниже.",
        reply_markup=keyboard
    )

# Функция запроса к Unsplash /photos/random
async def fetch_random_photo(session: aiohttp.ClientSession, query: str) -> Optional[Dict[str, Any]]:
    params = {
        "query": query,
        "orientation": "portrait",
        # можно добавить "content_filter": "high" если нужно более строгий контент
    }
    try:
        async with session.get(UNSPLASH_RANDOM_URL, headers=UNSPLASH_HEADERS, params=params, timeout=10) as resp:
            text = await resp.text()
            if resp.status == 200:
                # Unsplash возвращает объект (если count не указан) или список (если count>1)
                data = await resp.json()
                return data
            else:
                # логируем тело ответа для диагностики
                logger.warning("Unsplash returned status %s for query=%s: %s", resp.status, query, text[:1000])
                return {"__error_status": resp.status, "__error_text": text}
    except asyncio.TimeoutError:
        logger.exception("Timeout при запросе к Unsplash для query=%s", query)
        return None
    except Exception:
        logger.exception("Ошибка при запросе к Unsplash для query=%s", query)
        return None

# Хендлер кнопки "Получить предсказание"
@dp.message(lambda m: m.text == "🔮 Получить предсказание")
async def prediction(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    today = date.today()

    # 🔒 Ограничение: все, кроме тебя (как в оригинале)
    if username != "evgeny_pashkin":
        if user_last_request.get(user_id) == today:
            await message.answer(
                "✨ Сегодня судьба уже сказала своё слово.\n"
                "Возвращайся за новым предсказанием завтра 🔮"
            )
            return
        user_last_request[user_id] = today

    # Попробуем несколько разных запросов (shuffle) чтобы получить разнообразие
    queries = UNSPLASH_QUERIES.copy()
    random.shuffle(queries)

    async with aiohttp.ClientSession() as session:
        # Поправим логику: попробуем до N разных запросов, и для каждого — несколько попыток
        for query in queries[:8]:  # не пробуем все 100+ запросов — берем первые 8 случайных
            for attempt in range(3):
                data = await fetch_random_photo(session, query)
                # если None — ошибка сети/таймаут — попробуем снова
                if data is None:
                    continue

                # Проверка на явную ошибку статуса
                if isinstance(data, dict) and data.get("__error_status"):
                    status = data.get("__error_status")
                    # При 429 или 403 — возможно лимит; попробуем другой query
                    if status in (429, 403):
                        logger.warning("Unsplash rate-limited or forbidden (status=%s). Меняю запрос.", status)
                        break  # выход на другой query
                    # Для других статусов попробуем ещё раз
                    continue

                # Разный формат ответа: объект или список
                photo_obj = None
                if isinstance(data, list) and data:
                    photo_obj = data[0]
                elif isinstance(data, dict) and data.get("id"):
                    photo_obj = data
                else:
                    # Нечего — попробуем ещё
                    logger.debug("Пустой/неожиданный ответ от Unsplash для query=%s: %s", query, str(data)[:200])
                    continue

                # Уникальность: не отправляем тот же id, если уже был недавно
                photo_id = photo_obj.get("id")
                if photo_id and photo_id in recent_image_ids:
                    logger.info("Повторный id %s обнаружен, пропускаю", photo_id)
                    # попробуем получить другой рандом (повторно)
                    continue

                # Получаем URL изображения (fallback на разные варианты)
                urls = photo_obj.get("urls", {})
                image_url = urls.get("regular") or urls.get("full") or urls.get("small")
                if not image_url:
                    logger.warning("Нет URL в объекте фотографии для query=%s: %s", query, photo_obj.get("id"))
                    continue

                # Сохраняем id в кеш недавних чтобы избегать повторов
                if photo_id:
                    recent_image_ids.add(photo_id)
                    # Обрезаем кеш, если слишком большой
                    if len(recent_image_ids) > RECENT_CACHE_LIMIT:
                        # простая обрезка: создаём новый set из последних элементов
                        # Note: set не гарантирует порядок, но тут важно лишь поддерживать размер
                        while len(recent_image_ids) > RECENT_CACHE_LIMIT:
                            recent_image_ids.pop()

                # Собираем подпись (фото + автор + ссылка на Unsplash)
                author = None
                try:
                    user = photo_obj.get("user", {})
                    author = user.get("name")
                    profile_link = user.get("links", {}).get("html")
                except Exception:
                    profile_link = None

                caption_lines = []
                if author:
                    caption_lines.append(f"📷 {author}")
                    if profile_link:
                        caption_lines[-1] += f" — {profile_link}"
                caption_lines.append(f"Тема: {query}")

                caption = "\n".join(caption_lines)

                # Отправляем фото
                try:
                    await message.answer_photo(photo=image_url, caption=caption)
                    return
                except Exception:
                    logger.exception("Ошибка при отправке фото пользователю")
                    await message.answer("🔮 Не удалось отправить изображение, попробуй ещё раз.")
                    return

        # Если дошли сюда — не смогли получить валидное фото
        await message.answer("🔮 Судьба задумалась. Попробуй ещё раз чуть позже.")

async def main():
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
