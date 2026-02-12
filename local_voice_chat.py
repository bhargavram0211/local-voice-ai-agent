from datetime import datetime
import unicodedata

from fastrtc import ReplyOnPause, Stream, get_stt_model, get_tts_model
from ollama import chat

stt_model = get_stt_model()  # moonshine/base
tts_model = get_tts_model()  # kokoro

AGENT_NAME = "Bhargav's Local Voice Agent"


def get_current_datetime_string() -> str:
    """Return a human-friendly representation of the current local date and time."""
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")


def is_datetime_question(text: str) -> bool:
    """Heuristic check for questions about the current date or time."""
    t = text.lower()
    keywords = [
        "what time is it",
        "what's the time",
        "what is the time",
        "current time",
        "time right now",
        "time now",
        "what's the date",
        "what is the date",
        "today's date",
        "date today",
        "what day is it",
        "what is today",
        "what's today",
        "current date",
    ]
    return any(k in t for k in keywords)


def is_name_question(text: str) -> bool:
    """Heuristic check for questions about the agent's name or identity."""
    t = text.lower()
    keywords = [
        "what is your name",
        "what's your name",
        "who are you",
        "who am i talking to",
        "who am i speaking to",
        "your name",
        "what are you called",
    ]
    return any(k in t for k in keywords)


def clean_for_tts(text: str) -> str:
    """
    Remove emojis and most decorative symbols before sending text to TTS.

    We keep normal ASCII characters (with a few exceptions) and non-ASCII
    characters that are not in the 'So' (Symbol, other) Unicode category,
    which is where emojis live.
    """
    # Strip markdown-style asterisks so TTS doesn't say "asterisk"
    text = text.replace("*", "")

    cleaned_chars = []
    for ch in text:
        # Always allow ASCII characters
        if ch.isascii():
            cleaned_chars.append(ch)
            continue

        # For non-ASCII characters, drop emojis and other decorative symbols
        if unicodedata.category(ch).startswith("So"):
            continue

        cleaned_chars.append(ch)
    return "".join(cleaned_chars)


def echo(audio):
    transcript = stt_model.stt(audio)

    # Build messages based on the user's intent so we can give reliable
    # answers for date/time and the agent's name.
    if is_datetime_question(transcript):
        current_dt = get_current_datetime_string()
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are {AGENT_NAME}. "
                    f"The current local date and time is: {current_dt}. "
                    "When the user asks about the current date or time, answer using "
                    "this value only and do not guess other dates or times."
                ),
            },
            {"role": "user", "content": transcript},
        ]
    elif is_name_question(transcript):
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are {AGENT_NAME}. "
                    "When the user asks your name, always respond that your name is "
                    f"'{AGENT_NAME}' and do not invent any other names."
                ),
            },
            {"role": "user", "content": transcript},
        ]
    else:
        messages = [{"role": "user", "content": transcript}]

    response = chat(model="gemma3:1b", messages=messages)
    response_text = response["message"]["content"]
    cleaned_response_text = clean_for_tts(response_text)

    for audio_chunk in tts_model.stream_tts_sync(cleaned_response_text):
        yield audio_chunk


stream = Stream(ReplyOnPause(echo), modality="audio", mode="send-receive")
stream.ui.launch()
