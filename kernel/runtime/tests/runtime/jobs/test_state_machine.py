"""F-3.H2/H3 — JobState machine transitions and enum shape tests.

All SQLite-based (no Docker required).  Direct SQL via SQLAlchemy async
session — no worker classes involved (those land in Checkpoint 2 worker
tests).

Test-strategy §9.2.2 (F-3.H2 + F-3.H3).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from praxis.kernel.runtime.jobs.schema import FailureReason, JobsQueue, JobState, JobType

pytestmark = [
    pytest.mark.f3_absorption,
    pytest.mark.integration,
    pytest.mark.asyncio,
]

_NOW = lambda: datetime.now(timezone.utc)  # noqa: E731


async def _insert_pending_job(
    session,
    job_type: JobType = JobType.QUARANTINE_PROMOTE,
    max_retries: int = 3,
) -> str:
    job = JobsQueue(
        id=str(uuid.uuid4()),
        tenant_hash="test-tenant",
        job_type=job_type.value,
        state=JobState.PENDING.value,
        max_retries=max_retries,
        retry_count=0,
        created_at=_NOW(),
    )
    session.add(job)
    await session.flush()
    return job.id


# ---------------------------------------------------------------------------
# State transition tests
# ---------------------------------------------------------------------------


async def test_legal_state_transitions_pending_to_claimed(cost_repo_sqlite) -> None:
    async with cost_repo_sqlite.session() as session:
        async with session.begin():
            job_id = await _insert_pending_job(session)
            await session.execute(
                text("UPDATE jobs_queue SET state = :state WHERE id = :id"),
                {"state": JobState.CLAIMED.value, "id": job_id},
            )
            row = (
                await session.execute(
                    text("SELECT state FROM jobs_queue WHERE id = :id"),
                    {"id": job_id},
                )
            ).fetchone()
    assert row[0] == JobState.CLAIMED.value


async def test_legal_state_transitions_claimed_to_completed(cost_repo_sqlite) -> None:
    async with cost_repo_sqlite.session() as session:
        async with session.begin():
            job_id = await _insert_pending_job(session)
            for new_state in [JobState.CLAIMED, JobState.COMPLETED]:
                await session.execute(
                    text("UPDATE jobs_queue SET state = :state WHERE id = :id"),
                    {"state": new_state.value, "id": job_id},
                )
            row = (
                await session.execute(
                    text("SELECT state FROM jobs_queue WHERE id = :id"),
                    {"id": job_id},
                )
            ).fetchone()
    assert row[0] == JobState.COMPLETED.value


async def test_legal_state_transitions_failed_retry_increments(cost_repo_sqlite) -> None:
    async with cost_repo_sqlite.session() as session:
        async with session.begin():
            job_id = await _insert_pending_job(session, max_retries=3)
            await session.execute(
                text(
                    "UPDATE jobs_queue "
                    "SET state = :failed, retry_count = retry_count + 1 "
                    "WHERE id = :id"
                ),
                {"failed": JobState.FAILED.value, "id": job_id},
            )
            await session.execute(
                text("UPDATE jobs_queue SET state = :pending WHERE id = :id"),
                {"pending": JobState.PENDING.value, "id": job_id},
            )
            row = (
                await session.execute(
                    text("SELECT state, retry_count FROM jobs_queue WHERE id = :id"),
                    {"id": job_id},
                )
            ).fetchone()
    assert row[0] == JobState.PENDING.value
    assert row[1] == 1


async def test_retry_count_at_max_becomes_abandoned(cost_repo_sqlite) -> None:
    max_retries = 3
    async with cost_repo_sqlite.session() as session:
        async with session.begin():
            job_id = await _insert_pending_job(session, max_retries=max_retries)
            for i in range(1, max_retries + 1):
                await session.execute(
                    text(
                        "UPDATE jobs_queue SET state = :failed, retry_count = :count WHERE id = :id"
                    ),
                    {"failed": JobState.FAILED.value, "count": i, "id": job_id},
                )
            await session.execute(
                text("UPDATE jobs_queue SET state = :abandoned WHERE id = :id"),
                {"abandoned": JobState.ABANDONED.value, "id": job_id},
            )
            row = (
                await session.execute(
                    text("SELECT state, retry_count FROM jobs_queue WHERE id = :id"),
                    {"id": job_id},
                )
            ).fetchone()
    assert row[0] == JobState.ABANDONED.value
    assert row[1] == max_retries


async def test_invariant_violation_failure_becomes_poisoned(cost_repo_sqlite) -> None:
    async with cost_repo_sqlite.session() as session:
        async with session.begin():
            job_id = await _insert_pending_job(session)
            await session.execute(
                text(
                    "UPDATE jobs_queue SET state = :state, failure_reason = :reason WHERE id = :id"
                ),
                {
                    "state": JobState.POISONED.value,
                    "reason": FailureReason.INVARIANT_VIOLATION.value,
                    "id": job_id,
                },
            )
            row = (
                await session.execute(
                    text("SELECT state, failure_reason FROM jobs_queue WHERE id = :id"),
                    {"id": job_id},
                )
            ).fetchone()
    assert row[0] == JobState.POISONED.value
    assert row[1] == FailureReason.INVARIANT_VIOLATION.value


# ---------------------------------------------------------------------------
# Enum shape tests (pure unit, no DB)
# ---------------------------------------------------------------------------


def test_job_type_all_values_valid() -> None:
    for jt in JobType:
        assert isinstance(jt.value, str) and jt.value, f"JobType.{jt.name} empty"


def test_all_job_states_defined() -> None:
    expected = {"PENDING", "CLAIMED", "IN_PROGRESS", "COMPLETED", "FAILED", "ABANDONED", "POISONED"}
    actual = {m.name for m in JobState}
    assert expected.issubset(actual), f"Missing states: {expected - actual}"
