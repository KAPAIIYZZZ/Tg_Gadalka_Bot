import asyncio
import os
import random
import logging
import sys
from datetime import date

import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
# Это поможет видеть реальные причины ошибок в логах Railway
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# === ENV & CONFIGURATION ===
# Получаем переменные и сразу чистим их от случайных пробелов
TOKEN = os.getenv("BOT_TOKEN", "").strip()
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()

# Проверка наличия ключей перед стартом
if not TOKEN:
    logger.critical("❌ ОШИБКА: Не задан BOT_TOKEN в переменных окружения!")
    sys.exit(1)
if not UNSPLASH_ACCESS_KEY:
    logger.critical("❌ ОШИБКА: Не задан UNSPLASH_ACCESS_KEY в переменных окружения!")
    sys.exit(1)

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# user_id -> дата последнего предсказания
user_last_request = {}

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔮 Получить предсказание")]],
    resize_keyboard=True,
    one_time_keyboard=False
)

# 🔮 Поисковые запросы для Unsplash
UNSPLASH_QUERIES = [
    "fog", "lonely road", "reflection", "silence", "empty space",
    "light in darkness", "misty landscape", "abandoned place",
    "open door", "path", "calm water", "distant horizon",
    "night light", "minimal landscape", "soft shadows",
    "forest path", "mountains mist", "stars night"
]

# === START HANDLER ===
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🔮 Хочешь узнать, что приготовила судьба?\nНажми кнопку ниже.",
        reply_markup=keyboard
    )

# === PREDICTION HANDLER ===
@dp.message(F.text == "🔮 Получить предсказание")
async def prediction(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    today = date.today()

    # 🔒 Ограничение: 1 раз в день (кроме админа)
    # Проверяем, есть ли username, чтобы избежать ошибок с None
    is_admin = (username and username.lower() == "evgeny_pashkin")

    if not is_admin:
        last_date = user_last_request.get(user_id)
        if last_date == today:
            await message.answer(
                "✨ Сегодня судьба уже сказала своё слово.\n"
                "Возвращайся за новым предсказанием завтра 🔮"
            )
            return
        user_last_request[user_id] = today

    # Выбираем случайный запрос
    query = random.choice(UNSPLASH_QUERIES)
    logger.info(f"User {user_id} requested prediction. Query: {query}")

    # === Запрос к Unsplash ===
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
        "Accept-Version": "v1"
    }

    params = {
        "query": query,
        "orientation": "portrait",
        "content_filter": "high" # Фильтр контента (безопасный поиск)
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                "https://api.unsplash.com/photos/random",
                headers=headers,
                params=params,
                timeout=10
            ) as response:
                
                # ЛОГИКА ОБРАБОТКИ ОШИБОК API
                if response.status == 401:
                    error_text = await response.text()
                    logger.error(f"❌ Unsplash 401 Unauthorized: {error_text}")
                    await message.answer("⚠️ Ошибка авторизации на сервере. Проверьте логи.")
                    return
                
                if response.status == 403:
                    logger.error("❌ Unsplash 403 Rate Limit Exceeded (лимит запросов исчерпан)")
                    await message.answer("🔮 Звезды сегодня устали (лимит запросов). Попробуй позже.")
                    return

                if response.status != 200:
                    logger.error(f"❌ Unsplash Error {response.status}: {await response.text()}")
                    await message.answer("🔮 Туман скрывает будущее. Попробуй еще раз.")
                    return

                # Успешный ответ
                data = await response.json()
                
                # Берем обычную ссылку, но если её нет — raw
                image_url = data.get("urls", {}).get("regular")
                
                if not image_url:
                    logger.error("❌ URL изображения не найден в ответе Unsplash")
                    await message.answer("🔮 Образ будущего неясен.")
                    return
                
                caption_text = f"✨ Твой знак: {query.replace(' ', '_')}"
                await message.answer_photo(photo=image_url, caption=caption_text)

        except Exception as e:
            logger.exception(f"❌ Critical Error in request: {e}")
            await message.answer("🔮 Связь с космосом прервана (ошибка сети).")

# === MAIN ENTRY POINT ===
async def main():
    # Удаляем вебхуки, если были, чтобы бот не тупил при старте
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
