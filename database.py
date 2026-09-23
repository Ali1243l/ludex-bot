"""
Database Module for Digital Product Delivery Bot.
Powered by SQLAlchemy 2.0 Async engine (compatible with SQLite/aiosqlite and PostgreSQL/asyncpg).
"""

import string
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    select,
    func,
    update,
    desc
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import declarative_base, relationship

from config import settings

Base = declarative_base()


class User(Base):
    """Registered Telegram user profile."""
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    orders = relationship("Order", back_populates="customer", foreign_keys="Order.customer_telegram_id")

    def __repr__(self) -> str:
        return f"<User id={self.telegram_id} username=@{self.username}>"


class Order(Base):
    """Digital product delivery order."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_code = Column(String(32), unique=True, index=True, nullable=False)
    customer_name = Column(String(128), nullable=False)
    customer_username = Column(String(64), nullable=True)
    customer_telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=True, index=True)
    
    product_name = Column(String(128), nullable=False)
    product_type = Column(String(64), default="Account", nullable=False)  # Account, Subscription, License Key, Combo
    cost_price = Column(Float, default=0.0, nullable=False)
    selling_price = Column(Float, default=0.0, nullable=False)
    
    account_details = Column(Text, nullable=False)
    activation_guide = Column(Text, nullable=True)
    
    # Status: 'pending' (preparing), 'ready' (deliverable upon claim), 'claimed' (delivered to customer), 'completed'
    status = Column(String(32), default="ready", nullable=False, index=True)
    
    duration_days = Column(Integer, nullable=True)  # For subscription expiry calculation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("User", back_populates="orders", foreign_keys=[customer_telegram_id])
    two_factor_requests = relationship("TwoFactorRequest", back_populates="order", cascade="all, delete-orphan")

    @property
    def profit(self) -> float:
        return round(self.selling_price - self.cost_price, 2)

    @property
    def remaining_days(self) -> Optional[int]:
        if not self.expiry_date:
            return None
        delta = self.expiry_date - datetime.utcnow()
        return max(0, delta.days)


class TwoFactorRequest(Base):
    """User 2FA / OTP verification code request."""
    __tablename__ = "two_factor_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    telegram_id = Column(BigInteger, nullable=False, index=True)
    customer_name = Column(String(128), nullable=True)
    product_name = Column(String(128), nullable=True)
    
    # Status: 'pending', 'answered', 'rejected'
    status = Column(String(32), default="pending", nullable=False, index=True)
    code_reply = Column(String(64), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    replied_at = Column(DateTime, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="two_factor_requests")


# ------------------------------------------------------------------------------
# Engine & Session Factory
# ------------------------------------------------------------------------------
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ------------------------------------------------------------------------------
# CRUD & Business Helpers
# ------------------------------------------------------------------------------

def generate_random_claim_code(prefix: str = "DLV") -> str:
    """Generate a clean, high-entropy unique claim code like DLV-9A82-KC74."""
    chars = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters (0, O, 1, I)
    clean_chars = "".join([c for c in chars if c not in "0O1I"])
    chunk1 = "".join(secrets.choice(clean_chars) for _ in range(4))
    chunk2 = "".join(secrets.choice(clean_chars) for _ in range(4))
    return f"{prefix}-{chunk1}-{chunk2}"


async def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    full_name: Optional[str] = None
) -> User:
    """Find or register a user upon bot interaction."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Update username / full_name if changed
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                updated = True
            if updated:
                await session.commit()
                await session.refresh(user)
        return user


async def create_order(
    customer_name: str,
    customer_username: Optional[str],
    product_name: str,
    product_type: str,
    cost_price: float,
    selling_price: float,
    account_details: str,
    activation_guide: Optional[str] = None,
    status: str = "ready",
    duration_days: Optional[int] = None,
    customer_telegram_id: Optional[int] = None
) -> Order:
    """Create a new digital order and assign a unique claim code."""
    async with AsyncSessionLocal() as session:
        # Loop until unique code is found
        while True:
            code = generate_random_claim_code()
            exists = await session.execute(select(Order).where(Order.claim_code == code))
            if not exists.scalar_one_or_none():
                break

        order = Order(
            claim_code=code,
            customer_name=customer_name,
            customer_username=customer_username.lstrip("@") if customer_username else None,
            customer_telegram_id=customer_telegram_id,
            product_name=product_name,
            product_type=product_type,
            cost_price=cost_price,
            selling_price=selling_price,
            account_details=account_details,
            activation_guide=activation_guide,
            status=status,
            duration_days=duration_days,
            created_at=datetime.utcnow()
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order


async def get_order_by_code(code: str) -> Optional[Order]:
    """Retrieve an order by its tracking/claim code (case-insensitive)."""
    cleaned_code = code.strip().upper()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.claim_code == cleaned_code))
        return result.scalar_one_or_none()


async def get_order_by_id(order_id: int) -> Optional[Order]:
    """Retrieve an order by internal database ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()


async def claim_order_for_user(
    order_id: int,
    user_id: int,
    username: Optional[str] = None
) -> Optional[Order]:
    """Link claimed order to customer and set expiry date if subscription."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            return None

        order.customer_telegram_id = user_id
        if username:
            order.customer_username = username.lstrip("@")
        
        # If ready, mark claimed and calculate expiry
        if order.status == "ready":
            order.status = "claimed"
            order.claimed_at = datetime.utcnow()
            if order.duration_days and order.duration_days > 0:
                order.expiry_date = datetime.utcnow() + timedelta(days=order.duration_days)

        await session.commit()
        await session.refresh(order)
        return order


async def update_order_status(order_id: int, new_status: str) -> Optional[Order]:
    """Update order status (e.g. from 'pending' to 'ready' or 'completed')."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            return None

        order.status = new_status
        if new_status == "ready" and order.customer_telegram_id:
            # If user already claimed while pending, now activate it
            order.status = "claimed"
            order.claimed_at = datetime.utcnow()
            if order.duration_days and order.duration_days > 0:
                order.expiry_date = datetime.utcnow() + timedelta(days=order.duration_days)

        await session.commit()
        await session.refresh(order)
        return order


async def get_user_orders(telegram_id: int) -> List[Order]:
    """Retrieve all orders owned or claimed by a user."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order)
            .where(Order.customer_telegram_id == telegram_id)
            .order_by(desc(Order.created_at))
        )
        return list(result.scalars().all())


async def get_admin_stats() -> Dict[str, Any]:
    """Calculate total sales, total costs, net profit, and counts for dashboard."""
    async with AsyncSessionLocal() as session:
        # Aggregate financial stats
        sales_cost = await session.execute(
            select(
                func.coalesce(func.sum(Order.selling_price), 0.0),
                func.coalesce(func.sum(Order.cost_price), 0.0),
                func.count(Order.id)
            )
        )
        total_sales, total_cost, total_orders = sales_cost.one()
        net_profit = total_sales - total_cost

        # Status breakdown
        pending_count = (await session.execute(
            select(func.count(Order.id)).where(Order.status == "pending")
        )).scalar() or 0

        ready_count = (await session.execute(
            select(func.count(Order.id)).where(Order.status == "ready")
        )).scalar() or 0

        claimed_count = (await session.execute(
            select(func.count(Order.id)).where(Order.status == "claimed")
        )).scalar() or 0

        # Users count
        total_users = (await session.execute(
            select(func.count(User.telegram_id))
        )).scalar() or 0

        # Pending 2FA requests
        pending_2fa = (await session.execute(
            select(func.count(TwoFactorRequest.id)).where(TwoFactorRequest.status == "pending")
        )).scalar() or 0

        return {
            "total_sales": round(float(total_sales), 2),
            "total_cost": round(float(total_cost), 2),
            "net_profit": round(float(net_profit), 2),
            "total_orders": int(total_orders),
            "pending_orders": int(pending_count),
            "ready_orders": int(ready_count),
            "claimed_orders": int(claimed_count),
            "total_users": int(total_users),
            "pending_2fa": int(pending_2fa)
        }


async def create_2fa_request(
    order_id: int,
    telegram_id: int,
    customer_name: Optional[str],
    product_name: Optional[str]
) -> TwoFactorRequest:
    """Create a 2FA/OTP login request from user to admin."""
    async with AsyncSessionLocal() as session:
        req = TwoFactorRequest(
            order_id=order_id,
            telegram_id=telegram_id,
            customer_name=customer_name,
            product_name=product_name,
            status="pending",
            created_at=datetime.utcnow()
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)
        return req


async def get_2fa_request(req_id: int) -> Optional[TwoFactorRequest]:
    """Retrieve 2FA request by ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TwoFactorRequest).where(TwoFactorRequest.id == req_id)
        )
        return result.scalar_one_or_none()


async def answer_2fa_request(req_id: int, code: str) -> Optional[TwoFactorRequest]:
    """Fulfill 2FA request with verification code."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TwoFactorRequest).where(TwoFactorRequest.id == req_id)
        )
        req = result.scalar_one_or_none()
        if not req:
            return None

        req.status = "answered"
        req.code_reply = code
        req.replied_at = datetime.utcnow()
        await session.commit()
        await session.refresh(req)
        return req
