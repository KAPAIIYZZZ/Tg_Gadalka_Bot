import asyncio
import os
import random
from datetime import date

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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

# 🔮 Набор визуальных якорей (ОЧЕНЬ ВАЖНО)
# Запросы специально подобраны для таинственной атмосферы
UNSPLASH_QUERIES = [
    "fog mist mysterious",
    "shadow dark mood",
    "reflection mirror water",
    "empty abandoned room",
    "window light sunrise",
    "silhouette person",
    "abandoned house ruins",
    "lonely chair interior",
    "doorway passage entrance",
    "spiral stairs",
    "water surface calm",
    "forest path trees",
    "night light stars",
    "motion blur speed",
    "quiet street night",
    "dark room interior",
    "mirror reflection",
    "corridor hallway",
    "mystery atmosphere",
    "dream surreal",
]

async def get_unsplash_photo(query: str, max_retries: int = 3) -> str | None:
    """
    Получает фото с Unsplash по запросу.
    Использует несколько попыток с разными параметрами.
    
    Args:
        query: Поисковый запрос
        max_retries: Максимум попыток поиска
    
    Returns:
        URL фото или None если не найдено
    """
    for attempt in range(max_retries):
        try:
            # Варьируем параметры при повторных попытках
            page = random.randint(1, 50)
            per_page = random.randint(10, 30)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.unsplash.com/search/photos",
                    headers={
                        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
                    },
                    params={
                        "query": query,
                        "per_page": per_page,
                        "page": page,
                        "order_by": "relevant",  # Сортируем по релевантности
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    # Проверяем статус ответа
                    if response.status != 200:
                        print(f"Unsplash API error: {response.status}")
                        continue
                    
                    data = await response.json()
                    
                    # Проверяем наличие результатов
                    if not data.get("results") or len(data["results"]) == 0:
                        print(f"No results for query: {query}")
                        continue
                    
                    # Берём случайное фото из списка (не первое)
                    # Это избегает проблем с попадающимися в начале неподходящими фото
                    random_index = random.randint(0, len(data["results"]) - 1)
                    image_url = data["results"][random_index]["urls"]["regular"]
                    
                    if image_url:
                        print(f"✓ Got photo for query '{query}'")
                        return image_url
                        
        except asyncio.TimeoutError:
            print(f"Timeout on attempt {attempt + 1}")
            continue
        except aiohttp.ClientError as e:
            print(f"Network error on attempt {attempt + 1}: {e}")
            continue
        except (KeyError, IndexError) as e:
            print(f"Data parsing error on attempt {attempt + 1}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error on attempt {attempt + 1}: {e}")
            continue
    
    return None


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

    # Выбираем случайный запрос
    query = random.choice(UNSPLASH_QUERIES)
    
    # Пытаемся получить фото (максимум 3 попытки)
    image_url = await get_unsplash_photo(query, max_retries=3)
    
    if not image_url:
        await message.answer(
            "🔮 Судьба задумалась. Попробуй ещё раз."
        )
        return
    
    try:
        await message.answer_photo(photo=image_url)
    except Exception as e:
        print(f"Error sending photo: {e}")
        await message.answer(
            "🔮 Не удалось отправить изображение. Попробуй ещё раз."
        )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
