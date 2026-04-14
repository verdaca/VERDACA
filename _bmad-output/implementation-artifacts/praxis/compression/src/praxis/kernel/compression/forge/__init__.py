"""Forge — deterministic, zero-LLM conversation compaction.

Public API (architecture §3.2.2):
    Compactor(config=CompactionConfig()) — stateless compactor
    CompactionConfig — thresholds and switches
    Conversation, ConversationMessage — message models
    CompactionResult — output

Exceptions:
    ForgeError, CompactionError, ReasoningExtractionError, TemplateRenderError
"""
from .compactor import CompactionConfig, Compactor
from .errors import CompactionError, ForgeError, ReasoningExtractionError, TemplateRenderError
from .models import (
    CompactionRange,
    CompactionResult,
    Conversation,
    ConversationMessage,
    Role,
)

__all__ = [
    "Compactor",
    "CompactionConfig",
    "Conversation",
    "ConversationMessage",
    "Role",
    "CompactionResult",
    "CompactionRange",
    "ForgeError",
    "CompactionError",
    "ReasoningExtractionError",
    "TemplateRenderError",
]
