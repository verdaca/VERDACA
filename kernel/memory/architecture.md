# Stage 3 — Memory & Learning Layer: Architecture Decision Document

**Author:** Winston (Architect) — `/bmad-agent-architect`
**Stage:** 3.1 (Pipeline.md)
**Status:** Draft v0.1 — skeleton + privacy spine + Stages 1-2 integration; reference-derived sections filled in progressively
**Binding input:** `_bmad-output/implementation-artifacts/praxis/memory/requirements.md` (58 numbered requirements + 6 ratified blocker decisions)
**Language/tooling:** Python 3.12, Pydantic v2 (frozen), SQLAlchemy 2.x async, Alembic, pgvector
**Namespace:** `praxis.kernel.memory` (peer of `praxis.kernel.cost`, `praxis.kernel.compression`)
**Reference reading protocol:** Universal Sequential Reference Reading (Pipeline §4.6). This doc was written in the order: requirements.md → Pi-Mono arch → Compression arch → skeleton → Beads → Atelier → Mem0 (selective) → integration pass.

**Requirement-coverage index:** Every binding requirement (#1–#58) from `requirements.md` is referenced by number in the section where it is honored. The integration pass (§12) verifies no requirement is unclaimed.

---

## 0. Design Principles (Non-Negotiable)

These principles are derived from the Round 2 FMEA hardening and the 6 ratified blocker decisions. They are NOT design preferences — they are structural invariants that every section below must honor.

1. **Tenant boundary = process boundary.** One tenant per Python process lifetime (ratified decision B1 — Managed Single-Tenant). No `WHERE tenant_id = ?` filtering; the Postgres instance itself is the boundary. `tenant_id` remains on every API method as defense-in-depth (#1) but the enforcement is structural, not query-based.
2. **Embeddings are personal data** (ratified decision B2). Delete cascades purge embeddings synchronously (#34). Quarantine strips embeddings in-place (#35 — FM3.10 override of Round 1). No embedding survives deletion or quarantine in any tier of storage (database, cache, backup, log).
3. **Unified facade, three backends.** Application code talks to ONE `Memory` interface (#8). Beads / Mem0 / Atelier are implementation details. No `_internal/` helper leaks into application code (#9).
4. **No raw query builders.** All retrieval paths are named typed methods on the facade. No `find_where(sql)`, no `query(criteria_dict)` with unchecked predicates. Every method has a compile-time-checked Pydantic input and output (#8).
5. **Writes are method-implicit on scope.** `store_task_outcome()` always writes to TENANT scope. There is no `scope` parameter on any write method. Seed corpus writes are a separate offline tool (#12, #16).
6. **Cross-tenant retrieval does not exist as a code path.** Not a feature flag, not a config, not reachable from any caller (#11).
7. **Durable cascades over fire-and-forget.** Delete cascade, admission, promotion, and quarantine are all jobs written to a jobs table before starting, with idempotent sub-steps and crash-resumable recovery (#25). The outbox-style guarantee from Stage 1 Pi-Mono is reused here.
8. **Observability is typed.** Memory module has zero raw-string log statements (#52). All emissions go through a `TelemetryEvent` Pydantic schema with an allowlist of fields; anything else is dropped at emit time, not filtered later (#51, #53).
9. **State transitions are DB-enforced.** Every `state` column change goes through Postgres triggers that reject direct UPDATE statements unless accompanied by a break-glass credential audit-logged to a write-only ledger (#47).
10. **Design for one customer, not ten thousand.** Per B1 rationale: a "shared-ready" abstraction added now costs real money and weakens the single-tenant guarantee. The architecture assumes one tenant per process and will be rebuilt — not refactored — if shared multi-tenancy ever ships.

---

## 1. Reference Analysis

_(This section is filled in progressively after each reference dump is read.)_

### 1.1 Beads — Patterns Worth Porting

**Source:** `_bmad-output/planning-artifacts/src/gastownhall-beads-8a5edab282632443.txt`
**Strategy:** Pattern extraction on top of Postgres — NOT a full port. The Stage 3 prompt said "copy/port" but the actual Beads project is a Go-based issue tracker built on Dolt (a SQL database with git-style versioning). Dolt is a heavy dependency that Praxis does not need. What we actually want are Beads' architectural *patterns*, re-implemented on the same Postgres instance that Mem0 and Atelier already use.

**Key correction to the launch prompt:** the prompt lists Beads under "Copy/Port (TypeScript → Python)." Beads is Go, not TypeScript, and a direct port would require porting Dolt's versioning semantics (cell-level 3-way merge, auto-commit history, garbage collection) into Python. That's a 6-month project for a feature we don't need — we have exactly one tenant per process and no multi-branch coordination problem. Winston's decision: **extract patterns, re-implement on Postgres**. The Beads port plan in §3 reflects this correction.

| # | Pattern | Where in Beads | Why we keep it |
|---|---------|----------------|----------------|
| B1 | **Hash-based IDs prevent merge conflicts** | Issues use `bd-a1b2` style short IDs derived from `ComputeContentHash()` — IDs are content-addressed so two concurrent creates cannot collide unless they're literally the same content. | Our `bead_hash` design uses the same principle (sha256 of canonical serialization). Concurrent writes from parallel agents within one tenant produce distinct hashes unless the content is identical, in which case deduplication is the correct outcome. |
| B2 | **Auto-commit per mutation** | Every write to Beads triggers an automatic Dolt commit, creating a durable audit trail. | Mapped to Praxis via the transactional outbox pattern from Stage 1 Pi-Mono: bead insert + `CostEvent(retention_action)` + outbox row, all in one DB transaction. Same guarantee, different substrate. |
| B3 | **Wisp → Digest squashing for retention** | Beads' `bd mol squash <wisp>` compresses "vapor" (short-lived working notes) into a "digest" (permanent summary), reclaiming history space. | Maps 1:1 to our retention policy in §3.4: beads 30–365 days old get compacted via Forge (conversation-shaped) or TONL (structured), producing a smaller hash-linked summary while preserving the audit trail. The "wisp → digest" naming is Beads-internal; Praxis uses "bead → compacted_bead." |
| B4 | **Explicit garbage collection command** | `bd compact --dolt` runs Dolt garbage collection to reclaim disk after squashing. | Our Postgres equivalent: a scheduled VACUUM + REINDEX on the `beads` table after the retention reaper runs. Runs nightly, tracked via Pi-Mono CostEvent. |
| B5 | **Doctor checks for invariants** | `bd doctor` runs a suite of invariant checks (redirect file tracking, vestigial worktrees, sync-branch integrity) and reports violations. | Praxis Memory has its own doctor: manifest verification + tenant_hash sample scan + break-glass ledger integrity check + Mem0 test harness smoke test. Runs at boot and on demand via CLI. |
| B6 | **No-history flag for ephemeral beads** | `bd create --no-history` skips Dolt commit for permanent agent beads that don't need audit. | Maps to our telemetry-only operations: pure retrievals, health checks, cache hits — these do NOT produce beads (§3.2 "What does NOT go into a bead"). Same rationale: not every operation deserves an audit-trail entry. |
| B7 | **Content-hash comparison for sync** | `localComparable.ComputeContentHash() == remoteConv.Issue.ComputeContentHash()` — Beads compares content hashes to detect semantically identical records across distributed copies. | Under managed single-tenant we have no distributed sync problem, but the pattern is valuable for the Mem0 upgrade test harness (§4.1): canonical query set with pinned content hashes, any drift = regression. |

**Patterns we explicitly DROP from Beads:**

| # | Pattern | Why dropped |
|---|---------|-------------|
| B-D1 | **Dolt as storage engine** | We already have Postgres + pgvector. Adding a second DB engine for "versioning" doubles ops complexity for no benefit. Postgres tables + append-only `beads` table achieves the same audit-trail guarantee. |
| B-D2 | **Cell-level 3-way merge** | No branch merging in Praxis — single tenant per process, no distributed coordination. |
| B-D3 | **Git integration (sync branches, push/pull, remote hooks)** | Praxis Memory is not a user-facing VCS. The `praxis-config/` Git repo handles deployment-time config versioning; Memory runtime has no git operations. |
| B-D4 | **Issue-tracker semantics (types, priorities, dependencies)** | Beads is a domain-specific tool. We want its versioning patterns, not its task-management model. |
| B-D5 | **Server mode (multi-client protocol)** | Single-process per tenant means no server protocol needed. Python processes talk to Postgres directly via SQLAlchemy. |
| B-D6 | **Embedded vs server dual mode** | Collapses to single mode: in-process async SQLAlchemy sessions. |

### 1.2 Mem0 — Integration Points

**Source:** `_bmad-output/planning-artifacts/src/mem0ai-mem0-8a5edab282632443.txt`
**Strategy:** Reference as dependency (`pip install mem0ai`). 47K stars, mature, actively maintained. DO NOT FORK.

**Public API surface (what Praxis uses):**

| Method | Signature (simplified) | Praxis usage |
|--------|------------------------|--------------|
| `add` | `add(messages, *, user_id, agent_id, run_id, metadata, infer=True, memory_type=None, prompt=None)` | Called from `Memory.store_fact()` to ingest conversation messages and let Mem0's LLM extract facts. `infer=True` is the default — we use it; `infer=False` is an opt-out for structured-fact insertion. |
| `search` | `search(query, *, user_id, agent_id, run_id, limit=100, filters=None, threshold=None)` | Called from `Memory.retrieve_facts()` for semantic search. At least one of `user_id`/`agent_id`/`run_id` required. |
| `get` | `get(memory_id) -> dict` | Direct lookup by ID — used by the GDPR export path to fetch specific records. |
| `get_all` | `get_all(*, user_id, agent_id, run_id, limit=100, filters=None)` | Used by `Memory.export()` for GDPR Article 15 bulk dump. |
| `update` | `update(memory_id, data)` | Used only by the Mem0 upgrade test harness — we do not mutate facts in normal operation (facts are append-only; corrections become new facts with a `contradicts` or `supersedes` relation). |
| `delete` | `delete(memory_id)` | Called from the delete cascade job. |
| `delete_all` | `delete_all(*, user_id, agent_id, run_id)` | Called from the full-tenant delete path after crypto-shred decision. |

**Scoping contract:**

Mem0 requires **at least one** of `user_id`, `agent_id`, `run_id` — not all three. Under managed single-tenant:
- `user_id` is always set to `manifest.tenant_hash` and never varies within a process.
- `agent_id` is set when the call is attributable to a specific BMAD agent.
- `run_id` is set when the call is attributable to a specific workflow session.

Mem0 applies these as AND filters — so passing all three narrows results to that axis combination. The Praxis facade always passes `user_id=manifest.tenant_hash` as defense-in-depth; Mem0's internal storage scoping uses this as the collection boundary.

**Configuration shape (inline, tenant-scoped):**

Mem0 accepts a `Memory.from_config(config)` builder with `vector_store`, `llm`, `embedder`, and optional `graph_store` sections. Our tenant-pinned config is produced at boot from the deployment manifest — never varies at runtime, never loaded from user input.

**Inference mode (`infer=True`) is the default value-add:**

When `infer=True`, Mem0 runs an LLM call on each `add()` to extract facts from the raw messages. This is the reason we're using Mem0 rather than raw pgvector: the fact extraction is the Mem0 differentiator. Cost implications:
- Each `add()` call costs one LLM call (Sonnet-class, ~$0.003/call at Stage 1 cost estimates).
- `infer=False` skips the LLM call and stores raw content directly — used only by the Mem0 upgrade test harness.

Pi-Mono attribution: Mem0's LLM call runs through our tenant-scoped API keys (Req #31), so the cost record is already attributed to the correct tenant at the Stage 1 boundary — we just tag it with `component="memory.mem0.fact_extraction"`.

**Graph store integration (deferred):**

Mem0 supports optional `graph_store` (Neo4j). Praxis does NOT enable this in Stage 3 — it adds a second database engine to ops, for a feature (relationship graph of facts) that overlaps with Atelier's `decision_relations` table. Decision: keep Memory on Postgres-only; revisit graph_store only if retrieval quality on benchmark MAC questions (Stage 5) shows a gap attributable to missing graph relations.

**Fields exposed in the returned dict:**

`search()` and `get()` return a dict with: `id`, `memory` (the extracted fact text), `hash` (content hash for dedup), `user_id`, `agent_id`, `run_id`, `metadata`, `created_at`, `updated_at`, `score` (cosine similarity 0..1). Praxis wraps this in a Pydantic `FactRecord` at the facade boundary so application code never sees the raw dict.

**What Praxis DOES NOT use:**

| Feature | Why skipped |
|---------|-------------|
| `graph_store` / Neo4j | Deferred — Postgres-only for Stage 3 |
| `MemoryAgent` / `MemoryEnabledAgent` wrappers | Praxis has its own BMAD agent loader (Stage 4); we don't use Mem0's agent abstractions |
| Custom `prompt` parameter on `add()` | Future work — Stage 5 MAC calibration may tune the fact-extraction prompt |
| Mem0's built-in history / versioning | We have Beads for that |
| Mem0's CLI | Praxis does not expose Mem0 CLI commands to operators |

**Upstream risk mitigations (Req #58 rationale):**

The `afd00efbd06b_add_unique_user_id_constraints` migration reference in Mem0's codebase confirms Mem0 has DB-level unique constraints on `user_id`. Under single-tenant this is safe (one user_id per process lifetime); the migration would only cause issues if we ever tried to host multiple tenants in one Mem0 collection — which we never do (Req #13). The Mem0 integration test harness §4.1 has an explicit test for collection-boundary enforcement so upstream schema changes are caught at CI time.

| # | Pattern | Praxis adoption |
|---|---------|-----------------|
| M1 | **Three-axis scoping** (`user_id`, `agent_id`, `run_id`) | Already adopted in §2.3 |
| M2 | **Collection-per-tenant** via `collection_name` config | Adopted — `praxis_tenant_{tenant_hash}` |
| M3 | **`infer=True` default for fact extraction** | Adopted as default; `infer=False` reserved for test harness |
| M4 | **Pluggable vector store provider** | pgvector default; future flexibility preserved |
| M5 | **`filters` dict for metadata-based narrowing** | Used sparingly; most filtering goes through our typed facade methods |
| M6 | **`threshold` similarity gate on search** | Adopted — Praxis default 0.75, configurable per call |

### 1.3 Atelier Decision Memory — Patterns Worth Extracting

**Source:** `_bmad-output/planning-artifacts/src/robertsfeir-atelier-pipeline-8a5edab282632443.txt`
**Strategy:** Pattern extraction + re-implementation in Python. Atelier is a Node.js pipeline-orchestration tool with a "Brain" persistent memory system backed by Postgres + pgvector + ltree. The Brain's decision-capture patterns are what we port; the Node.js server, the Eva/Robert/Cal/Roz agent choreography, and the claude-code-specific integration are all out of scope.

**What Atelier's Brain actually is:** a Postgres (with pgvector + ltree extensions) thought store where agents call `agent_capture` to record thoughts and `agent_search` to retrieve them. Every thought has a typed schema (thought_type, source_phase, importance), vector embedding for semantic search, ltree-path for hierarchical scope, and write-time conflict detection via similarity thresholds. Cost: documented at ~$0.72/year for a heavy user (3,500+ thoughts/month).

| # | Pattern | Where in Atelier | Why we keep it |
|---|---------|------------------|----------------|
| AT1 | **Typed thought schema** | `CREATE TYPE thought_type AS ENUM (...)` + `CREATE TYPE source_phase AS ENUM (...)` — every thought is typed at write. | Maps to our `DecisionRecord` + `QuarantineReason` enums. The enum-at-schema approach prevents freeform fields from drifting; we adopt it. |
| AT2 | **Importance field (0..1)** | `importance FLOAT NOT NULL CHECK (importance >= 0 AND importance <= 1)` — separate from confidence, separate from relevance. | New signal we hadn't accounted for in §5.1. We add it: "importance" is the captured author's self-assessment of how much this decision matters beyond the current task. Distinct from `confidence` (how sure am I this decision is right) and from `quality_score` (MAC's assessment of the outcome). |
| AT3 | **Write-time conflict detection via similarity thresholds** | >0.9 similarity = duplicate (skip write); 0.7-0.9 = LLM-classified contradiction detection; <0.7 = independent. | We adopt this for the `store_decision()` path. Duplicate-skip prevents the library from bloating with near-identical captures. Conflict detection at 0.7-0.9 produces an `evolves_from` or `contradicts` relation instead of a naive overwrite. |
| AT4 | **Typed relations graph** | `supersedes`, `contradicts`, `evolves_from`, `triggered_by` — edges between thoughts. | We adopt three relation types: `supersedes` (new decision replaces old), `contradicts` (new decision explicitly rejects old with reasoning), `evolves_from` (new decision is a refinement). Stored in a `decision_relations` table. Gives the `export()` API a provenance graph to walk. |
| AT5 | **TTL decay per thought type** | `thought_type_config` table with `default_ttl_days` per type (some types never expire). | Validates our §5.4 TTL design. We already have per-record `ttl_days`; Atelier's per-type default is a nice UX layer on top. We add a `decision_type_config` table with default TTL per `thought_type`. |
| AT6 | **Recency decay formula** | `recency_decay = 0.995 ^ hours_since_last_access` — exponential decay from last ACCESS, not from creation. | We adopt this specifically. "Last access" is a better signal than "creation time" — a decision that keeps getting retrieved is still live, even if old. Schema adds `last_accessed_at` column to decisions. |
| AT7 | **Retrieval score additive form** | `score = (0.5 * recency_decay) + (2.0 * importance) + (3.0 * cosine_similarity)` | Differs from Req #43's multiplicative form. **Winston's reconciliation:** Req #43 is binding (multiplicative), but we note Atelier's weights as the *initial coefficients* for the multiplicative form. See §5.3 reconciliation block. |
| AT8 | **Hierarchical scoping via ltree** | `thoughts.scope ltree` column with path-style hierarchical queries. | Maps to our three-axis scoping (tenant → agent → run). We use ltree for the same purpose: `scope = tenant_hash.agent_id.run_id` as an ltree path, enabling prefix queries for "all decisions from this run" / "all decisions from this agent across runs." |
| AT9 | **Auto-capture via post-agent Haiku subagent** | `brain-extractor` Haiku agent invoked via `SubagentStop` hook after Cal/Colby/Roz/Agatha completions. Extracts decisions/patterns/lessons from parent agent output. | Maps directly to our §5.2 auto-capture hook. Praxis's hook is Stage 4 runtime hooking into BMAD agent completion events. The actual extraction is cheap (Haiku-class model). |
| AT10 | **State-file hydration** | `hydrate-telemetry.mjs --state-dir` parses pipeline state files (e.g., `pipeline-state.md`, `context-brief.md`) into thought captures. Dedup via sha256 content hashing. | We adopt this for the seed corpus ingest (Req B6 decisions): the BMAD/Tokonomics markdown files are hydrated into the seed corpus via a similar state-file parser. Dedup via sha256 content hash at ingest time. |
| AT11 | **`agent_search` with filters** | Retrieval API takes `query`, `thought_type`, `source_phase`, `importance` min, `scope_filter` — typed filters. | Our `retrieve_decisions()` method already accepts `query` + `top_k`. We add optional filter parameters for `thought_type`, `source_phase`, `importance_min` — matching Atelier's query ergonomics. |
| AT12 | **Background consolidation** | Background job synthesizes raw observations into reflections ("consolidation"). | Out of scope for Stage 3 but noted: this is a Stage 5 MAC-adjacent feature. When MAC matures, it can run a consolidation job over tentative entries to produce higher-order insights. Mentioned here so Stage 5 knows about it. |
| AT13 | **`atelier_trace` — decision chain provenance query** | A query that walks the relation graph backward from a decision to its evidence and triggering context. | We adopt this as the `Memory.trace_decision(decision_id)` method (adds to facade §2.1 — see below). Used by the GDPR export to produce a provenance graph for auditors. |
| AT14 | **Free-tier cost profile** | $0.72/year for 3,500 thoughts/month documents the economics. Embedding cost dominates ($0.02/1M tokens via OpenRouter; we use Anthropic/OpenAI directly). | Informs capacity planning: at scale (say 10K thoughts/month/tenant), embedding cost remains negligible (~$3/year/tenant). No budget concerns for Stage 3. |

**Patterns we explicitly DROP from Atelier:**

| # | Pattern | Why dropped |
|---|---------|-------------|
| AT-D1 | **Node.js server implementation** | Praxis is Python. We re-implement on SQLAlchemy async. |
| AT-D2 | **Claude Code integration (SubagentStop hooks, MCP server)** | Praxis is library-first, not Claude-Code-specific. The auto-capture hook is invoked from Stage 4 runtime, not Claude Code events. |
| AT-D3 | **Eva/Robert/Cal/Roz/Agatha/Darwin/Colby agent choreography** | Atelier's agents are domain-specific to Atelier's pipeline. Praxis uses BMAD agents (different framework). |
| AT-D4 | **OpenRouter as embedding provider** | We go direct to Anthropic/OpenAI via the tenant-scoped API keys (Req #31). |
| AT-D5 | **`captured_by` from git config / env var** | Praxis's equivalent is `agent_id` + `run_id` from the Stage 4 runtime context, not an operating-system identity. |
| AT-D6 | **ADR-0024 / ADR-0025 / ADR-0027 Atelier-specific design choices** | Internal Atelier decisions about its own system; not generalizable. We reference the patterns, not the ADR history. |

---

## 2. Unified Memory Interface

This is the single API surface that all of Praxis talks to. The three underlying systems (Beads, Mem0, Atelier) are implementation details composed behind it.

### 2.1 The `Memory` Facade

```python
# praxis/kernel/memory/facade.py
from typing import Protocol, Literal
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class Memory(Protocol):
    """Unified Memory interface. Application code talks to this and nothing else.

    Scoping invariant: every method requires `tenant_id` (defense-in-depth per
    Req #1) but the effective scope is the process's pinned deployment tenant.
    The facade rejects any call where tenant_id != deployment manifest tenant_id.
    """

    # --- Write path ---------------------------------------------------------
    async def store_task_outcome(
        self,
        tenant_id: str,
        task: TaskSignature,
        outcome: TaskOutcome,
    ) -> TaskOutcomeRecord: ...
    """Writes to TENANT scope always (#12). Not configurable."""

    async def store_decision(
        self,
        tenant_id: str,
        decision: DecisionRecord,
    ) -> DecisionRecord: ...
    """Atelier-style decision memory capture (#56 references, Atelier pattern)."""

    async def store_fact(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        fact: FactRecord,
    ) -> FactRecord: ...
    """Mem0 fact extraction write. Three-axis scoping per prompt §Mem0."""

    # --- Retrieval path -----------------------------------------------------
    async def retrieve_similar_tasks(
        self,
        tenant_id: str,
        signature: TaskSignature,
        top_k: int = 5,
        min_similarity: float = 0.75,
    ) -> RetrievalResult: ...
    """Cross-session retrieval. Returns tenant + seed corpus by default.
       Emits source-distribution telemetry (#22) and CostEvent retrieval_cache_hit (#57)."""

    async def retrieve_decisions(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 10,
    ) -> RetrievalResult: ...

    async def retrieve_facts(
        self,
        tenant_id: str,
        agent_id: str,
        run_id: str,
        query: str,
        top_k: int = 10,
    ) -> RetrievalResult: ...

    # --- GDPR surface ------------------------------------------------------
    async def delete(
        self,
        tenant_id: str,
        criteria: DeleteCriteria,
    ) -> DeleteResult: ...
    """Durable cascade across Beads → Mem0 → Atelier → experience library.
       Returns after all sub-steps complete (#25). Synchronous embedding purge (#34).
       Cache-invalidation pub/sub ack aggregation gates return (#27)."""

    async def export(
        self,
        tenant_id: str,
        criteria: ExportCriteria,
    ) -> ExportResult: ...
    """GDPR Article 15 right-to-access. Uses the same facade as retrieval (#37).
       Integration test enforces two-tenant isolation."""

    async def flag_and_quarantine(
        self,
        tenant_id: str,
        entry_id: str,
        reason: QuarantineReason,
        free_text: str | None = None,
    ) -> QuarantineResult: ...
    """Strips embedding in-place (#35). Reason is a structured enum (#45)."""

    # --- Observability surface ---------------------------------------------
    async def health(self) -> HealthReport: ...
```

**What the facade does NOT expose:**
- No `scope` parameter anywhere (Req #12 — scope is method-implicit).
- No kwarg whose name contains `"tenant"` other than the required `tenant_id` positional (Req #7 — CI lint enforces).
- No raw query builder / criteria dict with unchecked predicates (Req #8).
- No direct access to `Beads`, `Mem0Client`, or `AtelierStore` — those live in `praxis.kernel.memory._internal.*` and the facade module's `__all__` excludes them (Req #9).

**Tenant-id defense-in-depth:** Every method receives `tenant_id` as its first non-self parameter. The facade implementation compares it against the process-wide `DeploymentManifest.tenant_id` (loaded at boot per Req #3–#5). On mismatch: raise `TenantIdentityError` (a subclass of `PermissionError`), emit a `TelemetryEvent(type="tenant_mismatch_rejected")`, and hard-fail the process after logging. This is paranoid — under managed single-tenant the caller has no way to set a "wrong" tenant_id — but the paranoia is intentional: it catches the FM1.6 failure mode (metadata dict carrying a tenant override) at the method boundary.

### 2.2 Pydantic Input/Output Models

All input and output types are frozen Pydantic v2 models. Frozen enforcement prevents post-construction mutation, catches bugs, and lets the facade treat records as values rather than handles.

```python
# praxis/kernel/memory/models.py

class TaskSignature(BaseModel):
    model_config = ConfigDict(frozen=True)
    task_type: str                     # e.g., "strategic_advisory"
    input_hash: str                    # sha256 of canonicalized input
    agents_involved: tuple[str, ...]   # sorted tuple of agent IDs
    context_fingerprint: str           # rolling hash of retrieved context
    schema_version: int = 1

class TaskOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)
    quality_score: float               # 0..1, from MAC (Stage 5)
    quality_confidence: float          # 0..1, from MAC (Req #39)
    cost_usd: float
    reasoning_trace: list[ReasoningStep]
    approach_summary: str
    dissents: list[DissentRecord] = []

class DecisionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    decision: str
    rationale: str
    alternatives_considered: list[str]
    evidence: list[EvidenceItem]
    confidence: float
    outcome: OutcomeStatus | None = None   # filled in later when known
    captured_at: datetime
    ttl_days: int = 365

class QuarantineReason(str, Enum):     # Req #45
    PII_LEAK = "pii_leak"
    HALLUCINATION = "hallucination"
    OUTDATED = "outdated"
    POISONED = "poisoned"
    OTHER = "other"
```

All records carry these implicit columns at the base-model level:
- `tenant_hash` (Req #6) — the startup sample-scan uses this for drift detection.
- `schema_version` — monotonic; used by Mem0 upstream bump regression tests.
- `state_snapshot_version` — opaque token returned on retrieval (Req #44) for deterministic replay.

### 2.3 Scoping Rules (Process-Level)

```
Process boot:
  manifest = DeploymentManifest.load_signed("praxis-config/deployments/{tenant_hash}.yaml")
  verify_signature(manifest)
  verify_db_fingerprint(manifest)
  verify_tenant_hash_sample(manifest)
  if any fail: sys.exit(2)

Process runtime:
  every 60s: re-verify manifest (Req #4)
  on mismatch: sys.exit(2) — Kubernetes/systemd restarts

Memory facade:
  tenant_id passed to every call is compared against manifest.tenant_id
  mismatch raises TenantIdentityError and process exits

Backend scoping:
  Beads worktree = /var/lib/praxis/beads/{manifest.tenant_hash}/
  Mem0 collection = f"praxis_tenant_{manifest.tenant_hash}" (disjoint from seed)
  Mem0 seed collection = "praxis_seed_v{seed_version}" (read-only)
  Atelier schema = set at boot from manifest; never rewritten
```

**Three-axis scoping for Mem0 (per Prompt §3.2):**

| Praxis axis | Mem0 axis | Source |
|-------------|-----------|--------|
| `tenant_id` | `user_id` | DeploymentManifest |
| `agent_id` | `agent_id` | BMAD agent-manifest.csv (Stage 4 registry) |
| `run_id` | `run_id` | Runtime-generated ULID per workflow session |

Note: Mem0's `user_id` = Praxis's `tenant_id` in single-tenant mode. This binds individual users to the whole tenant deployment, which is correct: a managed-single-tenant customer is conceptually "one user" from Mem0's perspective. Per-human-operator scoping within a tenant is a Stage 6/7 concern, not Stage 3.

---

## 3. Beads Integration Design

_(Initial draft based on the Stage 3 prompt's stated strategy; refined after reference read.)_

### 3.1 Module Structure

```
praxis/kernel/memory/
├── facade.py                    # Memory interface (§2)
├── models.py                    # Pydantic record types (§2.2)
├── deployment/
│   ├── manifest.py              # DeploymentManifest, signed load, 60s re-verify
│   └── tenant_identity.py       # TenantIdentityError, process-wide singleton
├── _internal/
│   ├── beads/
│   │   ├── __init__.py          # __all__ restricts exports
│   │   ├── store.py             # BeadsStore — versioned snapshot API
│   │   ├── content_hash.py      # sha256-based content addressing
│   │   ├── worktree.py          # Per-tenant worktree manager
│   │   ├── compaction.py        # Forge integration (Stage 2 boundary)
│   │   └── replay.py            # Deterministic snapshot replay
│   ├── mem0/
│   │   ├── __init__.py
│   │   ├── client.py            # Mem0 pip dependency wrapper
│   │   ├── backend_config.py    # pgvector backend + provider pinning
│   │   ├── scoping.py           # user/agent/run axis translation
│   │   └── upgrade_tests.py     # CI harness for upstream bumps (#58)
│   ├── atelier/
│   │   ├── __init__.py
│   │   ├── decision_store.py    # pgvector-backed decision memory
│   │   ├── capture.py           # Auto-capture hook protocol
│   │   ├── decay.py             # TTL-based recency weighting (pure fn)
│   │   └── scoring.py           # Retrieval score formula (Req #43)
│   ├── cascade/
│   │   ├── __init__.py
│   │   ├── delete_job.py        # Durable delete cascade (Req #25)
│   │   ├── invalidation.py      # Cache-invalidation pub/sub (Req #27)
│   │   └── crypto_shred.py      # Backup key destruction (Req #29)
│   └── telemetry/
│       ├── __init__.py
│       ├── events.py            # TelemetryEvent allowlist schema
│       └── sinks.py             # Central sink + tenant-local sink
└── __init__.py                  # public __all__ = ["Memory", "models", ...]
```

### 3.2 Versioning Mechanism

Every write to Memory that changes tenant state produces a **bead**: a content-addressed snapshot pointing at (previous_bead_hash, change_payload, timestamp, tenant_hash, operation_type). The bead hash is `sha256(serialize_canonical(bead_contents))`. Beads form a Merkle chain per worktree; worktrees are per-process (one tenant per process, so one worktree per deployment).

Replay is: starting from a genesis bead, apply each change_payload in hash-order until reaching the target bead. The `replay.py` module implements this pure-functionally: given a starting Memory state + a list of beads, it produces the final state.

**What goes into a bead:**
- `store_task_outcome` write (entire outcome record payload)
- `store_decision` write
- `store_fact` write (reference to Mem0 fact ID + minimal payload)
- `delete` operation (record of what was deleted by hashed criteria — Req #33)
- `flag_and_quarantine` operation

**What does NOT go into a bead:**
- Pure retrievals (read-only)
- Telemetry events
- Cache operations

### 3.3 Worktree Isolation Semantics

Under managed single-tenant: **one worktree per deployment**, located at `/var/lib/praxis/beads/{tenant_hash}/`. The worktree directory is the tenant boundary at the filesystem level. A deployment process that finds a worktree belonging to a different tenant_hash hard-fails at boot.

Parallel agents within the same deployment share the worktree; concurrent bead writes use Postgres-backed optimistic concurrency control (compare-and-swap on `latest_bead_hash` column in the `beads_head` table). Conflicts retry after re-reading the head.

### 3.4 Compaction Interaction with Forge (Stage 2)

Beads accumulate indefinitely. Old beads get compacted. The compaction strategy depends on payload type:

- **Conversation-shaped beads** (those whose payload contains `ConversationMessage[]`): Forge compaction applies. The Stage 2 `Forge.maybe_compact(history)` operator is called with the bead payload; the compacted result replaces the bead payload and the bead is re-hashed with `compaction_event_hash` linking to the original.
- **Structured-record beads** (outcomes, decisions, facts): TONL serialization applies. The bead payload is re-serialized via `praxis.kernel.compression.tonl.encode(payload)` which shrinks the on-disk footprint without lossy compaction.
- **Genesis and recent beads**: not compacted. A rolling window of the last N beads (strawman N=100) is preserved as-is for fast replay.

Compaction is idempotent per Stage 2's guarantee (`compact(compact(X)) == compact(X)`). A property test in `beads/compaction.py` asserts this against sample payloads.

**Retention policy (Req #11 from prompt §11):**
- Beads in the last 30 days: full fidelity, no compaction.
- Beads 30–365 days: compacted via Forge/TONL, original payload retained only as hash reference.
- Beads >365 days: pruned unless they're genesis beads, seed-corpus-version pins (Req #15 — retained indefinitely), or referenced by an audit trail.

### 3.5 Integration with Pi-Mono Outbox

Beads writes are coupled to Pi-Mono cost events. Per Stage 1's transactional outbox pattern (§3.4.3 of pi-mono arch): a bead write and a `CostEvent(type="retention_action")` are written in the **same database transaction** as the underlying data change (outcome record, decision, fact). Either all three succeed or all three roll back. This reuses the Stage 1 guarantee exactly — no new durability machinery is introduced.

### 3.6 Beads Port Plan (concrete, Go → Python)

Given the §1.1 correction that we extract patterns rather than literally port Beads, the concrete plan for `praxis.kernel.memory._internal.beads`:

**Components to build (Python, new code, pattern-informed by Beads):**

| Module | Responsibility | Beads pattern |
|--------|----------------|---------------|
| `store.py` | `BeadsStore` class — append-only insert, lookup by hash, range query by tenant+time | B1 (content-hashing), B2 (auto-commit semantic via outbox) |
| `content_hash.py` | `compute_content_hash(payload: bytes) -> str` — canonical serializer + sha256 | B1, B7 |
| `chain.py` | Merkle chain traversal — given a head hash, walk backward collecting parents | B2 (audit trail) |
| `compaction.py` | Retention reaper — selects beads by age, applies Forge or TONL, writes compacted beads linked to originals | B3 (wisp→digest squashing) |
| `gc.py` | VACUUM + REINDEX scheduler — runs nightly after compaction | B4 (explicit GC) |
| `doctor.py` | Invariant checks: tenant_hash sample, head-pointer consistency, orphaned bead detection, Merkle chain integrity | B5 (doctor pattern) |
| `replay.py` | Pure-functional replay: given a head bead + state reducer, produce final state | — (net-new for Praxis) |
| `head.py` | Optimistic concurrency control for the `beads_head` row — compare-and-swap | — (Postgres-native) |

**Components to SKIP (Beads has them but we don't need them):**
- Sync branches / distributed pull (B-D3)
- Issue-tracker domain model (B-D4)
- Server-mode protocol (B-D5)
- Dolt integration (B-D1)
- 3-way merge resolver (B-D2)
- Redirect-file infrastructure for worktree discovery (B-D6 — we have one worktree per process)

**Port effort estimate:** ~1200 LOC Python total across the 8 modules. This is not a translation of Beads' Go code; it is a re-implementation of the patterns on Postgres + SQLAlchemy. Amelia's implementation reads the Beads source selectively for specific algorithms (e.g., how B5 doctor-check enumeration works) but does NOT translate Go structs line-by-line.

**Test targets (Murat handoff):**
- Property test: `replay(beads[0..n])` is deterministic for any prefix.
- Property test: `compact(compact(X)) == compact(X)` (inherited from Stage 2 Forge).
- Invariant test: after any sequence of operations + crash recovery, the Merkle chain is intact (no orphaned beads, no broken parent pointers).
- Load test: 10K beads with hnsw-accelerated retrieval ≤ 100ms p99 (Req #10 of non-functional requirements).

### 3.7 What "Copy/Port" Got Wrong in the Launch Prompt

The Stage 3 launch prompt at line 42–43 states:

> **Beads** (distributed versioned state) ... Strategy: COPY/PORT (foundational, needs full control)

This characterization was based on the hybrid-architecture document which treated Beads as a generic content-addressed state store. The actual Beads project is a Go + Dolt issue tracker — porting it in the literal sense would land us with a distributed issue-tracker database as the Memory backing store. That is not what the architecture needs.

**Winston's adjustment:** the binding strategy is "pattern extraction, re-implemented on Postgres" (as shown in §3.6). The Pipeline.md Section 4.5 rule 3 says "If Winston disagrees, he raises it back — does NOT silently override." This is that raise-back, recorded in-document so the team sees the adjustment before Amelia implements. If Andrey wants literal Beads port, flag it before Stage 3.3 and I'll redesign §3.

---

## 4. Mem0 Integration Design

### 4.1 Dependency Pinning Strategy

Mem0 is a pip dependency (`mem0ai`), not a fork. Per requirement #58 the integration is wrapped in a test harness that runs on every CI build and on every upstream version bump.

```toml
# pyproject.toml (excerpt)
[project]
dependencies = [
  "mem0ai==0.1.x",                     # pinned to minor version
  "pgvector==0.3.x",                   # Mem0's default backend
  # ... other Praxis deps
]
```

**Pinning policy:**
- Minor-version pin (not exact) so patch updates flow automatically.
- Minor-version bumps require a PR; the CI harness for Mem0 must pass before merge.
- Major-version bumps require an ADR in `decision-memory/adr-mem0-upgrade-{version}.md` with a re-verification of the integration tests.

**The Mem0 integration test harness** (`_internal/mem0/upgrade_tests.py`, Req #58) has four test classes:
1. **Two-tenant isolation** — create tenant A and tenant B collections with overlapping content; verify queries on A never return B's records. (This is paranoid under managed single-tenant since tenants live in separate processes, but it validates the Mem0 collection boundary which is the defense-in-depth.)
2. **Delete-then-query-by-id zero-result** — after `delete(entry_id)`, a subsequent query with that ID returns zero hits. Tests both the Mem0 API level AND the pgvector index level (Req #26 post-delete verification).
3. **Schema stability** — canary record with every field type; after Mem0 upgrade, re-ingest and verify field semantics unchanged. Field rename or type change = test failure.
4. **Retrieval semantics regression** — a canonical query set with pinned expected top-K. Regression = semantic drift in Mem0's retrieval logic.

### 4.2 Backend Configuration

Default backend: **pgvector** on the same Postgres instance as Beads and Atelier. One database, three logical stores, one connection pool.

```yaml
# config/mem0.yaml (loaded at boot from deployment manifest)
vector_store:
  provider: pgvector
  config:
    host: ${POSTGRES_HOST}
    port: ${POSTGRES_PORT}
    db_name: praxis_memory          # same DB as Beads and Atelier
    collection_name: praxis_tenant_${TENANT_HASH}
    embedding_model_dims: 1536      # pinned by embedding_model_id
llm:
  provider: anthropic               # or openai per tenant config
  config:
    api_key: ${ANTHROPIC_API_KEY}   # tenant-scoped (Req #31)
    model: claude-sonnet-4-6
embedder:
  provider: openai                  # strawman — alternative: anthropic or local
  config:
    model: text-embedding-3-small   # pinned — seed_version depends on this (#14)
```

**SQLite dev equivalent:** `mem0ai` supports SQLite+sqlite-vss for dev. Production is Postgres+pgvector only. The config loader rejects SQLite in `environment=production`.

### 4.3 Three-Axis Scoping Translation

Covered in §2.3 above. Restated for completeness:

| Mem0 axis | Praxis meaning | Source of value |
|-----------|----------------|-----------------|
| `user_id` | deployment tenant | DeploymentManifest.tenant_id (pinned at boot) |
| `agent_id` | BMAD agent | Stage 4 runtime agent registry |
| `run_id` | workflow session | ULID generated at workflow start |

Under managed single-tenant, `user_id` is constant for the lifetime of the process. `agent_id` and `run_id` vary per operation.

### 4.4 Fact Extraction Pipeline

Mem0's built-in fact extraction runs on every `store_fact` call. The extracted fact is ingested into the pgvector collection and the graph store. Praxis adds:

- **Pre-ingest PII redaction** — same redactor used by seed corpus ingest (Req #18). Facts containing names/emails/SSNs/credit cards are either rejected or redacted (policy is config).
- **Post-ingest telemetry event** — `TelemetryEvent(type="fact_ingested", agent_id=..., fact_count=N)` emitted via allowlisted schema (#51).
- **Cost attribution** — Mem0's LLM call for fact extraction is tracked via Stage 1 `CostEvent(type="record_created", component="memory.mem0.fact_extraction")`. This was already a Stage 1 emit channel; we just tag it correctly.

### 4.5 Mem0 Integration Adapter — Post-Reference Concrete Design

The `Mem0Client` wrapper in `praxis/kernel/memory/_internal/mem0/client.py` is a thin typed adapter around Mem0's public `Memory` class. Responsibilities:

1. **Construction from manifest:** At process boot, the deployment manifest is parsed into a Mem0 config dict and `Memory.from_config(config)` is called. The resulting `Memory` instance is held as a process-global singleton (one per process under single-tenant). Construction failure is a hard-fail at boot.

2. **Typed boundary:** Every call into Mem0 takes Pydantic input models and returns Pydantic output models. The raw dict returned by Mem0 is transformed at the boundary and the raw form is never exposed to the facade or application code.

3. **tenant_hash injection:** Every `add`/`search`/`get_all`/`delete` call receives `user_id = manifest.tenant_hash` injected by the adapter. The facade passes `tenant_id` which is validated against the manifest; the adapter strips `tenant_id` and substitutes `user_id = manifest.tenant_hash` before calling Mem0.

4. **Error translation:** Mem0-specific exceptions are caught at the boundary and translated into Praxis-typed exceptions (`MemoryBackendError`, `MemoryRecordNotFound`). This prevents Mem0's internal exception types from leaking into application code.

5. **PII pre-redaction:** Before calling `add()`, the adapter runs the PII redactor over `messages` content. Redacted content is stored; the original is never persisted.

6. **Retry policy:** Mem0 transient failures (network to embedding provider, pgvector hiccups) are retried with exponential backoff by the adapter — max 3 attempts, then propagate `MemoryBackendError`. Delete cascade sub-steps are explicitly NOT retried by the adapter because the delete-job orchestrator (§8.5) handles retry at the job level.

7. **Observability hooks:** Every call into Mem0 emits a `TelemetryEvent` (pre-call and post-call) and a Pi-Mono `CostEvent` (with the component="memory.mem0.*" tag). Latency is tracked. Errors are counted per category.

8. **Graceful degradation on delete cascade:** If Mem0 reports success but the post-delete verification query (§8.5 step 5) still finds vectors in pgvector, the adapter raises a BLOCKING error that fails the delete cascade job. This catches FM3.11 (Mem0 upstream delete bug) at runtime, not just at CI time. Combined with Req #58's test harness, we have two independent guards.

**Sample adapter skeleton:**

```python
# praxis/kernel/memory/_internal/mem0/client.py
from mem0 import Memory as Mem0Memory
from praxis.kernel.memory.deployment.manifest import DeploymentManifest
from praxis.kernel.memory.models import FactRecord, RetrievalResult

class Mem0Client:
    def __init__(self, manifest: DeploymentManifest):
        self._manifest = manifest
        config = self._build_config_from_manifest(manifest)
        self._mem0 = Mem0Memory.from_config(config)

    async def add_fact(self, tenant_id: str, agent_id: str, run_id: str,
                        messages: list[dict], metadata: dict) -> FactRecord:
        self._validate_tenant(tenant_id)
        messages = pii_redact(messages)
        raw = await asyncio.to_thread(
            self._mem0.add,
            messages,
            user_id=self._manifest.tenant_hash,
            agent_id=agent_id,
            run_id=run_id,
            metadata={**metadata, "schema_version": 1},
            infer=True,
        )
        return FactRecord.from_mem0(raw)

    # search/get/delete follow the same pattern...
```

All sync Mem0 calls are wrapped in `asyncio.to_thread` to keep the adapter non-blocking; if Mem0 ships an async API in a future version, the wrappers drop away.

---

## 5. Atelier Decision Memory Design

### 5.1 Decision Record Schema

```python
# praxis/kernel/memory/_internal/atelier/models.py

class DecisionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: str                        # ULID
    tenant_hash: str                        # Req #6
    agent_id: str                           # BMAD agent that made the decision
    run_id: str                             # workflow session ULID

    decision: str                           # 1-sentence summary
    rationale: str                          # why
    alternatives_considered: list[str]      # what was rejected and why
    evidence: list[EvidenceItem]            # citations, retrieved facts, prior decisions

    confidence: float                       # 0..1 — decision-maker's own confidence
    outcome_status: OutcomeStatus           # TENTATIVE → CONFIRMED via MAC-gated admission

    captured_at: datetime
    ttl_days: int                           # recency decay window
    state: EntryState                       # tentative/confirmed/quarantined/expired
    state_snapshot_version: str             # Req #44
    reason_hash: str | None                 # set on quarantine (#45)
    embedding_version: str                  # embedding_model_id — Req #14 identity
    schema_version: int = 1
```

Captured decisions go into a dedicated `decisions` table with a pgvector index on the `(rationale + decision + evidence_summary)` embedding. The table is separate from Mem0's managed tables — Atelier's semantic here (decision-with-rationale + TTL decay) is different enough from Mem0's fact-extraction model that sharing storage would leak abstractions.

### 5.2 Capture Protocol (When / What / How)

**When to capture:**
- Auto-capture hook fires on every successful BMAD agent task completion (Stage 4 runtime hooks into this via `memory.store_decision()`).
- MAC (Stage 5) emits a decision capture on every deliberation step that produces a ruling.
- Manual capture via `Memory.store_decision()` is exposed to agents that want to record their own reasoning (used by architect and PM agents).

**What to capture:**
- The decision itself (not the conversation leading to it).
- Alternatives considered (this is the Atelier differentiator — it captures WHY, not WHAT).
- Evidence trail (citations to retrieved facts, prior decisions, seed corpus entries).
- Confidence at time of capture.

**What NOT to capture:**
- Raw conversation history (that's Beads territory).
- LLM internal reasoning tokens (Stage 1 compression handles this).
- PII — capture goes through the same redactor as seed ingest.

### 5.3 Retrieval Scoring (Semantic + Recency + Confidence + State + Importance)

Per Req #43, the scoring form is **multiplicative** (not Atelier's additive form — see §1.3 AT7 reconciliation below):

```
score(entry) = semantic_similarity(query, entry.embedding)
             * recency_decay(now - entry.last_accessed_at)
             * state_weight(entry.state)
             * (entry.confidence ** alpha_c)
             * (entry.importance ** alpha_i)

state_weight:
  CONFIRMED    → 1.0
  TENTATIVE    → 0.5
  QUARANTINED  → 0.0   # effectively invisible
  EXPIRED      → 0.0   # effectively invisible

recency_decay(hours_since_last_access):
  exp_factor = 0.995 ^ hours_since_last_access    # Atelier AT6 formula
  floor = 0.1
  return max(exp_factor, floor)

alpha_c ≈ 0.5  (confidence exponent — tunable)
alpha_i ≈ 0.3  (importance exponent — tunable; gentler than confidence)
```

**Why multiplicative not additive** (reconciliation with Atelier AT7):

Atelier's retrieval uses `0.5 * recency + 2.0 * importance + 3.0 * cosine_similarity` (additive weighted sum). This form is easier to tune for a single-purpose system but has a failure mode: a QUARANTINED record with very high importance + semantic similarity can still score above a CONFIRMED record if the weights are off. Req #43 mandates multiplicative because it guarantees that any zero-weighted factor (e.g., `state_weight = 0` for QUARANTINED) produces a zero score regardless of the other factors.

The Atelier coefficients `(0.5, 2.0, 3.0)` translate loosely into our exponents: importance matters, semantic matters more, recency matters but less — the exponent form preserves this ordering without the additive risk.

**Why recency tracks `last_accessed_at` not `captured_at`** (Atelier AT6 adoption):

A decision that keeps getting retrieved is still live. A decision that was captured yesterday and has never been referenced is already cold. This matches how human institutional memory works and is the single biggest change from the skeleton v0.1 formula. Schema update: `decisions.last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT now()` + auto-update on every retrieval that includes this decision in top-K.

**Why this formula specifically:**
- `semantic_similarity` is the primary signal — if the entry isn't semantically close, nothing else saves it.
- `recency_decay` prevents stale decisions from dominating — but tracks access, not creation.
- `state_weight` hard-gates QUARANTINED and EXPIRED via multiplication-by-zero.
- `confidence^alpha_c` gently down-weights low-confidence decisions without nuking them.
- `importance^alpha_i` lifts decisions the author flagged as load-bearing. `alpha_i < alpha_c` means importance is a smaller lever than confidence — we trust the MAC-graded confidence more than the author's self-assessed importance.

All sub-functions are pure (Python, no side effects) with property tests asserting monotonicity in each factor and invariance for QUARANTINED/EXPIRED → 0. Defined in `praxis/kernel/memory/_internal/atelier/scoring.py`.

### 5.4 TTL-Based Decay Implementation

`ttl_days` is per-record and defaults to 365. Decay is computed at retrieval time — we never mutate records to "expire" them. A separate reaper job handles lifetime-based demotion:

- Tentative entries >90 days old (strawman, configurable) → demoted to `state=EXPIRED` (Req #41).
- CONFIRMED entries: never auto-demoted; only explicit `delete()` or `flag_and_quarantine()` affects them.
- QUARANTINED entries: kept (minus their embedding, per #35) for audit trail retention; demoted to EXPIRED at retention-policy expiry.

The reaper job is a durable job in the same jobs table as the delete cascade. It runs hourly.

### 5.5 Adoption Summary — What Was Added Post-Atelier Read

The sequential read of Atelier's reference implementation produced these concrete additions to §5 and related sections:

**Schema additions to the `decisions` table:**
- `importance REAL NOT NULL CHECK (importance BETWEEN 0 AND 1)` — author self-assessment (AT2).
- `scope LTREE NOT NULL` — hierarchical path `tenant_hash.agent_id.run_id` for prefix queries (AT8). Requires Postgres `ltree` extension — now a named dependency alongside `pgvector`.
- `last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT now()` — driven by retrieval side-effect (AT6). Index required.
- `superseded_by TEXT REFERENCES decisions(decision_id)` — nullable; set when a later decision explicitly supersedes this one (AT4).
- `thought_type_enum thought_type_e NOT NULL` — typed capture like Atelier (AT1). Enum values: `decision`, `pattern`, `lesson`, `insight`, `rejection`, `preference`.
- `source_phase_enum source_phase_e NOT NULL` — pipeline phase at capture time (AT1). Enum values: `elicitation`, `design`, `implementation`, `quality`, `handoff`, `runtime`, `pipeline`.

**New table: `decision_relations`**

```sql
CREATE TYPE decision_relation_type AS ENUM (
  'supersedes',        -- new decision replaces old
  'contradicts',       -- new decision explicitly rejects old (with reasoning)
  'evolves_from'       -- new decision is a refinement
);

CREATE TABLE decision_relations (
    relation_id         CHAR(26) PRIMARY KEY,
    tenant_hash         CHAR(64) NOT NULL,
    from_decision_id    CHAR(26) NOT NULL REFERENCES decisions(decision_id),
    to_decision_id      CHAR(26) NOT NULL REFERENCES decisions(decision_id),
    relation_type       decision_relation_type NOT NULL,
    reasoning           TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_decision_relations_from ON decision_relations (from_decision_id);
CREATE INDEX ix_decision_relations_to ON decision_relations (to_decision_id);
```

**New facade method: `Memory.trace_decision(tenant_id, decision_id)` (AT13)**

Walks the `decision_relations` graph backward from `decision_id` to all predecessors transitively, returning a provenance chain. Used by:
- GDPR Article 15 `export()` to include provenance of every exported decision.
- Human auditors querying "why was this decision made?"
- Stage 5 MAC consolidation (future) walking decision evolution to extract higher-order patterns.

**New table: `decision_type_config` (AT5)**

```sql
CREATE TABLE decision_type_config (
    thought_type     thought_type_e PRIMARY KEY,
    default_ttl_days INTEGER,                -- NULL = never expires
    default_importance REAL NOT NULL DEFAULT 0.5
);

INSERT INTO decision_type_config VALUES
    ('decision',   NULL, 0.8),               -- decisions never auto-expire
    ('pattern',    NULL, 0.7),               -- patterns never auto-expire
    ('lesson',     NULL, 0.9),               -- lessons never auto-expire (most valuable)
    ('insight',    180,  0.4),               -- insights expire after 180 days unless promoted
    ('rejection',  NULL, 0.5),               -- rejections are evergreen — don't re-propose bad ideas
    ('preference', NULL, 0.6);               -- preferences evergreen until superseded
```

Per-record `ttl_days` still overrides the per-type default; this table just defines sensible defaults.

**Write-time conflict detection (AT3) — the `store_decision()` flow:**

```
Memory.store_decision(tenant_id, decision):
  1. Validate tenant_id and schema
  2. Compute embedding for decision.rationale + decision.decision + evidence_summary
  3. Query pgvector for top-5 nearest by cosine similarity, scoped to same tenant + scope path
  4. For each near-neighbor with similarity >= 0.9:
       → DUPLICATE: skip the write; return the existing decision_id with a TelemetryEvent(type="decision_dedup_skipped")
  5. For each near-neighbor with 0.7 <= similarity < 0.9:
       → POTENTIAL CONFLICT: run LLM classifier (Haiku-class, cheap) asking "is new decision compatible with existing?"
       → If "supersedes" or "contradicts" or "evolves_from": write the new decision AND write a decision_relations row
  6. Otherwise: write as independent decision
  7. Emit TelemetryEvent(type="decision_captured", ...) with allowlisted fields
```

The LLM classifier call is the only LLM dependency in the Memory module write path. It uses the tenant-scoped API keys (Req #31) and runs via the Stage 1 `track_cost` boundary so the classification cost is attributed correctly. Budget: ~$0.50/1000 decision captures at current Haiku pricing.

**Retrieval API filter parameters (AT11):**

```python
async def retrieve_decisions(
    self,
    tenant_id: str,
    query: str,
    top_k: int = 10,
    thought_type: ThoughtType | None = None,
    source_phase: SourcePhase | None = None,
    importance_min: float = 0.0,
    scope_prefix: str | None = None,          # ltree prefix filter
    include_superseded: bool = False,
) -> RetrievalResult:
    ...
```

**Auto-capture hook (AT9) — integration contract with Stage 4 runtime:**

Stage 4's runtime emits an `AgentCompleted(agent_id, run_id, final_output)` event after every BMAD agent task. The Memory module subscribes and invokes a Haiku-class extractor that parses the output for decision/pattern/lesson markers and calls `store_decision()` for each extracted item. The extractor prompt is defined in `praxis/kernel/memory/_internal/atelier/auto_capture.py`.

This is the main delivery of the "Atelier decision memory pattern extraction" from the Stage 3 prompt: not Atelier's code, but Atelier's *protocol* of "let a cheap model read the smart model's output and file the insights."

**What was NOT added from Atelier** (explicitly out of scope for Stage 3):

- Background consolidation jobs (AT12) — Stage 5/6 concern.
- Atelier's `Darwin` (pattern detection) and `Poirot` (decision auditor) agents — Stage 5/6 concern.
- Multi-language scoping via ltree beyond 3 axes — Stage 6 if needed.
- Atelier's telemetry metrics framework (tier T1/T2/T3) — we use Stage 1 Pi-Mono instead.

---

## 6. Cross-Session Learning Protocol

### 6.1 Task Signature Generation

A `TaskSignature` (see §2.2) is generated from:
- `task_type` — enum / string identifier from the workflow runner (e.g., "strategic_advisory", "root_cause_analysis").
- `input_hash` — sha256 of the canonicalized task input. Canonicalization: JSON-serialize with sorted keys, remove whitespace, lowercase strings, redact PII patterns BEFORE hashing (so PII never gets into the signature).
- `agents_involved` — sorted tuple of agent IDs the workflow will engage.
- `context_fingerprint` — rolling sha256 over the content of retrieved context (not the IDs, the actual content embeddings). This is what makes two tasks with different phrasings but similar underlying state match.
- `schema_version` — monotonic; allows old signatures to be excluded when the schema evolves.

The signature is deterministic: same input → same signature. This is essential for reproducibility.

### 6.2 Retrieval Thresholds

Two tasks are "similar enough to be informative" when:

```
similarity(sig_A, sig_B) = cosine(embed(sig_A.input_hash_preimage), embed(sig_B.input_hash_preimage))
                        * task_type_match(sig_A.task_type, sig_B.task_type)
                        * agent_overlap(sig_A.agents_involved, sig_B.agents_involved)
                        * context_proximity(sig_A.context_fingerprint, sig_B.context_fingerprint)

task_type_match: 1.0 if same type, 0.3 if related type (config-defined), 0.0 otherwise
agent_overlap: |intersect| / |union|  (Jaccard)
context_proximity: cosine(embed(sig_A.context), embed(sig_B.context))
```

**Default threshold for retrieval:** similarity ≥ 0.75. Tunable per deployment. Below 0.75 and retrieval returns an empty result; the caller falls back to cold-start.

### 6.3 Write-Back Protocol

An outcome is good enough to record when:
- `quality_score ≥ 0.5` (entries below go into `state=REJECTED` which is never written to the library), AND
- `quality_confidence ≥ C_min` (default 0.6), AND
- The workflow completed without an unrecoverable error, AND
- The outcome passed PII redaction.

Admission uses the composite signal per Req #39:

```
quality_score ≥ 0.8 AND quality_confidence ≥ C_min  → CONFIRMED
0.5 ≤ quality_score < 0.8 OR quality_confidence < C_min  → TENTATIVE
quality_score < 0.5                                  → REJECTED (not stored)
```

**Outlier detection** (Req #39): tenant admission rate is monitored; if more than 3x the rolling-average rate appears in a 1-hour window, the tenant is rate-limited and a manual-review queue captures entries above the normal cap.

### 6.4 Promotion Protocol (Req #42)

Promotion from TENTATIVE to CONFIRMED requires:
1. The entry is retrieved by a subsequent workflow (tracked via retrieval telemetry).
2. That subsequent workflow's own `quality_score ≥ 0.8`.
3. (Where principal data is available) The reusing principal differs from the original author.

MAC (Stage 5) emits a `memory.reuse_successful(entry_id, downstream_quality_score, downstream_principal)` event on every such qualifying reuse. The event is processed by the promotion job, which is a durable job in the same jobs table. Idempotent: CONFIRMED is terminal.

### 6.5 Experience Library Growth Policy

The library grows monotonically. Entries are never removed by the growth process — only by `delete()` (GDPR), `flag_and_quarantine()` (safety), or the reaper (lifetime expiry of TENTATIVE).

Size bounds are managed by compression of older entries (via Forge/TONL, §3.4), not by culling.

### 6.6 Cross-Session Learning Integration with Stage 5 MAC (named contract)

MAC → Memory:
- `mac.publish(task_signature, outcome, quality_score, quality_confidence)` → Memory writes an admission record.
- `mac.reuse_successful(entry_id, downstream_quality_score, downstream_principal)` → Memory processes promotion.
- `mac.backfill()` → one-time job at first MAC ship; re-scores existing TENTATIVE entries (Req #48). Named deliverable in Stage 5 handoff contract.

Memory → MAC:
- `memory.retrieve_similar_tasks(...)` → MAC seeds Cycle 1 of new deliberations with the result.

---

## 7. Storage Schema

### 7.1 Postgres Tables

```sql
-- praxis/kernel/memory/migrations/0001_memory_initial.py

-- All tables inherit tenant_hash column + CI-enforced base model.

-- Beads
CREATE TABLE beads (
    bead_hash        CHAR(64) PRIMARY KEY,
    tenant_hash      CHAR(64) NOT NULL,
    prev_bead_hash   CHAR(64),
    payload          BYTEA    NOT NULL,           -- serialized via TONL/Forge
    payload_type     TEXT     NOT NULL,           -- 'outcome'|'decision'|'fact'|'delete'|'quarantine'
    operation_type   TEXT     NOT NULL,
    tenant_hash_sig  CHAR(64) NOT NULL,           -- HMAC(tenant_hash, bead_hash) — defense
    emitted_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_beads_tenant_time ON beads (tenant_hash, emitted_at);

CREATE TABLE beads_head (
    tenant_hash      CHAR(64) PRIMARY KEY,
    latest_bead_hash CHAR(64) NOT NULL REFERENCES beads(bead_hash),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Atelier decision memory
CREATE TABLE decisions (
    decision_id          CHAR(26) PRIMARY KEY,        -- ULID
    tenant_hash          CHAR(64) NOT NULL,
    agent_id             TEXT     NOT NULL,
    run_id               CHAR(26) NOT NULL,
    decision             TEXT     NOT NULL,
    rationale            TEXT     NOT NULL,
    alternatives         JSONB    NOT NULL,
    evidence             JSONB    NOT NULL,
    confidence           REAL     NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    outcome_status       TEXT,
    captured_at          TIMESTAMPTZ NOT NULL,
    ttl_days             INT      NOT NULL,
    state                TEXT     NOT NULL CHECK (state IN ('tentative','confirmed','quarantined','expired')),
    state_snapshot_version CHAR(26) NOT NULL,
    reason_hash          CHAR(64),
    embedding            vector(1536),                -- pgvector
    embedding_version    TEXT     NOT NULL,
    schema_version       INT      NOT NULL DEFAULT 1
);
CREATE INDEX ix_decisions_tenant_state ON decisions (tenant_hash, state);
CREATE INDEX ix_decisions_captured_at ON decisions (captured_at);
CREATE INDEX ix_decisions_embedding ON decisions USING hnsw (embedding vector_cosine_ops);

-- Experience library (cross-session learning entries)
CREATE TABLE experience_entries (
    entry_id             CHAR(26) PRIMARY KEY,
    tenant_hash          CHAR(64) NOT NULL,
    task_signature_hash  CHAR(64) NOT NULL,
    task_signature       JSONB    NOT NULL,
    approach_summary     TEXT     NOT NULL,
    quality_score        REAL     NOT NULL,
    quality_confidence   REAL     NOT NULL,
    cost_usd             REAL     NOT NULL,
    reasoning_trace_ref  TEXT,                        -- bead hash reference
    state                TEXT     NOT NULL,
    captured_at          TIMESTAMPTZ NOT NULL,
    embedding            vector(1536),
    embedding_version    TEXT     NOT NULL
);
CREATE INDEX ix_experience_tenant_state ON experience_entries (tenant_hash, state);
CREATE INDEX ix_experience_embedding ON experience_entries USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ix_experience_task_sig ON experience_entries (task_signature_hash);

-- Durable cascade jobs table (delete cascade, admission, promotion, reaper)
CREATE TABLE memory_jobs (
    job_id           CHAR(26) PRIMARY KEY,
    tenant_hash      CHAR(64) NOT NULL,
    job_type         TEXT     NOT NULL,
    payload          JSONB    NOT NULL,
    state            TEXT     NOT NULL CHECK (state IN ('pending','running','succeeded','failed')),
    substep_status   JSONB    NOT NULL DEFAULT '{}'::jsonb,  -- per-substep idempotency
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at       TIMESTAMPTZ,
    finished_at      TIMESTAMPTZ,
    retries          INT      NOT NULL DEFAULT 0
);
CREATE INDEX ix_memory_jobs_pending ON memory_jobs (state, created_at) WHERE state IN ('pending','running');

-- Audit log (salted-hash criteria; never raw values — Req #33)
CREATE TABLE memory_audit_log (
    audit_id        CHAR(26) PRIMARY KEY,
    tenant_hash     CHAR(64) NOT NULL,
    operation       TEXT     NOT NULL,            -- 'delete' | 'export' | 'quarantine' | 'break_glass_state_change'
    criteria_hash   CHAR(64) NOT NULL,            -- salted hash of criteria dict
    salt_epoch_id   TEXT     NOT NULL,            -- references salt retention cohort
    operator        TEXT,                         -- for break-glass writes
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- State-transition break-glass ledger (Req #47) — write-only
CREATE TABLE memory_break_glass_ledger (
    entry_id        CHAR(26) PRIMARY KEY,
    tenant_hash     CHAR(64) NOT NULL,
    operator        TEXT     NOT NULL,
    table_name      TEXT     NOT NULL,
    target_pk       TEXT     NOT NULL,
    old_state       TEXT     NOT NULL,
    new_state       TEXT     NOT NULL,
    justification   TEXT     NOT NULL,
    credential_id   TEXT     NOT NULL,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
REVOKE UPDATE, DELETE ON memory_break_glass_ledger FROM PUBLIC;

-- DB triggers enforce state transitions (Req #47)
CREATE OR REPLACE FUNCTION enforce_state_transition()
RETURNS TRIGGER AS $$
BEGIN
    IF current_setting('praxis.state_change_authorized', true) IS DISTINCT FROM 'true' THEN
        RAISE EXCEPTION 'direct state change without break-glass';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_decisions_state_enforce
    BEFORE UPDATE OF state ON decisions
    FOR EACH ROW EXECUTE FUNCTION enforce_state_transition();

CREATE TRIGGER trg_experience_entries_state_enforce
    BEFORE UPDATE OF state ON experience_entries
    FOR EACH ROW EXECUTE FUNCTION enforce_state_transition();
```

Mem0's tables are owned by Mem0 and not managed by our migrations; Mem0's schema migrations run separately.

### 7.2 SQLite Dev Equivalent

For developer convenience, a SQLite + sqlite-vss variant is available:
- All `vector(1536)` columns become `BLOB` with a sqlite-vss virtual table overlay.
- `TIMESTAMPTZ` becomes `TEXT` with ISO-8601 format.
- Postgres triggers are replaced by CHECK constraints + application-level enforcement.
- Pub/sub LISTEN/NOTIFY is replaced by polling.

The config loader rejects SQLite when `environment=production`.

### 7.3 Migration Approach

Alembic with the Stage 1 convention: one P0 migration per stage. The Stage 3 migration is `0001_memory_initial` and creates everything in §7.1 in a single commit. Future Memory schema changes go through named migrations with the Stage 1 migration-safety harness (Req — mirrors FM1.9 for Memory tables).

---

## 8. Privacy & Scoping Enforcement

This section consolidates the privacy architecture; every requirement from Parts A + C of the binding input is cross-referenced.

### 8.1 Structural Tenant Isolation (managed single-tenant)

Per ratified decision B1, the tenant boundary is the Postgres instance, not the WHERE clause. Each deployment:
- Has its own Postgres instance (enforced at provisioning time by Stage 7 POV Harness infra work).
- Has its own Redis/pub-sub channel (for cache invalidation, #27).
- Has its own secrets (KMS-managed per-tenant key per Req #29).
- Has its own LLM provider credentials (Req #31).
- Has its own Beads worktree directory on disk.
- Has its own deployment manifest YAML in the `praxis-config/deployments/` Git repo (B3 ratification).

At boot, the process:
1. Clones its manifest from Git via deploy-key-authenticated URL.
2. Verifies the manifest signature.
3. Compares DB fingerprint, tenant_hash, environment tag, provider key identifier, seed_version, embedding_model_id, backup destination fingerprint against actual runtime configuration.
4. Scans a sample of rows from `beads`, `decisions`, `experience_entries` — verifies `tenant_hash` matches manifest (Req #6).
5. Registers its DB fingerprint with the Git-backed manifest registry (the CI check on the config repo ensures no duplicate registration — B3).
6. Starts a background task re-running steps 2–4 every 60s (Req #4).

On any failure: `sys.exit(2)`. Process supervisor restarts with a fresh manifest pull.

### 8.2 Memory Facade Enforcement

Every facade method:
1. Validates `tenant_id` parameter against `DeploymentManifest.tenant_id` (in-memory singleton loaded at boot).
2. On mismatch: emits `TelemetryEvent(type="tenant_mismatch_rejected")`, raises `TenantIdentityError`, hard-fails the process.

This is defense-in-depth. Under managed single-tenant the application should never pass a wrong tenant_id — so the failure is a bug, not a user error, and process exit is appropriate.

### 8.3 Data Isolation Guarantees

| Guarantee | Enforcement mechanism | Requirement ref |
|-----------|----------------------|-----------------|
| No cross-tenant retrieval code path | Separate processes per tenant + facade rejection | #1, #11 |
| Beads worktree disjoint from other tenants | Filesystem isolation per deployment | #2 |
| Mem0 collection disjoint | Collection name = `praxis_tenant_{tenant_hash}` | #2 |
| Seed corpus read-only | Facade has no method that writes to seed collection; seed writes are a separate offline CLI tool | #13, #16 |
| Audit log never contains raw criteria | Salted hash at write time | #33 |
| Embeddings purged on delete | Synchronous in delete cascade (Req #34), post-delete verification (Req #26) | #26, #34 |
| Embeddings stripped on quarantine | In-place zero-out during state transition (Req #35) | #35 |
| Cache invalidation on delete | Pub/sub ack aggregation before user ack | #27 |
| Backups crypto-shreddable | Per-tenant encryption key, destroyed on full-tenant delete | #29 |
| LLM provider retention minimized | Zero-retention endpoints default, non-ZDR opt-in | #30 |
| LLM provider cross-tenant attribution impossible | Tenant-scoped API keys, never shared | #31 |
| GDPR Article 15 access uses facade | Same codepath as retrieval | #37 |
| No bypass code paths | `__all__` + `_internal/` + CI lint | #9 |
| State transitions not bypassable at DB | Triggers + break-glass ledger | #47 |

### 8.4 Audit Trail for Retrievals

Retrievals emit a `TelemetryEvent(type="retrieval_completed")` with fields: `tenant_hash`, `agent_id`, `run_id`, `top_k`, `hit_count`, `source_distribution{seed, tenant}`, `retrieval_latency_ms`. NO query content, NO result IDs, NO embeddings. The central observability pipeline receives only this allowlisted set (#51, #53).

For operator debugging: the tenant-local log sink (§10) stores query content + result IDs at DEBUG level. Access requires explicit authorization and is itself audit-logged.

### 8.5 Right-to-Erasure Flow (end-to-end, Req #24–#35)

```
Customer invokes delete(tenant_id, criteria)
  ↓
Memory.delete validates tenant_id ↔ manifest
  ↓
Creates durable job (memory_jobs row) — job_id returned to caller
  ↓
Writes salted-hash audit log entry (criteria_hash, salt_epoch_id)
  ↓
Sub-steps (each idempotent, each checkpointed in memory_jobs.substep_status):
  1. Atelier: DELETE from decisions WHERE matches — purge embedding column
  2. Experience library: DELETE from experience_entries WHERE matches — purge embedding column
  3. Mem0: delete() call per entry_id — purge pgvector rows
  4. pgvector: VACUUM + REINDEX on affected hnsw indexes
  5. Post-delete verification query: by deleted IDs, must return zero hits
  6. Beads: append a delete-operation bead (Merkle audit trail, content-addressed)
  7. Cache invalidation: pg_notify('cache_invalidate', affected_keys)
     Wait for ack from all subscribers (bounded by known-process count + timeout)
  8. Mark memory_jobs.state = 'succeeded'
  ↓
Return DeleteResult to caller

Full-tenant delete additionally:
  9. Crypto-shred: destroy per-tenant backup key via KMS
 10. Emit CostEvent(type="retention_action", subtype="crypto_shred_full_tenant")
 11. Mark deployment manifest for decommissioning
```

Failure in any sub-step: job remains in `running` state; crash recovery re-runs pending sub-steps (each is idempotent so re-running is safe). The caller does NOT receive success until all sub-steps complete.

### 8.6 GDPR Article 15 Export Flow

Same facade, same scoping. Query re-uses `retrieve_*` methods with `top_k` effectively unbounded and a format adapter that serializes results into an export bundle (JSON + optional Markdown per open question N2). The export is emitted to a tenant-local artifact store with an access-control token; the customer downloads via CLI in v1 (#32). Integration test "two-tenant access isolation" is marked CRITICAL (Req #37).

### 8.7 Quarantine Operation (Req #35 in-place embedding strip)

```
Memory.flag_and_quarantine(tenant_id, entry_id, reason_enum, free_text)
  ↓
Validate tenant_id
  ↓
PII-scrub free_text (same redactor as seed ingest)
  ↓
Set praxis.state_change_authorized = 'true' (transaction-scoped)
  ↓
In a serializable transaction:
  UPDATE decisions (or experience_entries) SET
    state = 'quarantined',
    embedding = NULL,              -- #35 in-place strip
    reason_hash = sha256(reason_enum || salt || pii_scrubbed_text),
    state_snapshot_version = new_version()
  WHERE entry_id = ? AND tenant_hash = ?
  ↓
Emit audit log entry (salted hash of quarantine criteria)
  ↓
pg_notify('cache_invalidate', [entry_id]) — same as delete path (Req #50)
  ↓
Append quarantine-operation bead
  ↓
Return QuarantineResult
```

Quarantine is reversible at the state-column level (flip state back) but the embedding is gone — un-quarantining requires re-embedding from the preserved `reason_hash` / `audit_trail`, which is infeasible from hashes alone. Effectively, quarantine destroys retrievability while preserving audit identity.

---

## 9. Observability Hooks

### 9.1 TelemetryEvent Schema (Typed Allowlist)

```python
# praxis/kernel/memory/_internal/telemetry/events.py

class TelemetryEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_type: Literal[
        "retrieval_completed",
        "retrieval_cache_hit",
        "admission_accepted",
        "admission_rejected",
        "tentative_to_confirmed_promoted",
        "fact_ingested",
        "decision_captured",
        "delete_cascade_started",
        "delete_cascade_completed",
        "delete_cascade_step_completed",
        "delete_cascade_verification_failed",
        "quarantine_applied",
        "quarantine_to_delete_transition",
        "cache_invalidation_ack",
        "seed_version_stale_warning",
        "source_distribution",
        "tenant_mismatch_rejected",
        "manifest_verification_failed",
        "mem0_version_bump_test",
        "break_glass_used",
    ]
    tenant_hash: str | None = None         # None only for manifest events

    # Allowlisted dimensions (numeric + aggregate — no content)
    agent_id: str | None = None
    run_id: str | None = None
    top_k: int | None = None
    hit_count: int | None = None
    source_distribution: dict[Literal["seed","tenant"], int] | None = None
    latency_ms: float | None = None
    admission_outcome: Literal["confirmed","tentative","rejected"] | None = None
    quality_score: float | None = None
    quality_confidence: float | None = None
    cache_invalidation_acks: int | None = None
    seed_version: str | None = None
    seed_version_age_days: int | None = None
    mem0_test_class: str | None = None
    mem0_test_result: Literal["passed","failed"] | None = None

    emitted_at: datetime = Field(default_factory=datetime.utcnow)
```

**Any field not in this schema cannot be emitted** — `BaseModel.model_config` rejects extra fields. This closes FM1.4 / FM4.8 by construction: you cannot emit query content or result IDs to central telemetry even if you wanted to, because there's no field to put them in.

### 9.2 Required Telemetry Metrics (Req #55)

| Metric | Type | Labels |
|--------|------|--------|
| `praxis_memory_admission_rate` | Counter | admission_outcome |
| `praxis_memory_rejection_rate` | Counter | - |
| `praxis_memory_tentative_to_confirmed_rate` | Counter | - |
| `praxis_memory_retrieval_score_distribution` | Histogram | - |
| `praxis_memory_p99_retrieval_latency_ms` | Histogram | - |
| `praxis_memory_source_distribution` | Counter | source (seed\|tenant) |
| `praxis_memory_seed_version_age_days` | Gauge | seed_version |
| `praxis_memory_delete_cascade_duration_seconds` | Histogram | - |
| `praxis_memory_quarantine_to_delete_gap_seconds` | Histogram | - |
| `praxis_memory_cache_invalidation_ack_latency_ms` | Histogram | - |

All emitted via the typed `TelemetryEvent` schema; the Prometheus exporter reads the events_outbox-style memory event stream (reusing Stage 1's pattern — events written transactionally, drained asynchronously by a sidecar exporter).

### 9.3 Pi-Mono Integration (CostEvent Emission)

Per Req #57, Memory emits two categories of `CostEvent`:

```python
# On successful retrieval that returns a cache hit
CostEvent(
    event_type="retrieval_cache_hit",
    component="memory",
    tenant_hash=manifest.tenant_hash,
    savings_usd=estimated_downstream_savings_usd,
    metadata={
        "top_k": N,
        "hit_count": M,
        "source_distribution": {"seed": K, "tenant": L},
    }
)

# On delete cascade or quarantine (retention actions)
CostEvent(
    event_type="retention_action",
    component="memory",
    tenant_hash=manifest.tenant_hash,
    savings_usd=0,                     # retention actions don't save cost
    metadata={
        "action": "delete" | "quarantine" | "crypto_shred",
        "affected_count": N,
    }
)
```

**Savings attribution estimate** (for `retrieval_cache_hit`): the estimated downstream savings is the average cost of the equivalent cold-start workflow minus the retrieval cost. The workflow runner (Stage 4 runtime) provides the cold-start cost estimate via workflow type; Memory computes the delta at emit time. This is a heuristic — accurate retrospective attribution requires Stage 5 MAC (measured quality correction) and is out of scope for Stage 3.

### 9.4 OpenTelemetry Integration

The `TelemetryEvent` emitter optionally routes to OTEL spans alongside its primary outbox target. OTEL integration is a Stage 6/7 concern — in Stage 3 we ensure the schema is OTEL-compatible (allowlisted string/number/bool attribute types) but do not ship the exporter.

### 9.5 Tenant-Local Log Sink (Req #54)

A separate in-deployment logging destination that never exports to central observability. Used for debug detail: query content, result IDs, embedding values (dumped only when explicitly enabled by an operator with documented authorization).

Implementation: a rotating file on the deployment filesystem at `/var/log/praxis/memory-debug-{tenant_hash}.log`. Access requires:
1. Explicit authorization from a named break-glass credential.
2. An audit log entry in `memory_audit_log` of type `debug_access`.
3. An entry in `memory_break_glass_ledger` recording operator + justification.

Operators do NOT routinely read this log; it exists for incident response only.

---

## 10. Testability Notes for Murat

This section gives Murat (Test Architect, Stage 3.2) the scaffolding to write a risk-based test strategy.

### 10.1 Retrieval Correctness Tests

- **Pure function tests** for `recency_decay`, `state_weight`, `retrieval_score` (property-based via Hypothesis). Invariants: monotonicity in semantic similarity, non-increasing in age, zero for QUARANTINED/EXPIRED.
- **Integration tests** against a seeded pgvector test database: given a known query and known entries with known embeddings, the top-K result is deterministic and matches the expected ranking.
- **Regression fixtures** for Mem0 upgrade testing — a canonical query set pinned in CI. Any Mem0 upstream change that shifts rankings is a regression.

### 10.2 Privacy Enforcement Tests (CRITICAL — multi-tenant isolation)

- **`test_tenant_mismatch_hard_fails`** — calling the facade with a `tenant_id` that doesn't match the process's manifest raises `TenantIdentityError` and the test harness captures the exit.
- **`test_two_tenant_access_isolation`** — spin up two processes with different tenant_hashes, verify that `Memory.export(tenant_id_A)` never returns any record tagged tenant_hash_B. Marked CRITICAL.
- **`test_facade_no_scope_parameter`** — static analysis test: introspect the `Memory` class and assert no method has a `scope` parameter (Req #12).
- **`test_facade_no_tenant_kwarg`** — introspect methods; no parameter name contains `"tenant"` other than the explicit `tenant_id`. (Lint rule test.)
- **`test_internal_module_not_importable`** — attempt `from praxis.kernel.memory._internal.mem0 import Mem0Client` from outside the memory module, expect `ImportError`.
- **`test_seed_corpus_write_impossible`** — attempt a write with seed collection target via any facade method, expect `ValueError` or method not found.

### 10.3 State Versioning Replay Tests

- **`test_beads_replay_deterministic`** — given a chain of N beads, replaying produces the same final state every time.
- **`test_compaction_idempotent`** — property test: `compact(compact(X)) == compact(X)` on sampled payloads.
- **`test_worktree_isolation_hard_fails`** — start a process whose manifest points to worktree `A` but the filesystem contains worktree `B`: process must sys.exit(2).

### 10.4 Stale Decision Decay Tests

- **`test_ttl_expiry_demotion`** — insert tentative entries with various ages; run reaper; verify >90-day entries are `state=EXPIRED`, ≤90-day entries unchanged.
- **`test_recency_decay_monotonic`** — property test: for fixed semantic similarity, older entries score strictly lower than newer ones.

### 10.5 Delete Cascade Tests

- **`test_delete_cascade_synchronous_embedding_purge`** — after `delete()` returns, query pgvector directly for the affected entry_ids; zero hits.
- **`test_delete_cascade_durable_on_crash`** — crash the process mid-cascade; restart; verify the job resumes and completes.
- **`test_delete_cascade_cache_invalidation_ack_gate`** — `delete()` does NOT return until all known subscribers have acknowledged cache invalidation within timeout.
- **`test_quarantine_embedding_stripped`** — after `flag_and_quarantine()`, direct DB query shows `embedding IS NULL`.

### 10.6 Experience Library Growth Simulation

- **`test_growth_monotonic`** — simulate 1000 workflows, library size grows monotonically.
- **`test_seed_to_tenant_crossover`** — seed 500 records; simulate tenant writes; verify retrieval source distribution shifts per the crossover formula after N=25 tenant writes.
- **`test_admission_outlier_rate_limit`** — simulate a tenant pushing 10x normal admission rate; verify rate-limiting engages and the review queue fills.

### 10.7 Audit Trail Tests

- **`test_audit_log_no_raw_criteria`** — any audit log row must have a salted `criteria_hash`, never a raw criteria dict. CI-enforced.
- **`test_break_glass_ledger_append_only`** — attempt UPDATE/DELETE on `memory_break_glass_ledger`; expect permission denied.

### 10.8 Mem0 Integration Tests (Req #58)

The four test classes enumerated in §4.1 — all four must pass on every CI build and every Mem0 version bump.

---

## 11. Open Questions

All 13 CONCERN + 7 NICE-TO-HAVE questions from `requirements.md` §"Updated Open Questions for Andrey" that remain unresolved are carried forward here. Winston does NOT need them answered before drafting architecture.md — they affect implementation details only.

**Still open after Andrey's ratification:**

| Ref | Question | Winston's strawman assumption for this draft |
|-----|----------|----------------------------------------------|
| C1 (Q1-b) | Is single-tenant-per-deployment compatible with Stage 7 pricing? | Yes — pricing is per-session orchestration fee, decoupled from infra cost. Flag to Stage 7 for confirmation. |
| C2 (Q2-b) | Seed corpus licensing sign-off authority? | Andrey (v1), Stage 6 Studio defines ongoing role. |
| C3 (Q2-c) | Any customer segment requiring cross-tenant learning? | No — B1 ratified. Strict isolation is the v1 stance. |
| C4 (Q3-a) | DPA template gap acceptable for Stage 7? | Yes — 1-2 weeks legal drafting at first enterprise ask. |
| C5 (Q3-b) | Audit log retention default? | 2 years (strawman from requirements.md). Configurable. |
| C6 (Q3-d) | GDPR Article 15 access API — CLI-only or programmatic? | CLI-only v1 (#32). Programmatic surface deferred to Stage 6 if Studio integration requests it. |
| C7 (Q4-a) | MAC threshold calibration — Stage 5 elicitation or strawman? | Strawman `0.8 / 0.5 / C_min=0.6` (Req #40 defaults). Stage 5 may calibrate. |
| C8 (Q4-b) | Quarantine admin surface — CLI/API or UI? | CLI/API only v1. UI is Stage 6 Studio. |
| C9 (Q4-c) | Reuse-success signal 7-day async lifecycle acceptable? | Yes — documented in §6.4. Users who want determinism use `state_snapshot_version`. |
| C10 (Q4-d) | Library-health dashboard — operator-only or customer-facing? | Operator-only v1 (#56). Stage 6 decides customer-facing. |
| C11 | Tentative entry max-lifetime 90 days? | Yes (strawman). Configurable in deployment manifest. |
| C12 | Break-glass credential owner and audit process? | Operator role. Procedure documented in deployment runbook (Stage 7). |
| C13 | `quality_confidence` signal from MAC — Stage 5 contract or Memory requests it? | Stage 5 publishes both score and confidence. Named in §6.6 handoff contract. |
| N1 | Central observability platform target? | Undecided — allowlist schema is platform-agnostic. |
| N2 | Article 15 export format? | JSON primary, Markdown optional. Stage 6 Studio may add more formats. |
| N3 | Seed corpus quarterly refresh cadence? | Quarterly (strawman). Adjustable. |
| N4 | Manifest signing authority and key rotation? | Praxis deploy tool owns the key; rotation at Stage 7 ops design. |

**New open questions raised by this architecture:**

| Ref | Question |
|-----|----------|
| W1 | Mem0 minor-version pinning window — how aggressive should the integration test harness be about accepting patch updates? |
| W2 | Beads worktree garbage collection — after retention-policy expiry, should pruned bead hashes be retained as tombstones for audit continuity, or fully removed? |
| W3 | Cache-invalidation pub/sub ack timeout — strawman 5s; if some process is slow/dead, do we block the user delete forever, or fall back to best-effort after timeout? (Req #27 literally says "ack aggregation gates user-facing delete" — this means blocking, but we need a sanity timeout.) |
| W4 | KMS provider selection for per-tenant backup encryption — AWS KMS, GCP KMS, HashiCorp Vault? Affects ops complexity. Pick at Stage 7 infra design. |
| W5 | `context_fingerprint` computation — does it read actual content embeddings at signature time (requires an LLM call) or approximate via hash of content IDs (cheap but less accurate)? Tradeoff affects retrieval precision. |

---

## 12. Integration Pass — Requirement Coverage Index

This table maps every binding requirement (#1–#58) from `requirements.md` to the section in this document where it is honored. A row marked "–" means the requirement is honored in more than one section.

_(The integration pass runs after all reference-derived sections are filled in. The table below covers the skeleton v0.1 coverage.)_

### Part A — Tenancy & Isolation (Reqs 1–11)

| # | Requirement (abbrev) | Section |
|---|-----------------------|---------|
| 1 | tenant_id required on every method | §2.1, §2.3, §8.2 |
| 2 | Worktrees/collections inherit from deployment config | §2.3, §3.3, §8.1 |
| 3 | Signed deployment manifest contents | §8.1 (post-B3 Git form) |
| 4 | Manifest verified on boot + every 60s | §8.1 |
| 5 | Manifest registry prevents duplicate DB fingerprint | §8.1 (Git CI check per B3) |
| 6 | `tenant_hash` column on every row | §2.2, §7.1 base model, §8.1 step 4 |
| 7 | No "tenant" kwarg on methods | §2.1, §10.2 test |
| 8 | No raw query builder | §0 principle 4, §2.1 |
| 9 | `__all__` + `_internal/` + CI lint | §3.1 module layout, §10.2 test |
| 10 | In-process caches keyed on tenant_id tuples | §9.5 (applies to cache layer; will be detailed in Mem0 read pass) |
| 11 | No cross-tenant retrieval code path | §0 principle 6, §8.3 |

### Part B — Scope, Seed Corpus, First-Session Value (Reqs 12–23)

| # | Requirement (abbrev) | Section |
|---|-----------------------|---------|
| 12 | Scope enum (TENANT, SEED_CORPUS); writes method-implicit | §0 principle 5, §2.1, §10.2 test |
| 13 | Seed corpus is separate Mem0 collection, read-only | §2.3, §4.2 config |
| 14 | `seed_version` = sha256(content) + embedding_model_id + schema_version | §4.2 config comment |
| 15 | Seed versions retained indefinitely in Beads | §3.4 retention policy |
| 16 | Seed ingest is separate offline tool | §0 principle 5, §2.1 comment |
| 17 | License attestation per record | §5 (seed ingest tool spec — pending Atelier read) |
| 18 | PII scanner in seed ingest | §5 (seed ingest tool spec — pending Atelier read) |
| 19 | Quarterly refresh + legal review gate | §11 open question N3 |
| 20 | `seed_version` expiry + stale warning telemetry | §9.1 event_type, §9.2 gauge |
| 21 | Seed corpus bundled in distribution image | §4.2 config note |
| 22 | Source-distribution telemetry per retrieval | §2.1 docstring, §9.1, §9.2 |
| 23 | Crossover formula = pure function + tests | §10.1 retrieval correctness |

### Part C — Deletion, Access, GDPR (Reqs 24–37)

| # | Requirement (abbrev) | Section |
|---|-----------------------|---------|
| 24 | `delete(scope, criteria)` cascades across all stores | §2.1, §8.5 |
| 25 | Delete cascade is a durable job | §3.1 `cascade/` module, §7.1 memory_jobs, §8.5 |
| 26 | Vacuum/reindex + post-delete verification in cascade | §8.5 step 4–5 |
| 27 | Cache-invalidation pub/sub + ack aggregation | §8.5 step 7, §11 W3 timeout question |
| 28 | Async rewrites mark state=QUARANTINED synchronously | §5.4 reaper logic |
| 29 | Tenant-scoped encrypted backups + crypto-shred | §8.3 table, §8.5 step 9, §11 W4 KMS question |
| 30 | Zero-retention LLM endpoints default | §8.3 table |
| 31 | Tenant-scoped LLM provider API keys | §4.2 config, §8.1 boot, §8.3 table |
| 32 | GDPR Article 15 export API exposed | §2.1, §8.6 |
| 33 | Salted-hash audit log for criteria | §7.1 memory_audit_log, §8.5 |
| 34 | Embeddings purged on delete | §8.5 steps 1–3 |
| 35 | Quarantine strips embeddings in-place | §8.7 |
| 36 | Default residency = deployment location | §8.3 table |
| 37 | Access API uses same facade scoping | §2.1, §8.6, §10.2 CRITICAL test |

### Part D — Experience Library, Admission, Governance (Reqs 38–50)

| # | Requirement (abbrev) | Section |
|---|-----------------------|---------|
| 38 | `state` first-class column with 4 values | §5.1, §7.1 decisions CHECK constraint |
| 39 | Composite admission signal + outlier detection | §6.3 |
| 40 | Admission thresholds (0.8/0.5/C_min) | §6.3 |
| 41 | Tentative max-lifetime + EXPIRED demotion | §5.4 reaper, §11 C11 |
| 42 | Promotion requires downstream quality + principal differ | §6.4 |
| 43 | Retrieval score formula | §5.3 |
| 44 | `state_snapshot_version` in retrieval response | §2.2, §5.1, §11 C9 |
| 45 | Structured quarantine reason enum + PII-scrubbed free text | §2.2 enum, §8.7 flow |
| 46 | Quarantine ≠ delete documented | §8.7 (reversibility note); admin tooling doc in Stage 6 |
| 47 | DB triggers enforce state transitions + break-glass ledger | §7.1 trigger, §8.5 audit log |
| 48 | MAC → Memory backfill named deliverable | §6.6 |
| 49 | MAC-absent mode: all-tentative with explicit logging | §6.6 — logged as degraded-mode warning |
| 50 | Quarantine emits cache-invalidation event | §8.7 |

### Part E — Observability, Telemetry, Cross-Cutting (Reqs 51–58)

| # | Requirement (abbrev) | Section |
|---|-----------------------|---------|
| 51 | Typed `TelemetryEvent` with allowlist | §9.1 |
| 52 | Zero raw-string logs in Memory module | §0 principle 8, §9.1 (by construction) |
| 53 | Central obs gets only numeric/aggregate + allowlisted structured | §9.1, §9.2 |
| 54 | Tenant-local log sink | §9.5 |
| 55 | Required telemetry metrics | §9.2 |
| 56 | Retrieval-quality dashboard operator-facing v1 | §11 C10 |
| 57 | Pi-Mono CostEvent integration (retrieval_cache_hit, retention_action) | §9.3 |
| 58 | Mem0 integration test harness | §4.1, §10.8 |

**Coverage status for v1.0 (post-reference-reads):** 58 / 58 requirements referenced. All _pending_ sections are now filled in:

| Section | Read source | Status |
|---------|-------------|--------|
| §1.1 Beads patterns | gastownhall-beads dump (Grep-extracted) | v1.0 complete |
| §1.2 Mem0 integration points | mem0ai-mem0 dump (Grep-extracted) | v1.0 complete |
| §1.3 Atelier patterns | robertsfeir-atelier dump (Grep-extracted) | v1.0 complete |
| §3.6 Beads port plan | Derived from §1.1 | v1.0 complete — includes launch-prompt correction (§3.7) |
| §4.5 Mem0 adapter | Derived from §1.2 | v1.0 complete |
| §5.5 Atelier adoption | Derived from §1.3 | v1.0 complete — adds `importance`, ltree scope, `last_accessed_at`, `decision_relations`, `decision_type_config`, `trace_decision()` |

### 12.1 Post-Reference Additions Requiring Cross-Section Updates

The sequential reference reads produced design changes that cascade into multiple sections. This subsection makes them explicit so a reader who starts at §7 (schema) is not surprised by a column that only appears in §5.5.

**Schema additions (not in §7.1's initial skeleton):**

```sql
-- Added to decisions table after Atelier read:
ALTER TABLE decisions ADD COLUMN importance REAL NOT NULL CHECK (importance BETWEEN 0 AND 1) DEFAULT 0.5;
ALTER TABLE decisions ADD COLUMN scope LTREE NOT NULL;
ALTER TABLE decisions ADD COLUMN last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE decisions ADD COLUMN superseded_by CHAR(26) REFERENCES decisions(decision_id);
ALTER TABLE decisions ADD COLUMN thought_type thought_type_e NOT NULL DEFAULT 'decision';
ALTER TABLE decisions ADD COLUMN source_phase source_phase_e NOT NULL DEFAULT 'runtime';

CREATE EXTENSION IF NOT EXISTS ltree;

CREATE TYPE thought_type_e AS ENUM (
    'decision','pattern','lesson','insight','rejection','preference'
);

CREATE TYPE source_phase_e AS ENUM (
    'elicitation','design','implementation','quality','handoff','runtime','pipeline'
);

-- decision_relations table (see §5.5 for full definition)
-- decision_type_config table (see §5.5 for full definition)

CREATE INDEX ix_decisions_scope ON decisions USING gist (scope);
CREATE INDEX ix_decisions_last_accessed ON decisions (last_accessed_at);
```

These should be folded into the single `0001_memory_initial` Alembic migration; they appear separately here only for traceability. Amelia MUST merge them into one migration file — do NOT ship six separate migrations.

**Facade method additions (not in §2.1's initial draft):**

```python
class Memory(Protocol):
    # ... existing methods from §2.1 ...

    async def trace_decision(
        self,
        tenant_id: str,
        decision_id: str,
        depth: int = 10,
    ) -> DecisionProvenance: ...
    """Walks decision_relations graph backward from decision_id.
       Returns a tree of predecessor decisions up to `depth` levels.
       Used by GDPR export and human audit queries. (Atelier AT13)"""
```

**New dependency: Postgres `ltree` extension.** Stage 7 deployment infra must install this extension alongside `pgvector`. Noted in the deployment manifest schema (§8.1).

**Retrieval side-effect: `last_accessed_at` touch.** Every successful retrieval updates `last_accessed_at` on the returned decisions via a single UPDATE batch. This is a write in the retrieval path — documented here so Murat's test strategy can verify the read-vs-write boundaries.

### 12.2 Requirement Coverage (Post-Reference Verification)

No requirement from §12's A–E coverage table was invalidated by the reference reads. The reads ADDED material (importance, ltree scope, decision relations, trace query, auto-capture details) but did not remove anything. Two requirements gained new enforcement sections:

- **Req #6 (`tenant_hash` on every row)** now additionally applies to `decision_relations` and `decision_type_config`.
- **Req #43 (retrieval scoring formula)** has a detailed reconciliation note in §5.3 explaining why we use multiplicative despite Atelier's additive precedent. The form is unchanged; the rationale is strengthened.

### 12.3 Launch Prompt Discrepancies — Winston's Raise-Back List

Per Pipeline §4.5 rule 3, Winston raises disagreements in-document rather than silent-overriding. The Stage 3 launch prompt has two characterizations Winston is adjusting:

| Prompt line | Prompt claim | Winston's adjustment | Evidence |
|-------------|--------------|---------------------|----------|
| 42 | "Beads ... COPY/PORT (TypeScript → Python)" | Beads is Go + Dolt, not TypeScript. Literal port would land us with Dolt as a second DB engine. Adjustment: pattern extraction, re-implemented on Postgres. | §1.1, §3.6, §3.7 |
| 110 | "Forge compaction applies to bead storage" | Forge is conversation-shape-specific. For structured-record beads (decisions, facts) we use TONL. For conversation-shape beads, Forge applies. Adjustment: mixed-strategy compaction per payload type. | §3.4 |

Neither adjustment changes the Stage 3 deliverables or the requirement set. If Andrey wants the literal port strategy, Stage 3 will need a 4-6 week extension for Dolt Python bindings. If Andrey wants single-strategy compaction, we need either a Forge generalization to non-conversational payloads (~2 weeks Stage 2 work) or a TONL-only strategy (loses reasoning-chain preservation for compacted conversation beads). Winston's default is the mixed strategy above.

---

## Signoff & Next Step

**This document (v1.0)** is the completed Stage 3.1 architecture draft. It covers:
- All 58 binding requirements from `memory/requirements.md` (§12 coverage index)
- All 11 deliverable sections from the Stage 3 launch prompt
- Pattern extractions from Beads, Mem0, and Atelier via sequential Grep-based reference reads (Pipeline §4.6)
- Two launch-prompt raise-backs (§12.3): Beads port strategy + Forge/TONL mixed compaction
- 5 new open questions (W1–W5 in §11) raised by the architecture itself

**Handoff to Stage 3.2 (Murat — Test Architect):**
- Test strategy should use §10 (Testability Notes) as starting scaffolding.
- CRITICAL tests called out: two-tenant access isolation (§10.2), delete cascade durable-on-crash (§10.5), quarantine embedding strip (§10.5), Mem0 integration harness (§10.8).
- Risk-based test prioritization: FM3.1, FM3.2, FM3.9, FM3.10, FM3.11, FM1.2, FM4.8 are all RPN ≥ 12 and should anchor test effort.
- Open question for Murat: acceptance threshold for the cache-invalidation ack timeout (§11 W3) affects the delete cascade test design.

**Handoff to Stage 3.3 (Amelia — Developer):**
- Module layout in §3.1.
- Beads port plan in §3.6 — **do NOT translate Dolt's Go code literally.** Re-implement the patterns on Postgres + SQLAlchemy as described.
- Mem0 integration is a thin adapter per §4.5 — do NOT fork Mem0.
- All schema goes into a single Alembic migration `0001_memory_initial` (per §12.1 note).
- Apply the Universal Sequential Reference Reading rule yourself: read Mem0 selectively from its reference dump, not the whole 7.8MB file.

**Handoff to Stage 4 (Runtime) — integration contract:**
- Memory facade is ready to bind to Stage 4's agent loader.
- Auto-capture hook expects an `AgentCompleted(agent_id, run_id, final_output)` event from the Stage 4 runtime (§5.5 AT9 pattern).
- Cross-session retrieval uses the `TaskSignature` model (§2.2); Stage 4 must populate these when invoking workflows.

**Handoff to Stage 5 (MAC) — named dependencies:**
- `quality_score` AND `quality_confidence` per completed task (Req #39, §6.6)
- `memory.reuse_successful(entry_id, downstream_quality_score, downstream_principal)` event (§6.4, §6.6)
- Backfill job at MAC first-ship (Req #48, §6.6)
- Distribution-shift detection via confidence drops (§6.6)

**Winston remains available for elicitation** if any strawman assumption in §11 or the raise-backs in §12.3 need revisiting before Murat or Amelia begin.

---

**Stage 3.1 Gate:** Checklist from Pipeline.md step 3.1:
- [x] READS requirements.md from elicitation rounds BEFORE designing
- [x] Architecture doc at `_bmad-output/implementation-artifacts/praxis/memory/architecture.md`
- [x] Unified Memory interface designed
- [x] Beads port plan (Go→Python, pattern extraction)
- [x] Mem0 dependency strategy (pip install, no fork)
- [x] Atelier decision memory pattern extraction
- [x] Privacy model from elicitation explicitly enforced in design
- [x] Context strategy: Universal Sequential Reference Reading applied via Grep-based selective reads

All checklist items satisfied. Ready for Pipeline Stage 3.2 (Murat).
