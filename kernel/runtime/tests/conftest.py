"""Shared database fixtures for Checkpoint 2 integration tests.

Provides:
  - sqlite_db_url : sqlite+aiosqlite:/// URL for schema-only / unit tests
  - postgres_url  : PostgreSQL URL via testcontainers (session-scoped)
  - cost_repo     : initialised CostRepository on the right backend
  - runtime_tables: Runtime-side tables created on the same DB

Import in test modules with:
    from tests.conftest_db import postgres_url, cost_repo_pg, runtime_tables_pg
or add to tests/runtime/jobs/conftest.py.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Dynamic import helpers — conftest.py has already extended sys.path
# ---------------------------------------------------------------------------
from praxis.kernel.cost.storage.repository import CostRepository

# ---------------------------------------------------------------------------
# SQLite fixture (no Docker required)
# ---------------------------------------------------------------------------


@pytest.fixture
def sqlite_db_url(tmp_path: Path) -> str:
    """Return a fresh sqlite+aiosqlite URL for each test function."""
    db = tmp_path / "test.db"
    return f"sqlite+aiosqlite:///{db}"


@pytest_asyncio.fixture
async def cost_repo_sqlite(sqlite_db_url: str) -> AsyncIterator[CostRepository]:
    """CostRepository + Runtime tables on a fresh SQLite DB."""
    from praxis.kernel.runtime.jobs.schema import RuntimeBase

    repo = CostRepository(sqlite_db_url)
    await repo.initialize()  # Pi-Mono tables

    # Runtime tables on the same engine
    async with repo._engine.begin() as conn:
        await conn.run_sync(RuntimeBase.metadata.create_all)

    try:
        yield repo
    finally:
        await repo.close()


# ---------------------------------------------------------------------------
# Postgres fixture (requires Docker / testcontainers)
# ---------------------------------------------------------------------------


def _requires_postgres() -> bool:
    """Return True if Postgres is available (Docker or env URL)."""
    if os.getenv("PRAXIS_TEST_POSTGRES_URL"):
        return True
    try:
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


requires_postgres = pytest.mark.skipif(
    not _requires_postgres(),
    reason="Postgres not available — set PRAXIS_TEST_POSTGRES_URL or ensure Docker is running",
)


@pytest.fixture(scope="session")
def postgres_container():
    """Start a Postgres 16 container once per test session."""
    custom_url = os.getenv("PRAXIS_TEST_POSTGRES_URL")
    if custom_url:
        yield custom_url
        return

    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url().replace("psycopg2", "asyncpg")
        yield url


@pytest_asyncio.fixture
async def cost_repo_pg(postgres_container: str) -> AsyncIterator[CostRepository]:
    """CostRepository + Runtime tables on a fresh Postgres schema."""

    from praxis.kernel.runtime.jobs.schema import RuntimeBase

    repo = CostRepository(postgres_container)
    await repo.initialize()  # creates Pi-Mono tables

    # Create Runtime tables (jobs_queue, outbox_drain_retries) on the same engine
    async with repo._engine.begin() as conn:
        await conn.run_sync(RuntimeBase.metadata.create_all)

    try:
        yield repo
    finally:
        # Drop Runtime tables to keep the container clean between tests
        async with repo._engine.begin() as conn:
            await conn.run_sync(RuntimeBase.metadata.drop_all)
        await repo.close()
