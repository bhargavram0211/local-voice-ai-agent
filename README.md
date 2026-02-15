# Local Voice AI Agent

A real-time voice chat application powered by local AI models. This repo includes a **general voice chat** app and a **restaurant order-taking agent** that takes dine-in and takeout orders by voice using a JSON menu.

## Features

- Real-time speech-to-text (Moonshine) and text-to-speech (Kokoro)
- Local LLM inference via Ollama (Gemma)
- **Restaurant agent**: Menu-driven ordering flow, guardrails (off-topic refusal, “item not on menu” denial), structured order JSON
- Web UI with conversation transcript and order summary (Gradio + FastRTC)
- Optional phone-number interface for the advanced voice chat

## Prerequisites

- macOS
- [Ollama](https://ollama.ai/) — run LLMs locally
- [uv](https://github.com/astral-sh/uv) — Python package installer and resolver

## Installation

### 1. Install prerequisites (Homebrew)

```bash
brew install ollama
brew install uv
```

### 2. Clone the repository

```bash
git clone https://github.com/jesuscopado/local-voice-ai-agent.git
cd local-voice-ai-agent
```

### 3. Python environment and dependencies

```bash
uv venv
source .venv/bin/activate
uv sync
```

### 4. Download Ollama models

```bash
ollama pull gemma3:1b
# Optional, for advanced chat
ollama pull gemma3:4b
```

## Usage

### Restaurant order-taking agent (recommended)

Voice agent that takes orders from a JSON menu (greeting → order type & table/name → items with spice and price confirmation → order summary). Run:

```bash
python restaurant_order_agent.py
```

Menu is read from `menu.json` in the project root. Override with:

```bash
PATH_TO_MENU=/path/to/menu.json python restaurant_order_agent.py
```

### Basic voice chat

Simple voice chat with a local LLM (no restaurant flow):

```bash
python local_voice_chat.py
```

### Advanced voice chat (system prompt, optional phone UI)

```bash
python local_voice_chat_advanced.py
```

With a temporary phone number for callers:

```bash
python local_voice_chat_advanced.py --phone
```

## How it works

- **Voice in**: FastRTC (WebRTC) captures audio → **Moonshine** (STT) produces transcript.
- **Restaurant agent**: Transcript → off-topic check → order parsing (match to menu, quantities, spice, order type, table/name) → conversation state updates → if “item request” with no menu match, return fixed “we don’t have that” message; otherwise → **Ollama** (Gemma) with context-aware prompt (menu + current order) → parse LLM reply for order updates → update order state → **Kokoro** (TTS) → stream audio back.
- **General chat**: Transcript → Ollama → TTS → stream back.

## Project structure

| File | Purpose |
|------|--------|
| **restaurant_order_agent.py** | Main restaurant order-taking app. Loads menu, runs STT → guardrails → parser → state → LLM → TTS; Gradio UI with transcript and order summary. |
| **menu.json** | Restaurant menu (categories, items, prices, tax rate). Editable without code changes. |
| **menu_loader.py** | Load menu from JSON; get item by ID, by category; validate structure; `get_category_info` for parser. |
| **order_structure.py** | `Order` and `OrderItem` models; `order_to_json`, `order_to_cart_markdown`; order ID and totals calculation. |
| **order_parser.py** | Parse free-form text into order updates: match item mentions to menu (fuzzy), extract quantity, spice level, order type, table/name; `parse_llm_response`, `merge_parsed_turn_into_order`. |
| **restaurant_prompts.py** | System prompt and context builder (menu + order summary); off-topic detection; greeting, “item not on menu”, and refusal messages. |
| **conversation_state.py** | Conversation stages (GREETING, ORDER_TYPE, ORDERING, CONFIRMATION, COMPLETED); order, order_type, table_or_name; create/reset state. |
| **local_voice_chat.py** | Basic voice chat (STT → LLM → TTS), no restaurant logic. |
| **local_voice_chat_advanced.py** | Advanced voice chat with configurable system prompt; optional phone interface. |

### Tests

| Directory / file | Purpose |
|------------------|--------|
| **tests/** | Unit tests for menu loader, order structure, order parser, restaurant prompts, conversation state. Run with `pytest tests/ -v`. |

### Docs and planning

| File | Purpose |
|------|--------|
| **ROADMAP.md** | Development phases, requirements, order JSON format, success criteria. |
| **BACKLOG.md** | Deferred work (e.g. intent classification, LLM-based extraction, env/voice issues). |
| **docs/intent-vs-phrase-list.md** | Why “item request” detection is currently phrase-based and how to move to intent-based understanding. |

## Testing

From the project root with the virtual environment active:

```bash
python -m pytest tests/ -v
```

## Menu and configuration

- **menu.json**: Must include `restaurant_name`, `tax_rate`, and `categories` (each with `name`, `items`; items with `id`, `name`, `price`, and optional `allows_spice_customization` at category level). See `menu_loader.validate_menu_structure` for validation rules.
- **Restaurant agent**: Uses `gemma3:1b` by default (see `restaurant_order_agent.py`). Conversation history is trimmed to the last 20 messages for context.
