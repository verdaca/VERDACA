"""Round-trip tests for AtelierStore decision capture and retrieval.

Exercises:
  - store_decision → retrieve_decisions round-trip with scoring
  - store_decision at multiple entries → retrieval ranks by similarity
  - delete by entry_id → retrieval returns zero hits
  - delete full tenant → empty store
  - export returns record counts consistent with store state
  - health reports OK
  - Tenant guard on every mutating method
  - Non-decision methods raise NotImplementedError as designed
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from praxis.kernel.memory._internal.atelier.store import AtelierStore
from praxis.kernel.memory.models import (
    DecisionDraft,
    DeleteCriteria,
    EvidenceItem,
    ExportCriteria,
    FactDraft,
    ReasoningStep,
    TaskOutcomeDraft,
    TaskSignature,
    TenantIdentityError,
)

TENANT = "atelier-roundtrip-tenant"


def _new_store() -> AtelierStore:
    return AtelierStore(tenant_hash=TENANT)


def _decision_draft(
    *,
    decision: str = "ship v1 on Tuesday",
    rationale: str = "compound delay risk outweighs polish",
    confidence: float = 0.82,
) -> DecisionDraft:
    return DecisionDraft(
        decision=decision,
        rationale=rationale,
        alternatives_considered=["delay 1 week", "ship with bug"],
        evidence=[EvidenceItem(source="user-interview-12", excerpt="pain is acute")],
        confidence=confidence,
        captured_at=datetime(2026, 4, 12, 21, 0, tzinfo=timezone.utc),
    )


# =============================================================================
# Store + retrieve round-trip
# =============================================================================


async def test_store_decision_returns_record_with_persistence_columns() -> None:
    store = _new_store()
    draft = _decision_draft()
    record = await store.store_decision(TENANT, draft)

    assert record.tenant_hash == TENANT
    assert record.decision == draft.decision
    assert record.rationale == draft.rationale
    assert record.confidence == draft.confidence
    assert record.state_snapshot_version
    assert record.entry_id


async def test_retrieve_decisions_finds_stored_decision_by_keyword() -> None:
    store = _new_store()
    await store.store_decision(TENANT, _decision_draft())
    await store.store_decision(
        TENANT,
        _decision_draft(
            decision="rewrite auth middleware",
            rationale="legal compliance requires session-token cleanup",
        ),
    )

    result = await store.retrieve_decisions(TENANT, "Tuesday ship", top_k=5)
    # The first decision has "ship Tuesday"; the second doesn't.
    assert len(result.hits) >= 1
    top = result.hits[0]
    assert top.record_type == "decision"
    assert "Tuesday" in top.record.decision  # type: ignore[union-attr]


async def test_retrieve_decisions_respects_top_k_cap() -> None:
    store = _new_store()
    # Store 5 decisions all matching the query.
    for i in range(5):
        await store.store_decision(
            TENANT,
            _decision_draft(
                decision=f"decision-{i} about pricing",
                rationale="pricing rationale",
            ),
        )
    result = await store.retrieve_decisions(TENANT, "pricing", top_k=3)
    assert len(result.hits) == 3


async def test_retrieve_decisions_returns_zero_hits_for_unrelated_query() -> None:
    store = _new_store()
    await store.store_decision(TENANT, _decision_draft())
    result = await store.retrieve_decisions(TENANT, "quantum harmonics xylophone", top_k=5)
    assert result.hits == []


async def test_retrieve_decisions_validates_top_k() -> None:
    store = _new_store()
    with pytest.raises(ValueError):
        await store.retrieve_decisions(TENANT, "any", top_k=0)


async def test_retrieve_decisions_validates_non_empty_query() -> None:
    store = _new_store()
    with pytest.raises(ValueError):
        await store.retrieve_decisions(TENANT, "   ")


# =============================================================================
# Delete + export
# =============================================================================


async def test_delete_by_entry_id_removes_from_retrieval() -> None:
    store = _new_store()
    record = await store.store_decision(TENANT, _decision_draft())

    result = await store.retrieve_decisions(TENANT, "Tuesday", top_k=5)
    assert len(result.hits) == 1

    delete_result = await store.delete(TENANT, DeleteCriteria(entry_ids=[record.entry_id]))
    assert delete_result.deleted_entry_count == 1

    result_after = await store.retrieve_decisions(TENANT, "Tuesday", top_k=5)
    assert result_after.hits == []


async def test_delete_full_tenant_clears_store() -> None:
    store = _new_store()
    for _ in range(3):
        await store.store_decision(TENANT, _decision_draft())

    delete_result = await store.delete(TENANT, DeleteCriteria(full_tenant=True))
    assert delete_result.deleted_entry_count == 3
    assert delete_result.crypto_shred_initiated is True

    after = await store.retrieve_decisions(TENANT, "Tuesday", top_k=5)
    assert after.hits == []


async def test_delete_requires_criteria() -> None:
    store = _new_store()
    with pytest.raises(ValueError):
        await store.delete(TENANT, DeleteCriteria())


async def test_export_full_tenant_counts_all_decisions() -> None:
    store = _new_store()
    for _ in range(4):
        await store.store_decision(TENANT, _decision_draft())
    result = await store.export(TENANT, ExportCriteria(full_tenant=True))
    assert result.record_count == 4


async def test_export_by_entry_ids_counts_matches_only() -> None:
    store = _new_store()
    r1 = await store.store_decision(TENANT, _decision_draft())
    r2 = await store.store_decision(TENANT, _decision_draft())
    result = await store.export(
        TENANT, ExportCriteria(entry_ids=[r1.entry_id, r2.entry_id, "non-existent"])
    )
    assert result.record_count == 2


async def test_export_requires_criteria() -> None:
    store = _new_store()
    with pytest.raises(ValueError):
        await store.export(TENANT, ExportCriteria())


# =============================================================================
# Health
# =============================================================================


async def test_health_reports_ok() -> None:
    store = _new_store()
    report = await store.health()
    assert report.overall.value == "ok"
    assert report.backends[0].backend == "atelier"


# =============================================================================
# Tenant guard
# =============================================================================


async def test_store_decision_rejects_wrong_tenant() -> None:
    store = _new_store()
    with pytest.raises(TenantIdentityError):
        await store.store_decision("wrong", _decision_draft())


async def test_retrieve_decisions_rejects_wrong_tenant() -> None:
    store = _new_store()
    with pytest.raises(TenantIdentityError):
        await store.retrieve_decisions("wrong", "query")


async def test_delete_rejects_wrong_tenant() -> None:
    store = _new_store()
    with pytest.raises(TenantIdentityError):
        await store.delete("wrong", DeleteCriteria(full_tenant=True))


async def test_export_rejects_wrong_tenant() -> None:
    store = _new_store()
    with pytest.raises(TenantIdentityError):
        await store.export("wrong", ExportCriteria(full_tenant=True))


# =============================================================================
# Non-decision methods — raise NotImplementedError
# =============================================================================


async def test_store_task_outcome_raises_not_implemented() -> None:
    store = _new_store()
    sig = TaskSignature(
        task_type="t",
        input_hash="a" * 64,
        agents_involved=("x",),
        context_fingerprint="f",
    )
    draft = TaskOutcomeDraft(
        quality_score=0.8,
        quality_confidence=0.7,
        cost_usd=1.0,
        reasoning_trace=[ReasoningStep(step_index=0, agent_id="x", summary="s")],
        approach_summary="summary",
    )
    with pytest.raises(NotImplementedError):
        await store.store_task_outcome(TENANT, sig, draft)


async def test_store_fact_raises_not_implemented() -> None:
    store = _new_store()
    with pytest.raises(NotImplementedError):
        await store.store_fact(TENANT, "agent", "run", FactDraft(fact="x"))


async def test_retrieve_facts_raises_not_implemented() -> None:
    store = _new_store()
    with pytest.raises(NotImplementedError):
        await store.retrieve_facts(TENANT, "agent", "run", "query")


async def test_retrieve_similar_tasks_raises_not_implemented() -> None:
    store = _new_store()
    sig = TaskSignature(
        task_type="t",
        input_hash="a" * 64,
        agents_involved=("x",),
        context_fingerprint="f",
    )
    with pytest.raises(NotImplementedError):
        await store.retrieve_similar_tasks(TENANT, sig)
