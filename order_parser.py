"""Parse free-form text into structured order updates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from menu_loader import get_category_info
from order_structure import (
    Order,
    OrderItem,
    calculate_order_totals,
    generate_order_id,
)

if TYPE_CHECKING:
    from conversation_state import ConversationState


@dataclass
class ParsedTurn:
    """Order updates extracted from one turn of conversation."""

    new_items: list[OrderItem]
    updated_order_type: str | None  # "dine_in" | "takeout" | None
    updated_table_or_name: str | None
    notes: str | None = None


def normalize_text(s: str) -> str:
    """Lowercase, strip, collapse spaces."""
    return " ".join(s.lower().strip().split())


def tokenize(s: str) -> list[str]:
    """Basic whitespace tokenization."""
    return s.split()


# Word to number for quantity extraction
_QUANTITY_WORDS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "a": 1,
    "an": 1,
    "a couple": 2,
    "couple": 2,
    "a few": 3,
    "few": 3,
}

# Spice levels (order by specificity so we can pick "indian spicy" over "spicy")
_SPICE_LEVELS = ["mild", "medium", "spicy", "indian spicy"]
_SPICE_LEVEL_MAP = {s: s.title() if s != "indian spicy" else "Indian Spicy" for s in _SPICE_LEVELS}


def build_menu_index(menu: dict) -> list[tuple[dict, str]]:
    """Return list of (item_dict, category_name) for all menu items."""
    result = []
    for cat in menu.get("categories", []):
        cat_name = cat.get("name", "")
        for item in cat.get("items", []):
            result.append((item, cat_name))
    return result


def match_item_mentions(text: str, menu: dict) -> list[tuple[dict, str]]:
    """Find menu items mentioned in text. Return list of (item_dict, category_name). Prefer exact/near-exact name match."""
    norm = normalize_text(text)
    index = build_menu_index(menu)
    matched = []
    for item, cat_name in index:
        name = item.get("name", "")
        norm_name = normalize_text(name)
        if norm_name in norm:
            matched.append((item, cat_name))
    # Prefer longer names first so "Chicken Biryani" matches before "Chicken" if both exist
    matched.sort(key=lambda x: -len(x[0].get("name", "")))
    # Dedupe by item id (same item might match multiple ways)
    seen: set[str] = set()
    out = []
    for item, cat in matched:
        iid = item.get("id", "")
        if iid not in seen:
            seen.add(iid)
            out.append((item, cat))
    return out


def extract_quantity_for_item(text: str, item_name: str) -> int:
    """Extract quantity for an item from text. Default 1."""
    norm = normalize_text(text)
    # Number immediately before or after item name
    norm_name = normalize_text(item_name)
    # Pattern: "2 butter chicken" or "two butter chicken" or "butter chicken 2"
    for word, num in _QUANTITY_WORDS.items():
        if word in ("a", "an") and num == 1:
            continue
        if re.search(rf"\b{re.escape(word)}\s+{re.escape(norm_name)}", norm):
            return num
        if re.search(rf"{re.escape(norm_name)}\s+{re.escape(word)}\b", norm):
            return num
    # Digits
    m = re.search(rf"\b(\d+)\s+{re.escape(norm_name)}", norm)
    if m:
        return max(1, int(m.group(1)))
    m = re.search(rf"{re.escape(norm_name)}\s+(\d+)\b", norm)
    if m:
        return max(1, int(m.group(1)))
    return 1


def extract_spice_level(text: str) -> str | None:
    """Extract spice level from text. Return last/most specific match (e.g. Indian Spicy over Spicy)."""
    norm = normalize_text(text)
    found: list[str] = []
    for level in _SPICE_LEVELS:
        if level in norm:
            found.append(level)
    if not found:
        return None
    # Prefer "indian spicy" over "spicy"
    if "indian spicy" in found:
        return _SPICE_LEVEL_MAP["indian spicy"]
    return _SPICE_LEVEL_MAP[found[-1]]


def extract_order_type(text: str) -> str | None:
    """Extract dine_in or takeout from text."""
    norm = normalize_text(text)
    if any(x in norm for x in ["dine in", "dining in", "eat here", "dine-in"]):
        return "dine_in"
    if any(x in norm for x in ["takeout", "take out", "to go", "to-go", "pickup", "pick up"]):
        return "takeout"
    return None


def extract_table_or_name(text: str) -> str | None:
    """Extract table number or customer name."""
    norm = normalize_text(text)
    # Table 5, table 7
    m = re.search(r"\btable\s+(\d+)\b", norm)
    if m:
        return f"Table {m.group(1)}"
    # for John, under Bhargav
    m = re.search(r"\b(?:for|under)\s+([a-z]+)\b", norm)
    if m:
        return m.group(1).title()
    return None


def create_order_item_from_menu_item(
    menu_item: dict,
    category: str,
    quantity: int,
    spice_level: str | None,
) -> OrderItem:
    """Build an OrderItem from a menu item dict and quantity/spice."""
    price = float(menu_item.get("price", 0))
    item_total = round(quantity * price, 2)
    return OrderItem(
        id=menu_item.get("id", ""),
        name=menu_item.get("name", ""),
        category=category,
        quantity=quantity,
        spice_level=spice_level,
        price=price,
        item_total=item_total,
    )


def parse_llm_response(
    text: str,
    menu: dict,
    current_state: "ConversationState",
) -> ParsedTurn:
    """Parse one turn of text into order updates (items, order type, table/name)."""
    new_items: list[OrderItem] = []
    pairs = match_item_mentions(text, menu)
    spice = extract_spice_level(text)
    for item_dict, category in pairs:
        qty = extract_quantity_for_item(text, item_dict.get("name", ""))
        cat_info = get_category_info(menu, category)
        allow_spice = cat_info.get("allows_spice_customization", False) if cat_info else False
        item_spice = spice if allow_spice else None
        new_items.append(
            create_order_item_from_menu_item(item_dict, category, qty, item_spice)
        )

    return ParsedTurn(
        new_items=new_items,
        updated_order_type=extract_order_type(text),
        updated_table_or_name=extract_table_or_name(text),
        notes=None,
    )


def merge_parsed_turn_into_order(
    order: Order | None,
    parsed: ParsedTurn,
    menu: dict,
    tax_rate: float,
) -> Order:
    """Merge ParsedTurn into an existing Order or create a new one. Recalculates totals."""
    restaurant_name = menu.get("restaurant_name", "Restaurant")
    if order is None:
        order = Order(
            order_id=generate_order_id(),
            restaurant_name=restaurant_name,
            order_type="dine_in",
            table_or_name="",
            items=[],
            subtotal=0.0,
            tax_rate=tax_rate,
            tax=0.0,
            total=0.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    order.items = list(order.items) + list(parsed.new_items)
    if parsed.updated_order_type is not None:
        order.order_type = parsed.updated_order_type
    if parsed.updated_table_or_name is not None:
        order.table_or_name = parsed.updated_table_or_name
    subtotal, tax, total = calculate_order_totals(order.items, tax_rate)
    order.subtotal = subtotal
    order.tax = tax
    order.total = total
    return order
