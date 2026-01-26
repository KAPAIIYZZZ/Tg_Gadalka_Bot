import asyncio
import os
from datetime import date

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Токен берётся из переменных окружения Railway
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Храним дату последнего запроса пользователя
user_last_request = {}

# Кнопка
keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔮 Получить предсказание")]],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Нажми кнопку ниже, чтобы получить предсказание",
        reply_markup=keyboard
    )

@dp.message(lambda m: m.text == "🔮 Получить предсказание")
async def prediction(message: types.Message):
    user_id = message.from_user.id
    today = date.today()

    # Проверка: уже получал сегодня?
    if user_last_request.get(user_id) == today:
        return

    user_last_request[user_id] = today

    # Рандомная картинка из интернета
    image_url = "https://loremflickr.com/600/800/fortune"

    await message.answer_photo(photo=image_url)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
