"""
Customer / User Keyboards (Inline & Reply) for Digital Product Delivery Bot.
"""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from config import settings


def get_user_main_keyboard() -> ReplyKeyboardMarkup:
    """Primary persistent reply keyboard for customers."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎁 Claim Order Code")],
            [KeyboardButton(text="👤 My Profile & Purchases"), KeyboardButton(text="ℹ️ Support & Help")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Claim code or view purchases..."
    )


def get_force_subscribe_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard enforcing channel subscription before bot access."""
    channel_url = settings.CHANNEL_URL or f"https://t.me/{settings.CHANNEL_ID.lstrip('@')}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Join Official Channel", url=channel_url)
            ],
            [
                InlineKeyboardButton(text="🔄 Verify Subscription", callback_data="check_subscription")
            ]
        ]
    )


def get_order_delivery_keyboard(order_id: int, is_pending: bool = False) -> InlineKeyboardMarkup:
    """Action buttons attached to order delivery message."""
    buttons = []
    if is_pending:
        buttons.append([
            InlineKeyboardButton(text="🔄 Check Preparation Status", callback_data=f"check_order_status:{order_id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="🔐 Request 2FA / OTP Code", callback_data=f"user_request_2fa:{order_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="📖 View Activation Guide", callback_data=f"user_view_guide:{order_id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_order_card_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Action buttons shown when viewing an order from purchase history."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔐 Request Login 2FA Code", callback_data=f"user_request_2fa:{order_id}")
            ],
            [
                InlineKeyboardButton(text="📖 Activation Instructions", callback_data=f"user_view_guide:{order_id}")
            ]
        ]
    )
