"""Compaction Port — Protocol + DTOs + error specializations.

Substance source: `port-contracts.md` v0.2.6 §4 / ADR-9.1.2-4 (PROPOSED).
Substrate selection is governed by `ports-architecture.md` §3 ADR-9.2-V6;
this module is the PORT and names no substrate — the compaction adapter
and the in-tree-stub fallback are authored in Phase B.1.

Beyond the §3 Protocol/DTO/error substance this module adds one Verdaca-
owned helper — `compute_determinism_hash` — specified by the v0.2.6
ADR-9.1.2-4 §3 corrigendum (closes F-9.4.6-COMP-SEED-PHANTOM). Standard
library only (`hashlib`, `json`); no upstream imports. Pure Python.

API_VERSION = "1.0.0" — unchanged by the v0.2.6 corrigendum: removing the
`StrategyDowngrade` error class is a `major++` event per port-contracts.md
§0.3, but `compaction.py` shipped at #28 with zero consumers, so v0.2.6
finalizes the 1.0.0 surface rather than bumping a consumed contract.

Coupling: Compaction consumes Serialization — `CompactionRequest.payload`
is a `SerializablePayload` (ADR-9.1.2-4 §5: one-way coupling). Compaction
does NOT consume Cost Meter — token counting is internal to the port.

Deprecation policy: see `ports-architecture.md` §6 for `API_VERSION` /
`schema_version` bump rules. No executable deprecation machinery lives at
the port layer.

14 Compaction MAC-Ts are catalogued at `test-strategy.md` §2.2.4
(`M-T-COMP-*` family). That catalog is flagged for re-authoring at Phase
9.4.6-B.2 (the §2.2.4 v0.7 corrigendum supersedes the earlier dual-path
asymmetric-coverage model with a single-adapter coverage model). The 3
error specializations below are no_waiver allow-list candidates deferred
to the Stage 9.9 promotion cycle (test-strategy.md §6.2 / Decision 9.3.2);
zero allow-list entries are authored this cycle. Contract-test authoring
is Phase B.2.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import ClassVar, Literal, Protocol, runtime_checkable

from praxis.ports.common import (
    ContractViolation,
    VerdacaDTOMixin,
)
from praxis.ports.serialization import SerializablePayload

# ---------------------------------------------------------------------------
# DTOs — §3 verbatim (ADR-9.1.2-4 §3; base DTOs substrate-agnostic per the
#         v0.2.4 corrigendum block — unchanged, no additions, no renames)
# ---------------------------------------------------------------------------


class CompactionRequest(VerdacaDTOMixin):
    """Input parameter DTO for `compact` and `estimate`.

    Per `port-contracts.md` v0.2.6 ADR-9.1.2-4 §3. `payload` is a
    `SerializablePayload` — Compaction consumes Serialization (one-way
    coupling per §5). `compaction_strategy` is the caller's requested
    strategy; the adapter MAY downgrade it — a downgrade is signalled by
    `CompactionResult.strategy_applied` differing from this field
    (downgrade-as-return; §3 v0.2.6), never by a raised error.
    """

    payload: SerializablePayload
    token_budget: int                                # contractual maximum tokens in result
    compaction_strategy: Literal["lossless", "lossy_summary", "lossy_eviction"]
    preserve_span_ids: list[str]                      # spans MUST survive compaction


class CompactionResult(VerdacaDTOMixin):
    """Return DTO for `compact`.

    Per `port-contracts.md` v0.2.6 ADR-9.1.2-4 §3. Two Verdaca-owned
    invariants the adapter MUST honor (raising on violation): `tokens_out`
    MUST be <= `request.token_budget` (inclusive bound), and
    `spans_preserved` MUST contain every id in `request.preserve_span_ids`.
    `determinism_hash` makes idempotency falsifiable — two `compact` calls
    with the same `CompactionRequest` MUST yield the same hash; per the §3
    owned-vs-delegated table the caller compares and raises
    `DeterminismViolation` on drift (the adapter does not raise it).
    """

    compacted_payload: SerializablePayload
    tokens_in: int
    tokens_out: int                                   # MUST be <= request.token_budget
    strategy_applied: Literal["lossless", "lossy_summary", "lossy_eviction"]  # downgrade-as-return
    spans_preserved: list[str]                        # MUST contain all request.preserve_span_ids
    spans_evicted: list[str]                          # MUST NOT include any id in
                                                      # request.preserve_span_ids
    determinism_hash: str                             # content-derived idempotency hash —
                                                      # compute_determinism_hash(request);
                                                      # ADR-9.1.2-4 §3 v0.2.6 corrigendum


class CompactionEstimate(VerdacaDTOMixin):
    """Return DTO for `estimate` — a non-binding forecast.

    Per `port-contracts.md` v0.2.6 ADR-9.1.2-4 §3. Unlike `CompactionResult`
    these values carry no invariant guarantee; `confidence` is the adapter's
    self-reported reliability of the forecast.
    """

    estimated_tokens_out: int
    estimated_strategy: Literal["lossless", "lossy_summary", "lossy_eviction"]
    confidence: float


# ---------------------------------------------------------------------------
# Error specializations — 3 classes, all `ContractViolation`. Verbatim per
#   ADR-9.1.2-4 §3 ("most detailed of all 6" ports); the v0.2.6 corrigendum
#   removed `StrategyDowngrade` (downgrade-as-return, F-9.4.6-COMP-DOWNGRADE-
#   CHANNEL). Docstrings substrate-neutral — the ADR §3 error prose carries
#   v0.1-era substrate-named text, governed by the v0.2.4 corrigendum block.
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class TokenBudgetUnreachable(ContractViolation):
    """The compaction adapter cannot reach `token_budget` even with
    `lossy_eviction`.

    Per `port-contracts.md` v0.2.6 ADR-9.1.2-4 §3: indicates the payload
    structurally exceeds the budget — caller fault, not adapter fault.
    """

    requested_budget: int
    minimum_achievable: int


@dataclass(kw_only=True)
class PreservedSpanEvicted(ContractViolation):
    """The compaction adapter evicted a span listed in
    `request.preserve_span_ids`.

    Per `port-contracts.md` v0.2.6 ADR-9.1.2-4 §3: hard violation — the
    only spans that may be evicted are those NOT in `preserve_span_ids`.
    """

    evicted_span_id: str


@dataclass(kw_only=True)
class DeterminismViolation(ContractViolation):
    """Two `compact` calls with the same `CompactionRequest` produced
    different `determinism_hash` values.

    Per `port-contracts.md` v0.2.6 ADR-9.1.2-4 §3: indicates upstream
    non-determinism leaked through the port boundary. Per the §3
    owned-vs-delegated table this is caller-raised — the caller compares
    the hashes of two calls and raises; the adapter does not.
    """

    expected_hash: str
    actual_hash: str


# ---------------------------------------------------------------------------
# Protocol surface — verbatim per ADR-9.1.2-4 §3 (smallest of the six — 2
#   methods)
# ---------------------------------------------------------------------------


@runtime_checkable
class CompactionPort(Protocol):
    """Deterministic compaction with explicit token-budget contracts.

    Per `port-contracts.md` v0.2.6 §4 ADR-9.1.2-4 design intent: the
    smallest port surface of the six (2 methods) with the most detailed
    error taxonomy. The token-budget invariant
    (`tokens_out <= request.token_budget`), the span-preservation
    invariant, and `determinism_hash` construction are Verdaca-owned
    (Protocol guarantees per the §3 owned-vs-delegated table); the
    compaction algorithm and strategy heuristics are adapter-delegated.

    Async / streaming / idempotency profile (ADR-9.1.2-4 §3):
        compact     — sync, NOT streaming, idempotent (same
                      CompactionRequest -> same determinism_hash)
        estimate    — sync, NOT streaming, idempotent

    `@runtime_checkable` decoration follows the 9.4.1 `VersionedStatePort`
    + 9.4.2 `SerializationPort` + 9.4.3 `MemoryPort` + 9.4.4
    `CostMeterPort` + 9.4.5 `LLMProxyPort` precedent. `API_VERSION` is a
    real `ClassVar` data attribute — `@runtime_checkable` Protocol
    conformance is data-attribute-sensitive; full isinstance conformance
    is exercised against the adapter at Phase B.1.
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    def compact(self, request: CompactionRequest) -> CompactionResult: ...

    def estimate(self, request: CompactionRequest) -> CompactionEstimate: ...


# ---------------------------------------------------------------------------
# Determinism-hash constructor — v0.2.6 corrigendum (closes
#   F-9.4.6-COMP-SEED-PHANTOM). The single Verdaca-owned constructor every
#   CompactionPort adapter MUST call to populate
#   `CompactionResult.determinism_hash`. Content-derived — no caller seed.
# ---------------------------------------------------------------------------


def compute_determinism_hash(request: CompactionRequest) -> str:
    """Return the content-derived determinism hash for a `CompactionRequest`.

    sha256 of canonical JSON over:
        payload_digest      — sha256 of the payload's content fields
        token_budget
        compaction_strategy
        preserve_span_ids   — sorted + de-duplicated (set semantics)

    Per ADR-9.1.2-4 §3 (v0.2.6): there is no caller-supplied `seed` —
    `CompactionRequest` has four fields and none is an entropy source. The
    trace-context fields `correlation_id` / `idempotency_key` (inherited from
    `VerdacaDTOMixin`) are excluded — they vary per call, are not content.
    `preserve_span_ids` is a set instruction, so list order and duplicates
    MUST NOT move the hash.

    F-010 discipline (`requirements.md` §6.5): dict keys are sorted before
    hashing; the digest is binary-stable across Python 3.11 / 3.12 (sort_keys
    + fixed separators). Every CompactionPort adapter MUST populate
    `CompactionResult.determinism_hash` via this one function; an adapter
    MUST NOT roll its own (ADR-9.1.2-4 §3 Cleo hand-off). Idempotency holds
    for a fixed adapter + substrate-pin.
    """
    payload_fields = request.payload.model_dump(
        mode="json", exclude={"correlation_id", "idempotency_key"}
    )
    payload_digest = hashlib.sha256(
        json.dumps(payload_fields, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    canonical = {
        "payload_digest": payload_digest,
        "token_budget": request.token_budget,
        "compaction_strategy": request.compaction_strategy,
        "preserve_span_ids": sorted(set(request.preserve_span_ids)),
    }
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


__all__ = [
    "API_VERSION",
    "CompactionEstimate",
    "CompactionPort",
    "CompactionRequest",
    "CompactionResult",
    "DeterminismViolation",
    "PreservedSpanEvicted",
    "TokenBudgetUnreachable",
    "compute_determinism_hash",
]


API_VERSION: str = CompactionPort.API_VERSION
