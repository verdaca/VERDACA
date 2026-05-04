# praxis-adapter-letta changelog

Per `ports-architecture.md` v0.2 §5 (upgrade workflow shape; one entry per version bump).

## v0.1.0 (2026-05-04)

Initial in-tree PyPI-pinned Letta adapter implementing `MemoryPort` per ADR-9.2-V1
(`ports-architecture.md` v0.3 §3). SECONDARY adapter in the dual-adapter pair (Mem0
primary at `adapters/mem0/` shipped 34a4eca; B.2 is substitute-readiness validator
per `port-contracts.md` v0.2.1 §3 substitute-readiness clause).

Upstream: `letta-client==1.10.3` (per Letta SDK survey 2026-05-03 §2 + #3 SDK
introspection probes). Range pin `>=1.10,<2.0`.

### Substance

- 5 `MemoryPort` methods (`store`, `query`, `promote`, `revoke_promotion`, `migrate`)
- AP-3 TierNormalizer (query, promote) per `port-contracts.md` v0.2.1 §7 line 306 (i)
- AP-4 ThresholdGuard (promote pre-upstream PS-1 enforcement)
- AP-5 TwoPhaseIdempotencyCommit per Q-B1-22 (i') inherited at 34a4eca: in-process
  dict + on_init reconciliation against Letta-side `verdaca.kind=idempotency:str`
  passages on the singleton agent. AP-5 dedup includes payload-equivalence check
  per `IdempotencyViolation` contract (`common.py` IdempotencyViolation).
- AP-6 SpanAttributeContract (promote 5-attribute canonical per PS-3 set-equality
  verbatim) + 3-attribute mirror span on revoke_promotion per Q-B1-Sub-6
- Adapter-private `verdaca.memory.confidence_synthesis` span — see Amendment D below
- AP-7 OpaqueIDWrapper (`uuid.uuid4().hex` for promotion_id at promote)
- AP-9 ConfidenceScaleNormalizer — see Amendment D below
- M.1 adapter-internal migrator registry per Q-MIGRATE-1 disposition inherited at
  34a4eca; per-passage delete-and-recreate (Letta has no native passage-update)

### Caller-DI Letta instance configuration (caller responsibility)

The adapter accepts a caller-constructed `Letta` instance via
`__init__(*, letta_client=...)`. Letta SDK is a thin httpx wrapper (survey §1) — no
LLM/embedder/vector-store init happens at `Letta()` build time (major contrast vs
B.1's eager-init Mem0 surface).

Caller-side configuration constraints:

1. **Server-side extraction must be disabled or single-passage on direct text
   inserts.** Per Amendment E disposition + #3 SDK introspection: Letta's
   `client.agents.passages.create()` returns `List[Passage]` (not a single Passage)
   because server-side extraction may chunk a single text input into 0 or N>1
   passages. Adapter asserts `len(response) == 1` and raises ContractViolation
   otherwise. **Caller MUST configure Letta server such that direct text-insert
   returns exactly one passage.** No SDK kwarg exposes this control at v1.10.3
   (asymmetry vs B.1 Mem0's `infer=False` bypass — see "Asymmetries" section);
   this is a server-config concern. Probe 9 (live integration) deferred to B.3.

2. **`VERDACA_LETTA_DEFAULT_MODEL` env var** if `system_agent_model` ctor kwarg is
   None and `system_agent_id` is None at on_init time. Adapter raises
   ContractViolation(violation_class="invariant") if neither resolves; NO silent
   fallback per Q-B2-Sub-1 (c) hybrid disposition.

3. **API key surface contained at `Letta()` construction.** No env-var key
   sourcing inside the adapter; caller pre-supplies via Letta SDK conventions
   (`LETTA_API_KEY` env or `api_key=` ctor kwarg).

### Singleton agent provisioning (Q-B2-Sub-1 (c) hybrid)

- Caller may pre-provision and supply `system_agent_id: str` at adapter
  `__init__` (multi-tenant / test scenarios).
- If None, `on_init()` auto-creates a singleton agent with deterministic name
  `f"verdaca-memory-{sha256(api_key)[:8]}"`.
- Model resolved from `system_agent_model` ctor kwarg → `VERDACA_LETTA_DEFAULT_MODEL`
  env var → ContractViolation if neither resolves.
- **Credential-rotation caveat:** changing `api_key` for a deployment changes
  the deterministic seed → orphaned `agent_id` → orphaned data. Surface as
  adapter-side migration concern. Not a B.2 blocker. Stage 10 hardening:
  externally pinned agent name + agent_id-by-tag discovery + migration
  helper.

### Tag-encoding convention (Sub-3 Option γ + Amendment B)

All `verdaca.*` tag values use `<key>=<value>:<type>` encoding where
`<type>` ∈ {str, int, float, bool}.

**Constraint (Amendment B):** caller-supplied str values (in
`MemoryEntry.metadata` and `MemoryEntry.source_span_id`) MUST NOT contain
`=` or `:`. Adapter raises `ContractViolation(violation_class="value")` at
encode time if violated. Rationale: prevent round-trip decode ambiguity.

**Caller-arbitrary key handling (idempotency_key, correlation_id):**
sha256-hashed before tag encoding (preserves dedup semantics; loses
informational round-trip on rehydrate). The original key is preserved
at the call site for `IdempotencyViolation` reporting.

**DTO payloads with JSON syntax** are stored in passage `text` field
(no encoding constraint), not as tag values. Idempotency SUCCESS records
use a JSON envelope `{"result_dto": ..., "prior_call_at_us": <int>}` in
text; promotion-state records use `{"hit_id": ..., "rationale": ...}`.

**Stage 10 deferred:** caller-arbitrary str-value support via base64-encoded
escape per advisor disposition. v0.1.0 ships defensive raise.

### Discriminator-tag taxonomy (Amendment A — sidecar isolation)

Letta's `client.agents.passages.search()` runs semantic search across ALL
passages on the singleton agent. The adapter partitions the namespace via
discriminator tags:

| Discriminator | Purpose |
|---|---|
| `verdaca.kind=user:str` | caller MemoryEntry-store passages |
| `verdaca.kind=promotion_state:str` | promotion-state sidecar passages |
| `verdaca.kind=idempotency:str` | AP-5 INTENT/SUCCESS sidecar passages |

`query()` filters sidecar passages by **EXCLUDING** the latter two kinds
from raw search results. Filter is post-search client-side; if cardinality
drops below `top_k` due to filtering, adapter does NOT compensate with
additional fetch — preserves M-T-MEM-QUERY-04 cardinality-drift contract.

`_load_promotion_state_cache()` at on_init does the **INVERSE** — INCLUDES
only promotion-state-tagged passages.

### Promotion-state sidecar pattern (asymmetry vs B.1)

Letta has no native `passage-update` method (survey §5.3) — promotion-state
synthesis cannot mutate the user passage's tags in place (unlike B.1's
read-merge-update on Mem0 metadata). Instead, B.2 creates a separate
sidecar passage carrying `verdaca.kind=promotion_state:str` discriminator
plus `verdaca.promotion_state.tier` and `verdaca.promotion_state.promotion_id`
tags. The user passage's `hit_id` continuity is preserved (no delete-and-
recreate of the user passage).

**Promotion-state cache (Amendment C):** rehydrated explicitly at on_init
into in-process `_promotion_by_id` + `_promotion_by_passage` dicts;
invalidated on `promote()` / `revoke_promotion()`. **Multi-LettaAdapter-
instance staleness:** if multiple LettaAdapter instances point at the same
singleton agent, cross-instance cache invalidation does NOT propagate
(Stage 10 deferred — periodic refresh or pub/sub mechanism). Single-instance
deployments unaffected.

**Revocation:** simple `passages.delete(memory_id, agent_id)` of the
promotion-state sidecar passage. Cleaner than B.1's read-merge-update
strip pattern (no metadata mutation needed).

### Migration: per-passage delete-and-recreate (asymmetry vs B.1)

Letta has no native `passage-update` method, so within-adapter
schema-version migration is structurally heavier than B.1's
read-merge-update pattern. For each candidate passage at `from_version`:

1. `client.agents.passages.delete(memory_id, agent_id)`
2. `client.agents.passages.create(agent_id, text=migrated_text, tags=migrated_tags)`

Per `port-contracts.md` v0.2.1 §3.5(a) AP-8 TwoWindowMigration is offline,
so the per-passage delete-and-recreate cost is amortized against the
offline window — not a hot-path concern.

**Sub-10b advisor disposition:** NO runtime span emission for migrate
(B.1 silence symmetry — B.1's migrate() at 34a4eca emits no span either).
The semantic `verdaca.memory.migration.path = "delete_and_recreate"` is
documented here as design-recorded asymmetry only; no `verdaca.port.memory.migrate`
span name introduced. Stage 10 may revisit with B.3 contract test author
input on whether the migration-path attribute is worth runtime instrumentation.

### Server pre-1.0 caveat (Q-B2-Sub-9)

SDK `letta-client` v1.10.3 is post-1.0 and follows semantic versioning;
**server-side `letta` is pre-1.0 (v0.16.7 / 2026-03-31)** per survey §2.
SDK API stability is downstream of server schema stability via Stainless
generation. v0.x server may break compat at v0.17.0+ and force SDK v2.0
bump. Range pin `letta-client>=1.10,<2.0` brackets SDK semantic stability,
NOT server schema stability. Adapter consumers should monitor server-side
release notes independently of SDK version pin.

### Asymmetries vs B.1 (Mem0 adapter at 34a4eca)

| Axis | B.1 (Mem0) | B.2 (Letta) |
|---|---|---|
| Eager init | Eager (LLM + embedder + vector store at Memory()) | Non-eager (httpx only at Letta()) |
| Chat-format marshaling | Required (`[{"role":"user","content":...}]`) | Not required (text=str directly) |
| Native confidence | None (default-1.0 synthesis fires per Q-B3-4 rare-path; N2 inversion) | None per Amendment D — Letta `Result` has NO score field (survey §5.2 misread the types-namespace; #3 introspection corrected). default-1.0 synthesis fires per-hit, NOT rare-path |
| Passage update | `Memory.update(memory_id, data, metadata)` partial-write | NO native update — promotion-state via sidecar passages (asymmetry); migration via delete-and-recreate (asymmetry) |
| Native idempotency_key | None (synthesis via Q-B1-22 (i')) | Same (synthesis via Q-B1-22 (i') inherited verbatim) |
| Server-side extraction bypass | `infer=False` ctor kwarg per Q-B1-1 | NO equivalent SDK kwarg; caller must configure server (Amendment E) |
| User-id partitioning | `_VERDACA_USER_ID` + `_VERDACA_SIDECAR_USER_ID` (user_id channel) | Singleton `system_agent_id` + discriminator tags (tag channel; Amendment A) |
| User-passage correlation_id capture | Stored in Mem0 metadata via `verdaca.correlation_id` key (informational; never read back into MemoryHit) | NOT stored on user passages. **Substitute-readiness IS preserved (case (b) per advisor #4 disposition):** `MemoryHit.correlation_id` is a VerdacaDTOMixin Protocol-surface field, but BOTH B.1 and B.2 populate it from `q.correlation_id` (the query's correlation_id), NOT from any stored-entry round-trip. Storage-side informational retention is the only delta; trace-stitching workflows reading `hit.correlation_id` get identical results across both adapters. AP-6 5-canonical PROMOTE span attribute set unchanged (`correlation_id` is NOT a span attribute on either adapter — propagated via OTEL trace-context layer per `common.py` §0.4) |
| `revoke_promotion` upstream call | read-merge-update strips promotion-marker keys | Single `passages.delete(memory_id)` of sidecar (cleaner) |

### Stage 10 deferred

- Durable cache backend hardening (cross-instance invalidation, periodic refresh)
- Async mode (Letta SDK has `AsyncLetta`; B.2 targets sync per Q-B1-1 caller-DI symmetric discipline)
- Caller-arbitrary str value support via base64-encoded escape (Amendment B relaxation)
- Server-side extraction-config investigation OR multi-passage stored_id encoding via Option (ii) JSON-array-as-stored_id (lossy at Protocol surface; breaks cross-adapter parity for stored_id value-shape)
- Externally pinned agent name + agent_id-by-tag discovery + credential-rotation migration helper (Sub-1 (c) caveat hardening)
- `passages.list` cursor-iteration optimization via Letta tag-filter once syntax verified (probe 5 at integration)
- Per-instance promotion-state cache invalidation propagation
- Optional `verdaca.memory.migration.path` runtime span attribute on migrate (Sub-10b reopened; cross-adapter span-set parity recheck with B.3 contract test author)

### Deferred-probe ledger (B.3 launch dependency notes)

Six probes deferred to integration testing (require live Letta server):

1. Default model resolution under test env (Sub-1 (c) caveat verification)
2. Deterministic-seed `sha256(api_key)[:8]` collision behavior across realistic scenarios
3. Auto-create failure mode (deliberately-invalid model name → ContractViolation surfaces with clear message)
4. Server auto-archive-management (Sub-2 — explicit archive create only if probe reveals no auto-management)
5. Sidecar-passage search-leak end-to-end query verification (Amendment A behavior)
6. Single-text `passages.create()` return-list cardinality (Amendment E — empirical confirmation under default Letta cloud config)

Carry forward to Stage 9.4.5 LLM Proxy port shipment for orchestration of live-integration probes 1, 2, 3, 4, 5, 6.

### SDK survey discrepancies discovered at #3 introspection

Letta SDK survey 2026-05-03 (research artifact, gitignored, no formal corrigendum
process) had two type-namespace-collision misreads corrected by #3 introspection
probes:

1. **Survey §5.2 "PassageSearchResponseItem.score: float" — FALSIFIED.** Survey
   sourced `letta_client.types.passage_search_response.PassageSearchResponseItem`
   which carries `passage / score / metadata` fields. Actual return type of
   `client.agents.passages.search()` is
   `letta_client.types.agents.passage_search_response.PassageSearchResponse`
   (different module path), a Pydantic class with `count: int` + `results:
   List[Result]` where `Result` has `id / content / timestamp / tags` only —
   NO score field. Confidence falls back to default-1.0 synthesis (Amendment D).

2. **Survey §5.1 single-Passage create return — FALSIFIED.**
   `PassageCreateResponse = List[Passage]` — server may return 0 or N>1 passages
   from a single create call (extraction-style chunking). Adapter asserts
   `len(response) == 1` and raises ContractViolation otherwise (Amendment E).

Both findings absorbed into v0.1.0 substance; documented in survey artifact tail
(out-of-scope for adapter shipment) per advisor disposition (gitignored research
artifact, not a ratified spec — no corrigendum process).
