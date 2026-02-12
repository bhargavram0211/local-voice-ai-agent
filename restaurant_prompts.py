"""Restaurant order-taking agent prompts and guardrail detection."""

from conversation_state import ConversationStage, ConversationState


def get_base_system_prompt(restaurant_name: str) -> str:
    """Return the base system prompt with restaurant identity and rules."""
    return f"""You are the voice assistant for {restaurant_name}. You take orders for dine-in and takeout.

Be friendly, professional, and concise. Your output will be spoken aloud, so do not use emojis or markdown bullets.

Rules:
- For each item that allows spice customization (Appetizers, Main Courses, Biryanis and Pulav), confirm spice level: Mild, Medium, Spicy, or Indian Spicy. Breads and Dessert do not have spice options.
- Confirm the price with the customer for every item.
- Order flow: greet, then ask if dine-in or takeout and get table number or name, then take items one by one with spice and price confirmation, then summarize and confirm the order.
- If the customer asks something unrelated to the restaurant (e.g. general knowledge, coding, other topics), politely decline and steer the conversation back to the menu or their order."""


def _format_menu_summary(menu: dict) -> str:
    """Build a compact menu summary for the LLM."""
    lines = ["Current menu (category - item name, price):"]
    for cat in menu.get("categories", []):
        cat_name = cat.get("name", "")
        for item in cat.get("items", []):
            name = item.get("name", "")
            price = item.get("price", 0)
            lines.append(f"  {cat_name}: {name}, ${price:.2f}")
    return "\n".join(lines)


def _format_order_summary(state: ConversationState) -> str:
    """Build a short summary of the current order."""
    order = state.order
    if order is None:
        return "Current order: (none yet)"
    parts = []
    for it in order.items:
        spice = f", {it.spice_level}" if it.spice_level else ""
        parts.append(f"  {it.name} x{it.quantity}{spice}, ${it.item_total:.2f}")
    return (
        "Current order:\n"
        + "\n".join(parts)
        + f"\nSubtotal: ${order.subtotal:.2f}; tax: ${order.tax:.2f}; total: ${order.total:.2f}."
    )


def _stage_instruction(stage: ConversationStage) -> str:
    """Brief instruction for the current stage."""
    if stage == ConversationStage.GREETING:
        return "Right now you are in the greeting stage. Greet the customer and offer to take their order."
    if stage == ConversationStage.ORDER_TYPE:
        return "Right now you are in the order type stage. Ask if they are dining in or ordering takeout, and get their table number or name."
    if stage == ConversationStage.ORDERING:
        return "Right now you are in the ordering stage. Take items one by one, confirm spice level when applicable, and confirm price for each item."
    if stage == ConversationStage.CONFIRMATION:
        return "Right now you are in the confirmation stage. Summarize the order and confirm with the customer before finalizing."
    if stage == ConversationStage.COMPLETED:
        return "The order has been completed."
    return ""


def build_system_prompt(menu: dict, state: ConversationState) -> str:
    """Build full system prompt with menu, current order, and stage."""
    restaurant_name = menu.get("restaurant_name", "the restaurant")
    prompt = get_base_system_prompt(restaurant_name)
    prompt += "\n\n" + _format_menu_summary(menu)
    prompt += "\n\n" + _format_order_summary(state)
    stage_instr = _stage_instruction(state.stage)
    if stage_instr:
        prompt += "\n\n" + stage_instr
    return prompt


# Blocklist of phrases that indicate off-topic (general knowledge, creative, coding, etc.)
_OFF_TOPIC_PHRASES = (
    "what is the capital of",
    "what's the capital of",
    "how do i code",
    "how to code",
    "write a poem",
    "write me a poem",
    "tell me about history",
    "what do you think about",
    "time travel",
    "recipe for",
    "how to cook",
    "explain ",
    "what is the meaning of",
    "who wrote",
    "who invented",
    "translate ",
    "write code",
    "write a story",
    "tell me a joke",
    "what is the weather",
    "current events",
    "news today",
    "political",
    "medical advice",
    "legal advice",
    "financial advice",
)


def is_off_topic(transcript: str) -> bool:
    """
    Return True if the user is clearly asking something we must refuse
    (non-restaurant question). Allow greetings and ordering-related speech.
    """
    if not transcript or not transcript.strip():
        return False
    t = transcript.lower().strip()
    # Allow short greetings and ordering-related
    if t in ("hi", "hello", "hey", "thanks", "thank you", "ok", "okay", "sure", "yes", "no"):
        return False
    if any(
        x in t
        for x in (
            "order",
            "menu",
            "dine",
            "takeout",
            "take out",
            "table",
            "spice",
            "mild",
            "medium",
            "spicy",
            "indian spicy",
            "dollar",
            "price",
            "bill",
            "check",
        )
    ):
        return False
    # Check blocklist
    for phrase in _OFF_TOPIC_PHRASES:
        if phrase in t:
            return True
    return False


def get_refusal_message(restaurant_name: str = "our restaurant") -> str:
    """Return a polite refusal to speak when the user is off-topic."""
    return f"I'm here to help with your order at {restaurant_name}. What would you like to order?"
