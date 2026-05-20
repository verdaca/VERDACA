"""Greenfield in-tree implementation of `VersionedStatePort`.

Per ADR-9.2-V3 v0.5 corrigendum (`ports-architecture.md` §3): greenfield
Verdaca-authored Python with in-process dict-backed snapshot store. No
upstream substrate; codename "Beads" inherited from the Stage 9 frame,
NOT a substrate-lift target.

Substrate hardening (Postgres backing, durability across process restart)
is a Stage 10 concern. At 9.4.1 the in-process dict store is sufficient
for the 10 `M-T-VS-*` MAC-Ts at `test-strategy.md` v0.2 §2.2.3.

Deprecation policy: see `ports-architecture.md` §6 for `API_VERSION` /
`schema_version` bump rules.
"""

from __future__ import annotations

import hashlib
import inspect
import threading
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar

from praxis.ports.migrator import Migrator
from praxis.ports.serialization import SerializablePayload
from praxis.ports.versioned_state import (
    MigrationGap,
    MigrationResult,
    Snapshot,
    SnapshotConflict,
    VersionedStatePort,
)

_PORT_NAME = "versioned_state"


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass(slots=True)
class _SnapshotRecord:
    """Internal representation of a stored snapshot."""

    key: str
    value: SerializablePayload
    snapshot_version: int
    payload_schema_version: int
    correlation_id: str
    created_at: datetime = field(default_factory=_utc_now)


def _migrator_signature(migrator: Migrator) -> str:
    """Stable hash of a Migrator's code (M-T-VS-MIGRATE-SIG-01).

    Uses `inspect.getsource()` with `repr(migrator)` fallback for
    built-ins, lambdas without source, and C-extension callables.
    """
    try:
        source = inspect.getsource(migrator)
    except (OSError, TypeError):
        source = repr(migrator)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


class BeadsAdapter:
    """In-tree, in-process `VersionedStatePort` implementation.

    Conforms to `praxis.ports.versioned_state.VersionedStatePort` (verify
    via `isinstance(adapter, VersionedStatePort)`; the Protocol is
    `@runtime_checkable`).
    """

    # Mirror the port's API_VERSION ClassVar so runtime_checkable Protocol
    # conformance succeeds at isinstance() — Protocol declares the
    # attribute, isinstance checks the candidate has it.
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(self, *, default_correlation_id: str | None = None) -> None:
        """Construct an adapter.

        `default_correlation_id` is the per-instance OTEL trace fallback
        used when callers do not thread a correlation_id through (mostly
        test ergonomics). If `None`, each adapter instance gets a fresh
        UUID4 — keeps test fixtures isolated from each other and avoids
        cross-instance correlation collisions. Real production callers
        SHOULD thread a per-call correlation_id; this field is the
        default of last resort.
        """
        self._snapshots: dict[str, list[_SnapshotRecord]] = {}
        self._lock = threading.Lock()
        self._default_correlation_id = default_correlation_id or uuid.uuid4().hex

    # ------------------------------------------------------------------
    # §2.2 Adapter Lifecycle
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        """Lifecycle: contract self-check.

        Greenfield adapter has no upstream healthcheck (no upstream).
        Version-pin assertion lives in `version_pin.py` and is read by
        the contract suite at boot. Self-check verifies `isinstance`
        conformance to `VersionedStatePort`.
        """
        if not isinstance(self, VersionedStatePort):
            raise RuntimeError("BeadsAdapter does not conform to VersionedStatePort")

    def on_shutdown(self) -> None:
        """Lifecycle: no-op.

        In-process dict store has no flush/close work.
        """

    # ------------------------------------------------------------------
    # VersionedStatePort surface
    # ------------------------------------------------------------------

    def snapshot(
        self,
        key: str,
        value: SerializablePayload,
        schema_version: int,
    ) -> Snapshot:
        if value.schema_version != schema_version:
            raise ValueError(
                f"value.schema_version ({value.schema_version}) does not match "
                f"schema_version argument ({schema_version})"
            )
        with self._lock:
            history = self._snapshots.setdefault(key, [])
            next_version = (history[-1].snapshot_version + 1) if history else 1
            record = _SnapshotRecord(
                key=key,
                value=value,
                snapshot_version=next_version,
                payload_schema_version=schema_version,
                correlation_id=self._default_correlation_id,
            )
            history.append(record)
        return self._dto_from_record(record)

    def latest(self, key: str) -> Snapshot | None:
        with self._lock:
            history = self._snapshots.get(key)
            if not history:
                return None
            return self._dto_from_record(history[-1])

    def at_version(self, key: str, schema_version: int) -> Snapshot | None:
        with self._lock:
            history = self._snapshots.get(key, [])
            for record in history:
                if record.payload_schema_version == schema_version:
                    return self._dto_from_record(record)
        return None

    def migrate(
        self,
        key: str,
        from_version: int,
        to_version: int,
        migrator: Migrator,
    ) -> MigrationResult:
        with self._lock:
            history = list(self._snapshots.get(key, []))
        available = [r.payload_schema_version for r in history]
        source = next(
            (r for r in history if r.payload_schema_version == from_version),
            None,
        )
        if source is None:
            raise MigrationGap(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                violation_class="invariant",
                key=key,
                requested_from=from_version,
                requested_to=to_version,
                available_versions=available,
            )
        new_value = migrator(source.value)
        if new_value.schema_version != to_version:
            raise MigrationGap(
                port_name=_PORT_NAME,
                correlation_id=self._default_correlation_id,
                occurred_at=_utc_now(),
                violation_class="invariant",
                key=key,
                requested_from=from_version,
                requested_to=to_version,
                available_versions=available,
            )
        self.snapshot(key, new_value, to_version)
        return MigrationResult(
            schema_version=1,
            correlation_id=self._default_correlation_id,
            key=key,
            from_version=from_version,
            to_version=to_version,
            snapshots_created=1,
            migrator_signature=_migrator_signature(migrator),
        )

    def list_versions(self, key: str) -> Sequence[int]:
        with self._lock:
            history = self._snapshots.get(key, [])
            return sorted(r.snapshot_version for r in history)

    # ------------------------------------------------------------------
    # Adapter-internal admin (test surface — used by M-T-VS-CONFLICT-01)
    # ------------------------------------------------------------------

    def _force_snapshot_at(
        self,
        key: str,
        value: SerializablePayload,
        schema_version: int,
        snapshot_version: int,
    ) -> Snapshot:
        """Force a specific `snapshot_version`. Raises `SnapshotConflict`
        if `(key, snapshot_version)` already exists.

        Adapter-internal; not part of `VersionedStatePort`. Used by
        `M-T-VS-CONFLICT-01` only.
        """
        if value.schema_version != schema_version:
            raise ValueError("value.schema_version != schema_version")
        with self._lock:
            history = self._snapshots.setdefault(key, [])
            for existing in history:
                if existing.snapshot_version == snapshot_version:
                    raise SnapshotConflict(
                        port_name=_PORT_NAME,
                        correlation_id=self._default_correlation_id,
                        occurred_at=_utc_now(),
                        violation_class="invariant",
                        key=key,
                        conflicting_version=snapshot_version,
                    )
            record = _SnapshotRecord(
                key=key,
                value=value,
                snapshot_version=snapshot_version,
                payload_schema_version=schema_version,
                correlation_id=self._default_correlation_id,
            )
            history.append(record)
            history.sort(key=lambda r: r.snapshot_version)
        return self._dto_from_record(record)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _dto_from_record(self, record: _SnapshotRecord) -> Snapshot:
        return Snapshot(
            schema_version=1,
            correlation_id=record.correlation_id,
            key=record.key,
            value=record.value,
            snapshot_version=record.snapshot_version,
            payload_schema_version=record.payload_schema_version,
        )


__all__ = ["BeadsAdapter"]
