"""Migration 0001 — ``mac_bootstrap_metadata`` sidecar table.

Per arch §8.1 Option Y ratification (2026-04-14): MAC's bootstrap
loader writes gold-standard records into ``experience_entries`` via
the Memory facade AND into this sidecar table at the same logical
write boundary. Stage 3 Memory schema is FROZEN; this sidecar is the
MAC-owned artifact that satisfies SQ-6 without reopening Memory.

**Schema (verbatim from arch §8.1):**

    CREATE TABLE mac_bootstrap_metadata (
        experience_entry_id  CHAR(26) PRIMARY KEY REFERENCES experience_entries(entry_id),
        tenant_hash          CHAR(64) NOT NULL,
        source               TEXT     NOT NULL,
        bootstrap            BOOLEAN  NOT NULL DEFAULT TRUE,
        benchmark_question_id TEXT    NOT NULL,
        calibration_anchor_score REAL NOT NULL,
        created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (tenant_hash, benchmark_question_id)
    );
    CREATE INDEX ix_mac_bootstrap_tenant ON mac_bootstrap_metadata (tenant_hash);

The migration file is module-load-safe — importing it does not touch
any database. The :func:`upgrade` function returns the SQL string for
the caller (Stage 7 deployment runbook or a test harness using
testcontainers Postgres) to execute.

Binding anchors:
  - mac/architecture.md §8.1 Option Y Ratification (table definition verbatim)
  - mac/architecture.md §13.2 Rejected Alternatives (Option X — JSONB column rejected)
  - mac/test-strategy.md v0.3 §8.1 MAC-T-BOOT-MIGRATION-01..03
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class BootstrapMetadataStore(Protocol):
    """Behavioral contract for the ``mac_bootstrap_metadata`` sidecar.

    Colocated with the schema-authoritative migration file so the
    behavioral contract and the DDL it shadows live side-by-side.
    Production code (``backfill.py``, ``bootstrap.py``,
    ``integrations/memory.py``) depends on this Protocol, never on any
    concrete implementation in ``testing.fakes``. The in-memory fake
    :class:`praxis.kernel.mac.testing.fakes.fake_metadata_store.InMemoryMacBootstrapMetadataStore`
    structurally satisfies the Protocol; at Stage 7 POV Harness a
    real database-backed store substitutes in without any production
    import-site change.
    """

    def is_loaded(self, tenant_hash: str) -> bool: ...

    def mark_loaded(self, tenant_hash: str) -> None: ...

    def insert(
        self,
        *,
        experience_entry_id: str,
        tenant_hash: str,
        source: str,
        benchmark_question_id: str,
        calibration_anchor_score: float,
        bootstrap: bool = True,
    ) -> object: ...


MIGRATION_ID: str = "0001"
"""Sequential migration ID. Future MAC migrations increment this."""

MIGRATION_NAME: str = "mac_bootstrap_metadata"
"""Migration short name; matches the filename suffix and the table
name being created."""


REQUIRED_COLUMNS: tuple[tuple[str, str], ...] = (
    ("experience_entry_id", "CHAR(26)"),
    ("tenant_hash", "CHAR(64)"),
    ("source", "TEXT"),
    ("bootstrap", "BOOLEAN"),
    ("benchmark_question_id", "TEXT"),
    ("calibration_anchor_score", "REAL"),
    ("created_at", "TIMESTAMPTZ"),
)
"""The 7 required columns per arch §8.1. ``MAC-T-BOOT-MIGRATION-01``
asserts every column is present in :data:`CREATE_TABLE_SQL`."""


CREATE_TABLE_SQL: str = """\
CREATE TABLE IF NOT EXISTS mac_bootstrap_metadata (
    experience_entry_id      CHAR(26) PRIMARY KEY REFERENCES experience_entries(entry_id),
    tenant_hash              CHAR(64) NOT NULL,
    source                   TEXT     NOT NULL,
    bootstrap                BOOLEAN  NOT NULL DEFAULT TRUE,
    benchmark_question_id    TEXT     NOT NULL,
    calibration_anchor_score REAL     NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_hash, benchmark_question_id)
);
CREATE INDEX IF NOT EXISTS ix_mac_bootstrap_tenant
    ON mac_bootstrap_metadata (tenant_hash);
"""
"""DDL for the sidecar table. ``CREATE TABLE IF NOT EXISTS`` makes
the migration idempotent at the SQL level — running it twice is a
no-op. ``MAC-T-BOOT-MIGRATION-02`` exercises this property."""


DROP_TABLE_SQL: str = """\
DROP INDEX IF EXISTS ix_mac_bootstrap_tenant;
DROP TABLE IF EXISTS mac_bootstrap_metadata;
"""
"""Reverse migration. Per arch §13.2 Rejected Alternatives rationale
#3 (reversibility), the sidecar approach is reversible — dropping
this table is a MAC-local change with no blast radius into the hot
``experience_entries`` table."""


def upgrade() -> str:
    """Return the forward-migration SQL.

    Callers (Stage 7 deployment runbook, integration test harnesses)
    execute this against their database connection. The migration
    module itself does NOT open any database connection — keeping the
    module load-safe under unit tests that only inspect the SQL string.
    """
    return CREATE_TABLE_SQL


def downgrade() -> str:
    """Return the reverse-migration SQL."""
    return DROP_TABLE_SQL


__all__ = (
    "BootstrapMetadataStore",
    "CREATE_TABLE_SQL",
    "DROP_TABLE_SQL",
    "MIGRATION_ID",
    "MIGRATION_NAME",
    "REQUIRED_COLUMNS",
    "downgrade",
    "upgrade",
)
