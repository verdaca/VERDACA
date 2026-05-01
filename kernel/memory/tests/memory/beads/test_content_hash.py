"""Property-based + unit tests for Beads content hashing.

Validates the three invariants that make the Merkle chain meaningful:

1. **Determinism.** The same input always hashes to the same output.
2. **Stability under key reordering.** Canonicalization eliminates field
   ordering as a variable, so two semantically identical beads produce
   the same hash regardless of dict construction order.
3. **Sensitivity.** Any change to any field (tenant_hash, timestamp,
   previous_bead_hash, operation_type, payload field) flips the hash.

`verify_bead_hash` round-trip is tested as the operational contract: a
freshly hashed bead verifies; a tampered bead does not.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from praxis.kernel.memory._internal.beads.content_hash import (
    canonical_serialize,
    compute_bead_hash,
    verify_bead_hash,
)
from praxis.kernel.memory._internal.beads.models import (
    Bead,
    BeadOperationType,
    GenesisPayload,
    StoreDecisionPayload,
)

# NOTE: tests/memory/** is exempted from ruff TID251 — white-box allowed.


def _make_decision_payload(
    *,
    entry_id: str = "entry-1",
    decision_summary: str = "choose option A",
    confidence: float = 0.9,
) -> StoreDecisionPayload:
    return StoreDecisionPayload(
        entry_id=entry_id,
        decision_summary=decision_summary,
        confidence=confidence,
    )


# =============================================================================
# Canonical serialization
# =============================================================================


def test_canonical_serialize_sorts_top_level_keys() -> None:
    unordered = {"b": 1, "a": 2, "c": 3}
    reordered = {"c": 3, "a": 2, "b": 1}
    assert canonical_serialize(unordered) == canonical_serialize(reordered)


def test_canonical_serialize_sorts_nested_keys() -> None:
    unordered = {"outer": {"z": 1, "a": 2}}
    reordered = {"outer": {"a": 2, "z": 1}}
    assert canonical_serialize(unordered) == canonical_serialize(reordered)


def test_canonical_serialize_preserves_none_values() -> None:
    """None-valued field is distinct from absent field."""
    with_none = {"field": None}
    absent = {}
    assert canonical_serialize(with_none) != canonical_serialize(absent)


def test_canonical_serialize_preserves_list_order() -> None:
    """Lists are NOT sorted — their order is semantic content."""
    a = {"items": [1, 2, 3]}
    b = {"items": [3, 2, 1]}
    assert canonical_serialize(a) != canonical_serialize(b)


# =============================================================================
# compute_bead_hash — determinism and sensitivity
# =============================================================================


def test_compute_bead_hash_is_deterministic() -> None:
    kwargs = dict(
        previous_bead_hash=None,
        timestamp="2026-04-12T21:00:00+00:00",
        tenant_hash="tenant-abc",
        operation_type=BeadOperationType.STORE_DECISION,
        payload=_make_decision_payload(),
    )
    h1 = compute_bead_hash(**kwargs)  # type: ignore[arg-type]
    h2 = compute_bead_hash(**kwargs)  # type: ignore[arg-type]
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex length
    assert h1 == h1.lower()  # lowercase hex discipline


def test_compute_bead_hash_flips_on_tenant_change() -> None:
    base_kwargs = dict(
        previous_bead_hash=None,
        timestamp="2026-04-12T21:00:00+00:00",
        operation_type=BeadOperationType.STORE_DECISION,
        payload=_make_decision_payload(),
    )
    h1 = compute_bead_hash(tenant_hash="tenant-a", **base_kwargs)  # type: ignore[arg-type]
    h2 = compute_bead_hash(tenant_hash="tenant-b", **base_kwargs)  # type: ignore[arg-type]
    assert h1 != h2


def test_compute_bead_hash_flips_on_timestamp_change() -> None:
    base_kwargs = dict(
        previous_bead_hash=None,
        tenant_hash="tenant-abc",
        operation_type=BeadOperationType.STORE_DECISION,
        payload=_make_decision_payload(),
    )
    h1 = compute_bead_hash(timestamp="2026-04-12T21:00:00+00:00", **base_kwargs)  # type: ignore[arg-type]
    h2 = compute_bead_hash(timestamp="2026-04-12T21:00:01+00:00", **base_kwargs)  # type: ignore[arg-type]
    assert h1 != h2


def test_compute_bead_hash_flips_on_previous_hash_change() -> None:
    base_kwargs = dict(
        timestamp="2026-04-12T21:00:00+00:00",
        tenant_hash="tenant-abc",
        operation_type=BeadOperationType.STORE_DECISION,
        payload=_make_decision_payload(),
    )
    h1 = compute_bead_hash(previous_bead_hash=None, **base_kwargs)  # type: ignore[arg-type]
    h2 = compute_bead_hash(previous_bead_hash="a" * 64, **base_kwargs)  # type: ignore[arg-type]
    assert h1 != h2


def test_compute_bead_hash_flips_on_payload_field_change() -> None:
    base_kwargs = dict(
        previous_bead_hash=None,
        timestamp="2026-04-12T21:00:00+00:00",
        tenant_hash="tenant-abc",
        operation_type=BeadOperationType.STORE_DECISION,
    )
    h1 = compute_bead_hash(payload=_make_decision_payload(confidence=0.9), **base_kwargs)  # type: ignore[arg-type]
    h2 = compute_bead_hash(payload=_make_decision_payload(confidence=0.91), **base_kwargs)  # type: ignore[arg-type]
    assert h1 != h2


# =============================================================================
# Hypothesis property tests
# =============================================================================


@given(
    tenant=st.text(min_size=1, max_size=32),
    seconds=st.integers(min_value=0, max_value=2_000_000_000),
    entry_id=st.text(min_size=1, max_size=32),
    confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
def test_property_hash_is_deterministic_across_arbitrary_inputs(
    tenant: str,
    seconds: int,
    entry_id: str,
    confidence: float,
) -> None:
    """For any legal input combination, compute_bead_hash is deterministic."""
    ts = datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
    payload = _make_decision_payload(entry_id=entry_id, confidence=confidence)
    h1 = compute_bead_hash(
        previous_bead_hash=None,
        timestamp=ts,
        tenant_hash=tenant,
        operation_type=BeadOperationType.STORE_DECISION,
        payload=payload,
    )
    h2 = compute_bead_hash(
        previous_bead_hash=None,
        timestamp=ts,
        tenant_hash=tenant,
        operation_type=BeadOperationType.STORE_DECISION,
        payload=payload,
    )
    assert h1 == h2


@given(
    tenant_a=st.text(min_size=1, max_size=32),
    tenant_b=st.text(min_size=1, max_size=32),
)
def test_property_different_tenants_produce_different_hashes(tenant_a: str, tenant_b: str) -> None:
    """If tenants differ, the hashes differ (no accidental collision)."""
    if tenant_a == tenant_b:
        return  # skip the empty-difference case
    ts = "2026-04-12T21:00:00+00:00"
    payload = _make_decision_payload()
    h1 = compute_bead_hash(
        previous_bead_hash=None,
        timestamp=ts,
        tenant_hash=tenant_a,
        operation_type=BeadOperationType.STORE_DECISION,
        payload=payload,
    )
    h2 = compute_bead_hash(
        previous_bead_hash=None,
        timestamp=ts,
        tenant_hash=tenant_b,
        operation_type=BeadOperationType.STORE_DECISION,
        payload=payload,
    )
    assert h1 != h2


# =============================================================================
# verify_bead_hash round-trip
# =============================================================================


def test_verify_bead_hash_accepts_self_consistent_bead() -> None:
    ts = datetime(2026, 4, 12, 21, 0, 0, tzinfo=timezone.utc)
    payload = GenesisPayload()
    bead_hash = compute_bead_hash(
        previous_bead_hash=None,
        timestamp=ts.isoformat(),
        tenant_hash="tenant-abc",
        operation_type=BeadOperationType.GENESIS,
        payload=payload,
    )
    bead = Bead(
        bead_hash=bead_hash,
        previous_bead_hash=None,
        timestamp=ts,
        tenant_hash="tenant-abc",
        operation_type=BeadOperationType.GENESIS,
        payload=payload,
    )
    assert verify_bead_hash(bead) is True


def test_verify_bead_hash_rejects_tampered_bead() -> None:
    """A bead constructed with a wrong hash fails verification."""
    ts = datetime(2026, 4, 12, 21, 0, 0, tzinfo=timezone.utc)
    bead = Bead(
        bead_hash="0" * 64,  # deliberately wrong
        previous_bead_hash=None,
        timestamp=ts,
        tenant_hash="tenant-abc",
        operation_type=BeadOperationType.GENESIS,
        payload=GenesisPayload(),
    )
    assert verify_bead_hash(bead) is False


def test_bead_model_is_frozen() -> None:
    """Beads are values, not handles — post-construction mutation forbidden."""
    ts = datetime(2026, 4, 12, 21, 0, 0, tzinfo=timezone.utc)
    bead = Bead(
        bead_hash="0" * 64,
        previous_bead_hash=None,
        timestamp=ts,
        tenant_hash="tenant-abc",
        operation_type=BeadOperationType.GENESIS,
        payload=GenesisPayload(),
    )
    with pytest.raises(ValidationError):
        bead.tenant_hash = "tenant-xyz"  # type: ignore[misc]
