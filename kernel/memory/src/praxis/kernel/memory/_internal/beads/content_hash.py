"""Content-hash addressing for beads (pattern B1, B7 from §1.1).

Beads are content-addressed: `bead_hash = sha256(canonical(bead_minus_hash))`.
Two beads with identical content produce identical hashes; concurrent writes
that happen to be the same content dedupe naturally. Two beads with any
content difference produce different hashes — even a one-bit change in a
timestamp or payload field flips the entire hash.

Canonical serialization rules
-----------------------------

1. Fields are ordered lexicographically by key name (recursively for nested
   dicts). Pydantic v2's `model_dump(mode="json")` then a sort pass.
2. `None` values are preserved (not dropped) — presence of a field with
   None is semantically distinct from field absence.
3. `datetime` values serialize to ISO-8601 with UTC offset — Pydantic's
   default JSON mode does this.
4. Floats are serialized as Python `repr()` via the JSON encoder — no
   precision loss from rounding.
5. `bytes` are hex-encoded. Payloads should avoid `bytes` where possible.
6. The `bead_hash` field on `Bead` is excluded from the hash input (it's
   what we're computing).

All serialization uses UTF-8 encoding. The sha256 is emitted as a lowercase
hex string.

Why this matters for replay
---------------------------

Replay (§3.2) walks a chain from genesis, re-computing each bead's hash as
it goes. If a bead's stored hash doesn't match the re-computed hash, the
chain has been tampered with (or the canonical serialization rules
drifted). The invariant test in `tests/memory/beads/` covers both.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from praxis.kernel.memory._internal.beads.models import (
    Bead,
    BeadOperationType,
    BeadPayload,
)


def _canonicalize(value: Any) -> Any:
    """Recursive canonicalizer — sorts dict keys, preserves None, etc.

    This is the gatekeeper for hash stability. DO NOT change without
    bumping the bead payload schema_version AND updating the replay
    invariant test.
    """
    if isinstance(value, dict):
        return {k: _canonicalize(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [_canonicalize(v) for v in value]
    if isinstance(value, tuple):
        return [_canonicalize(v) for v in value]
    return value


def canonical_serialize(bead_without_hash: dict[str, Any]) -> bytes:
    """Serialize a bead-minus-hash dict to canonical UTF-8 JSON bytes.

    Parameters
    ----------
    bead_without_hash
        A dict representing the bead's fields EXCEPT `bead_hash`. Callers
        should use `compute_bead_hash` rather than building this dict
        directly; this function is exposed for replay verification.

    Returns
    -------
    bytes
        UTF-8 encoded JSON with sorted keys at every level. Suitable for
        sha256 input.
    """
    canonical = _canonicalize(bead_without_hash)
    return json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def compute_bead_hash(
    *,
    previous_bead_hash: str | None,
    timestamp: str,
    tenant_hash: str,
    operation_type: BeadOperationType,
    payload: BeadPayload,
) -> str:
    """Compute the sha256 content address of a bead's fields.

    This takes the five bead fields other than `bead_hash` itself and
    returns the lowercase hex digest. Callers then construct the Bead
    model with `bead_hash=<result of this function>`.

    `timestamp` is accepted as a string (the ISO-8601 serialization of a
    datetime) rather than a datetime object so that callers must commit
    to the serialized form before hashing — preventing tz-aware vs
    tz-naive mismatches at hash time.
    """
    bead_dict: dict[str, Any] = {
        "previous_bead_hash": previous_bead_hash,
        "timestamp": timestamp,
        "tenant_hash": tenant_hash,
        "operation_type": operation_type.value,
        "payload": payload.model_dump(mode="json"),
    }
    return hashlib.sha256(canonical_serialize(bead_dict)).hexdigest()


def verify_bead_hash(bead: Bead) -> bool:
    """Re-compute a bead's hash and compare to its stored `bead_hash`.

    Returns True iff the stored hash matches the re-computation. A False
    result indicates chain tampering, canonicalization drift, or a
    construction bug.
    """
    recomputed = compute_bead_hash(
        previous_bead_hash=bead.previous_bead_hash,
        timestamp=bead.timestamp.isoformat(),
        tenant_hash=bead.tenant_hash,
        operation_type=bead.operation_type,
        payload=bead.payload,
    )
    return recomputed == bead.bead_hash


__all__ = [
    "canonical_serialize",
    "compute_bead_hash",
    "verify_bead_hash",
]
