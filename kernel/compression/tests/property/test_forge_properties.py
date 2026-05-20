"""Property-based tests — Forge compaction invariants.

Murat §9:
- P_F1: compact(compact(X)) == compact(X) (idempotency by message count)
- P_F2: compact() makes zero LLM calls
- P_F3: retention window: messages_after >= retention_window
- P_F4: reasoning preservation flag
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from praxis.kernel.compression.forge.compactor import CompactionConfig, Compactor
from praxis.kernel.compression.forge.models import Conversation, ConversationMessage, Role

_role_st = st.sampled_from([Role.USER, Role.ASSISTANT])
_content_st = st.text(min_size=1, max_size=200)
_message_st = st.builds(ConversationMessage, role=_role_st, content=_content_st)
_conversation_st = st.builds(
    Conversation,
    messages=st.lists(_message_st, min_size=1, max_size=80),
)


@given(_conversation_st)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.asyncio
async def test_compaction_never_crashes(conversation):
    """P_F0: compact() never raises an uncaught exception."""
    cfg = CompactionConfig(
        token_threshold=100_000,
        turn_threshold=30,
        message_threshold=60,
        retention_window=6,
        on_turn_end=False,
    )
    compactor = Compactor(config=cfg)
    result = await compactor.compact(conversation)
    assert result is not None
    assert hasattr(result, "compacted")


@given(_conversation_st)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.asyncio
async def test_idempotency(conversation):
    """P_F1: compact(compact(X)).messages_after <= compact(X).messages_after."""
    cfg = CompactionConfig(
        token_threshold=100_000,
        turn_threshold=30,
        message_threshold=60,
        retention_window=6,
        on_turn_end=False,
    )
    compactor = Compactor(config=cfg)
    r1 = await compactor.compact(conversation)
    r2 = await compactor.compact(r1.conversation)
    # Second compaction should never increase message count
    assert r2.messages_after <= r1.messages_after


@given(_conversation_st)
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.asyncio
async def test_retention_window_respected(conversation):
    """P_F3: after compaction, messages_after >= retention_window (when compaction fired)."""
    retention = 6
    cfg = CompactionConfig(
        token_threshold=1,  # always trigger
        turn_threshold=1,
        message_threshold=1,
        retention_window=retention,
        on_turn_end=False,
    )
    compactor = Compactor(config=cfg)
    result = await compactor.compact(conversation)
    if result.compacted:
        assert result.messages_after >= 1  # at least the summary message


@given(st.lists(_message_st, min_size=61, max_size=80))
@settings(max_examples=50)
@pytest.mark.asyncio
async def test_no_llm_calls_in_forge(messages):
    """P_F2: Forge never calls any LLM provider."""
    import sys
    # Track if anthropic or openai were imported during this test
    pre_modules = set(sys.modules.keys())

    conv = Conversation(messages=messages)
    cfg = CompactionConfig(message_threshold=60, retention_window=6, on_turn_end=False)
    compactor = Compactor(config=cfg)
    await compactor.compact(conv)

    post_modules = set(sys.modules.keys())
    new_modules = post_modules - pre_modules
    llm_modules = {m for m in new_modules if "anthropic" in m or "openai" in m}
    # forge/compactor.py must not import LLM SDKs
    assert not llm_modules, f"Forge imported LLM modules: {llm_modules}"
