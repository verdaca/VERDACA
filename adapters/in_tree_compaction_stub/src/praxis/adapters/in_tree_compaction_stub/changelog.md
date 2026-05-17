# praxis-adapter-in_tree_compaction_stub changelog

Per `ports-architecture.md` v0.7 §5 (upgrade workflow shape; one entry per version bump).

## v0.1.0 (2026-05-17)

Initial in-tree compaction stub adapter implementing `CompactionPort` per
ADR-9.1.2-4 §3 Substitute-readiness (`port-contracts.md` v0.2.6). Greenfield
Verdaca-authored Python — no external upstream (no PyPI package, no submodule,
no sidecar). Sibling structural precedent: the Beads in-tree-greenfield adapter
(`adapters/beads/`).

Stage 9.4.6 Phase B.1-W2 — second of three B.1 commits (W1 = the v0.2.6 §3
corrigendum at `e98a25b`; W3 = `adapters/llmlingua/`).

### Role

A PERMANENT CI fallback, not only the Decision-2 Option-D degradation path
(Phase B.1 handover §5): it lets the B.2 contract suite, CI, and every
downstream consumer run green with no LLMLingua wheel installed, and it is
what keeps Verdaca shipping if the substrate-truth probe verdict is FAIL. It
runs the SAME B.2 contract suite as `adapters/llmlingua/`. Selection between
the stub and the real adapter is composition-time configuration, never a
code-path branch — `on_init()` emits a WARNING so a stub-backed CI run is
observably the stub.

### Substance

- 2 `CompactionPort` methods (`compact`, `estimate`) + lifecycle (`on_init`
  isinstance self-check + stub-active WARNING log; `on_shutdown` no-op).
- `API_VERSION` ClassVar mirror (`"1.0.0"`) for `@runtime_checkable` Protocol
  conformance at `isinstance(adapter, CompactionPort)`.
- Span model: each top-level key of `SerializablePayload.body` is one span;
  the key is the span id. `preserve_span_ids` references these keys. A
  `preserve_span_id` absent from `body` is silently ignored (vacuous
  satisfaction) — the stub does not reject it; the W3 LLMLingua adapter
  matches this disposition (both run the same B.2 suite).
- Token model: no upstream tokenizer — the stub's token unit is one
  character of the canonical-JSON serialization of the span set
  (deterministic, binary-stable). A self-consistent stand-in for a real
  tokenizer; the `adapters/llmlingua/` adapter counts real tokens.
- Strategies: `lossless` (no eviction; raises `TokenBudgetUnreachable` if
  the payload exceeds budget); `lossy_eviction` (evicts non-preserved spans
  in deterministic sorted-id order — the stub has no recency signal, so
  "LRU" degrades to a stable order — until the budget is met);
  `lossy_summary` (unsupported — downgraded-as-return to `lossy_eviction`
  per the v0.2.6 downgrade-as-return disposition; it does NOT raise).
- `compact` and `estimate` share one eviction algorithm (`_evict_to_budget`)
  so the forecast cannot drift from the actual.
- `determinism_hash` is computed by the shared Verdaca-owned
  `compute_determinism_hash(request)` imported from `praxis.ports.compaction`
  — the stub does NOT roll its own (ADR-9.1.2-4 §3 v0.2.6; W1 OD-2).
- Error posture: the stub raises `TokenBudgetUnreachable` (the budget cannot
  be met without evicting a preserved span; carries `requested_budget` +
  `minimum_achievable`). It NEVER raises `PreservedSpanEvicted` —
  `_evict_to_budget` evicts only non-preserved spans, so the preserved-span
  invariant holds correct-by-construction (verified by the B.2 output
  assertion, not by a triggered raise). `DeterminismViolation` is
  caller-raised per the §3 owned-vs-delegated table — not raised here.

### v0.1.0 scope notes

- The token model is a deterministic character-count stand-in, NOT a real
  tokenizer. It is self-consistent (the same measure enforces the budget and
  reports `tokens_out`), so the `tokens_out <= token_budget` invariant and
  the B.2 M-T-COMP-* suite are meaningful.
- "LRU" eviction degrades to deterministic sorted-id order: a stub has no
  recency signal. The contract (budget met, preserved spans survive,
  determinism) is honored; recency-accurate eviction is the real substrate's
  concern.
- Contract-test authoring (`tests/.../test_compaction_contract.py`) is Phase
  B.2 — not this cycle. Zero `no_waiver` allow-list entries.

### Version pin

`version_pin.py`: `UPSTREAM_KIND="in_tree"`, `UPSTREAM_NAME=
"in_tree_compaction_stub"`, `UPSTREAM_VERSION="0.1.0"` (the adapter's own
version — there is no external upstream; B.1-W2 OD-4, Beads `beads_in_tree`
precedent). `UPSTREAM_LOCK_HASH` is a Cleo-9.6 source-tree-sha256
placeholder. Per the v0.2.6 ADR-9.1.2-4 §3 corrigendum (W1 OD-1),
`version_pin.py` is the out-of-band home for the stub's substrate identity —
the determinism-hash idempotency contract is scoped to a fixed adapter +
substrate-pin.

### Pre-Cleo invocation

```
PYTHONPATH='adapters/in_tree_compaction_stub/src' uv run --package praxis-contract-tests \
    pytest tests/src/praxis/contract_tests/ports/test_compaction_contract.py -v
```

Workspace registration of `adapters/in_tree_compaction_stub/` in repo-root
`pyproject.toml` + `uv.lock` is Cleo 9.6 territory. Pre-Cleo, the
`--package praxis-contract-tests` + `PYTHONPATH` override mirrors the
Pi-Mono / LiteLLM sibling precedent (`325820a` / `9f6a010`).
