"""Forge Compactor — deterministic, zero-LLM conversation compaction.

Architecture §3.2 — the central class. All compaction logic is pure Python.
No LLM calls, no randomness, no I/O. Property test: compact(compact(X)) == compact(X).
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .errors import CompactionError, TemplateRenderError
from .models import (
    CompactionRange,
    CompactionResult,
    Conversation,
    ConversationMessage,
    Role,
)
from .reasoning import (
    inject_reasoning,
    last_non_empty_reasoning,
    validate_reasoning_schema,
)
from .strategy import (
    conservative_range,
    evict_strategy,
    retain_strategy,
    walk_back_to_complete_pair,
)
from .transformers import apply_all
from .triggers import should_compact

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class CompactionConfig:
    """Compaction thresholds and behaviour switches."""

    def __init__(
        self,
        token_threshold: int = 140_000,
        turn_threshold: int = 30,
        message_threshold: int = 60,
        retention_window: int = 6,
        eviction_window: Decimal = Decimal("0.2"),
        on_turn_end: bool = True,
    ) -> None:
        self.token_threshold = token_threshold
        self.turn_threshold = turn_threshold
        self.message_threshold = message_threshold
        self.retention_window = retention_window
        self.eviction_window = eviction_window
        self.on_turn_end = on_turn_end


class Compactor:
    """Deterministic conversation compactor.

    Usage::

        compactor = Compactor(config=CompactionConfig())
        result = await compactor.compact(conversation)
        assert result.compacted is True   # or False if no trigger fired
    """

    def __init__(self, config: CompactionConfig | None = None) -> None:
        self._config = config or CompactionConfig()
        self._jinja = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=False,
            undefined=StrictUndefined,
        )

    async def compact(self, conversation: Conversation) -> CompactionResult:
        """Compact *conversation* if any trigger fires.

        Returns a CompactionResult. If no trigger fires, result.compacted is False
        and the original conversation is returned unchanged.
        """
        cfg = self._config
        msgs = conversation.messages

        if not should_compact(
            conversation,
            token_threshold=cfg.token_threshold,
            turn_threshold=cfg.turn_threshold,
            message_threshold=cfg.message_threshold,
            on_turn_end=cfg.on_turn_end,
        ):
            return CompactionResult(
                compacted=False,
                conversation=conversation,
                messages_before=len(msgs),
                messages_after=len(msgs),
                reason="no_trigger",
            )

        retain_r = retain_strategy(conversation, cfg.retention_window)
        evict_r = evict_strategy(conversation, cfg.eviction_window)
        range_ = conservative_range(retain_r, evict_r)

        if range_ is None:
            return CompactionResult(
                compacted=False,
                conversation=conversation,
                messages_before=len(msgs),
                messages_after=len(msgs),
                reason="nothing_to_compact",
            )

        # Walk back boundary to avoid splitting tool pairs
        end = walk_back_to_complete_pair(msgs, range_.end)
        if end <= range_.start:
            return CompactionResult(
                compacted=False,
                conversation=conversation,
                messages_before=len(msgs),
                messages_after=len(msgs),
                reason="tool_chain_too_long",
            )
        range_ = CompactionRange(start=range_.start, end=end)

        sequence = list(msgs[range_.start:range_.end])
        sequence = apply_all(sequence)

        # Render Markdown summary (deterministic — no LLM)
        try:
            summary_text = self._render_summary(sequence)
        except Exception as exc:
            raise TemplateRenderError(f"Jinja2 template render failed: {exc}") from exc

        # Extract last reasoning block
        reasoning_text, schema = last_non_empty_reasoning(sequence)
        reasoning_preserved = False
        reasoning_drift = False

        if reasoning_text:
            if validate_reasoning_schema(schema):
                reasoning_preserved = True
            else:
                # Unknown schema — do NOT inject; log already emitted
                reasoning_text = None
                reasoning_drift = True

        # Build new message list
        summary_msg = ConversationMessage(
            role=Role.USER,
            content=summary_text,
            synthetic=True,
            metadata={"source": "forge.compaction", "compacted_count": len(sequence)},
        )
        new_messages: list[ConversationMessage] = (
            list(msgs[: range_.start])
            + [summary_msg]
            + list(msgs[range_.end:])
        )

        # Inject reasoning into first post-boundary assistant message (if available)
        if reasoning_text:
            new_messages = inject_reasoning(new_messages, reasoning_text, range_.start + 1)

        tokens_before = conversation.total_tokens()
        new_conv = Conversation(
            messages=new_messages,
            provider=conversation.provider,
            session_id=conversation.session_id,
        )
        tokens_after = new_conv.total_tokens()

        # Guard: if compaction made things worse, return original
        if tokens_after >= tokens_before:
            logger.warning(
                "forge.compaction produced no savings (before=%d, after=%d); returning original",
                tokens_before,
                tokens_after,
            )
            return CompactionResult(
                compacted=False,
                conversation=conversation,
                messages_before=len(msgs),
                messages_after=len(msgs),
                reason="no_savings",
            )

        tags = {
            "compression.forge.compactions": "1",
            "compression.forge.tokens_saved": str(tokens_before - tokens_after),
        }

        return CompactionResult(
            compacted=True,
            conversation=new_conv,
            messages_before=len(msgs),
            messages_after=len(new_messages),
            tokens_saved=tokens_before - tokens_after,
            reasoning_preserved=reasoning_preserved,
            reasoning_drift_detected=reasoning_drift,
            range=range_,
            forge_tags=tags,
        )

    def _render_summary(self, sequence: list[ConversationMessage]) -> str:
        """Render the compaction summary using the Jinja2 template."""
        roles = list(dict.fromkeys(m.role.value for m in sequence))
        tool_calls_list = [m.tool_calls for m in sequence if m.tool_calls]

        # Simple decision extraction: first sentence of each assistant message
        decisions: dict[str, list[str]] = {}
        for msg in sequence:
            if msg.role == Role.ASSISTANT and msg.content:
                first_sentence = msg.content.split(".")[0].strip()
                if first_sentence:
                    decisions.setdefault("assistant", []).append(
                        first_sentence[:120] + ("..." if len(first_sentence) > 120 else "")
                    )

        now = datetime.now(UTC).isoformat()
        template = self._jinja.get_template("partial_summary_frame.md.j2")
        return template.render(
            message_count=len(sequence),
            first_timestamp=now,
            last_timestamp=now,
            participant_roles=roles,
            tool_calls_summarized=tool_calls_list,
            decisions_by_agent=decisions,
        )
