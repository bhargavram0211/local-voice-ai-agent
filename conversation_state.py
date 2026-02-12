"""Conversation state for the restaurant order-taking flow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from order_structure import Order


class ConversationStage(str, Enum):
    """Stage of the order-taking conversation."""

    GREETING = "greeting"
    ORDER_TYPE = "order_type"
    ORDERING = "ordering"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"


@dataclass
class ConversationState:
    """Current state of the order-taking conversation."""

    order: "Order | None"
    order_type: str | None  # "dine_in" | "takeout" | None
    table_or_name: str
    stage: ConversationStage
    current_item_id: str | None = None  # item we're currently confirming


def create_initial_state() -> ConversationState:
    """Create a new conversation state at the greeting stage."""
    return ConversationState(
        order=None,
        order_type=None,
        table_or_name="",
        stage=ConversationStage.GREETING,
        current_item_id=None,
    )


def reset_state() -> ConversationState:
    """Return a fresh state (same as initial). For starting a new order."""
    return create_initial_state()
