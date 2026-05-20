"""F-1.H2/H4/H5 + F-13.C1 (no_waiver) — Path A same-transaction atomicity.

Architecture §8.1.4: the UPDATE jobs_queue SET state='completed' and the
INSERT INTO events_outbox happen in the SAME Postgres transaction.

F-13.C1 is the load-bearing no_waiver proof: both rows must have the same
xmin (committed in the same transaction).  If this test fails or is
removed, NFR-C-A1 collapses.

Test-strategy §6.2.A (F-1.H2) + §6.2.C (F-13.C1) + §9.1.3 (F-1.H4/H5).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from tests.conftest import requires_postgres

pytestmark = [pytest.mark.asyncio, pytest.mark.f1_absorption, pytest.mark.integration]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _job_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# F-1.H2 — Path A end-to-end: job completion → CostEvent in same session
# ---------------------------------------------------------------------------


@requires_postgres
@pytest.mark.critical
async def test_path_a_completion_writes_event_row_in_postgres(cost_repo_pg) -> None:
    """Completing a retention job writes an EventRow in the same session."""
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType
    from praxis.kernel.runtime.outbox.path_a import complete_retention_job_path_a

    jid = _job_id()
    from praxis.kernel.runtime.outbox.path_a import _dedup_event_id

    dedup_key = _dedup_event_id(jid)

    # Pre-populate a claimed job
    async with cost_repo_pg.session() as session:
        async with session.begin():
            session.add(
                JobsQueue(
                    id=jid,
                    tenant_hash="test-tenant",
                    job_type=JobType.RETENTION_SHRED.value,
                    state=JobState.CLAIMED.value,
                    max_retries=10,
                    retry_count=0,
                    created_at=_utc_now(),
                    claimed_at=_utc_now(),
                    claim_token=str(uuid.uuid4()),
                    claim_expires_at=_utc_now(),
                )
            )

    # Execute Path A
    await complete_retention_job_path_a(
        cost_repo=cost_repo_pg,
        job_id=jid,
        claim_token=None,  # skip claim_token check in test
        tenant_hash="test-tenant",
        manifest_tenant_hash="test-tenant",
    )

    # Verify both rows exist
    async with cost_repo_pg.session() as session:
        job_row = (
            await session.execute(text("SELECT state FROM jobs_queue WHERE id = :id"), {"id": jid})
        ).fetchone()
        event_row = (
            await session.execute(
                text("SELECT event_id FROM events_outbox WHERE event_id = :eid"),
                {"eid": dedup_key},
            )
        ).fetchone()

    assert job_row[0] == JobState.COMPLETED.value, "jobs_queue.state != completed"
    assert event_row is not None, "events_outbox row not found after Path A commit"


# ---------------------------------------------------------------------------
# F-13.C1 (no_waiver) — physical txid_current() / xmin identity proof
# ---------------------------------------------------------------------------


@requires_postgres
@pytest.mark.critical
@pytest.mark.no_waiver
@pytest.mark.f1_absorption
async def test_f13_c1_path_a_shared_transaction_via_xmin(cost_repo_pg) -> None:
    """F-13.C1 (no_waiver): jobs_queue and events_outbox rows share the same xmin.

    This is the PHYSICAL proof that both writes committed in the same
    Postgres transaction.  Two rows with the same xmin were created by the
    same transaction ID.  If this assertion ever fails, NFR-C-A1's
    audit-trail guarantee collapses from structural to orchestration-only.

    This test CANNOT be quarantined, skipped, or waived.  Presence is
    enforced by the no_waiver meta-check.
    """
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType
    from praxis.kernel.runtime.outbox.path_a import complete_retention_job_path_a

    jid = _job_id()
    from praxis.kernel.runtime.outbox.path_a import _dedup_event_id

    dedup_key = _dedup_event_id(jid)

    async with cost_repo_pg.session() as session:
        async with session.begin():
            session.add(
                JobsQueue(
                    id=jid,
                    tenant_hash="test-tenant",
                    job_type=JobType.RETENTION_SHRED.value,
                    state=JobState.CLAIMED.value,
                    max_retries=10,
                    retry_count=0,
                    created_at=_utc_now(),
                    claimed_at=_utc_now(),
                    claim_token=str(uuid.uuid4()),
                    claim_expires_at=_utc_now(),
                )
            )

    await complete_retention_job_path_a(
        cost_repo=cost_repo_pg,
        job_id=jid,
        claim_token=None,
        tenant_hash="test-tenant",
        manifest_tenant_hash="test-tenant",
    )

    # The xmin comparison is the structural proof
    async with cost_repo_pg.session() as session:
        result = (
            await session.execute(
                text("""
            SELECT
                j.xmin AS job_xmin,
                e.xmin AS event_xmin,
                j.xmin = e.xmin AS same_transaction
            FROM jobs_queue j
            JOIN events_outbox e ON e.event_id = :dedup
            WHERE j.id = :jid
        """),
                {"dedup": dedup_key, "jid": jid},
            )
        ).fetchone()

    assert result is not None, "join returned no rows — rows not found"
    assert result[2] is True, (
        f"F-13.C1 FAILED: jobs_queue.xmin={result[0]}, events_outbox.xmin={result[1]}. "
        f"They are NOT the same transaction.  NFR-C-A1 structural guarantee violated. "
        f"Both writes MUST commit in one transaction per architecture §8.1.4."
    )


# ---------------------------------------------------------------------------
# F-1.H4 — Fault injection: commit failure rolls back BOTH rows
# ---------------------------------------------------------------------------


@requires_postgres
@pytest.mark.critical
@pytest.mark.f1_absorption
async def test_path_a_rollback_leaves_consistent_state(cost_repo_pg) -> None:
    """On commit failure, neither jobs_queue nor events_outbox has the row."""
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType

    jid = _job_id()

    async with cost_repo_pg.session() as session:
        async with session.begin():
            session.add(
                JobsQueue(
                    id=jid,
                    tenant_hash="test-tenant",
                    job_type=JobType.RETENTION_SHRED.value,
                    state=JobState.CLAIMED.value,
                    max_retries=10,
                    retry_count=0,
                    created_at=_utc_now(),
                )
            )

    from praxis.kernel.runtime.outbox.path_a import _dedup_event_id

    dedup = _dedup_event_id(jid)

    # Simulate a failed Path A: rollback mid-transaction
    try:
        async with cost_repo_pg.session() as session:
            async with session.begin():
                await session.execute(
                    text("UPDATE jobs_queue SET state='completed' WHERE id=:id"),
                    {"id": jid},
                )
                await session.execute(
                    text(
                        "INSERT INTO events_outbox(event_id, event_type, record_id, payload, emitted_at)"
                        " VALUES(:eid, 'memory.retention_action', NULL, '{}'::json, NOW())"
                    ),
                    {"eid": dedup},
                )
                raise RuntimeError("simulated commit failure")
    except RuntimeError:
        pass

    # Verify neither write persisted
    async with cost_repo_pg.session() as session:
        job_row = (
            await session.execute(text("SELECT state FROM jobs_queue WHERE id=:id"), {"id": jid})
        ).fetchone()
        event_row = (
            await session.execute(
                text("SELECT event_id FROM events_outbox WHERE event_id=:eid"),
                {"eid": dedup},
            )
        ).fetchone()

    assert job_row[0] == JobState.CLAIMED.value, "job state should still be CLAIMED after rollback"
    assert event_row is None, "events_outbox should NOT have the row after rollback"
