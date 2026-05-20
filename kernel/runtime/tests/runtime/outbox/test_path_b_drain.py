"""F-1.H3/H6/H7 + OQ-N.T1..T7 — Path B tick-drain integration tests.

Architecture §8.1.5: at-least-once drain of Memory.audit_buffer events
into Pi-Mono's events_outbox.  OQ-N Path (i) position-based shim.

Test-strategy §9.1.3 (F-1.H3), §9.1.6 (F-1.H6), §9.1.7 (F-1.H7),
§7.2 (OQ-N drain_adapter fixture).
"""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone

import pytest

from praxis.kernel.memory._internal.audit import AuditBuffer, AuditEvent, AuditEventType
from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter
from tests.conftest import requires_postgres

pytestmark = [pytest.mark.asyncio, pytest.mark.f1_absorption]

_NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


def _make_audit_event(
    tenant_hash: str = "test-tenant",
    event_type: AuditEventType = AuditEventType.STORE_FACT,
) -> AuditEvent:
    return AuditEvent(
        tenant_hash=tenant_hash,
        method="store_fact",
        event_type=event_type,
        created_at=_NOW(),
    )


# ---------------------------------------------------------------------------
# OQ-N.T2 — concurrent append during snapshot_undrained (thread safety)
# ---------------------------------------------------------------------------


@pytest.mark.oqn_escalation_canary
def test_oqn_t2_concurrent_append_during_snapshot() -> None:
    """OQ-N.T2 — concurrent _audit_append during snapshot_undrained.

    AuditBuffer's internal lock serializes append and events().
    The position-based shim only reads _drained_count after events() returns.
    A concurrent append landing AFTER events() does NOT cause loss — it will
    be picked up on the next tick.
    """
    buf = AuditBuffer()
    adapter = PositionBasedDrainAdapter(buf)
    errors: list[str] = []

    # Pre-append 10 events
    for _ in range(10):
        buf.append(_make_audit_event())

    def concurrent_appender() -> None:
        for _ in range(5):
            buf.append(_make_audit_event())

    # Start concurrent appender DURING snapshot
    t = threading.Thread(target=concurrent_appender)
    t.start()
    snapshot = adapter.snapshot_undrained()
    t.join()

    # The snapshot contains at least the 10 pre-loaded events
    assert len(snapshot) >= 10, f"OQ-N.T2: expected ≥10 events in snapshot, got {len(snapshot)}"

    # After the thread finishes, all 15 events are in the buffer
    # If we mark_drained(len(snapshot)) and snapshot again, we get only the remainder
    adapter.mark_drained(len(snapshot))
    remainder = adapter.snapshot_undrained()
    total = len(snapshot) + len(remainder)
    assert total == 15, (
        f"OQ-N.T2: expected 15 total events (10+5), got {total}. "
        f"Silent drop detected — escalate to OQ-N Path (ii)."
    )


# ---------------------------------------------------------------------------
# OQ-N.T3 — memory ceiling (simulated, no DB needed)
# ---------------------------------------------------------------------------


def test_oqn_t3_memory_ceiling_50mb() -> None:
    """OQ-N.T3 — buffer with 100K events stays under 60 MB.

    Architecture §12 OQ-N: 'AuditEvent ≈ 500 bytes × 100K entries ≈ 50 MB.
    Tolerable for single-tenant-per-deployment topology.'
    """
    import sys

    buf = AuditBuffer()
    adapter = PositionBasedDrainAdapter(buf)

    # Add 1000 events (not 100K for test speed — verify per-event size)
    sample_size = 1000
    for _ in range(sample_size):
        buf.append(_make_audit_event())

    snapshot = adapter.snapshot_undrained()
    assert len(snapshot) == sample_size

    # Per-event size estimate
    event_bytes = sys.getsizeof(snapshot[0]) if snapshot else 500
    estimated_100k_mb = (event_bytes * 100_000) / (1024 * 1024)

    assert estimated_100k_mb < 60, (
        f"OQ-N.T3 ESCALATION TRIGGER: estimated 100K-event footprint = "
        f"{estimated_100k_mb:.1f} MB exceeds 60 MB ceiling. "
        f"Escalate to OQ-N Path (ii) (drain_atomic). "
        f"Per-event size: {event_bytes} bytes."
    )


# ---------------------------------------------------------------------------
# OQ-N.T4 — async reentrance (asyncio task yielding between snapshot/mark)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_oqn_t4_async_reentrance_does_not_drop_events() -> None:
    """OQ-N.T4 — concurrent asyncio append between snapshot and mark_drained.

    _drain_once yields at await points.  A concurrent buf.append() scheduled
    on the same loop AFTER snapshot must not be lost or double-counted.
    """
    buf = AuditBuffer()
    adapter = PositionBasedDrainAdapter(buf)

    # Pre-load 5 events
    for _ in range(5):
        buf.append(_make_audit_event())

    # Simulate: take snapshot, then yield, then another event arrives
    snapshot = adapter.snapshot_undrained()
    assert len(snapshot) == 5

    # Yield to event loop (simulates await asyncio.sleep(0) inside _drain_once)
    await asyncio.sleep(0)

    # Append ONE more event (simulates concurrent agent appending)
    buf.append(_make_audit_event())

    # Mark the original 5 drained
    adapter.mark_drained(len(snapshot))

    # The new event must be in the next snapshot, NOT lost
    next_snapshot = adapter.snapshot_undrained()
    assert len(next_snapshot) == 1, (
        f"OQ-N.T4: expected 1 new event after yield, got {len(next_snapshot)}. "
        f"Events dropped under async reentrance."
    )


# ---------------------------------------------------------------------------
# OQ-N.T5 — compaction race regression guard
# ---------------------------------------------------------------------------


def test_oqn_t5_compaction_race_would_drop_events() -> None:
    """OQ-N.T5 — documents WHY compaction is rejected.

    If buffer.clear() is called after the emptiness check but before
    a concurrent append, the new event is silently lost.

    This test deliberately demonstrates the race that would occur if
    compaction were implemented.  Its existence guards against future
    contributors adding compaction.  The test PASSES by documenting the
    loss — a future compaction implementation would need to prove it
    avoids this scenario.
    """
    buf = AuditBuffer()
    adapter = PositionBasedDrainAdapter(buf)

    # All events drained
    for _ in range(3):
        buf.append(_make_audit_event())
    adapter.mark_drained(3)
    assert adapter.undrained_count() == 0

    # Simulate: "emptiness check passes, then a new event arrives, then clear()"
    # In production this would be a race; here we simulate it sequentially.
    buf.append(_make_audit_event())  # event_X arrives
    buf.clear()  # compaction fires — event_X lost!
    # DO NOT reset _drained_count — this simulates the race

    # Verify the loss: the high-water mark points past the cleared buffer
    remainder = adapter.snapshot_undrained()
    # After clear(), buffer has 0 events.  _drained_count is still 3.
    # snapshot_undrained() = events[3:] = [] — event_X is gone.
    assert len(remainder) == 0, (
        "OQ-N.T5: expected 0 events (event_X was lost by compaction). "
        "This documents WHY compaction is rejected under Path (i)."
    )
    # This test passing means the race IS real and compaction IS unsafe.


# ---------------------------------------------------------------------------
# F-1.H6 — Path B dedup on replay (no_mark_drained crash simulation)
# ---------------------------------------------------------------------------


@requires_postgres
@pytest.mark.critical
@pytest.mark.f1_absorption
async def test_f1_h6_path_b_dedup_on_crash_replay(cost_repo_pg) -> None:
    """F-1.H6 — commit succeeds but mark_drained is skipped (crash simulation).

    Next tick re-drains the same events.  Dedup via events_outbox.event_id
    (PK uniqueness) ensures no double-counting.
    """
    # Use unique tenant to isolate from cross-test Postgres contamination
    import uuid as _uuid

    from praxis.kernel.runtime.outbox.drain_loop import drain_once
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    unique_tenant = f"f1h6-test-{_uuid.uuid4().hex[:8]}"

    buf = AuditBuffer()
    adapter = PositionBasedDrainAdapter(buf)

    # Seed 5 events in buffer
    for _ in range(5):
        buf.append(_make_audit_event(tenant_hash=unique_tenant))

    # First drain — commit succeeds but we DON'T call mark_drained (simulates crash)
    await drain_once(
        cost_repo=cost_repo_pg,
        drain_adapter=adapter,
        manifest_tenant_hash=unique_tenant,
        mark_after_commit=False,  # simulate crash before mark_drained
    )

    # Second drain — replays same events (counter not advanced)
    await drain_once(
        cost_repo=cost_repo_pg,
        drain_adapter=adapter,
        manifest_tenant_hash=unique_tenant,
        mark_after_commit=True,  # normal operation
    )

    from sqlalchemy import text

    async with cost_repo_pg.session() as session:
        result = (
            await session.execute(
                text("SELECT COUNT(*) FROM events_outbox WHERE payload::text LIKE :pat"),
                {"pat": f"%{unique_tenant}%"},
            )
        ).scalar()

    assert result == 5, (
        f"F-1.H6 FAILED: expected 5 events (dedup), got {result}. "
        f"At-least-once dedup via event_id PK is broken."
    )
