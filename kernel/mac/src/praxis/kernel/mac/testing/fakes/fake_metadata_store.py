"""InMemoryMacBootstrapMetadataStore — test-strategy v0.3 §14.3.6.

In-memory substitute for the ``mac_bootstrap_metadata`` sidecar table.
Used by Tier 1 unit tests so they don't need a real Postgres or
SQLite instance. Tier 2 integration tests substitute a real adapter
backed by testcontainers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class MacBootstrapMetadataRow:
    """One row in the sidecar table."""

    experience_entry_id: str
    tenant_hash: str
    source: str
    bootstrap: bool
    benchmark_question_id: str
    calibration_anchor_score: float
    created_at: datetime


@dataclass
class InMemoryMacBootstrapMetadataStore:
    """In-memory implementation of the sidecar table contract.

    Maintains a list of rows + a per-tenant ``loaded`` flag so the
    bootstrap loader's idempotency check can read it without touching
    a real database.

    Used by:
      - ``MAC-T-BOOT-IDEMPOTENT-01..04`` (S-Q1 idempotency)
      - ``MAC-T-BOOT-LOAD-01..03`` (gold-standard loading)
      - ``MAC-T-BOOT-FACADE-01..02`` (loader signature sanity)
      - ``MAC-T-INT-MEMORY-PUBLISH-01..02`` (named MAC contract)
    """

    rows: list[MacBootstrapMetadataRow] = field(default_factory=list)
    _loaded_tenants: set[str] = field(default_factory=set)

    def insert(
        self,
        *,
        experience_entry_id: str,
        tenant_hash: str,
        source: str,
        benchmark_question_id: str,
        calibration_anchor_score: float,
        bootstrap: bool = True,
    ) -> MacBootstrapMetadataRow:
        row = MacBootstrapMetadataRow(
            experience_entry_id=experience_entry_id,
            tenant_hash=tenant_hash,
            source=source,
            bootstrap=bootstrap,
            benchmark_question_id=benchmark_question_id,
            calibration_anchor_score=calibration_anchor_score,
            created_at=datetime.now(timezone.utc),
        )
        self.rows.append(row)
        return row

    def mark_loaded(self, tenant_hash: str) -> None:
        self._loaded_tenants.add(tenant_hash)

    def is_loaded(self, tenant_hash: str) -> bool:
        return tenant_hash in self._loaded_tenants

    def count_for_tenant(self, tenant_hash: str) -> int:
        return sum(1 for row in self.rows if row.tenant_hash == tenant_hash)

    def reset(self) -> None:
        self.rows.clear()
        self._loaded_tenants.clear()


__all__ = (
    "InMemoryMacBootstrapMetadataStore",
    "MacBootstrapMetadataRow",
)
