# Pi-Mono Cost Tracker — Architecture Decision Document

**Module:** `praxis.kernel.cost` (Pi-Mono)
**Stage:** Praxis Stage 1, Step 1.1 (Measurement Foundation)
**Author:** Winston (System Architect)
**Date:** 2026-04-12
**Status:** Draft for Murat's test strategy review
**Version:** 0.1
**Risk class:** RPN 20 — highest risk component in the Praxis architecture (flagged by Murat)
**Language:** Python 3.12

**Inputs consulted:**
- `praxis-build-plan.md` — Stage 1 goals and measure-first sequencing
- `box-core-architecture.md` — kernel layer position, 5-layer structure
- `hybrid-architecture-recommendations.md` — best-of-breed rationale
- `src/badlogic-pi-mono-8a5edab282632443.txt` — TypeScript reference implementation (5.3 MB)

**Not in scope (explicit):**
- Implementation code → Amelia (after Murat's test strategy)
- Test code → Quinn (after Murat designs strategy from this doc)
- Dashboard UI → Step 1.3 (later in Stage 1)
- Budget enforcement / auto-escalation → Stage 4 (runtime concern, reads from tracker)

---

## 0. EXECUTIVE SUMMARY

Pi-Mono is the foundation every subsequent Praxis component reports through. One rule dominates every design decision: **cost math in `decimal.Decimal`, never float, never IEEE 754, no exceptions.**

The design follows four load-bearing principles:

1. **Float is the enemy.** The reference implementation (badlogic/pi-mono) uses JavaScript `number` for cost, which is IEEE 754 double. That pattern is not portable to Praxis at any scale — error compounds per request, and the Decimal boundary must be the only path from tokens to money.
2. **Cost records are immutable facts.** Every tracked call produces exactly one `CostRecord` row that is written once and never mutated. Aggregations are derived views, never authoritative.
3. **Pricing is versioned.** Provider prices change. Historical queries must reconcile against the price that was in effect at the request time, not today's price.
4. **Providers extract tokens, the tracker computes cost.** Providers never touch Decimal. They translate vendor-specific token field names into the universal 4-class token schema (input, output, cache_read, cache_write). The tracker owns every cost calculation.

These four principles, combined with property-based tests (Hypothesis), golden file fixtures per provider, and real-invoice reconciliation, make the Murat-flagged failure modes **structurally impossible**, not merely unlikely.

Every design choice below is traceable to a numbered Praxis requirement (R1–R11) or a numbered Murat risk (M1–M5), collected in the traceability matrix at the end.

---

## 1. REFERENCE ANALYSIS — `badlogic/pi-mono`

The TypeScript monorepo at `badlogic/pi-mono` is a production-tested, multi-provider LLM client library with native token-usage capture. It is the right starting point for patterns, the wrong starting point for code. What follows is the delta between what it does and what Praxis needs.

### 1.1 What we KEEP (conceptually)

| # | Pattern | Location in pi-mono | Why we keep it |
|---|---------|---------------------|----------------|
| K1 | **Central model registry** | `packages/ai/src/models.ts:modelRegistry` | `provider × model_id → Model` with cost metadata. Clean O(1) lookup, trivially extensible. |
| K2 | **4-class token taxonomy** | `packages/ai/src/types.ts:Usage` | Every major provider (Anthropic, OpenAI, Google) can be expressed as `(input, output, cache_read, cache_write)`. Universal schema worth adopting. |
| K3 | **Provider-scoped field translation** | `packages/ai/src/providers/anthropic.ts:11299-11305` | Each provider translates its native field names (`cache_creation_input_tokens`, `cache_read_input_tokens`, `input_tokens_details.cached_tokens`, etc.) into the universal 4-class schema. Translation is a per-provider concern, not the tracker's. |
| K4 | **Cache retention as first-class intent** | `packages/ai/src/providers/anthropic.ts:resolveCacheRetention` | `"none" \| "short" \| "long"` as a request parameter. Allows callers to opt into expensive 1-hour cache writes explicitly and makes cost attribution straightforward. |
| K5 | **Price-per-million-tokens canonical representation** | `packages/ai/src/types.ts:Model.cost` | Aligns exactly with how vendors publish pricing (USD/MTok). Divide-by-1e6 is the only unit conversion anywhere. |
| K6 | **Capture at end-of-stream, not mid-stream** | `packages/ai/src/providers/anthropic.ts:11425+` (`message_delta`) | Providers only finalize usage on the terminal message event. Any mid-stream capture is guaranteed incomplete. |
| K7 | **Multi-provider registration** | `packages/ai/src/providers/register-builtins.ts` | Providers self-register at import time. Praxis retains this — it makes the extensibility contract simple to reason about. |
| K8 | **OpenAI cached-token subtraction** | `packages/ai/src/providers/openai-responses.ts:18004-18007` | OpenAI reports `input_tokens` as the *sum* of fresh + cached; you must subtract `input_tokens_details.cached_tokens` to get the fresh count. Easy to get wrong; the reference code does it right. |

### 1.2 What we CHANGE

These are the non-negotiable deltas from the reference:

| # | Change | Rationale | Requirement/Risk |
|---|--------|-----------|------------------|
| C1 | **`number` → `decimal.Decimal` everywhere cost touches** | JS `number` is IEEE 754 double. `0.1 + 0.2 !== 0.3`. Error compounds per request; drift at scale is guaranteed. This is the exact failure mode Murat flagged at the top of the list. | R7, M1 |
| C2 | **Immutable `CostRecord`, decoupled from `LLMResponse`** | pi-mono mutates `usage.cost` on the `AssistantMessage` object (see `calculateCost` at `models.ts:9692`). Praxis emits an immutable Pydantic model that is written once, never rewritten. Easier to audit and replay. | R4, M3 |
| C3 | **Versioned pricing with `effective_from`** | pi-mono stores pricing as module-level constants. If a provider raises prices mid-month, historical queries silently use today's price. Praxis stores pricing as `(provider, model_id, effective_from, ...)` rows; every `CostRecord` snapshots the `pricing_effective_from` it used. | R6, M4 |
| C4 | **Durable SQL storage, not per-message state** | pi-mono attaches usage to a message object and exposes no query layer. Praxis needs per-session, per-workflow, per-agent, per-time-range aggregation — that is a SQL workload. | R4, R6 |
| C5 | **Explicit aggregation model with deterministic rollups** | pi-mono does not aggregate. Praxis needs `get_session_cost`, `get_workflow_cost`, `get_agent_cost`, each returning a deterministic `CostSummary`. | R4 |
| C6 | **Multi-currency reserved (USD canonical v1)** | pi-mono assumes USD globally. Praxis keeps USD as the only active currency in v1, but every monetary record carries a `currency` field so multi-currency is a config change, not a schema migration. | — (forward-compat) |
| C7 | **Async event stream for dashboards** | pi-mono exposes no streaming hook. Praxis provides `stream_events(filter)` as an `AsyncIterator[CostEvent]` backed by a transactional outbox table. | R5 |
| C8 | **Invoice reconciliation** | pi-mono has no concept of reconciling to provider invoices. Praxis exposes `reconcile(invoice)` to detect silent pricing drift and silent counter drift against real invoices. | M4 |
| C9 | **Providers do NOT touch Decimal** | In pi-mono, the Anthropic provider calls `calculateCost` directly and writes a float cost onto the response. In Praxis, providers are **token-only**. They translate vendor field names to the 4-class schema and return `LLMResponse` with `int` counts. The tracker is the **only** caller of cost math. | R7, M1 |
| C10 | **Pure Python `Protocol` for providers, not TS class inheritance** | pi-mono uses a `StreamFunction` generic type and interface inheritance. Praxis uses `typing.Protocol` for structural typing — minimum friction for third-party provider contributions, no inheritance ceremony. | — (idiom) |
| C11 | **`async` by default** | pi-mono is fundamentally callback/promise based. Praxis is async-first with `asyncio` throughout. `track_cost` accepts an already-completed response (sync return is fine) but storage + streaming + reconciliation are all async. | R8 |
| C12 | **Sub-1ms hot path** | pi-mono's cost math is fine, but it runs inline with streaming which can allocate thousands of usage objects per session. Praxis targets <1ms amortized per `track_cost()` call with the storage write deferred via the event loop where safe. | R10 |
| C13 | **Pricing snapshot hash in every record** | pi-mono records only the computed cost. Praxis stores `pricing_snapshot_sha256` in every record so the exact rate schedule used can be recovered byte-for-byte from version control. Makes disputes with providers winnable. | M4 |
| C14 | **SQLite dev / Postgres prod via async SQLAlchemy** | pi-mono is unstoried re: persistence. Praxis uses async SQLAlchemy 2.0 with `aiosqlite` in dev and `asyncpg` in prod. Same ORM classes, same repository, dialect-aware only where necessary. | R8 |

### 1.3 What we DO NOT PORT

Irrelevant to the cost-tracker slice, or actively in the way:

- **All of `packages/agent/*`.** Agent loop is not this module's business; Praxis has its own runtime in Stage 4.
- **OAuth utilities** (`packages/ai/src/utils/oauth/*`). Praxis uses API keys from environment / secret store. No OAuth flows for Anthropic, Google, GitHub Copilot, OpenAI, Google Antigravity, or Gemini CLI.
- **Provider implementations for Bedrock, Azure, GitHub Copilot, Gemini CLI, Mistral, Groq, Cerebras, OpenRouter, Vercel AI Gateway, Z.AI, MiniMax, HuggingFace, OpenCode, Kimi.** Launch set is Anthropic + OpenAI + Google Gemini (R2). The rest are on the extensibility contract for later.
- **`transform-messages.ts` / `simple-options.ts` / Claude Code tool naming mimicry.** These normalize request construction — not the tracker's concern. Whoever calls the provider SDK constructs the request; the tracker sees only the response.
- **TypeBox schemas.** Replaced by Pydantic v2.
- **`bedrock-provider.d.ts` shims.** TypeScript type fiction with no Python equivalent.
- **Stealth-mode headers, cache-control tag negotiation in prompt construction.** Caller's business.
- **`faux.ts` fake provider.** Praxis will have its own `FakeProvider` for tests, written to the Praxis `Protocol`, not the pi-mono interface.

### 1.4 Summary of the reference-vs-Praxis delta

Ninety percent of the patterns port. The ten percent that change — the move from `number` to `Decimal`, the move from mutable `Usage` to immutable `CostRecord`, and the move from in-memory attribute to SQL facts — are exactly where Pi-Mono's risk profile differs from the reference's risk profile. badlogic/pi-mono is a client library whose consumers are aware of the floating-point tradeoff; Praxis is a **billing-critical** foundation whose consumers assume the numbers are right.

---

## 2. MODULE STRUCTURE

### 2.1 File layout

```
praxis/kernel/cost/
├── __init__.py                  # Public API re-exports only
├── tracker.py                   # CostTracker — main entry point
├── models.py                    # Pydantic v2 data models (pure)
├── math.py                      # Decimal math primitives (pure)
├── aggregator.py                # Rollup logic (session/workflow/agent)
├── events.py                    # Event streaming / outbox consumer
├── reconciliation.py            # Invoice reconciliation
├── telemetry.py                 # OpenTelemetry spans + Prometheus metrics
│
├── providers/
│   ├── __init__.py
│   ├── base.py                  # Provider Protocol + shared types
│   ├── registry.py              # Provider registration + lookup
│   ├── anthropic.py             # Anthropic token extractor
│   ├── openai.py                # OpenAI token extractor
│   ├── google.py                # Google Gemini token extractor
│   └── fake.py                  # Deterministic test provider
│
├── pricing/
│   ├── __init__.py
│   ├── catalog.py               # In-memory current-price catalog
│   ├── loader.py                # Snapshot loading + version management
│   └── snapshots/
│       ├── 2026-04-12.json      # Seed snapshot
│       └── README.md            # How to add a new snapshot
│
└── storage/
    ├── __init__.py
    ├── schema.py                # SQLAlchemy 2.0 mapped classes
    ├── repository.py            # Async DAO
    ├── dialects.py              # SQLite vs Postgres divergences
    └── migrations/              # Alembic
        ├── env.py
        └── versions/
```

### 2.2 Dependency direction rules

These rules are enforced by `ruff`'s `import-linter` (or equivalent) in CI. Any PR that violates them fails the build.

```
L0 (no internal imports):
  models.py
  math.py

L1 (depends only on L0):
  pricing/catalog.py
  pricing/loader.py
  providers/base.py

L2 (depends on L0–L1):
  providers/anthropic.py
  providers/openai.py
  providers/google.py
  providers/fake.py
  providers/registry.py
  storage/schema.py
  storage/dialects.py

L3 (depends on L0–L2):
  storage/repository.py

L4 (depends on L0–L3):
  aggregator.py
  events.py

L5 (top):
  tracker.py          # depends on everything below
  reconciliation.py
  telemetry.py
```

**Hard rules:**

1. **Nothing in `providers/*` imports from `math.py`.** Providers deal only in integer token counts. If a provider file has `from ..math import` anywhere, it is a bug. The tracker is the single caller of cost math.
2. **`models.py` has zero imports from Praxis.** Pure Pydantic. No `praxis.*` imports.
3. **`math.py` has zero imports from Praxis.** Pure Decimal utilities. No `praxis.*` imports.
4. **Nothing in `praxis.kernel.cost.*` imports from any other Praxis package.** This is the foundation layer (R9). `kernel.cost` must be installable and runnable standalone, which is also how we test it in isolation.
5. **No circular imports.** The layers above are strictly acyclic.
6. **`__init__.py` is the only public surface.** Code outside `praxis.kernel.cost` must import only from `praxis.kernel.cost`, never from its submodules.

### 2.3 Public API (what `__init__.py` re-exports)

```
CostTracker                       # class, the main entry point
LLMRequest                        # dataclass (Pydantic)
LLMResponse                       # dataclass
CostRecord                        # dataclass
CostSummary                       # dataclass
CostEvent                         # dataclass
CostAmount                        # dataclass
ModelPricing                      # dataclass
TimeRange                         # dataclass
Filter                            # dataclass
Invoice                           # dataclass
InvoiceLine                       # dataclass
ReconciliationReport              # dataclass
ReconciliationDrift               # dataclass
ProviderName                      # StrEnum
TokenClass                        # StrEnum
CacheRetention                    # StrEnum
Currency                          # StrEnum
AggregationScope                  # StrEnum

# Exceptions
CostTrackerError                  # base
UnknownModelError                 # pricing lookup miss
PricingGapError                   # no price covers request time
ProviderExtractionError           # provider couldn't parse token counts
ReconciliationError               # invoice couldn't be matched
```

Anything not in this list is implementation detail. Third-party provider plugins import `Provider` from `praxis.kernel.cost.providers` (a separately exported namespace for extensibility) — see §5.

---

## 3. DATA MODEL

### 3.1 Conventions

- **All models `frozen=True`** unless explicitly noted. Immutability by default.
- **All IDs are `str` (ULID)** — 26 characters, lexicographically sortable by time, opaque enough to not leak information. Not `int` (not portable), not raw `uuid.UUID` (not time-sortable). Praxis will generate them via `python-ulid`.
- **All timestamps are `datetime` with `tzinfo=UTC`.** Naive datetimes are rejected at the model boundary via a `@field_validator`.
- **All monetary amounts are `Decimal`.** Pydantic serializes `Decimal` as a string to preserve precision across JSON boundaries.
- **Token fields are `int`** with non-negative check. Expect values up to billions on long-running installations; `int` is unbounded in Python so this is safe.
- **Unknown fields rejected** via `model_config = ConfigDict(extra="forbid")`. Typos in fields names fail loudly.

### 3.2 Enums

```
ProviderName (StrEnum):
  ANTHROPIC = "anthropic"
  OPENAI    = "openai"
  GOOGLE    = "google"
  # Reserved for Stage 2+: AMAZON_BEDROCK, AZURE_OPENAI, MISTRAL, ...

TokenClass (StrEnum):
  INPUT       = "input"         # fresh, non-cached input tokens
  OUTPUT      = "output"        # generated output tokens
  CACHE_READ  = "cache_read"    # input tokens satisfied from prompt cache
  CACHE_WRITE = "cache_write"   # input tokens written to prompt cache

CacheRetention (StrEnum):
  NONE  = "none"                # no cache control on request
  SHORT = "short"               # ~5 minutes (Anthropic default)
  LONG  = "long"                # ~1 hour (Anthropic 1h TTL)

Currency (StrEnum):
  USD = "USD"                   # canonical and only currency for v1

AggregationScope (StrEnum):
  REQUEST   = "request"
  SESSION   = "session"
  WORKFLOW  = "workflow"
  AGENT     = "agent"
  PROVIDER  = "provider"
  ALL       = "all"
```

### 3.3 Core models (Pydantic v2)

The sections below define every field, its type, its invariants, and its relationships. The actual Pydantic class definition is Amelia's job; Winston's job is to nail the contracts down so tightly that Amelia's implementation has exactly one legal shape.

#### 3.3.1 `ModelPricing`

Represents a single versioned rate schedule for a `(provider, model_id)` pair. Many `ModelPricing` rows can exist for the same pair; the one whose `[effective_from, effective_until)` window contains the request's `started_at` is the authoritative price.

| Field | Type | Notes |
|-------|------|-------|
| `provider` | `ProviderName` | |
| `model_id` | `str` | Provider-native model id, e.g., `"claude-opus-4-6"`, `"gpt-5-preview"`, `"gemini-3.1-pro"`. |
| `currency` | `Currency` | `USD` in v1. |
| `input_rate` | `Decimal` | USD per 1,000,000 fresh input tokens. `>= 0`. |
| `output_rate` | `Decimal` | USD per 1,000,000 output tokens. `>= 0`. |
| `cache_read_rate` | `Decimal` | USD per 1,000,000 cache-read tokens. Typically ~10% of `input_rate` for Anthropic. `>= 0`. |
| `cache_write_rate` | `Decimal` | USD per 1,000,000 cache-write tokens. Typically ~125% of `input_rate` for Anthropic short cache, ~200% for long cache. `>= 0`. |
| `effective_from` | `datetime` (UTC) | First instant at which this rate applies. Inclusive. |
| `effective_until` | `datetime \| None` | First instant at which this rate no longer applies. Exclusive. `None` means "current". |
| `source_url` | `str \| None` | Provider's pricing page URL at the time of snapshot. For audit. |
| `snapshot_sha256` | `str \| None` | SHA-256 of the JSON snapshot file this row was loaded from. For audit. |

**Invariants (`@model_validator(mode="after")`):**

1. All rates non-negative.
2. `effective_until > effective_from` if `effective_until is not None`.
3. `effective_from` and `effective_until` are tz-aware UTC.
4. **Soft check (warning, not error):** `cache_read_rate <= input_rate` and `cache_write_rate >= input_rate`. These are conventions, not universal laws; a future provider may violate them. Log a warning and proceed.

**Relationships:**
- `CostRecord.pricing_effective_from` and `CostRecord.pricing_snapshot_sha256` together form a logical FK back to `ModelPricing`.
- Uniqueness: `(provider, model_id, effective_from)` is the composite primary key.
- Gap detection: at load time, the pricing catalog verifies that `[effective_from, effective_until)` windows for each `(provider, model_id)` form a contiguous partition of time with no gaps and no overlaps. A gap is a `PricingGapError` at load time.

#### 3.3.2 `LLMRequest`

Metadata about a pending or completed call, from the tracker's perspective. Does **not** contain the prompt. The tracker never sees prompt content; that is deliberately scoped out for privacy and for a clean API surface.

| Field | Type | Notes |
|-------|------|-------|
| `request_id` | `str` (ULID) | Caller-assigned or auto-generated. Must be globally unique. |
| `provider` | `ProviderName` | |
| `model_id` | `str` | Must exist in the pricing catalog at `started_at`. |
| `session_id` | `str \| None` | Logical session grouping. Typically a BMAD session or a user session. |
| `workflow_id` | `str \| None` | A workflow execution (one run of a template). |
| `agent` | `str \| None` | BMAD agent name (e.g., `"winston"`, `"amelia"`, `"murat"`). |
| `parent_request_id` | `str \| None` | For sub-calls (one LLM call spawning another). Forms a tree. |
| `cache_retention` | `CacheRetention` | Intent at request time. |
| `tags` | `dict[str, str]` | Freeform labels for arbitrary filtering (e.g., `{"cycle": "2", "gate": "dissent_present"}`). Max 32 keys, each key/value max 128 chars. |
| `started_at` | `datetime` (UTC) | Request dispatch time. |

**Invariants:**
- `request_id` matches ULID regex (`^[0-9A-HJKMNP-TV-Z]{26}$`).
- `started_at` is tz-aware UTC.
- `tags` size bounds checked.
- No validation of `session_id` / `workflow_id` / `agent` shape (freeform).

#### 3.3.3 `LLMResponse`

The raw token counts returned by the provider. **No Decimal fields. No cost. Only integer token counts.** This is the boundary: anything from this point in toward the tracker deals in money; anything from here out toward the LLM deals in tokens.

| Field | Type | Notes |
|-------|------|-------|
| `request_id` | `str` | Matches the `LLMRequest` it pairs with. |
| `input_tokens` | `int` | Fresh (non-cached) input tokens only. Provider translators must subtract any cached portion. |
| `output_tokens` | `int` | |
| `cache_read_tokens` | `int` | Default 0. |
| `cache_write_tokens` | `int` | Default 0. |
| `finished_at` | `datetime` (UTC) | |
| `stop_reason` | `Literal["stop", "length", "tool_use", "error", "aborted"]` | |
| `error_message` | `str \| None` | Populated when `stop_reason` is `"error"` or `"aborted"`. |

**Invariants:**
- All token counts `>= 0`.
- `finished_at >= request.started_at` (checked at tracker level, not here — `LLMResponse` doesn't know the request).
- If `stop_reason in ("error", "aborted")`, `error_message` must be non-empty.

#### 3.3.4 `CostAmount`

A single cost calculation split by token class, in a single currency. Every field is `Decimal`. **This is the type that never, ever sees a `float`.**

| Field | Type | Notes |
|-------|------|-------|
| `input` | `Decimal` | |
| `output` | `Decimal` | |
| `cache_read` | `Decimal` | |
| `cache_write` | `Decimal` | |
| `total` | `Decimal` | |
| `currency` | `Currency` | |

**Invariants:**
- All components `>= 0`.
- `total == input + output + cache_read + cache_write` — **exactly equal** under the Decimal context defined in §6. Not "within epsilon"; exactly equal.
- Each component has at most `QUANTUM_PLACES` (see §6) decimal places after rounding.

#### 3.3.5 `CostRecord`

The immutable fact table row for one tracked LLM call. Written exactly once. Never updated, never deleted (except by retention policy — see §7).

| Field | Type | Notes |
|-------|------|-------|
| `record_id` | `str` (ULID) | Primary key. |
| `request_id` | `str` | Unique. One-to-one with a completed `LLMRequest`/`LLMResponse` pair. |
| `provider` | `ProviderName` | |
| `model_id` | `str` | |
| `input_tokens` | `int` | |
| `output_tokens` | `int` | |
| `cache_read_tokens` | `int` | |
| `cache_write_tokens` | `int` | |
| `total_tokens` | `int` | Derived; stored for query performance. |
| `cost` | `CostAmount` | |
| `pricing_effective_from` | `datetime` (UTC) | Snapshot of which price row was used. |
| `pricing_snapshot_sha256` | `str` | SHA-256 of the snapshot JSON, for byte-exact audit. |
| `session_id` | `str \| None` | |
| `workflow_id` | `str \| None` | |
| `agent` | `str \| None` | |
| `parent_request_id` | `str \| None` | |
| `tags` | `dict[str, str]` | |
| `started_at` | `datetime` (UTC) | |
| `finished_at` | `datetime` (UTC) | |
| `latency_ms` | `int` | Derived: `(finished_at - started_at).total_seconds() * 1000`, rounded down. |
| `stop_reason` | `str` | |
| `error_message` | `str \| None` | |
| `cache_retention` | `CacheRetention` | |
| `created_at` | `datetime` (UTC) | Bookkeeping — when the row was written. |

**Invariants:**
- `total_tokens == input_tokens + output_tokens + cache_read_tokens + cache_write_tokens`.
- `cost.total == cost.input + cost.output + cost.cache_read + cost.cache_write` (exact Decimal equality).
- `latency_ms >= 0`.
- `finished_at >= started_at`.
- `record_id` and `request_id` are ULIDs.
- Storage enforces uniqueness of `request_id` — **cost records are idempotent on `request_id`**. A retry with the same `request_id` reads the existing record, does not write a new one, and does not recompute cost.

#### 3.3.6 `TimeRange`

| Field | Type | Notes |
|-------|------|-------|
| `start` | `datetime` (UTC) | Inclusive. |
| `end` | `datetime` (UTC) | Exclusive. |

**Invariants:** `end > start`; both tz-aware UTC.

#### 3.3.7 `Filter`

Composable filter used by `stream_events()` and the aggregator. Empty filter matches everything.

| Field | Type | Notes |
|-------|------|-------|
| `provider` | `ProviderName \| None` | |
| `model_id` | `str \| None` | |
| `session_id` | `str \| None` | |
| `workflow_id` | `str \| None` | |
| `agent` | `str \| None` | |
| `time_range` | `TimeRange \| None` | |
| `tag_match` | `dict[str, str]` | AND semantics — all entries must match. |
| `stop_reason` | `str \| None` | |

No invariants beyond field types. All-None filter = "all records".

#### 3.3.8 `CostSummary`

An aggregated rollup over some scope. Computed on demand by the aggregator (§4.3).

| Field | Type | Notes |
|-------|------|-------|
| `scope` | `AggregationScope` | |
| `scope_id` | `str` | `session_id`, `workflow_id`, agent name, `"all"`, etc. |
| `input_tokens` | `int` | |
| `output_tokens` | `int` | |
| `cache_read_tokens` | `int` | |
| `cache_write_tokens` | `int` | |
| `total_tokens` | `int` | |
| `cost` | `CostAmount` | |
| `request_count` | `int` | |
| `error_count` | `int` | Rows where `stop_reason in ("error", "aborted")`. |
| `first_request_at` | `datetime \| None` | None if `request_count == 0`. |
| `last_request_at` | `datetime \| None` | |
| `computed_at` | `datetime` (UTC) | |

**Invariants:**
- `total_tokens == sum of four token classes`.
- `cost.total == sum of four cost components`.
- `error_count <= request_count`.
- `first_request_at <= last_request_at` when both present.

#### 3.3.9 `CostEvent`

One event emitted by `stream_events()`.

| Field | Type | Notes |
|-------|------|-------|
| `event_id` | `str` (ULID) | Primary key in outbox. Sortable by emission time. |
| `event_type` | `Literal["record_created", "record_amended", "reconciliation_drift"]` | |
| `emitted_at` | `datetime` (UTC) | |
| `record` | `CostRecord \| None` | For `record_created` / `record_amended`. |
| `drift` | `ReconciliationDrift \| None` | For `reconciliation_drift`. |

**Invariants:** Exactly one of `record` or `drift` is non-None, matching `event_type`.

**Note on `record_amended`:** Records are immutable *as facts*, but the tracker reserves one escape hatch: when a reconciliation run detects that a CostRecord was calculated against the wrong pricing snapshot (e.g., a snapshot was loaded with a bad rate and later corrected), a `record_amended` event is emitted carrying a *new* `CostRecord` with a new `record_id` and a `parent_request_id == old.request_id`. The old record stays in storage as a soft-tombstone (a status column on `cost_records` — see §7). The system never overwrites a row in place.

#### 3.3.10 `Invoice` / `InvoiceLine` / `ReconciliationReport` / `ReconciliationDrift`

```
InvoiceLine:
  provider:          ProviderName
  model_id:          str
  period_start:      datetime (UTC)
  period_end:        datetime (UTC)
  input_tokens:      int
  output_tokens:     int
  cache_read_tokens: int
  cache_write_tokens:int
  amount:            Decimal
  currency:          Currency

Invoice:
  invoice_id:     str
  provider:       ProviderName
  period_start:   datetime (UTC)
  period_end:     datetime (UTC)
  lines:          list[InvoiceLine]
  total:          Decimal     # == sum(line.amount for line in lines)
  source_file:    str | None  # path to the parsed invoice file
  source_sha256:  str | None  # hash of the source file

ReconciliationDrift:
  provider:          ProviderName
  model_id:          str
  period_start:      datetime (UTC)
  period_end:        datetime (UTC)
  internal_tokens_by_class: dict[TokenClass, int]
  invoice_tokens_by_class:  dict[TokenClass, int]
  token_delta_by_class:     dict[TokenClass, int]  # invoice - internal
  internal_cost:     Decimal
  invoice_cost:      Decimal
  cost_delta:        Decimal   # invoice - internal
  drift_pct:         Decimal   # cost_delta / invoice_cost, 0–1

ReconciliationReport:
  invoice_id:        str
  reconciled_at:     datetime (UTC)
  lines:             list[ReconciliationDrift]
  total_internal:    Decimal
  total_invoice:     Decimal
  total_delta:       Decimal
  total_drift_pct:   Decimal
  status:            Literal["clean", "within_tolerance", "drift_detected", "critical_drift"]
```

**Status thresholds** (defaults; configurable):
- `clean` — `|total_drift_pct| < 0.001` (0.1%)
- `within_tolerance` — `0.001 <= |total_drift_pct| < 0.01` (1%)
- `drift_detected` — `0.01 <= |total_drift_pct| < 0.05` (5%)
- `critical_drift` — `|total_drift_pct| >= 0.05`

### 3.4 Storage schema (SQLAlchemy 2.0 mapped classes)

Mapped style: SQLAlchemy 2.0 `DeclarativeBase` with `Mapped[T]` annotations. Async engine via `create_async_engine`.

#### 3.4.1 `pricing`

Composite PK. Append-only (history preserved by adding new rows, not updating old ones).

```
CREATE TABLE pricing (
    provider              TEXT          NOT NULL,
    model_id              TEXT          NOT NULL,
    effective_from        TIMESTAMPTZ   NOT NULL,
    effective_until       TIMESTAMPTZ,
    currency              TEXT          NOT NULL DEFAULT 'USD',
    input_rate            NUMERIC(20,10) NOT NULL CHECK (input_rate >= 0),
    output_rate           NUMERIC(20,10) NOT NULL CHECK (output_rate >= 0),
    cache_read_rate       NUMERIC(20,10) NOT NULL CHECK (cache_read_rate >= 0),
    cache_write_rate      NUMERIC(20,10) NOT NULL CHECK (cache_write_rate >= 0),
    source_url            TEXT,
    snapshot_sha256       TEXT,
    PRIMARY KEY (provider, model_id, effective_from)
);

-- Partial index for the "current price" lookup hot path
CREATE INDEX ix_pricing_current
    ON pricing (provider, model_id)
    WHERE effective_until IS NULL;
```

SQLite dialect: `NUMERIC(20,10)` maps to SQLite's `NUMERIC` storage class. `TIMESTAMPTZ` maps to `TEXT` (ISO 8601). The repository layer handles serialization.

#### 3.4.2 `cost_records`

The fact table. Append-only.

```
CREATE TABLE cost_records (
    record_id              TEXT          PRIMARY KEY,    -- ULID, 26 chars
    request_id             TEXT          NOT NULL,
    provider               TEXT          NOT NULL,
    model_id               TEXT          NOT NULL,

    -- Token counts (BigInt — don't trust Int32 over long runtime)
    input_tokens           BIGINT        NOT NULL CHECK (input_tokens >= 0),
    output_tokens          BIGINT        NOT NULL CHECK (output_tokens >= 0),
    cache_read_tokens      BIGINT        NOT NULL CHECK (cache_read_tokens >= 0),
    cache_write_tokens     BIGINT        NOT NULL CHECK (cache_write_tokens >= 0),
    total_tokens           BIGINT        NOT NULL CHECK (total_tokens >= 0),

    -- Cost components (Numeric, never Float)
    cost_input             NUMERIC(20,10) NOT NULL CHECK (cost_input >= 0),
    cost_output            NUMERIC(20,10) NOT NULL CHECK (cost_output >= 0),
    cost_cache_read        NUMERIC(20,10) NOT NULL CHECK (cost_cache_read >= 0),
    cost_cache_write       NUMERIC(20,10) NOT NULL CHECK (cost_cache_write >= 0),
    cost_total             NUMERIC(20,10) NOT NULL CHECK (cost_total >= 0),
    currency               TEXT          NOT NULL DEFAULT 'USD',

    -- Pricing provenance
    pricing_effective_from TIMESTAMPTZ   NOT NULL,
    pricing_snapshot_sha256 TEXT         NOT NULL,

    -- Scope
    session_id             TEXT,
    workflow_id            TEXT,
    agent                  TEXT,
    parent_request_id      TEXT,
    tags                   JSONB         NOT NULL DEFAULT '{}',

    -- Timing
    started_at             TIMESTAMPTZ   NOT NULL,
    finished_at            TIMESTAMPTZ   NOT NULL,
    latency_ms             BIGINT        NOT NULL CHECK (latency_ms >= 0),

    -- Status
    stop_reason            TEXT          NOT NULL,
    error_message          TEXT,
    cache_retention        TEXT          NOT NULL,
    lifecycle_state        TEXT          NOT NULL DEFAULT 'active',  -- 'active' | 'amended'
    amended_by_record_id   TEXT,

    created_at             TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT ux_cost_records_request_id UNIQUE (request_id),
    CONSTRAINT ck_cost_total_sum CHECK (
        cost_total = cost_input + cost_output + cost_cache_read + cost_cache_write
    ),
    CONSTRAINT ck_token_total_sum CHECK (
        total_tokens = input_tokens + output_tokens + cache_read_tokens + cache_write_tokens
    )
);
```

**Indexes** (critical for R6 query perf):

```
CREATE INDEX ix_cost_records_started_at         ON cost_records (started_at DESC);
CREATE INDEX ix_cost_records_session            ON cost_records (session_id, started_at DESC) WHERE session_id IS NOT NULL;
CREATE INDEX ix_cost_records_workflow           ON cost_records (workflow_id, started_at DESC) WHERE workflow_id IS NOT NULL;
CREATE INDEX ix_cost_records_agent              ON cost_records (agent, started_at DESC) WHERE agent IS NOT NULL;
CREATE INDEX ix_cost_records_provider_model     ON cost_records (provider, model_id, started_at DESC);
CREATE INDEX ix_cost_records_tags_gin           ON cost_records USING gin (tags);  -- Postgres only
CREATE INDEX ix_cost_records_lifecycle          ON cost_records (lifecycle_state) WHERE lifecycle_state <> 'active';
```

SQLite drops partial/GIN indexes; `dialects.py` handles it.

#### 3.4.3 `events_outbox`

Transactional outbox for event streaming. Written in the **same transaction** as `cost_records` — this is the guarantee that no event is ever lost.

```
CREATE TABLE events_outbox (
    event_id       TEXT         PRIMARY KEY,   -- ULID
    event_type     TEXT         NOT NULL,
    record_id      TEXT,                       -- FK cost_records.record_id (nullable for non-record events)
    payload        JSONB        NOT NULL,      -- Pydantic-serialized CostEvent
    emitted_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    delivered_at   TIMESTAMPTZ                 -- null = undelivered
);

CREATE INDEX ix_events_outbox_undelivered
    ON events_outbox (emitted_at)
    WHERE delivered_at IS NULL;
```

Consumer model: `stream_events(filter)` polls (SQLite) or `LISTEN/NOTIFY`s (Postgres) on this table, filters in Python, yields matching events, and marks `delivered_at` for at-least-once semantics. Subscribers are responsible for idempotency on `event_id`.

#### 3.4.4 `reconciliation_reports` / `reconciliation_drift_lines`

```
CREATE TABLE reconciliation_reports (
    invoice_id        TEXT         PRIMARY KEY,
    provider          TEXT         NOT NULL,
    period_start      TIMESTAMPTZ  NOT NULL,
    period_end        TIMESTAMPTZ  NOT NULL,
    reconciled_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    total_internal    NUMERIC(20,10) NOT NULL,
    total_invoice     NUMERIC(20,10) NOT NULL,
    total_delta       NUMERIC(20,10) NOT NULL,
    total_drift_pct   NUMERIC(10,6)  NOT NULL,
    status            TEXT         NOT NULL,
    invoice_source    TEXT,                   -- original file path
    invoice_sha256    TEXT                    -- original file hash
);

CREATE TABLE reconciliation_drift_lines (
    line_id                    TEXT PRIMARY KEY,   -- ULID
    invoice_id                 TEXT NOT NULL REFERENCES reconciliation_reports(invoice_id),
    provider                   TEXT NOT NULL,
    model_id                   TEXT NOT NULL,
    period_start               TIMESTAMPTZ NOT NULL,
    period_end                 TIMESTAMPTZ NOT NULL,
    internal_input_tokens      BIGINT NOT NULL,
    internal_output_tokens     BIGINT NOT NULL,
    internal_cache_read_tokens BIGINT NOT NULL,
    internal_cache_write_tokens BIGINT NOT NULL,
    invoice_input_tokens       BIGINT NOT NULL,
    invoice_output_tokens      BIGINT NOT NULL,
    invoice_cache_read_tokens  BIGINT NOT NULL,
    invoice_cache_write_tokens BIGINT NOT NULL,
    internal_cost              NUMERIC(20,10) NOT NULL,
    invoice_cost               NUMERIC(20,10) NOT NULL,
    cost_delta                 NUMERIC(20,10) NOT NULL,
    drift_pct                  NUMERIC(10,6)  NOT NULL
);
```

#### 3.4.5 Optional `cost_summaries_cache`

For Stage 1 this table is **not** built. Summaries are computed on demand by the aggregator with the appropriate SQL `GROUP BY` and index coverage. We add a materialized cache if and only if Stage 2+ profiling shows that aggregation queries exceed budget. Premature caching is explicitly rejected (see CLAUDE.md "No speculative code").

---

## 4. API SURFACE CONTRACTS

### 4.1 `CostTracker` — the entry point

The `CostTracker` class is the single public object. All other components are constructed behind it and not exposed to callers.

```
CostTracker(
    storage_url: str,                      # e.g., "sqlite+aiosqlite:///praxis.db" or "postgresql+asyncpg://..."
    pricing_snapshot_dir: Path,            # path to pricing/snapshots/
    clock: Callable[[], datetime] = utcnow_default,
    engine_options: dict | None = None,
    telemetry: TelemetryConfig | None = None,
) -> CostTracker
```

Construction does **not** touch the database. Call `await tracker.initialize()` to open the engine, load the pricing catalog, and run any pending migrations (in dev only — in prod, migrations are a separate CI step).

```
async tracker.initialize() -> None
async tracker.close() -> None
```

The tracker is `async`-native. Callers must use `async with CostTracker(...)` or explicit `initialize()/close()` pairs.

### 4.2 `track_cost` — the hot path

```
async tracker.track_cost(
    request: LLMRequest,
    response: LLMResponse,
) -> CostRecord
```

**Pre-conditions (raised as `ValueError` or specific subclasses before any DB work):**
- `request.request_id == response.request_id`
- `response.finished_at >= request.started_at`
- `request.model_id` exists in the pricing catalog at `request.started_at`
- All `LLMRequest` and `LLMResponse` invariants hold
- If `response.stop_reason == "error"`, `error_message` is non-empty

**Post-conditions:**
- A `CostRecord` row is written to `cost_records` exactly once for `request_id`. If the same `request_id` is tracked twice (retry/idempotency), the second call returns the existing record **without** recomputing cost. This is a load-bearing idempotency guarantee for R7 — the cost for a given call is never re-derived from a price schedule that changed between retries.
- A `CostEvent` row (`event_type = "record_created"`) is written to `events_outbox` in the **same transaction**. Either both succeed or both roll back.
- The returned `CostRecord` is exactly the row that was persisted (not a pre-persist in-memory copy).

**Error cases:**

| Exception | Cause |
|-----------|-------|
| `UnknownModelError` | `model_id` not in pricing catalog for this provider. |
| `PricingGapError` | Model exists but no pricing row covers `started_at`. |
| `ValueError` | Pre-condition violation (e.g., mismatched `request_id`, negative tokens). |
| `StorageError` | DB write failed. Nothing persisted. Event not emitted. Caller may retry. |

**Performance budget:** <1 ms amortized excluding DB write latency. The DB write is async and I/O-bound; its latency is not counted against the <1 ms target for pure-compute overhead. The budget is measured as: `t_end - t_start` of `track_cost()` when the storage backend is a loopback mock. Property-based benchmarks in Murat's test plan.

**Idempotency strategy:** `INSERT ... ON CONFLICT (request_id) DO NOTHING RETURNING *` on Postgres. On SQLite, a transactional `SELECT ... FOR UPDATE` + `INSERT` (SQLite uses BEGIN IMMEDIATE to acquire the write lock). In both cases, the existing row is returned verbatim on conflict, not recomputed.

**Concurrency:** `track_cost` is safe to call concurrently from multiple coroutines. Two concurrent calls with the same `request_id` resolve to one persisted row; the loser's `track_cost` returns the winner's record. This addresses **M3** (async race conditions in concurrent cost aggregation).

### 4.3 Aggregation queries

```
async tracker.get_session_cost(session_id: str) -> CostSummary
async tracker.get_workflow_cost(workflow_id: str) -> CostSummary
async tracker.get_agent_cost(agent: str, time_range: TimeRange) -> CostSummary
async tracker.get_cost_summary(filter: Filter) -> CostSummary
```

**Pre-conditions:**
- The scope id is non-empty.
- For `get_agent_cost`, `time_range` is required and valid.

**Post-conditions:**
- Returns a `CostSummary` with the same currency as the underlying records (v1: always USD).
- `computed_at` is set to `clock()`.
- If no matching records exist: returns a summary with `request_count=0`, all token counts `0`, all cost components `Decimal("0")`, `first_request_at=None`, `last_request_at=None`. **Never returns `None`.**

**Rounding:** The aggregator sums `Decimal` components exactly. The result is then passed through the rounding rule in §6 only at the very end (when writing to storage / serializing to JSON). Sums do not accumulate rounding error because `Decimal` addition is exact.

**Error cases:**
- `ValueError` for invalid filters.
- `StorageError` on DB read failures. Read retries are at the caller's discretion.

### 4.4 Event streaming

```
async def stream_events(
    filter: Filter,
    from_event_id: str | None = None,
) -> AsyncIterator[CostEvent]
```

**Semantics:**
- Emits **at-least-once**. Subscribers deduplicate on `event_id` if exactly-once matters to them.
- Starts from `from_event_id` (inclusive) if provided; otherwise from the current watermark.
- Yields events as they land in `events_outbox`. Backpressure is cooperative: if the subscriber stops consuming, the outbox grows.
- Gracefully handles disconnection. Internal reconnect logic; subscribers see a continuous stream.
- Filter is applied in Python after the row is loaded — the outbox is global, filtering is in-process. For high-volume environments we can later add filter-aware outbox indexes, but Stage 1 prioritizes simplicity.

**Implementation detail — SQLite vs Postgres:**
- SQLite: `stream_events` polls `events_outbox` every `poll_interval_ms` (default 100 ms) for new rows where `delivered_at IS NULL` (or where `event_id > watermark` for replay).
- Postgres: Subscribes to a `cost_events` LISTEN channel. A trigger on `events_outbox` fires `pg_notify('cost_events', event_id)`. Notifications wake the subscriber, which then reads the row.

**Back-pressure and durability:**
- The outbox is bounded only by disk. A periodic sweeper marks delivered rows and deletes them after a retention window (default 7 days).
- If a subscriber dies mid-stream, delivered-but-not-acked events are re-delivered. This is at-least-once by design.

**Error cases:**
- `StorageError` on DB issues; iterator terminates with an exception after retry exhaustion.

### 4.5 Reconciliation

```
async tracker.reconcile(
    invoice: Invoice,
    tolerance_pct: Decimal = Decimal("0.001"),
) -> ReconciliationReport
```

**Pre-conditions:**
- `invoice.lines` is non-empty.
- `invoice.period_end > invoice.period_start`.
- `invoice.total == sum(line.amount for line in invoice.lines)` — verified as a pre-condition; if not, raises `ReconciliationError` without writing anything.

**Post-conditions:**
- Writes exactly one `reconciliation_reports` row and one `reconciliation_drift_lines` row per `InvoiceLine`, all in a single transaction.
- Emits a `CostEvent` with `event_type="reconciliation_drift"` for each drift line whose `drift_pct >= tolerance_pct`. Clean reconciliations emit no events.
- Returns the fully-populated `ReconciliationReport`.
- Does **not** amend existing `CostRecord` rows. Amendments are a separate, explicit operation (see `amend_record` below) — reconciliation only *detects* drift.

**How matching works:**
- For each `InvoiceLine`, the tracker queries `cost_records` where `provider = line.provider AND model_id = line.model_id AND started_at IN [line.period_start, line.period_end)`.
- Sums the four token counts and the cost components exactly (Decimal).
- Compares against the invoice line.
- Computes drift.

**Error cases:**
- `ReconciliationError` for malformed invoices.
- `StorageError` on DB failures.

### 4.6 Amendment (reserved, not Stage-1 P0)

```
async tracker.amend_record(
    record_id: str,
    reason: str,
    new_pricing: ModelPricing | None = None,
) -> CostRecord
```

Creates a new `CostRecord` that replaces the old one, keeping the old row as a tombstone (`lifecycle_state = "amended"`, `amended_by_record_id = new.record_id`). Emits a `record_amended` event. **Used only to fix bad pricing snapshots loaded into history; never used for arbitrary corrections.**

This API is included in the architecture for completeness and to future-proof the schema (the `lifecycle_state` column already exists), but implementation is deferred until we have a reason to amend. Listed here so Amelia knows not to need a schema migration later.

### 4.7 Async vs sync decisions

| Method | Sync/Async | Rationale |
|--------|-----------|-----------|
| `track_cost` | async | DB write on hot path. |
| `get_*_cost` | async | DB read. |
| `stream_events` | async | Obvious. |
| `reconcile` | async | Multi-row DB tx. |
| `math.*` helpers | sync | Pure Decimal compute. No I/O. |
| Pydantic model construction | sync | Pure Python. |
| Pricing catalog lookup | sync | In-memory dict after load. |
| Provider token extraction | sync | Pure translation. |

Every `async` method exists to cover an I/O boundary. Nothing is async for fashion's sake.

---

## 5. PROVIDER ABSTRACTION

### 5.1 The Protocol

```
class Provider(Protocol):
    """
    Structural type that every cost-tracker provider must satisfy.
    Providers translate vendor-native response payloads into the
    universal 4-class token schema. They never compute cost.
    """

    name: ClassVar[ProviderName]

    @staticmethod
    def supported_models() -> list[str]:
        """Return the set of model_ids this provider knows how to extract."""
        ...

    @staticmethod
    def extract_tokens(
        request: LLMRequest,
        raw_response: Any,      # provider-native response object
    ) -> LLMResponse:
        """
        Translate a provider-native response into an LLMResponse.
        Must not allocate Decimal. Must not touch pricing.
        """
        ...
```

`Provider` is a `typing.Protocol`, not an abstract base class. Third-party implementers do not need to inherit from anything; they just need to match the shape.

### 5.2 Per-provider responsibilities

Each built-in provider in `providers/{anthropic,openai,google}.py` is a module containing:
1. A class (or a module-level namespace) that satisfies `Provider`.
2. A `supported_models` list — the model ids this provider is canonical for.
3. An `extract_tokens` function that:
   - Accepts the raw response (the provider SDK's final message/response object).
   - Normalizes field names and handles cache/prompt-cache semantics correctly.
   - Returns an `LLMResponse` with exact integer counts.
4. Zero cost math. Zero Decimal. Zero pricing lookups. Providers are functions from bytes to integers.

#### 5.2.1 Anthropic token extractor — what it actually does

From the reference implementation (lines 11299–11305, 11425–11445):

```
input_tokens             = raw.usage.input_tokens
output_tokens            = raw.usage.output_tokens
cache_read_tokens        = raw.usage.cache_read_input_tokens or 0
cache_write_tokens       = raw.usage.cache_creation_input_tokens or 0
```

**Subtleties:**
- `input_tokens` from Anthropic is the *fresh* input count; cache-read tokens are accounted separately. No subtraction needed.
- `cache_creation_input_tokens` maps to our `cache_write_tokens` (the tokens that were *written into* the cache during this request).
- Anthropic updates usage incrementally in `message_delta` events. The extractor must consume the **final** `message_delta`, never an intermediate one. Tests must cover partial deltas to catch accidental mid-stream capture.
- `stop_reason` mapping: Anthropic's `"end_turn"` → `"stop"`, `"max_tokens"` → `"length"`, `"tool_use"` → `"tool_use"`, `"stop_sequence"` → `"stop"`, `"error"` (from stream error events) → `"error"`.

#### 5.2.2 OpenAI token extractor — the subtraction trap

From the reference implementation (line 18004–18007):

```
cached_tokens = raw.usage.input_tokens_details.cached_tokens or 0
input_tokens  = (raw.usage.input_tokens or 0) - cached_tokens   # <-- subtract
output_tokens = raw.usage.output_tokens or 0
cache_read_tokens  = cached_tokens
cache_write_tokens = 0                                          # OpenAI has no explicit cache-write metric
```

**This subtraction is the #1 porting trap for OpenAI.** OpenAI reports `input_tokens` as the sum of fresh + cached; cached tokens must be subtracted to get the fresh count. Test fixtures must include the `input_tokens_details.cached_tokens` case explicitly.

OpenAI has no direct `cache_write_tokens` equivalent in the public usage object. For now we report 0. Pricing is calibrated so OpenAI model pricing never charges for cache_write anyway — it's an Anthropic-first construct. Revisit if OpenAI adds it.

#### 5.2.3 Google Gemini token extractor

From the reference (line 10603–10606):

```
input_tokens             = raw.usage.inputTokens or 0      # camelCase in google-generative-ai
output_tokens            = raw.usage.outputTokens or 0
cache_read_tokens        = raw.usage.cacheReadInputTokens or 0
cache_write_tokens       = raw.usage.cacheWriteInputTokens or 0    # Gemini has this
```

**Subtleties:**
- Google uses camelCase in some SDKs (`inputTokens`) and snake_case in others (`input_tokens`). The extractor must handle both. Pattern: try canonical camelCase first, then fall back to snake_case. Reference pi-mono normalizes both at the SDK layer.
- Gemini exposes `cacheReadInputTokens` and `cacheWriteInputTokens` natively, unlike OpenAI.
- `totalTokens` is a reported convenience sum; the extractor **computes** `total_tokens` itself from the four classes to avoid trusting the provider's own sum (provider sums drift from reality in edge cases).

### 5.3 The extensibility contract — how to add a new provider

Adding a new provider (e.g., Bedrock in Stage 2) requires exactly these steps:

1. Create `providers/<name>.py` with a class/namespace satisfying `Provider`.
2. Implement `extract_tokens` against the provider's native response type. Use integer arithmetic only.
3. Add pricing entries for every supported model_id to `pricing/snapshots/<date>.json`.
4. Register the provider in `providers/registry.py` via `register_provider(MyProvider)`.
5. Add a `ProviderName` enum value (`models.py`).
6. Add a golden-file fixture capturing a representative raw response (`tests/fixtures/providers/<name>/*.json`).
7. Add a property-based test using Hypothesis that generates synthetic token counts, round-trips them through the extractor, and asserts equality (catches accidental arithmetic).

Nothing else changes. No core code edits. **The tracker itself never learns about the new provider** except via `ProviderName` and the pricing catalog. This is the architectural guarantee that the extensibility surface is exactly 7 files and nothing more.

### 5.4 Provider registry

`providers/registry.py` maintains a `dict[ProviderName, Provider]`. Registration happens at import time:

```
# providers/__init__.py
from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
from .google import GoogleProvider
from .registry import register_provider

register_provider(AnthropicProvider)
register_provider(OpenAIProvider)
register_provider(GoogleProvider)
```

The tracker calls `get_provider(name).extract_tokens(request, raw)` when a caller uses the convenience `track_raw_response()` helper (below). Callers who already have an `LLMResponse` skip providers entirely.

### 5.5 The `track_raw_response` convenience API

Most callers should construct `LLMResponse` themselves from their provider SDK. But for ergonomics, the tracker provides:

```
async tracker.track_raw_response(
    request: LLMRequest,
    raw: Any,
) -> CostRecord
```

which looks up `request.provider` → `Provider.extract_tokens(request, raw)` → calls `track_cost(request, response)`. Syntactic sugar, nothing more. Every line of it is covered by provider unit tests.

---

## 6. COST MATH STRATEGY

**This is the section where Pi-Mono either works or destroys trust permanently.** Every decision here is designed to make **M1** (floating-point cost calculations) and **M2** (rounding errors on cache token pricing) structurally impossible.

### 6.1 The one rule

**Every line of code in `praxis.kernel.cost` that participates in cost math uses `decimal.Decimal`. No exceptions. No `float`. No `int / int` (which returns `float`). No `math.*`. No NumPy. No Pandas. No JSON numeric parsing that goes through `float`.**

This rule is enforced in three ways:
1. **Type hints and mypy `--strict`.** `CostAmount` and `ModelPricing` rates are `Decimal`; any `float` assignment is a type error.
2. **A ruff rule** (custom or via `flake8-numerics` equivalent) that forbids `float(` and `/` between non-Decimal operands in `math.py` and callers.
3. **A property-based test** that asserts: after running `track_cost` on a million random request/response pairs, the sum of `cost_total` across all records equals the sum of the four components computed independently, byte-for-byte.

### 6.2 The Decimal context

All cost math runs in a **local** Decimal context. Never the default:

```
# math.py
from decimal import Decimal, Context, ROUND_HALF_EVEN, localcontext

COST_PRECISION = 28            # more than enough for USD at 10^-10 granularity
QUANTUM_PLACES = 10            # we persist 10 decimal places
QUANTUM        = Decimal("1e-10")
MILLION        = Decimal("1000000")
ZERO           = Decimal("0")

COST_CONTEXT = Context(
    prec=COST_PRECISION,
    rounding=ROUND_HALF_EVEN,    # banker's rounding — IEEE 754 default, unbiased
)
```

**Rounding policy:** `ROUND_HALF_EVEN` (banker's rounding).
- Unbiased: average of many roundings trends to zero error, whereas `ROUND_HALF_UP` systematically biases upward.
- Matches what most providers use internally for invoice totals.
- Matches IEEE 754 default (round-to-nearest-even). A reader who knows floating-point semantics immediately recognizes the choice.

**Rationale for `QUANTUM = 1e-10`:**
- A single token cost at the cheapest current rate (cache read on Haiku) is ~8 × 10⁻⁹ USD. We need enough precision that quantization is not the dominant error term.
- Storage columns are `NUMERIC(20, 10)` — ten places after the decimal point. The quantum matches the column.
- Rollup sums stay exact in this regime up to ~10^18 rows (well beyond any plausible horizon).

**Rounding timing:**
- Intermediate math runs **unquantized** in the 28-precision context. Do not round between multiplications and additions.
- Rounding to `QUANTUM` happens **only** at the final write to storage or JSON serialization. This is the single quantization point.
- Total is computed *after* rounding the four components, and the total equals the sum of the rounded components (exact Decimal equality under the chosen quantum).

**Why not round to cents (1e-2)?**
- Providers price in fractions of cents. Anthropic's cache_read_rate is $0.30/MTok = $3 × 10⁻⁷ per token. Rounding per-request cost to cents zeros out small requests entirely. Cumulative drift would be a lie.
- We store sub-cent precision and round only at display time in the dashboard layer (Step 1.3).

### 6.3 The only cost formula

The entire cost pipeline is expressed in one function:

```
def compute_cost(
    response: LLMResponse,
    pricing: ModelPricing,
) -> CostAmount:
    """
    The ONE place cost is computed. Every CostRecord.cost is derived from
    exactly one call to this function.

    Unit math:
      USD = tokens * (USD per million tokens) / 1,000,000

    Invariants enforced:
      - All arithmetic in COST_CONTEXT (ROUND_HALF_EVEN, prec=28)
      - All rates and amounts are Decimal
      - Final components quantized to QUANTUM
      - total == sum of four components (exact Decimal equality)
    """
    with localcontext(COST_CONTEXT):
        input_c  = Decimal(response.input_tokens)       * pricing.input_rate       / MILLION
        output_c = Decimal(response.output_tokens)      * pricing.output_rate      / MILLION
        cread_c  = Decimal(response.cache_read_tokens)  * pricing.cache_read_rate  / MILLION
        cwrite_c = Decimal(response.cache_write_tokens) * pricing.cache_write_rate / MILLION

        input_q  = input_c.quantize(QUANTUM,  rounding=ROUND_HALF_EVEN)
        output_q = output_c.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
        cread_q  = cread_c.quantize(QUANTUM,  rounding=ROUND_HALF_EVEN)
        cwrite_q = cwrite_c.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)

        total_q  = (input_q + output_q + cread_q + cwrite_q).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)

    return CostAmount(
        input=input_q,
        output=output_q,
        cache_read=cread_q,
        cache_write=cwrite_q,
        total=total_q,
        currency=pricing.currency,
    )
```

**This is the only function that multiplies a token count by a rate.** Anywhere else in the codebase that computes cost is a bug.

### 6.4 Places floating-point would be tempting — and why we do not use it

This list is enumerated so that Murat's review can verify each point is structurally impossible, not merely avoided.

| Temptation | Why the naive approach breaks | Praxis rule |
|------------|-------------------------------|-------------|
| **T1. `rate / 1_000_000` as `float`** | The reference code does exactly this (`usage.cost.input = (model.cost.input / 1000000) * usage.input`). Once cast to float, the error is baked in. | All rates are `Decimal`. All divisions are Decimal / Decimal in `COST_CONTEXT`. No implicit cast. |
| **T2. `tokens * rate` as Python `int * float`** | `int * float = float`. Any token count above ~9e15 becomes lossy. Even small counts introduce IEEE error. | `Decimal(tokens) * Decimal(rate)`. Always. |
| **T3. Summing `CostRecord.cost.total` with `sum()`** | Built-in `sum(floats)` accumulates IEEE error. Kahan summation exists but it's a compensation for a problem we don't have. | `Decimal` addition is associative and exact for any finite precision. Regular `sum()` is fine as long as every operand is `Decimal`. |
| **T4. JSON parsing a snapshot into `float`** | `json.loads("0.3")` returns `float(0.3)` — IEEE 754 rounding starts at parse time. | JSON pricing snapshots use **string-encoded** rates (`"input_rate": "3.0"`). Loader calls `Decimal(str_value)`. Never `Decimal(float_value)`. |
| **T5. `decimal.Decimal(float_value)`** | `Decimal(0.1) == Decimal("0.1000000000000000055511151231257827021181583404541015625")`. Disaster. | A `pydantic` field validator rejects any input that arrives as `float` and demands `str` or `Decimal`. Enforced at the model boundary. |
| **T6. Multiplying tokens by a per-thousand rate** | Some providers publish per-1K rates. Mixed units yield 1000x drift. | We normalize to USD/MTok at snapshot load time. The single unit of division is `/ MILLION`. |
| **T7. Cache-token pricing as "10% of base"** | A common shortcut: `cache_read = input_rate * 0.1`. Provider actually publishes a distinct rate; they may drift. | Pricing is always stored as four independent rates. **Never derived.** `cache_read_rate` is published by the provider on their pricing page and parsed as-is. |
| **T8. Free SDK usage structs reporting floats** | Some provider SDKs might serialize usage values as JSON numbers. | Token counts are `int`. If a provider reports a fractional token, the extractor `int()`-casts and logs a warning. Token fields are always integers in `LLMResponse`. |
| **T9. Percentage and ratio math (drift_pct, tax, etc.)** | Dividing two `Decimal` gives an exact quotient only if it's a terminating fraction. Otherwise we hit `InvalidOperation`. | All ratio math uses `COST_CONTEXT` with `prec=28`; `Decimal` division truncates to 28 sig figs rather than raising. Final quantization to a display precision at serialization. |
| **T10. Rounding halfway points** | `ROUND_HALF_UP` biases every tied value upward. For millions of requests, this compounds noticeably. | `ROUND_HALF_EVEN` (banker's rounding). The 5s split evenly. |
| **T11. Using `Decimal("NaN")`** | `Decimal` supports NaN — a foot-gun if token counts are `None`. | `int(None)` raises; we let it. No NaN path. Tests enumerate None explicitly. |
| **T12. Context bleed from global `decimal.setcontext()`** | If some other part of Praxis sets the global context, our math changes behavior. | We use `localcontext(COST_CONTEXT)` every time. Global context is never touched. |

### 6.5 Cache token pricing — the specific formulas

**Anthropic (Claude Opus 4.6, Sonnet 4.6, Haiku 4.5 — April 2026 as baseline):**
- `input_rate` — the headline per-1M price
- `output_rate` — typically 5x input
- `cache_read_rate = 0.1 × input_rate` (**as published**, parsed as a distinct field)
- `cache_write_rate` (short):  `1.25 × input_rate` (5-minute cache)
- `cache_write_rate` (long):   `2.00 × input_rate` (1-hour cache)

Note: Praxis stores a single `cache_write_rate` per `(provider, model_id, effective_from)` triple. If a provider has cache-write rates that depend on cache retention (Anthropic does), we express this as **two separate pricing rows** — one for `cache_retention=short` and one for `cache_retention=long`. The request's chosen `cache_retention` drives the lookup.

This is a design choice over the alternative "one row with a retention-indexed dict of rates". Reasons:
- Simpler SQL (`WHERE cache_retention_key = ?` is a straight filter).
- Cleaner snapshot files (one rate per key/value pair).
- Invariant checks are easier (each row has a single rate tuple).

**Updated `ModelPricing` key:**

```
PRIMARY KEY (provider, model_id, cache_retention_key, effective_from)
```

where `cache_retention_key ∈ {"short", "long", "none"}`. The `CostRecord` includes `cache_retention` so the correct row is found.

**OpenAI:**
- `cache_read_rate` — OpenAI publishes a separate cached-input rate.
- `cache_write_rate = 0` — no separate charge.
- `cache_retention_key = "short"` always (OpenAI has implicit short-lived cache).

**Google Gemini:**
- Similar to Anthropic but with vendor-specific ratios.
- Both `cache_read_rate` and `cache_write_rate` published.

### 6.6 Currency handling

USD is the only currency in v1. Every `CostAmount` carries `currency=Currency.USD`. Every `ModelPricing` row carries `currency=Currency.USD`. Every storage column has `DEFAULT 'USD'` with a CHECK constraint.

When v2 introduces non-USD providers, the rules are:
1. Conversion happens only at display time, never at `track_cost` time.
2. Historical conversion rates are stored with `effective_from` windows, like pricing.
3. Mixed-currency summation is an error — `CostSummary` is per-currency. Callers who want to combine must convert explicitly.

This is called out in §10 as an open question to validate with product before v2.

### 6.7 Why banker's rounding and not "truncate to N"

Considered alternatives:
- **Truncate to N decimal places:** biased downward (always toward zero), worst for reconciliation because we systematically under-report.
- **`ROUND_HALF_UP`:** unbiased at a single request, biased upward in the aggregate (ties are always rounded up). Over a million requests, measurable drift.
- **`ROUND_HALF_EVEN`:** unbiased over the aggregate. Ties split evenly. Also matches most provider internals. **Chosen.**

The difference between `ROUND_HALF_UP` and `ROUND_HALF_EVEN` is small for a single request but compounds in reconciliation comparisons. We want the cleanest possible drift profile, so banker's rounding is the right default.

### 6.8 What is not rounded

- **Token counts** — integers, no rounding.
- **Intermediate multiplications** — 28-digit precision, no rounding.
- **Pricing rates** — stored exactly as published, up to 10 decimal places.
- **Aggregations** — `Decimal` sums are exact; no rounding in `CostSummary` computation.
- **Drift percentages** — computed to 28 digits, quantized to 6 decimal places only at display time.

The quantization step is a single, final, auditable event.

---

## 7. STORAGE STRATEGY

### 7.1 SQLite-to-Postgres interface

One ORM class set. Two engines. The dialect differences are confined to `storage/dialects.py`.

**Shared:**
- SQLAlchemy 2.0 `DeclarativeBase`.
- `Mapped[T]` typed columns.
- Async session via `async_sessionmaker`.

**Dialect differences:**

| Concern | SQLite | Postgres |
|---------|--------|----------|
| **JSONB** | `TEXT` (serialized JSON) | `JSONB` |
| **Tag queries** | `json_extract(tags, '$.key') = ?` | `tags @> '{"key": "value"}'::jsonb` |
| **GIN index on tags** | None (full scan) | `CREATE INDEX ... USING gin (tags)` |
| **Partial indexes (`WHERE session_id IS NOT NULL`)** | Supported 3.8+, keep | Keep |
| **`NUMERIC(20,10)`** | SQLite stores as `NUMERIC` affinity | Real fixed-point |
| **`LISTEN/NOTIFY`** | Poll `events_outbox` every 100 ms | `pg_notify('cost_events', event_id)` + async `LISTEN` |
| **Write concurrency** | Writer lock (BEGIN IMMEDIATE) | Row-level MVCC |

`dialects.py` exposes two functions:
- `dialect_specific_upsert(session, table, conflict_cols, values) -> row` — the dialect-correct `ON CONFLICT` upsert.
- `dialect_specific_event_listener(engine, callback)` — returns an async context that either polls the outbox (SQLite) or listens to the notification channel (Postgres).

The tracker's core logic is agnostic; it asks `dialects.upsert(...)` and does not care.

### 7.2 Migrations

Alembic, configured with `async_engine` support. Migration strategy:

- **`0001_initial.py`** — creates `pricing`, `cost_records`, `events_outbox`, `reconciliation_reports`, `reconciliation_drift_lines`, all indexes. One commit. This is the Stage 1 P0 migration.
- Subsequent migrations are additive: new columns are nullable-with-default, new tables are additive, new indexes are concurrent on Postgres.
- **Never destructive in prod.** Alembic migrations that drop columns or change types require an explicit `--destructive` flag and a migration reviewer's sign-off. For Stage 1, no destructive migrations are expected.
- Dev workflow: `alembic upgrade head` runs automatically on `CostTracker.initialize()` if a dev env variable is set. In prod, it's an explicit step in the deployment pipeline.

### 7.3 Indexing for time-range queries

R6 demands query by `(agent, time_range)`, `(session_id)`, `(workflow_id)`, etc. Index design is driven by the expected query shapes:

| Query shape | Index used |
|-------------|-----------|
| `WHERE session_id = ?` | `ix_cost_records_session` |
| `WHERE workflow_id = ?` | `ix_cost_records_workflow` |
| `WHERE agent = ? AND started_at >= ? AND started_at < ?` | `ix_cost_records_agent` |
| `WHERE provider = ? AND model_id = ? AND started_at >= ? AND started_at < ?` | `ix_cost_records_provider_model` |
| `WHERE started_at >= ? AND started_at < ?` | `ix_cost_records_started_at` |
| `WHERE tags @> '{"key": "value"}'` (Postgres only) | `ix_cost_records_tags_gin` |

All scoped indexes are partial (`WHERE col IS NOT NULL`) where applicable, which keeps them small and forces Postgres to use them only when the column is actually queried.

**Index write cost:** Each `track_cost` insert updates 5–6 indexes. Postgres tests show ~50 μs per index update on SSD. The 1-ms target (R10) is computed excluding DB latency, so this is under the "DB side" budget. We revisit only if Stage 2 profiling finds this dominant.

### 7.4 Retention and archival

Stage 1 P0: **retain forever.** We want the full build dataset for the pre-sales case study ("we tracked every token from inception"). Storage cost for 1 million CostRecord rows is ~200 MB including indexes — irrelevant.

Stage 2+ will add:
- A configurable retention window for `events_outbox` (default: delete rows where `delivered_at IS NOT NULL` and `emitted_at < now() - interval '7 days'`).
- An archival target for `cost_records` older than 90 days: write to S3 as Parquet, delete from Postgres. Tracked as an open question (§10) — decision deferred until we have Stage 1 data to size it.

**No retention on `cost_records` in Stage 1.** This is deliberate: the pre-sales dataset is load-bearing.

### 7.5 Schema evolution philosophy

- `cost_records.tags` (JSONB) absorbs any new categorical dimension without a migration.
- New token classes (e.g., a hypothetical "thinking_tokens") require: add a column, add a rate, add a migration, update `compute_cost`. This is OK because token taxonomy changes are rare (the 4-class schema has been stable for ~2 years).
- New provider concepts (e.g., "pooled tokens", "distillation credits") may require more — flag as open questions at the time, do not try to pre-accommodate.

---

## 8. OBSERVABILITY HOOKS

### 8.1 OpenTelemetry integration

Every public async method on `CostTracker` opens an OTel span. Span attributes follow the semantic-convention-ish naming `praxis.cost.*`:

| Span | Attributes |
|------|-----------|
| `track_cost` | `praxis.cost.provider`, `praxis.cost.model_id`, `praxis.cost.session_id`, `praxis.cost.workflow_id`, `praxis.cost.agent`, `praxis.cost.input_tokens`, `praxis.cost.output_tokens`, `praxis.cost.cache_read_tokens`, `praxis.cost.cache_write_tokens`, `praxis.cost.total_usd` (as string, not float), `praxis.cost.cache_retention`, `praxis.cost.latency_ms` |
| `get_session_cost` / `get_workflow_cost` / `get_agent_cost` | Scope + `praxis.cost.request_count`, `praxis.cost.total_usd` |
| `reconcile` | `praxis.cost.invoice_id`, `praxis.cost.invoice_total`, `praxis.cost.internal_total`, `praxis.cost.drift_pct`, `praxis.cost.status` |
| `stream_events` | `praxis.cost.subscriber_id`, event counter |

**Important:** `praxis.cost.total_usd` is a **string** in OTel attributes, not a float. OTel attribute types are limited to `str/int/bool/Sequence[...]`; for cost we serialize as a Decimal `str`. Downstream consumers that want to plot it must parse it back to Decimal.

Traces from `kernel.cost` link to parent spans via the standard OTel context. Any Praxis caller whose span is active when calling `track_cost` will see the cost-tracker child span nested.

### 8.2 Logging

Structured logs (JSON) via `structlog`. Every cost event emits:

```
{"event": "cost_record_created",
 "record_id": "01J...",
 "request_id": "01J...",
 "provider": "anthropic",
 "model_id": "claude-opus-4-6",
 "session_id": "...",
 "workflow_id": "...",
 "agent": "winston",
 "input_tokens": 1234,
 "output_tokens": 567,
 "cache_read_tokens": 0,
 "cache_write_tokens": 0,
 "cost_total_usd": "0.0012340000",
 "latency_ms": 842,
 "ts": "2026-04-12T14:22:19.204Z"}
```

**Always** cost values as strings, never floats. A linter rule rejects any logger call that includes a Decimal formatted with `%f`.

**Log levels:**
- `INFO` — normal `cost_record_created`, reconciliation `clean`.
- `WARN` — reconciliation `within_tolerance`, non-zero drift that is below the action threshold, pricing gap detected at load, cache rate convention violated.
- `ERROR` — reconciliation `drift_detected` or `critical_drift`, storage failure, extraction failure.
- `DEBUG` — per-span entry/exit, detailed extraction decisions. Disabled in prod by default.

### 8.3 Prometheus metrics

Metrics exposed via `prometheus_client` (scraped by the shell layer's `/metrics` endpoint):

```
praxis_cost_records_total{provider, model_id, stop_reason}               Counter
praxis_cost_usd_total{provider, model_id}                                Counter (observed in cents as float — see below)
praxis_cost_tokens_total{provider, model_id, class}                      Counter
praxis_cost_track_latency_seconds{provider}                              Histogram (buckets: 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1)
praxis_cost_reconciliation_drift_pct{provider}                           Gauge
praxis_cost_outbox_depth                                                 Gauge
praxis_cost_outbox_undelivered                                           Gauge
praxis_cost_errors_total{error_type}                                     Counter
```

**Important exception to the "no float" rule:** Prometheus clients natively use `float` for counter and gauge values. For metrics export only, we cast Decimal to float **as the final step in the metric update**, with an explicit call to `float(cost.total)` and a comment explaining that this is a metrics-only boundary. The authoritative number lives in the DB as Decimal; the metric is an approximation for observability.

This is the only place in the module where `float()` appears. It is allowed exactly here, with exactly this comment: `# METRICS BOUNDARY: approximate for observability; authoritative Decimal in cost_records`.

### 8.4 Health check

`CostTracker.health()` returns:
```
{
    "status": "healthy" | "degraded" | "unhealthy",
    "db_reachable": bool,
    "outbox_undelivered_count": int,
    "pricing_catalog_loaded": bool,
    "pricing_catalog_age_seconds": int,
    "last_track_cost_age_seconds": int | None,
}
```

Used by the shell's `/health/cost` endpoint and by Kubernetes liveness probes.

### 8.5 Pre-sales hook

One convenience method exists specifically for the Praxis "Built with Praxis" dashboard (per the build plan's self-demonstrating savings goal):

```
async tracker.get_lifetime_cost() -> CostSummary
```

Returns a `CostSummary` over every `cost_record` in the database, from the beginning of time. Implemented as a single aggregated query. Cached in memory for 60 seconds to avoid DB thrash when the public dashboard polls. This is Stage 1's single pre-sales affordance; richer pre-sales breakdowns happen in the dashboard layer.

---

## 9. TESTABILITY NOTES FOR MURAT

The test plan is Murat's to design; this section exists to tell Murat what the architecture has made possible, where the risk lives, and which fixtures need to exist. Pi-Mono is RPN 20 — nothing is higher priority than getting the test strategy right.

### 9.1 Risk-to-test mapping

| Murat risk | Test type | Coverage target |
|-----------|-----------|-----------------|
| **M1. Floating-point cost calculations** | Property-based (Hypothesis) + static typing | 100% — zero floats in any cost-math path |
| **M2. Rounding errors on cache token pricing** | Golden file + property-based + parametrized fixtures | 100% of cache-bearing pricing rows |
| **M3. Async race conditions** | Concurrent stress test + idempotency property tests | 100% on `track_cost` idempotency |
| **M4. Cross-provider price drift** | Reconciliation fixture against real invoices | Every active `(provider, model_id, effective_from)` tuple |
| **M5. Currency precision / fractions of a cent** | Property-based with extreme-ratio inputs | Full `compute_cost` domain |

### 9.2 Property-based tests (Hypothesis)

The architecture is designed to make every public function a clean target for property-based testing. A non-exhaustive list of properties Amelia should implement against (via `hypothesis`):

**P1. Zero tokens → zero cost.**
```
compute_cost(response_with_all_zeros, any_pricing).total == Decimal("0")
```

**P2. Cost is non-negative.** For any non-negative `LLMResponse` and non-negative `ModelPricing`, `compute_cost(...).total >= Decimal("0")`.

**P3. Cost total equals sum of components (exact equality).**
```
cost = compute_cost(resp, pricing)
assert cost.total == cost.input + cost.output + cost.cache_read + cost.cache_write
```
**Byte-exact equality under `Decimal`.** Not "close to".

**P4. Linearity in tokens.** For any `resp, pricing, k`:
```
compute_cost(resp * k, pricing).total == k * compute_cost(resp, pricing).total
```
up to one quantum of rounding drift (tolerance `4 * QUANTUM`, since up to four components may each round separately).

**P5. Associativity of aggregation.** For any three records:
```
sum([r1.cost.total, r2.cost.total, r3.cost.total]) == 
    sum([r2.cost.total, r3.cost.total, r1.cost.total])
```
(trivially holds for Decimal, but the test pins it).

**P6. Idempotency of `track_cost`.** Tracking the same `request_id` twice returns the same `record_id` and the same cost:
```
r1 = await tracker.track_cost(req, resp)
r2 = await tracker.track_cost(req, resp)
assert r1 == r2
```

**P7. Provider extraction is pure.** For any `extract_tokens(req, raw)` call, repeated invocation returns the exact same `LLMResponse`. No hidden state.

**P8. Reconciliation is exact on synthetic invoices.** If you generate 1000 records, sum them into a synthetic invoice, and reconcile, the result must be `status="clean"` and `total_delta == 0`.

**P9. Concurrent `track_cost` with the same `request_id` is safe.** Using `asyncio.gather(*[track_cost(req, resp) for _ in range(100)])` must produce exactly one row and one event.

**P10. Pricing gap detection.** For a model with pricing rows `[(t0, t1), (t2, t3)]` where `t2 > t1`, a request at time `t1.5` raises `PricingGapError`. This is the test that proves gaps are caught at runtime, not silently filled.

**P11. Price step transition.** For a model with pricing rows `[(t0, t1, rate_A), (t1, None, rate_B)]`, a request at `t1 - 1ms` uses `rate_A` and a request at `t1 + 1ms` uses `rate_B`. Strict.

Hypothesis strategies (sketched in the test plan Murat will write):
- `st.integers(min_value=0, max_value=10_000_000)` for token counts
- `st.decimals(min_value="0.00", max_value="1000.00", places=4, allow_nan=False, allow_infinity=False)` for rates
- `st.datetimes(min_value=..., max_value=..., timezones=st.just(UTC))` for timestamps
- `st.one_of(st.none(), st.text(alphabet="abc123", min_size=1, max_size=26))` for scope ids

### 9.3 Golden-file regression fixtures

Golden files are the regression net for extraction and cost math. They live in `tests/golden/` and are checked into git.

**Directory layout:**

```
tests/golden/
├── providers/
│   ├── anthropic/
│   │   ├── opus_4_6_simple.json           # raw response
│   │   ├── opus_4_6_simple.expected.json  # expected LLMResponse
│   │   ├── opus_4_6_with_cache.json
│   │   ├── opus_4_6_with_cache.expected.json
│   │   ├── sonnet_4_6_tool_use.json
│   │   ├── sonnet_4_6_tool_use.expected.json
│   │   ├── sonnet_4_6_error.json
│   │   ├── sonnet_4_6_error.expected.json
│   │   ├── haiku_4_5_long_cache.json
│   │   └── haiku_4_5_long_cache.expected.json
│   ├── openai/
│   │   ├── gpt_5_responses_cached_input.json           # CRITICAL: cached tokens subtraction
│   │   ├── gpt_5_responses_cached_input.expected.json
│   │   └── ...
│   └── google/
│       ├── gemini_3_1_pro_cache_read_write.json
│       └── gemini_3_1_pro_cache_read_write.expected.json
├── cost_math/
│   ├── zero_tokens.py                     # test case as data
│   ├── extreme_cache_write.py             # M2: cache_write_rate = 125% of input
│   ├── cache_only_no_input.py             # M2: request that is entirely cache-read
│   ├── rounding_halfway.py                # M2: cost ending in .5
│   ├── linear_1000x.py                    # P4 at 1000x token scale
│   └── ...
└── pricing/
    ├── anthropic_2026_04.json             # seed snapshot
    ├── openai_2026_04.json
    └── google_2026_04.json
```

**Update workflow:** Golden files are regenerated only via `python -m praxis.kernel.cost.tests.update_golden` with an explicit `--confirm` flag. Any PR that modifies golden files without running this script is rejected.

**Why golden files at all?** Property-based tests catch logic errors. Golden files catch regression against **actual provider payloads**. When Anthropic renames a field from `cache_creation_input_tokens` to `cache_write_input_tokens` in SDK v3, the golden file breaks immediately; a property test would not notice.

### 9.4 Reconciliation tests against real invoices

This is the capstone test for M4 (pricing drift). Protocol:

1. Nightly job downloads Andrey's actual provider invoices (Anthropic, OpenAI, Google) via their billing APIs.
2. The job loads the invoices as `Invoice` objects.
3. Runs `tracker.reconcile(invoice)` against the real `cost_records` for the same period.
4. Asserts `status in ("clean", "within_tolerance")`. Any `drift_detected` or `critical_drift` opens a ticket.

**Bootstrapping:** Until Praxis is running in production, Murat's plan should include a manual reconciliation test using:
- One historical invoice PDF (manually parsed into an `Invoice` JSON).
- Synthetic `cost_records` reconstructed from the build-log (badlogic/pi-mono output files or Claude Max usage exports).
- A CI job that runs this reconciliation on every PR that touches `pricing/snapshots/`.

### 9.5 Edge cases to cover

Murat's plan should explicitly enumerate and cover these:

1. **Zero-token response.** Some providers return a response with 0 input and 0 output tokens (especially on tool-use continuation messages). Must not divide by zero; must return a zero cost.
2. **All tokens are cache reads.** A full cache hit, zero input, zero output. Cost is `cache_read_tokens * cache_read_rate / 1e6`, nothing else.
3. **Negative token count from a broken SDK.** Must be rejected at the `LLMResponse` boundary with a `ValueError`. Do not let a negative count reach `compute_cost`.
4. **Pricing rate of exactly zero.** A model with `input_rate=0` (maybe a free-tier preview). Must compute zero input cost without raising `DivisionByZero`. `Decimal(0) / Decimal("1000000")` is `Decimal("0")`, not an error — verified.
5. **Extremely large token count** (10⁹). `Decimal` handles this; test it.
6. **Pricing row with `effective_until = effective_from + 1ms`.** A one-millisecond window. Does the catalog behave correctly at the edge? Yes, half-open intervals; verify with a fixture.
7. **Two pricing rows with the same `effective_from`.** This is a data error — catalog load raises `PricingGapError` (overlap detection).
8. **Gap between two pricing rows.** A request in the gap raises `PricingGapError`. Request outside the gap works. Verify.
9. **Concurrent snapshot reload.** If the catalog is reloaded mid-flight, in-flight `track_cost` calls must either use the old snapshot or the new one, never a mix. Architecturally enforced by loading a new catalog into a fresh dict and swapping the reference atomically.
10. **UTC-naive datetime.** Rejected at the model boundary. Verify.
11. **DST transition / leap second.** UTC everywhere means DST is impossible; leap seconds are handled by the OS — we trust them. No special path.
12. **ULID collision.** ULID includes 10 bytes of randomness; collision is ~1-in-2⁸⁰. Do not test for collision (astronomically improbable); do assert uniqueness constraint on `record_id`.
13. **Invoice with a model_id we've never seen.** Reconciliation emits a warning and treats it as zero internal cost / full invoice cost (100% drift on that line). Status is `critical_drift` for the report.
14. **Invoice with a period that partially overlaps our data.** Query bounds are inclusive-exclusive; partial-period records are included iff `started_at ∈ [period_start, period_end)`.
15. **Cost that quantizes to 0 but is non-zero before rounding.** Extremely small requests (1 cache_read_token on Haiku). Rounding policy should preserve exactness: since we round to 10⁻¹⁰ and a Haiku cache_read of 1 token is ~8 × 10⁻¹⁰, the rounded value is either `0` or `1e-10` depending on banker's rounding direction. Verify with a concrete fixture.
16. **Response with cache_write_tokens but cache_retention="none".** Logically impossible; provider misbehavior. Log warning; accept and bill the cache_write tokens (they were billed by the provider).
17. **Snapshot file with a numeric (not string) rate.** Loader raises `ValueError` at load time with a clear error. Never falls back to float.

### 9.6 Test coverage targets

R11 demands ≥95% line coverage for Pi-Mono as a high-risk component. The architecture is designed so that this target is achievable without heroic effort:

- `math.py` — near-100% coverage via property tests.
- `providers/*` — 100% via golden file fixtures per provider per stop-reason.
- `storage/*` — 95%+ via round-trip tests against both SQLite and Postgres (Docker container in CI).
- `tracker.py` — 95%+ via integration tests that exercise every public method with both success and error paths.
- `events.py`, `reconciliation.py` — 95%+ via end-to-end tests.

The one file where coverage is less meaningful is `telemetry.py` — OTel instrumentation is hard to cover without spinning up a collector. Target: 85% with the remaining 15% explicitly justified per-line.

### 9.7 Stress / performance test

One non-property benchmark, used to verify R10 (<1 ms overhead):

```
# Benchmark: 100_000 track_cost calls against a mock storage.
# Mock storage records to memory; measures pure compute.
# Target: median <1 ms, p99 <2 ms.
```

Run in CI on every PR that touches `math.py`, `compute_cost`, `tracker.py`, or `providers/*`. Regressions fail the build.

### 9.8 What the architecture makes easy vs hard to test

**Easy:**
- `compute_cost` — pure function, one line of business logic. Trivially property-testable.
- Providers — pure translation functions, golden files nail them down.
- Pricing catalog lookup — pure dict lookup against a loaded snapshot.
- Idempotency — `request_id` uniqueness is a DB constraint; tests can verify with concurrent writes.

**Harder (but handled):**
- Async race conditions — architectural mitigation via `ON CONFLICT DO NOTHING` means the test is a stress test, not a lock-dance.
- Event stream integration — covered by integration tests that subscribe to `stream_events` and verify delivery after `track_cost`.
- Storage dialect divergence — Docker-based CI runs the full suite against both SQLite and Postgres.

**Not cleanly testable without real data (deferred to reconciliation job):**
- Actual provider pricing correctness. We can verify our math is internally consistent, but only real invoices prove we're charging what the provider is charging. This is exactly why the reconciliation cadence exists.

---

## 10. OPEN QUESTIONS

These are decisions that need stakeholder input or real data before we commit. Murat and Amelia should not block on these for Stage 1 P0; defaults are listed, decision owners are named.

### 10.1 Currency and multi-currency readiness

**Question:** Stage 1 is USD-only. Should the architecture prove out multi-currency handling now or defer?

**Default:** Defer. Keep the `currency` column and field as forward-compat, but implement only USD. Multi-currency is a v2 concern.

**Who decides:** Andrey (product). Surface when v2 has a real non-USD customer.

### 10.2 Retention policy for `cost_records`

**Question:** Stage 1 keeps everything forever. At what scale does this break?

**Back-of-envelope:** 1M records ≈ 200 MB with indexes. 100M records ≈ 20 GB. At 10 workflows per day on a fully-loaded Praxis system, 100M takes ~30 years. Not a Stage 1 problem.

**Default:** No retention. Revisit if/when Stage 4 pushes record volume over 10M rows.

**Who decides:** Andrey + whoever is running Praxis in production at scale.

### 10.3 Amendment API usage policy

**Question:** The schema supports `lifecycle_state='amended'` and an amendment API is sketched in §4.6. Should it be exposed in Stage 1 or held back?

**Default:** Schema is there (zero cost), API is not wired up. Exposed in a later stage once we have a real reason to amend (e.g., a pricing snapshot error).

**Who decides:** Winston (me) + Murat on risk signal.

### 10.4 Dashboard streaming cadence

**Question:** The dashboard (Step 1.3) polls `stream_events` or `get_lifetime_cost`. What's the right cadence?

**Default:** `stream_events` for real-time numbers; `get_lifetime_cost` cached 60s for the public totals. Revisit after the first dashboard iteration.

**Who decides:** Whoever owns Step 1.3 (Sally, our UX lead, or whichever agent takes dashboard design).

### 10.5 Pricing snapshot cadence and ownership

**Question:** How often do we snapshot provider pricing? Who owns the update?

**Default:** Monthly manual snapshot (the first of each month UTC) for Stage 1. Stage 2 adds an automated scraper. Until then, it's a checklist item in the Praxis release process.

**Who decides:** Andrey. Flag when a provider changes prices and we're slow to react.

### 10.6 Cache retention semantics for non-Anthropic providers

**Question:** Our `CacheRetention` enum has `short`/`long`/`none`. OpenAI and Google have their own semantics. How do we map?

**Research needed:** Read current OpenAI and Google cache documentation (mid-2026) and decide whether to extend `CacheRetention` or map onto existing values. Default mapping:
- OpenAI has implicit short-lived cache. All OpenAI requests: `CacheRetention.SHORT`.
- Google Gemini has context caching with configurable TTLs. Requires a first-cut mapping.

**Who decides:** Winston (me) in a follow-up before OpenAI/Google are added to the provider registry. Before then, `CacheRetention` is Anthropic-semantic; other providers store the value but it affects nothing.

### 10.7 Tagging conventions

**Question:** The `tags` dict is freeform. Without conventions, tag hygiene will diverge across Praxis components.

**Default:** Document a minimal convention in the Praxis internal docs:
- `cycle: "1" | "2" | "3"` — MAC cycle
- `gate: <gate_name>` — quality gate context
- `role: <role>` — e.g., `"production" | "review"` for information asymmetry

No enforcement in Stage 1; enforcement added when a dashboard wants to filter on them consistently.

**Who decides:** Winston (me) in coordination with whoever designs the MAC in Stage 5.

### 10.8 Observability: do we need per-agent Prometheus labels?

**Question:** `praxis_cost_usd_total{agent}` — is this worth the cardinality?

**Default:** No agent label on Prometheus counters (would blow up cardinality with 16+ agents × 3+ providers × 10+ models). Agent-level cost lives in the DB and is queried on demand. Prometheus stays coarse: `(provider, model_id, stop_reason)`.

**Who decides:** Winston (me).

### 10.9 Is Stage 1 P0 just the hot path, or also reconciliation?

**Question:** The prompt lists reconciliation in the API minimums (R4). But reconciliation is slow to bootstrap (needs invoices). Should reconciliation implementation slip to Stage 2?

**Default:** API and data model land in Stage 1. *Implementation* of real-invoice reconciliation lands in Stage 2 (we won't have real invoices to reconcile against until we've been running through Pi-Mono for a few weeks anyway). The `reconcile` method is implemented against synthetic invoices (property test P8) to exercise the code path — that is enough proof that the architecture supports real reconciliation.

**Who decides:** Andrey. Flagged for explicit confirmation before Amelia cuts scope.

### 10.10 Distributed deployment concerns

**Question:** Does Pi-Mono assume a single-process writer?

**Default:** Multi-process safe by virtue of the DB unique constraint on `request_id` — if two workers track the same request, the second sees the conflict and returns the first's row. No distributed lock needed.

Multi-process concerns show up only if:
- Multiple writers race on the same `events_outbox` LISTEN/NOTIFY — handled by Postgres correctly.
- Pricing catalog load is per-process and can drift between processes — solution is to pin the catalog version via `snapshot_sha256` and refuse to write records if two processes disagree. Stage 1 P0 is single-process (dev + single-node prod), so this is a Stage 4+ concern.

**Who decides:** Deferred to the Stage where we run multiple Pi-Mono writers.

### 10.11 What does "same request" mean under retry?

**Question:** A caller retries the same logical request after a network timeout. Same `request_id`, potentially different timing, potentially different usage counters (if the first call actually succeeded server-side and the second is a dup). What is correct?

**Default:** Idempotent on `request_id`. The first successful `track_cost` wins; subsequent calls with the same `request_id` return that record verbatim. The caller is responsible for generating a fresh `request_id` if they want two separate bills. This is documented in the public docstring for `track_cost`.

**Who decides:** Winston (me). Confirmed.

---

## 11. REQUIREMENT → DESIGN TRACEABILITY MATRIX

Every design decision in this document is traceable to a Praxis requirement or a Murat risk. The grid below is the minimum audit surface; anything not listed should be justified or removed.

### 11.1 Praxis requirements (R-series)

| # | Requirement | Addressed in |
|---|-------------|--------------|
| R1 | Track input/output/cache tokens per request | §3.3.5 `CostRecord` fields; §5.2 extractors |
| R2 | Providers: Anthropic, OpenAI, Google Gemini at launch | §5.2.1–5.2.3; `ProviderName` enum §3.2 |
| R3 | Extensible provider interface | §5.1 Protocol; §5.3 contract; §5.4 registry |
| R4 | Per-request, session, workflow, agent aggregation | §3.3.8 `CostSummary`; §4.3 aggregator API; §3.4.2 indexes |
| R5 | Real-time cost event stream | §3.3.9 `CostEvent`; §4.4 stream API; §3.4.3 outbox |
| R6 | Historical queries by time/agent/workflow/provider | §4.3 `Filter`-based queries; §3.4.2 indexes |
| R7 | Decimal for all cost math, never float | §6 in its entirety |
| R8 | SQLite dev, Postgres-ready, async | §3.4 schema; §7.1 dialects; §4 async methods |
| R9 | Zero runtime dependencies on other Praxis components | §2.2 dependency rules (hard rule 4) |
| R10 | <1 ms overhead per tracked call | §4.2 budget; §9.7 benchmark; §3.4.2 index sizing |
| R11 | Test coverage ≥ 95% | §9.6 targets; architecture designed for testability (§9.8) |

### 11.2 Murat risks (M-series)

| # | Risk | Mitigations |
|---|------|-------------|
| M1 | Floating-point cost calculations | §6.1 "the one rule"; §6.3 `compute_cost`; §6.4 T1-T12 table; §9.2 property tests; ruff / mypy enforcement |
| M2 | Rounding errors on cache token pricing | §6.2 banker's rounding; §6.3 single quantization point; §6.5 explicit cache rate formulas; §9.3 golden fixtures for cache cases; edge case §9.5.15 |
| M3 | Async race conditions in concurrent aggregation | §4.2 idempotency on `request_id`; §3.4.2 unique constraint; §9.2 property P6 and P9 |
| M4 | Cross-provider price drift | §3.3.1 versioned pricing + `effective_from`; §3.3.5 pricing provenance in every record; §4.5 reconciliation API; §9.4 real-invoice reconciliation |
| M5 | Currency precision / fractions of a cent | §6.2 `QUANTUM = 1e-10`; §3.4.2 `NUMERIC(20, 10)`; §9.5 edge case 15 |

### 11.3 Design decisions not driven by R or M

Decisions made for maintainability, clarity, or developer ergonomics that are not directly mandated:

| Decision | Rationale |
|----------|-----------|
| ULID for IDs | Time-sortable, human-readable enough for logs, portable across DBs |
| `structlog` over stdlib logging | JSON-first, structured context |
| Append-only `pricing` table | Auditable history without migration pain |
| Provider `Protocol` over ABC | Minimum friction for third-party providers |
| Transactional outbox for events | Exactly-the-right amount of guarantee for at-least-once semantics |
| Single `compute_cost` function | One place to audit, one place to break, one place to test |
| SQLite in dev / Postgres in prod | Boring choice; developer ergonomics |
| `frozen=True` Pydantic models by default | Immutability makes reasoning about concurrency trivial |
| No speculative caching of summaries | Premature optimization avoided; add if profiling demands |

---

## 12. HANDOFF

This document is ready for Murat's risk-based test strategy review.

**For Murat:** The test strategy you design will:
1. Turn §9 (Testability Notes) into a concrete test plan with owners and fixtures.
2. Design the property-based test suite for `math.py` and `providers/*`.
3. Specify the golden-file capture format and the update workflow.
4. Define the reconciliation test cadence (manual for Stage 1, automated for Stage 2).
5. Set quality gates for the ≥95% coverage target per module.
6. Identify any additional failure modes this architecture has not anticipated.

**For Amelia (after Murat):** You will implement against this document and Murat's test plan. Both live under `_bmad-output/implementation-artifacts/praxis/pi-mono/`. Nothing in §6 (Cost Math Strategy) is negotiable; everything else should be read for intent first and asked-about if anything is unclear. If a design decision seems wrong, flag it to Winston (me) before writing code — we adjust the doc, not the code.

**For Andrey:** Stage 1 Step 1.1 is now specified. Open questions §10.1–10.11 need your input at the timelines noted. Two items are urgent:
- §10.9 — confirm reconciliation implementation slips to Stage 2 (my recommendation).
- §10.5 — confirm monthly manual snapshot process for pricing.

Everything else can wait until the test plan and first implementation land.

**Design is ready for Murat's review.**

— Winston
