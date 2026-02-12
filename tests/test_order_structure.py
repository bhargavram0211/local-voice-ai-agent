"""Unit tests for order_structure module."""

import json

import pytest

from order_structure import (
    Order,
    OrderItem,
    generate_order_id,
    calculate_order_totals,
    order_to_dict,
    order_to_json,
)


def test_order_item_with_spice_level() -> None:
    """Test OrderItem creation with spice_level."""
    item = OrderItem(
        id="butter_chicken",
        name="Butter Chicken",
        category="Main Courses",
        quantity=2,
        spice_level="Medium",
        price=14.99,
        item_total=29.98,
    )
    assert item.spice_level == "Medium"
    assert item.item_total == 29.98


def test_order_item_without_spice_level() -> None:
    """Test OrderItem creation without spice_level (Breads/Dessert)."""
    item = OrderItem(
        id="gulab_jamun",
        name="Gulab Jamun",
        category="Dessert",
        quantity=1,
        spice_level=None,
        price=5.99,
        item_total=5.99,
    )
    assert item.spice_level is None


def test_order_creation_with_multiple_items() -> None:
    """Test Order creation with multiple items."""
    items = [
        OrderItem("samosa", "Vegetable Samosa", "Appetizers", 2, "Spicy", 4.99, 9.98),
        OrderItem("naan", "Garlic Naan", "Breads", 2, None, 3.99, 7.98),
    ]
    order = Order(
        order_id="order_20260212_120000",
        restaurant_name="Spice Garden",
        order_type="dine_in",
        table_or_name="Table 5",
        items=items,
        subtotal=17.96,
        tax_rate=8.5,
        tax=1.53,
        total=19.49,
        timestamp="2026-02-12T12:00:00Z",
    )
    assert len(order.items) == 2
    assert order.subtotal == 17.96
    assert order.total == 19.49


def test_calculate_order_totals_accuracy() -> None:
    """Test calculate_order_totals returns correct subtotal, tax, total."""
    items = [
        OrderItem("a", "A", "Cat", 1, None, 10.0, 10.0),
        OrderItem("b", "B", "Cat", 2, None, 5.0, 10.0),
    ]
    subtotal, tax, total = calculate_order_totals(items, 10.0)
    assert subtotal == 20.0
    assert tax == 2.0
    assert total == 22.0


def test_calculate_order_totals_rounding() -> None:
    """Test tax and total are rounded to 2 decimal places."""
    items = [
        OrderItem("a", "A", "Cat", 1, None, 10.99, 10.99),
    ]
    subtotal, tax, total = calculate_order_totals(items, 8.5)
    assert subtotal == 10.99
    assert tax == 0.93  # 10.99 * 0.085 = 0.93415 -> 0.93
    assert total == 11.92


def test_order_to_dict() -> None:
    """Test order_to_dict serialization."""
    items = [
        OrderItem("x", "Item X", "Cat", 1, "Mild", 5.0, 5.0),
    ]
    order = Order(
        order_id="ord_1",
        restaurant_name="Test",
        order_type="takeout",
        table_or_name="John",
        items=items,
        subtotal=5.0,
        tax_rate=8.5,
        tax=0.43,
        total=5.43,
        timestamp="2026-02-12T12:00:00Z",
    )
    d = order_to_dict(order)
    assert d["order_id"] == "ord_1"
    assert d["restaurant_name"] == "Test"
    assert d["order_type"] == "takeout"
    assert d["table_or_name"] == "John"
    assert len(d["items"]) == 1
    assert d["items"][0]["id"] == "x"
    assert d["items"][0]["spice_level"] == "Mild"
    assert d["subtotal"] == 5.0
    assert d["tax"] == 0.43
    assert d["total"] == 5.43
    assert d["timestamp"] == "2026-02-12T12:00:00Z"


def test_order_to_json() -> None:
    """Test order_to_json produces valid JSON."""
    items = [
        OrderItem("y", "Y", "Cat", 1, None, 1.0, 1.0),
    ]
    order = Order(
        order_id="ord_2",
        restaurant_name="R",
        order_type="dine_in",
        table_or_name="Table 1",
        items=items,
        subtotal=1.0,
        tax_rate=0,
        tax=0.0,
        total=1.0,
        timestamp="2026-02-12T12:00:00Z",
    )
    s = order_to_json(order)
    parsed = json.loads(s)
    assert parsed["order_id"] == "ord_2"
    assert parsed["items"][0]["quantity"] == 1


def test_generate_order_id_format() -> None:
    """Test generate_order_id returns expected format."""
    oid = generate_order_id()
    assert oid.startswith("order_")
    parts = oid.replace("order_", "").split("_")
    assert len(parts) == 2
    assert len(parts[0]) == 8  # YYYYMMDD
    assert len(parts[1]) == 6  # HHMMSS


def test_calculate_order_totals_empty_list() -> None:
    """Test calculate_order_totals with empty items."""
    subtotal, tax, total = calculate_order_totals([], 10.0)
    assert subtotal == 0.0
    assert tax == 0.0
    assert total == 0.0
