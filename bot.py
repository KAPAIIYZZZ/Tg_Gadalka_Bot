import asyncio
import os
import random
from datetime import date

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# user_id -> дата последнего предсказания
user_last_request = {}

keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔮 Получить предсказание")]],
    resize_keyboard=True
)

# 🔹 Список подсказок для предсказаний
IMAGE_PROMPTS = [
    "mystical abstract landscape, soft pastel colors, floating shapes, ethereal light, surreal",
    "foggy forest path disappearing into distance, dreamy atmosphere, mystical",
    "calm lake reflecting colorful sky, abstract reflections, serene, surreal",
    "winding mountain path with soft mist, ethereal lighting, mysterious",
    "open door in fog, symbolic, surreal, mysterious light",
    "long empty bridge disappearing into clouds, mystical atmosphere",
    "single tree in vast field under dramatic sky, dreamy, inspiring",
    "floating geometric shapes in soft pastel colors, abstract, mystical",
    "shimmering light patterns, cosmic, dreamy, surreal",
    "ancient staircase leading to unknown, soft mystical lighting, symbolic",
    "stormy sea with single glowing lantern, mysterious, surreal",
    "floating origami birds in pastel sky, ethereal, mystical",
    "glowing orbs above calm ocean, surreal, dreamy atmosphere",
    "soft abstract clouds with golden light, mystical, inspiring",
    "empty road leading to mountains under magical sky, dreamy, surreal",
    "crystal-like shapes floating in soft mist, abstract, mystical",
    "reflection of surreal sky in still water, ethereal, mysterious",
    "faint glowing paths through dense fog, mysterious, dreamy",
    "glowing tree in dark landscape, surreal, mystical",
    "floating islands with soft pastel lighting, abstract, ethereal",
    "mysterious cave opening with soft light, mystical, surreal",
    "winding river through enchanted forest, dreamy, magical atmosphere",
    "scattered lanterns floating in dark night, ethereal, surreal",
    "surreal desert landscape with pastel dunes, mysterious, abstract",
    "glowing geometric portal in dark forest, mystical, inspiring"
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
    username = message.from_user.username  # Для бесконечных предсказаний
    today = date.today()

    # 🔒 Ограничение для всех кроме моего аккаунта
    if username != "evgeny_pashkin":
        if user_last_request.get(user_id) == today:
            await message.answer(
                "✨ Сегодня судьба уже сказала своё слово.\n"
                "Возвращайся за новым предсказанием завтра 🔮"
            )
            return
        user_last_request[user_id] = today

    # 🎲 Выбираем случайную подсказку
    prompt = random.choice(IMAGE_PROMPTS)

    # 🔹 Формируем теги для URL (берем первые 2-3 ключевых слова)
    tags = ",".join([word.strip().replace(" ", "_") for word in prompt.split(",")[:3]])
    random_number = random.randint(1, 1_000_000)

    # 🔹 URL для картинки с тегами
    image_url = f"https://loremflickr.com/600/800/{tags}?random={random_number}"

    # ✨ Отправляем картинку с подписью
    await message.answer_photo(photo=image_url, caption="🔮 Твоя подсказка")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
