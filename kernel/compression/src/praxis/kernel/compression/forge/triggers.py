"""Forge compaction trigger conditions (architecture §3.2.4)."""
from __future__ import annotations

from .models import Conversation, Role


def should_compact_due_to_tokens(conversation: Conversation, threshold: int) -> bool:
    """Return True if conversation.total_tokens() >= threshold."""
    return conversation.total_tokens() >= threshold


def should_compact_due_to_turns(conversation: Conversation, threshold: int) -> bool:
    """Return True if the number of user turns >= threshold."""
    return conversation.user_turn_count() >= threshold


def should_compact_due_to_messages(conversation: Conversation, threshold: int) -> bool:
    """Return True if len(conversation.messages) >= threshold."""
    return len(conversation.messages) >= threshold


def should_compact_on_turn_end(conversation: Conversation) -> bool:
    """Return True if the last message is a user turn (turn-end trigger)."""
    return bool(conversation.messages) and conversation.messages[-1].role == Role.USER


def should_compact(
    conversation: Conversation,
    token_threshold: int,
    turn_threshold: int,
    message_threshold: int,
    on_turn_end: bool = True,
) -> bool:
    """Composite trigger: any one of the four conditions fires compaction."""
    return any([
        should_compact_due_to_tokens(conversation, token_threshold),
        should_compact_due_to_turns(conversation, turn_threshold),
        should_compact_due_to_messages(conversation, message_threshold),
        on_turn_end and should_compact_on_turn_end(conversation),
    ])
