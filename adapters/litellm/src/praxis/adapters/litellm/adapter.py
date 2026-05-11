"""LiteLLM adapter — LLM Proxy port implementation.

Per ADR-9.2-V5 v0.6 (`ports-architecture.md` post-2026-05-11 stacked-
corrigendum): SOLE LLMProxyPort substrate post-H2-falsification
(Q-9.4.5-21). Wraps `litellm` PyPI SDK 1.83.14 behind `LLMProxyPort`.
No dual-adapter pattern; no Docker sidecar; no upstream substrate
retired at Phase A.3 close 2043563 per close-via-rescope disposition.

Authority caveat (Option D-refined per project_verdaca_stage9_4_5):
the spec docs `port-contracts.md` v0.2.3 + `ports-architecture.md` v0.6
live in `_bmad-output/implementation-artifacts/verdaca/stage9/` which
is gitignored. Substance-of-record for ADR-9.1.2-6 §3 + §3.7 DTOs is
commit body of `de365ff` (corrigendum) + `e195fcf` (port-file
convergence); for ADR-9.2-V5 v0.6 substrate disposition is commit body
of `2043563` (H2-falsification corrigendum); local working surface is
secondary. Sectional cites per V8 Approach b discipline.

Substrate composition (per LiteLLM API surface probes 2026-05-11):
    call           — `litellm.completion(model, messages, max_tokens,
                     temperature, api_key, ...)` returns
                     `litellm.types.utils.ModelResponse`. Marshals
                     LLMRequest fields through; strips upstream
                     cost-adjacent fields via DS-1 prefix-match before
                     constructing LLMResponse.
    stream         — `litellm.completion(stream=True,
                     stream_options={"include_usage": True})` returns
                     iterator of `ModelResponseStream` chunks. Maps each
                     chunk to LLMStreamChunk with chunk_index tracking;
                     final chunk (where choices[0].finish_reason is not
                     None) carries final_input_tokens/final_output_tokens
                     from chunk.usage.
    supported_providers — enumerates `litellm.models_by_provider` keys
                     (88 providers; DS-2 Option α per advisor H#2
                     override of H#1 DS-2 GO=133; capability-grounded
                     vs declarative-enum-surface). For each provider,
                     sorted model set -> tuple[str, ...];
                     streaming_supported derived via
                     `litellm.get_supported_openai_params(first_model,
                     custom_llm_provider=provider)` membership of
                     "stream".

Cost-strip 3-layer defense-in-depth (Q-9.4.5-6 + §3.6 cost-meter
ownership ADR substance + ADR-9.2-V5 v0.6 §3 bullet 3):
    Layer 1 (construction-time): VerdacaDTOMixin extra="forbid" rejects
            any cost_usd kwarg at LLMResponse() construction (verified
            at Phase A.2 H#3 watch D — `LLMResponse(cost_usd=99.0)`
            raises ValidationError).
    Layer 2 (port-boundary): LLMProxyPort runtime guard via
            `CostFieldLeakage` ContractViolation — inherited from
            `ports/llm_proxy.py` post-e195fcf.
    Layer 3 (adapter-layer; THIS MODULE): DS-1 prefix-match strip of
            cost_*/usd_*/price_* keys from `response.usage.model_dump()`
            BEFORE LLMResponse construction. Defensive; LiteLLM v1.83.14
            does NOT auto-attach cost (J-B1-1 finding 2026-05-11:
            `litellm.completion_cost` is a SEPARATE helper, NOT auto-
            attached to response.usage) — but caller-registered callbacks
            (litellm.callbacks) CAN attach. Adapter strip is defense-in-
            depth, regardless of LiteLLM's default behavior.
    Adapter MUST NOT call `litellm.completion_cost()` — that violates
    §3.6 (Pi-Mono is sole cost computer).

Idempotency profile (per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3):
    call          — sync, idempotent (idempotency_key required;
                    in-process dict cache per DS-4). Duplicate key
                    returns cached LLMResponse.
    stream        — sync (returns iterator), idempotent
                    (idempotency_key required), BUT no caching per DS-5
                    strict-β disposition: spec M-T-LLM-IDEMPOTENT-01
                    tests call() only; stream-idempotency is
                    semantically-fragile (cached aggregate vs network-
                    paced delta replay); deferred to v1.1.0 minor bump
                    if Stage 10+ MAC-T demands it.
    supported_providers — sync, idempotent, read-only.

OTEL span discipline: LLM-Proxy port does NOT mint canonical 5-attr
spans (unlike Memory port's PS-3 promote span). Adapter MAY emit
adapter-private spans for observability but they are NOT contract-
specified. v0.1.0 ships NO span emission (defer to v0.2.0 / Stage 10+).

Error specializations (per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3):
    CompressionContractViolation — compression_hint="none" violated
                                 (LiteLLM v1.83.14 does NOT auto-
                                 compress; v0.1.0 implements as no-op
                                 check; raises only on observed
                                 compression — Stage 10+ may add
                                 detection heuristics).
    CostFieldLeakage           — Adapter strip miss; raised at
                                 construction-time via extra="forbid"
                                 (Layer 1). Adapter MUST NOT construct
                                 LLMResponse with cost-adjacent kwarg.
    ContractViolation          — finish_reason unmapped (DS-3); other
                                 invariant violations.

DS rulings applied:
    DS-1 cost-strip: prefix-match cost_*/usd_*/price_* on
                     response.usage.model_dump()
    DS-2 ProviderInfo cardinality: 88 (models_by_provider) per advisor
                     H#2 override of H#1 DS-2 GO=133 (per executor
                     finding J-B1-2 substrate-truth probe; capability-
                     grounded wins over declarative-enum surface)
    DS-3 finish_reason: tool_calls -> tool_use; function_call ->
                     tool_use; unmapped raises ContractViolation
    DS-4 idempotency cache: in-process dict only (no rehydrate)
    DS-5 stream idempotency: STRICT-β (advisor override per H#2) —
                     NO caching for stream(); pass-through to LiteLLM

10 binding MAC-Ts at `test-strategy.md` §2.2.6 post-A-8 (7 active —
3 §2.2.6 retirements at A-8 per H2-falsification + LiteLLM-specific
preservation):
    M-T-LLM-CALL-LITELLM-01, M-T-LLM-STREAM-LITELLM-01,
    M-T-LLM-COMPRESS-01 (deferred to 9.9), M-T-LLM-COSTLEAK-01
    (deferred to 9.9), M-T-LLM-PROVIDERS-01, M-T-LLM-PROVIDERS-02,
    M-T-LLM-IDEMPOTENT-01. LLM-Proxy has ZERO no_waiver allow-list
    entries (advisor §3.1).

Deprecation policy: see `ports-architecture.md` v0.6 §6 for
`API_VERSION` / `schema_version` bump rules.
"""

from __future__ import annotations

import importlib.metadata
import uuid
from collections.abc import Iterator, Sequence
from datetime import datetime, timezone
from typing import Any, ClassVar

import litellm

from praxis.adapters.litellm.version_pin import UPSTREAM_NAME
from praxis.ports.common import ContractViolation
from praxis.ports.llm_proxy import (
    CompressionContractViolation,
    LLMProxyPort,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    ProviderInfo,
)

_PORT_NAME = "llm_proxy"

# DS-1: cost-strip prefix-match per §3.6 cost-meter ownership ADR substance
# (mirrors port-boundary CostFieldLeakage prefix-check semantics in
# `ports/llm_proxy.py` post-e195fcf).
_COST_FIELD_PREFIXES = ("cost_", "usd_", "price_")

# DS-3: finish_reason mapping (LiteLLM OpenAI-style strings -> LLMResponse
# Literal["stop", "length", "content_filter", "tool_use"]).
_FINISH_REASON_MAP: dict[str, str] = {
    "stop": "stop",
    "length": "length",
    "content_filter": "content_filter",
    "tool_calls": "tool_use",
    "function_call": "tool_use",  # LiteLLM legacy OpenAI compat
}


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _strip_cost_fields(usage_dict: dict[str, Any]) -> dict[str, Any]:
    """DS-1 cost-strip: remove cost_*/usd_*/price_* keys.

    Per §3.6 cost-meter ownership ADR substance + ADR-9.2-V5 v0.6 §3
    bullet 3 + Q-9.4.5-6. Mirrors port-boundary prefix-check semantics
    in `ports/llm_proxy.py` post-e195fcf. Defense-in-depth Layer 3 of 3.
    """
    return {
        k: v for k, v in usage_dict.items()
        if not any(k.startswith(p) for p in _COST_FIELD_PREFIXES)
    }


def _map_finish_reason(
    litellm_value: str | None,
    *,
    correlation_id: str,
) -> str:
    """DS-3 finish_reason mapping. Raises ContractViolation on unmapped.

    LiteLLM emits OpenAI-style: stop / length / content_filter /
    tool_calls / function_call. Maps to LLMResponse Literal:
    stop / length / content_filter / tool_use. Unmapped values raise
    ContractViolation to catch future LiteLLM drift.
    """
    if litellm_value is None:
        raise ContractViolation(
            port_name=_PORT_NAME,
            correlation_id=correlation_id,
            occurred_at=_utc_now(),
            upstream_name=UPSTREAM_NAME,
            violation_class="invariant",
        )
    mapped = _FINISH_REASON_MAP.get(litellm_value)
    if mapped is None:
        raise ContractViolation(
            port_name=_PORT_NAME,
            correlation_id=correlation_id,
            occurred_at=_utc_now(),
            upstream_name=UPSTREAM_NAME,
            violation_class="value",
        )
    return mapped


def _litellm_version() -> str:
    """Retrieve LiteLLM version via importlib.metadata.

    Per executor probe 2026-05-11: `litellm.__version__` attribute is
    gone in 1.83.14 (raises AttributeError via module __getattr__).
    `importlib.metadata.version("litellm")` is the canonical retrieval.
    """
    return importlib.metadata.version("litellm")


class LiteLLMAdapter:
    """In-tree PyPI-pinned wrap of `litellm` SDK against `LLMProxyPort`.

    Conforms to `praxis.ports.llm_proxy.LLMProxyPort` (verify via
    `isinstance(adapter, LLMProxyPort)`; the Protocol is `@runtime_checkable`).
    Sole LLMProxyPort substrate post-H2-falsification per ADR-9.2-V5
    v0.6 (Q-9.4.5-21).
    """

    # Mirror the port's API_VERSION ClassVar so runtime_checkable Protocol
    # conformance succeeds at isinstance() — Protocol declares the
    # attribute, isinstance checks the candidate has it. Per 9.4.1
    # API_VERSION ClassVar bug lesson (executor playbook §9.C addendum;
    # B.1 precedent at adapters/mem0/.../adapter.py:221 = 34a4eca).
    API_VERSION: ClassVar[str] = "1.0.0"

    def __init__(
        self,
        *,
        api_keys: dict[str, str] | None = None,
        default_correlation_id: str | None = None,
    ) -> None:
        """Construct an adapter.

        `api_keys` is the per-provider API key map per advisor H#1 auth-
        pattern approval. Optional — caller MAY pass {} (or None) and
        rely on env-var-first behavior of LiteLLM (OPENAI_API_KEY,
        ANTHROPIC_API_KEY, etc.). When passed, individual provider keys
        are threaded to `litellm.completion(api_key=...)` per call.

        `default_correlation_id` per Mem0 (34a4eca) / Letta (b14285b) /
        Pi-Mono (325820a) sibling precedent.

        DS-4: in-process idempotency cache for call() only. DS-5 strict-
        β: stream() has NO caching.
        """
        self._api_keys = dict(api_keys or {})
        self._default_correlation_id = default_correlation_id or uuid.uuid4().hex
        # DS-4 idempotency cache; call()-only per DS-5 strict-β.
        self._idempotency_cache: dict[str, LLMResponse] = {}

    # ------------------------------------------------------------------
    # Adapter Lifecycle (per `ports-architecture.md` v0.6 §2.2)
    # ------------------------------------------------------------------

    def on_init(self) -> None:
        """Lifecycle: contract self-check ONLY.

        LiteLLM is in-process Python library; no upstream-liveness probe
        needed (mirrors Pi-Mono in-tree-native pattern at
        adapters/pi_mono_native/.../adapter.py:182-193 = 325820a). No
        AP-5 reconciliation (DS-4 in-process-only cache).
        """
        if not isinstance(self, LLMProxyPort):
            raise RuntimeError("LiteLLMAdapter does not conform to LLMProxyPort")

    def on_shutdown(self) -> None:
        """Lifecycle: no-op.

        LiteLLM is in-process; no upstream connections to close. Mirrors
        Pi-Mono in-tree-native pattern.
        """

    # ------------------------------------------------------------------
    # LLMProxyPort surface (3 methods)
    # ------------------------------------------------------------------

    def call(self, request: LLMRequest) -> LLMResponse:
        """Per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3 call() spec.

        DS-4 idempotency cache lookup first; cache hit short-circuits.
        DS-1 cost-strip + DS-3 finish_reason map applied before LLMResponse
        construction. Compression-detection (DS no-op for v0.1.0) per
        Q-9.4.5-6 + CompressionContractViolation.
        """
        # 1. DS-4 idempotency cache lookup.
        if request.idempotency_key is not None:
            cached = self._idempotency_cache.get(request.idempotency_key)
            if cached is not None:
                return cached

        # 2. Invoke litellm.completion(). model arg combines provider+model
        # per LiteLLM convention (e.g., "anthropic/claude-opus-4-7").
        messages_payload = [
            {"role": m.role, "content": m.content} for m in request.messages
        ]
        litellm_response = litellm.completion(
            model=f"{request.provider}/{request.model}",
            messages=messages_payload,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            api_key=self._api_keys.get(request.provider),
        )

        # 3. Compression detection (v0.1.0 no-op per scope restriction;
        # LiteLLM v1.83.14 does not auto-compress).
        if request.compression_hint == "none" and self._detect_compression(
            request, litellm_response
        ):
            raise CompressionContractViolation(
                port_name=_PORT_NAME,
                correlation_id=request.correlation_id,
                occurred_at=_utc_now(),
                upstream_name=UPSTREAM_NAME,
                violation_class="invariant",
                hint_was="none",
                compressed_anyway=True,
            )

        # 4. DS-1 cost-strip — defense-in-depth Layer 3.
        usage_dict: dict[str, Any] = (
            litellm_response.usage.model_dump()
            if litellm_response.usage is not None
            else {}
        )
        usage_dict = _strip_cost_fields(usage_dict)

        # 5. DS-3 finish_reason map.
        finish_reason = _map_finish_reason(
            litellm_response.choices[0].finish_reason,
            correlation_id=request.correlation_id,
        )

        # 6. Construct LLMResponse — VerdacaDTOMixin extra="forbid" is
        # Layer 1 of cost-strip defense-in-depth (rejects any cost_*
        # kwarg at construction-time).
        response = LLMResponse(
            schema_version=request.schema_version,
            correlation_id=request.correlation_id,
            idempotency_key=request.idempotency_key,
            content=litellm_response.choices[0].message.content or "",
            finish_reason=finish_reason,  # type: ignore[arg-type]
            input_tokens=usage_dict.get("prompt_tokens", 0),
            output_tokens=usage_dict.get("completion_tokens", 0),
            raw_response_id=litellm_response.id,
        )

        # 7. DS-4 cache store.
        if request.idempotency_key is not None:
            self._idempotency_cache[request.idempotency_key] = response

        return response

    def stream(self, request: LLMRequest) -> Iterator[LLMStreamChunk]:
        """Per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3 stream() spec.

        DS-5 strict-β: NO idempotency cache; pass-through to LiteLLM.
        DS-1 cost-strip applied per chunk usage (final chunk only).
        stream_options={"include_usage": True} ensures final-chunk usage
        delivery per LiteLLM streaming semantics.
        """
        messages_payload = [
            {"role": m.role, "content": m.content} for m in request.messages
        ]
        chunk_iter = litellm.completion(
            model=f"{request.provider}/{request.model}",
            messages=messages_payload,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=True,
            stream_options={"include_usage": True},
            api_key=self._api_keys.get(request.provider),
        )

        chunk_index = 0
        for chunk in chunk_iter:
            # Final-chunk detection.
            has_choices = bool(chunk.choices)
            is_final = (
                has_choices
                and chunk.choices[0].finish_reason is not None
            )

            # DS-1 cost-strip on chunk usage (final chunk only carries it).
            final_input_tokens: int | None = None
            final_output_tokens: int | None = None
            if is_final and chunk.usage is not None:
                usage_dict = _strip_cost_fields(chunk.usage.model_dump())
                final_input_tokens = usage_dict.get("prompt_tokens", 0)
                final_output_tokens = usage_dict.get("completion_tokens", 0)

            delta_content = ""
            if has_choices and chunk.choices[0].delta is not None:
                delta_content = chunk.choices[0].delta.content or ""

            yield LLMStreamChunk(
                schema_version=request.schema_version,
                correlation_id=request.correlation_id,
                idempotency_key=request.idempotency_key,
                delta=delta_content,
                chunk_index=chunk_index,
                is_final=is_final,
                final_input_tokens=final_input_tokens,
                final_output_tokens=final_output_tokens,
            )
            chunk_index += 1

    def supported_providers(self) -> Sequence[ProviderInfo]:
        """Per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3 supported_providers()
        + §3.7 ProviderInfo shape (Q-9.4.5-13).

        DS-2 advisor H#2 override of H#1 DS-2 GO=133 per executor finding
        J-B1-2: enumerates `litellm.models_by_provider` keys (88
        providers; capability-grounded vs declarative-enum-surface).
        For each provider:
          - name: provider key from models_by_provider
          - version: importlib.metadata.version("litellm") (per probe note:
            litellm.__version__ attribute gone in 1.83.14)
          - model_catalog: tuple(sorted(models_by_provider[provider])) per
            Q-9.4.5-13 immutability
          - streaming_supported: derived via
            litellm.get_supported_openai_params(first_model,
            custom_llm_provider=provider) membership of "stream"
        """
        version = _litellm_version()
        providers: list[ProviderInfo] = []
        for provider_name, models_set in sorted(litellm.models_by_provider.items()):
            sorted_models = tuple(sorted(models_set))
            streaming = False
            if sorted_models:
                try:
                    params = litellm.get_supported_openai_params(
                        model=sorted_models[0],
                        custom_llm_provider=provider_name,
                    )
                    streaming = "stream" in (params or [])
                except Exception:  # noqa: BLE001
                    # Conservative: unknown -> assume no streaming support.
                    streaming = False
            providers.append(
                ProviderInfo(
                    schema_version=1,
                    correlation_id=self._default_correlation_id,
                    name=provider_name,
                    version=version,
                    model_catalog=sorted_models,
                    streaming_supported=streaming,
                )
            )
        return tuple(providers)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_compression(
        self,
        request: LLMRequest,
        response: Any,
    ) -> bool:
        """Compression detection per Q-9.4.5-6 + CompressionContractViolation.

        v0.1.0 scope: no-op (always False). LiteLLM v1.83.14 does NOT
        auto-compress responses; compression would require caller-
        configured litellm.callbacks. Detection heuristics (e.g.,
        response.content length << expected for prompt) are fragile and
        deferred to v0.2.0 / Stage 10+. M-T-LLM-COMPRESS-01 is deferred
        to 9.9 promotion cycle (test-strategy.md §2.2.6); v0.1.0
        compression-detection no-op is acceptable.
        """
        return False


__all__ = ["LiteLLMAdapter"]
