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

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🔮 Хочешь узнать, что приготовила судьба?\nНажми кнопку ниже.",
        reply_markup=keyboard
    )

@dp.message(lambda m: m.text == "🔮 Получить предсказание")
async def prediction(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username  # Получаем имя пользователя
    today = date.today()

    # 🔒 Проверка: уже получал сегодня, кроме моего аккаунта
    if username != "evgeny_pashkin":  # Бесконечные предсказания для меня
        if user_last_request.get(user_id) == today:
            await message.answer(
                "✨ Сегодня судьба уже сказала своё слово.\n"
                "Возвращайся за новым предсказанием завтра 🔮"
            )
            return
        user_last_request[user_id] = today

    # 🎲 Делаем URL уникальным, чтобы картинки были разные
    random_number = random.randint(1, 1_000_000)
    image_url = f"https://loremflickr.com/600/800/fortune?random={random_number}"

    await message.answer_photo(photo=image_url)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
