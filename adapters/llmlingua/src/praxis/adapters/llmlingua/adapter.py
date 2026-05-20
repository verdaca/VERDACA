"""LLMLingua adapter — CompactionPort implementation (PyPI-pinned).

Per ADR-9.1.2-4 §3 (`port-contracts.md` v0.2.6, the v0.2.4 substrate
re-anchor): the primary CompactionPort adapter — wraps the `llmlingua`
PyPI SDK (microsoft/LLMLingua, `llmlingua==0.2.2`, MIT) behind
`CompactionPort`. `adapters/llmlingua/` supersedes the v0.1-era
`adapters/forge/` (F-9.4.6-FORGE-SEMANTIC-MISFIT). Sibling structural
precedent: the LiteLLM PyPI-library adapter (`adapters/litellm/`, 9f6a010).

Substrate-truth probe (`docs/stage-9.4.6-b.1-substrate-truth-probe.md`,
W1-H#1, verdict PASS-DEGRADED): LLMLingua's `compress_prompt(target_token=)`
is a soft target, not an inclusive ceiling — this adapter emulates the hard
`tokens_out <= token_budget` bound (OD-5). LLMLingua exposes no caller-facing
seed and pins its RNG (`seed_everything(42)`) — deterministic by
construction; the empirical twice-run is a B.2 contract test.

Contract (v0.2.6, ratified at engineering-SHA #29 / e98a25b):
    - 3-class error taxonomy — TokenBudgetUnreachable, PreservedSpanEvicted,
      DeterminismViolation (caller-raised). No StrategyDowngrade.
    - A downgrade is downgrade-as-return (`strategy_applied` differs from
      the request) — it does NOT raise.
    - `determinism_hash` via the shared `compute_determinism_hash(request)`
      imported from `praxis.ports.compaction` — never rolled here (W1 OD-2).

Span model: each top-level key of `SerializablePayload.body` is one span;
the key IS the span id. Preserved spans (`preserve_span_ids` intersect the
body keys) bypass LLMLingua entirely and are kept verbatim — the
preservation invariant holds exact-by-construction. A `preserve_span_id`
absent from `body` is silently ignored (vacuous satisfaction — matches the
in-tree stub adapter; both run the same B.2 suite). Only non-preserved
spans are sent to `compress_prompt`.

Strategy mapping (cross-adapter-coherent with the in-tree stub):
    lossless       — no compression; pass-through. TokenBudgetUnreachable
                     if the payload exceeds the budget.
    lossy_summary  — LLMLingua compression — this adapter's native mode.
    lossy_eviction — LLMLingua has no span-eviction primitive; downgraded-
                     as-return to lossy_summary (compression). Never raises.

OD-5 hard-budget emulation: after `compress_prompt`, the adapter counts the
result (`get_token_length`); if over budget it re-compresses at a tighter
`target_token` (<= `_MAX_RECOMPRESS` iterations); the final guard raises
`TokenBudgetUnreachable` if still over.

Lifecycle (`ports-architecture.md` v0.7 §2.2):
    on_init     — isinstance self-check. The `PromptCompressor` (and its
                  model) loads lazily on first compact/estimate, not here.
    on_shutdown — no-op (in-process; the compressor is GC'd).

14 Compaction MAC-Ts at `test-strategy.md` §2.2.4 (re-authored at Phase
9.4.6-B.2). Contract-test authoring is B.2 — not this cycle. Zero
`no_waiver` allow-list entries this cycle.

B.2-verified empirical assumptions: (a) `compress_prompt` dispatches to
llmlingua2 mode for a `use_llmlingua2=True` compressor; (b)
`compressed_prompt_list` is positionally aligned to the input `context`.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, ClassVar, Literal

from llmlingua import PromptCompressor
from praxis.adapters.llmlingua.version_pin import UPSTREAM_NAME
from praxis.ports.common import ContractViolation
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
_DEFAULT_MODEL = "microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank"
_MAX_RECOMPRESS = 3

_Strategy = Literal["lossless", "lossy_summary", "lossy_eviction"]


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _span_text(value: JsonValue) -> str:
    """Render a span value as text for LLMLingua.

    A string span is passed through; any other JsonValue is canonical-JSON
    serialized (deterministic — sort_keys + fixed separators).
    """
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _count_tokens(compressor: PromptCompressor, spans: dict[str, JsonValue]) -> int:
    """Total LLMLingua token length across every span's text rendering."""
    return sum(compressor.get_token_length(_span_text(v)) for v in spans.values())


class LLMLinguaAdapter:
    """PyPI-pinned wrap of `llmlingua` against `CompactionPort`.

    Conforms to `praxis.ports.compaction.CompactionPort` (verify via
    `isinstance(adapter, CompactionPort)`; the Protocol is
    `@runtime_checkable`).
    """

    # Mirror the port's API_VERSION ClassVar so @runtime_checkable Protocol
    # conformance succeeds at isinstance() — per the 9.4.1 API_VERSION
    # ClassVar lesson (LiteLLM precedent, adapter.py:232 / 9f6a010).
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(
        self,
        *,
        model_name: str = _DEFAULT_MODEL,
        device_map: str = "cpu",
        use_llmlingua2: bool = True,
        default_correlation_id: str | None = None,
    ) -> None:
        """Construct an adapter — config only; the model loads lazily.

        `model_name` / `device_map` / `use_llmlingua2` are threaded to
        `PromptCompressor` on first use. The default is the LLMLingua-2
        bert-base model (ungated, CPU, deterministic-by-construction);
        callers (and the B.2 environment) may override.
        """
        self._model_name = model_name
        self._device_map = device_map
        self._use_llmlingua2 = use_llmlingua2
        self._default_correlation_id = default_correlation_id or uuid.uuid4().hex
        self._compressor: PromptCompressor | None = None

    # ------------------------------------------------------------------
    # Adapter Lifecycle (per `ports-architecture.md` v0.7 §2.2)
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        """Lifecycle: contract self-check only.

        The `PromptCompressor` (and its model weights) loads lazily on the
        first `compact` / `estimate` — not here — so `on_init` stays cheap.
        """
        if not isinstance(self, CompactionPort):
            raise RuntimeError("LLMLinguaAdapter does not conform to CompactionPort")

    def on_shutdown(self) -> None:
        """Lifecycle: no-op (in-process; the compressor is GC'd)."""

    # ------------------------------------------------------------------
    # CompactionPort surface (2 methods)
    # ------------------------------------------------------------------

    def compact(self, request: CompactionRequest) -> CompactionResult:
        """Compact a payload under the token budget — see module docstring.

        `lossy_eviction` is unsupported natively and downgrades-as-return to
        `lossy_summary` (v0.2.6) — it does NOT raise. Raises
        `TokenBudgetUnreachable` when the budget cannot be met.
        """
        applied = self._resolve_strategy(request.compaction_strategy)
        body = dict(request.payload.body)
        preserve = set(request.preserve_span_ids)
        compressor = self._get_compressor()

        kept: dict[str, JsonValue]
        evicted: list[str]
        if applied == "lossless":
            kept, evicted = dict(body), []
        else:
            kept, evicted = self._compress(
                compressor, body, preserve, request.token_budget,
                request.correlation_id,
            )

        tokens_out = _count_tokens(compressor, kept)
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
            tokens_in=_count_tokens(compressor, body),
            tokens_out=tokens_out,
            strategy_applied=applied,
            spans_preserved=[sid for sid in body if sid in kept],
            spans_evicted=evicted,
            determinism_hash=compute_determinism_hash(request),
        )

    def estimate(self, request: CompactionRequest) -> CompactionEstimate:
        """Forecast `compact` — non-binding, never raises, never compresses.

        `lossless` -> the exact token count (confidence 1.0). A lossy
        strategy -> the budget (LLMLingua targets it; confidence 0.8).
        """
        applied = self._resolve_strategy(request.compaction_strategy)
        body = dict(request.payload.body)
        compressor = self._get_compressor()
        tokens_in = _count_tokens(compressor, body)

        if applied == "lossless":
            estimated_out = tokens_in
            confidence = 1.0
        else:
            estimated_out = min(request.token_budget, tokens_in)
            confidence = 0.8

        return CompactionEstimate(
            schema_version=request.schema_version,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            estimated_tokens_out=estimated_out,
            estimated_strategy=applied,
            confidence=confidence,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_strategy(requested: _Strategy) -> _Strategy:
        """Map requested -> applied strategy.

        `lossy_eviction` is unsupported natively (LLMLingua has no
        span-eviction primitive) and downgrades to `lossy_summary`
        (downgrade-as-return, v0.2.6).
        """
        return "lossy_summary" if requested == "lossy_eviction" else requested

    def _get_compressor(self) -> PromptCompressor:
        """Lazily construct and cache the `PromptCompressor`.

        The model weights load here, on first use — not at `__init__` or
        `on_init`.
        """
        if self._compressor is None:
            self._compressor = PromptCompressor(
                model_name=self._model_name,
                device_map=self._device_map,
                use_llmlingua2=self._use_llmlingua2,
            )
        return self._compressor

    def _compress(
        self,
        compressor: PromptCompressor,
        body: dict[str, JsonValue],
        preserve: set[str],
        token_budget: int,
        correlation_id: str,
    ) -> tuple[dict[str, JsonValue], list[str]]:
        """Compress non-preserved spans under the budget (OD-5 emulation).

        Preserved spans bypass LLMLingua and are kept verbatim. Non-preserved
        spans go to `compress_prompt` as a `context` list; the result is
        re-compressed at a tighter `target_token` (<= `_MAX_RECOMPRESS`
        iterations) while it overshoots the budget. The kept set MAY still
        exceed the budget after the cap — the caller's final guard raises
        `TokenBudgetUnreachable`.
        """
        kept_verbatim = {k: body[k] for k in body if k in preserve}
        non_preserved = [k for k in body if k not in preserve]
        if not non_preserved:
            return kept_verbatim, []

        context = [_span_text(body[k]) for k in non_preserved]
        preserved_tokens = _count_tokens(compressor, kept_verbatim)
        target = max(1, token_budget - preserved_tokens)

        trial: dict[str, JsonValue] = dict(kept_verbatim)
        evicted: list[str] = []
        for _ in range(_MAX_RECOMPRESS):
            result: dict[str, Any] = compressor.compress_prompt(
                context=context, target_token=target
            )
            compressed = result.get("compressed_prompt_list")
            if not isinstance(compressed, list) or len(compressed) != len(non_preserved):
                raise ContractViolation(
                    port_name=_PORT_NAME,
                    correlation_id=correlation_id,
                    occurred_at=_utc_now(),
                    upstream_name=UPSTREAM_NAME,
                    violation_class="invariant",
                )
            trial = dict(kept_verbatim)
            evicted = []
            for key, comp in zip(non_preserved, compressed, strict=True):
                text = str(comp or "").strip()
                if text:
                    trial[key] = text
                else:
                    evicted.append(key)
            total = _count_tokens(compressor, trial)
            if total <= token_budget:
                return trial, evicted
            target = max(1, target - (total - token_budget))

        return trial, evicted


__all__ = ["LLMLinguaAdapter"]
