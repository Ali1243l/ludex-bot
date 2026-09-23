# 📦 Digital Product Delivery Telegram Bot (aiogram 3.x)

An enterprise-ready, asynchronous Telegram Bot for automated digital goods fulfillment, subscription lifespan tracking, customer account delivery, and real-time 2FA / OTP login code routing.

---

## 🌟 Key Architecture & Workflows

### 1. 🛠️ Admin Management & Analytics
- **Step-by-Step FSM Order Creator:** Input Customer Name, Username, Product Name, Category, Cost Price, Selling Price, Duration, Credentials, and Activation Guide.
- **Unique Code Generator:** Generates high-entropy claim codes (e.g. `DLV-9K82-MC74`) and provides a one-tap copyable customer delivery message.
- **Real-Time Financial Dashboard:** Calculates Total Sales, Acquisition Costs, Net Realized Profit, Profit Margins, and order status counts.
- **Interactive 2FA / OTP Fulfillment:** Instant admin push notifications with inline buttons to dispatch OTP verification codes directly to the customer in real time.

### 2. 🎁 Customer Delivery & Self-Service
- **Mandatory Force-Subscribe Check:** Verifies membership in your official channel before allowing access to product delivery.
- **Claim Code Redemption:** Customers submit codes to unlock credentials, license keys, or accounts.
- **Queueing for Pending Orders:** If an order is marked "Pending", the customer is informed that preparation is underway and is automatically alerted when the admin sets it to "Ready".
- **Customer Dashboard:** Displays claimed products, credentials, remaining validity days for subscriptions, and activation guides.
- **2FA / OTP Request Trigger:** Customer taps "Request 2FA Code" to ping the admin team when signing into their delivered account.

### 3. 🗄️ Relational Database Schema (SQLAlchemy 2.0 Async)
- **`users`**: `telegram_id` (PK), `username`, `full_name`, `joined_at`.
- **`orders`**: `id`, `claim_code` (Unique), `customer_name`, `customer_username`, `customer_telegram_id`, `product_name`, `product_type`, `cost_price`, `selling_price`, `account_details`, `activation_guide`, `status`, `duration_days`, `created_at`, `claimed_at`, `expiry_date`.
- **`two_factor_requests`**: `id`, `order_id`, `telegram_id`, `customer_name`, `product_name`, `status`, `code_reply`, `created_at`, `replied_at`.

---

## 🚀 Quick Start Guide

### 1. Requirements & Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

Edit `.env`:
```env
BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
ADMIN_IDS="123456789,987654321"
CHANNEL_ID="@myvipchannel"
CHANNEL_URL="https://t.me/myvipchannel"
DATABASE_URL="sqlite+aiosqlite:///delivery_bot.db"
CURRENCY_SYMBOL="$"
```

### 3. Run the Bot
```bash
python bot.py
```

The bot will automatically generate all database tables on the first run.
