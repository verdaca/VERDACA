"""Forge compaction strategy — range selection (retain window vs eviction window)."""
from __future__ import annotations

from decimal import Decimal

from .models import CompactionRange, Conversation, ConversationMessage, Role


def retain_strategy(
    conversation: Conversation,
    retention_window: int,
) -> CompactionRange | None:
    """Return the range [0, len - retention_window) to compact.

    The last *retention_window* messages are NEVER touched.
    Returns None if there are fewer messages than the retention window.
    """
    n = len(conversation.messages)
    if n <= retention_window:
        return None
    return CompactionRange(start=0, end=n - retention_window)


def evict_strategy(
    conversation: Conversation,
    eviction_window: Decimal,
) -> CompactionRange | None:
    """Return the range based on percentage eviction.

    Compacts the oldest (1 - eviction_window) fraction of messages.
    Returns None if there is nothing to compact.
    """
    n = len(conversation.messages)
    evict_count = int(n * (Decimal("1") - eviction_window))
    if evict_count <= 0:
        return None
    return CompactionRange(start=0, end=evict_count)


def conservative_range(
    retain: CompactionRange | None,
    evict: CompactionRange | None,
) -> CompactionRange | None:
    """Return the more conservative (smaller) of the two ranges.

    More conservative = smaller end index = retains more messages.
    """
    if retain is None:
        return evict
    if evict is None:
        return retain
    # Pick the range with the smaller end index
    return retain if retain.end <= evict.end else evict


def walk_back_to_complete_pair(
    messages: list[ConversationMessage],
    end: int,
) -> int:
    """Walk *end* backward until we are not splitting a tool_use/tool_result pair.

    A tool_use message must always be followed by its tool_result.
    If the compaction boundary falls between them, we move the boundary back.

    Returns the adjusted end index.
    """
    if end <= 0 or end > len(messages):
        return end

    # Check if messages[end - 1] is a tool_use without its paired tool_result
    # in the retained portion (messages[end:])
    adjusted = end
    while adjusted > 0:
        msg = messages[adjusted - 1]
        if msg.is_tool_use():
            # Look for the tool_result immediately after in the retained portion
            # (it would be messages[adjusted], but that's the boundary — it's not compacted)
            # Actually: we're compacting messages[0:adjusted], so messages[adjusted] is kept.
            # If messages[adjusted - 1] is tool_use, check messages[adjusted] is tool_result.
            if adjusted < len(messages) and messages[adjusted].is_tool_result():
                # The pair is split: tool_use at adjusted-1 (compacted) and
                # tool_result at adjusted (retained). Move boundary back.
                adjusted -= 1
            else:
                break
        else:
            break
    return adjusted
