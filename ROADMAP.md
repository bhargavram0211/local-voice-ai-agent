# Restaurant Order-Taking AI Agent - Development Roadmap

## Project Overview

Transform the existing local voice AI agent into a restaurant order-taking assistant for an Indian restaurant. The PoC will support dine-in and takeout orders with a menu of 15 items across 5 categories, with spice level customization and price confirmation.

---

## Requirements Summary

### Core Features
- **Restaurant Type**: Indian Restaurant
- **Menu**: 15 items across 5 categories (JSON file)
- **Order Types**: Dine-in and Takeout
- **Customization**: Spice level only (Mild, Medium, Spicy, Indian Spicy)
- **Pricing**: Each item has price, tax rate applied, subtotal/tax/total calculated
- **Price Confirmation**: Agent confirms price with customer for every item
- **Guardrails**: Politely deny non-restaurant questions, allow light small talk
- **Frontend**: Extend Gradio UI with running conversation log (transcript panel)
- **Output**: Structured JSON order format ready for POS integration

### Technical Stack
- **STT**: Moonshine (via FastRTC)
- **LLM**: Ollama with Gemma models
- **TTS**: Kokoro
- **UI**: FastRTC/Gradio
- **Menu Source**: JSON file

---

## Development Phases

### Phase 1: Menu Structure & Data Foundation
**Goal**: Create the menu JSON structure and data loading utilities.

**Tasks**:
1. Create `menu.json` with boilerplate Indian restaurant menu:
   - 5 categories (e.g., Appetizers, Main Courses, Breads, Beverages, Desserts)
   - 15 items total (3 items per category)
   - Each item includes:
     - `id`: unique identifier (e.g., "butter_chicken")
     - `name`: display name (e.g., "Butter Chicken")
     - `category`: category name
     - `price`: float (e.g., 12.99)
     - `description`: brief item description
   - Global `tax_rate`: percentage (e.g., 8.5)
   - Restaurant name field

2. Create `menu_loader.py` utility:
   - Function to load menu from JSON
   - Function to get item by ID
   - Function to get items by category
   - Function to calculate price with tax
   - Function to validate menu structure

3. Create `order_structure.py`:
   - Define OrderItem dataclass/model
   - Define Order dataclass/model with:
     - `order_type`: "dine_in" | "takeout"
     - `table_or_name`: string
     - `items`: list of OrderItem
     - `subtotal`: float
     - `tax`: float
     - `total`: float
     - `timestamp`: ISO datetime string
   - OrderItem includes:
     - `id`: menu item ID
     - `name`: item name
     - `category`: category
     - `quantity`: int
     - `spice_level`: "Mild" | "Medium" | "Spicy" | "Indian Spicy"
     - `price`: unit price
     - `item_total`: quantity * price

**Deliverables**:
- `menu.json` file
- `menu_loader.py` module
- `order_structure.py` module
- Unit tests for menu loading and order calculations

---

### Phase 2: LLM Prompt Engineering & Guardrails
**Goal**: Design the restaurant agent persona and conversation flow.

**Tasks**:
1. Create `restaurant_prompts.py`:
   - System prompt for restaurant order-taking agent:
     - Restaurant name and identity
     - Role: friendly, professional order-taking assistant
     - Instructions: confirm spice level and price for each item
     - Guardrails: politely decline non-restaurant questions
     - Order flow: greet → take order → confirm → summarize
   - Function to build context-aware prompts (include menu items, current order state)
   - Function to detect non-restaurant questions (guardrail check)

2. Create `conversation_state.py`:
   - Track conversation state:
     - Current order (Order object)
     - Order type (dine_in/takeout)
     - Table/name
     - Current item being ordered
     - Conversation stage (greeting, ordering, confirmation, etc.)

3. Implement guardrail logic:
   - Detect off-topic questions
   - Return polite refusal messages
   - Steer conversation back to menu/ordering

**Deliverables**:
- `restaurant_prompts.py` module
- `conversation_state.py` module
- Prompt templates and guardrail detection functions

---

### Phase 3: Order Parsing & Extraction
**Goal**: Extract structured order data from LLM responses.

**Tasks**:
1. Create `order_parser.py`:
   - Function to parse LLM response for order intent:
     - Detect item mentions (match against menu)
     - Extract quantities
     - Extract spice level preferences
     - Detect order type (dine-in vs takeout)
     - Extract table number or customer name
   - Function to build order from parsed data
   - Function to calculate totals (subtotal, tax, total)

2. Implement fuzzy matching for menu items:
   - Handle variations in item names
   - Handle partial matches
   - Handle common misspellings

3. Create order validation:
   - Ensure items exist in menu
   - Ensure quantities are valid
   - Ensure spice levels are valid

**Deliverables**:
- `order_parser.py` module
- Order extraction and validation logic
- Tests for parsing various order formats

---

### Phase 4: Core Order-Taking Logic
**Goal**: Integrate menu, prompts, state, and parsing into the main echo function.

**Tasks**:
1. Modify `local_voice_chat.py` (or create new `restaurant_order_agent.py`):
   - Load menu on startup
   - Initialize conversation state
   - In `echo()` function:
     - Get transcript from STT
     - Check guardrails (if off-topic, return refusal)
     - Update conversation state based on transcript
     - Build context-aware prompt (include menu, current order)
     - Call LLM with restaurant-specific prompt
     - Parse response for order updates
     - Update order state
     - Generate response with price confirmations
     - Clean response for TTS
   - Handle order completion:
     - Detect when order is complete
     - Generate order summary
     - Output structured JSON order

2. Implement conversation flow:
   - Greeting and menu offer
   - Item-by-item ordering with price confirmation
   - Spice level selection
   - Order type selection (dine-in/takeout)
   - Final order summary and confirmation

**Deliverables**:
- `restaurant_order_agent.py` (or modified `local_voice_chat.py`)
- Working order-taking conversation flow
- Order JSON output on completion

---

### Phase 5: Frontend Enhancement - Transcript Panel
**Goal**: Add running conversation log to Gradio UI.

**Tasks**:
1. Research FastRTC/Gradio UI customization:
   - Understand how to extend the default UI
   - Find ways to add custom components (text display, panels)

2. Modify UI launch code:
   - Add conversation log state (list of messages)
   - Create transcript panel component:
     - Display user transcripts
     - Display agent responses
     - Show current order summary
     - Show final order JSON (when complete)
   - Update log on each turn

3. Integrate transcript logging:
   - Capture STT transcripts
   - Capture LLM responses
   - Format and display in UI panel

**Deliverables**:
- Enhanced Gradio UI with transcript panel
- Running conversation log display
- Order summary display in UI

---

### Phase 6: Testing & Refinement
**Goal**: Test the complete flow and refine prompts/logic.

**Tasks**:
1. Create test scenarios:
   - Happy path: complete order flow
   - Edge cases: wrong item names, unclear quantities, off-topic questions
   - Error handling: invalid menu items, missing information

2. Manual testing:
   - Test various order scenarios
   - Test guardrails with off-topic questions
   - Test price confirmations
   - Test transcript accuracy

3. Refinement:
   - Tune prompts based on test results
   - Improve item name matching
   - Refine guardrail responses
   - Optimize conversation flow

**Deliverables**:
- Test scenarios document
- Refined prompts and logic
- Bug fixes and improvements

---

## File Structure (Proposed)

```
local-voice-ai-agent/
├── menu.json                          # Menu data (15 items, 5 categories)
├── menu_loader.py                     # Menu loading utilities
├── order_structure.py                 # Order data models
├── restaurant_prompts.py              # LLM prompts and guardrails
├── conversation_state.py              # Conversation state management
├── order_parser.py                    # Order extraction from LLM responses
├── restaurant_order_agent.py         # Main order-taking agent (new file)
├── local_voice_chat.py                # Original basic chat (keep for reference)
├── local_voice_chat_advanced.py       # Original advanced chat (keep for reference)
├── ROADMAP.md                         # This file
└── tests/
    ├── test_menu_loader.py
    ├── test_order_parser.py
    └── test_order_structure.py
```

---

## Order JSON Structure (Final Format)

```json
{
  "order_id": "order_20260212_182345",
  "restaurant_name": "Spice Garden",
  "order_type": "dine_in",
  "table_or_name": "Table 5",
  "timestamp": "2026-02-12T18:23:45Z",
  "items": [
    {
      "id": "butter_chicken",
      "name": "Butter Chicken",
      "category": "Main Courses",
      "quantity": 2,
      "spice_level": "Medium",
      "unit_price": 14.99,
      "item_total": 29.98
    },
    {
      "id": "naan",
      "name": "Garlic Naan",
      "category": "Breads",
      "quantity": 2,
      "spice_level": "Mild",
      "unit_price": 3.99,
      "item_total": 7.98
    }
  ],
  "subtotal": 37.96,
  "tax_rate": 8.5,
  "tax": 3.23,
  "total": 41.19
}
```

---

## Success Criteria

- [ ] Agent can take complete orders (multiple items, quantities, spice levels)
- [ ] Agent confirms price for each item
- [ ] Agent handles dine-in and takeout orders
- [ ] Agent politely declines non-restaurant questions
- [ ] Order JSON is correctly structured and calculated
- [ ] Transcript panel shows running conversation log
- [ ] Menu is easily editable via JSON file
- [ ] Price calculations (subtotal, tax, total) are accurate

---

## Next Steps

1. Review and approve this roadmap
2. Start with Phase 1: Create menu.json and data loading utilities
3. Iterate through phases sequentially
4. Test and refine after each phase

---

## Notes

- Keep original `local_voice_chat.py` and `local_voice_chat_advanced.py` for reference
- New restaurant agent will be in `restaurant_order_agent.py`
- Menu JSON can be updated without code changes
- Structured JSON output ready for future POS/API integration
