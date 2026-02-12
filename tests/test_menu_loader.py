"""Unit tests for menu_loader module."""

import json
import tempfile
from pathlib import Path

import pytest

from menu_loader import (
    load_menu,
    get_item_by_id,
    get_items_by_category,
    get_all_items,
    calculate_price_with_tax,
    validate_menu_structure,
    get_category_info,
)


def test_load_menu_valid(tmp_path: Path) -> None:
    """Test loading valid menu.json."""
    menu_data = {
        "restaurant_name": "Test",
        "tax_rate": 8.5,
        "categories": [
            {
                "name": "Appetizers",
                "allows_spice_customization": True,
                "items": [
                    {"id": "samosa", "name": "Samosa", "description": "Yum", "price": 4.99},
                ],
            },
        ],
    }
    path = tmp_path / "menu.json"
    path.write_text(json.dumps(menu_data), encoding="utf-8")
    loaded = load_menu(str(path))
    assert loaded["restaurant_name"] == "Test"
    assert loaded["tax_rate"] == 8.5
    assert len(loaded["categories"]) == 1
    assert loaded["categories"][0]["items"][0]["id"] == "samosa"


def test_load_menu_missing_file() -> None:
    """Test loading invalid/missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Menu file not found"):
        load_menu("/nonexistent/menu.json")


def test_get_item_by_id_found() -> None:
    """Test get_item_by_id when item exists."""
    menu = {
        "categories": [
            {
                "name": "Mains",
                "items": [
                    {"id": "butter_chicken", "name": "Butter Chicken", "price": 14.99},
                ],
            },
        ],
    }
    item = get_item_by_id(menu, "butter_chicken")
    assert item is not None
    assert item["name"] == "Butter Chicken"
    assert item["price"] == 14.99


def test_get_item_by_id_not_found() -> None:
    """Test get_item_by_id when item does not exist."""
    menu = {"categories": [{"name": "Mains", "items": []}]}
    assert get_item_by_id(menu, "nonexistent") is None


def test_get_items_by_category_found() -> None:
    """Test get_items_by_category returns items."""
    menu = {
        "categories": [
            {
                "name": "Breads",
                "items": [
                    {"id": "naan", "name": "Naan", "price": 3.99},
                    {"id": "roti", "name": "Roti", "price": 2.99},
                ],
            },
        ],
    }
    items = get_items_by_category(menu, "Breads")
    assert len(items) == 2
    assert items[0]["id"] == "naan"
    assert items[1]["id"] == "roti"


def test_get_items_by_category_not_found() -> None:
    """Test get_items_by_category returns empty list for unknown category."""
    menu = {"categories": [{"name": "Mains", "items": []}]}
    assert get_items_by_category(menu, "Desserts") == []


def test_calculate_price_with_tax() -> None:
    """Test calculate_price_with_tax with various rates."""
    assert calculate_price_with_tax(10.0, 0) == 10.0
    assert calculate_price_with_tax(100.0, 10) == 110.0
    assert calculate_price_with_tax(10.0, 8.5) == 10.85
    assert calculate_price_with_tax(4.99, 8.5) == 5.41


def test_validate_menu_structure_valid() -> None:
    """Test validate_menu_structure accepts valid menu."""
    menu = {
        "restaurant_name": "X",
        "tax_rate": 8.5,
        "categories": [
            {
                "name": "A",
                "allows_spice_customization": False,
                "items": [{"id": "i1", "name": "Item", "price": 5.0}],
            },
        ],
    }
    valid, msg = validate_menu_structure(menu)
    assert valid is True
    assert msg == ""


def test_validate_menu_structure_missing_restaurant_name() -> None:
    """Test validate_menu_structure rejects missing restaurant_name."""
    menu = {"tax_rate": 8.5, "categories": []}
    valid, msg = validate_menu_structure(menu)
    assert valid is False
    assert "restaurant_name" in msg


def test_validate_menu_structure_missing_tax_rate() -> None:
    """Test validate_menu_structure rejects missing tax_rate."""
    menu = {"restaurant_name": "X", "categories": []}
    valid, msg = validate_menu_structure(menu)
    assert valid is False
    assert "tax_rate" in msg


def test_validate_menu_structure_negative_tax() -> None:
    """Test validate_menu_structure rejects negative tax_rate."""
    menu = {"restaurant_name": "X", "tax_rate": -1, "categories": []}
    valid, msg = validate_menu_structure(menu)
    assert valid is False
    assert "tax_rate" in msg or "non-negative" in msg


def test_validate_menu_structure_duplicate_item_id() -> None:
    """Test validate_menu_structure rejects duplicate item ids."""
    menu = {
        "restaurant_name": "X",
        "tax_rate": 8.5,
        "categories": [
            {
                "name": "A",
                "allows_spice_customization": False,
                "items": [
                    {"id": "dup", "name": "One", "price": 1.0},
                    {"id": "dup", "name": "Two", "price": 2.0},
                ],
            },
        ],
    }
    valid, msg = validate_menu_structure(menu)
    assert valid is False
    assert "Duplicate" in msg or "dup" in msg


def test_get_category_info_found() -> None:
    """Test get_category_info returns metadata including spice flag."""
    menu = {
        "categories": [
            {"name": "Appetizers", "allows_spice_customization": True, "items": []},
            {"name": "Breads", "allows_spice_customization": False, "items": []},
        ],
    }
    info = get_category_info(menu, "Appetizers")
    assert info is not None
    assert info["name"] == "Appetizers"
    assert info["allows_spice_customization"] is True

    info2 = get_category_info(menu, "Breads")
    assert info2 is not None
    assert info2["allows_spice_customization"] is False


def test_get_category_info_not_found() -> None:
    """Test get_category_info returns None for unknown category."""
    menu = {"categories": [{"name": "Mains", "items": []}]}
    assert get_category_info(menu, "Desserts") is None


def test_get_all_items() -> None:
    """Test get_all_items returns flattened list."""
    menu = {
        "categories": [
            {"name": "A", "items": [{"id": "1", "name": "One", "price": 1.0}]},
            {"name": "B", "items": [{"id": "2", "name": "Two", "price": 2.0}]},
        ],
    }
    items = get_all_items(menu)
    assert len(items) == 2
    assert items[0]["id"] == "1"
    assert items[1]["id"] == "2"
