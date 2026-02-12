"""Order and order item data models for restaurant orders."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json


@dataclass
class OrderItem:
    """A single line item in an order."""

    id: str
    name: str
    category: str
    quantity: int
    spice_level: str | None  # "Mild" | "Medium" | "Spicy" | "Indian Spicy" | None
    price: float
    item_total: float  # quantity * price


@dataclass
class Order:
    """Restaurant order with items and totals."""

    order_id: str
    restaurant_name: str
    order_type: str  # "dine_in" | "takeout"
    table_or_name: str
    items: list[OrderItem]
    subtotal: float
    tax_rate: float
    tax: float
    total: float
    timestamp: str  # ISO format datetime string


def generate_order_id() -> str:
    """Generate unique order ID (e.g., order_20260212_182345)."""
    now = datetime.now(timezone.utc)
    return f"order_{now.strftime('%Y%m%d_%H%M%S')}"


def calculate_order_totals(
    items: list[OrderItem], tax_rate: float
) -> tuple[float, float, float]:
    """Calculate (subtotal, tax, total). All rounded to 2 decimal places."""
    subtotal = round(sum(it.item_total for it in items), 2)
    tax = round(subtotal * (tax_rate / 100), 2)
    total = round(subtotal + tax, 2)
    return subtotal, tax, total


def order_to_dict(order: Order) -> dict:
    """Convert Order to dictionary for JSON serialization."""
    return {
        "order_id": order.order_id,
        "restaurant_name": order.restaurant_name,
        "order_type": order.order_type,
        "table_or_name": order.table_or_name,
        "items": [
            {
                "id": it.id,
                "name": it.name,
                "category": it.category,
                "quantity": it.quantity,
                "spice_level": it.spice_level,
                "price": it.price,
                "item_total": it.item_total,
            }
            for it in order.items
        ],
        "subtotal": order.subtotal,
        "tax_rate": order.tax_rate,
        "tax": order.tax,
        "total": order.total,
        "timestamp": order.timestamp,
    }


def order_to_json(order: Order) -> str:
    """Convert Order to JSON string."""
    return json.dumps(order_to_dict(order), indent=2)
