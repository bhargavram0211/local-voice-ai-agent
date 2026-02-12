"""Unit tests for restaurant_prompts module."""

import pytest

from conversation_state import ConversationStage, ConversationState, create_initial_state
from order_structure import Order, OrderItem
from restaurant_prompts import (
    build_system_prompt,
    get_base_system_prompt,
    get_refusal_message,
    is_off_topic,
)


def test_get_base_system_prompt_contains_restaurant_name() -> None:
    """Test get_base_system_prompt includes restaurant name and key instructions."""
    prompt = get_base_system_prompt("Spice Garden")
    assert "Spice Garden" in prompt
    assert "voice assistant" in prompt
    assert "dine-in" in prompt or "takeout" in prompt
    assert "spice" in prompt.lower()
    assert "price" in prompt.lower()
    assert "emojis" in prompt or "markdown" in prompt


def test_build_system_prompt_empty_order() -> None:
    """Test build_system_prompt with no order includes menu summary."""
    menu = {
        "restaurant_name": "Test Restaurant",
        "tax_rate": 8.5,
        "categories": [
            {
                "name": "Appetizers",
                "allows_spice_customization": True,
                "items": [
                    {"id": "samosa", "name": "Vegetable Samosa", "price": 4.99},
                ],
            },
        ],
    }
    state = create_initial_state()
    prompt = build_system_prompt(menu, state)
    assert "Test Restaurant" in prompt
    assert "Vegetable Samosa" in prompt
    assert "4.99" in prompt or "5" in prompt
    assert "Current order: (none yet)" in prompt
    assert "greeting" in prompt.lower()


def test_build_system_prompt_with_order() -> None:
    """Test build_system_prompt with sample order includes order summary."""
    menu = {
        "restaurant_name": "Spice Garden",
        "tax_rate": 8.5,
        "categories": [],
    }
    items = [
        OrderItem("butter_chicken", "Butter Chicken", "Main Courses", 2, "Medium", 14.99, 29.98),
    ]
    order = Order(
        order_id="ord_1",
        restaurant_name="Spice Garden",
        order_type="dine_in",
        table_or_name="Table 3",
        items=items,
        subtotal=29.98,
        tax_rate=8.5,
        tax=2.55,
        total=32.53,
        timestamp="2026-02-12T12:00:00Z",
    )
    state = ConversationState(
        order=order,
        order_type="dine_in",
        table_or_name="Table 3",
        stage=ConversationStage.ORDERING,
        current_item_id=None,
    )
    prompt = build_system_prompt(menu, state)
    assert "Butter Chicken" in prompt
    assert "29.98" in prompt or "30" in prompt
    assert "Subtotal" in prompt or "total" in prompt
    assert "ordering" in prompt.lower()


def test_is_off_topic_refuses_general_knowledge() -> None:
    """Test is_off_topic returns True for general knowledge questions."""
    assert is_off_topic("What's the capital of France?") is True
    assert is_off_topic("What is the capital of India?") is True


def test_is_off_topic_refuses_creative_requests() -> None:
    """Test is_off_topic returns True for write a poem etc."""
    assert is_off_topic("Write me a poem") is True
    assert is_off_topic("Tell me a joke") is True


def test_is_off_topic_allows_ordering_phrases() -> None:
    """Test is_off_topic returns False for ordering-related speech."""
    assert is_off_topic("I'd like butter chicken") is False
    assert is_off_topic("Table 5") is False
    assert is_off_topic("Medium spice") is False
    assert is_off_topic("Two naan please") is False


def test_is_off_topic_allows_greetings() -> None:
    """Test is_off_topic returns False for hi, thanks, ok."""
    assert is_off_topic("Hi") is False
    assert is_off_topic("Hello") is False
    assert is_off_topic("Thanks") is False
    assert is_off_topic("Ok") is False
    assert is_off_topic("Sure") is False


def test_is_off_topic_empty_or_whitespace() -> None:
    """Test is_off_topic returns False for empty input."""
    assert is_off_topic("") is False
    assert is_off_topic("   ") is False


def test_get_refusal_message_default() -> None:
    """Test get_refusal_message returns non-empty string."""
    msg = get_refusal_message()
    assert isinstance(msg, str)
    assert len(msg) > 0
    assert "order" in msg.lower()
    assert "our restaurant" in msg


def test_get_refusal_message_with_restaurant_name() -> None:
    """Test get_refusal_message includes restaurant name when provided."""
    msg = get_refusal_message("Spice Garden")
    assert "Spice Garden" in msg
    assert "order" in msg.lower()
