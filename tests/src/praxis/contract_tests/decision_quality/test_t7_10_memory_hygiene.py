"""T7.10 Memory hygiene — Governance & Decision-Quality (T7) tier.

Literature source: Zhong et al. (2024) MemoryBank
(verdaca-literature-review.md §"Assessment Approaches to Carry Forward for
Murat", row "Memory causes stale, irrelevant, or private context leakage").
The lever: long-session memory must support store / query / promote / revoke,
carry provenance, and isolate channel/workspace boundaries so private context
from one channel does not leak into another.

Verdaca operationalization, asserted at the MemoryPort CONTRACT level (stub
adapter — the FakeMemory MemoryPort conformer; live Letta/Mem0 variant is the
T7.10-live counterpart, out of scope this pass):
    1. store/query/promote/revoke round-trip across the full Protocol surface.
    2. provenance present — stored entries carry a source span + correlation id;
       the gateway-written entry carries session_id + workspace_id provenance.
    3. no cross-channel/workspace leak — entries written under one workspace
       carry that workspace's provenance, distinguishable from another's.

PASS: full Protocol round-trip + provenance present + workspace boundary
distinguishable. Hermetic — no live memory backend, no creds. Plain tests
(NO @pytest.mark.no_waiver; 14/9/23 pin untouched).
"""

from __future__ import annotations

from praxis.contract_tests.ports.gateway_contract_fakes import (
    FakeMemory,
    make_ctx,
    make_gateway_harness,
    make_intent,
)
from praxis.ports.memory import (
    MemoryEntry,
    MemoryHit,
    MemoryPort,
    MemoryQuery,
    PromotedMemory,
    PromotionRationale,
    PromotionTier,
    RevokedPromotion,
    StoredMemory,
)

_CID = "t7-10-correlation"


def _entry(content: str, *, workspace_id: str, channel: str) -> MemoryEntry:
    return MemoryEntry(
        schema_version=1,
        correlation_id=_CID,
        idempotency_key=f"t7-10-{workspace_id}-{channel}",
        content=content,
        metadata={"workspace_id": workspace_id, "channel": channel},
        confidence=0.9,
        source_span_id=f"span-{workspace_id}-{channel}",
    )


def _rationale() -> PromotionRationale:
    return PromotionRationale(
        schema_version=1,
        correlation_id=_CID,
        idempotency_key="t7-10-promote",
        threshold_met=0.9,
        threshold_required=0.75,
        promoting_actor="t7-10-actor",
        evidence_span_ids=["evidence-span-1"],
    )


def test_T7_10_MEMORY_conforms_to_port_protocol() -> None:
    """The stub adapter under test structurally satisfies MemoryPort — the
    hygiene contract is asserted against the real Protocol surface."""
    assert isinstance(FakeMemory(), MemoryPort)


def test_T7_10_MEMORY_store_query_promote_revoke_roundtrip() -> None:
    """MemoryBank lifecycle: store → query → promote → revoke exercises the
    full Protocol surface and returns the contractual DTOs at each hop."""
    memory: MemoryPort = FakeMemory()

    stored = memory.store(_entry("buyer context", workspace_id="ws-1", channel="cli"))
    assert isinstance(stored, StoredMemory)

    hits = memory.query(
        MemoryQuery(
            schema_version=1,
            correlation_id=_CID,
            idempotency_key=None,
            query_text="buyer context",
            k=5,
        )
    )
    assert len(hits) >= 1
    hit = hits[0]
    assert isinstance(hit, MemoryHit)
    assert 0.0 <= hit.confidence <= 1.0
    assert hit.tier in {"working", "session", "promoted"}

    promoted = memory.promote(
        hit_id=hit.hit_id,
        target_tier=PromotionTier.SESSION,
        rationale=_rationale(),
    )
    assert isinstance(promoted, PromotedMemory)
    assert promoted.promotion_id

    revoked = memory.revoke_promotion(promotion_id=promoted.promotion_id, reason="t7-10")
    assert isinstance(revoked, RevokedPromotion)
    assert revoked.promotion_id == promoted.promotion_id
    assert revoked.reason == "t7-10"


def test_T7_10_MEMORY_stored_entries_carry_provenance() -> None:
    """Provenance present: every stored entry retains its correlation id and a
    source span, so a stored memory can be traced to where it came from."""
    memory = FakeMemory()
    memory.store(_entry("private ws-1 note", workspace_id="ws-1", channel="teams"))

    assert len(memory.stores) == 1
    entry = memory.stores[0]
    assert entry.correlation_id == _CID
    assert entry.source_span_id == "span-ws-1-teams"
    assert entry.metadata["workspace_id"] == "ws-1"
    assert entry.metadata["channel"] == "teams"


def test_T7_10_MEMORY_no_cross_channel_leak_provenance_isolation() -> None:
    """No cross-channel/workspace leak: entries written under distinct
    workspace/channel pairs remain distinguishable by their provenance — the
    boundary signal a backend uses to scope queries and prevent private
    context from one channel leaking into another."""
    memory = FakeMemory()
    memory.store(_entry("ws-1 secret", workspace_id="ws-1", channel="slack"))
    memory.store(_entry("ws-2 secret", workspace_id="ws-2", channel="teams"))

    provenance = {
        (e.metadata["workspace_id"], e.metadata["channel"]) for e in memory.stores
    }
    assert provenance == {("ws-1", "slack"), ("ws-2", "teams")}
    # Each workspace's content is bound to its own provenance, never merged.
    by_ws = {e.metadata["workspace_id"]: e.content for e in memory.stores}
    assert by_ws["ws-1"] == "ws-1 secret"
    assert by_ws["ws-2"] == "ws-2 secret"


def test_T7_10_MEMORY_gateway_writes_session_scoped_provenance(tmp_path) -> None:
    """End-to-end: a gateway run stores its recommendation with session +
    workspace provenance, so memory written during execution is channel/
    workspace-scoped by construction (MemoryBank leak-prevention lever)."""
    harness = make_gateway_harness(tmp_path)
    result = harness.gateway.execute(
        make_intent(workspace_id="workspace-1"), make_ctx()
    )

    assert len(harness.memory.stores) == 1
    written = harness.memory.stores[0]
    assert written.metadata["session_id"] == result.session.session_id
    assert written.metadata["workspace_id"] == "workspace-1"
    assert written.source_span_id  # provenance span present
