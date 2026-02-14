# Intent vs. Finite Phrase List

There are no finite number of ways in which a human can request an item (or express any other behaviour). For a fully functional PoC, the bare minimum to expect is **understanding the human's instructions properly** — i.e., inferring intent rather than matching a fixed list of phrases.

## Current Approach and Its Limit

The current fix for “item not on menu” relies on:

- **Parser** (`order_parser.py`): Matches words in the transcript to `menu.json` (item names, categories). This gives a reliable, menu-grounded signal: “did the user mention something that exists on the menu?”
- **Guard** (`restaurant_order_agent.py`): “If it *looks like* an item request (via a fixed phrase list) and the parser found *no* menu items → deny and don’t call the LLM.”
- **LLM**: Used for open-ended reply when we don’t take the deny path.

So today, “understanding” is split in a brittle way:

- **Intent** (“is this an item request?”) = finite pattern list.
- **What was requested** (“which item?”) = parser + menu only.

The weakness: we can’t enumerate every way a user might ask for an item. Phrases like “could I get”, “they have a”, “I would like some” are a few examples; users will keep saying things we didn’t anticipate. The bare minimum is that the system should **infer the user’s intent** (e.g. “asking for an item”) rather than matching a fixed set of strings.

## What “Understanding Instructions Properly” Could Mean

1. **Intent classification**  
   Decide *why* the user spoke: e.g. “requesting an item”, “giving name/table”, “confirming/cancelling”, “off-topic”, “just chatting”. That’s a general “what is the user trying to do?” layer, not tied to a fixed set of sentences.

2. **Slot filling from intent**  
   Once we know “requesting an item”, we still need *which* item. That can stay menu-grounded (parser + menu) so we never invent items. The improvement is: we only treat something as “requesting an item” when we’ve actually understood that intent, not when a substring matched.

3. **Consistent behaviour**  
   For an item request with no menu match: always deny (or ask for clarification) and never let the main LLM suggest or invent dishes. So “understanding” also means the *downstream behaviour* is correct given that intent.

## Ways to Get There (Without a Finite Phrase List)

- **Use the LLM for intent only**  
  Before the main flow, ask the model a very narrow question, e.g.: “Given this customer message, answer only: is the customer trying to order a specific food or drink item? Yes or No.” Use that “Yes/No” plus parser output: if intent = “item request” and parser found 0 items → deny; otherwise continue as now. You still don’t let the LLM name or suggest items; you only use it to recognise “item request” in open-ended language.

- **Two-phase flow**  
  Phase 1: Classify intent (LLM or a small classifier). Phase 2: If “item request”, run parser; if no match → deterministic denial. If not “item request”, use the LLM for greeting, order type, confirmation, etc. So “understanding” is explicit (intent) and behaviour is deterministic where it matters (menu strictness).

- **Parser-first, LLM only for wording**  
  Always run the parser. If the parser finds ≥1 item, merge into the order and then optionally use the LLM only to *phrase* the confirmation (with strict instructions: only mention the items that were parsed). If the parser finds 0 items, you could either (a) ask the LLM “item request yes/no?” and deny when yes, or (b) use a learned/intent classifier. Either way, item presence is never decided by the LLM.

## Summary

For a PoC, the “bare minimum” is: **replace the finite phrase list with a proper intent-understanding step** (e.g. LLM or classifier) so we recognise “requesting an item” in an open-ended way, and **keep the rule “no menu match → deny”** so we never hallucinate items. The current code is a useful first step (parser + deny path), but the missing piece is that general intent layer instead of the fixed list of phrases.
