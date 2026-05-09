"""LLM Proxy Port — Protocol + DTOs + error specializations.

Substance source: `port-contracts.md` v0.2.3 §6 / ADR-9.1.2-6.
Vendor strategy: `ports-architecture.md` §3 ADR-9.2-V5 (RTK Docker
sidecar + LiteLLM PyPI substitute-conformance per Stage 9.2
ratification).

This module introduces zero new contract substance. Pure Python, no
upstream imports.

API_VERSION = "1.0.0" (initial version; first stable contract surface).

§3.7 pinned DTOs (`Message`, `ProviderInfo`) are pinned per the Phase
A.1 corrigendum at SHA `de365ff`; the A.1 commit body is the
authoritative substance-of-record per the
`_bmad-output/implementation-artifacts/` gitignore caveat at
.gitignore:30. `Message` lives in `praxis.ports.common` (chat-API-
shaped, multi-port-relevant per A.1-WINSTON-1); `ProviderInfo` lives
here (LLM-Proxy-scoped capability descriptor — proxy-owned per §3.6
cost-meter ownership ADR substance + cross-port schema-overlap
invariant per A.1-WINSTON-2).

Cost-meter ownership ADR substance (port-contracts.md v0.2.3 §3.6):
    LLM Proxy port returns tokens, NEVER USD. Cost flow:
    LLMResponse.input_tokens, output_tokens -> caller invokes
    CostMeterPort.record(CostEvent(...)) -> Cost Meter computes USD.
    RTK + LiteLLM adapters' internal cost numbers are discarded.
    `CostFieldLeakage` ContractViolation enforces this: any field
    starting with cost_/usd_/price_ on LLMResponse subclasses raises
    PR failure. Single source of truth = Cost Meter port. Period.

Deprecation policy: see `ports-architecture.md` §6 for `API_VERSION` /
`schema_version` bump rules. No executable deprecation machinery lives
at the port layer.

10 binding MAC-Ts at `test-strategy.md` §2.2.6 (Murat §2.2.6):
    M-T-LLM-CALL-RTK-01, M-T-LLM-CALL-LITELLM-01,
    M-T-LLM-STREAM-RTK-01, M-T-LLM-STREAM-LITELLM-01,
    M-T-LLM-COMPRESS-01 (deferred to 9.9 promotion cycle),
    M-T-LLM-COSTLEAK-01 (deferred to 9.9 promotion cycle),
    M-T-LLM-PROVIDERS-01, M-T-LLM-PROVIDERS-02,
    M-T-LLM-IDEMPOTENT-01, M-T-LLM-COST-STRIP-01.
LLM-Proxy has ZERO no_waiver allow-list entries per advisor §3.1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Iterator, Literal, Protocol, Sequence, runtime_checkable

from praxis.ports.common import (
    ContractViolation,
    Message,
    VerdacaDTOMixin,
)


# ---------------------------------------------------------------------------
# DTOs — pinned per ADR-9.1.2-6 §3 (port-contracts.md v0.2.3)
#   §3 base DTOs (3): LLMRequest, LLMResponse, LLMStreamChunk
#   §3.7 corrigendum DTO (1 new at v0.2.3): ProviderInfo
#   (§3.7 corrigendum DTO `Message` lives in praxis.ports.common per
#    A.1-WINSTON-1; imported above)
# ---------------------------------------------------------------------------


class LLMRequest(VerdacaDTOMixin):
    """LLM call/stream input parameter DTO.

    Per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3. `messages` carries
    the chat-API-shaped Message sequence (Message DTO hosted in
    `praxis.ports.common` per A.1-WINSTON-1). `compression_hint`
    Literal gates adapter-side compression: "none" forbids it (raises
    `CompressionContractViolation` if adapter compresses anyway);
    "compress_if_safe" permits adapter discretion.
    """

    provider: str
    model: str
    messages: list[Message]
    max_tokens: int
    temperature: float
    compression_hint: Literal["none", "compress_if_safe"]


class LLMResponse(VerdacaDTOMixin):
    """LLM call return DTO.

    Per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3. NO `cost_usd` field
    — cost is computed by Cost Meter port from `input_tokens` +
    `output_tokens`. `CostFieldLeakage` ContractViolation enforces
    this at port boundary (per §3.6 cost-meter ownership ADR
    substance). `finish_reason` Literal enforces the four valid
    completion states.
    """

    content: str
    finish_reason: Literal["stop", "length", "content_filter", "tool_use"]
    input_tokens: int
    output_tokens: int
    raw_response_id: str


class LLMStreamChunk(VerdacaDTOMixin):
    """LLM stream() iterator yield DTO.

    Per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3. `is_final` flags
    the terminal chunk; `final_input_tokens` + `final_output_tokens`
    are set ONLY on the terminal chunk (None for intermediate
    chunks) — caller closes the cost-meter loop on terminal-chunk
    receipt.
    """

    delta: str
    chunk_index: int
    is_final: bool
    final_input_tokens: int | None
    final_output_tokens: int | None


class ProviderInfo(VerdacaDTOMixin):
    """LLM-Proxy capability descriptor — per-provider catalog + streaming
    support.

    Per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3.7 corrigendum at SHA
    `de365ff`.
    """

    name: str                                # source-pin §3 method-sig: supported_providers()
                                             # returns Sequence[ProviderInfo]; cross-port
                                             # sibling: BudgetScope.scope_id str-label shape
    version: str                             # source-pin test-strategy.md §2.2.6
                                             # M-T-LLM-PROVIDERS-02 trigger: "adapter-current
                                             # vs adapter-current-1" version comparison;
                                             # cross-port sibling: API_VERSION/schema_version
                                             # pattern from common.py §0
    model_catalog: tuple[str, ...]           # source-pin A.1-MURAT-2: load-bearing for
                                             # M-T-LLM-PROVIDERS-02 set-equality assertion;
                                             # immutable tuple per Pydantic frozen=True idiom;
                                             # gates dual-adapter substitute-conformance H2
                                             # at 9.9
    streaming_supported: bool                # source-pin A.1-MURAT-2: gates M-T-LLM-STREAM-*
                                             # skip-logic per matrix tier; without it,
                                             # adapter-version drift in stream support silently
                                             # degrades H2 parity measurement


# ---------------------------------------------------------------------------
# Error specializations — verbatim per ADR-9.1.2-6 §3
# ---------------------------------------------------------------------------


@dataclass(kw_only=True)
class CompressionContractViolation(ContractViolation):
    """Adapter compressed payload despite compression_hint='none',
    OR returned content the request didn't request (echo bug).

    Per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3. Bound by
    M-T-LLM-COMPRESS-01 (test-strategy.md §2.2.6; deferred to 9.9
    promotion cycle per ruling B). LLM-Proxy has zero no_waiver
    allow-list entries (advisor §3.1); contract-test enforcement is
    gate-only.
    """

    hint_was: str
    compressed_anyway: bool


@dataclass(kw_only=True)
class CostFieldLeakage(ContractViolation):
    """Adapter included a cost field on LLMResponse. Hard violation —
    cost is NEVER computed by the LLM Proxy port.

    Per `port-contracts.md` v0.2.3 ADR-9.1.2-6 §3. Bound by
    M-T-LLM-COSTLEAK-01 (test-strategy.md §2.2.6; deferred to 9.9
    promotion cycle per ruling B; Cleo grep-rule enforces at supply-
    chain hygiene regardless of allow-list status). Port-boundary
    runtime guard per Q-9.4.5-6: any field starting with cost_/usd_/
    price_ on LLMResponse subclasses raises this. RTK adapter strips
    at adapter layer (defense-in-depth); port boundary is the
    load-bearing enforcement.
    """

    leaked_field: str


# ---------------------------------------------------------------------------
# Protocol surface — verbatim per ADR-9.1.2-6 §3 method signatures
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMProxyPort(Protocol):
    """LLM proxy passthrough with cost-stamped responses.

    Per `port-contracts.md` v0.2.3 §1 ADR-9.1.2-6 design intent: the
    port returns tokens (input_tokens + output_tokens), NEVER USD;
    cost computation is delegated to Cost Meter port (ADR-9.1.2-5)
    per §3.6 cost-meter ownership ADR substance. Adapters wrap RTK
    (primary, Docker sidecar) and LiteLLM (substitute-conformance,
    PyPI library) per ADR-9.2-V5 dual-adapter pattern. Substitute-
    readiness clause at §3 substitute-readiness clause: Protocol MUST
    be implementable on top of either substrate without modification.

    Async / streaming / idempotency profile (ADR-9.1.2-6 §3
    idempotency table):
        call                  — sync, NOT streaming, idempotent
                                (idempotency_key required;
                                 provider-level idempotency varies)
        stream                — sync (returns iterator), streaming,
                                idempotent (idempotency_key required)
        supported_providers   — sync, NOT streaming, idempotent

    `@runtime_checkable` decoration follows the 9.4.1
    `VersionedStatePort` + 9.4.2 `SerializationPort` + 9.4.3
    `MemoryPort` + 9.4.4 `CostMeterPort` precedent. Adapter
    `on_init()` performs `isinstance(self, LLMProxyPort)` self-check
    per executor playbook §9.C addendum (substrate API surface
    verified per F7 precedent — structural Protocol matching, NOT
    nominal inheritance).
    """

    API_VERSION: ClassVar[str] = "1.0.0"

    def call(self, request: LLMRequest) -> LLMResponse: ...

    def stream(self, request: LLMRequest) -> Iterator[LLMStreamChunk]: ...

    def supported_providers(self) -> Sequence[ProviderInfo]: ...


__all__ = [
    "API_VERSION",
    "CompressionContractViolation",
    "CostFieldLeakage",
    "LLMProxyPort",
    "LLMRequest",
    "LLMResponse",
    "LLMStreamChunk",
    "ProviderInfo",
]


API_VERSION: str = LLMProxyPort.API_VERSION
