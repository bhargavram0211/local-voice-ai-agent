# Backlog

Items deferred for later. Not in current scope.

---

## Environment / Tooling

- **uv sync failing (av / FFmpeg build)**  
  `uv sync` fails because the `av` package (PyAV, dependency of fastrtc → aiortc) builds from source and cannot find FFmpeg libraries (libavformat, libavcodec, etc.) via pkg-config. Fix options: install FFmpeg 7 and set `PKG_CONFIG_PATH`, or use pre-built wheels when available. Until then: use existing venv and `python -m pytest tests/ -v` for Phase 1 tests; run voice app with existing working environment.

---

## Voice agent / UX

- **Noise suppression / background voices**  
  STT currently transcribes everything in the audio (user + background). Reduce agent reacting to background speech (e.g. VAD, noise suppression, or STT settings). Deferred.

- **Latency and voice breaking up**  
  Improve perceived latency and smoothness (e.g. stream LLM to TTS, shorten responses, or tune TTS chunking/playback). Deferred.

---

## Order parsing

- **LLM-based order extraction**  
  Use the LLM to turn natural user sentences into structured order data (items, quantities, spice, order type, table/name) instead of or in addition to the rule-based parser. Options: (1) One LLM call that returns both the conversational reply and a JSON block of order updates; (2) A separate small LLM call for extraction only (transcript + menu → JSON). Validate and merge LLM output against the menu before updating the cart. Handles varied phrasing (e.g. "two portions of butter chicken", "a couple of", "double") without expanding rule coverage. Deferred.

---

*Add new backlog items below.*
