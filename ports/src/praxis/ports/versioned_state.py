"""Versioned State Port — Protocol + DTOs + error specializations.

Substance source: `port-contracts.md` v0.2 §3 / ADR-9.1.2-3 (PROPOSED).
Vendor strategy: `ports-architecture.md` v0.2 §3 ADR-9.2-V3 v0.4 corrigendum
(in-tree adapter, lifted from kernel/memory/_internal/beads/ at 9.4.7).

This module introduces zero new contract substance. Pure Python, no
upstream imports.

Deprecation policy: see `ports-architecture.md` §6 for `API_VERSION` /
`schema_version` bump rules. No executable deprecation machinery lives at
the port layer.

10 binding MAC-Ts at `test-strategy.md` v0.2 §2.2.3:
    M-T-VS-SNAPSHOT-01 / -LATEST-01 / -AT-VERSION-01 / -LIST-01 /
    -MIGRATE-01 / -MIGRATE-02 / -MIGRATE-SIG-01 /
    -CONFLICT-01 / -GAP-01 / -SERIAL-COUPLING-01.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol, Sequence, runtime_checkable

from praxis.ports.common import (
    ContractViolation,
    VerdacaDTOMixin,
)
from praxis.ports.migrator import Migrator
from praxis.ports.serialization import SerializablePayload


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class Snapshot(VerdacaDTOMixin):
    """A single versioned snapshot of a key.

    `snapshot_version` is monotonic per key (M-T-VS-SNAPSHOT-01).
    `payload_schema_version` matches the contained value's schema_version
    (M-T-VS-SNAPSHOT-01 invariant).
    """

    key: str
    value: SerializablePayload
    snapshot_version: int
    payload_schema_version: int


class MigrationResult(VerdacaDTOMixin):
    """Outcome of a `migrate(key, from, to, migrator)` call.

    `migrator_signature` is a stable hash of the Migrator code (audit field;
    same Migrator object across two calls produces identical signature —
    M-T-VS-MIGRATE-SIG-01).
    """

    key: str
    from_version: int
    to_version: int
    snapshots_created: int
    migrator_signature: str


# ---------------------------------------------------------------------------
# Error specializations (inherits §0.1 ContractViolation base)
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class SnapshotConflict(ContractViolation):
    """Two snapshots for the same key claim the same `snapshot_version`.

    Bound by M-T-VS-CONFLICT-01: must carry `key` and `conflicting_version`.
    """

    key: str
    conflicting_version: int


@dataclass(kw_only=True)
class MigrationGap(ContractViolation):
    """`migrate(from=A, to=C)` called but no Migrator chains exist for A→B→C.

    Bound by M-T-VS-GAP-01: must carry `key`, `requested_from`,
    `requested_to`, `available_versions`.
    """

    key: str
    requested_from: int
    requested_to: int
    available_versions: list[int]


# ---------------------------------------------------------------------------
# Protocol surface
# ---------------------------------------------------------------------------


@runtime_checkable
class VersionedStatePort(Protocol):
    """Versioned state with deterministic, Verdaca-owned migration.

    Per `port-contracts.md` v0.2 §3 design intent: migration is Verdaca-owned
    (Migrator Protocol at `praxis.ports.migrator.Migrator`); adapter executes
    Verdaca-authored Migrators against its snapshot store. Adapter never
    authors a concrete Migrator (M-T-VS-MIGRATE-02 grep-enforced).

    Async / streaming / idempotency profile (§3.3):
        snapshot              — sync, idempotent (idempotency_key required)
        latest / at_version   — sync, idempotent (read-only)
        list_versions         — sync, idempotent (read-only)
        migrate               — sync (long-running), idempotent (key required)
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    def snapshot(
        self,
        key: str,
        value: SerializablePayload,
        schema_version: int,
    ) -> Snapshot: ...

    def latest(self, key: str) -> Snapshot | None: ...

    def at_version(self, key: str, schema_version: int) -> Snapshot | None: ...

    def migrate(
        self,
        key: str,
        from_version: int,
        to_version: int,
        migrator: Migrator,
    ) -> MigrationResult: ...

    def list_versions(self, key: str) -> Sequence[int]: ...


__all__ = [
    "API_VERSION",
    "MigrationGap",
    "MigrationResult",
    "Snapshot",
    "SnapshotConflict",
    "VersionedStatePort",
]


API_VERSION: str = VersionedStatePort.API_VERSION
