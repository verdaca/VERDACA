"""Bootstrap migration tests — mac/test-strategy.md v0.3 §8.1.

Covers MAC-T-BOOT-MIGRATION-01..03. Verifies the migration file
exists at the canonical path, declares the 7 required columns per
arch §8.1, and is idempotent at the SQL level (CREATE TABLE IF NOT
EXISTS).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.mac.migrations import (
    CREATE_TABLE_SQL,
    DROP_TABLE_SQL,
    MIGRATION_ID,
    MIGRATION_NAME,
    REQUIRED_COLUMNS,
    upgrade,
)


_MIGRATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "praxis"
    / "kernel"
    / "mac"
    / "migrations"
    / "mac_bootstrap_metadata_0001.py"
)


@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
def test_mac_t_boot_migration_01_creates_sidecar_table_with_required_columns() -> None:
    """MAC-T-BOOT-MIGRATION-01 — migration declares the 7 required
    columns per arch §8.1 verbatim.
    """
    assert MIGRATION_ID == "0001"
    assert MIGRATION_NAME == "mac_bootstrap_metadata"
    assert len(REQUIRED_COLUMNS) == 7

    expected_columns = {
        "experience_entry_id",
        "tenant_hash",
        "source",
        "bootstrap",
        "benchmark_question_id",
        "calibration_anchor_score",
        "created_at",
    }
    actual_columns = {col_name for col_name, _ in REQUIRED_COLUMNS}
    assert actual_columns == expected_columns

    # Each required column appears in the DDL string.
    for col_name in expected_columns:
        assert col_name in CREATE_TABLE_SQL, f"missing column {col_name} in DDL"

    # Tenant hash index present.
    assert "ix_mac_bootstrap_tenant" in CREATE_TABLE_SQL
    assert "tenant_hash" in CREATE_TABLE_SQL

    # FK to experience_entries declared (arch §8.1 verbatim).
    assert "REFERENCES experience_entries(entry_id)" in CREATE_TABLE_SQL


@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
def test_mac_t_boot_migration_02_is_idempotent_at_sql_level() -> None:
    """MAC-T-BOOT-MIGRATION-02 — CREATE TABLE IF NOT EXISTS makes the
    migration safe to re-run.

    Per arch §8.1 + S-Q1: the migration is idempotent at the SQL
    level (re-running yields no error). Table-level S-Q1 is
    enforced via ``CREATE TABLE IF NOT EXISTS``; row-level S-Q1
    (loader idempotency) is in MAC-T-BOOT-IDEMPOTENT-01..04.
    """
    assert "CREATE TABLE IF NOT EXISTS mac_bootstrap_metadata" in CREATE_TABLE_SQL
    assert "CREATE INDEX IF NOT EXISTS ix_mac_bootstrap_tenant" in CREATE_TABLE_SQL

    # Reverse migration is also idempotent.
    assert "DROP TABLE IF EXISTS" in DROP_TABLE_SQL
    assert "DROP INDEX IF EXISTS" in DROP_TABLE_SQL


@pytest.mark.critical
@pytest.mark.mac_bootstrap_loader
@pytest.mark.static
def test_mac_t_boot_migration_03_lives_under_mac_migrations() -> None:
    """MAC-T-BOOT-MIGRATION-03 — migration lives at
    ``praxis/kernel/mac/migrations/mac_bootstrap_metadata_0001.py``,
    NOT under ``praxis/kernel/memory/migrations/``.

    Stage 3 Memory schema is FROZEN — MAC owns its own migration
    namespace per arch §8.1 Option Y rationale.
    """
    assert _MIGRATION_FILE.exists(), (
        f"MAC migration file missing at {_MIGRATION_FILE}"
    )

    # The migration must NOT live under praxis/kernel/memory/
    assert "praxis" in str(_MIGRATION_FILE)
    assert "kernel" in str(_MIGRATION_FILE)
    assert "mac" in str(_MIGRATION_FILE)
    assert "migrations" in str(_MIGRATION_FILE)
    # NOT under memory/
    parts = _MIGRATION_FILE.parts
    assert "memory" not in parts, (
        f"MAC migration must NOT live under praxis/kernel/memory/; "
        f"got path {_MIGRATION_FILE}"
    )

    # upgrade() is callable and returns the DDL string.
    assert upgrade() == CREATE_TABLE_SQL
