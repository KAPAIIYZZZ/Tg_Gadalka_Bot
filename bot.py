import asyncio
import os
import random
from datetime import date

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# user_id -> дата последнего предсказания
user_last_request = {}

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔮 Получить предсказание")]],
    resize_keyboard=True
)

# 🔮 Набор визуальных якорей (ОЧЕНЬ ВАЖНО)
UNSPLASH_QUERIES = [
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
]

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🔮 Хочешь узнать, что приготовила судьба?\nНажми кнопку ниже.",
        reply_markup=keyboard
    )

@dp.message(lambda m: m.text == "🔮 Получить предсказание")
async def prediction(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    today = date.today()

    # 🔒 Ограничение: все, кроме тебя
    if username != "evgeny_pashkin":
        if user_last_request.get(user_id) == today:
            await message.answer(
                "✨ Сегодня судьба уже сказала своё слово.\n"
                "Возвращайся за новым предсказанием завтра 🔮"
            )
            return
        user_last_request[user_id] = today

    query = random.choice(UNSPLASH_QUERIES)
    page = random.randint(1, 10)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.unsplash.com/search/photos",
            headers={
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
            },
            params={
                "query": query,
                "orientation": "portrait",
                "per_page": 1,
                "page": page,
            }
        ) as response:
            data = await response.json()

            if not data.get("results"):
                await message.answer("🔮 Судьба задумалась. Попробуй ещё раз.")
                return

            image_url = data["results"][0]["urls"]["regular"]

    await message.answer_photo(photo=image_url)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
