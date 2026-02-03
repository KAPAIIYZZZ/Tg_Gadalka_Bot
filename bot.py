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

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# === ENV & CONFIGURATION ===
TOKEN = os.getenv("BOT_TOKEN", "").strip()
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "").strip()

if not TOKEN:
    logger.critical("❌ ОШИБКА: Не задан BOT_TOKEN!")
    sys.exit(1)
if not UNSPLASH_ACCESS_KEY:
    logger.critical("❌ ОШИБКА: Не задан UNSPLASH_ACCESS_KEY!")
    sys.exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# user_id -> дата последнего предсказания
user_last_request = {}

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔮 Получить предсказание")]],
    resize_keyboard=True
)

# === СИСТЕМА АРХЕТИПОВ ===
ARCHETYPES = {
    "Путь и Выбор": [
        "crossroads", "misty bridge", "mountain path", "hidden door", "labyrinth"
    ],
    "Внутренний Свет": [
        "candle in dark", "sun rays forest", "lighthouse night", "starry sky", "prism glass"
    ],
    "Трансформация": [
        "butterfly cocoon", "thunderstorm lightning", "melting ice", "burning fire", "flying birds"
    ],
    "Созерцание": [
        "still lake reflection", "zen stones", "raindrops on glass", "old library", "desert dunes"
    ],
    "Ресурс и Сила": [
        "giant oak roots", "ocean waves crashing", "golden field sunset", "mountain peak", "wild horse"
    ]
}

# === START HANDLER ===
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🔮 Каждое изображение сегодня — это зеркало твоего завтра.\nНажми кнопку, чтобы получить знак.",
        reply_markup=keyboard
    )

# === PREDICTION HANDLER ===
@dp.message(F.text == "🔮 Получить предсказание")
async def prediction(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    today = date.today()

    # Ограничение (админ — безлимит)
    is_admin = (username and username.lower() == "evgeny_pashkin")
    if not is_admin:
        if user_last_request.get(user_id) == today:
            await message.answer("✨ Твой знак на сегодня уже получен. Приходи завтра.")
            return
        user_last_request[user_id] = today

    # Выбор архетипа и конкретного запроса
    archetype_name = random.choice(list(ARCHETYPES.keys()))
    query = random.choice(ARCHETYPES[archetype_name])
    
    logger.info(f"User {user_id} | Archetype: {archetype_name} | Query: {query}")

    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
        "Accept-Version": "v1"
    }
    params = {
        "query": query,
        "orientation": "portrait",
        "content_filter": "high"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                "https://api.unsplash.com/photos/random",
                headers=headers,
                params=params,
                timeout=15
            ) as response:
                
                if response.status != 200:
                    logger.error(f"Unsplash Error {response.status}")
                    await message.answer("🔮 Видение затуманено. Попробуй через минуту.")
                    return

                data = await response.json()
                image_url = data.get("urls", {}).get("regular")
                
                if image_url:
                    # Отправляем чистое фото
                    await message.answer_photo(photo=image_url)
                else:
                    await message.answer("🔮 Образ не может проявиться. Попробуй еще раз.")

        except Exception as e:
            logger.exception(f"Request failed: {e}")
            await message.answer("🔮 Связь с миром образов прервана.")

# === RUN ===
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Бот на системе архетипов запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
