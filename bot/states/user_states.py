"""
Finite State Machine (FSM) definitions for Customer/User workflows.
"""

from aiogram.fsm.state import State, StatesGroup


class ClaimOrderFSM(StatesGroup):
    """FSM for customer entering unique claim/tracking code."""
    waiting_for_claim_code = State()
