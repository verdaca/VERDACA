"""In-tree wrap of kernel TONL substrate against `SerializationPort`.

Per ADR-9.2-V2 v0.2 corrigendum (`ports-architecture.md` §3): single
TONL implementation in the codebase, two consumers — kernel
`compression/orchestrator.py` (Stage-2 compression-layer duty) and this
adapter (`SerializationPort` duty). Direct ADR-9.2-V4 Pi-Mono shape.

Substrate composition (per 9.4.2 preload Item 7.3 mapping table):
    encode/decode primitives → delegated to kernel substrate
    can_decode_version       → adapter-authored on top
    fuzz_roundtrip           → adapter-authored on top
    schema-evolution checks  → adapter-authored at decode boundary

Substrate hardening (streaming encode/decode wiring, msgspec substitute,
forward-migration chains) is Stage 10 concern. At 9.4.2 the in-tree
wrapper is sufficient for the 10 in-scope `M-T-SER-*` MAC-Ts at
`test-strategy.md` v0.2 §2.2.2.

Deprecation policy: see `ports-architecture.md` §6 for `API_VERSION` /
`schema_version` bump rules.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import ClassVar

from praxis.kernel.compression.tonl import (
    decode as tonl_decode,
    encode as tonl_encode,
)
from praxis.kernel.compression.tonl.errors import (
    TONLParseError,
    TONLSecurityError,
    TONLTypeError,
    TONLValidationError,
)
from praxis.ports.common import ContractViolation
from praxis.ports.serialization import (
    EncodedBytes,
    JsonValue,
    RoundtripDriftDetected,
    RoundtripFuzzReport,
    SchemaEvolutionFailure,
    SerializablePayload,
    SerializationPort,
)

from praxis.adapters.tonl.version_pin import UPSTREAM_NAME

_PORT_NAME = "serialization"
_ENCODING_FORMAT = "tonl-v0.1.0"
_EXPECTED_PAYLOAD_KEYS = frozenset({"body", "payload_kind", "schema_version"})


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class TONLAdapter:
    """In-tree wrapper of `praxis.kernel.compression.tonl` against
    `SerializationPort`.

    Conforms to `praxis.ports.serialization.SerializationPort` (verify via
    `isinstance(adapter, SerializationPort)`; the Protocol is
    `@runtime_checkable`).
    """

    # Mirror the port's API_VERSION ClassVar so runtime_checkable Protocol
    # conformance succeeds at isinstance() — Protocol declares the
    # attribute, isinstance checks the candidate has it. Per 9.4.1
    # API_VERSION ClassVar bug lesson (executor playbook §9.C addendum).
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(
        self,
        *,
        default_correlation_id: str | None = None,
        supported_schema_versions: set[int] | None = None,
    ) -> None:
        """Construct an adapter.

        `default_correlation_id` is the per-instance OTEL trace fallback
        used when callers do not thread a correlation_id through. If
        `None`, each adapter instance gets a fresh UUID4 — keeps test
        fixtures isolated and avoids cross-instance correlation
        collisions. Mirrors the 9.4.1 BeadsAdapter pattern.

        `supported_schema_versions` declares which schema_versions the
        adapter accepts in `can_decode_version` and at decode boundary.
        Defaults to `{1}` — the v0.1.0 baseline. Tests covering schema
        evolution register additional versions via constructor (e.g.
        `TONLAdapter(supported_schema_versions={1, 2})`). v0.1.0 supports
        only same-version decode; forward-migration chains are Stage 10.
        """
        self._default_correlation_id = default_correlation_id or uuid.uuid4().hex
        self._supported_versions: frozenset[int] = frozenset(
            supported_schema_versions if supported_schema_versions is not None else {1}
        )

    # ------------------------------------------------------------------
    # §2.2 Adapter Lifecycle
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        """Lifecycle: contract self-check.

        Kernel TONL substrate is in-process Python — no upstream
        healthcheck needed. Self-check verifies `isinstance` conformance
        to `SerializationPort` (per executor playbook §9.C addendum;
        precedent: 9.4.1 API_VERSION ClassVar bug surfaced only at test
        run, not by static syntax check).
        """
        if not isinstance(self, SerializationPort):
            raise RuntimeError("TONLAdapter does not conform to SerializationPort")

    def on_shutdown(self) -> None:
        """Lifecycle: no-op.

        In-process kernel-substrate wrapper has no flush/close work.
        """

    # ------------------------------------------------------------------
    # SerializationPort surface
    # ------------------------------------------------------------------

    def encode(self, payload: SerializablePayload) -> EncodedBytes:
        envelope = {
            "body": payload.body,
            "payload_kind": payload.payload_kind,
            "schema_version": payload.schema_version,
        }
        try:
            text = tonl_encode(envelope)
        except TONLValidationError as exc:
            raise self._contract_violation(payload.correlation_id, "value") from exc
        except TONLTypeError as exc:
            raise self._contract_violation(payload.correlation_id, "type") from exc
        except TONLSecurityError as exc:
            raise self._contract_violation(payload.correlation_id, "invariant") from exc

        return EncodedBytes(
            schema_version=1,
            correlation_id=payload.correlation_id,
            idempotency_key=payload.idempotency_key,
            data=text.encode("utf-8"),
            encoding_format=_ENCODING_FORMAT,
            encoded_schema_version=payload.schema_version,
        )

    def decode(
        self,
        encoded: EncodedBytes,
        expected_schema_version: int,
    ) -> SerializablePayload:
        if encoded.encoded_schema_version != expected_schema_version:
            raise SchemaEvolutionFailure(
                port_name=_PORT_NAME,
                correlation_id=encoded.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
                decoded_version=encoded.encoded_schema_version,
                expected_version=expected_schema_version,
            )
        try:
            text = encoded.data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise self._contract_violation(encoded.correlation_id, "value") from exc
        try:
            envelope = tonl_decode(text)
        except TONLParseError as exc:
            raise self._contract_violation(encoded.correlation_id, "value") from exc
        except TONLSecurityError as exc:
            raise self._contract_violation(encoded.correlation_id, "invariant") from exc

        if not isinstance(envelope, dict):
            raise self._contract_violation(encoded.correlation_id, "type")

        # M-T-SER-EXTRA-FORBID-01 — reject extra upstream-leaked fields.
        extra_keys = set(envelope.keys()) - _EXPECTED_PAYLOAD_KEYS
        if extra_keys:
            raise self._contract_violation(encoded.correlation_id, "invariant")

        # Required-key presence — surface as ContractViolation rather than
        # bare KeyError.
        for required_key in _EXPECTED_PAYLOAD_KEYS:
            if required_key not in envelope:
                raise self._contract_violation(encoded.correlation_id, "invariant")

        return SerializablePayload(
            schema_version=envelope["schema_version"],
            correlation_id=encoded.correlation_id,
            idempotency_key=encoded.idempotency_key,
            body=envelope["body"],
            payload_kind=envelope["payload_kind"],
        )

    def can_decode_version(self, schema_version: int) -> bool:
        return schema_version in self._supported_versions

    def fuzz_roundtrip(
        self,
        sample_count: int,
        seed: int,
    ) -> RoundtripFuzzReport:
        rng = random.Random(seed)
        report_correlation_id = f"fuzz-seed-{seed}"
        for idx in range(sample_count):
            sample = self._fuzz_sample(rng, idx, schema_version=1)
            encoded = self.encode(sample)
            decoded = self.decode(encoded, expected_schema_version=1)
            if decoded != sample:
                raise RoundtripDriftDetected(
                    port_name=_PORT_NAME,
                    correlation_id=report_correlation_id,
                    occurred_at=_utc_now(),
                    upstream_name=UPSTREAM_NAME,
                    violation_class="value",
                    failing_seed=seed,
                    diff_summary=f"sample[{idx}]: {sample!r} != {decoded!r}",
                )
        return RoundtripFuzzReport(
            schema_version=1,
            correlation_id=report_correlation_id,
            sample_count=sample_count,
            seed=seed,
            samples_passed=sample_count,
            encoding_format=_ENCODING_FORMAT,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _contract_violation(
        self,
        correlation_id: str,
        violation_class: str,
    ) -> ContractViolation:
        return ContractViolation(
            port_name=_PORT_NAME,
            correlation_id=correlation_id,
            occurred_at=_utc_now(),
            upstream_name=UPSTREAM_NAME,
            violation_class=violation_class,  # type: ignore[arg-type]
        )

    def _fuzz_sample(
        self,
        rng: random.Random,
        idx: int,
        *,
        schema_version: int,
    ) -> SerializablePayload:
        """Deterministic sample given (rng-state, idx).

        Excludes floats (kernel TONL rejects them per
        `kernel/compression/.../tonl/encode.py:64-67`). Includes nested
        dicts, lists, Unicode strings for M-T-SER-FUZZ-03 adversarial
        coverage.
        """
        body: dict[str, JsonValue] = {
            f"f{i}": self._fuzz_value(rng, depth=0)
            for i in range(rng.randint(1, 4))
        }
        return SerializablePayload(
            schema_version=schema_version,
            correlation_id=f"fuzz-sample-{idx}",
            body=body,
            payload_kind=rng.choice(["task", "decision", "fact"]),
        )

    def _fuzz_value(self, rng: random.Random, *, depth: int) -> JsonValue:
        if depth >= 3:
            return rng.choice([None, True, False, 0, 1, "leaf", "ünicödé"])
        choice = rng.randint(0, 6)
        if choice == 0:
            return None
        if choice == 1:
            return rng.choice([True, False])
        if choice == 2:
            return rng.randint(-1_000_000, 1_000_000)
        if choice == 3:
            return rng.choice(["", "a", "ünicödé", "🚀", "line\nbreak", "tab\there"])
        if choice == 4:
            size = rng.randint(0, 3)
            return [self._fuzz_value(rng, depth=depth + 1) for _ in range(size)]
        size = rng.randint(0, 3)
        return {f"k{i}": self._fuzz_value(rng, depth=depth + 1) for i in range(size)}


__all__ = ["TONLAdapter"]
