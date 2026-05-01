"""Versioned State port contract tests — 10 MAC-Ts.

Per `test-strategy.md` v0.2 §2.2.3 — 10 binding `M-T-VS-*` MAC-Ts. Each
test below embeds its MAC-T ID in the function name; docstrings quote
the §2.2.3 assertion language verbatim for auditability.

Discipline (per Stage 9.4.1 test-author hand-off):
- Stay strictly within the 10-ID scope. No 11th test, no parametrized
  expansion, no opportunistic coverage.
- Test the public `VersionedStatePort` Protocol surface via the adapter,
  except `M-T-VS-CONFLICT-01` which uses the documented adapter-internal
  `_force_snapshot_at` admin path (the only natural trigger for
  `SnapshotConflict` in this lock-guarded in-process substrate; see
  `adapters/beads/src/praxis/adapters/beads/changelog.md` v0.1.0 entry).
- No `@pytest.mark.no_waiver` — Beads has zero entries in the 22-entry
  allow-list (`test-strategy.md` v0.2 §6.1).
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest

from praxis.adapters.beads.adapter import BeadsAdapter
from praxis.ports.serialization import SerializablePayload
from praxis.ports.versioned_state import (
    MigrationGap,
    MigrationResult,
    Snapshot,
    SnapshotConflict,
)


# Test-only payload constructors (per 9.4.2 Finding B disposition B.1).
# Pre-9.4.2 these were Pydantic subclass narrowings of SerializablePayload
# (body: str overriding body: dict[str, JsonValue]). Pydantic v2 covariance
# blocks that narrowing AND the new SerializablePayload requires
# `correlation_id` (inherited from VerdacaDTOMixin) + `payload_kind`
# (port-contracts.md v0.2 §2.3). Helper-function constructors instantiate
# SerializablePayload directly with body={"text": ...} + payload_kind
# discriminator. See 9.4.2 advisor disposition: B.1 honors port-contracts.md
# verbatim; 9.4.1 placeholder commit at common.py:140-142 pre-staged this
# transition ("9.4.2 replaces this with the full Serialization-port DTO").
_TEST_CORRELATION_ID = "test-correlation-vs-contract"


def _payload_v1(body: str, *, correlation_id: str = _TEST_CORRELATION_ID) -> SerializablePayload:
    """Test-only constructor at schema_version 1."""
    return SerializablePayload(
        schema_version=1,
        correlation_id=correlation_id,
        body={"text": body},
        payload_kind="test_payload_v1",
    )


def _payload_v2(
    body: str,
    label: str,
    *,
    correlation_id: str = _TEST_CORRELATION_ID,
) -> SerializablePayload:
    """Test-only constructor at schema_version 2 (migration target)."""
    return SerializablePayload(
        schema_version=2,
        correlation_id=correlation_id,
        body={"text": body, "label": label},
        payload_kind="test_payload_v2",
    )


@pytest.fixture
def adapter() -> BeadsAdapter:
    return BeadsAdapter()


# ---------------------------------------------------------------------------
# M-T-VS-SNAPSHOT-01
# ---------------------------------------------------------------------------
def test_M_T_VS_SNAPSHOT_01_snapshot_monotonic(adapter: BeadsAdapter) -> None:
    """`snapshot(key, value, schema_version)` — Returns `Snapshot`;
    `snapshot_version` monotonic per key;
    `payload_schema_version == value.schema_version`."""
    snap1 = adapter.snapshot("k", _payload_v1("first"), schema_version=1)
    snap2 = adapter.snapshot("k", _payload_v1("second"), schema_version=1)
    snap3 = adapter.snapshot("k", _payload_v1("third"), schema_version=1)
    assert isinstance(snap1, Snapshot)
    assert snap1.snapshot_version < snap2.snapshot_version
    assert snap2.snapshot_version < snap3.snapshot_version
    assert snap1.payload_schema_version == snap1.value.schema_version
    assert snap2.payload_schema_version == snap2.value.schema_version
    assert snap3.payload_schema_version == snap3.value.schema_version


# ---------------------------------------------------------------------------
# M-T-VS-LATEST-01
# ---------------------------------------------------------------------------
def test_M_T_VS_LATEST_01_latest_after_three_snapshots(adapter: BeadsAdapter) -> None:
    """`latest(key)` after 3 snapshots — Returns snapshot with highest
    `snapshot_version`; p99 < 50ms on synthetic fixture."""
    for i in range(3):
        adapter.snapshot("k", _payload_v1(f"v{i}"), schema_version=1)
    timings: list[float] = []
    last: Snapshot | None = None
    for _ in range(100):
        t0 = time.perf_counter()
        last = adapter.latest("k")
        timings.append(time.perf_counter() - t0)
    assert last is not None
    assert last.snapshot_version == 3
    timings.sort()
    p99 = timings[int(len(timings) * 0.99)]
    assert p99 < 0.050, f"p99={p99 * 1000:.2f}ms exceeds 50ms"


# ---------------------------------------------------------------------------
# M-T-VS-AT-VERSION-01
# ---------------------------------------------------------------------------
def test_M_T_VS_AT_VERSION_01_historical_read(adapter: BeadsAdapter) -> None:
    """`at_version(key, schema_version=N)` — Returns matching snapshot
    or None; no side effect."""
    adapter.snapshot("k", _payload_v1("v1"), schema_version=1)
    adapter.snapshot("k", _payload_v2("v2", "x"), schema_version=2)
    versions_before = list(adapter.list_versions("k"))

    snap = adapter.at_version("k", schema_version=2)
    assert snap is not None
    assert snap.payload_schema_version == 2

    missing = adapter.at_version("k", schema_version=999)
    assert missing is None

    # No side effect: list_versions unchanged across the read calls.
    assert list(adapter.list_versions("k")) == versions_before


# ---------------------------------------------------------------------------
# M-T-VS-LIST-01
# ---------------------------------------------------------------------------
def test_M_T_VS_LIST_01_list_versions_sorted(adapter: BeadsAdapter) -> None:
    """`list_versions(key)` after 5 snapshots — Returns `Sequence[int]`
    of all `snapshot_version` values; sorted ascending."""
    for i in range(5):
        adapter.snapshot("k", _payload_v1(f"v{i}"), schema_version=1)
    versions = list(adapter.list_versions("k"))
    assert versions == [1, 2, 3, 4, 5]
    assert versions == sorted(versions)


# ---------------------------------------------------------------------------
# M-T-VS-MIGRATE-01
# ---------------------------------------------------------------------------
def test_M_T_VS_MIGRATE_01_migrate_happy(adapter: BeadsAdapter) -> None:
    """`migrate(key, from_version, to_version, migrator)` with
    Verdaca-owned Migrator — Returns `MigrationResult`;
    `snapshots_created >= 1`; `migrator_signature` stable hash of
    Migrator code."""
    adapter.snapshot("k", _payload_v1("v1"), schema_version=1)

    def upgrade_v1_to_v2(old: SerializablePayload) -> SerializablePayload:
        text = str(old.body.get("text", ""))
        return _payload_v2(text, "upgraded")

    result = adapter.migrate("k", from_version=1, to_version=2, migrator=upgrade_v1_to_v2)
    assert isinstance(result, MigrationResult)
    assert result.snapshots_created >= 1
    assert isinstance(result.migrator_signature, str)
    assert len(result.migrator_signature) == 64  # sha256 hex
    assert result.from_version == 1
    assert result.to_version == 2


# ---------------------------------------------------------------------------
# M-T-VS-MIGRATE-02
# ---------------------------------------------------------------------------
def test_M_T_VS_MIGRATE_02_adapter_authors_no_migrator() -> None:
    """Cleo grep: `rg "class.*Migrator" adapters/beads/src/praxis/adapters/beads/` —
    Zero results outside `ports/src/praxis/ports/migrator/`. Adapter
    never authors a Migrator."""
    repo_root = Path(__file__).resolve().parents[5]
    adapter_dir = repo_root / "adapters" / "beads" / "src" / "praxis" / "adapters" / "beads"
    assert adapter_dir.exists(), f"Adapter directory not found: {adapter_dir}"

    pattern = re.compile(r"class\b.*\bMigrator\b")
    matches: list[str] = []
    for py_file in adapter_dir.rglob("*.py"):
        for line_no, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                matches.append(f"{py_file.relative_to(repo_root)}:{line_no}: {line}")
    assert not matches, f"Found Migrator class declarations in adapter: {matches}"


# ---------------------------------------------------------------------------
# M-T-VS-MIGRATE-SIG-01
# ---------------------------------------------------------------------------
def test_M_T_VS_MIGRATE_SIG_01_signature_stable(adapter: BeadsAdapter) -> None:
    """Same Migrator code → two `migrate` calls — Same
    `migrator_signature` hash; audit-stable."""

    def upgrade(old: SerializablePayload) -> SerializablePayload:
        text = str(old.body.get("text", ""))
        return _payload_v2(text, "u")

    adapter.snapshot("k1", _payload_v1("a"), schema_version=1)
    r1 = adapter.migrate("k1", from_version=1, to_version=2, migrator=upgrade)

    adapter.snapshot("k2", _payload_v1("b"), schema_version=1)
    r2 = adapter.migrate("k2", from_version=1, to_version=2, migrator=upgrade)

    assert r1.migrator_signature == r2.migrator_signature


# ---------------------------------------------------------------------------
# M-T-VS-CONFLICT-01
# ---------------------------------------------------------------------------
def test_M_T_VS_CONFLICT_01_snapshot_conflict(adapter: BeadsAdapter) -> None:
    """Two snapshots for same key claiming same `snapshot_version` —
    Raises `SnapshotConflict`; `key` + `conflicting_version` set.

    Uses adapter-internal `_force_snapshot_at` admin path (only natural
    trigger for `SnapshotConflict` in this lock-guarded in-process
    substrate; documented in changelog.md v0.1.0).
    """
    adapter._force_snapshot_at(
        "k",
        _payload_v1("first"),
        schema_version=1,
        snapshot_version=1,
    )
    with pytest.raises(SnapshotConflict) as exc_info:
        adapter._force_snapshot_at(
            "k",
            _payload_v1("dup"),
            schema_version=1,
            snapshot_version=1,
        )
    err = exc_info.value
    assert err.key == "k"
    assert err.conflicting_version == 1


# ---------------------------------------------------------------------------
# M-T-VS-GAP-01
# ---------------------------------------------------------------------------
def test_M_T_VS_GAP_01_migration_gap(adapter: BeadsAdapter) -> None:
    """`migrate(from=A, to=C)` with no Migrator for A→B→C chain —
    Raises `MigrationGap`; `requested_from`, `requested_to`,
    `available_versions` set."""
    adapter.snapshot("k", _payload_v1("v1"), schema_version=1)

    def identity(old: SerializablePayload) -> SerializablePayload:
        return old

    with pytest.raises(MigrationGap) as exc_info:
        adapter.migrate("k", from_version=99, to_version=100, migrator=identity)
    err = exc_info.value
    assert err.requested_from == 99
    assert err.requested_to == 100
    assert err.available_versions == [1]


# ---------------------------------------------------------------------------
# M-T-VS-SERIAL-COUPLING-01
# ---------------------------------------------------------------------------
def test_M_T_VS_SERIAL_COUPLING_01_serializable_roundtrip(adapter: BeadsAdapter) -> None:
    """`snapshot(key, value=SerializablePayload)` — Value roundtrips
    through Serialization port; no direct byte-level coupling."""
    payload = _payload_v1("content")
    snap = adapter.snapshot("k", payload, schema_version=1)
    assert isinstance(snap.value, SerializablePayload)
    assert snap.value.payload_kind == "test_payload_v1"
    assert snap.value == payload

    fetched = adapter.latest("k")
    assert fetched is not None
    assert isinstance(fetched.value, SerializablePayload)
    assert fetched.value.payload_kind == "test_payload_v1"
    assert fetched.value == payload
