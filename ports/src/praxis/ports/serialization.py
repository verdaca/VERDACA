"""Serialization Port — Protocol + DTOs + error specializations.

Substance source: `port-contracts.md` v0.2 §2 / ADR-9.1.2-2 (PROPOSED).
Vendor strategy: `ports-architecture.md` §3 ADR-9.2-V2 v0.2 corrigendum
(in-tree adapter wrapping kernel TONL substrate at
`praxis.kernel.compression.tonl`; substrate composes per V4-Pi-Mono shape).

This module introduces zero new contract substance beyond §2.3. Pure
Python, no upstream imports.

Deprecation policy: see `ports-architecture.md` §6 for `API_VERSION` /
`schema_version` bump rules. No executable deprecation machinery lives at
the port layer.

12 binding MAC-Ts at `test-strategy.md` v0.2 §2.2.2:
    M-T-SER-ENCODE-TONL-01 / -DECODE-TONL-01 (TONL adapter primitives)
    M-T-SER-ENCODE-MSGSPEC-01 / -DECODE-MSGSPEC-01 (Stage 10 deferred per ADR-9.2-V2 v0.2)
    M-T-SER-EVO-01..04 (schema-evolution; -EVO-01 carries allow-list entry #21)
    M-T-SER-FUZZ-01..03 (fuzz roundtrip; -FUZZ-01 carries allow-list entry #22)
    M-T-SER-EXTRA-FORBID-01 (DTO discipline)

`SerializablePayload` is the canonical home for the Serialization port DTO
per `port-contracts.md` v0.2 §2.3. The 9.4.1 placeholder at
`common.py:122-146` is retired by this module's landing; consumers (Versioned
State port, Migrator Protocol, Beads adapter, VS contract tests) source
`SerializablePayload` from here directly per the A.2 disposition at 9.4.2
preload (4-file consumer rewire, surfaced as Finding A in the 9.4.2
scaffold-window inspection).
"""

from dataclasses import dataclass
from typing import ClassVar, Protocol, runtime_checkable

from praxis.ports.common import (
    ContractViolation,
    VerdacaDTOMixin,
)

# ---------------------------------------------------------------------------
# Type alias — recursive JSON-compatible values per §2.3
# ---------------------------------------------------------------------------

# `JsonValue` matches port-contracts.md v0.2 §2.3 line 305 ("JsonValue =
# recursive primitive type"). PEP 695 `type` statement is required by
# Pydantic v2 for recursive aliases (per Pydantic 2.12 docs:
# https://docs.pydantic.dev/2.12/concepts/types/#named-recursive-types —
# implicit Union forward-refs trigger RecursionError during schema build).
# Python 3.12+ syntax; matches kernel/compression pyproject.toml target.
type JsonValue = bool | int | float | str | None | list[JsonValue] | dict[str, JsonValue]


# ---------------------------------------------------------------------------
# DTOs — §2.3 verbatim
# ---------------------------------------------------------------------------


class SerializablePayload(VerdacaDTOMixin):
    """The payload value crossing a serialization boundary.

    `body` carries the JSON-compatible content; `payload_kind` discriminates
    the tagged-union variant. `schema_version` (inherited from VerdacaDTOMixin)
    couples to the encoded form via `EncodedBytes.encoded_schema_version`
    (binding contract per M-T-SER-ENCODE-TONL-01).

    Per port-contracts.md v0.2 §2.3 Verdaca-owned: `schema_version` field
    presence is structural. `extra="forbid"` (inherited from VerdacaDTOMixin)
    is the structural enforcement of M-T-SER-EXTRA-FORBID-01.
    """

    body: dict[str, JsonValue]
    payload_kind: str


class EncodedBytes(VerdacaDTOMixin):
    """Encoded form of a `SerializablePayload`.

    `data` is the encoded bytes; `encoding_format` names the adapter
    (e.g. "tonl-v0.1", "msgspec-json"); `encoded_schema_version` MUST match
    the source payload's `schema_version` pre-encode (binding contract per
    port-contracts.md v0.2 §2.3 + M-T-SER-ENCODE-TONL-01 assertion).
    """

    data: bytes
    encoding_format: str
    encoded_schema_version: int


class RoundtripFuzzReport(VerdacaDTOMixin):
    """Output of `fuzz_roundtrip(sample_count, seed)`.

    Deterministic per `(sample_count, seed)` pair (M-T-SER-FUZZ-02 invariant:
    same arguments invoked twice → identical report). `samples_passed`
    equals `sample_count` when no failure occurred (otherwise the harness
    raises `RoundtripDriftDetected` with `failing_seed` + `diff_summary`
    instead of returning a report — M-T-SER-FUZZ-01).
    """

    sample_count: int
    seed: int
    samples_passed: int
    encoding_format: str


# ---------------------------------------------------------------------------
# Error specializations — §2.3 verbatim
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class SchemaEvolutionFailure(ContractViolation):
    """Decoded payload's `schema_version` is incompatible with
    `expected_schema_version` AND no migration path exists.

    Bound by M-T-SER-EVO-01 (allow-list entry #21) and M-T-SER-EVO-02:
    must carry `decoded_version` and `expected_version`.
    """

    decoded_version: int
    expected_version: int


@dataclass(kw_only=True)
class RoundtripDriftDetected(ContractViolation):
    """`fuzz_roundtrip` found a sample where `decode(encode(x)) != x`.

    Bound by M-T-SER-FUZZ-01 (allow-list entry #22): must carry
    `failing_seed` + `diff_summary`.
    """

    failing_seed: int
    diff_summary: str


# ---------------------------------------------------------------------------
# Protocol surface — §2.3 verbatim
# ---------------------------------------------------------------------------


@runtime_checkable
class SerializationPort(Protocol):
    """Roundtrip-stable serialization with explicit schema-evolution.

    Per `port-contracts.md` v0.2 §2 design intent: schema evolution is a
    falsifiable contract (`can_decode_version` returns True/False, never
    "maybe"); fuzz harness on Protocol makes drift detection structural,
    not procedural.

    Async / streaming / idempotency profile (§2.3):
        encode / decode       — sync, deterministic, idempotent
        can_decode_version    — sync, idempotent
        fuzz_roundtrip        — sync (long-running), idempotent (seeded)

    `@runtime_checkable` decoration follows the 9.4.1 `VersionedStatePort`
    precedent (agent-initiative additive decision documented in
    `adapters/beads/.../changelog.md` v0.1.0; Cleo 9.6 supply-chain review
    is aware). Adapter `on_init()` performs `isinstance(self,
    SerializationPort)` self-check per executor playbook §9.C addendum.
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    def encode(self, payload: SerializablePayload) -> EncodedBytes: ...

    def decode(
        self,
        encoded: EncodedBytes,
        expected_schema_version: int,
    ) -> SerializablePayload: ...

    def can_decode_version(self, schema_version: int) -> bool: ...

    def fuzz_roundtrip(
        self,
        sample_count: int,
        seed: int,
    ) -> RoundtripFuzzReport: ...


__all__ = [
    "API_VERSION",
    "EncodedBytes",
    "JsonValue",
    "RoundtripDriftDetected",
    "RoundtripFuzzReport",
    "SchemaEvolutionFailure",
    "SerializablePayload",
    "SerializationPort",
]


API_VERSION: str = SerializationPort.API_VERSION
