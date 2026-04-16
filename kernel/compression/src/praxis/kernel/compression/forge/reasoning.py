"""Forge reasoning chain preservation (architecture §3.2.3 + FMEA F.2/F.6).

Reasoning blocks MUST NOT be compacted. This module:
1. Detects reasoning content in messages (F8 — last-block extraction)
2. Injects the last reasoning block into the first post-boundary assistant message
   IF AND ONLY IF that message has no existing reasoning (never overwrite)
3. Detects unknown reasoning schema versions and emits alerts (FMEA F.2)
"""
from __future__ import annotations

import logging
import re

from .models import ConversationMessage, Role

logger = logging.getLogger(__name__)

# Known reasoning schema versions (update as provider SDKs evolve)
KNOWN_REASONING_SCHEMAS: frozenset[str] = frozenset({"v1-thinking", "v1-extended_thinking"})

# Patterns that identify reasoning content
_THINKING_TAG_RE = re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE)
_STEP_RE = re.compile(r"(?:step\s+\d+[:.)]|\d+\.\s+)", re.IGNORECASE)
_REASONING_KEYWORDS = frozenset({
    "let me think", "reasoning:", "analysis:", "therefore",
    "step 1", "first,", "secondly", "in conclusion", "thus,"
})


def detect_reasoning_schema(text: str | None) -> str | None:
    """Return the schema version string if *text* contains recognisable reasoning."""
    if not text:
        return None
    if _THINKING_TAG_RE.search(text):
        return "v1-thinking"
    if "extended_thinking" in text.lower():
        return "v1-extended_thinking"
    return None


def has_reasoning(message: ConversationMessage) -> bool:
    """Return True if *message* contains a reasoning block."""
    if message.reasoning_details:
        return True
    if message.role == Role.ASSISTANT and message.content:
        schema = detect_reasoning_schema(message.content)
        return schema is not None
    return False


def extract_reasoning_text(message: ConversationMessage) -> str | None:
    """Extract the reasoning content from *message*, or None if absent."""
    if message.reasoning_details:
        return message.reasoning_details
    if message.content:
        m = _THINKING_TAG_RE.search(message.content)
        if m:
            return m.group(0)
    return None


def last_non_empty_reasoning(
    messages: list[ConversationMessage],
) -> tuple[str | None, str | None]:
    """Return (reasoning_text, schema_version) for the last message with reasoning.

    Scans *messages* in reverse order.
    Returns (None, None) if no reasoning found.
    """
    for msg in reversed(messages):
        text = extract_reasoning_text(msg)
        if text:
            schema = detect_reasoning_schema(text)
            if schema is None:
                # Content has reasoning-like text but unknown schema
                schema = "v1-unknown"
            return text, schema
    return None, None


def inject_reasoning(
    messages: list[ConversationMessage],
    reasoning_text: str,
    from_index: int,
) -> list[ConversationMessage]:
    """Inject *reasoning_text* into the first assistant message at or after *from_index*.

    Rules (architecture §3.2.3):
    - IF the first assistant message already has reasoning → leave it alone, discard
    - IF it has no reasoning → inject into reasoning_details
    - NEVER overwrite, never merge, never append to existing reasoning
    """
    result = list(messages)
    for i in range(from_index, len(result)):
        msg = result[i]
        if msg.role == Role.ASSISTANT:
            if has_reasoning(msg):
                # Already has reasoning — leave untouched, discard extracted block
                return result
            # Inject
            result[i] = msg.model_copy(update={"reasoning_details": reasoning_text})
            return result
    return result


def validate_reasoning_schema(schema: str | None) -> bool:
    """Return True if *schema* is a known version; emit alert and return False otherwise."""
    if schema is None:
        return True
    if schema in KNOWN_REASONING_SCHEMAS:
        return True
    logger.error(
        "forge.reasoning.unknown_schema detected: %r — falling back to no-reasoning mode. "
        "Update KNOWN_REASONING_SCHEMAS when the provider SDK stabilises.",
        schema,
    )
    return False
