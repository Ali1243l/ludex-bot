"""
Customer / User Handlers Module for Digital Product Delivery Bot.
Includes:
- Mandatory Channel Force Subscription Verification
- Claim Code Redemption & Validation
- Immediate Delivery or Pending Status Queueing
- Customer Dashboard, Purchase History & Subscription Duration Tracker
- 2FA / OTP Verification Request Dispatcher to Administrators
"""

import html
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext

from config import settings
from database import (
    get_or_create_user,
    get_order_by_code,
    get_order_by_id,
    claim_order_for_user,
    get_user_orders,
    create_2fa_request
)
from bot.states.user_states import ClaimOrderFSM
from bot.middlewares.subscription import check_user_subscription
from bot.keyboards.user_kb import (
    get_user_main_keyboard,
    get_force_subscribe_keyboard,
    get_order_delivery_keyboard,
    get_order_card_keyboard
)
from bot.keyboards.admin_kb import get_admin_2fa_action_keyboard

user_router = Router(name="user_router")


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

async def enforce_channel_subscription(message_or_call, bot: Bot, user_id: int) -> bool:
    """Check subscription and show join alert if not joined."""
    is_sub, _ = await check_user_subscription(bot, user_id)
    if is_sub:
        return True

    text = (
        "📢 <b>Channel Subscription Required</b>\n\n"
        "To access our automated delivery service, you must be a member of our official channel.\n"
        "Please join using the button below and tap <b>Verify Subscription</b>."
    )
    kb = get_force_subscribe_keyboard()

    if isinstance(message_or_call, Message):
        await message_or_call.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message_or_call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await message_or_call.answer("Please subscribe to continue", show_alert=True)
    return False


# ------------------------------------------------------------------------------
# /start & Subscription Verification
# ------------------------------------------------------------------------------

@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext, bot: Bot):
    """Handle /start command with optional deep-linked claim code."""
    await state.clear()
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    # Check force subscribe
    if not await enforce_channel_subscription(message, bot, message.from_user.id):
        return

    # Check for deep-link argument e.g. /start DLV-ABCD-1234
    args = command.args
    if args and args.strip():
        await process_claim_code_submission(message, args.strip(), bot)
        return

    welcome_text = (
        f"👋 Hello, <b>{html.escape(message.from_user.first_name)}</b>!\n\n"
        "Welcome to the <b>Digital Product Delivery Bot</b>.\n"
        "Here you can instantly claim your purchased accounts, view active subscriptions, "
        "and request 2FA login codes anytime.\n\n"
        "👇 Tap <b>🎁 Claim Order Code</b> below to retrieve your credentials."
    )
    await message.answer(welcome_text, reply_markup=get_user_main_keyboard(), parse_mode="HTML")


@user_router.callback_query(F.data == "check_subscription")
async def callback_verify_subscription(callback: CallbackQuery, bot: Bot):
    """Verify button tapped in the force subscribe dialog."""
    is_sub, _ = await check_user_subscription(bot, callback.from_user.id)
    if not is_sub:
        await callback.answer("❌ You haven't joined yet. Please join the channel first!", show_alert=True)
        return

    await callback.answer("✅ Subscription verified! Welcome!")
    await callback.message.delete()
    welcome_text = (
        f"✅ <b>Subscription Verified!</b>\n\n"
        "Thank you for joining our community. You now have full access to our automated delivery bot.\n"
        "Use the menu below to claim your product code."
    )
    await callback.message.answer(welcome_text, reply_markup=get_user_main_keyboard(), parse_mode="HTML")


# ------------------------------------------------------------------------------
# Claim Order Flow
# ------------------------------------------------------------------------------

@user_router.message(F.text == "🎁 Claim Order Code")
@user_router.message(Command("claim"))
async def start_claim_order(message: Message, state: FSMContext, bot: Bot):
    """Prompt user to submit their unique claim code."""
    if not await enforce_channel_subscription(message, bot, message.from_user.id):
        return

    await state.set_state(ClaimOrderFSM.waiting_for_claim_code)
    await message.answer(
        "🔑 <b>Claim Your Digital Product</b>\n\n"
        "Please send your unique claim code (e.g. <code>DLV-AB12-XY89</code>):",
        parse_mode="HTML"
    )


@user_router.message(ClaimOrderFSM.waiting_for_claim_code)
async def process_entered_claim_code(message: Message, state: FSMContext, bot: Bot):
    """Validate submitted claim code and deliver product or notify pending status."""
    code = message.text.strip()
    await state.clear()
    await process_claim_code_submission(message, code, bot)


async def process_claim_code_submission(message: Message, code: str, bot: Bot):
    """Core business logic for claiming a digital delivery code."""
    order = await get_order_by_code(code)
    if not order:
        await message.answer(
            "❌ <b>Invalid or Unrecognized Code</b>\n\n"
            f"The code <code>{html.escape(code.upper())}</code> was not found in our database.\n"
            "Please check for typos or contact support if you believe this is an error.",
            reply_markup=get_user_main_keyboard(),
            parse_mode="HTML"
        )
        return

    # Link order to current user
    order = await claim_order_for_user(
        order_id=order.id,
        user_id=message.from_user.id,
        username=message.from_user.username
    )

    # Scenario A: Order is still pending preparation by admin
    if order.status == "pending":
        pending_text = (
            "⏳ <b>Your Order is Being Prepared!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Product:</b> {html.escape(order.product_name)}\n"
            f"🔑 <b>Claim Code:</b> <code>{order.claim_code}</code>\n"
            f"⚡ <b>Status:</b> <i>PREPARING / PENDING</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Our team is currently setting up your account credentials. "
            "You do not need to do anything—<b>this bot will automatically notify you</b> "
            "here the moment your order is marked Ready!",
            get_order_delivery_keyboard(order.id, is_pending=True)
        )
        await message.answer(pending_text[0], reply_markup=pending_text[1], parse_mode="HTML")
        return

    # Scenario B: Order is Ready / Claimed -> Immediate Delivery!
    duration_info = ""
    if order.duration_days and order.duration_days > 0:
        exp_date_str = order.expiry_date.strftime('%Y-%m-%d') if order.expiry_date else "N/A"
        duration_info = f"⏱️ <b>Lifespan:</b> {order.duration_days} Days (Expires: <code>{exp_date_str}</code>)\n"

    guide_section = ""
    if order.activation_guide:
        guide_section = (
            "\n📖 <b>Activation & Setup Guide:</b>\n"
            f"{html.escape(order.activation_guide)}\n"
        )

    delivered_text = (
        "🎉 <b>Order Claimed Successfully!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Product:</b> <b>{html.escape(order.product_name)}</b>\n"
        f"🏷️ <b>Category:</b> {html.escape(order.product_type)}\n"
        f"🔑 <b>Claim Code:</b> <code>{order.claim_code}</code>\n"
        f"{duration_info}"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 <b>Your Account Credentials:</b>\n"
        f"<code>{html.escape(order.account_details)}</code>\n"
        "<i>(tap the code block above to copy credentials)</i>"
        f"{guide_section}"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Need a 2FA/OTP login code? Use the button below to request one directly from our admin team.</i>"
    )

    await message.answer(
        delivered_text,
        reply_markup=get_order_delivery_keyboard(order.id, is_pending=False),
        parse_mode="HTML"
    )


# ------------------------------------------------------------------------------
# Customer Dashboard & Purchase History
# ------------------------------------------------------------------------------

@user_router.message(F.text == "👤 My Profile & Purchases")
@user_router.message(Command("profile"))
async def show_customer_profile(message: Message, bot: Bot):
    """View customer stats, active subscriptions, and claimed orders."""
    if not await enforce_channel_subscription(message, bot, message.from_user.id):
        return

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    orders = await get_user_orders(message.from_user.id)

    total_spent = sum(o.selling_price for o in orders)
    active_subs = [o for o in orders if o.duration_days and (o.remaining_days or 0) > 0]

    header_text = (
        "👤 <b>Customer Dashboard</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.telegram_id}</code>\n"
        f"👤 <b>Name:</b> {html.escape(user.full_name or 'Customer')}\n"
        f"📅 <b>Member Since:</b> {user.joined_at.strftime('%b %d, %Y')}\n"
        f"🛍️ <b>Total Orders Claimed:</b> {len(orders)}\n"
        f"💰 <b>Total Spent:</b> {settings.CURRENCY_SYMBOL}{total_spent:,.2f}\n"
        f"⏳ <b>Active Subscriptions:</b> {len(active_subs)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    if not orders:
        header_text += "You have not claimed any orders yet. Click <b>🎁 Claim Order Code</b> to redeem your first product!"
        await message.answer(header_text, reply_markup=get_user_main_keyboard(), parse_mode="HTML")
        return

    header_text += "📦 <b>Your Claimed Products:</b>"
    await message.answer(header_text, parse_mode="HTML")

    # Send individual interactive cards for each order
    for o in orders[:5]:  # show up to 5 most recent
        remaining_str = ""
        if o.duration_days:
            rem = o.remaining_days or 0
            emoji = "🟢" if rem > 5 else "🟡" if rem > 0 else "🔴"
            remaining_str = f"\n⏱️ <b>Remaining Duration:</b> {emoji} {rem} day(s)"

        card_text = (
            f"📦 <b>{html.escape(o.product_name)}</b>\n"
            f"🔑 Code: <code>{o.claim_code}</code> | Status: <b>{o.status.upper()}</b>\n"
            f"🔐 <b>Credentials:</b> <code>{html.escape(o.account_details)}</code>"
            f"{remaining_str}"
        )
        await message.answer(card_text, reply_markup=get_order_card_keyboard(o.id), parse_mode="HTML")


# ------------------------------------------------------------------------------
# 2FA / OTP Login Code Request
# ------------------------------------------------------------------------------

@user_router.callback_query(F.data.startswith("user_request_2fa:"))
async def handle_user_request_2fa(callback: CallbackQuery, bot: Bot):
    """Handle customer request for 2FA / OTP verification code."""
    order_id = int(callback.data.split(":", 1)[1])
    order = await get_order_by_id(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    # Record 2FA request in DB
    req = await create_2fa_request(
        order_id=order.id,
        telegram_id=callback.from_user.id,
        customer_name=callback.from_user.full_name,
        product_name=order.product_name
    )

    # In-app confirmation to customer
    await callback.answer("Request sent to admin! Please wait.", show_alert=False)
    await callback.message.reply(
        "📡 <b>2FA Verification Code Requested!</b>\n\n"
        f"Your request for <b>{html.escape(order.product_name)}</b> has been dispatched to our administrators.\n"
        "When the admin sends the OTP code, it will appear here automatically.\n"
        "<i>Please remain on the login screen of your app.</i>",
        parse_mode="HTML"
    )

    # Notify all configured administrators
    admin_alert = (
        "🚨 <b>NEW 2FA / OTP CODE REQUEST</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Customer:</b> {html.escape(callback.from_user.full_name)} "
        f"(@{html.escape(callback.from_user.username or 'no_user')})\n"
        f"🆔 <b>Telegram ID:</b> <code>{callback.from_user.id}</code>\n"
        f"📦 <b>Product:</b> <b>{html.escape(order.product_name)}</b>\n"
        f"🔑 <b>Claim Code:</b> <code>{order.claim_code}</code>\n"
        f"🔐 <b>Account Details:</b> <code>{html.escape(order.account_details)}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Tap <b>Reply with OTP Code</b> to send the verification code directly to the customer:"
    )

    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_alert,
                reply_markup=get_admin_2fa_action_keyboard(req.id, order.id),
                parse_mode="HTML"
            )
        except Exception:
            pass


# ------------------------------------------------------------------------------
# Guide & Help Callbacks
# ------------------------------------------------------------------------------

@user_router.callback_query(F.data.startswith("user_view_guide:"))
async def handle_user_view_guide(callback: CallbackQuery):
    """Display setup and activation guide for an order."""
    order_id = int(callback.data.split(":", 1)[1])
    order = await get_order_by_id(order_id)
    if not order or not order.activation_guide:
        await callback.answer("No specific activation guide for this product.", show_alert=True)
        return

    text = (
        f"📖 <b>Activation Guide: {html.escape(order.product_name)}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{html.escape(order.activation_guide)}"
    )
    await callback.message.reply(text, parse_mode="HTML")
    await callback.answer()


@user_router.callback_query(F.data.startswith("check_order_status:"))
async def handle_check_order_status(callback: CallbackQuery):
    """User manually refreshes pending order status."""
    order_id = int(callback.data.split(":", 1)[1])
    order = await get_order_by_id(order_id)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    if order.status == "pending":
        await callback.answer("⏳ Still in preparation. We will notify you once ready!", show_alert=True)
    else:
        await callback.answer("⚡ Order is ready! Showing details...")
        # Show delivery details
        guide_section = f"\n\n📖 <b>Guide:</b>\n{order.activation_guide}" if order.activation_guide else ""
        text = (
            "🎉 <b>Your Order is Ready!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>{html.escape(order.product_name)}</b>\n"
            f"🔐 <b>Credentials:</b> <code>{html.escape(order.account_details)}</code>"
            f"{guide_section}"
        )
        await callback.message.edit_text(
            text,
            reply_markup=get_order_delivery_keyboard(order.id, is_pending=False),
            parse_mode="HTML"
        )


@user_router.message(F.text == "ℹ️ Support & Help")
async def show_support_info(message: Message):
    """Provide customer support and instructions."""
    text = (
        "ℹ️ <b>Customer Support & Help Center</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "• <b>How to claim an order?</b>\n"
        "Tap <i>🎁 Claim Order Code</i> and enter the code given by the seller.\n\n"
        "• <b>How does 2FA/OTP login work?</b>\n"
        "When signing into your delivered account, tap <i>🔐 Request 2FA / OTP Code</i>. "
        "The verification code will be forwarded here in real time.\n\n"
        "• <b>Account issues or warranty claims?</b>\n"
        "Contact our support team directly via our official channel."
    )
    await message.answer(text, parse_mode="HTML")
