"""Unit tests for conversation_state module."""

import pytest

from conversation_state import (
    ConversationStage,
    ConversationState,
    create_initial_state,
    reset_state,
)
from order_structure import Order, OrderItem


def test_create_initial_state() -> None:
    """Test create_initial_state returns greeting stage and no order."""
    state = create_initial_state()
    assert state.order is None
    assert state.order_type is None
    assert state.table_or_name == ""
    assert state.stage == ConversationStage.GREETING
    assert state.current_item_id is None


def test_reset_state() -> None:
    """Test reset_state returns same as initial."""
    state = reset_state()
    assert state.order is None
    assert state.order_type is None
    assert state.table_or_name == ""
    assert state.stage == ConversationStage.GREETING


def test_state_holds_order() -> None:
    """Test that ConversationState can hold an Order from order_structure."""
    items = [
        OrderItem("samosa", "Vegetable Samosa", "Appetizers", 1, "Medium", 4.99, 4.99),
    ]
    order = Order(
        order_id="order_20260212_120000",
        restaurant_name="Spice Garden",
        order_type="dine_in",
        table_or_name="Table 5",
        items=items,
        subtotal=4.99,
        tax_rate=8.5,
        tax=0.42,
        total=5.41,
        timestamp="2026-02-12T12:00:00Z",
    )
    state = ConversationState(
        order=order,
        order_type="dine_in",
        table_or_name="Table 5",
        stage=ConversationStage.ORDERING,
        current_item_id="samosa",
    )
    assert state.order is not None
    assert state.order.restaurant_name == "Spice Garden"
    assert len(state.order.items) == 1
    assert state.order.items[0].name == "Vegetable Samosa"
    assert state.stage == ConversationStage.ORDERING
    assert state.current_item_id == "samosa"


def test_stage_enum_values() -> None:
    """Test ConversationStage has expected values."""
    assert ConversationStage.GREETING.value == "greeting"
    assert ConversationStage.ORDER_TYPE.value == "order_type"
    assert ConversationStage.ORDERING.value == "ordering"
    assert ConversationStage.CONFIRMATION.value == "confirmation"
    assert ConversationStage.COMPLETED.value == "completed"
