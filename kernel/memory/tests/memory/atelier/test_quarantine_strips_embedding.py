"""Quarantine strips embedding in place — Murat R-04 critical test.

This is the FM3.10 override (Req #35): quarantine is NOT a
state-field-only operation. The embedding itself must be destroyed,
not just the state flipped. Without this, a quarantined record's
residual embedding stays queryable through pgvector index hits even
though the state field says "quarantined."

Invariants under test:

1. **Pre-quarantine.** A matching query returns the record in the
   top-K.

2. **Post-quarantine — direct.** Looking at the internal stored row,
   the embedding is an empty frozenset (the "strip in place" — §8.7).
   state is QUARANTINED. state_snapshot_version has advanced.
   reason_hash is set.

3. **Post-quarantine — via retrieval.** The same matching query that
   returned the record before quarantine now returns zero hits. This
   is the end-to-end property: quarantined records are invisible to
   the retrieval path even if similarity was 1.0 before.

4. **QuarantineResult.embedding_stripped is True.** The caller has
   explicit confirmation that the strip happened.

5. **Idempotence.** Re-quarantining an already-quarantined entry is a
   no-op beyond bumping state_snapshot_version.

6. **Missing entry.** Quarantining a non-existent entry_id raises
   MemoryRecordNotFound.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from praxis.kernel.memory._internal.atelier.store import (
    AtelierStore,
    _AtelierEntryState,
)
from praxis.kernel.memory.models import (
    DecisionDraft,
    EvidenceItem,
    MemoryRecordNotFound,
    QuarantineReason,
)

TENANT = "atelier-quarantine-tenant"


def _draft(text: str = "pricing decision for Q3") -> DecisionDraft:
    return DecisionDraft(
        decision=text,
        rationale="based on conversion data from segment X",
        alternatives_considered=["delay to Q4"],
        evidence=[EvidenceItem(source="call-17", excerpt="customer demand signal")],
        confidence=0.85,
        captured_at=datetime(2026, 4, 12, tzinfo=timezone.utc),
    )


# =============================================================================
# Pre/post quarantine retrieval visibility
# =============================================================================


async def test_decision_is_retrievable_before_quarantine() -> None:
    store = AtelierStore(tenant_hash=TENANT)
    record = await store.store_decision(TENANT, _draft())

    result = await store.retrieve_decisions(TENANT, "pricing Q3", top_k=5)
    assert len(result.hits) == 1
    assert result.hits[0].entry_id == record.entry_id


async def test_decision_is_NOT_retrievable_after_quarantine() -> None:
    """R-04 end-to-end property."""
    store = AtelierStore(tenant_hash=TENANT)
    record = await store.store_decision(TENANT, _draft())

    # Before quarantine — visible.
    before = await store.retrieve_decisions(TENANT, "pricing Q3", top_k=5)
    assert len(before.hits) == 1

    # Quarantine.
    result = await store.flag_and_quarantine(
        TENANT, record.entry_id, QuarantineReason.POISONED, free_text="bad source"
    )
    assert result.embedding_stripped is True

    # After quarantine — invisible to retrieval.
    after = await store.retrieve_decisions(TENANT, "pricing Q3", top_k=5)
    assert after.hits == []


# =============================================================================
# Internal state: embedding stripped, state flipped, snapshot advanced
# =============================================================================


async def test_quarantine_strips_embedding_in_place_at_row_level() -> None:
    """White-box check: the stored row has empty embedding + QUARANTINED state."""
    store = AtelierStore(tenant_hash=TENANT)
    record = await store.store_decision(TENANT, _draft())
    original_entry = store._debug_get_entry(record.entry_id)
    assert original_entry is not None
    assert len(original_entry.embedding) > 0  # had content before

    await store.flag_and_quarantine(TENANT, record.entry_id, QuarantineReason.HALLUCINATION)

    quarantined_entry = store._debug_get_entry(record.entry_id)
    assert quarantined_entry is not None

    # Req #35 / FM3.10: embedding stripped in place.
    assert quarantined_entry.embedding == frozenset()
    assert quarantined_entry.state is _AtelierEntryState.QUARANTINED
    # State snapshot version advanced.
    assert quarantined_entry.state_snapshot_version != original_entry.state_snapshot_version
    # reason_hash set.
    assert quarantined_entry.reason_hash is not None
    # Draft content preserved for audit.
    assert quarantined_entry.draft.decision == original_entry.draft.decision


async def test_quarantine_result_carries_version_chain() -> None:
    store = AtelierStore(tenant_hash=TENANT)
    record = await store.store_decision(TENANT, _draft())

    result = await store.flag_and_quarantine(TENANT, record.entry_id, QuarantineReason.OUTDATED)
    assert result.entry_id == record.entry_id
    assert result.previous_state_snapshot_version == record.state_snapshot_version
    assert result.new_state_snapshot_version != result.previous_state_snapshot_version
    assert result.embedding_stripped is True


# =============================================================================
# Edge cases
# =============================================================================


async def test_quarantine_nonexistent_entry_raises_not_found() -> None:
    store = AtelierStore(tenant_hash=TENANT)
    with pytest.raises(MemoryRecordNotFound):
        await store.flag_and_quarantine(TENANT, "nonexistent-entry-id", QuarantineReason.OUTDATED)


async def test_quarantine_is_idempotent_beyond_snapshot_bump() -> None:
    """Re-quarantining a quarantined entry does not error and advances snapshot."""
    store = AtelierStore(tenant_hash=TENANT)
    record = await store.store_decision(TENANT, _draft())

    r1 = await store.flag_and_quarantine(TENANT, record.entry_id, QuarantineReason.POISONED)
    r2 = await store.flag_and_quarantine(TENANT, record.entry_id, QuarantineReason.POISONED)

    assert r1.embedding_stripped is True
    assert r2.embedding_stripped is True
    assert r1.new_state_snapshot_version != r2.new_state_snapshot_version
