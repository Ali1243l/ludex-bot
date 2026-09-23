"""
Admin Keyboards (Inline & Reply) for Digital Product Delivery Bot.
"""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)


def get_admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Primary persistent reply keyboard for administrators."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Create New Order"), KeyboardButton(text="📊 Sales & Analytics")],
            [KeyboardButton(text="📦 Orders Management"), KeyboardButton(text="🔐 Pending 2FA Requests")],
            [KeyboardButton(text="👤 Switch to User View")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Admin Control Panel"
    )


def get_product_type_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for product type selection."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Streaming / Account", callback_data="type:Streaming Account"),
                InlineKeyboardButton(text="🛡️ VPN / Proxy", callback_data="type:VPN Service")
            ],
            [
                InlineKeyboardButton(text="🔑 Software / Key", callback_data="type:License Key"),
                InlineKeyboardButton(text="☁️ Cloud / Hosting", callback_data="type:Cloud Account")
            ],
            [
                InlineKeyboardButton(text="📦 Custom Digital Good", callback_data="type:Custom Product"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="admin_order_cancel")
            ]
        ]
    )


def get_duration_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for subscription duration in days."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="30 Days (1 Mo)", callback_data="duration:30"),
                InlineKeyboardButton(text="90 Days (3 Mo)", callback_data="duration:90")
            ],
            [
                InlineKeyboardButton(text="180 Days (6 Mo)", callback_data="duration:180"),
                InlineKeyboardButton(text="365 Days (1 Yr)", callback_data="duration:365")
            ],
            [
                InlineKeyboardButton(text="♾️ Lifetime (No Expiry)", callback_data="duration:0"),
                InlineKeyboardButton(text="✍️ Custom Days", callback_data="duration:custom")
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="admin_order_cancel")
            ]
        ]
    )


def get_initial_status_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard to set initial order state."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡ Ready for Delivery", callback_data="status:ready"),
                InlineKeyboardButton(text="⏳ Pending (Preparing)", callback_data="status:pending")
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="admin_order_cancel")
            ]
        ]
    )


def get_skip_keyboard(step_name: str) -> InlineKeyboardMarkup:
    """Generic skip inline keyboard for optional fields."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Skip this step", callback_data=f"skip:{step_name}")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="admin_order_cancel")]
        ]
    )


def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Order confirmation and code generation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm & Generate Code", callback_data="order_confirm_submit"),
            ],
            [
                InlineKeyboardButton(text="❌ Cancel Order", callback_data="admin_order_cancel")
            ]
        ]
    )


def get_admin_2fa_action_keyboard(req_id: int, order_id: int) -> InlineKeyboardMarkup:
    """Interactive actions for admin when a user requests an OTP / 2FA code."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✉️ Reply with OTP Code", callback_data=f"otp_reply:{req_id}")
            ],
            [
                InlineKeyboardButton(text="🔍 Order Details", callback_data=f"admin_view_order:{order_id}"),
                InlineKeyboardButton(text="🚫 Dismiss", callback_data=f"otp_dismiss:{req_id}")
            ]
        ]
    )


def get_order_status_update_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Actions to change status of an order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡ Mark as Ready", callback_data=f"set_status:{order_id}:ready"),
                InlineKeyboardButton(text="⏳ Mark as Pending", callback_data=f"set_status:{order_id}:pending")
            ],
            [
                InlineKeyboardButton(text="🔙 Back", callback_data="admin_orders_back")
            ]
        ]
    )
