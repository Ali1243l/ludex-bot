"""
Digital Product Delivery Telegram Bot - Main Application Runner.
Built with aiogram 3.x and SQLAlchemy 2.0 Async.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database import init_db
from bot.handlers.admin import admin_router
from bot.handlers.user import user_router

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("delivery_bot")


async def set_bot_commands(bot: Bot) -> None:
    """Register standard commands in Telegram UI command menu."""
    commands = [
        BotCommand(command="start", description="Start bot & main menu"),
        BotCommand(command="claim", description="🎁 Claim order via tracking code"),
        BotCommand(command="profile", description="👤 View claimed products & subscriptions"),
        BotCommand(command="admin", description="🛠️ Admin management dashboard (Admins only)"),
        BotCommand(command="help", description="ℹ️ Help and customer support")
    ]
    await bot.set_my_commands(commands)


async def main() -> None:
    """Application startup, database migration, and polling loop."""
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ":
        logger.warning(
            "⚠️ BOT_TOKEN is empty or default placeholder! "
            "Please configure your real Telegram Bot token in .env before running the bot."
        )

    # Initialize async database tables
    logger.info("Initializing database schema...")
    await init_db()
    logger.info("Database initialized successfully.")

    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Include handler routers (Admin router registered first for priority)
    dp.include_router(admin_router)
    dp.include_router(user_router)

    # Set command hints
    try:
        await set_bot_commands(bot)
    except Exception as e:
        logger.warning(f"Failed to set bot commands: {e}")

    logger.info("Starting Telegram Bot long-polling...")
    logger.info(f"Configured Admins: {settings.ADMIN_IDS}")
    logger.info(f"Channel ID: {settings.CHANNEL_ID}")

    # Drop pending updates to prevent processing stale events on boot
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Telegram Bot stopped.")
