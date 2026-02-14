"""
Restaurant order-taking voice agent: STT -> guardrails -> parse -> state -> LLM -> TTS.
Run with: python restaurant_order_agent.py
"""

import os
import sys
import unicodedata
from pathlib import Path

import gradio as gr
from fastrtc import AdditionalOutputs, ReplyOnPause, WebRTC, get_stt_model, get_tts_model
from ollama import chat

from conversation_state import (
    ConversationStage,
    ConversationState,
    create_initial_state,
    reset_state,
)
from menu_loader import load_menu, validate_menu_structure
from order_parser import merge_parsed_turn_into_order, parse_llm_response
from order_structure import order_to_cart_markdown, order_to_json
from restaurant_prompts import (
    build_system_prompt,
    get_greeting_message,
    get_item_not_on_menu_message,
    get_refusal_message,
    is_off_topic,
)

# Menu path: same dir as this script, or PATH_TO_MENU env
_SCRIPT_DIR = Path(__file__).resolve().parent
_MENU_PATH = os.environ.get("PATH_TO_MENU", str(_SCRIPT_DIR / "menu.json"))

# Load menu at import
try:
    _MENU = load_menu(_MENU_PATH)
except FileNotFoundError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
valid, err = validate_menu_structure(_MENU)
if not valid:
    print(f"Invalid menu: {err}", file=sys.stderr)
    sys.exit(1)

# Persistent state and history (survive across echo() calls)
current_state: ConversationState = create_initial_state()
conversation_history: list[dict] = []
_MAX_HISTORY_MESSAGES = 20

# Models (loaded once)
stt_model = get_stt_model()
tts_model = get_tts_model()


def clean_for_tts(text: str) -> str:
    """Remove emojis and asterisks so TTS does not say 'asterisk'."""
    text = text.replace("*", "")
    cleaned = []
    for ch in text:
        if ch.isascii():
            cleaned.append(ch)
            continue
        if unicodedata.category(ch).startswith("So"):
            continue
        cleaned.append(ch)
    return "".join(cleaned)


def _is_done_adding(transcript: str) -> bool:
    """User said they are done adding items."""
    t = transcript.lower().strip()
    return any(
        x in t
        for x in ("that's all", "nothing else", "done", "that's it", "that is all")
    )


def _is_confirming(transcript: str) -> bool:
    """User is confirming the order (yes, correct, confirm)."""
    t = transcript.lower().strip()
    return any(x in t for x in ("yes", "correct", "confirm", "that's correct"))


def _looks_like_item_request(transcript: str) -> bool:
    """True if transcript sounds like the customer is asking for an item (and not 'that\'s all' etc.)."""
    t = transcript.lower().strip()
    if _is_done_adding(transcript):
        return False
    return any(
        x in t
        for x in (
            "i want",
            "i'd like",
            "i would like",
            "can i get",
            "could i get",
            "could i please get",
            "give me",
            "i'll have",
            "i will have",
            "add",
            "get me",
            "get some",
            "have a",
            "they have",
            "tea",
            "coffee",
        )
    )


def _apply_stage_transitions(transcript: str) -> None:
    """Update current_state.stage from transcript and current state."""
    global current_state
    # GREETING/ORDER_TYPE -> ORDERING when we have order_type and table_or_name
    if current_state.stage in (ConversationStage.GREETING, ConversationStage.ORDER_TYPE):
        if current_state.order_type and current_state.table_or_name:
            current_state.stage = ConversationStage.ORDERING
    # ORDERING -> CONFIRMATION when user says done and we have items
    if current_state.stage == ConversationStage.ORDERING:
        if _is_done_adding(transcript) and current_state.order and len(current_state.order.items) > 0:
            current_state.stage = ConversationStage.CONFIRMATION
    # CONFIRMATION -> COMPLETED when user confirms
    if current_state.stage == ConversationStage.CONFIRMATION:
        if _is_confirming(transcript):
            current_state.stage = ConversationStage.COMPLETED


def _output_order_and_reset() -> None:
    """Print order JSON and reset state/history for next order."""
    global current_state, conversation_history
    if current_state.order is None:
        return
    json_str = order_to_json(current_state.order)
    print("--- Order completed ---")
    print(json_str)
    print("--- End order ---")
    current_state = reset_state()
    conversation_history = []


def end_session():
    """Reset conversation and order state; return empty transcript and cart for UI."""
    global current_state, conversation_history
    current_state = reset_state()
    conversation_history = []
    return [], order_to_cart_markdown(None)


def _get_ui_state():
    """Return (transcript_messages, cart_markdown) for AdditionalOutputs."""
    return list(conversation_history), order_to_cart_markdown(current_state.order)


def echo(audio):
    global current_state, conversation_history
    transcript = stt_model.stt(audio) or ""
    transcript = transcript.strip()

    # Empty transcript: greet on first turn (user hit record but said nothing), else prompt to repeat
    if not transcript:
        if len(conversation_history) == 0:
            restaurant_name = _MENU.get("restaurant_name", "our restaurant")
            msg = get_greeting_message(restaurant_name)
            conversation_history.append({"role": "user", "content": "(listening)"})
            conversation_history.append({"role": "assistant", "content": msg})
            for ch in tts_model.stream_tts_sync(clean_for_tts(msg)):
                yield ch
        else:
            msg = "I didn't catch that. What would you like to order?"
            conversation_history.append({"role": "user", "content": "(listening)"})
            conversation_history.append({"role": "assistant", "content": msg})
            for ch in tts_model.stream_tts_sync(clean_for_tts(msg)):
                yield ch
        yield AdditionalOutputs(*_get_ui_state())
        return

    restaurant_name = _MENU.get("restaurant_name", "our restaurant")

    # 1. Guardrails
    if is_off_topic(transcript):
        msg = get_refusal_message(restaurant_name)
        conversation_history.append({"role": "user", "content": transcript})
        conversation_history.append({"role": "assistant", "content": msg})
        if len(conversation_history) > _MAX_HISTORY_MESSAGES:
            conversation_history = conversation_history[-_MAX_HISTORY_MESSAGES:]
        for ch in tts_model.stream_tts_sync(clean_for_tts(msg)):
            yield ch
        yield AdditionalOutputs(*_get_ui_state())
        return

    # 2. Parse user turn (transcript = what the user said)
    parsed = parse_llm_response(transcript, _MENU, current_state)

    # 3. Merge into order and update state
    tax_rate = float(_MENU.get("tax_rate", 0))
    order = merge_parsed_turn_into_order(current_state.order, parsed, _MENU, tax_rate)
    current_state.order = order
    current_state.order_type = order.order_type
    current_state.table_or_name = order.table_or_name

    # 4. Stage transitions
    _apply_stage_transitions(transcript)

    # 4b. Item not on menu: customer asked for something but nothing matched (any stage)
    if len(parsed.new_items) == 0 and _looks_like_item_request(transcript):
        msg = get_item_not_on_menu_message(restaurant_name)
        conversation_history.append({"role": "user", "content": transcript})
        conversation_history.append({"role": "assistant", "content": msg})
        if len(conversation_history) > _MAX_HISTORY_MESSAGES:
            conversation_history = conversation_history[-_MAX_HISTORY_MESSAGES:]
        for ch in tts_model.stream_tts_sync(clean_for_tts(msg)):
            yield ch
        yield AdditionalOutputs(*_get_ui_state())
        return

    # 5. Build messages for LLM
    system_content = build_system_prompt(_MENU, current_state)
    messages = [
        {"role": "system", "content": system_content},
        *conversation_history,
        {"role": "user", "content": transcript},
    ]

    # 6. Call LLM
    response = chat(model="gemma3:1b", messages=messages)
    response_text = response["message"]["content"] or ""

    # 7. Update conversation history
    conversation_history.append({"role": "user", "content": transcript})
    conversation_history.append({"role": "assistant", "content": response_text})
    if len(conversation_history) > _MAX_HISTORY_MESSAGES:
        conversation_history = conversation_history[-_MAX_HISTORY_MESSAGES:]

    # 8. Order completion: output JSON and reset when COMPLETED
    if current_state.stage == ConversationStage.COMPLETED:
        _output_order_and_reset()

    # 9. TTS and yield
    cleaned = clean_for_tts(response_text)
    for ch in tts_model.stream_tts_sync(cleaned):
        yield ch
    yield AdditionalOutputs(*_get_ui_state())


if __name__ == "__main__":
    with gr.Blocks(title="Spice Garden – Voice Order") as demo:
        gr.Markdown("# Spice Garden – Voice Order")
        with gr.Row():
            with gr.Column(scale=1):
                audio = WebRTC(
                    label="Voice",
                    mode="send-receive",
                    modality="audio",
                )
            with gr.Column(scale=1):
                transcript_ui = gr.Chatbot(label="Conversation", type="messages", height=400)
                cart_ui = gr.Markdown(value=order_to_cart_markdown(current_state.order), label="Cart")
        disconnect_btn = gr.Button("End session (disconnect)")
        disconnect_btn.click(
            end_session,
            inputs=[],
            outputs=[transcript_ui, cart_ui],
        )
        audio.stream(
            ReplyOnPause(echo),
            inputs=[audio],
            outputs=[audio],
        )
        audio.on_additional_outputs(
            lambda transcript_list, cart_md: (transcript_list, cart_md),
            outputs=[transcript_ui, cart_ui],
            queue=False,
            show_progress="hidden",
        )
    demo.launch()
