"""Forge data models — conversation message and compaction result types."""
from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ConversationMessage(BaseModel):
    """Canonical message representation for Forge (Pydantic v2, frozen)."""

    model_config = ConfigDict(frozen=True, extra="allow")

    role: Role
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    reasoning_details: str | None = None
    droppable: bool = False
    synthetic: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def is_tool_use(self) -> bool:
        return bool(self.tool_calls)

    def is_tool_result(self) -> bool:
        return self.role == Role.TOOL and self.tool_call_id is not None


class Conversation(BaseModel):
    """Ordered sequence of messages with token accounting."""

    model_config = ConfigDict(frozen=True)

    messages: list[ConversationMessage] = Field(default_factory=list)
    provider: str = "anthropic"
    session_id: str | None = None

    def total_tokens(self) -> int:
        """Rough token estimate: 4 chars ≈ 1 token (heuristic, no SDK call)."""
        total_chars = sum(
            len(m.content) + sum(len(str(tc)) for tc in (m.tool_calls or []))
            for m in self.messages
        )
        return max(1, total_chars // 4)

    def user_turn_count(self) -> int:
        return sum(1 for m in self.messages if m.role == Role.USER)


class CompactionRange(BaseModel):
    """Index range [start, end) in the message list that was compacted."""

    model_config = ConfigDict(frozen=True)

    start: int
    end: int  # exclusive


class CompactionResult(BaseModel):
    """Output of Compactor.compact()."""

    model_config = ConfigDict(frozen=True)

    compacted: bool
    conversation: Conversation
    messages_before: int
    messages_after: int
    tokens_saved: int = 0
    reasoning_preserved: bool = True
    reasoning_drift_detected: bool = False
    reason: str | None = None  # why compaction was skipped or what happened
    range: CompactionRange | None = None
    forge_tags: dict[str, str] = Field(default_factory=dict)
