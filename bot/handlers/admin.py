"""
Admin Handlers Module for Digital Product Delivery Bot.
Includes:
- Step-by-step Order Creation FSM
- Automatic Claim Code Generation
- Financial Sales & Analytics Dashboard
- 2FA / OTP Request Answering Workflow
- Order Status Management
"""

import html
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import settings
from database import (
    create_order,
    get_admin_stats,
    get_order_by_id,
    get_order_by_code,
    update_order_status,
    get_2fa_request,
    answer_2fa_request,
    AsyncSessionLocal,
    Order
)
from sqlalchemy import select, desc
from bot.states.admin_states import OrderCreationFSM, Answer2FAFSM
from bot.keyboards.admin_kb import (
    get_admin_main_keyboard,
    get_product_type_keyboard,
    get_duration_keyboard,
    get_initial_status_keyboard,
    get_skip_keyboard,
    get_order_confirmation_keyboard,
    get_admin_2fa_action_keyboard,
    get_order_status_update_keyboard
)
from bot.keyboards.user_kb import get_user_main_keyboard

admin_router = Router(name="admin_router")


def is_admin_filter(user_id: int) -> bool:
    """Check if the requesting user is in the configured ADMIN_IDS."""
    return settings.is_admin(user_id)


# ------------------------------------------------------------------------------
# Navigation & Entry Points
# ------------------------------------------------------------------------------

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Admin entry point and control dashboard."""
    if not is_admin_filter(message.from_user.id):
        await message.answer("⛔ Access denied. You do not have administrator permissions.")
        return

    await state.clear()
    await message.answer(
        "🛠️ <b>Admin Control Panel</b>\n\n"
        "Welcome to the Digital Product Delivery management suite. "
        "Use the options below to generate claim codes, view revenue metrics, "
        "or reply to customer 2FA requests.",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )


@admin_router.message(F.text == "👤 Switch to User View")
async def switch_to_user_view(message: Message, state: FSMContext):
    """Allow admin to view and test the bot from a customer perspective."""
    if not is_admin_filter(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "🔄 <b>Switched to Customer View</b>\n"
        "You can now test customer features (claiming codes, viewing orders). "
        "Type /admin at any time to return.",
        reply_markup=get_user_main_keyboard(),
        parse_mode="HTML"
    )


# ------------------------------------------------------------------------------
# Sales Dashboard & Analytics
# ------------------------------------------------------------------------------

@admin_router.message(F.text == "📊 Sales & Analytics")
async def show_sales_dashboard(message: Message):
    """Display comprehensive financial metrics and order inventory."""
    if not is_admin_filter(message.from_user.id):
        return

    stats = await get_admin_stats()
    currency = settings.CURRENCY_SYMBOL
    margin = 0.0
    if stats["total_sales"] > 0:
        margin = round((stats["net_profit"] / stats["total_sales"]) * 100, 1)

    text = (
        "📈 <b>Business Performance & Sales Analytics</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Total Gross Sales:</b> {currency}{stats['total_sales']:,.2f}\n"
        f"📉 <b>Total Product Costs:</b> {currency}{stats['total_cost']:,.2f}\n"
        f"💵 <b>Net Realized Profit:</b> <b>{currency}{stats['net_profit']:,.2f}</b> ({margin}% margin)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Total Orders:</b> {stats['total_orders']}\n"
        f"⚡ <b>Ready (Unclaimed):</b> {stats['ready_orders']}\n"
        f"⏳ <b>Pending (Preparing):</b> {stats['pending_orders']}\n"
        f"✅ <b>Claimed by Customers:</b> {stats['claimed_orders']}\n"
        f"👥 <b>Registered Users:</b> {stats['total_users']}\n"
        f"🔐 <b>Open 2FA Requests:</b> {stats['pending_2fa']}\n"
    )
    await message.answer(text, parse_mode="HTML")


# ------------------------------------------------------------------------------
# Orders Overview
# ------------------------------------------------------------------------------

@admin_router.message(F.text == "📦 Orders Management")
async def show_orders_management(message: Message):
    """Show the 10 most recent orders with their claim codes and statuses."""
    if not is_admin_filter(message.from_user.id):
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order).order_by(desc(Order.created_at)).limit(10)
        )
        orders = result.scalars().all()

    if not orders:
        await message.answer("📦 No orders created yet. Tap <b>➕ Create New Order</b> to add one.", parse_mode="HTML")
        return

    text = "📦 <b>Recent Orders (Last 10)</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for o in orders:
        status_emoji = "⚡" if o.status == "ready" else "⏳" if o.status == "pending" else "✅"
        user_tag = f"@{o.customer_username}" if o.customer_username else o.customer_name
        text += (
            f"{status_emoji} <b>Code:</b> <code>{o.claim_code}</code>\n"
            f"   • Product: {html.escape(o.product_name)} ({o.product_type})\n"
            f"   • Customer: {html.escape(user_tag)} | Price: {settings.CURRENCY_SYMBOL}{o.selling_price:.2f}\n"
            f"   • Status: <i>{o.status.upper()}</i>\n\n"
        )

    text += "💡 <i>To inspect or change an order status, type its code or use /order &lt;code&gt;</i>"
    await message.answer(text, parse_mode="HTML")


# ------------------------------------------------------------------------------
# Step-by-Step Order Creation FSM
# ------------------------------------------------------------------------------

@admin_router.message(F.text == "➕ Create New Order")
async def start_order_creation(message: Message, state: FSMContext):
    """Initiate step 1 of order creation wizard."""
    if not is_admin_filter(message.from_user.id):
        return

    await state.clear()
    await state.set_state(OrderCreationFSM.waiting_for_customer_name)
    await message.answer(
        "📝 <b>Step 1 of 8: Customer Name</b>\n\n"
        "Please send the full name or display name of the customer:",
        reply_markup=get_skip_keyboard("customer_name"),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "admin_order_cancel")
async def cancel_order_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel order creation at any step."""
    await state.clear()
    await callback.message.edit_text("❌ Order creation cancelled.")
    await callback.answer("Cancelled")


# Step 1 -> Step 2
@admin_router.message(OrderCreationFSM.waiting_for_customer_name)
async def process_customer_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("⚠️ Customer name must be at least 2 characters long. Please re-enter:")
        return

    await state.update_data(customer_name=name)
    await state.set_state(OrderCreationFSM.waiting_for_customer_username)
    await message.answer(
        f"👤 Customer: <b>{html.escape(name)}</b>\n\n"
        "📝 <b>Step 2 of 8: Telegram Username</b>\n"
        "Enter customer's @username (optional, without or with @), or skip:",
        reply_markup=get_skip_keyboard("username"),
        parse_mode="HTML"
    )


@admin_router.callback_query(OrderCreationFSM.waiting_for_customer_username, F.data == "skip:username")
async def skip_customer_username(callback: CallbackQuery, state: FSMContext):
    await state.update_data(customer_username=None)
    await state.set_state(OrderCreationFSM.waiting_for_product_name)
    await callback.message.edit_text(
        "📝 <b>Step 3 of 8: Product Name</b>\n\n"
        "Enter the product name (e.g. <code>Netflix Premium 4K UHD 1 Month</code>):",
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(OrderCreationFSM.waiting_for_customer_username)
async def process_customer_username(message: Message, state: FSMContext):
    username = message.text.strip().lstrip("@")
    await state.update_data(customer_username=username)
    await state.set_state(OrderCreationFSM.waiting_for_product_name)
    await message.answer(
        f"👤 Username: <b>@{html.escape(username)}</b>\n\n"
        "📝 <b>Step 3 of 8: Product Name</b>\n"
        "Enter the product name (e.g. <code>Netflix Premium 4K UHD 1 Month</code>):",
        parse_mode="HTML"
    )


# Step 3 -> Step 4
@admin_router.message(OrderCreationFSM.waiting_for_product_name)
async def process_product_name(message: Message, state: FSMContext):
    p_name = message.text.strip()
    if len(p_name) < 2:
        await message.answer("⚠️ Product name cannot be empty. Please enter a valid name:")
        return

    await state.update_data(product_name=p_name)
    await state.set_state(OrderCreationFSM.waiting_for_product_type)
    await message.answer(
        f"📦 Product: <b>{html.escape(p_name)}</b>\n\n"
        "📝 <b>Step 4 of 8: Product Type</b>\n"
        "Select a product category below or type a custom category:",
        reply_markup=get_product_type_keyboard(),
        parse_mode="HTML"
    )


@admin_router.callback_query(OrderCreationFSM.waiting_for_product_type, F.data.startswith("type:"))
async def process_product_type_button(callback: CallbackQuery, state: FSMContext):
    p_type = callback.data.split(":", 1)[1]
    await state.update_data(product_type=p_type)
    await state.set_state(OrderCreationFSM.waiting_for_cost_price)
    await callback.message.edit_text(
        f"🏷️ Category: <b>{html.escape(p_type)}</b>\n\n"
        f"📝 <b>Step 5 of 8: Cost Price ({settings.CURRENCY_SYMBOL})</b>\n"
        "How much did this item cost you to acquire/produce? (Enter a number, e.g. <code>2.50</code> or <code>0</code>):",
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(OrderCreationFSM.waiting_for_product_type)
async def process_product_type_text(message: Message, state: FSMContext):
    p_type = message.text.strip()
    await state.update_data(product_type=p_type)
    await state.set_state(OrderCreationFSM.waiting_for_cost_price)
    await message.answer(
        f"🏷️ Category: <b>{html.escape(p_type)}</b>\n\n"
        f"📝 <b>Step 5 of 8: Cost Price ({settings.CURRENCY_SYMBOL})</b>\n"
        "How much did this item cost you? (Enter a number, e.g. <code>2.50</code> or <code>0</code>):",
        parse_mode="HTML"
    )


# Step 5 -> Step 6
@admin_router.message(OrderCreationFSM.waiting_for_cost_price)
async def process_cost_price(message: Message, state: FSMContext):
    text = message.text.strip().replace("$", "").replace("€", "")
    try:
        cost = float(text)
        if cost < 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Invalid amount. Please enter a valid number (e.g. <code>4.50</code>):", parse_mode="HTML")
        return

    await state.update_data(cost_price=cost)
    await state.set_state(OrderCreationFSM.waiting_for_selling_price)
    await message.answer(
        f"📉 Cost: <b>{settings.CURRENCY_SYMBOL}{cost:.2f}</b>\n\n"
        f"📝 <b>Step 6 of 8: Selling Price ({settings.CURRENCY_SYMBOL})</b>\n"
        "How much is the customer paying? (e.g. <code>9.99</code>):",
        parse_mode="HTML"
    )


# Step 6 -> Duration / Expiry
@admin_router.message(OrderCreationFSM.waiting_for_selling_price)
async def process_selling_price(message: Message, state: FSMContext):
    text = message.text.strip().replace("$", "").replace("€", "")
    try:
        price = float(text)
        if price < 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Invalid amount. Please enter a valid number (e.g. <code>12.00</code>):", parse_mode="HTML")
        return

    await state.update_data(selling_price=price)
    await state.set_state(OrderCreationFSM.waiting_for_duration_days)
    await message.answer(
        f"💰 Selling Price: <b>{settings.CURRENCY_SYMBOL}{price:.2f}</b>\n\n"
        "⏱️ <b>Subscription / Account Duration</b>\n"
        "Select account lifespan for automatic expiry tracking, or choose Lifetime:",
        reply_markup=get_duration_keyboard(),
        parse_mode="HTML"
    )


@admin_router.callback_query(OrderCreationFSM.waiting_for_duration_days, F.data.startswith("duration:"))
async def process_duration_callback(callback: CallbackQuery, state: FSMContext):
    dur_str = callback.data.split(":", 1)[1]
    if dur_str == "custom":
        await callback.message.edit_text("⏱️ Send the duration in days as a number (e.g. <code>45</code>):", parse_mode="HTML")
        await callback.answer()
        return

    duration = int(dur_str)
    await state.update_data(duration_days=duration if duration > 0 else None)
    await state.set_state(OrderCreationFSM.waiting_for_account_details)
    await callback.message.edit_text(
        "📝 <b>Step 7 of 8: Account Credentials / Product Details</b>\n\n"
        "Send the actual credentials or digital product content.\n"
        "<i>Example:</i>\n"
        "<code>email:pass@domain.com\nPIN: 1234\nProfile: 3</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(OrderCreationFSM.waiting_for_duration_days)
async def process_custom_duration(message: Message, state: FSMContext):
    try:
        days = int(message.text.strip())
        if days < 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Please enter a positive integer of days (e.g. <code>30</code>):", parse_mode="HTML")
        return

    await state.update_data(duration_days=days if days > 0 else None)
    await state.set_state(OrderCreationFSM.waiting_for_account_details)
    await message.answer(
        "📝 <b>Step 7 of 8: Account Credentials / Product Details</b>\n\n"
        "Send the actual credentials or digital product content.\n"
        "<i>Example:</i>\n"
        "<code>email:pass@domain.com\nPIN: 1234\nProfile: 3</code>",
        parse_mode="HTML"
    )


# Step 7 -> Step 8 (Guide)
@admin_router.message(OrderCreationFSM.waiting_for_account_details)
async def process_account_details(message: Message, state: FSMContext):
    details = message.text.strip()
    if not details:
        await message.answer("⚠️ Credentials cannot be empty. Please send the account details:")
        return

    await state.update_data(account_details=details)
    await state.set_state(OrderCreationFSM.waiting_for_activation_guide)
    await message.answer(
        "📝 <b>Step 8 of 8: Activation Guide / Setup Instructions</b>\n\n"
        "Enter any step-by-step setup instructions for the customer (or tap skip):",
        reply_markup=get_skip_keyboard("guide"),
        parse_mode="HTML"
    )


@admin_router.callback_query(OrderCreationFSM.waiting_for_activation_guide, F.data == "skip:guide")
async def skip_activation_guide(callback: CallbackQuery, state: FSMContext):
    await state.update_data(activation_guide=None)
    await state.set_state(OrderCreationFSM.waiting_for_initial_status)
    await callback.message.edit_text(
        "⚡ <b>Initial Order Readiness</b>\n\n"
        "Is this order ready for immediate delivery upon claiming, or is it pending preparation?",
        reply_markup=get_initial_status_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(OrderCreationFSM.waiting_for_activation_guide)
async def process_activation_guide(message: Message, state: FSMContext):
    guide = message.text.strip()
    await state.update_data(activation_guide=guide)
    await state.set_state(OrderCreationFSM.waiting_for_initial_status)
    await message.answer(
        "⚡ <b>Initial Order Readiness</b>\n\n"
        "Is this order ready for immediate delivery upon claiming, or is it pending preparation?",
        reply_markup=get_initial_status_keyboard(),
        parse_mode="HTML"
    )


# Initial Status -> Confirmation
@admin_router.callback_query(OrderCreationFSM.waiting_for_initial_status, F.data.startswith("status:"))
async def process_initial_status(callback: CallbackQuery, state: FSMContext):
    status = callback.data.split(":", 1)[1]
    await state.update_data(status=status)
    data = await state.get_data()

    profit = round(data["selling_price"] - data["cost_price"], 2)
    duration_str = f"{data['duration_days']} Days" if data.get("duration_days") else "Lifetime / No Expiry"
    guide_str = "Configured" if data.get("activation_guide") else "None"
    username_str = f"@{data['customer_username']}" if data.get("customer_username") else "None"

    preview = (
        "🔍 <b>Review Order Summary Before Creation</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Customer:</b> {html.escape(data['customer_name'])} ({username_str})\n"
        f"📦 <b>Product:</b> {html.escape(data['product_name'])}\n"
        f"🏷️ <b>Category:</b> {html.escape(data['product_type'])}\n"
        f"⏱️ <b>Duration:</b> {duration_str}\n"
        f"💵 <b>Selling Price:</b> {settings.CURRENCY_SYMBOL}{data['selling_price']:.2f}\n"
        f"📉 <b>Cost Price:</b> {settings.CURRENCY_SYMBOL}{data['cost_price']:.2f}\n"
        f"💰 <b>Estimated Profit:</b> <b>{settings.CURRENCY_SYMBOL}{profit:.2f}</b>\n"
        f"⚡ <b>Status:</b> {status.upper()}\n"
        f"📖 <b>Guide:</b> {guide_str}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 <b>Credentials:</b>\n"
        f"<code>{html.escape(data['account_details'])}</code>\n\n"
        "Click below to finalize and generate the customer's unique claim code:"
    )

    await state.set_state(OrderCreationFSM.confirm_order)
    await callback.message.edit_text(preview, reply_markup=get_order_confirmation_keyboard(), parse_mode="HTML")
    await callback.answer()


# Final Confirmation -> Code Generation
@admin_router.callback_query(OrderCreationFSM.confirm_order, F.data == "order_confirm_submit")
async def finalize_order_creation(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Save order to database and output generated unique tracking code."""
    data = await state.get_data()
    await state.clear()

    order = await create_order(
        customer_name=data["customer_name"],
        customer_username=data.get("customer_username"),
        product_name=data["product_name"],
        product_type=data["product_type"],
        cost_price=data["cost_price"],
        selling_price=data["selling_price"],
        account_details=data["account_details"],
        activation_guide=data.get("activation_guide"),
        status=data["status"],
        duration_days=data.get("duration_days")
    )

    customer_tag = f"@{order.customer_username}" if order.customer_username else order.customer_name

    success_msg = (
        "✅ <b>Order Created & Code Generated!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 <b>Claim Code:</b> <code>{order.claim_code}</code> <i>(tap to copy)</i>\n"
        f"📦 <b>Product:</b> {html.escape(order.product_name)}\n"
        f"👤 <b>Customer:</b> {html.escape(customer_tag)}\n"
        f"💰 <b>Amount:</b> {settings.CURRENCY_SYMBOL}{order.selling_price:.2f}\n"
        f"⚡ <b>Status:</b> {order.status.upper()}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📋 <b>Customer Delivery Template (Copy & Send to Customer):</b>\n"
        "<blockquote>"
        f"Hello {html.escape(order.customer_name)}!\n"
        f"Your order for <b>{html.escape(order.product_name)}</b> is ready.\n\n"
        f"Claim your account in our automated delivery bot using this code:\n"
        f"<code>{order.claim_code}</code>\n\n"
        "Start the bot and press '🎁 Claim Order Code'."
        "</blockquote>"
    )

    await callback.message.edit_text(success_msg, parse_mode="HTML")
    await callback.answer("Order successfully created!")


# ------------------------------------------------------------------------------
# 2FA / OTP Fulfillment Workflow
# ------------------------------------------------------------------------------

@admin_router.callback_query(F.data.startswith("otp_reply:"))
async def handle_otp_reply_button(callback: CallbackQuery, state: FSMContext):
    """Admin clicked 'Reply with OTP Code' on an incoming 2FA request."""
    if not is_admin_filter(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return

    req_id = int(callback.data.split(":", 1)[1])
    req = await get_2fa_request(req_id)
    if not req or req.status != "pending":
        await callback.answer("This request has already been answered or dismissed.", show_alert=True)
        return

    await state.set_state(Answer2FAFSM.waiting_for_otp_code)
    await state.update_data(two_fa_req_id=req_id, customer_tg_id=req.telegram_id, product_name=req.product_name)

    await callback.message.reply(
        f"✉️ <b>Enter OTP / 2FA Code for {html.escape(req.customer_name or 'User')}</b>\n"
        f"Product: <b>{html.escape(req.product_name or 'Account')}</b>\n\n"
        "Send the 6-digit or verification code as a message right now:",
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(Answer2FAFSM.waiting_for_otp_code)
async def process_otp_code_reply(message: Message, state: FSMContext, bot: Bot):
    """Deliver admin's OTP code directly to the customer."""
    data = await state.get_data()
    req_id = data["two_fa_req_id"]
    customer_id = data["customer_tg_id"]
    product_name = data.get("product_name", "Account")
    code = message.text.strip()

    await state.clear()

    # Update database record
    await answer_2fa_request(req_id, code)

    # Forward code directly to customer
    try:
        customer_msg = (
            "🔐 <b>2FA / OTP Login Code Received!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Product:</b> {html.escape(product_name)}\n"
            f"🔑 <b>Verification Code:</b> <code>{html.escape(code)}</code> <i>(tap to copy)</i>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <i>This code expires in 5-10 minutes. Use it immediately to sign in.</i>"
        )
        await bot.send_message(chat_id=customer_id, text=customer_msg, parse_mode="HTML")
        await message.answer(f"✅ OTP code <code>{html.escape(code)}</code> delivered successfully to the user!", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"⚠️ Code saved in DB, but failed to direct-message user (Telegram error: {e})")


@admin_router.callback_query(F.data.startswith("otp_dismiss:"))
async def handle_otp_dismiss(callback: CallbackQuery):
    """Admin dismisses a 2FA request."""
    if not is_admin_filter(callback.from_user.id):
        return
    req_id = int(callback.data.split(":", 1)[1])
    req = await get_2fa_request(req_id)
    if req:
        req.status = "dismissed"
    await callback.message.edit_text("🚫 2FA request dismissed by admin.")
    await callback.answer("Dismissed")


# ------------------------------------------------------------------------------
# Quick Order Status Toggle
# ------------------------------------------------------------------------------

@admin_router.callback_query(F.data.startswith("set_status:"))
async def handle_set_status(callback: CallbackQuery, bot: Bot):
    """Admin toggles an order status from pending to ready or vice versa."""
    if not is_admin_filter(callback.from_user.id):
        return

    _, order_id_str, new_status = callback.data.split(":")
    order_id = int(order_id_str)
    order = await update_order_status(order_id, new_status)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    await callback.answer(f"Status changed to {new_status.upper()}")
    await callback.message.edit_text(
        f"✅ Order <code>{order.claim_code}</code> is now marked as <b>{new_status.upper()}</b>.",
        parse_mode="HTML"
    )

    # If order is now ready and a customer was waiting, notify them!
    if new_status == "ready" and order.customer_telegram_id:
        try:
            guide_text = f"\n\n📖 <b>Activation Guide:</b>\n{html.escape(order.activation_guide)}" if order.activation_guide else ""
            notify_text = (
                "🎉 <b>Great News! Your Order is Ready!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 <b>Product:</b> {html.escape(order.product_name)}\n"
                f"🔑 <b>Claim Code:</b> <code>{order.claim_code}</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🔐 <b>Account Credentials:</b>\n"
                f"<code>{html.escape(order.account_details)}</code>"
                f"{guide_text}\n\n"
                "You can request 2FA login codes anytime from your profile."
            )
            from bot.keyboards.user_kb import get_order_delivery_keyboard
            await bot.send_message(
                chat_id=order.customer_telegram_id,
                text=notify_text,
                reply_markup=get_order_delivery_keyboard(order.id, is_pending=False),
                parse_mode="HTML"
            )
        except Exception as e:
            pass
