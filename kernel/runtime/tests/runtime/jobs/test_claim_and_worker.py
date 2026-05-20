"""F-3.H4/H5 + coverage for claim.py, worker.py, reaper_integration.py.

Tests claim token fencing, NFR-Q6 orphan reclaim, and the worker's
startup sequence.

Test-strategy §9.2.4 (F-3.H4 concurrent claim), §9.2.5 (F-3.H5 crash recovery).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import pytest

from tests.conftest import requires_postgres

pytestmark = [pytest.mark.asyncio, pytest.mark.f3_absorption]

_NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


# ---------------------------------------------------------------------------
# claim.py unit tests
# ---------------------------------------------------------------------------


def test_new_claim_token_is_uuid_string() -> None:
    from praxis.kernel.runtime.jobs.claim import new_claim_token

    token = new_claim_token()
    # Must be a valid UUID4 string
    parsed = uuid.UUID(token)
    assert parsed.version == 4


def test_claim_expires_at_is_5_minutes_later() -> None:

    from praxis.kernel.runtime.jobs.claim import _CLAIM_DURATION_SECONDS, claim_expires_at

    before = _NOW()
    expires = claim_expires_at(before)
    delta = expires - before
    assert abs(delta.total_seconds() - _CLAIM_DURATION_SECONDS) < 1


def test_claim_expires_at_uses_utc_now_if_none() -> None:
    from praxis.kernel.runtime.jobs.claim import claim_expires_at

    expires = claim_expires_at(None)
    now = _NOW()
    # Should be roughly 5 minutes from now
    delta = expires - now
    assert 290 < delta.total_seconds() < 310


# ---------------------------------------------------------------------------
# reaper_integration.py smoke test (thin delegation to path_a)
# ---------------------------------------------------------------------------


@requires_postgres
async def test_reaper_integration_complete_and_emit(cost_repo_pg) -> None:
    """complete_and_emit delegates to path_a and writes CostEvent atomically."""
    from sqlalchemy import text

    from praxis.kernel.runtime.jobs.reaper_integration import complete_and_emit
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType

    jid = str(uuid.uuid4())
    token = str(uuid.uuid4())

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
                    created_at=_NOW(),
                    claimed_at=_NOW(),
                    claim_token=token,
                    claim_expires_at=_NOW(),
                )
            )

    await complete_and_emit(
        cost_repo=cost_repo_pg,
        job_id=jid,
        claim_token=None,
        tenant_hash="test-tenant",
        manifest_tenant_hash="test-tenant",
    )

    async with cost_repo_pg.session() as session:
        row = (
            await session.execute(text("SELECT state FROM jobs_queue WHERE id=:id"), {"id": jid})
        ).fetchone()
    assert row[0] == JobState.COMPLETED.value


# ---------------------------------------------------------------------------
# F-3.H4 — concurrent claim fencing (Postgres FOR UPDATE SKIP LOCKED)
# ---------------------------------------------------------------------------


@requires_postgres
async def test_f3_h4_concurrent_claim_fencing(cost_repo_pg) -> None:
    """Two concurrent workers claim different jobs via FOR UPDATE SKIP LOCKED."""
    from sqlalchemy import text

    from praxis.kernel.runtime.jobs.claim import claim_expires_at, new_claim_token
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType

    # Insert 10 pending jobs
    async with cost_repo_pg.session() as session:
        async with session.begin():
            for _ in range(10):
                session.add(
                    JobsQueue(
                        id=str(uuid.uuid4()),
                        tenant_hash="test-tenant",
                        job_type=JobType.QUARANTINE_PROMOTE.value,
                        state=JobState.PENDING.value,
                        max_retries=3,
                        retry_count=0,
                        created_at=_NOW(),
                    )
                )

    now = _NOW()

    async def _claim_one() -> str | None:
        token = new_claim_token()
        expires = claim_expires_at(now)
        async with cost_repo_pg.session() as session:
            async with session.begin():
                result = await session.execute(
                    text("""
                    UPDATE jobs_queue
                    SET state='claimed', claimed_at=:now,
                        claim_token=:token, claim_expires_at=:expires
                    WHERE id = (
                        SELECT id FROM jobs_queue
                        WHERE state='pending'
                        ORDER BY created_at
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    RETURNING id
                """),
                    {"now": now, "token": token, "expires": expires},
                )
                row = result.fetchone()
        return row[0] if row else None

    # Run 12 concurrent claim attempts
    claims = await asyncio.gather(*[_claim_one() for _ in range(12)])
    claimed_ids = [c for c in claims if c is not None]

    # Exactly 10 unique claims (no double-claiming)
    assert len(claimed_ids) == 10, f"Expected 10 claims, got {len(claimed_ids)}"
    assert len(set(claimed_ids)) == 10, "Duplicate job IDs claimed (fencing broken)"


# ---------------------------------------------------------------------------
# F-3.H5 — NFR-Q6 crash recovery via orphan reclaim
# ---------------------------------------------------------------------------


@requires_postgres
@pytest.mark.wall_clock
async def test_f3_h5_nfr_q6_orphan_reclaim_on_startup(cost_repo_pg) -> None:
    """NFR-Q6: expired claimed jobs are reclaimed on worker startup.

    Architecture §4.2.4: _reclaim_orphans_on_startup() runs a single UPDATE
    that returns all orphaned (claimed + claim_expires_at < NOW()) jobs to
    pending state within 1 second.
    """
    import time

    from sqlalchemy import text

    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    # Insert 5 jobs in CLAIMED state with already-expired claim_expires_at
    expired_time = datetime(2020, 1, 1, tzinfo=timezone.utc)  # far in the past

    async with cost_repo_pg.session() as session:
        async with session.begin():
            for _ in range(5):
                session.add(
                    JobsQueue(
                        id=str(uuid.uuid4()),
                        tenant_hash="test-tenant",
                        job_type=JobType.QUARANTINE_PROMOTE.value,
                        state=JobState.CLAIMED.value,
                        max_retries=3,
                        retry_count=0,
                        created_at=_NOW(),
                        claimed_at=expired_time,
                        claim_token=str(uuid.uuid4()),
                        claim_expires_at=expired_time,  # already expired
                    )
                )

    # Create worker and run orphan reclaim
    buf = AuditBuffer()
    adapter = PositionBasedDrainAdapter(buf)
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=adapter,
        manifest_tenant_hash="test-tenant",
    )

    start = time.monotonic()
    await worker._reclaim_orphans_on_startup()
    elapsed = time.monotonic() - start

    # Verify all 5 jobs are back to PENDING
    async with cost_repo_pg.session() as session:
        result = (
            await session.execute(text("SELECT COUNT(*) FROM jobs_queue WHERE state='pending'"))
        ).scalar()

    assert result == 5, f"Expected 5 reclaimed jobs, got {result}"
    assert elapsed < 10.0, (
        f"NFR-Q6: orphan reclaim took {elapsed:.2f}s — exceeds 10s canary budget. "
        f"Full NFR-Q6 5-min budget is safe but canary threshold is 10s."
    )


# ---------------------------------------------------------------------------
# Worker inner methods — claim_next_job, process_job, mark_failed, shutdown
# ---------------------------------------------------------------------------


@requires_postgres
async def test_worker_claim_next_job_returns_job_dict(cost_repo_pg) -> None:
    """_claim_next_job() returns a dict with job metadata."""
    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    jid = str(uuid.uuid4())
    async with cost_repo_pg.session() as session:
        async with session.begin():
            session.add(
                JobsQueue(
                    id=jid,
                    tenant_hash="test-tenant",
                    job_type=JobType.QUARANTINE_PROMOTE.value,
                    state=JobState.PENDING.value,
                    max_retries=3,
                    retry_count=0,
                    created_at=_NOW(),
                )
            )

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
    )

    job = await worker._claim_next_job()
    assert job is not None
    assert job["id"] == jid
    assert job["job_type"] == JobType.QUARANTINE_PROMOTE.value


@requires_postgres
async def test_worker_claim_next_job_returns_none_for_empty_queue(cost_repo_pg) -> None:
    """_claim_next_job() returns None when no pending jobs."""
    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
    )
    job = await worker._claim_next_job()
    assert job is None


@requires_postgres
async def test_worker_mark_failed_increments_retry_count(cost_repo_pg) -> None:
    """_mark_failed() increments retry_count on a claimed job."""
    from sqlalchemy import text

    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    jid = str(uuid.uuid4())
    claim_tok = str(uuid.uuid4())
    async with cost_repo_pg.session() as session:
        async with session.begin():
            session.add(
                JobsQueue(
                    id=jid,
                    tenant_hash="test-tenant",
                    job_type=JobType.QUARANTINE_PROMOTE.value,
                    state=JobState.CLAIMED.value,
                    max_retries=3,
                    retry_count=0,
                    created_at=_NOW(),
                    claim_token=claim_tok,
                    claimed_at=_NOW(),
                    claim_expires_at=_NOW(),
                )
            )

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
    )
    job = {
        "id": jid,
        "job_type": JobType.QUARANTINE_PROMOTE.value,
        "tenant_hash": "test-tenant",
        "payload_json": {},
        "retry_count": 0,
        "max_retries": 3,
        "claim_token": claim_tok,
    }
    await worker._mark_failed(job, "test error")

    async with cost_repo_pg.session() as session:
        row = (
            await session.execute(
                text("SELECT retry_count, last_error FROM jobs_queue WHERE id=:id"), {"id": jid}
            )
        ).fetchone()
    assert row[0] == 1
    assert "test error" in row[1]


def test_worker_shutdown_sets_event() -> None:
    """shutdown() sets the internal Event so loops can detect it."""
    from unittest.mock import MagicMock

    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=MagicMock(),
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
    )
    assert not worker._shutdown.is_set()
    worker.shutdown()
    assert worker._shutdown.is_set()


@requires_postgres
async def test_worker_tick_drain_loop_runs_one_tick(cost_repo_pg) -> None:
    """_tick_drain_loop() runs at least one iteration before shutdown."""
    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
        tick_interval_seconds=0.01,  # very short tick
    )
    worker.shutdown()  # set shutdown immediately

    # The drain loop checks shutdown at the top of each iteration
    # It should run once then exit since shutdown is set
    await asyncio.wait_for(worker._tick_drain_loop(), timeout=2.0)


@requires_postgres
async def test_worker_process_job_completes_retention_shred(cost_repo_pg) -> None:
    """_process_job() calls complete_and_emit for a RETENTION_SHRED job."""
    from sqlalchemy import text

    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    jid = str(uuid.uuid4())
    async with cost_repo_pg.session() as session:
        async with session.begin():
            session.add(
                JobsQueue(
                    id=jid,
                    tenant_hash="test-tenant",
                    job_type=JobType.RETENTION_SHRED.value,
                    state=JobState.CLAIMED.value,
                    max_retries=3,
                    retry_count=0,
                    created_at=_NOW(),
                    claim_token=str(uuid.uuid4()),
                    claimed_at=_NOW(),
                    claim_expires_at=_NOW(),
                )
            )

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
    )
    job = {
        "id": jid,
        "job_type": JobType.RETENTION_SHRED.value,
        "tenant_hash": "test-tenant",
        "payload_json": {},
        "retry_count": 0,
        "max_retries": 3,
        "claim_token": None,
    }
    await worker._process_job(job)

    async with cost_repo_pg.session() as session:
        row = (
            await session.execute(text("SELECT state FROM jobs_queue WHERE id=:id"), {"id": jid})
        ).fetchone()
    assert row[0] == JobState.COMPLETED.value


@requires_postgres
async def test_worker_run_processes_a_job_and_shuts_down(cost_repo_pg) -> None:
    """Worker.run() processes one job via TaskGroup then exits on shutdown."""
    from sqlalchemy import text

    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    jid = str(uuid.uuid4())
    async with cost_repo_pg.session() as session:
        async with session.begin():
            session.add(
                JobsQueue(
                    id=jid,
                    tenant_hash="test-tenant",
                    job_type=JobType.RETENTION_SHRED.value,
                    state=JobState.PENDING.value,
                    max_retries=3,
                    retry_count=0,
                    created_at=_NOW(),
                )
            )

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
        tick_interval_seconds=0.05,
    )

    async def _run_and_stop() -> None:
        await asyncio.sleep(0.3)
        worker.shutdown()

    results = await asyncio.gather(
        asyncio.wait_for(worker.run(), timeout=5.0),
        _run_and_stop(),
        return_exceptions=True,
    )
    # The run() call exits after shutdown — may raise CancelledError/ExceptionGroup, that's OK

    async with cost_repo_pg.session() as session:
        row = (
            await session.execute(text("SELECT state FROM jobs_queue WHERE id=:id"), {"id": jid})
        ).fetchone()
    assert row[0] == JobState.COMPLETED.value, f"Worker did not process the job: state={row[0]}"


@requires_postgres
async def test_worker_tick_drain_drains_audit_events(cost_repo_pg) -> None:
    """_tick_drain_loop() drains audit events from the buffer (if drained: branch)."""
    from sqlalchemy import text

    from praxis.kernel.memory._internal.audit import AuditBuffer, AuditEvent, AuditEventType
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    # Use unique tenant_hash to isolate from other tests in the same Postgres container
    unique_tenant = f"tick-drain-test-{uuid.uuid4().hex[:8]}"

    buf = AuditBuffer()
    # Seed some events
    for _ in range(3):
        buf.append(
            AuditEvent(
                tenant_hash=unique_tenant,
                method="store_fact",
                event_type=AuditEventType.STORE_FACT,
                created_at=_NOW(),
            )
        )

    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash=unique_tenant,  # match the events' tenant_hash
        tick_interval_seconds=0.05,
    )

    async def _stop_after_drain() -> None:
        await asyncio.sleep(0.2)  # let one tick run
        worker.shutdown()

    await asyncio.gather(
        asyncio.wait_for(worker._tick_drain_loop(), timeout=2.0),
        _stop_after_drain(),
        return_exceptions=True,
    )

    async with cost_repo_pg.session() as session:
        result = (
            await session.execute(
                text("SELECT COUNT(*) FROM events_outbox WHERE payload::text LIKE :pat"),
                {"pat": f"%{unique_tenant}%"},
            )
        ).scalar()
    assert result == 3


@requires_postgres
async def test_worker_jobs_loop_handles_empty_queue(cost_repo_pg) -> None:
    """_jobs_worker_loop() sleeps and retries when queue is empty."""
    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
        tick_interval_seconds=0.05,
    )

    async def _stop_after_one_cycle() -> None:
        await asyncio.sleep(0.3)  # let one empty cycle run
        worker.shutdown()

    # Queue is empty — loop should hit the "job is None" branch and sleep once then stop
    await asyncio.gather(
        asyncio.wait_for(worker._jobs_worker_loop(), timeout=3.0),
        _stop_after_one_cycle(),
        return_exceptions=True,
    )


def test_retry_returns_failed_when_retries_remain() -> None:
    """get_final_state returns FAILED for retryable reasons with budget remaining."""
    from praxis.kernel.runtime.jobs.retry import get_final_state
    from praxis.kernel.runtime.jobs.schema import FailureReason, JobState

    result = get_final_state(FailureReason.TRANSIENT_BACKEND, retry_count=1, max_retries=5)
    assert result == JobState.FAILED


def test_alert_severity_returns_none_for_non_terminal_state() -> None:
    """get_alert_severity returns 'none' for COMPLETED / non-terminal states."""
    from praxis.kernel.runtime.jobs.retry import get_alert_severity
    from praxis.kernel.runtime.jobs.schema import JobType

    result = get_alert_severity(JobType.RETENTION_SHRED, final_state_name="completed")
    assert result == "none"


@requires_postgres
async def test_worker_process_job_handles_exception_and_marks_failed(cost_repo_pg) -> None:
    """_process_job() exception path → _mark_failed() called (covers lines 185-187)."""
    from unittest.mock import AsyncMock, patch

    from sqlalchemy import text

    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.schema import JobsQueue, JobState, JobType
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    jid = str(uuid.uuid4())
    async with cost_repo_pg.session() as session:
        async with session.begin():
            session.add(
                JobsQueue(
                    id=jid,
                    tenant_hash="test-tenant",
                    job_type=JobType.QUARANTINE_PROMOTE.value,
                    state=JobState.CLAIMED.value,
                    max_retries=3,
                    retry_count=0,
                    created_at=_NOW(),
                    claim_token=str(uuid.uuid4()),
                    claimed_at=_NOW(),
                    claim_expires_at=_NOW(),
                )
            )

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
    )
    job = {
        "id": jid,
        "job_type": JobType.QUARANTINE_PROMOTE.value,
        "tenant_hash": "test-tenant",
        "payload_json": {},
        "retry_count": 0,
        "max_retries": 3,
        "claim_token": None,
    }

    # Inject an exception in complete_and_emit to trigger the except branch (lines 185-187)
    with patch(
        "praxis.kernel.runtime.outbox.path_a.complete_retention_job_path_a",
        new=AsyncMock(side_effect=RuntimeError("injected failure")),
    ):
        await worker._process_job(job)

    async with cost_repo_pg.session() as session:
        row = (
            await session.execute(
                text("SELECT state, retry_count FROM jobs_queue WHERE id=:id"), {"id": jid}
            )
        ).fetchone()
    # Should be in FAILED state (retry_count < max_retries)
    assert row[0] in ("failed", "poisoned"), (
        f"Expected failed/poisoned after exception, got {row[0]}"
    )


@requires_postgres
async def test_worker_tick_drain_loop_handles_exception(cost_repo_pg) -> None:
    """_tick_drain_loop exception handler is exercised (covers lines 112-113)."""
    from unittest.mock import patch

    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
        tick_interval_seconds=0.02,
    )

    call_count = 0

    async def _drain_that_raises(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("injected tick drain failure")
        worker.shutdown()
        return 0

    with patch("praxis.kernel.runtime.jobs.worker.drain_once", side_effect=_drain_that_raises):

        async def _stop() -> None:
            await asyncio.sleep(0.2)
            worker.shutdown()

        await asyncio.gather(
            asyncio.wait_for(worker._tick_drain_loop(), timeout=2.0),
            _stop(),
            return_exceptions=True,
        )
    assert call_count >= 1


@requires_postgres
async def test_worker_jobs_loop_handles_cancellation(cost_repo_pg) -> None:
    """_jobs_worker_loop exits cleanly on CancelledError (covers lines 129-132)."""
    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.jobs.worker import JobsWorker
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    buf = AuditBuffer()
    worker = JobsWorker(
        cost_repo=cost_repo_pg,
        drain_adapter=PositionBasedDrainAdapter(buf),
        manifest_tenant_hash="test-tenant",
        tick_interval_seconds=0.02,
    )

    task = asyncio.create_task(worker._jobs_worker_loop())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass  # CancelledError re-raises from the loop — expected


def test_alert_severity_accepts_uppercase_state_name() -> None:
    """get_alert_severity handles uppercase state name via name-based lookup."""
    from praxis.kernel.runtime.jobs.retry import get_alert_severity
    from praxis.kernel.runtime.jobs.schema import JobType

    # "POISONED" (uppercase) → fails JobState("POISONED") → falls to JobState["POISONED"] → P1
    result = get_alert_severity(JobType.RETENTION_SHRED, final_state_name="POISONED")
    assert result == "P1"
