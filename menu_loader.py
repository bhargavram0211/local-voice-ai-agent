"""Load and query menu data from JSON."""

import json
from pathlib import Path


def load_menu(file_path: str) -> dict:
    """Load menu from JSON file. Returns dict. Raises on missing file or invalid JSON."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Menu file not found: {file_path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_item_by_id(menu: dict, item_id: str) -> dict | None:
    """Find menu item by ID. Returns item dict or None."""
    for cat in menu.get("categories", []):
        for item in cat.get("items", []):
            if item.get("id") == item_id:
                return item
    return None


def get_items_by_category(menu: dict, category_name: str) -> list[dict]:
    """Get all items in a category. Returns list of item dicts (empty if category not found)."""
    for cat in menu.get("categories", []):
        if cat.get("name") == category_name:
            return list(cat.get("items", []))
    return []


def get_all_items(menu: dict) -> list[dict]:
    """Get flattened list of all menu items."""
    items = []
    for cat in menu.get("categories", []):
        for item in cat.get("items", []):
            items.append(item)
    return items


def calculate_price_with_tax(price: float, tax_rate: float) -> float:
    """Calculate price including tax. Rounds to 2 decimal places."""
    return round(price * (1 + tax_rate / 100), 2)


def validate_menu_structure(menu: dict) -> tuple[bool, str]:
    """
    Validate menu JSON structure.
    Returns (is_valid, error_message). error_message is empty when valid.
    """
    if not isinstance(menu, dict):
        return False, "Menu must be a dictionary"

    if "restaurant_name" not in menu:
        return False, "Missing 'restaurant_name'"
    if "tax_rate" not in menu:
        return False, "Missing 'tax_rate'"
    if "categories" not in menu:
        return False, "Missing 'categories'"

    tax_rate = menu["tax_rate"]
    if not isinstance(tax_rate, (int, float)) or tax_rate < 0:
        return False, "tax_rate must be a non-negative number"

    categories = menu["categories"]
    if not isinstance(categories, list):
        return False, "'categories' must be a list"

    seen_ids: set[str] = set()
    for cat in categories:
        if not isinstance(cat, dict):
            return False, "Each category must be a dictionary"
        if "name" not in cat:
            return False, "Each category must have 'name'"
        if "allows_spice_customization" not in cat:
            return False, "Each category must have 'allows_spice_customization'"
        if "items" not in cat:
            return False, "Each category must have 'items'"
        items = cat["items"]
        if not isinstance(items, list):
            return False, "Category 'items' must be a list"
        for item in items:
            if not isinstance(item, dict):
                return False, "Each menu item must be a dictionary"
            if "id" not in item:
                return False, "Each item must have 'id'"
            if "name" not in item:
                return False, "Each item must have 'name'"
            if "price" not in item:
                return False, "Each item must have 'price'"
            iid = item["id"]
            if iid in seen_ids:
                return False, f"Duplicate item id: {iid}"
            seen_ids.add(iid)
            price = item["price"]
            if not isinstance(price, (int, float)) or price < 0:
                return False, f"Item price must be non-negative number: {iid}"

    return True, ""


def get_category_info(menu: dict, category_name: str) -> dict | None:
    """Get category metadata (name, allows_spice_customization). Returns None if not found."""
    for cat in menu.get("categories", []):
        if cat.get("name") == category_name:
            return {
                "name": cat["name"],
                "allows_spice_customization": cat.get("allows_spice_customization", False),
            }
    return None
