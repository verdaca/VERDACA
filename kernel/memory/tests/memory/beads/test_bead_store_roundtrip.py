"""Round-trip tests for BeadsStore.

Exercises the MemoryProtocol write path end-to-end:

- store_task_outcome → TaskOutcomeRecord returned with persistence columns
- store_decision → DecisionRecord
- store_fact → FactRecord
- delete / flag_and_quarantine → audit bead appended
- chain invariants: length grows by exactly one per write; head pointer
  advances; parent pointers form a valid back-chain from head to genesis

Plus the critical tenant guard — a mismatched tenant_id raises
TenantIdentityError, never silently succeeds.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from praxis.kernel.memory._internal.beads.content_hash import verify_bead_hash
from praxis.kernel.memory._internal.beads.models import BeadOperationType
from praxis.kernel.memory._internal.beads.store import BeadsStore
from praxis.kernel.memory.models import (
    DecisionDraft,
    DeleteCriteria,
    EvidenceItem,
    ExportCriteria,
    FactDraft,
    QuarantineReason,
    ReasoningStep,
    TaskOutcomeDraft,
    TaskSignature,
    TenantIdentityError,
)

# NOTE: asyncio_mode = "auto" in pyproject.toml auto-marks coroutine tests,
# so we do not need `pytestmark = pytest.mark.asyncio`. A module-level mark
# triggers a warning when applied to the one sync test below.


TENANT = "tenant-roundtrip-fixture"


def _new_store() -> BeadsStore:
    return BeadsStore(tenant_hash=TENANT)


def _signature() -> TaskSignature:
    return TaskSignature(
        task_type="strategic_advisory",
        input_hash="a" * 64,
        agents_involved=("mary", "winston"),
        context_fingerprint="ctx-1",
    )


def _outcome_draft() -> TaskOutcomeDraft:
    return TaskOutcomeDraft(
        quality_score=0.87,
        quality_confidence=0.75,
        cost_usd=3.21,
        reasoning_trace=[ReasoningStep(step_index=0, agent_id="mary", summary="assess landscape")],
        approach_summary="Pick option A; hedge with B",
    )


def _decision_draft() -> DecisionDraft:
    return DecisionDraft(
        decision="ship v1 on Tuesday",
        rationale="compound risk of delay outweighs polish budget",
        alternatives_considered=["delay 1 week", "ship with known bug"],
        evidence=[EvidenceItem(source="user-interview-12", excerpt="pain is acute")],
        confidence=0.82,
        captured_at=datetime(2026, 4, 12, 21, 0, 0, tzinfo=timezone.utc),
    )


def _fact_draft() -> FactDraft:
    return FactDraft(fact="ICP segment X converts at 3× rate", source_excerpt="call 7")


# =============================================================================
# Construction + genesis
# =============================================================================


def test_new_store_has_genesis_bead() -> None:
    store = _new_store()
    assert len(store) == 1
    assert store.head is not None
    chain = store.iter_chain()
    assert len(chain) == 1
    assert chain[0].operation_type == BeadOperationType.GENESIS
    assert verify_bead_hash(chain[0]) is True


# =============================================================================
# Store round-trips
# =============================================================================


async def test_store_task_outcome_appends_bead_and_returns_record() -> None:
    store = _new_store()
    initial_len = len(store)
    sig = _signature()
    outcome = _outcome_draft()

    record = await store.store_task_outcome(TENANT, sig, outcome)

    assert len(store) == initial_len + 1
    assert record.tenant_hash == TENANT
    assert record.signature == sig
    assert record.quality_score == outcome.quality_score
    assert record.cost_usd == outcome.cost_usd
    assert record.state_snapshot_version == store.head
    assert record.record_type == "task_outcome"
    # entry_id is fresh
    assert record.entry_id and len(record.entry_id) >= 8


async def test_store_decision_appends_bead_and_returns_record() -> None:
    store = _new_store()
    draft = _decision_draft()
    record = await store.store_decision(TENANT, draft)
    assert record.tenant_hash == TENANT
    assert record.decision == draft.decision
    assert record.confidence == draft.confidence
    assert record.record_type == "decision"
    assert store.iter_chain()[-1].operation_type == BeadOperationType.STORE_DECISION


async def test_store_fact_appends_bead_and_returns_record() -> None:
    store = _new_store()
    draft = _fact_draft()
    record = await store.store_fact(TENANT, "winston", "run-42", draft)
    assert record.tenant_hash == TENANT
    assert record.fact == draft.fact
    assert record.record_type == "fact"
    assert store.iter_chain()[-1].operation_type == BeadOperationType.STORE_FACT


# =============================================================================
# Chain invariants
# =============================================================================


async def test_chain_grows_by_exactly_one_per_operation() -> None:
    store = _new_store()
    start = len(store)
    await store.store_task_outcome(TENANT, _signature(), _outcome_draft())
    await store.store_decision(TENANT, _decision_draft())
    await store.store_fact(TENANT, "winston", "run-1", _fact_draft())
    await store.flag_and_quarantine(TENANT, "entry-x", QuarantineReason.OUTDATED)
    await store.delete(TENANT, DeleteCriteria(entry_ids=["entry-y"]))
    assert len(store) == start + 5


async def test_chain_parent_pointers_form_back_chain() -> None:
    store = _new_store()
    for _ in range(5):
        await store.store_decision(TENANT, _decision_draft())
    chain = store.iter_chain()
    assert len(chain) == 6  # genesis + 5 decisions
    # Every bead except genesis points to its immediate predecessor.
    for i in range(1, len(chain)):
        assert chain[i].previous_bead_hash == chain[i - 1].bead_hash
    # Every bead's hash is self-consistent.
    for bead in chain:
        assert verify_bead_hash(bead) is True


# =============================================================================
# Tenant guard — defense in depth
# =============================================================================


async def test_store_task_outcome_rejects_wrong_tenant() -> None:
    store = _new_store()
    with pytest.raises(TenantIdentityError):
        await store.store_task_outcome("wrong-tenant", _signature(), _outcome_draft())
    # Chain length unchanged — rejection happened before any append.
    assert len(store) == 1


async def test_store_decision_rejects_wrong_tenant() -> None:
    store = _new_store()
    with pytest.raises(TenantIdentityError):
        await store.store_decision("wrong-tenant", _decision_draft())


async def test_store_fact_rejects_wrong_tenant() -> None:
    store = _new_store()
    with pytest.raises(TenantIdentityError):
        await store.store_fact("wrong-tenant", "agent", "run", _fact_draft())


async def test_delete_rejects_wrong_tenant() -> None:
    store = _new_store()
    with pytest.raises(TenantIdentityError):
        await store.delete("wrong-tenant", DeleteCriteria(full_tenant=True))


async def test_flag_and_quarantine_rejects_wrong_tenant() -> None:
    store = _new_store()
    with pytest.raises(TenantIdentityError):
        await store.flag_and_quarantine("wrong-tenant", "entry-x", QuarantineReason.OUTDATED)


# =============================================================================
# Retrieval (Beads returns empty results — not a semantic store)
# =============================================================================


async def test_retrieval_methods_return_empty_results() -> None:
    store = _new_store()
    r1 = await store.retrieve_similar_tasks(TENANT, _signature())
    r2 = await store.retrieve_decisions(TENANT, "any query")
    r3 = await store.retrieve_facts(TENANT, "agent", "run", "any query")
    for r in (r1, r2, r3):
        assert r.hits == []
        assert r.source_distribution.tenant_hits == 0
        assert r.source_distribution.seed_hits == 0


async def test_retrieve_similar_tasks_validates_top_k() -> None:
    store = _new_store()
    with pytest.raises(ValueError):
        await store.retrieve_similar_tasks(TENANT, _signature(), top_k=0)


async def test_retrieve_similar_tasks_validates_min_similarity() -> None:
    store = _new_store()
    with pytest.raises(ValueError):
        await store.retrieve_similar_tasks(TENANT, _signature(), min_similarity=1.5)


async def test_retrieve_decisions_validates_non_empty_query() -> None:
    store = _new_store()
    with pytest.raises(ValueError):
        await store.retrieve_decisions(TENANT, "   ")


# =============================================================================
# Delete + Quarantine + Export + Health
# =============================================================================


async def test_delete_records_audit_bead_and_returns_job_id() -> None:
    store = _new_store()
    result = await store.delete(TENANT, DeleteCriteria(entry_ids=["e1", "e2", "e3"]))
    assert result.deleted_entry_count == 3
    assert result.job_id
    assert result.crypto_shred_initiated is False
    assert store.iter_chain()[-1].operation_type == BeadOperationType.DELETE


async def test_delete_full_tenant_sets_crypto_shred_flag() -> None:
    store = _new_store()
    result = await store.delete(TENANT, DeleteCriteria(full_tenant=True))
    assert result.crypto_shred_initiated is True


async def test_delete_requires_criteria() -> None:
    store = _new_store()
    with pytest.raises(ValueError):
        await store.delete(TENANT, DeleteCriteria())


async def test_quarantine_reports_embedding_stripped() -> None:
    store = _new_store()
    result = await store.flag_and_quarantine(
        TENANT, "entry-1", QuarantineReason.HALLUCINATION, free_text="wrong claim"
    )
    assert result.entry_id == "entry-1"
    assert result.embedding_stripped is True
    # State snapshot version advanced.
    assert result.previous_state_snapshot_version != result.new_state_snapshot_version


async def test_export_returns_artifact_marker() -> None:
    store = _new_store()
    result = await store.export(TENANT, ExportCriteria(full_tenant=True))
    assert result.record_count == 0
    assert result.artifact_path
    assert result.access_token


async def test_export_requires_criteria() -> None:
    store = _new_store()
    with pytest.raises(ValueError):
        await store.export(TENANT, ExportCriteria())


async def test_health_reports_ok_after_genesis() -> None:
    store = _new_store()
    report = await store.health()
    assert report.overall.value == "ok"
    assert len(report.backends) == 1
    assert report.backends[0].backend == "beads"
