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
    resize_keyboard=True,
    one_time_keyboard=False
)

# 🔮 Поисковые запросы
UNSPLASH_QUERIES = [
    "open door light",       # Символ новой возможности, которая уже перед тобой.
    "climbing hand",         # Усилие, преодоление, работа на результат.
    "holding hands",         # Поддержка, примирение или новое знакомство.
    "broken glass",          # Предупреждение о хрупкости или необходимости перемен.
    "compass forest",        # Нужно определиться с направлением, поиск пути.
    "blank paper pen",       # Время начать с чистого листа, написать свою историю.
    "flying bird solo",      # Свобода, выход за рамки, одиночное путешествие.
    "storm lightning",       # Грядут резкие перемены, эмоциональная разрядка.
    "burning candle",        # Вера, надежда или необходимость сфокусироваться на главном.
    "old key",               # Решение проблемы уже у тебя в руках, осталось найти замок.
    "mountain climber",      # Ты почти у цели, нельзя останавливаться.
    "clock sand",            # Время уходит, не откладывай важное на потом.
    "sprout through concrete", # Сила и рост вопреки тяжелым обстоятельствам.
    "dark tunnel light",     # Выход из сложной ситуации уже виден.
    "locked padlock",        # Пока путь закрыт, нужно поискать другой подход.
    "autumn leaf water",     # Время отпустить прошлое и плыть по течению.
    "starry sky night",      # Масштабные мечты, взгляд за горизонт рутины.
    "chess move",            # Нужно тщательно обдумать следующий шаг.
    "running person",        # Динамика, спешка или бегство от чего-то.
    "mirror reflection",     # Пора заглянуть внутрь себя, ответ внутри.
    "stepping stone river",  # Двигайся осторожно, шаг за шагом.
    "lighthouse beam",       # Впереди есть ориентир, ты не потеряешься.
    "closed book",           # Какой-то этап завершен, пора открывать новую главу.
    "sunrise city",          # Начало чего-то большого и энергичного.
    "foggy forest path"      # Неопределенность, в которой нужно доверять интуиции.
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
        "content_filter": "high"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                "https://api.unsplash.com/photos/random",
                headers=headers,
                params=params,
                timeout=10
            ) as response:
                
                if response.status != 200:
                    logger.error(f"❌ Unsplash Error {response.status}: {await response.text()}")
                    await message.answer("🔮 Туман скрывает будущее. Попробуй еще раз.")
                    return

                data = await response.json()
                image_url = data.get("urls", {}).get("regular")
                
                if not image_url:
                    await message.answer("🔮 Образ будущего неясен.")
                    return
                
                # ИСПРАВЛЕНИЕ: Убрали caption, отправляем только фото
                await message.answer_photo(photo=image_url)

        except Exception as e:
            logger.exception(f"❌ Critical Error: {e}")
            await message.answer("🔮 Связь с космосом прервана.")

# === MAIN ===
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Бот запущен (версия без подписей)!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
