"""
Finite State Machine (FSM) definitions for Admin workflows.
"""

from aiogram.fsm.state import State, StatesGroup


class OrderCreationFSM(StatesGroup):
    """FSM for step-by-step admin digital product order creation."""
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
    """FSM for admin replying to a customer's 2FA / OTP verification code request."""
    waiting_for_otp_code = State()
