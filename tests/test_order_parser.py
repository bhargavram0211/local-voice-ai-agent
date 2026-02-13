"""Unit tests for order_parser module."""

import pytest

from conversation_state import create_initial_state
from order_parser import (
    ParsedTurn,
    create_order_item_from_menu_item,
    extract_order_type,
    extract_quantity_for_item,
    extract_spice_level,
    extract_table_or_name,
    merge_parsed_turn_into_order,
    parse_llm_response,
)
from order_structure import OrderItem


# Minimal menu for tests: Main Courses (spice), Breads (no spice), Biryanis (spice)
_SAMPLE_MENU = {
    "restaurant_name": "Spice Garden",
    "tax_rate": 8.5,
    "categories": [
        {
            "name": "Main Courses",
            "allows_spice_customization": True,
            "items": [
                {"id": "butter_chicken", "name": "Butter Chicken", "price": 14.99},
            ],
        },
        {
            "name": "Breads",
            "allows_spice_customization": False,
            "items": [
                {"id": "garlic_naan", "name": "Garlic Naan", "price": 3.99},
            ],
        },
        {
            "name": "Biryanis & Pulav",
            "allows_spice_customization": True,
            "items": [
                {"id": "chicken_biryani", "name": "Chicken Biryani", "price": 13.99},
            ],
        },
    ],
}


def test_item_and_quantity_two_butter_chicken_one_naan() -> None:
    """I'd like two butter chicken and one garlic naan -> 2 items with correct quantities."""
    state = create_initial_state()
    parsed = parse_llm_response(
        "I'd like two butter chicken and one garlic naan",
        _SAMPLE_MENU,
        state,
    )
    assert len(parsed.new_items) == 2
    by_name = {it.name: it for it in parsed.new_items}
    assert "Butter Chicken" in by_name
    assert by_name["Butter Chicken"].quantity == 2
    assert by_name["Butter Chicken"].item_total == pytest.approx(29.98)
    assert "Garlic Naan" in by_name
    assert by_name["Garlic Naan"].quantity == 1
    assert by_name["Garlic Naan"].item_total == pytest.approx(3.99)


def test_quantity_default_one() -> None:
    """No explicit quantity -> default 1."""
    state = create_initial_state()
    parsed = parse_llm_response("I want butter chicken", _SAMPLE_MENU, state)
    assert len(parsed.new_items) == 1
    assert parsed.new_items[0].quantity == 1
    assert parsed.new_items[0].name == "Butter Chicken"


def test_quantity_two_when_transcript_spelling_differs() -> None:
    """Quantity extracted when STT spells item differently (e.g. Gagar vs Gajar)."""
    assert extract_quantity_for_item("two gagar halwa", "Gajar Halwa") == 2
    assert extract_quantity_for_item("I'd like two gajar halwa", "Gajar Halwa") == 2


def test_spice_level_indian_spicy() -> None:
    """Make the butter chicken Indian spicy -> spice_level Indian Spicy."""
    state = create_initial_state()
    parsed = parse_llm_response(
        "Make the butter chicken Indian spicy",
        _SAMPLE_MENU,
        state,
    )
    assert len(parsed.new_items) == 1
    assert parsed.new_items[0].spice_level == "Indian Spicy"


def test_spice_level_medium_biryani() -> None:
    """Medium spice for the biryani -> spice for biryani; breads/desserts have no spice."""
    state = create_initial_state()
    parsed = parse_llm_response(
        "One chicken biryani medium spice",
        _SAMPLE_MENU,
        state,
    )
    assert len(parsed.new_items) == 1
    assert parsed.new_items[0].name == "Chicken Biryani"
    assert parsed.new_items[0].spice_level == "Medium"


def test_spice_level_none_for_breads() -> None:
    """Garlic naan has no spice customization."""
    state = create_initial_state()
    parsed = parse_llm_response(
        "Two garlic naan",
        _SAMPLE_MENU,
        state,
    )
    assert len(parsed.new_items) == 1
    assert parsed.new_items[0].spice_level is None


def test_order_type_dine_in_table_5() -> None:
    """We are dining in at table 5 -> order_type dine_in, table_or_name Table 5."""
    state = create_initial_state()
    parsed = parse_llm_response(
        "We are dining in at table 5",
        _SAMPLE_MENU,
        state,
    )
    assert parsed.updated_order_type == "dine_in"
    assert parsed.updated_table_or_name == "Table 5"


def test_order_type_takeout_for_bhargav() -> None:
    """This is takeout for Bhargav -> order_type takeout, table_or_name contains Bhargav."""
    state = create_initial_state()
    parsed = parse_llm_response(
        "This is takeout for Bhargav",
        _SAMPLE_MENU,
        state,
    )
    assert parsed.updated_order_type == "takeout"
    assert parsed.updated_table_or_name is not None
    assert "Bhargav" in parsed.updated_table_or_name


def test_full_parsed_turn_and_merge() -> None:
    """Dining in at table 3, two chicken biryanis Indian spicy -> one OrderItem, merge creates Order with correct totals."""
    state = create_initial_state()
    text = "We're dining in at table 3. Two chicken biryani, Indian spicy."
    parsed = parse_llm_response(text, _SAMPLE_MENU, state)
    assert len(parsed.new_items) == 1
    assert parsed.new_items[0].id == "chicken_biryani"
    assert parsed.new_items[0].quantity == 2
    assert parsed.new_items[0].spice_level == "Indian Spicy"
    assert parsed.updated_order_type == "dine_in"
    assert parsed.updated_table_or_name == "Table 3"

    order = merge_parsed_turn_into_order(None, parsed, _SAMPLE_MENU, 8.5)
    assert order.restaurant_name == "Spice Garden"
    assert order.order_type == "dine_in"
    assert order.table_or_name == "Table 3"
    assert len(order.items) == 1
    assert order.items[0].item_total == pytest.approx(27.98)
    assert order.subtotal == pytest.approx(27.98)
    assert order.tax == pytest.approx(2.38)
    assert order.total == pytest.approx(30.36)


def test_unknown_items_ignored() -> None:
    """Unknown items are not matched."""
    state = create_initial_state()
    parsed = parse_llm_response(
        "I want pizza and sushi",
        _SAMPLE_MENU,
        state,
    )
    assert len(parsed.new_items) == 0


def test_extract_spice_last_wins() -> None:
    """Conflicting spice levels -> last in text wins (or most specific)."""
    assert extract_spice_level("mild no wait make it indian spicy") == "Indian Spicy"
    assert extract_spice_level("medium spice") == "Medium"


def test_extract_order_type_ambiguous_none() -> None:
    """No clear dine_in/takeout phrase -> None."""
    assert extract_order_type("I'm hungry") is None
    assert extract_order_type("Just some naan") is None


def test_create_order_item_from_menu_item() -> None:
    """create_order_item_from_menu_item fills all fields."""
    item = create_order_item_from_menu_item(
        {"id": "x", "name": "Item X", "price": 10.0},
        "Mains",
        2,
        "Medium",
    )
    assert item.id == "x"
    assert item.name == "Item X"
    assert item.category == "Mains"
    assert item.quantity == 2
    assert item.spice_level == "Medium"
    assert item.price == 10.0
    assert item.item_total == 20.0


def test_merge_into_existing_order() -> None:
    """merge_parsed_turn_into_order appends to existing order and updates type/table."""
    state = create_initial_state()
    parsed1 = parse_llm_response("One butter chicken", _SAMPLE_MENU, state)
    order = merge_parsed_turn_into_order(None, parsed1, _SAMPLE_MENU, 8.5)
    assert len(order.items) == 1

    parsed2 = parse_llm_response("And one garlic naan", _SAMPLE_MENU, state)
    order = merge_parsed_turn_into_order(order, parsed2, _SAMPLE_MENU, 8.5)
    assert len(order.items) == 2
    assert order.subtotal == pytest.approx(14.99 + 3.99)
    assert order.tax_rate == 8.5
