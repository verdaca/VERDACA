"""drain_once — shared Path B tick-drain logic.

Used by both the production JobsWorker and the test harness.  Separating
the drain logic from the worker loop makes unit-testing without a running
worker straightforward.

Architecture §8.1.5 Path B.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert

from praxis.kernel.cost.storage.repository import CostRepository
from praxis.kernel.cost.storage.schema import EventRow
from praxis.kernel.memory._internal.audit import AuditEventType
from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter
from praxis.kernel.runtime.outbox.tenant_check import check_tenant

# M5 — OQ-N Path (i): AuditEventType is imported from memory._internal.audit because
# no public Memory API exposes event type filtering. This _internal coupling is
# architecturally authorized per architecture §16.3 + Checkpoint 2 ratification
# (2026-04-13). If Memory ever exposes AuditEventType publicly, migrate this import.

_log = logging.getLogger(__name__)

# Path B processes only these event types (not retention_action — that is Path A)
_PATH_B_EVENT_TYPES = frozenset(
    {
        AuditEventType.STORE_FACT,
        AuditEventType.STORE_TASK_OUTCOME,
        AuditEventType.STORE_DECISION,
    }
)


def _dedup_event_id_path_b(audit_event_id: str) -> str:
    """AuditEvent.id → 26-char deterministic event_id for events_outbox PK dedup."""
    return hashlib.sha256(f"audit:{audit_event_id}".encode()).hexdigest()[:26]


async def drain_once(
    *,
    cost_repo: CostRepository,
    drain_adapter: PositionBasedDrainAdapter,
    manifest_tenant_hash: str,
    mark_after_commit: bool = True,
) -> int:
    """Drain one tick's worth of Path B events from the AuditBuffer.

    Returns the number of events drained in this tick.

    Parameters
    ----------
    mark_after_commit:
        If False, skip mark_drained after commit (for crash simulation in tests).
        Production always passes True.
    """
    events = drain_adapter.snapshot_undrained()

    # Path B only drains STORE_FACT / STORE_TASK_OUTCOME / STORE_DECISION events.
    # QUARANTINE events are handled via Path A (retention_action).
    path_b_events = [e for e in events if e.event_type in _PATH_B_EVENT_TYPES]

    if not path_b_events:
        return 0

    now = datetime.now(timezone.utc)

    async with cost_repo.session() as session:
        async with session.begin():
            for event in path_b_events:
                check_tenant(event.tenant_hash, manifest_tenant_hash)
                dedup_id = _dedup_event_id_path_b(str(id(event)))

                stmt = (
                    pg_insert(EventRow)
                    .values(
                        event_id=dedup_id,
                        event_type=event.event_type.value,
                        record_id=None,
                        payload={
                            "tenant_hash": event.tenant_hash,
                            "method": event.method,
                            "outcome": event.outcome,
                        },
                        emitted_at=now,
                    )
                    .on_conflict_do_nothing(index_elements=["event_id"])
                )
                await session.execute(stmt)
        # commit happens here — both success and fail are handled by the context manager

    if mark_after_commit:
        drain_adapter.mark_drained(len(path_b_events))

    return len(path_b_events)


__all__ = ["drain_once"]
