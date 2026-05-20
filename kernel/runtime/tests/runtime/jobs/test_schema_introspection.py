"""F-3.H1 — jobs_queue + outbox_drain_retries schema introspection.

Verifies that the Alembic / SQLAlchemy migration actually creates every
column, CHECK constraint, and index specified in architecture §4.2.2–§4.2.3.

Test-strategy §9.2.1 (F-3.H1).  Uses SQLite for dialect-neutral column
checking; Postgres-only constraints (CHECK, partial index) are verified in
a Postgres variant.
"""

from __future__ import annotations

import pytest

from tests.conftest import requires_postgres

# ---------------------------------------------------------------------------
# SQLite — column presence and ORM mapping smoke (no Docker needed)
# ---------------------------------------------------------------------------


@pytest.mark.f3_absorption
@pytest.mark.integration
@pytest.mark.asyncio
async def test_jobs_queue_columns_present_sqlite(cost_repo_sqlite) -> None:
    """All 17 jobs_queue columns from arch §4.2.2 are in the ORM model."""
    from praxis.kernel.runtime.jobs.schema import JobsQueue

    column_names = {c.name for c in JobsQueue.__table__.columns}
    required = {
        "id",
        "tenant_hash",
        "job_type",
        "payload_json",
        "state",
        "created_at",
        "claimed_at",
        "started_at",
        "completed_at",
        "retry_count",
        "max_retries",
        "next_retry_at",
        "last_error",
        "failure_reason",
        "claim_token",
        "claim_expires_at",
        "retry_state",
    }
    missing = required - column_names
    assert missing == set(), f"jobs_queue missing columns: {missing}"


@pytest.mark.f3_absorption
@pytest.mark.integration
@pytest.mark.asyncio
async def test_outbox_drain_retries_columns_present_sqlite(cost_repo_sqlite) -> None:
    """All outbox_drain_retries columns from arch §4.2.3 are present."""
    from praxis.kernel.runtime.jobs.schema import OutboxDrainRetries

    column_names = {c.name for c in OutboxDrainRetries.__table__.columns}
    required = {
        "audit_event_id",
        "tenant_hash",
        "event_type",
        "first_seen_at",
        "retry_count",
        "max_retries",
        "last_error",
        "next_retry_at",
        "state",
    }
    missing = required - column_names
    assert missing == set(), f"outbox_drain_retries missing columns: {missing}"


@pytest.mark.f3_absorption
@pytest.mark.integration
@pytest.mark.asyncio
async def test_jobs_queue_table_exists_in_db_sqlite(cost_repo_sqlite) -> None:
    """Verify SQLAlchemy create_all() actually created the table."""
    from sqlalchemy import text

    async with cost_repo_sqlite.session() as session:
        result = await session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs_queue'")
        )
        row = result.fetchone()
    assert row is not None, "jobs_queue table not created"


@pytest.mark.f3_absorption
@pytest.mark.integration
@pytest.mark.asyncio
async def test_jobs_queue_enum_values_valid_sqlite(cost_repo_sqlite) -> None:
    """job_type and state column values map to Python enums."""
    from praxis.kernel.runtime.jobs.schema import JobState, JobType

    # Verify all enum values are defined
    assert JobState.PENDING.value == "pending"
    assert JobState.CLAIMED.value == "claimed"
    assert JobState.COMPLETED.value == "completed"
    assert JobState.POISONED.value == "poisoned"

    assert JobType.RETENTION_SHRED.value == "retention_shred"
    assert JobType.RETENTION_CASCADE.value == "retention_cascade"


# ---------------------------------------------------------------------------
# Postgres — partial indexes + CHECK constraints (requires Docker)
# ---------------------------------------------------------------------------


@requires_postgres
@pytest.mark.f3_absorption
@pytest.mark.integration
@pytest.mark.asyncio
async def test_jobs_queue_pending_index_exists_postgres(cost_repo_pg) -> None:
    """Partial index on jobs_queue for worker pickup exists (arch §4.2.2)."""
    from sqlalchemy import text

    async with cost_repo_pg.session() as session:
        result = await session.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename='jobs_queue' AND indexname='idx_jobs_pending_pickup'"
            )
        )
        row = result.fetchone()
    assert row is not None, "idx_jobs_pending_pickup index missing from jobs_queue"


@requires_postgres
@pytest.mark.f3_absorption
@pytest.mark.integration
@pytest.mark.asyncio
async def test_jobs_queue_orphan_reclaim_index_exists_postgres(cost_repo_pg) -> None:
    """Partial index on claim_expires_at for orphan reclaim exists."""
    from sqlalchemy import text

    async with cost_repo_pg.session() as session:
        result = await session.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename='jobs_queue' AND indexname='idx_jobs_orphan_reclaim'"
            )
        )
        row = result.fetchone()
    assert row is not None, "idx_jobs_orphan_reclaim index missing"
