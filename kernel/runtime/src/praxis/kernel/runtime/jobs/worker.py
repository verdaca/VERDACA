"""JobsWorker — retention reaper + tick-drain worker.

Architecture §4.2.4: single worker per deployment, running as an asyncio
TaskGroup inside the Runtime process.

Two responsibilities:
  1. Claim and process jobs from jobs_queue (retention_shred / retention_cascade / etc.)
  2. Drain Memory.audit_buffer via tick-drain loop (Path B, OQ-N Path (i) shim)

NFR-Q6 (5-min crash RTO): startup runs _reclaim_orphans_on_startup() first,
restoring any claimed-but-unfinished jobs from the prior crashed worker.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from praxis.kernel.cost.storage.repository import CostRepository
from praxis.kernel.runtime.jobs.claim import claim_expires_at, new_claim_token
from praxis.kernel.runtime.outbox.drain_loop import drain_once

if TYPE_CHECKING:
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

_log = logging.getLogger(__name__)


class JobsWorker:
    """Single-process retention + tick-drain worker.

    Architecture §4.2.4.  Constructed at Orchestrator boot and injected with
    a CostRepository (shared engine with Pi-Mono tables) plus a DrainAdapter
    wrapping the Memory.audit_buffer.
    """

    def __init__(
        self,
        *,
        cost_repo: CostRepository,
        drain_adapter: "PositionBasedDrainAdapter",
        manifest_tenant_hash: str,
        tick_interval_seconds: float = 0.5,
        claim_duration_seconds: int = 300,
    ) -> None:
        self._cost_repo = cost_repo
        self._drain_adapter = drain_adapter
        self._manifest_tenant_hash = manifest_tenant_hash
        self._tick_interval_seconds = tick_interval_seconds
        self._claim_duration_seconds = claim_duration_seconds
        self._shutdown = asyncio.Event()

    async def run(self) -> None:
        """Start the worker.  Runs until shutdown() is called."""
        await self._reclaim_orphans_on_startup()
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._tick_drain_loop())
            tg.create_task(self._jobs_worker_loop())

    def shutdown(self) -> None:
        """Signal the worker to stop."""
        self._shutdown.set()

    # ------------------------------------------------------------------
    # NFR-Q6 orphan reclaim
    # ------------------------------------------------------------------

    async def _reclaim_orphans_on_startup(self) -> None:
        """Reclaim claimed-but-expired jobs from a prior crashed worker.

        Architecture §4.2.4: runs before any new work is claimed.  Ensures
        crashed-worker jobs are re-queued within the NFR-Q6 5-min budget.
        """
        async with self._cost_repo.session() as session:
            async with session.begin():
                result = await session.execute(
                    text("""
                    UPDATE jobs_queue
                    SET state = 'pending',
                        retry_count = retry_count + 1,
                        claim_token = NULL,
                        claim_expires_at = NULL,
                        last_error = COALESCE(last_error, '') || '; reclaimed on worker restart'
                    WHERE state = 'claimed'
                      AND claim_expires_at < CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
                    RETURNING id
                """)
                )
                reclaimed = result.rowcount  # type: ignore[attr-defined]  # SQLAlchemy async returns CursorResult
        if reclaimed:
            _log.info("NFR-Q6 reclaim: restored %d orphaned jobs on startup", reclaimed)

    # ------------------------------------------------------------------
    # Path B tick-drain loop
    # ------------------------------------------------------------------

    async def _tick_drain_loop(self) -> None:
        """Drain Memory.audit_buffer into events_outbox once per tick."""
        while not self._shutdown.is_set():
            await asyncio.sleep(self._tick_interval_seconds)
            try:
                drained = await drain_once(
                    cost_repo=self._cost_repo,
                    drain_adapter=self._drain_adapter,
                    manifest_tenant_hash=self._manifest_tenant_hash,
                )
                if drained:
                    _log.debug("tick drain: wrote %d events to outbox", drained)
            except Exception:
                _log.exception("tick drain failed; next tick will retry")

    # ------------------------------------------------------------------
    # Jobs worker loop (Path A)
    # ------------------------------------------------------------------

    async def _jobs_worker_loop(self) -> None:
        """Claim and process pending retention jobs."""
        while not self._shutdown.is_set():
            try:
                job = await self._claim_next_job()
                if job is None:
                    # No pending jobs — back off briefly
                    await asyncio.sleep(self._tick_interval_seconds * 2)
                    continue
                await self._process_job(job)
            except asyncio.CancelledError:
                raise
            except Exception:
                _log.exception("jobs worker loop error")

    async def _claim_next_job(self) -> dict[str, Any] | None:
        """Claim one pending job.  Returns job dict or None if queue empty."""
        now = datetime.now(timezone.utc)
        token = new_claim_token()
        expires = claim_expires_at(now)

        async with self._cost_repo.session() as session:
            async with session.begin():
                # SELECT + UPDATE with claim fencing
                result = await session.execute(
                    text("""
                    UPDATE jobs_queue
                    SET state = 'claimed',
                        claimed_at = :now,
                        claim_token = :token,
                        claim_expires_at = :expires
                    WHERE id = (
                        SELECT id FROM jobs_queue
                        WHERE state = 'pending'
                          AND (next_retry_at IS NULL OR next_retry_at <= :now)
                        ORDER BY next_retry_at NULLS FIRST, created_at
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    RETURNING id, job_type, tenant_hash, payload_json, retry_count, max_retries
                """),
                    {"now": now, "token": token, "expires": expires},
                )
                row = result.fetchone()

        if row is None:
            return None
        return {
            "id": row[0],
            "job_type": row[1],
            "tenant_hash": row[2],
            "payload_json": row[3],
            "retry_count": row[4],
            "max_retries": row[5],
            "claim_token": token,
        }

    async def _process_job(self, job: dict[str, Any]) -> None:
        """Dispatch job to the appropriate handler."""
        from praxis.kernel.runtime.outbox.path_a import complete_retention_job_path_a

        try:
            await complete_retention_job_path_a(
                cost_repo=self._cost_repo,
                job_id=job["id"],
                claim_token=job["claim_token"],
                tenant_hash=job["tenant_hash"],
                manifest_tenant_hash=self._manifest_tenant_hash,
            )
        except Exception as exc:
            _log.exception("job %s failed: %s", job["id"], exc)
            await self._mark_failed(job, str(exc))

    async def _mark_failed(self, job: dict[str, Any], error: str) -> None:
        """Increment retry_count and set next_retry_at or route to final state."""
        from praxis.kernel.runtime.jobs.retry import FailureReason, backoff, get_final_state

        new_count = job["retry_count"] + 1
        final_state = get_final_state(FailureReason.UNKNOWN, new_count, job["max_retries"])
        now = datetime.now(timezone.utc)
        next_retry = now + backoff(new_count) if final_state.value == "failed" else None

        async with self._cost_repo.session() as session:
            async with session.begin():
                await session.execute(
                    text("""
                    UPDATE jobs_queue
                    SET state = :state,
                        retry_count = :count,
                        last_error = :error,
                        next_retry_at = :next_retry,
                        failure_reason = :reason
                    WHERE id = :id
                """),
                    {
                        "state": final_state.value,
                        "count": new_count,
                        "error": error[:2048],
                        "next_retry": next_retry,
                        "reason": FailureReason.UNKNOWN.value,
                        "id": job["id"],
                    },
                )


__all__ = ["JobsWorker"]
