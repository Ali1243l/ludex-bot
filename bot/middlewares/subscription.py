"""
Channel Subscription Verification Middleware & Utility.
Verifies whether a Telegram user is a member of the required mandatory channel.
"""

import logging
from typing import Tuple
from aiogram import Bot
from config import settings

logger = logging.getLogger(__name__)


async def check_user_subscription(bot: Bot, user_id: int) -> Tuple[bool, str]:
    """
    Check if the user is subscribed to the mandatory channel.
    Returns:
        (is_subscribed: bool, reason: str)
    """
    channel_id = settings.CHANNEL_ID.strip()
    # If no channel is configured, pass by default (useful for local development)
    if not channel_id or channel_id in ("@", ""):
        return True, "No channel configured; bypass active."

    # Admins are exempt from force-subscription checks
    if settings.is_admin(user_id):
        return True, "Admin bypass."

    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        # Valid statuses: creator, administrator, member, restricted (if still in chat)
        if member.status in ("creator", "administrator", "member", "restricted"):
            return True, "Subscribed"
        return False, "Not subscribed"
    except Exception as e:
        logger.warning(f"Error checking subscription for user {user_id} in {channel_id}: {e}")
        # In case the bot is not yet added to the channel as admin or channel username is invalid,
        # fail gracefully so bot remains functional.
        return True, f"Subscription check failed with error: {e}"
