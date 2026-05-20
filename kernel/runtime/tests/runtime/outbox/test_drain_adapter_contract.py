"""
Tests for the OQ-N.T1 drain adapter contract.
No DB or async required — AuditBuffer and PositionBasedDrainAdapter are synchronous.
"""

from datetime import datetime, timezone

from praxis.kernel.memory._internal.audit import AuditBuffer, AuditEvent, AuditEventType
from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_event(method: str = "store_fact") -> AuditEvent:
    return AuditEvent(
        tenant_hash="test",
        method=method,
        event_type=AuditEventType.STORE_FACT,
        created_at=datetime.now(timezone.utc),
    )


def _make_adapter() -> PositionBasedDrainAdapter:
    buffer = AuditBuffer()
    return PositionBasedDrainAdapter(buffer)


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------


def test_snapshot_undrained_returns_appended_events():
    adapter = _make_adapter()
    for _ in range(5):
        adapter.buffer.append(_make_event())
    events = adapter.snapshot_undrained()
    assert len(events) == 5


def test_mark_drained_advances_high_water_mark():
    adapter = _make_adapter()
    for _ in range(5):
        adapter.buffer.append(_make_event())
    first_snapshot = adapter.snapshot_undrained()
    assert len(first_snapshot) == 5

    adapter.mark_drained(5)

    for _ in range(3):
        adapter.buffer.append(_make_event())
    second_snapshot = adapter.snapshot_undrained()
    assert len(second_snapshot) == 3, (
        f"Expected 3 new events after mark_drained(5), got {len(second_snapshot)}"
    )


def test_snapshot_before_any_mark_returns_all():
    adapter = _make_adapter()
    events = adapter.snapshot_undrained()
    assert events == []


def test_mark_drained_zero_is_noop():
    adapter = _make_adapter()
    for _ in range(3):
        adapter.buffer.append(_make_event())
    adapter.mark_drained(0)
    events = adapter.snapshot_undrained()
    assert len(events) == 3, (
        f"mark_drained(0) should be a no-op; expected 3 events, got {len(events)}"
    )


def test_position_counter_resets_not_supported_until_process_restart():
    """
    Known limitation: manually calling buffer.clear() without resetting the
    position counter causes snapshot_undrained() to return incorrect (empty)
    results for subsequent appends that fall within the old high-water mark.

    This test documents the limitation — it is expected to demonstrate the
    wrong behaviour rather than pass with correct semantics.
    """
    adapter = _make_adapter()
    for _ in range(5):
        adapter.buffer.append(_make_event())
    adapter.mark_drained(5)

    # Simulate an unsupported "reset" by clearing the buffer directly
    adapter.buffer.clear()

    # Append events whose positions are <= old high-water mark
    for _ in range(3):
        adapter.buffer.append(_make_event())

    snapshot = adapter.snapshot_undrained()
    # Document the known limitation: snapshot may return 0 instead of 3
    # because the high-water mark was not reset alongside the buffer.
    assert len(snapshot) == 0, (
        "Known limitation: position counter not reset with buffer.clear(); "
        "snapshot_undrained() returns empty until position counter exceeds old HWM."
    )
