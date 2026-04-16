"""Path A — reaper-direct same-transaction CostEvent emission.

Architecture §8.1.4: the UPDATE jobs_queue SET state='completed' and the
INSERT INTO events_outbox BOTH happen in the SAME Postgres transaction via
a single CostRepository.session().  This is the structural guarantee that
backs NFR-C-A1 (7-day crypto-shred audit SLA).

F-13.C1 (no_waiver) verifies this at implementation time.  The xmin values
of both rows must be identical after commit.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from praxis.kernel.cost.storage.repository import CostRepository
from praxis.kernel.cost.storage.schema import EventRow
from praxis.kernel.runtime.jobs.schema import JobState
from praxis.kernel.runtime.outbox.tenant_check import check_tenant

_RETENTION_EVENT_TYPE = "memory.retention_action"


def _dedup_event_id(job_id: str) -> str:
    """Deterministic 26-char event_id for a retention job's CostEvent.

    SHA-256 prefix guarantees the same job always produces the same
    event_id (collision probability negligible for per-deployment use).
    26 chars matches Pi-Mono's EventRow.event_id String(26) column.
    """
    return hashlib.sha256(f"retention:{job_id}".encode()).hexdigest()[:26]


async def complete_retention_job_path_a(
    *,
    cost_repo: CostRepository,
    job_id: str,
    claim_token: str | None,
    tenant_hash: str,
    manifest_tenant_hash: str,
) -> None:
    """Mark a retention job completed AND insert its CostEvent in ONE transaction.

    This is the Path A emission point.  Architecture §8.1.4:
    'One transaction = atomicity = audit trail mathematically sound.'

    F-13.C1 proof: both the UPDATE and the INSERT share the same Postgres
    xmin because they commit together.
    """
    check_tenant(tenant_hash, manifest_tenant_hash)

    dedup_event_id = _dedup_event_id(job_id)
    now = datetime.now(timezone.utc)

    async with cost_repo.session() as session:
        async with session.begin():
            # UPDATE jobs_queue state → completed
            update_params: dict[str, Any] = {
                "state": JobState.COMPLETED.value,
                "completed_at": now,
                "id": job_id,
            }
            if claim_token is not None:
                await session.execute(
                    text(
                        "UPDATE jobs_queue "
                        "SET state = :state, completed_at = :completed_at "
                        "WHERE id = :id AND claim_token = :token"
                    ),
                    {**update_params, "token": claim_token},
                )
            else:
                await session.execute(
                    text(
                        "UPDATE jobs_queue "
                        "SET state = :state, completed_at = :completed_at "
                        "WHERE id = :id"
                    ),
                    update_params,
                )

            # INSERT CostEvent into events_outbox IN THE SAME TRANSACTION
            # Using Pi-Mono's EventRow (event_id PK = natural dedup)
            stmt = (
                pg_insert(EventRow)
                .values(
                    event_id=dedup_event_id,
                    event_type=_RETENTION_EVENT_TYPE,
                    record_id=None,
                    payload={
                        "tenant_hash": tenant_hash,
                        "job_id": job_id,
                        "category": "retention_action",
                    },
                    emitted_at=now,
                )
                .on_conflict_do_nothing(index_elements=["event_id"])
            )
            await session.execute(stmt)
        # commit is implicit — both writes land atomically or neither does


__all__ = ["complete_retention_job_path_a", "_dedup_event_id"]
