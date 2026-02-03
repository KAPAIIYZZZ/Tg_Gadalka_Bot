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

    # 🎲 Случайная коллекция
    collection_id = random.choice(UNSPLASH_COLLECTIONS)

    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }

    async with aiohttp.ClientSession() as session:
        # Шаг 1: получить количество фото в коллекции
        try:
            url_info = f"https://api.unsplash.com/collections/{collection_id}"
            async with session.get(url_info, headers=headers, timeout=10) as resp_info:
                if resp_info.status != 200:
                    await message.answer("🔮 Судьба задумалась. Попробуй позже.")
                    return
                info_data = await resp_info.json()
                total_photos = info_data.get("total_photos", 1)
                if total_photos == 0:
                    await message.answer("🔮 Картинка не нашлась. Попробуй снова.")
                    return
        except Exception as e:
            await message.answer("🔮 Судьба задумалась. Попробуй позже.")
            print("Error fetching collection info:", e)
            return

        # Шаг 2: выбрать безопасную случайную страницу
        per_page = 1
        max_page = max(1, total_photos // per_page)
        page = random.randint(1, max_page)

        # Шаг 3: запрос фото из коллекции
        try:
            url_photos = f"https://api.unsplash.com/collections/{collection_id}/photos"
            params = {"page": page, "per_page": per_page}
            async with session.get(url_photos, headers=headers, params=params, timeout=10) as resp_photos:
                if resp_photos.status != 200:
                    await message.answer("🔮 Судьба задумалась. Попробуй позже.")
                    return
                photos_data = await resp_photos.json()
                if not photos_data:
                    await message.answer("🔮 Картинка не нашлась. Попробуй снова.")
                    return
                image_url = photos_data[0]["urls"]["regular"]
        except Exception as e:
            await message.answer("🔮 Судьба задумалась. Попробуй позже.")
            print("Error fetching photo:", e)
            return

    # ✅ Отправка фото пользователю
    await message.answer_photo(photo=image_url)

# === MAIN ===
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
