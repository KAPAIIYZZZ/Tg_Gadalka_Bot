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

# === Unsplash Collections для разнообразия ===
UNSPLASH_COLLECTIONS = [
    317099,   # Minimalism
    139386,   # Solitude
    365219,   # Mood
    1580860,  # Silence
    804697,   # Introspection
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

    # 🔒 Ограничение: все, кроме тебя
    if username != "evgeny_pashkin":
        if user_last_request.get(user_id) == today:
            await message.answer(
                "✨ Сегодня судьба уже сказала своё слово.\n"
                "Возвращайся за новым предсказанием завтра 🔮"
            )
            return
        user_last_request[user_id] = today

    # 🎲 Выбираем случайную коллекцию и страницу
    collection_id = random.choice(UNSPLASH_COLLECTIONS)
    page = random.randint(1, 10)  # можно увеличить диапазон для большего разнообразия
    per_page = 1  # берем 1 фото на страницу

    # === Запрос к Unsplash Collection Photos ===
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }

    params = {
        "page": page,
        "per_page": per_page
    }

    async with aiohttp.ClientSession() as session:
        url = f"https://api.unsplash.com/collections/{collection_id}/photos"
        async with session.get(url, headers=headers, params=params, timeout=10) as response:
            if response.status != 200:
                await message.answer("🔮 Судьба задумалась. Попробуй ещё раз позже.")
                return

            data = await response.json()
            if not data:
                await message.answer("🔮 Картинка не нашлась. Попробуй снова.")
                return

            image_url = data[0]["urls"]["regular"]

    await message.answer_photo(photo=image_url)

# === MAIN ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

