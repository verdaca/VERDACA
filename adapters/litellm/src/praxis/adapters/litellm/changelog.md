# praxis-adapter-litellm changelog

Per `ports-architecture.md` v0.6 §5 (upgrade workflow shape; one entry per version bump).

## v0.1.0 (2026-05-11)

Initial LiteLLM PyPI-pinned LLM Proxy adapter implementing `LLMProxyPort` per
ADR-9.2-V5 v0.6 (`ports-architecture.md` post-2026-05-11 stacked-corrigendum).
**Sole LLMProxyPort substrate** post-H2-falsification per Q-9.4.5-21
(Phase A.3 close at `2043563`). No dual-adapter pattern; no Docker sidecar;
no RTK substrate (retired at Phase A.3 close per close-via-rescope).

Upstream: PyPI `litellm==1.83.14` per `version_pin.py`. Cleo 9.6 supply-chain
review computes `UPSTREAM_LOCK_HASH` (`sha256:` lock in workspace-root
`uv.lock`).

Sibling structural precedents:
- PRIMARY: Mem0 (`34a4eca`) — PyPI client construction + caller-DI auth
- SECONDARY: Pi-Mono native (`325820a`) — API_VERSION ClassVar + on_init
  isinstance + in-process idempotency cache (no upstream-liveness probe;
  in-process pattern)
- TERTIARY: Letta (`b14285b`) — lighter-weight PyPI shape

### Substance

- 3 `LLMProxyPort` methods (`call`, `stream`, `supported_providers`) + lifecycle
  (`on_init` isinstance self-check; `on_shutdown` no-op per in-process posture)
- Caller-DI auth: `api_keys: dict[str, str] | None = None` constructor parameter
  passes per-provider keys to `litellm.completion(api_key=...)`. Caller MAY
  pass `None` and rely on LiteLLM env-var-first behavior (`OPENAI_API_KEY`,
  `ANTHROPIC_API_KEY`, etc.). No upstream-liveness probe at `on_init()`
  (LiteLLM is in-process; mirrors Pi-Mono in-tree-native pattern).
- DS-4 idempotency cache: in-process `dict[str, LLMResponse]` for `call()`
  only. Stage 10+ may add cross-restart durability if MAC-T demands it.
- DS-5 strict-β: `stream()` has NO idempotency cache; pass-through to
  LiteLLM per advisor H#2 override. Rationale: M-T-LLM-IDEMPOTENT-01 spec
  trigger says "`call()` with duplicate idempotency_key" — singular method;
  stream-idempotency is semantically-fragile (cached aggregate vs network-
  paced delta replay); deferred to v1.1.0 minor bump if Stage 10+ MAC-T
  demands it.
- 2 error specializations (per ADR-9.1.2-6 §3):
    - `CompressionContractViolation` raised by `call()` when
      `compression_hint="none"` and adapter detects compression. v0.1.0
      scope: no-op compression-detection (returns False always); LiteLLM
      v1.83.14 does NOT auto-compress; detection heuristics deferred to
      v0.2.0 / Stage 10+. M-T-LLM-COMPRESS-01 deferred to 9.9 promotion
      cycle (test-strategy.md §2.2.6) regardless.
    - `CostFieldLeakage` raised at LLMResponse construction-time via
      VerdacaDTOMixin `extra="forbid"` (Layer 1 of 3-layer defense-in-
      depth). Adapter strips at adapter-layer (Layer 3); port-boundary
      runtime guard is Layer 2 (in `ports/llm_proxy.py` post-`e195fcf`).
- DS-1 cost-strip prefix-match: `cost_*/usd_*/price_*` keys removed from
  `response.usage.model_dump()` before LLMResponse construction. Mirrors
  port-boundary `CostFieldLeakage` prefix-check semantics.
- DS-3 finish_reason mapping: `tool_calls` → `tool_use`; `function_call` →
  `tool_use` (LiteLLM OpenAI-legacy); `stop`/`length`/`content_filter`
  pass-through. Unmapped values raise `ContractViolation` to catch future
  LiteLLM drift.
- DS-2 ProviderInfo enumeration: from `litellm.models_by_provider` (88
  providers; capability-grounded per advisor H#2 override of H#1 DS-2
  GO=133, accepting executor finding J-B1-2 substrate-truth probe).
  Each ProviderInfo carries `name + version + model_catalog: tuple[str, ...]
  + streaming_supported: bool` per Q-9.4.5-13 immutability.

### v0.1.0 scope restrictions (deferred to v0.2.0 / Stage 10+)

- **Auth-token rotation**: caller MUST construct a new `LiteLLMAdapter` to
  rotate `api_keys`. Stage 10+ may add live-rotation discipline.
- **Streaming-cancel**: `stream()` is non-cancellable; caller MUST consume
  the iterator to completion or accept iterator drop. Stage 10+ may add
  cancellation discipline.
- **Stream-idempotency**: `stream()` with duplicate `idempotency_key` does
  NOT replay from cache per DS-5 strict-β. v1.1.0 minor bump if Stage 10+
  MAC-T demands it (e.g., `M-T-LLM-IDEMPOTENT-STREAM-01`).
- **Compression detection**: `_detect_compression()` is no-op for v0.1.0.
  Heuristic detection (response length, callback inspection) is deferred.

### Performance characteristics (F-B1-AUTH-NOISE-1)

`supported_providers()` first-call latency is ~60-90s due to LiteLLM's
provider-introspection (`get_supported_openai_params()`) triggering
GitHub device-auth probes for some providers (`aiml`, `aleph_alpha`
observed; possibly more). Adapter's `try/except` handler catches
device-auth timeouts and conservatively sets `streaming_supported=False`
for those providers — functional correctness intact, but caller should
cache the `supported_providers()` result per session to avoid repeated
60-90s latency.

stderr noise during the call (LiteLLM device-auth WARN/ERROR lines) is
unsuppressed at v0.1.0; Stage 10+ may add stderr redirection during
provider-introspection. M-T-LLM-PROVIDERS-* tests (B.2 territory)
should consider session-scope fixtures or mocked `supported_providers()`
to avoid 60-90s per test run.

### LiteLLM substrate empirical clarification (J-B1-1 finding 2026-05-11)

ADR-9.2-V5 v0.6 §3 Decision bullet 3 prose reads "LiteLLM exposes
`usage.cost_usd` on response by default" — empirically, LiteLLM v1.83.14
does NOT auto-attach `cost_usd` to `response.usage`. Cost is computed via
the SEPARATE `litellm.completion_cost(response)` helper function. Auto-
attach requires caller-registered `litellm.callbacks` or explicit caller
invocation. Defensive strip still applies for any custom callback
configurations that might attach cost fields; 3-layer defense-in-depth is
unaffected. Adapter MUST NOT call `litellm.completion_cost()` — that
violates §3.6 cost-meter ownership ADR substance (Pi-Mono is sole cost
computer). Not corrigendum-triggering (prose-imprecision in supporting
rationale, not in binding decision); noted for substrate-truth fidelity.

### Pre-Cleo invocation (per Q-9.4.5-7 = Option α)

```
PYTHONPATH='adapters/litellm/src' uv run --package praxis-contract-tests \
    pytest tests/src/praxis/contract_tests/ports/test_llm_proxy_contract.py -v
```

Workspace registration of `adapters/litellm/` in repo-root `pyproject.toml`
+ `uv.lock` is Cleo 9.6 territory. Pre-Cleo, the `--package praxis-contract-
tests` + `PYTHONPATH` override mirrors B.1 sibling precedent at `34a4eca` /
Pi-Mono at `325820a`.

### Stage 9.6 housekeeping items

- `UPSTREAM_LOCK_HASH` placeholder `sha256:placeholder-cleo-9.6-computes-on-
  supply-chain-review` — Cleo 9.6 computes real sha256 from `uv.lock`.
- Workspace registration in repo-root `pyproject.toml` + `tests/pyproject.toml`
  — Cleo 9.6 territory.
- M-T-LLM-COMPRESS-01 + M-T-LLM-COSTLEAK-01 stay deferred-to-9.9 per
  test-strategy.md §6.1 (no_waiver allow-list — LLM-Proxy has zero entries
  per advisor §3.1).
