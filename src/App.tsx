import React, { useState } from "react";
import {
  Bot as BotIcon,
  Shield,
  User,
  ShoppingBag,
  PlusCircle,
  Key,
  Clock,
  DollarSign,
  TrendingUp,
  FileCode,
  Database,
  CheckCircle2,
  AlertCircle,
  Send,
  Copy,
  ExternalLink,
  ChevronRight,
  Terminal,
  RefreshCw,
  Sparkles,
  Smartphone,
  Lock,
  Layers,
  ArrowRight,
  Check
} from "lucide-react";

interface SimulatedOrder {
  id: number;
  claim_code: string;
  customer_name: string;
  customer_username?: string;
  customer_telegram_id?: number;
  product_name: string;
  product_type: string;
  cost_price: number;
  selling_price: number;
  account_details: string;
  activation_guide?: string;
  status: "pending" | "ready" | "claimed";
  duration_days?: number;
  created_at: string;
  claimed_at?: string;
  expiry_date?: string;
}

interface Simulated2FARequest {
  id: number;
  order_id: number;
  order_code: string;
  customer_name: string;
  customer_tg_id: number;
  product_name: string;
  status: "pending" | "answered";
  code_reply?: string;
  created_at: string;
}

interface ChatMessage {
  id: string;
  sender: "bot" | "user";
  text: string;
  timestamp: string;
  markup?: {
    type: "inline" | "reply";
    buttons: { text: string; action: () => void; url?: string; variant?: "primary" | "secondary" | "danger" }[];
  };
}

export default function App() {
  const [activeTab, setActiveTab] = useState<"simulator" | "code" | "database" | "overview">("simulator");
  const [botMode, setBotMode] = useState<"customer" | "admin">("customer");

  // Simulated DB State
  const [orders, setOrders] = useState<SimulatedOrder[]>([
    {
      id: 1,
      claim_code: "DLV-NETF-9921",
      customer_name: "Alex Smith",
      customer_username: "alexsmith",
      customer_telegram_id: 88123456,
      product_name: "Netflix 4K UHD 1 Screen",
      product_type: "Streaming Account",
      cost_price: 2.50,
      selling_price: 6.99,
      account_details: "user: alex.smith82@gmail.com\npass: StreamPass2026!\nprofile: Profile 4 (PIN 8821)",
      activation_guide: "1. Log in on your Smart TV or Browser.\n2. Select Profile 4.\n3. Do not change account password or primary email.",
      status: "claimed",
      duration_days: 30,
      created_at: "2026-09-20 14:32:00",
      claimed_at: "2026-09-20 15:10:00",
      expiry_date: "2026-10-20"
    },
    {
      id: 2,
      claim_code: "DLV-VPN7-4102",
      customer_name: "Sarah Miller",
      customer_username: "sarahm",
      product_name: "NordVPN Premium Ultra 1 Year",
      product_type: "VPN Service",
      cost_price: 9.00,
      selling_price: 24.50,
      account_details: "user: nord_sarah22@secure.net\npass: NordFast77#",
      activation_guide: "Download NordVPN app, log in with credentials, connect to any server.",
      status: "ready",
      duration_days: 365,
      created_at: "2026-09-22 09:15:00"
    },
    {
      id: 3,
      claim_code: "DLV-SPOT-1108",
      customer_name: "David Kim",
      customer_username: "dkim99",
      product_name: "Spotify Premium Family Slot",
      product_type: "Streaming Account",
      cost_price: 1.20,
      selling_price: 4.50,
      account_details: "Account being provisioned by seller.",
      status: "pending",
      duration_days: 30,
      created_at: "2026-09-23 06:20:00"
    }
  ]);

  const [twoFARequests, setTwoFARequests] = useState<Simulated2FARequest[]>([
    {
      id: 101,
      order_id: 1,
      order_code: "DLV-NETF-9921",
      customer_name: "Alex Smith",
      customer_tg_id: 88123456,
      product_name: "Netflix 4K UHD 1 Screen",
      status: "pending",
      created_at: "Just now"
    }
  ]);

  // Force subscribe simulation state
  const [isSubscribed, setIsSubscribed] = useState<boolean>(true);

  // FSM Admin creation state
  const [fsmStep, setFsmStep] = useState<number>(0);
  const [newOrderData, setNewOrderData] = useState({
    customer_name: "",
    customer_username: "",
    product_name: "",
    product_type: "Streaming Account",
    cost_price: "2.00",
    selling_price: "5.99",
    duration_days: "30",
    account_details: "",
    activation_guide: "",
    status: "ready" as "ready" | "pending"
  });

  // Customer Chat History
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "m1",
      sender: "bot",
      text: "👋 Hello, <b>Customer</b>!\n\nWelcome to the <b>Digital Product Delivery Bot</b>.\nTap <b>🎁 Claim Order Code</b> below to retrieve your credentials.",
      timestamp: "10:00 AM",
      markup: {
        type: "reply",
        buttons: [
          { text: "🎁 Claim Order Code", action: () => handleUserAction("claim") },
          { text: "👤 My Profile & Purchases", action: () => handleUserAction("profile") }
        ]
      }
    }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [copiedFile, setCopiedFile] = useState<string | null>(null);

  // Selected file for Code Explorer
  const [selectedFile, setSelectedFile] = useState<string>("bot.py");

  // OTP reply input in admin view
  const [otpInput, setOtpInput] = useState<{ [key: number]: string }>({});

  // Helper stats calculation
  const totalSales = orders.reduce((sum, o) => sum + o.selling_price, 0);
  const totalCosts = orders.reduce((sum, o) => sum + o.cost_price, 0);
  const netProfit = totalSales - totalCosts;
  const readyCount = orders.filter(o => o.status === "ready").length;
  const pendingCount = orders.filter(o => o.status === "pending").length;
  const claimedCount = orders.filter(o => o.status === "claimed").length;

  const handleUserAction = (action: string) => {
    if (!isSubscribed) {
      addBotMessage(
        "📢 <b>Channel Subscription Required</b>\n\nTo access our automated delivery service, you must be a member of our official channel.",
        {
          type: "inline",
          buttons: [
            { text: "📢 Join Official Channel", action: () => setIsSubscribed(true), url: "https://t.me/example" },
            { text: "🔄 Verify Subscription", action: () => {
              setIsSubscribed(true);
              addBotMessage("✅ <b>Subscription Verified!</b>\nYou now have full access to our delivery bot.");
            }, variant: "primary" }
          ]
        }
      );
      return;
    }

    if (action === "claim") {
      addBotMessage("🔑 <b>Claim Your Digital Product</b>\n\nPlease enter your unique claim code (e.g. <code>DLV-VPN7-4102</code> or <code>DLV-SPOT-1108</code>):");
    } else if (action === "profile") {
      const userOrders = orders.filter(o => o.customer_telegram_id === 88123456 || o.status === "claimed");
      let msg = `👤 <b>Customer Dashboard</b>\n━━━━━━━━━━━━━━━━━━━━━━\n🆔 <b>Telegram ID:</b> <code>88123456</code>\n🛍️ <b>Claimed Products:</b> ${userOrders.length}\n💰 <b>Total Spent:</b> $${userOrders.reduce((s, o) => s + o.selling_price, 0).toFixed(2)}\n━━━━━━━━━━━━━━━━━━━━━━\n\n`;

      if (userOrders.length === 0) {
        msg += "You have no claimed products yet. Send your code to claim one!";
        addBotMessage(msg);
      } else {
        userOrders.forEach(o => {
          msg += `📦 <b>${o.product_name}</b>\n🔑 Code: <code>${o.claim_code}</code>\n🔐 <b>Credentials:</b>\n<code>${o.account_details}</code>\n⏱️ <b>Lifespan:</b> ${o.duration_days ? o.duration_days + " Days" : "Lifetime"}\n\n`;
        });
        addBotMessage(msg, {
          type: "inline",
          buttons: [
            {
              text: "🔐 Request 2FA / OTP Code",
              action: () => trigger2FARequest(userOrders[0]?.id || 1),
              variant: "primary"
            }
          ]
        });
      }
    }
  };

  const trigger2FARequest = (orderId: number) => {
    const order = orders.find(o => o.id === orderId) || orders[0];
    const newReq: Simulated2FARequest = {
      id: Date.now(),
      order_id: order.id,
      order_code: order.claim_code,
      customer_name: order.customer_name,
      customer_tg_id: 88123456,
      product_name: order.product_name,
      status: "pending",
      created_at: "Just now"
    };

    setTwoFARequests(prev => [newReq, ...prev]);

    addBotMessage(
      `📡 <b>2FA Verification Code Requested!</b>\n\nYour request for <b>${order.product_name}</b> has been dispatched to our administrators. When the admin sends the OTP code, it will appear here automatically.\n<i>Please remain on the login screen of your app.</i>`
    );
  };

  const handleAdminSendOtp = (reqId: number) => {
    const code = otpInput[reqId]?.trim() || "849201";
    setTwoFARequests(prev =>
      prev.map(r => (r.id === reqId ? { ...r, status: "answered", code_reply: code } : r))
    );

    // Push notification to user chat!
    addBotMessage(
      `🔐 <b>2FA / OTP Login Code Received!</b>\n━━━━━━━━━━━━━━━━━━━━━━\n🔑 <b>Verification Code:</b> <code>${code}</code> <i>(tap to copy)</i>\n━━━━━━━━━━━━━━━━━━━━━━\n⚠️ <i>This code expires in 5-10 minutes. Use it immediately to sign in.</i>`
    );

    setOtpInput(prev => ({ ...prev, [reqId]: "" }));
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userText = chatInput.trim();
    setChatInput("");

    // Add user message to UI
    addUserMessage(userText);

    // Evaluate response
    const upper = userText.toUpperCase();
    const matchedOrder = orders.find(o => o.claim_code.toUpperCase() === upper);

    if (matchedOrder) {
      // Mark as claimed in DB
      setOrders(prev =>
        prev.map(o =>
          o.id === matchedOrder.id
            ? { ...o, status: o.status === "pending" ? "pending" : "claimed", customer_telegram_id: 88123456 }
            : o
        )
      );

      if (matchedOrder.status === "pending") {
        addBotMessage(
          `⏳ <b>Your Order is Being Prepared!</b>\n━━━━━━━━━━━━━━━━━━━━━━\n📦 <b>Product:</b> ${matchedOrder.product_name}\n🔑 <b>Claim Code:</b> <code>${matchedOrder.claim_code}</code>\n⚡ <b>Status:</b> <i>PREPARING / PENDING</i>\n━━━━━━━━━━━━━━━━━━━━━━\nOur team is currently configuring your account credentials. You will be automatically notified here the moment it is ready!`
        );
      } else {
        const guide = matchedOrder.activation_guide
          ? `\n\n📖 <b>Activation Guide:</b>\n${matchedOrder.activation_guide}`
          : "";
        addBotMessage(
          `🎉 <b>Order Claimed Successfully!</b>\n━━━━━━━━━━━━━━━━━━━━━━\n📦 <b>Product:</b> <b>${matchedOrder.product_name}</b>\n🏷️ <b>Type:</b> ${matchedOrder.product_type}\n🔑 <b>Code:</b> <code>${matchedOrder.claim_code}</code>\n⏱️ <b>Validity:</b> ${matchedOrder.duration_days || 30} Days\n━━━━━━━━━━━━━━━━━━━━━━\n🔐 <b>Account Credentials:</b>\n<code>${matchedOrder.account_details}</code>${guide}\n━━━━━━━━━━━━━━━━━━━━━━\n💡 <i>Need a 2FA code to log in? Tap the button below!</i>`,
          {
            type: "inline",
            buttons: [
              {
                text: "🔐 Request 2FA / OTP Code",
                action: () => trigger2FARequest(matchedOrder.id),
                variant: "primary"
              },
              {
                text: "📖 View Guide",
                action: () => addBotMessage(`📖 <b>Guide for ${matchedOrder.product_name}:</b>\n${matchedOrder.activation_guide || "Standard login via official client."}`)
              }
            ]
          }
        );
      }
    } else if (upper.startsWith("DLV-")) {
      addBotMessage(`❌ <b>Code Not Found</b>\nThe code <code>${userText}</code> was not found. Please verify your claim code or contact support.`);
    } else {
      addBotMessage("💡 Send a claim code (e.g. <code>DLV-VPN7-4102</code>) or tap a button below.", {
        type: "reply",
        buttons: [
          { text: "🎁 Claim Order Code", action: () => handleUserAction("claim") },
          { text: "👤 My Profile & Purchases", action: () => handleUserAction("profile") }
        ]
      });
    }
  };

  const addUserMessage = (text: string) => {
    setChatMessages(prev => [
      ...prev,
      {
        id: "msg_" + Date.now(),
        sender: "user",
        text,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      }
    ]);
  };

  const addBotMessage = (text: string, markup?: ChatMessage["markup"]) => {
    setChatMessages(prev => [
      ...prev,
      {
        id: "msg_" + Date.now(),
        sender: "bot",
        text,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        markup
      }
    ]);
  };

  const handleCreateOrderSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    const c1 = Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
    const c2 = Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
    const generatedCode = `DLV-${c1}-${c2}`;

    const createdOrder: SimulatedOrder = {
      id: Date.now(),
      claim_code: generatedCode,
      customer_name: newOrderData.customer_name || "Customer",
      customer_username: newOrderData.customer_username || undefined,
      product_name: newOrderData.product_name || "Digital Account",
      product_type: newOrderData.product_type,
      cost_price: parseFloat(newOrderData.cost_price) || 0,
      selling_price: parseFloat(newOrderData.selling_price) || 0,
      account_details: newOrderData.account_details || "email: demo@pass.com\npass: Secret123",
      activation_guide: newOrderData.activation_guide || undefined,
      status: newOrderData.status,
      duration_days: parseInt(newOrderData.duration_days) || 30,
      created_at: new Date().toISOString().replace("T", " ").substring(0, 19)
    };

    setOrders(prev => [createdOrder, ...prev]);
    setFsmStep(0);
    setNewOrderData({
      customer_name: "",
      customer_username: "",
      product_name: "",
      product_type: "Streaming Account",
      cost_price: "2.00",
      selling_price: "5.99",
      duration_days: "30",
      account_details: "",
      activation_guide: "",
      status: "ready"
    });
  };

  const projectFiles: { [path: string]: { description: string; language: string; code: string } } = {
    "bot.py": {
      description: "Main bot execution runner, dispatcher setup, command registration & long-polling.",
      language: "python",
      code: `"""
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("delivery_bot")

async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Start bot & main menu"),
        BotCommand(command="claim", description="🎁 Claim order via tracking code"),
        BotCommand(command="profile", description="👤 View claimed products & subscriptions"),
        BotCommand(command="admin", description="🛠️ Admin management dashboard"),
        BotCommand(command="help", description="ℹ️ Help and customer support")
    ]
    await bot.set_my_commands(commands)

async def main() -> None:
    await init_db()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router)
    dp.include_router(user_router)
    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())`
    },
    "config.py": {
      description: "Environment configuration, admin ID parsing, channel IDs and database URLs.",
      language: "python",
      code: `"""Configuration Module."""
import os
from typing import List
from dotenv import load_dotenv

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
        if not self._admin_ids_raw:
            return []
        return [int(x.strip()) for x in self._admin_ids_raw.split(",") if x.strip().isdigit()]

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.ADMIN_IDS

settings = Settings()`
    },
    "database.py": {
      description: "SQLAlchemy 2.0 Async models (User, Order, TwoFactorRequest) and business operations.",
      language: "python",
      code: `"""SQLAlchemy Async Database Module."""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String, Text, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, relationship
from config import settings

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    orders = relationship("Order", back_populates="customer")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_code = Column(String(32), unique=True, index=True, nullable=False)
    customer_name = Column(String(128), nullable=False)
    customer_username = Column(String(64), nullable=True)
    customer_telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    product_name = Column(String(128), nullable=False)
    product_type = Column(String(64), default="Account")
    cost_price = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    account_details = Column(Text, nullable=False)
    activation_guide = Column(Text, nullable=True)
    status = Column(String(32), default="ready") # pending, ready, claimed
    duration_days = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    claimed_at = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    customer = relationship("User", back_populates="orders")
    two_factor_requests = relationship("TwoFactorRequest", back_populates="order")

class TwoFactorRequest(Base):
    __tablename__ = "two_factor_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    customer_name = Column(String(128), nullable=True)
    product_name = Column(String(128), nullable=True)
    status = Column(String(32), default="pending")
    code_reply = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    replied_at = Column(DateTime, nullable=True)
    order = relationship("Order", back_populates="two_factor_requests")

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)`
    },
    "bot/handlers/admin.py": {
      description: "Admin FSM order creator, code generator, sales analytics dashboard & 2FA replies.",
      language: "python",
      code: `"""Admin Handlers: Step-by-Step Order Creation & Analytics."""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.states.admin_states import OrderCreationFSM, Answer2FAFSM
from database import create_order, get_admin_stats, answer_2fa_request

admin_router = Router(name="admin_router")

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await message.answer("🛠️ Admin Control Panel\\nUse buttons below to manage orders or view stats.")`
    },
    "bot/handlers/user.py": {
      description: "Customer Force-Subscribe check, code claiming, account delivery, dashboard & 2FA ping.",
      language: "python",
      code: `"""Customer Handlers: Force-Subscribe, Claiming & 2FA Requests."""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from database import get_order_by_code, claim_order_for_user, create_2fa_request
from bot.middlewares.subscription import check_user_subscription

user_router = Router(name="user_router")

@user_router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    is_sub, _ = await check_user_subscription(bot, message.from_user.id)
    if not is_sub:
        await message.answer("📢 Subscription required to continue.")
        return
    await message.answer("👋 Welcome! Tap '🎁 Claim Order Code' to redeem your product.")`
    },
    "bot/states/admin_states.py": {
      description: "FSM state groups for step-by-step order creation & OTP replies.",
      language: "python",
      code: `"""Admin FSM States."""
from aiogram.fsm.state import State, StatesGroup

class OrderCreationFSM(StatesGroup):
    waiting_for_customer_name = State()
    waiting_for_customer_username = State()
    waiting_for_product_name = State()
    waiting_for_product_type = State()
    waiting_for_cost_price = State()
    waiting_for_selling_price = State()
    waiting_for_duration_days = State()
    waiting_for_account_details = State()
    waiting_for_activation_guide = State()
    waiting_for_initial_status = State()
    confirm_order = State()

class Answer2FAFSM(StatesGroup):
    waiting_for_otp_code = State()`
    },
    "bot/middlewares/subscription.py": {
      description: "Channel Force Subscribe verification against official Telegram channel.",
      language: "python",
      code: `"""Force Subscribe Verification."""
from aiogram import Bot
from config import settings

async def check_user_subscription(bot: Bot, user_id: int):
    if not settings.CHANNEL_ID or settings.is_admin(user_id):
        return True, "Bypass"
    try:
        member = await bot.get_chat_member(chat_id=settings.CHANNEL_ID, user_id=user_id)
        return member.status in ("creator", "administrator", "member", "restricted"), "Status"
    except Exception as e:
        return True, str(e)`
    },
    "requirements.txt": {
      description: "Python package dependencies with exact versions.",
      language: "text",
      code: `aiogram>=3.17.0
sqlalchemy[asyncio]>=2.0.36
aiosqlite>=0.20.0
asyncpg>=0.30.0
pydantic>=2.10.0
pydantic-settings>=2.7.0
python-dotenv>=1.0.1`
    },
    ".env.example": {
      description: "Environment variables template for bot token, admin IDs, and database.",
      language: "env",
      code: `BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
ADMIN_IDS="123456789,987654321"
CHANNEL_ID="@myvipchannel"
CHANNEL_URL="https://t.me/myvipchannel"
DATABASE_URL="sqlite+aiosqlite:///delivery_bot.db"
CURRENCY_SYMBOL="$"`
    }
  };

  const copyToClipboard = (text: string, filename: string) => {
    navigator.clipboard.writeText(text);
    setCopiedFile(filename);
    setTimeout(() => setCopiedFile(null), 2500);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500/30">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <BotIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">Digital Delivery Bot</span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                  aiogram 3.x
                </span>
              </div>
              <p className="text-xs text-slate-400">Automated Account Delivery & 2FA Routing Engine</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <nav className="flex items-center bg-slate-800/80 p-1 rounded-xl border border-slate-700/60 text-xs font-medium">
              <button
                onClick={() => setActiveTab("simulator")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === "simulator"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" />
                Live Bot Simulator
              </button>
              <button
                onClick={() => setActiveTab("code")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === "code"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                GitHub Code Files
              </button>
              <button
                onClick={() => setActiveTab("database")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === "database"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                Database ({orders.length})
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6">
        {activeTab === "simulator" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Telegram Simulator Chat Interface */}
            <div className="lg:col-span-7 flex flex-col items-center">
              <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col h-[720px] ring-1 ring-slate-700/50">
                {/* Simulated Telegram Phone Top Bar */}
                <div className="bg-slate-800/90 border-b border-slate-700/80 px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow">
                      🤖
                    </div>
                    <div>
                      <div className="font-semibold text-sm text-white flex items-center gap-1.5">
                        Delivery Bot
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                      </div>
                      <span className="text-[11px] text-slate-400">bot • automated service</span>
                    </div>
                  </div>

                  {/* Mode switcher inside simulator */}
                  <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-700 text-xs">
                    <button
                      onClick={() => setBotMode("customer")}
                      className={`px-2.5 py-1 rounded-md transition-all ${
                        botMode === "customer" ? "bg-indigo-600 text-white font-medium" : "text-slate-400"
                      }`}
                    >
                      Customer View
                    </button>
                    <button
                      onClick={() => setBotMode("admin")}
                      className={`px-2.5 py-1 rounded-md transition-all ${
                        botMode === "admin" ? "bg-amber-600 text-white font-medium" : "text-slate-400"
                      }`}
                    >
                      Admin View
                    </button>
                  </div>
                </div>

                {/* Force Subscribe Banner Simulation */}
                {!isSubscribed && (
                  <div className="bg-amber-500/10 border-b border-amber-500/20 px-3 py-2 flex items-center justify-between text-xs text-amber-300">
                    <div className="flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5 text-amber-400" />
                      <span>Channel subscription not verified</span>
                    </div>
                    <button
                      onClick={() => setIsSubscribed(true)}
                      className="text-xs bg-amber-500 text-slate-950 font-bold px-2 py-0.5 rounded hover:bg-amber-400"
                    >
                      Verify Now
                    </button>
                  </div>
                )}

                {/* Chat Messages Body */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px]">
                  {chatMessages.map(msg => (
                    <div
                      key={msg.id}
                      className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed ${
                          msg.sender === "user"
                            ? "bg-indigo-600 text-white rounded-tr-none shadow-md shadow-indigo-600/20"
                            : "bg-slate-800 text-slate-200 border border-slate-700/80 rounded-tl-none shadow-md"
                        }`}
                      >
                        <div
                          className="whitespace-pre-wrap"
                          dangerouslySetInnerHTML={{ __html: msg.text.replace(/<code>(.*?)<\/code>/g, '<code class="bg-slate-900/90 text-amber-300 px-1.5 py-0.5 rounded font-mono text-[11px] font-bold border border-slate-700/60">$1</code>') }}
                        />
                        <div
                          className={`text-[10px] mt-1 text-right ${
                            msg.sender === "user" ? "text-indigo-200" : "text-slate-400"
                          }`}
                        >
                          {msg.timestamp}
                        </div>
                      </div>

                      {/* Inline or Reply Buttons */}
                      {msg.markup && (
                        <div className="mt-2 flex flex-col gap-1.5 w-full max-w-[85%]">
                          {msg.markup.buttons.map((btn, i) => (
                            <button
                              key={i}
                              onClick={btn.action}
                              className={`text-xs px-3 py-2 rounded-xl transition-all flex items-center justify-center gap-1.5 font-medium border ${
                                btn.variant === "primary"
                                  ? "bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white border-indigo-400/30 shadow-md"
                                  : "bg-slate-800/90 hover:bg-slate-700/90 text-slate-200 border-slate-700"
                              }`}
                            >
                              {btn.text}
                              {btn.url && <ExternalLink className="w-3 h-3 text-slate-400" />}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Chat Quick Action Bar */}
                <div className="p-2 bg-slate-800/60 border-t border-slate-800 flex items-center gap-1.5 overflow-x-auto text-xs">
                  <button
                    onClick={() => handleUserAction("claim")}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 whitespace-nowrap border border-slate-700/60 flex items-center gap-1"
                  >
                    🎁 Claim Code
                  </button>
                  <button
                    onClick={() => handleUserAction("profile")}
                    className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 whitespace-nowrap border border-slate-700/60 flex items-center gap-1"
                  >
                    👤 My Purchases
                  </button>
                  <button
                    onClick={() => {
                      setChatInput("DLV-VPN7-4102");
                    }}
                    className="px-2 py-1 rounded-lg bg-indigo-950/80 hover:bg-indigo-900/80 text-indigo-300 whitespace-nowrap border border-indigo-800/50 text-[11px]"
                  >
                    Paste Test Code 1
                  </button>
                  <button
                    onClick={() => {
                      setChatInput("DLV-SPOT-1108");
                    }}
                    className="px-2 py-1 rounded-lg bg-indigo-950/80 hover:bg-indigo-900/80 text-indigo-300 whitespace-nowrap border border-indigo-800/50 text-[11px]"
                  >
                    Paste Pending Code 2
                  </button>
                </div>

                {/* Input Bar */}
                <form onSubmit={handleSendMessage} className="p-3 bg-slate-900 border-t border-slate-800 flex items-center gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    placeholder="Type code or message..."
                    className="flex-1 bg-slate-800/90 border border-slate-700 rounded-xl px-3.5 py-2 text-xs sm:text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <button
                    type="submit"
                    className="w-9 h-9 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center transition-colors shadow-md shadow-indigo-600/30"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </div>

            {/* Right Column: Admin Panel / Real-time Companion */}
            <div className="lg:col-span-5 space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                    <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
                    Total Sales
                  </div>
                  <div className="text-lg font-bold text-white">${totalSales.toFixed(2)}</div>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                    <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
                    Net Profit
                  </div>
                  <div className="text-lg font-bold text-emerald-400">${netProfit.toFixed(2)}</div>
                </div>

                <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl col-span-2 sm:col-span-1">
                  <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                    <ShoppingBag className="w-3.5 h-3.5 text-blue-400" />
                    Orders
                  </div>
                  <div className="text-lg font-bold text-white">
                    {orders.length} <span className="text-xs text-slate-400 font-normal">({readyCount} ready)</span>
                  </div>
                </div>
              </div>

              {/* Step-by-Step FSM Order Creator */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
                <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                      <PlusCircle className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm text-white">FSM Order Creator</h3>
                      <p className="text-[11px] text-slate-400">Admin Step-by-Step Code Generator</p>
                    </div>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                    Step {fsmStep + 1} of 4
                  </span>
                </div>

                <form onSubmit={handleCreateOrderSubmit} className="space-y-3.5 text-xs">
                  {fsmStep === 0 && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-slate-400 font-medium mb-1">Customer Full Name</label>
                        <input
                          type="text"
                          required
                          value={newOrderData.customer_name}
                          onChange={e => setNewOrderData({ ...newOrderData, customer_name: e.target.value })}
                          placeholder="e.g. John Doe"
                          className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-400 font-medium mb-1">Telegram @username (Optional)</label>
                        <input
                          type="text"
                          value={newOrderData.customer_username}
                          onChange={e => setNewOrderData({ ...newOrderData, customer_username: e.target.value })}
                          placeholder="e.g. johndoe"
                          className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => setFsmStep(1)}
                        className="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-xl flex items-center justify-center gap-1 transition-colors"
                      >
                        Next: Product Info <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}

                  {fsmStep === 1 && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-slate-400 font-medium mb-1">Product Title</label>
                        <input
                          type="text"
                          required
                          value={newOrderData.product_name}
                          onChange={e => setNewOrderData({ ...newOrderData, product_name: e.target.value })}
                          placeholder="e.g. Disney+ Premium 1 Month"
                          className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-slate-400 font-medium mb-1">Category</label>
                          <select
                            value={newOrderData.product_type}
                            onChange={e => setNewOrderData({ ...newOrderData, product_type: e.target.value })}
                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-2 text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                          >
                            <option value="Streaming Account">Streaming Account</option>
                            <option value="VPN Service">VPN Service</option>
                            <option value="License Key">License Key</option>
                            <option value="Cloud Account">Cloud Account</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-slate-400 font-medium mb-1">Duration (Days)</label>
                          <input
                            type="number"
                            value={newOrderData.duration_days}
                            onChange={e => setNewOrderData({ ...newOrderData, duration_days: e.target.value })}
                            placeholder="30"
                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                          />
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setFsmStep(0)}
                          className="w-1/3 bg-slate-800 text-slate-300 py-2 rounded-xl"
                        >
                          Back
                        </button>
                        <button
                          type="button"
                          onClick={() => setFsmStep(2)}
                          className="w-2/3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-xl flex items-center justify-center gap-1"
                        >
                          Next: Pricing <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}

                  {fsmStep === 2 && (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-slate-400 font-medium mb-1">Cost Price ($)</label>
                          <input
                            type="number"
                            step="0.01"
                            value={newOrderData.cost_price}
                            onChange={e => setNewOrderData({ ...newOrderData, cost_price: e.target.value })}
                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-100 focus:outline-none"
                          />
                        </div>
                        <div>
                          <label className="block text-slate-400 font-medium mb-1">Selling Price ($)</label>
                          <input
                            type="number"
                            step="0.01"
                            value={newOrderData.selling_price}
                            onChange={e => setNewOrderData({ ...newOrderData, selling_price: e.target.value })}
                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-100 focus:outline-none"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-slate-400 font-medium mb-1">Initial Readiness</label>
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            type="button"
                            onClick={() => setNewOrderData({ ...newOrderData, status: "ready" })}
                            className={`py-2 px-3 rounded-xl border text-center transition-all ${
                              newOrderData.status === "ready"
                                ? "bg-emerald-500/20 border-emerald-500 text-emerald-300 font-semibold"
                                : "bg-slate-800 border-slate-700 text-slate-400"
                            }`}
                          >
                            ⚡ Ready (Instant)
                          </button>
                          <button
                            type="button"
                            onClick={() => setNewOrderData({ ...newOrderData, status: "pending" })}
                            className={`py-2 px-3 rounded-xl border text-center transition-all ${
                              newOrderData.status === "pending"
                                ? "bg-amber-500/20 border-amber-500 text-amber-300 font-semibold"
                                : "bg-slate-800 border-slate-700 text-slate-400"
                            }`}
                          >
                            ⏳ Pending (Prep)
                          </button>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setFsmStep(1)}
                          className="w-1/3 bg-slate-800 text-slate-300 py-2 rounded-xl"
                        >
                          Back
                        </button>
                        <button
                          type="button"
                          onClick={() => setFsmStep(3)}
                          className="w-2/3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-xl flex items-center justify-center gap-1"
                        >
                          Next: Credentials <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}

                  {fsmStep === 3 && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-slate-400 font-medium mb-1">Account Credentials / Content</label>
                        <textarea
                          rows={3}
                          required
                          value={newOrderData.account_details}
                          onChange={e => setNewOrderData({ ...newOrderData, account_details: e.target.value })}
                          placeholder="email:pass or license key details..."
                          className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-100 font-mono text-[11px] focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-400 font-medium mb-1">Activation Guide (Optional)</label>
                        <input
                          type="text"
                          value={newOrderData.activation_guide}
                          onChange={e => setNewOrderData({ ...newOrderData, activation_guide: e.target.value })}
                          placeholder="Setup instructions for the customer..."
                          className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-slate-100 focus:outline-none"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => setFsmStep(2)}
                          className="w-1/3 bg-slate-800 text-slate-300 py-2 rounded-xl"
                        >
                          Back
                        </button>
                        <button
                          type="submit"
                          className="w-2/3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2 rounded-xl flex items-center justify-center gap-1.5 shadow-lg shadow-emerald-600/20"
                        >
                          <Check className="w-4 h-4" /> Generate Code
                        </button>
                      </div>
                    </div>
                  )}
                </form>
              </div>

              {/* 2FA / OTP Request Queue */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
                <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2.5">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400 border border-amber-500/20">
                      <Key className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm text-white">2FA / OTP Notifications</h3>
                      <p className="text-[11px] text-slate-400">Customer verification requests</p>
                    </div>
                  </div>
                  <span className="text-xs bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full font-medium">
                    {twoFARequests.filter(r => r.status === "pending").length} Open
                  </span>
                </div>

                <div className="space-y-3">
                  {twoFARequests.length === 0 ? (
                    <div className="text-center py-6 text-xs text-slate-500">
                      No incoming 2FA requests right now.
                    </div>
                  ) : (
                    twoFARequests.map(req => (
                      <div
                        key={req.id}
                        className={`p-3 rounded-xl border text-xs ${
                          req.status === "pending"
                            ? "bg-amber-500/5 border-amber-500/30 text-slate-200"
                            : "bg-slate-800/40 border-slate-800 text-slate-400"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-bold text-white">{req.customer_name}</span>
                          <span className="font-mono text-[10px] text-slate-400">{req.order_code}</span>
                        </div>
                        <p className="text-slate-300 mb-2">Product: {req.product_name}</p>

                        {req.status === "pending" ? (
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={otpInput[req.id] || ""}
                              onChange={e => setOtpInput({ ...otpInput, [req.id]: e.target.value })}
                              placeholder="e.g. 592810"
                              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1 text-slate-100 font-mono text-xs focus:outline-none"
                            />
                            <button
                              onClick={() => handleAdminSendOtp(req.id)}
                              className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-3 py-1 rounded-lg transition-colors flex items-center gap-1"
                            >
                              Reply OTP
                            </button>
                          </div>
                        ) : (
                          <div className="text-emerald-400 flex items-center gap-1 text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Sent OTP:{" "}
                            <span className="font-mono font-bold">{req.code_reply}</span>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "code" && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
            {/* Left: File Tree Explorer */}
            <div className="md:col-span-4 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
              <h3 className="font-bold text-sm text-white mb-1 flex items-center gap-2">
                <FileCode className="w-4 h-4 text-indigo-400" />
                Project Code Structure
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                All files are created in your repository root ready to sync to GitHub.
              </p>

              <div className="space-y-1 text-xs">
                {Object.keys(projectFiles).map(filename => (
                  <button
                    key={filename}
                    onClick={() => setSelectedFile(filename)}
                    className={`w-full text-left px-3 py-2 rounded-xl transition-all flex items-center justify-between font-mono text-[12px] ${
                      selectedFile === filename
                        ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 font-semibold"
                        : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                    }`}
                  >
                    <span>{filename}</span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
                  </button>
                ))}
              </div>
            </div>

            {/* Right: Code Viewer */}
            <div className="md:col-span-8 bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
              <div className="bg-slate-800/80 border-b border-slate-700/80 px-4 py-3 flex items-center justify-between">
                <div>
                  <div className="font-mono text-sm font-bold text-white flex items-center gap-2">
                    <span>{selectedFile}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-700 text-slate-300 font-sans">
                      {projectFiles[selectedFile].language}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{projectFiles[selectedFile].description}</p>
                </div>

                <button
                  onClick={() => copyToClipboard(projectFiles[selectedFile].code, selectedFile)}
                  className="px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors"
                >
                  {copiedFile === selectedFile ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" /> Copy Code
                    </>
                  )}
                </button>
              </div>

              <div className="p-4 bg-slate-950 overflow-x-auto max-h-[600px]">
                <pre className="font-mono text-xs leading-relaxed text-slate-300 selection:bg-indigo-500/40">
                  <code>{projectFiles[selectedFile].code}</code>
                </pre>
              </div>
            </div>
          </div>
        )}

        {activeTab === "database" && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Database className="w-4 h-4 text-indigo-400" />
                  SQLite / PostgreSQL Database Inspector
                </h3>
                <p className="text-xs text-slate-400">
                  Live table view for <code>orders</code>, tracking claim codes, profit margins, and statuses.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  {claimedCount} Claimed
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
                  {readyCount} Ready
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                  {pendingCount} Pending
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-700/80 font-medium">
                  <tr>
                    <th className="px-3 py-2.5">ID</th>
                    <th className="px-3 py-2.5">Claim Code</th>
                    <th className="px-3 py-2.5">Customer</th>
                    <th className="px-3 py-2.5">Product</th>
                    <th className="px-3 py-2.5">Type</th>
                    <th className="px-3 py-2.5">Cost</th>
                    <th className="px-3 py-2.5">Price</th>
                    <th className="px-3 py-2.5">Status</th>
                    <th className="px-3 py-2.5">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono text-[11px]">
                  {orders.map(order => (
                    <tr key={order.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-3 py-3 text-slate-500">#{order.id}</td>
                      <td className="px-3 py-3 font-bold text-amber-300">
                        <code>{order.claim_code}</code>
                      </td>
                      <td className="px-3 py-3 font-sans text-slate-200">
                        {order.customer_name} {order.customer_username && `@${order.customer_username}`}
                      </td>
                      <td className="px-3 py-3 font-sans text-slate-100">{order.product_name}</td>
                      <td className="px-3 py-3 font-sans text-slate-400">{order.product_type}</td>
                      <td className="px-3 py-3 text-slate-400">${order.cost_price.toFixed(2)}</td>
                      <td className="px-3 py-3 text-emerald-400 font-bold">${order.selling_price.toFixed(2)}</td>
                      <td className="px-3 py-3">
                        <span
                          className={`px-2 py-0.5 rounded-full font-sans text-[10px] font-semibold ${
                            order.status === "claimed"
                              ? "bg-emerald-500/20 text-emerald-300"
                              : order.status === "ready"
                              ? "bg-sky-500/20 text-sky-300"
                              : "bg-amber-500/20 text-amber-300"
                          }`}
                        >
                          {order.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-3 py-3">
                        {order.status === "pending" ? (
                          <button
                            onClick={() => {
                              setOrders(prev =>
                                prev.map(o => (o.id === order.id ? { ...o, status: "ready" } : o))
                              );
                            }}
                            className="bg-sky-600 hover:bg-sky-500 text-white font-sans px-2.5 py-1 rounded text-[11px]"
                          >
                            Mark Ready
                          </button>
                        ) : (
                          <button
                            onClick={() => copyToClipboard(order.claim_code, order.claim_code)}
                            className="text-slate-400 hover:text-slate-200 font-sans flex items-center gap-1 text-[11px]"
                          >
                            <Copy className="w-3 h-3" /> Copy Code
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
