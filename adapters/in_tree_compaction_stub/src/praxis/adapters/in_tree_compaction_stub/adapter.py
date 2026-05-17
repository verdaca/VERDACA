"""In-tree compaction stub — CompactionPort implementation (Verdaca-authored).

Per ADR-9.1.2-4 §3 Substitute-readiness (`port-contracts.md` v0.2.6): the
G-1 fallback CompactionPort adapter. Greenfield Verdaca-authored Python —
no external upstream, no submodule, no PyPI substrate. Sibling structural
precedent: the Beads in-tree-greenfield adapter (`adapters/beads/`).

Role (Phase B.1 handover §5): a PERMANENT CI fallback, not only the
Decision-2 Option-D degradation path. It lets the B.2 contract suite, CI,
and every downstream consumer run green with no LLMLingua wheel installed,
and it keeps Verdaca shipping if the substrate-truth probe verdict is FAIL.
It runs the SAME B.2 contract suite as the `adapters/llmlingua/` adapter.

Contract (v0.2.6, ratified at engineering-SHA #29 / e98a25b):
    - 3-class error taxonomy — TokenBudgetUnreachable, PreservedSpanEvicted,
      DeterminismViolation (caller-raised). No StrategyDowngrade.
    - A strategy downgrade is downgrade-as-return: a `lossy_summary` request
      (unsupported here) returns a CompactionResult with
      `strategy_applied="lossy_eviction"` — it does NOT raise.
    - `determinism_hash` is computed by the shared Verdaca-owned
      `compute_determinism_hash(request)` imported from
      `praxis.ports.compaction` — this adapter MUST NOT roll its own.

Span model: each top-level key of `SerializablePayload.body` is one span;
the key IS the span id. `preserve_span_ids` references these keys. A
`preserve_span_id` absent from `body` is silently ignored (vacuous
satisfaction) — the stub does not reject it; the W3 LLMLingua adapter
matches this disposition (both run the same B.2 suite).

Token model: no upstream tokenizer. The stub's token unit is one character
of the canonical-JSON serialization of the span set
(`json.dumps(body, sort_keys=True, separators=(",", ":"))`) — a
deterministic, binary-stable stand-in. NOT a real tokenizer; the
`adapters/llmlingua/` adapter counts real tokens. The measure is
self-consistent (it both enforces the budget and reports `tokens_out`).

Strategies:
    lossless       — no span evicted; raises TokenBudgetUnreachable if the
                     payload exceeds the budget.
    lossy_eviction — evicts non-preserved spans (deterministic sorted-id
                     order — no recency signal, so "LRU" degrades to a
                     stable order) until the budget is met.
    lossy_summary  — unsupported; downgraded-as-return to lossy_eviction.

Error posture: the stub raises `TokenBudgetUnreachable` when the budget
cannot be met without evicting a preserved span. It never raises
`PreservedSpanEvicted` — `_evict_to_budget` evicts only non-preserved
spans, so the preserved-span invariant holds correct-by-construction.
`DeterminismViolation` is caller-raised per the §3 owned-vs-delegated table.

Lifecycle (`ports-architecture.md` v0.7 §2.2):
    on_init     — isinstance self-check + a WARNING log making a stub run
                  observable (handover §5).
    on_shutdown — no-op (no upstream connections; no state to flush).

14 Compaction MAC-Ts at `test-strategy.md` §2.2.4 (re-authored at Phase
9.4.6-B.2). Contract-test authoring is B.2 — not this cycle. Zero
`no_waiver` allow-list entries this cycle.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import ClassVar, Literal

from praxis.adapters.in_tree_compaction_stub.version_pin import UPSTREAM_NAME
from praxis.ports.compaction import (
    CompactionEstimate,
    CompactionPort,
    CompactionRequest,
    CompactionResult,
    TokenBudgetUnreachable,
    compute_determinism_hash,
)
from praxis.ports.serialization import JsonValue, SerializablePayload

_PORT_NAME = "compaction"
_logger = logging.getLogger(__name__)

_Strategy = Literal["lossless", "lossy_summary", "lossy_eviction"]


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _count_tokens(body: dict[str, JsonValue]) -> int:
    """Stub token count — characters of the canonical-JSON serialization.

    Deterministic and binary-stable (sort_keys + fixed separators). A
    stand-in for a real tokenizer; see the module docstring.
    """
    return len(json.dumps(body, sort_keys=True, separators=(",", ":")))


def _evict_to_budget(
    body: dict[str, JsonValue],
    preserve: set[str],
    token_budget: int,
) -> tuple[dict[str, JsonValue], list[str]]:
    """Evict non-preserved spans until the budget is met — non-raising core.

    Eviction order is sorted span-id order: the stub has no recency signal,
    so "LRU" degrades to a deterministic, stable order. Returns the kept
    spans and the evicted ids; the kept set MAY still exceed the budget if
    every non-preserved span has been evicted — the caller decides whether
    that is a `TokenBudgetUnreachable` (`compact`) or a forecast
    (`estimate`). This one helper is the single eviction algorithm — both
    `compact` and `estimate` call it so they cannot drift.
    """
    kept = dict(body)
    evicted: list[str] = []
    for span_id in sorted(s for s in body if s not in preserve):
        if _count_tokens(kept) <= token_budget:
            break
        del kept[span_id]
        evicted.append(span_id)
    return kept, evicted


class InTreeCompactionStubAdapter:
    """Verdaca-authored in-tree stub implementing `CompactionPort`.

    Conforms to `praxis.ports.compaction.CompactionPort` (verify via
    `isinstance(adapter, CompactionPort)`; the Protocol is
    `@runtime_checkable`).
    """

    # Mirror the port's API_VERSION ClassVar so @runtime_checkable Protocol
    # conformance succeeds at isinstance() — per the 9.4.1 Beads close-memo
    # §4.1 API_VERSION ClassVar lesson.
    API_VERSION: ClassVar[str] = "1.0.0"

    # Observability marker (handover §5) — a stub run must be distinguishable
    # from a real-substrate run.
    ADAPTER_KIND: ClassVar[str] = "in_tree_compaction_stub"

    # ------------------------------------------------------------------
    # Adapter Lifecycle (per `ports-architecture.md` v0.7 §2.2)
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        """Lifecycle: contract self-check + stub-active observability log.

        In-tree greenfield posture (Beads precedent): no upstream
        healthcheck (no upstream). The WARNING log makes a stub-backed CI
        run observable so it is not mistaken for a real LLMLingua run.
        """
        if not isinstance(self, CompactionPort):
            raise RuntimeError(
                "InTreeCompactionStubAdapter does not conform to CompactionPort"
            )
        _logger.warning(
            "CompactionPort backed by the in-tree STUB adapter "
            "(ADAPTER_KIND=%s) - NOT the real LLMLingua substrate.",
            self.ADAPTER_KIND,
        )

    def on_shutdown(self) -> None:
        """Lifecycle: no-op (no upstream connections; no state to flush)."""

    # ------------------------------------------------------------------
    # CompactionPort surface (2 methods)
    # ------------------------------------------------------------------

    def compact(self, request: CompactionRequest) -> CompactionResult:
        """Compact a payload under the token budget — see module docstring.

        `lossy_summary` is unsupported and downgrades-as-return to
        `lossy_eviction` (v0.2.6) — it does NOT raise. Raises
        `TokenBudgetUnreachable` when the budget cannot be met without
        evicting a preserved span.
        """
        applied = self._resolve_strategy(request.compaction_strategy)
        body = dict(request.payload.body)
        preserve = set(request.preserve_span_ids)

        kept: dict[str, JsonValue]
        evicted: list[str]
        if applied == "lossless":
            kept, evicted = dict(body), []
        else:
            kept, evicted = _evict_to_budget(body, preserve, request.token_budget)

        tokens_out = _count_tokens(kept)
        if tokens_out > request.token_budget:
            raise TokenBudgetUnreachable(
                port_name=_PORT_NAME,
                correlation_id=request.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
                requested_budget=request.token_budget,
                minimum_achievable=tokens_out,
            )

        compacted = SerializablePayload(
            schema_version=request.payload.schema_version,
            correlation_id=request.payload.correlation_id,
            idempotency_key=request.payload.idempotency_key,
            body=kept,
            payload_kind=request.payload.payload_kind,
        )
        return CompactionResult(
            schema_version=request.schema_version,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            compacted_payload=compacted,
            tokens_in=_count_tokens(body),
            tokens_out=tokens_out,
            strategy_applied=applied,
            spans_preserved=[sid for sid in body if sid in kept],
            spans_evicted=evicted,
            determinism_hash=compute_determinism_hash(request),
        )

    def estimate(self, request: CompactionRequest) -> CompactionEstimate:
        """Forecast `compact` — non-binding, never raises.

        The stub is deterministic and cheap, so the forecast is exact
        (`confidence=1.0`). When the budget is unreachable the forecast
        reports the minimum achievable token count rather than raising.
        Shares the one `_evict_to_budget` algorithm with `compact`.
        """
        applied = self._resolve_strategy(request.compaction_strategy)
        body = dict(request.payload.body)
        preserve = set(request.preserve_span_ids)

        if applied == "lossless":
            estimated_out = _count_tokens(body)
        else:
            kept, _ = _evict_to_budget(body, preserve, request.token_budget)
            estimated_out = _count_tokens(kept)

        return CompactionEstimate(
            schema_version=request.schema_version,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            estimated_tokens_out=estimated_out,
            estimated_strategy=applied,
            confidence=1.0,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_strategy(requested: _Strategy) -> _Strategy:
        """Map requested -> applied strategy.

        `lossy_summary` is unsupported by the stub and downgrades to
        `lossy_eviction` (downgrade-as-return, v0.2.6).
        """
        return "lossy_eviction" if requested == "lossy_summary" else requested


__all__ = ["InTreeCompactionStubAdapter"]
