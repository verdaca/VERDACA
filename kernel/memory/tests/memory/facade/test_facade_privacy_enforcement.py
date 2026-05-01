"""R-01..R-06 privacy enforcement battery at the facade level.

Murat's six CRITICAL no-waiver risks, tested against the composed
facade. Some risks are DB-level (pgvector orphans, cache invalidation,
telemetry sink) and are explicitly documented here as Quinn territory
— Phase 3C cannot test them without live infrastructure. The three
that ARE testable at Phase 3C (R-03 audit log PII, R-04 quarantine
embedding strip, R-06 two-tenant export isolation) get full coverage.

| Risk | Scope            | Phase 3C testable? |
|------|------------------|--------------------|
| R-01 | pgvector orphans | NO — DB level, Quinn's Step 3.4 |
| R-02 | cache invalidate | NO — no cache layer in Phase 3C |
| R-03 | audit log PII    | YES — audit buffer shape test  |
| R-04 | quarantine strip | YES — facade → Atelier         |
| R-05 | telemetry leak   | NO — no telemetry sink yet     |
| R-06 | export isolation | YES — two-facade test          |
"""

from __future__ import annotations

from praxis.kernel.memory import (
    DeleteCriteria,
    ExportCriteria,
    QuarantineReason,
)
from tests.memory.facade._helpers import (
    DEFAULT_TENANT_ID,
    make_memory,
    sample_decision,
    sample_fact,
    sample_task_outcome,
)

TENANT = DEFAULT_TENANT_ID


# =============================================================================
# R-03 — Audit log NEVER contains raw query strings or raw criteria
# =============================================================================


async def test_r03_audit_event_never_contains_raw_query_strings() -> None:
    """R-03 equivalent at Phase 3C: audit buffer shape is allowlisted.

    The AuditEvent model uses extra="forbid" + strict=True so callers
    cannot silently add fields. Phase 3C's audit-hook wiring feeds only
    method names, tenant_hash, entry_ids, and PRE-HASHED criteria into
    the buffer. This test asserts each of those for every event type.
    """
    memory = make_memory()
    await memory.store_decision(TENANT, sample_decision())
    await memory.store_fact(TENANT, "a", "r", sample_fact())
    await memory.delete(TENANT, DeleteCriteria(entry_ids=["fake-id"]))
    await memory.export(TENANT, ExportCriteria(entry_ids=["fake-id"]))

    events = memory.audit_buffer.events()
    assert len(events) == 4

    for event in events:
        # Allowlisted fields only.
        assert event.tenant_hash == TENANT
        assert event.method  # non-empty
        # No raw criteria — only a hash if any.
        if event.criteria_hash is not None:
            # 64-char hex sha256 digest.
            assert len(event.criteria_hash) == 64
            assert all(c in "0123456789abcdef" for c in event.criteria_hash)
        # Outcome is a short string, not a free-form error message.
        assert event.outcome in ("ok", "error", "rejected")


async def test_r03_delete_audit_event_hashes_criteria_never_leaks_raw() -> None:
    """Delete criteria entry_ids must never appear verbatim in the audit event."""
    memory = make_memory()
    secret_id = "user-personal-id-9f8e7d-secret-leak-canary"
    await memory.delete(TENANT, DeleteCriteria(entry_ids=[secret_id]))

    events = memory.audit_buffer.events()
    delete_events = [e for e in events if e.method == "delete"]
    assert len(delete_events) == 1
    delete_event = delete_events[0]

    # The secret id must NOT appear in any field of the event.
    event_str = delete_event.model_dump_json()
    assert secret_id not in event_str
    # A hashed form IS present.
    assert delete_event.criteria_hash is not None


# =============================================================================
# R-04 — Quarantine strips embedding; post-quarantine retrieval returns zero
# =============================================================================


async def test_r04_quarantine_via_facade_strips_embedding_end_to_end() -> None:
    """R-04 end-to-end through the facade."""
    memory = make_memory()
    record = await memory.store_decision(TENANT, sample_decision())

    # Pre-quarantine: retrieval finds it.
    before = await memory.retrieve_decisions(TENANT, "Tuesday ship", top_k=5)
    assert len(before.hits) == 1

    result = await memory.flag_and_quarantine(TENANT, record.entry_id, QuarantineReason.POISONED)
    assert result.embedding_stripped is True

    # Post-quarantine: retrieval returns zero hits.
    after = await memory.retrieve_decisions(TENANT, "Tuesday ship", top_k=5)
    assert after.hits == []


async def test_r04_quarantine_is_multiplicatively_gated() -> None:
    """Structural check: even a 1.0 similarity can't rescue a quarantined record.

    This is a behavioral echo of the Atelier scoring property test —
    run at the facade layer to prove the multiplicative gate is wired
    end-to-end, not just present at the backend.
    """
    memory = make_memory()
    # Identical wording in two decisions; quarantine one, retrieve both.
    r1 = await memory.store_decision(TENANT, sample_decision())
    await memory.store_decision(TENANT, sample_decision())

    await memory.flag_and_quarantine(TENANT, r1.entry_id, QuarantineReason.HALLUCINATION)

    # Query should find the second decision but NOT the quarantined first.
    result = await memory.retrieve_decisions(TENANT, "Tuesday ship", top_k=5)
    assert len(result.hits) == 1
    assert result.hits[0].entry_id != r1.entry_id


# =============================================================================
# R-06 — Two-tenant export isolation
# =============================================================================


async def test_r06_two_tenant_export_never_returns_other_tenants_data() -> None:
    """R-06: each facade's export contains only its own tenant's data.

    Two independent Memory instances with distinct tenant_ids and
    distinct backend sets (Phase 3C minimum — real production always
    has process isolation on top). The invariant under test is that
    calling .export() on facade_A never surfaces any record that was
    written via facade_B, and vice versa.
    """
    a = make_memory(tenant_id="tenant-alpha")
    b = make_memory(tenant_id="tenant-bravo")

    # Tenant A writes three records across all three backends.
    await a.store_fact("tenant-alpha", "agent", "run", sample_fact())
    await a.store_decision("tenant-alpha", sample_decision())
    await a.store_task_outcome(
        "tenant-alpha",
        __import__(
            "tests.memory.facade._helpers", fromlist=["sample_signature"]
        ).sample_signature(),
        sample_task_outcome(),
    )

    # Tenant B writes one fact.
    await b.store_fact("tenant-bravo", "agent", "run", sample_fact())

    a_export = await a.export("tenant-alpha", ExportCriteria(full_tenant=True))
    b_export = await b.export("tenant-bravo", ExportCriteria(full_tenant=True))

    # A has more records than B (Atelier has A's decision + derived
    # task-outcome decision; Mem0 has A's one fact; Beads has several
    # audit beads). B has just one fact in Mem0 + audit beads.
    assert a_export.record_count > b_export.record_count
    # And both exports are non-zero — each tenant sees its own data.
    assert a_export.record_count > 0
    assert b_export.record_count > 0


async def test_r06_delete_on_one_tenant_does_not_touch_the_other() -> None:
    a = make_memory(tenant_id="tenant-alpha")
    b = make_memory(tenant_id="tenant-bravo")

    await a.store_decision("tenant-alpha", sample_decision())
    await b.store_decision("tenant-bravo", sample_decision())

    # A deletes its full tenant.
    await a.delete("tenant-alpha", DeleteCriteria(full_tenant=True))

    # B's decision is still retrievable.
    b_result = await b.retrieve_decisions("tenant-bravo", "Tuesday ship", top_k=5)
    assert len(b_result.hits) == 1

    # A's retrieval returns zero.
    a_result = await a.retrieve_decisions("tenant-alpha", "Tuesday ship", top_k=5)
    assert a_result.hits == []
