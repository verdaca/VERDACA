"""Verdaca-owned Migrator Protocol.

Per `port-contracts.md` v0.2 §3 / ADR-9.1.2-3 design intent: Verdaca authors
Migrators; adapters execute them. Adapter never authors a concrete
`Migrator` (M-T-VS-MIGRATE-02 grep-enforced at Cleo 9.6: zero
`class.*Migrator` matches outside this subpackage).

Per `ports-architecture.md` v0.2 §4.1 v0.3 corrigendum, this subpackage is
the SOLE legitimate home for Migrator implementations across all Verdaca
code. Concrete Migrators land here over time; the Protocol surface is
captured below.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from praxis.ports.serialization import SerializablePayload


@runtime_checkable
class Migrator(Protocol):
    """Verdaca-owned. Adapter never authors a Migrator.

    Pure function from old payload to new payload. Caller (Versioned State
    port `migrate()` method) supplies the Migrator instance; adapter routes
    snapshots through it. Migrator code hash = `migrator_signature` field
    on `MigrationResult` (audit-stable across calls with same code).
    """

    def __call__(self, old_value: SerializablePayload) -> SerializablePayload: ...


__all__ = ["Migrator"]
