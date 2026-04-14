# Stage 4 — Stage 3 Deferred Findings Brief for Winston

**Audience:** Winston (Architect), about to execute Stage 4.1 `/bmad-agent-architect`
**Author:** Andrey (via assistant)
**Date:** 2026-04-13
**Status:** Binding input to Stage 4.1 architecture.md — Winston MUST absorb F-1 and F-3 into the Agent Runtime design
**Source of truth:** `_bmad-output/implementation-artifacts/praxis/memory/alignment-review.md` §2, §3, §6, §7
**Authority:** Pipeline.md Section 4.7 (added 2026-04-13) — F-1 + F-3 closure is a Stage 5 gate requirement; F-2 is explicitly parked

---

## 1. Purpose

Stage 3 (Memory) landed with four tracked findings in its alignment review. Two of them (F-1, F-3) are HIGH severity and structurally belong to the Stage 4 Orchestrator — they were deliberately deferred per the Stage 2 precedent (cross-stage wiring is the downstream stage's concern, not the upstream stage's rework). This brief translates those two findings into architectural inputs Winston can absorb at 4.1 draft time.

**What this brief does:** State the problem, locate the seam, list what Winston MUST design.
**What this brief does NOT do:** Propose solutions. Winston owns the architectural shapes. Amelia owns implementation.

**F-2** (Memory → Compression passthrough) is explicitly parked as a Stage 6 optimization pass — **not a Stage 4 concern**. Noted for completeness in §4 so Winston doesn't re-open it mid-architecture.

---

## 2. F-1 — Memory → Pi-Mono CostEvent Wiring

### 2.1 Problem Statement

The Memory architecture documents `CostEvent` emission to Pi-Mono in two places:

- `memory/architecture.md §3.5` — "a bead write and a `CostEvent(type='retention_action')` are written in the **same database transaction**… reuses the Stage 1 guarantee exactly — no new durability machinery is introduced."
- `memory/architecture.md §9.3` — Memory emits two `CostEvent` categories: `retention_action` (reaper + crypto-shred) and `record_created` (Mem0 fact extraction, component tag `memory.mem0.*`).

**Binding requirement #57** (from `memory/requirements.md`): *"Memory integrates with Pi-Mono (Stage 1) as a cost attribution source. Retrievals emit `CostEvent` of type `retrieval_cache_hit` with savings attribution. Delete cascades emit `CostEvent` of type `retention_action`."*

**Current implementation state** (verified via grep on `_bmad-output/implementation-artifacts/praxis/memory/src/`):

```
grep "praxis.kernel.cost|CostEvent|CostTracker" src/praxis/kernel/memory/**/*.py
  → 0 import matches
  → CostEvent appears ONLY in docstrings (_internal/protocol.py:189, :223)
```

Memory is a self-contained package. It has no runtime dependency on `praxis.kernel.cost`. The wiring that would emit CostEvents to Pi-Mono's outbox does not exist.

### 2.2 The Seam (Where Memory Stops and Stage 4 Starts)

The integration seam is a single property on the facade:

**File:** `memory/src/praxis/kernel/memory/facade.py:142`

```python
@property
def audit_buffer(self) -> AuditBuffer:
    """Read-only accessor for tests and ops tooling.

    Stage 7 wiring will replace this with a durable sink adapter;
    the property remains for backward compatibility.
    """
    return self._audit
```

> **Note on docstring drift:** The docstring references "Stage 7 wiring." Per `memory/alignment-review.md §6`, this is **Stage 4**, not Stage 7. This is a minor comment drift introduced during Stage 3.3; Amelia or post-4.3 cleanup should reconcile. Not load-bearing for Winston's architecture.

Every Memory write path calls `_audit_append(...)` (facade.py:173), which appends a typed `AuditEvent` record to the in-memory `_audit` buffer. The buffer exposes `tenant_hash`, `method`, `event_type`, `criteria_hash`, `entry_id`, `outcome`, and `created_at`.

**The Stage 4 Orchestrator's job:** Construct an adapter that drains `Memory.audit_buffer` → translates `AuditEvent` records into Pi-Mono `CostEvent` records → writes them to Pi-Mono's existing transactional outbox.

### 2.3 What Pi-Mono Already Provides (Re-use, Don't Rebuild)

Pi-Mono (Stage 1) has the full cost-tracking plumbing shipped and tested:

| Component | Location | Purpose |
|---|---|---|
| `CostEvent` model | `pi-mono/src/praxis/kernel/cost/models.py:335` | Frozen Pydantic event schema |
| `CostTracker` | `pi-mono/src/praxis/kernel/cost/tracker.py:42` | Async API: `track_cost`, `track_raw_response` |
| Transactional outbox | `pi-mono/src/praxis/kernel/cost/storage/schema.py:106` (`events_outbox` table) | Stage 1's durability guarantee |
| Outbox gauge + telemetry | `pi-mono/src/praxis/kernel/cost/telemetry.py:44` | Prometheus `praxis_cost_outbox_undelivered` |
| Outbox undelivered count | `pi-mono/src/praxis/kernel/cost/storage/repository.py:283` | Query for operational visibility |

**Implication for Winston:** F-1 does NOT require new durability machinery. Pi-Mono's outbox pattern is the canonical emission path. Stage 4's Orchestrator just needs to plug Memory's audit stream into it.

### 2.4 What Winston MUST Design in architecture.md

Specific architectural shapes Winston owns in 4.1:

1. **Outbox adapter shape** — What Python class/interface does the Orchestrator expose to drain Memory's audit buffer? Is it polling-based (Orchestrator ticks every N ms), event-driven (Memory emits a hook), or transactional (Memory's `_audit_append` directly writes to Pi-Mono's outbox within the same DB transaction)? Each choice has trade-offs for latency, coupling, and failure semantics.

2. **Trigger points from Memory** — The Orchestrator must know *which* `_audit_append` call sites emit CostEvents and *which category*. Memory's architecture §9.3 specifies two categories (`retention_action`, `record_created`) plus req #57's `retrieval_cache_hit`. Winston should catalogue the mapping in architecture.md §3 or §5 so Amelia doesn't guess during implementation.

3. **Failure semantics** — If Pi-Mono's outbox write fails, does the Memory operation fail, retry, or degrade gracefully? Stage 2 precedent (compression tags) degraded gracefully; Stage 4 for Memory cost events may need stricter semantics because cost attribution feeds billing and NFR-C-A1 crypto-shred verification.

4. **Tenant identity passthrough** — Every CostEvent must carry a tenant identifier consistent with the manifest pinning (R3, R4, R6). Winston should specify whether the Orchestrator reads tenant from Memory's audit record or from its own deployment manifest (they should be structurally identical per R6, but the design must say so explicitly).

5. **Integration with Stage 4's own cost events** — Stage 4 Orchestrator will also emit its own CostEvents for agent spawns, tool calls, etc. Winston should unify the category taxonomy so Memory's events and Runtime's events compose cleanly in Pi-Mono aggregations (`memory.retention_action` vs. `runtime.tool_call` vs. `runtime.agent_spawn`, for example).

### 2.5 What Winston MUST NOT Design

- The CostEvent schema itself (already shipped in Pi-Mono `models.py:335` — do not redesign)
- The outbox durability mechanism (already shipped in `schema.py:106` — reuse, do not replace)
- The `audit_buffer` property signature (frozen by Memory's public contract — Stage 4 consumes, does not modify)
- Memory's `_audit_append` call sites (Stage 3 code — frozen by binding condition #4 of Pipeline.md Stage 4 pre-work)

### 2.6 NFR Anchors

F-1 closure unlocks these NFRs which are currently structurally deferred:

- **NFR-C-A1** (7-day crypto-shred SLA) — depends on `retention_action` CostEvents being durably emitted so the retention reaper's work is auditable
- **NFR-Q6** (5-min RTO for crash recovery) — requires the outbox pattern Stage 4 wires to Memory (shared fate with F-3)
- **NFR-Q2** (entry ceiling 100K soft / 250K hard) — requires CostEvent telemetry wiring so the ceiling can be enforced operationally

---

## 3. F-3 — Durable Jobs Table for Retention Reaper

### 3.1 Problem Statement

Memory's retention reaper (deletion, crypto-shred, quarantine-to-delete) is currently backed by an **in-memory** audit buffer. Per `memory/alignment-review.md §6`:

> *"Durable jobs table for retention reaper. Current implementation uses an in-memory audit buffer; Stage 4 must provide a Postgres/SQLite jobs table substrate before crypto-shred SLA can be claimed."*

**What this blocks** (from `alignment-review.md §7`):

- **NFR-C-A1** — 7-day crypto-shred SLA cannot be honored because there is no durable record of pending shred jobs. If the process crashes mid-reaper, there is nothing to recover from.
- **NFR-Q6** — 5-min crash RTO cannot be honored for the retention-action work path. The in-memory buffer is lost on restart.

This is the **blocking constraint** for any customer invoking right-to-erasure (GDPR Article 17) on a multi-day timeline.

### 3.2 What Winston MUST Design

Specific architectural shapes Winston owns in 4.1:

1. **Jobs table schema** — A Postgres table (or SQLite fallback for single-tenant dev mode) that durably records every retention-action job. Minimum columns Winston must specify:
   - Job identity (`id`, `tenant_hash`, `job_type` enum)
   - Payload (opaque or typed per job_type)
   - Lifecycle state (`pending`, `claimed`, `in_progress`, `completed`, `failed`, `abandoned`)
   - Timestamps (`created_at`, `claimed_at`, `started_at`, `completed_at`)
   - Retry state (`retry_count`, `max_retries`, `next_retry_at`)
   - Failure context (`last_error`, `failure_reason_enum`)
   - Claim fencing (`claim_token`, `claim_expires_at` — for worker crash detection)

   Winston does not need to specify migrations or exact SQL; he needs to specify **the columns that exist** and **the state transitions that are legal**.

2. **Worker loop lifecycle** — How does the reaper worker claim-process-ack jobs? Single-worker-per-deployment? Multi-worker with claim fencing? Winston's choice interacts with tenant scoping (single-tenant-per-deployment per R1–R6 means single-worker is tractable).

3. **Crash recovery semantics** — On process restart, how does the worker discover claimed-but-not-acked jobs? What's the claim-token expiry policy that NFR-Q6 5-min RTO implies? (Hint: claim expiry ≤ 5 min, worker reclaims expired jobs on restart.)

4. **Failure recovery semantics** — What happens to a job that fails its retry budget? Alert + operator intervention? Quarantine state? Auto-abandon with audit trail? Winston must specify because it interacts with req #25 ("Delete cascade is a durable job (written to a jobs table before starting). Each sub-step is idempotent. Crash recovery re-runs pending sub-steps. User delete is NOT acknowledged until all sub-steps complete.")

5. **Deployment topology** — **Open question for Winston to decide**: Is the jobs table tenant-scoped (one table per deployment, aligned with R1 single-tenant-per-deployment pin) or is there a shared-infra Postgres with tenant-hash column enforcement? Both are compatible with R6 ("every row… carries a `tenant_hash` column via a mandatory base model class"), but they have different operational implications. Winston must make this call because it shapes §4 Spawner, §9 Security Model, and §10 Observability simultaneously.

6. **Integration with the F-1 outbox** — Should the jobs table and the Pi-Mono outbox share a database (enabling transactional coordination — jobs insert + CostEvent emit atomically) or be separate (independent failure modes)? Memory architecture §3.5 says "same database transaction" for bead writes + CostEvents — does that invariant extend to jobs table writes + CostEvents?

### 3.3 What Winston MUST NOT Design

- The reaper worker implementation (Amelia's job)
- The exact migration DDL (Amelia's job)
- Memory's public API (frozen)
- Alternative architectures that bypass the jobs table — per `alignment-review.md §6`, the jobs table is the required substrate

### 3.4 NFR Anchors

F-3 closure unlocks:

- **NFR-C-A1** — 7-day crypto-shred SLA becomes honorable because every shred job is durably recorded and crash-recoverable
- **NFR-Q6** — 5-min crash RTO becomes measurable because worker claim expiry + reclaim semantics provide a deterministic recovery path

---

## 4. F-2 — Parked (Noted for Completeness)

**F-2:** Memory → Compression TONL encoding of bead payloads (`memory/architecture.md §3.4`)

**Status:** Explicitly parked per Pipeline.md Section 4.7 (addition #3) and earlier binding condition #3 from 2026-04-13. F-2 is a cost optimization, not a correctness issue — bead writes work correctly with raw JSON payloads. The TONL encoding would reduce storage footprint but is not on Stage 4's critical path.

**Reassessment trigger:** Stage 6 optimization pass. If compression cost data reveals a meaningful storage-cost lever, revisit then.

**Action for Winston:** Do NOT absorb F-2 into Stage 4.1 architecture. If Winston's design naturally exposes a TONL-encoding seam at the Memory boundary (e.g., via a pluggable encoder interface on the Beads store), that's a free optionality; if it requires architectural effort, defer.

---

## 5. Handoff Checklist for Winston's architecture.md

Winston's 4.1 draft must produce evidence of absorbing F-1 and F-3. This checklist is the minimum bar for alignment review 4.5 to close F-1 and F-3:

### F-1 (Pi-Mono CostEvent wiring)

- [ ] architecture.md §3 or §5 names the outbox adapter component explicitly
- [ ] architecture.md specifies the adapter shape choice (polling / event-driven / transactional)
- [ ] architecture.md catalogues the trigger-point mapping (which Memory operation emits which CostEvent category)
- [ ] architecture.md specifies failure semantics (fail-hard / retry / graceful-degrade)
- [ ] architecture.md specifies tenant identity passthrough rules from Memory audit records to Pi-Mono CostEvents
- [ ] architecture.md unifies Memory's CostEvent categories with Runtime's own CostEvent taxonomy
- [ ] architecture.md §8 Integration Contracts explicitly lists the F-1 adapter as a Stage 4 deliverable

### F-3 (Durable jobs table)

- [ ] architecture.md §4 (Spawner) OR a new §X (Jobs Infrastructure) names the jobs table component
- [ ] architecture.md specifies the jobs table columns (minimum list from §3.2 item 1 above)
- [ ] architecture.md specifies legal state transitions and failure handling
- [ ] architecture.md specifies worker loop lifecycle (single / multi-worker, claim fencing)
- [ ] architecture.md specifies crash recovery semantics consistent with NFR-Q6 5-min RTO
- [ ] architecture.md decides deployment topology (tenant-scoped DB vs. shared with RLS) with rationale
- [ ] architecture.md specifies whether jobs table and outbox share a database (transactional coordination question)
- [ ] architecture.md §11 Testability Notes includes crash-recovery and claim-expiry test requirements for Murat

### F-2 (parked)

- [ ] architecture.md §12 Open Questions notes F-2 as Stage 6 reassess (no active work)

---

## 6. Pre-Condition Before Winston Fires

Before Winston begins Stage 4.1, his frame must load **three documents** (not just `stage-4-winston-prompt.md`):

1. `_bmad-output/planning-artifacts/Praxis/stage-4-winston-prompt.md` — existing architect frame (266 lines)
2. `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md` — 4.0.1 Carson output (tool library catalog he must anchor §6 on, cannot invent tools)
3. **This brief** — F-1 + F-3 architectural inputs he must absorb into §3/§4/§5/§8/§9

Winston's `architecture.md` §6 Tool Library Catalog is *constrained* by document 2. Winston's `architecture.md` §3/§4/§5/§8/§9 is *constrained* by document 3. Document 1 is the baseline frame; documents 2 and 3 are the Stage-3-to-Stage-4 handoff contracts.

---

## 7. Summary Table

| Finding | Severity | Seam | Winston Owns | Amelia Owns | NFRs Unblocked | Stage 4 Status |
|---|---|---|---|---|---|---|
| **F-1** | HIGH | `Memory.audit_buffer` property (facade.py:142) | Adapter shape, trigger mapping, failure semantics, taxonomy unification | Adapter implementation, wiring, tests | NFR-C-A1, NFR-Q6, NFR-Q2 | MUST CLOSE before 4.6 completion |
| **F-3** | HIGH | New jobs table (does not exist yet) | Schema, worker lifecycle, crash recovery, deployment topology | DDL, worker implementation, crash-recovery tests | NFR-C-A1, NFR-Q6 | MUST CLOSE before 4.6 completion |
| **F-2** | MEDIUM | (no seam needed at Stage 4) | — | — | — | **PARKED to Stage 6** |
| F-4 | LOW | — | — | — | NFR-P-R1 (naturally closed by 3.6) | Closed by Stage 3.6 |

---

**End of brief. Length: ~1.5 pages equivalent. Winston has everything he needs to absorb F-1 and F-3 into 4.1.**
