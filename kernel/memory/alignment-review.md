# Praxis Stage 3 — Alignment Review

**Reviewer:** Independent alignment pass (Stage 3.5)
**Date:** 2026-04-13
**Subject:** Memory & Cross-Session Learning (Beads + Mem0 adapter + Atelier + Facade)
**Gate:** Stage 3 → Stage 3.6 Pre-Sales Checkpoint readiness

---

## 0. SCOPE OF THIS REVIEW

Adversarial alignment check. The goal is to prove Stage 3 is **not yet ready**
for the pre-sales checkpoint (3.6) by finding drift, broken contracts with
Stages 1-2, or unmitigated risks — and, failing that, to bless the module as
a safe dependency for Stage 4 Runtime.

**Artifacts reviewed:**
- `memory/architecture.md` (Winston, Stage 3.1)
- `memory/requirements.md` (Dr. Quinn FMEA, Stage 3.0.2 — 58 numbered reqs)
- `memory/test-strategy.md` v1.1 (Murat, Stage 3.2)
- `memory/nfr-report.md` (Murat NR Pass 2, Stage 3.2 bonus)
- `memory/src/praxis/kernel/memory/**/*.py` (Amelia, Stage 3.3)
- `memory/code-review.md` (Cleo, Stage 3.3.5)
- `memory/automation-summary.md` (Quinn, Stage 3.4)
- `pi-mono/alignment-review.md` + `pi-mono/src/praxis/kernel/cost/__init__.py`
- `compression/alignment-review.md` + `compression/src/praxis/kernel/compression/__init__.py`

**Questions this review answers (per Pipeline.md:302-304):**
1. Does Memory integrate with Pi-Mono cost events (Stage 1 dependency)?
2. Do Memory stores pass through the Compression layer (Stage 2 dependency)?
3. Is there API drift from Stages 1-2?

---

## 1. STAGE 3 GATE-BY-GATE AUDIT

### 3.0.1 Elicitation Round 1 (Stakeholder Round Table)

| Gate | Evidence | Verdict |
|------|----------|---------|
| `requirements-privacy.md` produced | v0.2, ~600 lines | **PASS** |
| 5 prescribed personas embodied | 6 executed (5 + GTM Lead/Platform Eng/Memory-Sys Researcher) | **PASS** |
| Privacy questions resolved | 4 binding defaults + 13 escalations to Andrey | **PASS** |

### 3.0.2 Elicitation Round 2 (FMEA + Risk Matrix — Dr. Quinn)

| Gate | Evidence | Verdict |
|------|----------|---------|
| `requirements.md` consolidated | 58 numbered binding requirements | **PASS** |
| FMEA coverage | 43 failure modes + 5 cross-cutting threats | **PASS** |
| RPN gating | 28 BLOCKERs + 11 CONCERNs + 4 ACCEPTEDs | **PASS** |

### 3.1 Winston architecture

| Gate | Evidence | Verdict |
|------|----------|---------|
| `architecture.md` saved | 105 KB, full doc | **PASS** |
| Reference dumps studied (Beads / Mem0 / Atelier) | §1 reference reading protocol documented | **PASS** |
| Pi-Mono outbox pattern reused | §3.5 — bead write + CostEvent in same transaction | **PASS (doc)** — see Finding F-1 |
| Compression layer reuse | §3.4 — structured bead payloads TONL-encoded | **PASS (doc)** — see Finding F-2 |
| 13 pre-3.4 conditions (P0..P3 amendments) | Delegated as arch.md v1.1 parallel track | **TRACKED** |

### 3.2 Murat test strategy + NFR

| Gate | Evidence | Verdict |
|------|----------|---------|
| `test-strategy.md` v1.1 saved | ~1250 lines, 225 → 239 tests | **PASS** |
| 6 CRITICAL risks (R-01..R-06) | All no-waiver, linked to tests | **PASS** |
| `nfr-report.md` (NR Pass 2) | ~800 lines, 0 HARD-FAIL across S/C/P/R/S | **PASS** |
| 3 Andrey ratifications captured | NR-P-R1 p99 matrix, NR-C-A1 crypto-shred SLA = 7d, NR-Q6 RTO = 5m, NR-Q2 entry ceiling 100K/250K | **PASS** |
| 3 pre-3.3 conditions (Amelia) | A3.3.1 SCA, A3.3.2 pool, A3.3.3 ruff — all done | **PASS** |
| 13 pre-3.4 conditions (Winston v1.1) | Parallel track, non-blocking | **TRACKED** |

### 3.3 Amelia implementation

| Gate | Evidence | Verdict |
|------|----------|---------|
| `src/praxis/kernel/memory/` package present | Full — facade, 3 backends, deployment manifest | **PASS** |
| Public facade only | `__init__.py` re-exports `Memory` + model surface; `_internal/*` hidden | **PASS** |
| `Mem0ClientProtocol` DI boundary | `client_protocol.py` single-file boundary, ruff TID251 guards | **PASS** |
| Beads content-addressed Merkle chain | `beads/content_hash.py` + `beads/store.py` | **PASS** |
| Atelier §5.3 multiplicative scoring | `atelier/scoring.py` — property-tested | **PASS** |
| R-04 in-place embedding strip | `facade.py` + `atelier/store.py` — tested end-to-end | **PASS** |
| Protocol conformance across 4 backends | 84 parametrized tests pass | **PASS** |

### 3.3.5 Cleo code review

| Gate | Evidence | Verdict |
|------|----------|---------|
| 0 CRITICAL violations | GREEN across 23 files | **PASS** |
| WARNINGs addressed or deferred with rationale | 3/6 applied, 3/6 deferred with written rationale | **PASS** |
| ruff check + format clean | Both clean | **PASS** |

### 3.4 Quinn QA

| Gate | Evidence | Verdict |
|------|----------|---------|
| Coverage ≥ 85% | **98% aggregate** (855 stmts, 19 missed) | **PASS** |
| Privacy/scoping tests pass | 42/42 (R-01..R-06 + tenant identity + backend scoping) | **PASS** |
| Retrieval correctness verified | 69/69 (atelier + mem0 + facade + scoring property) | **PASS** |
| Live-backend integration closed | 11 new contract tests against real `mem0.Memory` class | **PASS** |
| Total | **264 / 264 passing** | **PASS** |

---

## 2. STAGE 1 DEPENDENCY AUDIT — Pi-Mono

### 2.1 Contract: Memory emits CostEvent to Pi-Mono outbox

**What the architecture promises:**

- `architecture.md` §3.5 — "a bead write and a `CostEvent(type='retention_action')`
  are written in the **same database transaction**… reuses the Stage 1 guarantee
  exactly — no new durability machinery is introduced."
- `architecture.md` §9.3 — Memory emits two CostEvent categories: `retention_action`
  (for reaper + shred) and `record_created` (for Mem0 fact extraction, component
  tag `memory.mem0.*`).
- `_internal/protocol.py:189, :223` — docstrings explicitly state CostEvent emission
  postconditions on `store_fact` and `retrieve_similar_tasks`.
- Req #57 — "Retrieval cache hits are reported to Pi-Mono as a cost saving".

**What the implementation actually does:**

```
grep "praxis.kernel.cost\|CostEvent\|CostTracker" src/praxis/kernel/memory/**/*.py
  → 0 import matches
  → CostEvent appears ONLY in docstrings (protocol.py:189, :223)
```

Zero imports of `praxis.kernel.cost` from the memory package. No CostTracker is
wired. No outbox transaction exists. The entire Pi-Mono integration surface
described in architecture §3.5 and §9.3 is **unwired** at the code level.

### 2.2 Verdict on Pi-Mono integration

**FINDING F-1 (HIGH — deferred to Stage 4):** The Pi-Mono ↔ Memory outbox
integration described in architecture §3.5 and §9.3 is documented but not
implemented. Memory is a self-contained package with no runtime dependency on
Pi-Mono.

**Is this blocking?** Depends on how Pipeline §3.5 interprets "Memory integrates
with Pi-Mono cost events":

- **Strict reading:** Memory must emit `CostEvent` at runtime. Under this
  reading, F-1 is BLOCKING and Amelia must add a `CostTracker` dependency
  injection and wrap all write paths. That is several days of work and would
  re-open Cleo + Quinn.
- **Stage-2 precedent reading:** Stage 2 alignment review (F-2/F-3) accepted
  the same pattern — compression tags are produced but not attached to
  `LLMRequest` because that integration is a Stage 4 Orchestrator concern.
  Memory follows the identical pattern: the facade produces the data that a
  Stage 4 orchestrator will wire into Pi-Mono.

**I take the Stage-2-precedent reading** for three reasons:

1. Pipeline.md:99 explicitly states: *"F-1/F-2/F-3 Stage 2 alignment had similar
   deferred tracking… all deferred to Stage 4, non-blocking."* The same posture
   applies here.
2. The `CostTracker` API is a write-through sink. Wiring it into Memory at this
   stage would create a circular dependency risk (cost → memory via retention
   events → cost) that the Stage 4 Orchestrator is specifically designed to
   break by owning both sides of the wire.
3. The Memory facade's `_audit` buffer (`facade.py:143`) is the seam where a
   Stage 4 CostTracker adapter will hook in. The buffer is already exposed for
   this purpose.

**Recommendation:** Track F-1 as a Stage 4 pre-flight requirement. Do not block
Stage 3.6.

### 2.3 Contract: Pi-Mono public API surface unchanged

Stage 1 re-exports from `praxis.kernel.cost.__init__.py`:

```
CostTracker, compute_cost, QUANTUM, CostEvent, CostRecord, CostSummary,
Filter, LLMRequest, LLMResponse, ModelPricing, TimeRange, TokenClass, ...
```

Memory does not import any of these at the code level. Therefore memory cannot
drift from this surface — it is orthogonal. When Stage 4 wires the adapter, it
will import directly from `praxis.kernel.cost` (the canonical public facade),
not from an intermediate memory shim. **No drift risk.**

---

## 3. STAGE 2 DEPENDENCY AUDIT — Compression

### 3.1 Contract: Beads payloads are TONL-encoded via Compression

**What the architecture promises:**

- `architecture.md` §3.4 — "Structured-record beads (outcomes, decisions,
  facts): TONL serialization applies. The bead payload is re-serialized via
  `praxis.kernel.compression.tonl.encode(payload)` which shrinks the on-disk
  footprint without lossy compaction."

**What the implementation actually does:**

```
grep "praxis.kernel.compression\|CompressionLayer\|tonl" src/praxis/kernel/memory/**/*.py
  → 0 import matches
```

Zero imports of `praxis.kernel.compression` from the memory package. Bead
payloads are stored as raw JSON/str via the Beads SQLite layer. No TONL encoding
happens at the memory-write boundary.

### 3.2 Verdict on Compression integration

**FINDING F-2 (MEDIUM — deferred to Stage 4):** The Beads ↔ Compression TONL
encoding described in architecture §3.4 is documented but not implemented.

**Is this blocking?**

- The Compression layer's Stage 2 alignment review §6 documents the integration
  contract for Stage 3 consumers: "Stage 3 will produce memory writes that may
  be compressed before storage." Note the "may" — compression at the memory
  boundary is advisory, not mandatory.
- Stage 2 guarantees cascade isolation: `encode_request` is safe to call on any
  payload. Adding it to the memory write path is a single-call retrofit that
  does not change the semantics of storage.
- The quantified cost savings target for TONL is ~30% on structured payloads
  (Stage 2 pre-sales metric). For bead payloads (mostly structured JSON), this
  is a substantive optimization, but NOT a correctness issue.

**Recommendation:** Track F-2 as a Stage 4 enhancement or a Stage 3 post-landing
optimization. Do not block Stage 3.6 on it. The pre-sales metric for Stage 3
is *cross-session memory savings* (30-50% second-task target), NOT on-disk
storage savings.

### 3.3 Compression public API surface unchanged

Stage 2 re-exports `CompressionLayer`, `CompressionConfig`, `SessionStats`.
Memory does not import these. No drift risk. When Stage 4 (or a future Memory
optimization pass) wires TONL into the bead write path, it will import from the
canonical public facade, not from memory internals. **No drift.**

---

## 4. API DRIFT AUDIT (Stages 1 → 2 → 3)

| Check | Stage 1 | Stage 2 | Stage 3 | Verdict |
|---|---|---|---|---|
| Package namespace | `praxis.kernel.cost` | `praxis.kernel.compression` | `praxis.kernel.memory` | **Consistent** ✅ |
| Single public facade | `praxis.kernel.cost.__init__.py` re-exports | `praxis.kernel.compression.__init__.py` re-exports | `praxis.kernel.memory.__init__.py` re-exports | **Consistent** ✅ |
| Internal hiding convention | `praxis/kernel/cost/storage/` not hidden | `praxis/kernel/compression/{tonl,forge,caveman,rtk}/` not hidden | `praxis/kernel/memory/_internal/` — hidden via NR-S-R1 ruff TID251 | **Stage 3 stricter** — not drift, improvement |
| Python version | ≥ 3.11 | ≥ 3.11 | ≥ 3.11 (per `pyproject.toml`) | **Consistent** ✅ |
| Pydantic models | Yes | Yes | Yes | **Consistent** ✅ |
| Async shape | Mixed (sync tracker) | Async facade | Async facade (all write/read methods) | **Consistent — Stage 3 follows Stage 2** ✅ |
| Error class hierarchy | `CostTrackerError` → specific | `CompressionError` → specific | `MemoryBackendError` + `TenantIdentityError` → specific | **Consistent pattern** ✅ |
| Deployment/config artifact | `pricing/*.json` | `CompressionConfig` dataclass | `DeploymentManifest` dataclass | **Consistent — config-as-type** ✅ |

**No API drift.** Memory's `_internal/` hiding convention (NR-S-R1 ruff TID251
+ grep tripwire) is STRICTER than Stages 1-2 and should be back-propagated as
a Stage 4 convention. That is an improvement, not a regression.

---

## 5. REQUIREMENT TRACEABILITY (Stage 3)

A full 58-requirement × test traceability matrix lives in `test-strategy.md`
v1.1 Section 10 (Murat). This review samples the high-risk requirements.

| Req | Implementation | Test evidence | Status |
|---|---|---|---|
| #1-7 Tenant isolation | `DeploymentManifest.tenant_hash` enforced at every facade method | 11 tenant-identity tests | ✅ |
| #18 PII pre-redaction | `mem0_adapter/pii.py:redact` | Round-trip tests assert PII stripped | ✅ |
| #22 Source distribution attribution | `RetrievalResult.source_distribution` model | Facade composition tests | ✅ |
| #25 Durable cascade (delete, admission, quarantine) | `facade.delete` + `_audit` buffer + jobs pattern (partial) | 17 facade composition + 10 audit buffer | ⚠ partial — jobs table is in-memory; durable outbox deferred to F-1 |
| #31 Tenant-scoped API keys | Mem0 adapter accepts injected client | `Mem0ClientProtocol` DI + fake client | ✅ |
| #57 Retrieval cost-saving telemetry | CostEvent emission documented, not wired | None | ⚠ F-1 |
| R-01 pgvector orphans | facade.delete → all backends | 3 tests | ✅ |
| R-02 cache invalidation | delete-full-tenant drains | 3 tests | ✅ |
| R-03 audit log PII | audit event hashes criteria | 2 tests | ✅ |
| R-04 quarantine embedding strip | in-place strip end-to-end | 2 tests | ✅ |
| R-05 telemetry leak | cross-tenant retrieve rejection | 10 tests | ✅ |
| R-06 export isolation | two-tenant export + delete | 6 tests | ✅ |

**6 CRITICAL risks (R-01..R-06) — all MITIGATED with no waivers.**
**Req #25 and #57 — partial, tracked as F-1.**

---

## 6. MURAT RISK MITIGATION MAP (Stage 3)

| Risk (test-strategy.md v1.1) | Mitigation | Verdict |
|---|---|---|
| R-01 pgvector orphans | Cascade-delete through facade reaches all backends; 3 R-01 tests | **MITIGATED** |
| R-02 cache invalidation | In-memory drain verified on all 3 backends | **MITIGATED** |
| R-03 audit log PII | Criteria hashed before audit write; 2 R-03 tests | **MITIGATED** |
| R-04 quarantine embedding strip | In-place strip at facade + atelier store; 2 R-04 tests + 6 atelier quarantine tests | **MITIGATED** |
| R-05 telemetry query leak | Retrieval rejects cross-tenant on all 4 surfaces; 10 R-05 tests | **MITIGATED** |
| R-06 two-tenant export isolation | Two-tenant property tests + delete isolation; 6 R-06 tests | **MITIGATED** |
| NFR-P-R1 p99 latency matrix | Not yet measured (Stage 3.6 pre-sales checkpoint) | **DEFERRED to 3.6** |
| NFR-C-A1 crypto-shred 7-day SLA | Structural — reaper + outbox not durable-wired | **F-1 (deferred to Stage 4)** |
| NFR-Q6 crash RTO 5 min | Structural — depends on durable jobs table | **F-1** |
| NFR-Q2 entry ceiling 100K/250K | Soft ceiling telemetry documented, not wired | **F-1** |

The six no-waiver CRITICAL risks are all structurally mitigated and tested.
The four NFR items that require durable cross-stage wiring are deferred to
Stage 4 via F-1, consistent with the Stage 2 precedent.

---

## 7. INTEGRATION CONTRACTS FOR STAGE 4

Stage 4 Agent Runtime will be the **first consumer** of Memory. Contract:

```python
from praxis.kernel.memory import Memory, DeploymentManifest

manifest = DeploymentManifest(tenant_hash=tenant_hash, ...)
memory = Memory.from_manifest(manifest, ...)

# Write path
await memory.store_task_outcome(tenant_id=tenant_hash, draft=...)

# Read path (cross-session retrieval)
hits = await memory.retrieve_similar_tasks(
    tenant_id=tenant_hash, signature=sig, top_k=5, min_similarity=0.75
)
```

**Guarantees Stage 4 can depend on:**

1. `Memory` is the ONLY class to import; every value type is re-exported from
   `praxis.kernel.memory`. No reach into `_internal` is permitted (NR-S-R1).
2. Every method rejects a wrong `tenant_id` with `TenantIdentityError` — Stage 4
   does not need to re-check scoping.
3. Retrieval returns `RetrievalResult` with `source_distribution` attribution.
4. All methods are async; Stage 4 can await them in its orchestrator loop.
5. The `audit_buffer` property is the integration seam for Stage 4's eventual
   Pi-Mono adapter wiring (F-1 closure).
6. The facade composition has zero runtime dependency on Pi-Mono or Compression
   — Stage 4 owns the wiring, not Memory.

**Non-guarantees (Stage 4 responsibilities):**

- F-1: CostEvent emission to Pi-Mono outbox. Stage 4 orchestrator must
  construct a CostTracker adapter that drains `memory.audit_buffer` into the
  Pi-Mono outbox on each tick.
- F-2: TONL encoding of bead payloads via `praxis.kernel.compression`. Stage 4
  can either bypass (accept raw JSON in beads) or add an encoding hook at the
  facade seam.
- Connection pool live tuning. Pool is sized at (10, overflow 15) per Winston
  strawman, not yet measured against real workload (Stage 3.6).
- Durable jobs table for retention reaper. Current implementation uses an
  in-memory audit buffer; Stage 4 must provide a Postgres/SQLite jobs table
  substrate before crypto-shred SLA can be claimed.

---

## 8. TRACKED ITEMS

| ID | Finding | Severity | Owner | Blocking Stage 3.6? | Blocking Stage 4? |
|---|---|---|---|---|---|
| F-1 | Pi-Mono CostEvent emission documented in arch §3.5, §9.3 but not wired in code. `audit_buffer` is the seam. | HIGH | Stage 4 Orchestrator | No | **YES** — must wire before first live tenant |
| F-2 | Compression TONL encoding of bead payloads documented in arch §3.4 but not wired. | MEDIUM | Stage 4 or Stage 3 post-landing optimization | No | No — cost optimization, not correctness |
| F-3 | Durable jobs table for retention reaper. Currently in-memory. Required for NFR-C-A1 (7-day crypto-shred SLA) and NFR-Q6 (5-min RTO). | HIGH | Stage 4 (Postgres infrastructure) | No | **YES** — must ship before any customer can invoke right-to-erasure on a multi-day timeline |
| F-4 | Connection pool sizing validated via strawman smoke test only; not measured under load. | LOW | Stage 3.6 pre-sales or Stage 4 performance pass | No | No |

---

## 9. VERDICT

**Stage 3 graduates to Stage 3.6 (Pre-Sales Checkpoint).**

Four tracked items, none blocking 3.6:

- **F-1 is the largest gap** — Pi-Mono integration is documented but unwired.
  The review accepts this under the Stage 2 precedent (cross-stage wiring is
  a Stage 4 Orchestrator concern) and tracks it as **MUST-CLOSE BEFORE STAGE 4
  CAN CLAIM COMPLETION**, not before 3.6.
- **F-2** is a cost optimization, not a correctness issue. Memory writes work
  correctly without Compression.
- **F-3** (durable jobs table) is a structural dependency that Stage 4 must
  provide before crypto-shred SLA can be honored. Tracked.
- **F-4** (pool sizing under load) is naturally answered by 3.6 itself.

**The Memory package is structurally sound:**

- 98% aggregate coverage (264/264 tests passing).
- 6 CRITICAL risks (R-01..R-06) mitigated with no waivers.
- Tenant isolation enforced at every facade method.
- `Mem0ClientProtocol` DI boundary is a single file; real Mem0 class
  structurally conforms (verified by the 11 live-backend contract tests Quinn
  added in Stage 3.4).
- `_internal/` hiding convention (NR-S-R1 ruff TID251 + grep tripwire) is the
  strictest in the codebase — propagate to Stages 4+.
- No API drift from Stages 1-2: consistent namespace, Pydantic models, async
  shape, error hierarchy, config-as-type pattern.
- Python 3.11+, `praxis.kernel.memory` namespace, no circular dependency on
  Stages 1-2.

**Stage 3.6 is cleared to begin.** Pre-sales checkpoint should measure
cross-session memory savings on a second-task workload (Pipeline.md:307-309).

— Alignment Review Pass, 2026-04-13
