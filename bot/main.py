# bot/main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers import router

# Configure logging
logging.basicConfig(level=logging.INFO)


async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # Include routers
    dp.include_router(router)

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())