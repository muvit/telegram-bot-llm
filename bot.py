import os, asyncio
from collections import defaultdict
from dotenv import load_dotenv
import httpx
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
from openai import AsyncOpenAI

load_dotenv()

# Настройка прокси (для Telegram и нейросети)
proxy = os.getenv("PROXY_URL")
session = AiohttpSession(proxy=proxy) if proxy else None
http_client = httpx.AsyncClient(proxy=proxy) if proxy else None

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"), session=session)
dp = Dispatcher()

llm = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    http_client=http_client
)
model = os.getenv("MODEL_NAME", "google/gemini-2.0-flash-exp:free")

# Контекст диалога (память)
history = defaultdict(list)

@dp.message(Command("start", "help"))
async def start_handler(msg: types.Message):
    history[msg.from_user.id].clear()
    await msg.answer("Привет! Я AI-бот с памятью диалога. Напиши мне любой вопрос.")

@dp.message(F.text)
async def text_handler(msg: types.Message):
    user_id = msg.from_user.id
    history[user_id].append({"role": "user", "content": msg.text})
    history[user_id] = history[user_id][-6:]

    res = await llm.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": "Отвечай кратко и по делу."}] + history[user_id]
    )
    answer = res.choices[0].message.content
    history[user_id].append({"role": "assistant", "content": answer})
    await msg.answer(answer)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())