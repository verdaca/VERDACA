"""Forge stateless message transformers (architecture §3.2.3 F7).

All transformers are pure functions: list[ConversationMessage] → list[ConversationMessage].
They are order-stable, side-effect-free, and 100% line-coverage is required (Murat §0.1).
"""
from __future__ import annotations

import re

from .models import ConversationMessage, Role


def drop_role(
    messages: list[ConversationMessage],
    role: Role,
) -> list[ConversationMessage]:
    """Remove all messages with the given *role* (e.g. SYSTEM messages in compacted range)."""
    return [m for m in messages if m.role != role]


def dedupe_consecutive_role(
    messages: list[ConversationMessage],
    role: Role,
) -> list[ConversationMessage]:
    """Merge consecutive messages of *role* into a single message.

    When two user turns appear back-to-back (after a system drop, for instance),
    deduplicate by keeping the last one.
    """
    result: list[ConversationMessage] = []
    for msg in messages:
        if result and result[-1].role == role == msg.role:
            # Replace the previous same-role message with the current one
            result[-1] = msg
        else:
            result.append(msg)
    return result


_CONTEXT_SUMMARY_RE = re.compile(
    r"\[Context\s+Summary[^\]]*\]|<context_summary>.*?</context_summary>",
    re.DOTALL | re.IGNORECASE,
)


def trim_context_summary(
    messages: list[ConversationMessage],
) -> list[ConversationMessage]:
    """Remove embedded context-summary blocks from message content.

    Forge may have previously injected a summary into the conversation. When
    re-compacting, we strip the old summary to avoid summary-of-summary nesting.
    """
    result: list[ConversationMessage] = []
    for msg in messages:
        cleaned = _CONTEXT_SUMMARY_RE.sub("", msg.content).strip()
        if cleaned != msg.content:
            msg = msg.model_copy(update={"content": cleaned})
        result.append(msg)
    return result


_WORKING_DIR_RE = re.compile(
    r"(?:working directory|cwd|current directory):\s*/[^\n]+",
    re.IGNORECASE,
)


def strip_working_dir(
    messages: list[ConversationMessage],
) -> list[ConversationMessage]:
    """Strip absolute working-directory path references from message content.

    These are typically injected by the agent runtime and are machine-specific.
    Stripping them keeps the compacted summary portable.
    """
    result: list[ConversationMessage] = []
    for msg in messages:
        cleaned = _WORKING_DIR_RE.sub("", msg.content).strip()
        if cleaned != msg.content:
            msg = msg.model_copy(update={"content": cleaned})
        result.append(msg)
    return result


def drop_droppable(messages: list[ConversationMessage]) -> list[ConversationMessage]:
    """Remove messages flagged as droppable."""
    return [m for m in messages if not m.droppable]


def apply_all(messages: list[ConversationMessage]) -> list[ConversationMessage]:
    """Apply the full standard transformer pipeline in the documented order.

    Order (architecture §3.2.3): DropRole(SYSTEM) → DedupeRole(USER) →
    TrimContextSummary → StripWorkingDir → DropDroppable
    """
    messages = drop_role(messages, Role.SYSTEM)
    messages = dedupe_consecutive_role(messages, Role.USER)
    messages = trim_context_summary(messages)
    messages = strip_working_dir(messages)
    messages = drop_droppable(messages)
    return messages
