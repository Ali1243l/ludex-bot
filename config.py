"""
Configuration Module for Digital Product Delivery Telegram Bot.
Loads environment variables, validates settings, and provides typed configuration.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load variables from .env if present
load_dotenv()


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    _admin_ids_raw: str = os.getenv("ADMIN_IDS", "")
    CHANNEL_ID: str = os.getenv("CHANNEL_ID", "")
    CHANNEL_URL: str = os.getenv("CHANNEL_URL", "https://t.me/")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///delivery_bot.db")
    CURRENCY_SYMBOL: str = os.getenv("CURRENCY_SYMBOL", "$")

    @property
    def ADMIN_IDS(self) -> List[int]:
        """Parse comma-separated admin IDs into a list of integers."""
        if not self._admin_ids_raw:
            return []
        ids = []
        for item in self._admin_ids_raw.split(","):
            cleaned = item.strip()
            if cleaned.isdigit():
                ids.append(int(cleaned))
        return ids

    def is_admin(self, user_id: int) -> bool:
        """Check if a specific Telegram user ID is an admin."""
        return user_id in self.ADMIN_IDS


settings = Settings()
