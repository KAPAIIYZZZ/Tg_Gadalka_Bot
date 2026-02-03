import asyncio
import os
import random
from datetime import date

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# === ENV ===
TOKEN = os.getenv("BOT_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv("gcgK3oxK7-RgzpU-99dnMOnz6vzrmujsbClaujuXK40")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# user_id -> дата последнего предсказания
user_last_request = {}

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔮 Получить предсказание")]],
    resize_keyboard=True
)

# 🔮 Поисковые запросы для Unsplash (интерпретируемые)
UNSPLASH_QUERIES = [
    "fog",
    "lonely road",
    "reflection",
    "silence",
    "empty space",
    "light in darkness",
    "misty landscape",
    "abandoned place",
    "open door",
    "path",
    "calm water",
    "distant horizon",
    "night light",
    "minimal landscape",
    "soft shadows"
]

# === START ===
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🔮 Хочешь узнать, что приготовила судьба?\nНажми кнопку ниже.",
        reply_markup=keyboard
    )

# === PREDICTION ===
@dp.message(lambda m: m.text == "🔮 Получить предсказание")
async def prediction(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    today = date.today()

    # 🔒 Ограничение: 1 раз в день (кроме тебя)
    if username != "evgeny_pashkin":
        if user_last_request.get(user_id) == today:
            await message.answer(
                "✨ Сегодня судьба уже сказала своё слово.\n"
                "Возвращайся за новым предсказанием завтра 🔮"
            )
            return
        user_last_request[user_id] = today

    query = random.choice(UNSPLASH_QUERIES)

    # === Запрос к Unsplash ===
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }

    params = {
        "query": query,
        "orientation": "portrait"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.unsplash.com/photos/random",
            headers=headers,
            params=params,
            timeout=10
        ) as response:
            if response.status != 200:
                await message.answer("🔮 Судьба задумалась. Попробуй чуть позже.")
                return

            data = await response.json()
            image_url = data["urls"]["regular"]

    await message.answer_photo(photo=image_url)

# === MAIN ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
