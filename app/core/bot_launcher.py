import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

# Настраиваем логирование один раз
logging.basicConfig(level=logging.INFO)

# Удаляем глобальное чтение .env и инициализацию bot/dp

async def run_bot():
    # 1. Загружаем переменные окружения (включая обновленные из .env)
    load_dotenv() 

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    WEB_APP_URL = os.getenv("WEB_APP_URL")

    if not BOT_TOKEN or not WEB_APP_URL:
        logging.error("BOT_TOKEN или WEB_APP_URL не найдены. Проверьте .env файл.")
        return

    # 2. Инициализируем бота и диспетчер внутри run_bot()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # 3. Определяем обработчики, используя WebAppInfo с актуальным URL
    @dp.message(CommandStart())
    async def send_welcome(message: types.Message):
        # Используем актуальный WEB_APP_URL
        web_app_button = InlineKeyboardButton(
            text="Открыть Web App",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
        markup = InlineKeyboardMarkup(inline_keyboard=[[web_app_button]])
        await message.answer(
            "Привет! Нажми кнопку ниже, чтобы открыть наше веб-приложение:",
            reply_markup=markup
        )

    # 4. Запускаем polling
    await dp.start_polling(bot)
