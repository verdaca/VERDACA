# praxis-adapter-llmlingua changelog

Per `ports-architecture.md` v0.7 §5 (upgrade workflow shape; one entry per version bump).

## v0.1.0 (2026-05-17)

Initial LLMLingua PyPI-pinned Compaction adapter implementing `CompactionPort`
per ADR-9.1.2-4 §3 (`port-contracts.md` v0.2.6, the v0.2.4 substrate
re-anchor). Wraps the `llmlingua` PyPI SDK (microsoft/LLMLingua,
`llmlingua==0.2.2`, MIT). `adapters/llmlingua/` supersedes the v0.1-era
`adapters/forge/` (F-9.4.6-FORGE-SEMANTIC-MISFIT — Forge is a coding agent,
not a compaction substrate). Sibling structural precedent: the LiteLLM
PyPI-library adapter (`adapters/litellm/`, `9f6a010`).

Stage 9.4.6 Phase B.1-W3 — third of three B.1 commits (W1 = the v0.2.6 §3
corrigendum at `e98a25b`; W2 = `adapters/in_tree_compaction_stub/` at
`15d5a57`). B.1 is complete at this commit.

### Role

The primary CompactionPort adapter. The `adapters/in_tree_compaction_stub/`
adapter (B.1-W2) is the permanent CI fallback and the G-1 degradation path;
this adapter is the production substrate. Both run the same B.2 contract
suite.

### Substrate-truth probe

Per the W1-H#1 substrate-truth probe
(`docs/stage-9.4.6-b.1-substrate-truth-probe.md`, verdict **PASS-DEGRADED**):
the surface is >= the contract on every probe item, but
`compress_prompt(target_token=...)` is a soft target, not an inclusive
ceiling — this adapter emulates the hard `tokens_out <= token_budget` bound
(OD-5). Determinism is PASS on static evidence (`seed_everything(42)` +
zero sampling knobs); the empirical twice-run is a B.2 contract test.

### Substance

- 2 `CompactionPort` methods (`compact`, `estimate`) + lifecycle (`on_init`
  isinstance self-check; `on_shutdown` no-op).
- `API_VERSION` ClassVar mirror (`"1.0.0"`) for `@runtime_checkable` Protocol
  conformance at `isinstance(adapter, CompactionPort)`.
- Span model: each top-level key of `SerializablePayload.body` is one span;
  the key is the span id. Preserved spans (`preserve_span_ids` intersect the
  body keys) bypass LLMLingua entirely and are kept verbatim — the
  preservation invariant holds exact-by-construction; the adapter never
  raises `PreservedSpanEvicted`. A `preserve_span_id` absent from `body` is
  silently ignored (vacuous satisfaction — matches the in-tree stub).
- Strategy mapping (cross-adapter-coherent with the in-tree stub, which has
  the inverse native strength): `lossless` (no compression; pass-through;
  raises `TokenBudgetUnreachable` if the payload exceeds budget);
  `lossy_summary` (LLMLingua compression — this adapter's native mode);
  `lossy_eviction` (LLMLingua has no span-eviction primitive — downgraded-
  as-return to `lossy_summary` per the v0.2.6 disposition; does NOT raise).
- OD-5 hard-budget emulation: after `compress_prompt`, the result is counted
  via `get_token_length`; if over budget it is re-compressed at a tighter
  `target_token` (<= 3 iterations); the final guard raises
  `TokenBudgetUnreachable` if still over.
- `determinism_hash` is computed by the shared Verdaca-owned
  `compute_determinism_hash(request)` imported from `praxis.ports.compaction`
  — the adapter does NOT roll its own (ADR-9.1.2-4 §3 v0.2.6; W1 OD-2).
- A substrate-drift guard raises `ContractViolation` if LLMLingua's
  `compressed_prompt_list` is not positionally aligned to the input
  `context` (LiteLLM `_map_finish_reason` "catch future drift" precedent).
- `PromptCompressor` is constructed lazily (config-only `__init__`,
  `_get_compressor()` cache) — the model weights load on first
  compact/estimate, not at construction or `on_init`.

### v0.1.0 scope notes

- Default model: LLMLingua-2 bert-base
  (`microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank`,
  `use_llmlingua2=True`, `device_map="cpu"`) — ungated, CPU,
  deterministic-by-construction. Callers (and the B.2 environment) override
  via the `__init__` keyword arguments.
- OD-5 re-compress is capped at 3 iterations; an unreachable budget surfaces
  as `TokenBudgetUnreachable` via the final guard.
- B.2-verified empirical assumptions: (a) `compress_prompt` dispatches to
  llmlingua2 mode for a `use_llmlingua2=True` compressor; (b)
  `compressed_prompt_list` is positionally aligned to the input `context`.
  The empirical determinism twice-run is a B.2 contract test.
- Contract-test authoring (`tests/.../test_compaction_contract.py`) is
  Phase B.2 — not this cycle. Zero `no_waiver` allow-list entries.

### Version pin

`version_pin.py`: `UPSTREAM_KIND="pypi"`, `UPSTREAM_NAME="llmlingua"`,
`UPSTREAM_VERSION="0.2.2"`. `UPSTREAM_LOCK_HASH` is a Cleo-9.6
`uv.lock`-sha256 placeholder. Per the v0.2.6 ADR-9.1.2-4 §3 corrigendum
(W1 OD-1), `version_pin.py` is the out-of-band home for the adapter's
substrate identity — the determinism-hash idempotency contract is scoped
to a fixed adapter + substrate-pin.

### Pre-Cleo invocation

```
PYTHONPATH='adapters/llmlingua/src' uv run --package praxis-contract-tests \
    pytest tests/src/praxis/contract_tests/ports/test_compaction_contract.py -v
```

Workspace registration of `adapters/llmlingua/` in the repo-root
`pyproject.toml` + `uv.lock` is Cleo 9.6 territory. Pre-Cleo, the
`--package praxis-contract-tests` + `PYTHONPATH` override mirrors the
LiteLLM sibling precedent (`9f6a010`).
