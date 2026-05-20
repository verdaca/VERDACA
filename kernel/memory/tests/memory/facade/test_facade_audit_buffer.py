"""Audit buffer coverage — shape, content, and lifecycle."""

from __future__ import annotations

from praxis.kernel.memory import (
    DeleteCriteria,
    ExportCriteria,
    QuarantineReason,
)
from praxis.kernel.memory._internal.audit import AuditEventType
from tests.memory.facade._helpers import (
    DEFAULT_TENANT_ID,
    make_memory,
    sample_decision,
    sample_fact,
    sample_signature,
    sample_task_outcome,
)

TENANT = DEFAULT_TENANT_ID


async def test_audit_buffer_starts_empty() -> None:
    memory = make_memory()
    assert len(memory.audit_buffer) == 0
    assert memory.audit_buffer.events() == []


async def test_store_task_outcome_appends_event() -> None:
    memory = make_memory()
    await memory.store_task_outcome(TENANT, sample_signature(), sample_task_outcome())
    events = memory.audit_buffer.events()
    assert len(events) == 1
    assert events[0].event_type == AuditEventType.STORE_TASK_OUTCOME
    assert events[0].method == "store_task_outcome"
    assert events[0].tenant_hash == TENANT


async def test_store_decision_appends_event() -> None:
    memory = make_memory()
    await memory.store_decision(TENANT, sample_decision())
    events = memory.audit_buffer.events()
    assert len(events) == 1
    assert events[0].event_type == AuditEventType.STORE_DECISION


async def test_store_fact_appends_event() -> None:
    memory = make_memory()
    await memory.store_fact(TENANT, "a", "r", sample_fact())
    events = memory.audit_buffer.events()
    assert len(events) == 1
    assert events[0].event_type == AuditEventType.STORE_FACT


async def test_delete_appends_event_with_criteria_hash() -> None:
    memory = make_memory()
    await memory.delete(TENANT, DeleteCriteria(entry_ids=["e1", "e2"]))
    events = memory.audit_buffer.events()
    assert len(events) == 1
    event = events[0]
    assert event.event_type == AuditEventType.DELETE
    assert event.criteria_hash is not None
    # 64-char sha256 hex
    assert len(event.criteria_hash) == 64


async def test_export_appends_event_with_criteria_hash() -> None:
    memory = make_memory()
    await memory.export(TENANT, ExportCriteria(full_tenant=True))
    events = memory.audit_buffer.events()
    assert len(events) == 1
    event = events[0]
    assert event.event_type == AuditEventType.EXPORT
    assert event.criteria_hash is not None


async def test_quarantine_appends_event_with_entry_id() -> None:
    memory = make_memory()
    record = await memory.store_decision(TENANT, sample_decision())
    # Clear to isolate the quarantine event
    memory.audit_buffer.clear()

    await memory.flag_and_quarantine(TENANT, record.entry_id, QuarantineReason.POISONED)
    events = memory.audit_buffer.events()
    assert len(events) == 1
    event = events[0]
    assert event.event_type == AuditEventType.QUARANTINE
    assert event.entry_id == record.entry_id


async def test_multiple_operations_accumulate_events_in_order() -> None:
    memory = make_memory()
    await memory.store_decision(TENANT, sample_decision())
    await memory.store_fact(TENANT, "a", "r", sample_fact())
    await memory.delete(TENANT, DeleteCriteria(entry_ids=["x"]))

    events = memory.audit_buffer.events()
    assert len(events) == 3
    assert [e.method for e in events] == [
        "store_decision",
        "store_fact",
        "delete",
    ]


async def test_buffer_snapshot_is_a_copy_not_a_reference() -> None:
    """events() returns a defensive copy — mutating it must not affect state."""
    memory = make_memory()
    await memory.store_decision(TENANT, sample_decision())
    snapshot = memory.audit_buffer.events()
    snapshot.clear()
    # Internal state is unaffected.
    assert len(memory.audit_buffer) == 1


async def test_audit_buffer_clear_resets_state() -> None:
    memory = make_memory()
    await memory.store_decision(TENANT, sample_decision())
    assert len(memory.audit_buffer) == 1
    memory.audit_buffer.clear()
    assert len(memory.audit_buffer) == 0
