# Session Handoff — Stage 3.3 Phase 3B (Amelia Backend Implementations)

**Created:** 2026-04-12 (during a session at 63% context, cutover before Phase 3B starts)
**Purpose:** Enable a fresh Claude session to pick up exactly where we left off — reviewing Amelia's Memory layer implementation work with the same rigor and context.
**Attach this file to the new session alongside:** `Pipeline.md`, `stage-3-winston-prompt.md`, and Amelia's next status message.

---

## SECTION 1 — FRESH SESSION BOOTSTRAP (READ FIRST)

You are Claude, resuming the role of **Andrey**, the solo founder building **Praxis** — a productized BMAD multi-agent framework. You are currently in **Stage 3 (Memory Layer)**, **Step 3.3 (Amelia Developer Implementation)**, **Phase 3B (backend implementations)**.

Your immediate job: respond to Amelia's next message with the same rigor, specificity, and discipline as the previous session. You are the decision authority; Amelia is the executor who halts at predefined boundaries and asks for explicit go.

**Before responding to Amelia, confirm you understand:**
1. What phase we are in (Phase 3B, backend implementations auto-continue between sub-tasks)
2. What the halt conditions are (full halt at Phase 3B → Phase 3C boundary only; status pings OK, no halts)
3. What scope bounds apply (DO / DO NOT lists in Section 6)
4. What the binding protocol contract is (Section 4)
5. What decisions are NOT to be re-litigated (Section 5)

If you are unclear on any of these, read Sections 2-10 below BEFORE drafting a response.

---

## SECTION 2 — CURRENT STAGE STATE

### Praxis Project Overview (context)
- **What we're building:** Praxis, a multi-agent reasoning engine productizing the BMAD framework. Target customers: strategic advisory, compliance automation, software delivery, sales/content pipelines.
- **Billing context:** Claude Max 5x ($100/mo), CLI mode (NOT API). `ANTHROPIC_API_KEY` must NOT be set in environment.
- **Total build plan:** 7 stages. Currently in Stage 3 of 7.
- **Stage 3 goal:** Ship the unified Memory layer (Beads + Mem0 + Atelier decision memory) behind a single `MemoryProtocol` facade with privacy enforcement.

### Stage 3.3 State
- **3.0, 3.0.1, 3.0.2:** ✅ Complete (elicitation + 6 blockers resolved)
- **3.1 Winston Architect:** ✅ Complete (architecture.md delivered, 58 requirements)
- **3.2 Murat Test Architect:** ✅ Complete (test-strategy.md + nfr-report.md)
- **3.3 Amelia Developer:** 🔄 IN PROGRESS — currently in Phase 3B transition
  - Phase 1 (pre-conditions A3.3.1, A3.3.3): ✅ Complete
  - Phase 2 (pre-condition A3.3.2): ✅ Complete (NR-SC-R2 pool sizing)
  - **Phase 3A (Facade Protocol Definition): ✅ Complete and APPROVED with Q1-Q5 adjustments**
  - **Phase 3B (Backend Implementations): AUTHORIZED, awaiting Amelia to apply protocol adjustments and begin**
  - Phase 3C (Facade Composition): HARD-GATED, awaits explicit approval
- **3.3.5 Cleo Clean Code Review:** Pending Phase 3C completion
- **3.4 Quinn QA:** Pending Phase 3C completion
- **3.5 Alignment Review:** Pending Phase 3C completion
- **3.6 Pre-sales Checkpoint:** Pending

### What just happened (last session)
Amelia delivered Phase 3A (`models.py` + `_internal/protocol.py` + `test_protocol_contract.py`) and asked 5 open questions. I reviewed the delivery, answered all 5 questions decisively, added one new error type (`MemoryQuotaExceeded`), and authorized Phase 3B to start AFTER Amelia applies the Q1-Q5 adjustments.

**As of cutover:** Amelia is applying the protocol adjustments (Q1-Q5 + the new error type). She will next post either:
- "Protocol locked, Phase 3B starting" + begin Beads port, OR
- A clarification question if the adjustments reveal an ambiguity, OR
- A blocker if something unexpected surfaces

---

## SECTION 3 — PHASE 3B EXECUTION PLAN (AUTHORIZED)

### Phase 3B Sub-Tasks (auto-continue between them, status pings welcome)

#### 3B-i — Beads Core Port
- **Reference (Sequential Reference Reading):** Read `_bmad-output/planning-artifacts/src/gastownhall-beads-8a5edab282632443.txt` ONCE. Extract patterns as notes. Close the reference. Implement from notes.
- **Focus sections:** hash addressing, versioning, worktree isolation, bead store
- **Implementation:** `src/praxis/kernel/memory/_internal/beads/` module
- **Port:** `Bead` type, `BeadStore` interface, content-addressable hashing, version chain logic
- **Rule:** Python-idiomatic, NOT line-by-line TypeScript translation. Pydantic v2, hashlib, proper type hints.
- **Tests:**
  - Property-based (Hypothesis) for hash stability and collision resistance
  - Store + retrieve + get_by_id round-trip
  - Phase 3A contract harness parameterized against Beads backend

#### 3B-ii — Mem0 Adapter
- **Reference:** Read `mem0ai-mem0-8a5edab282632443.txt` SELECTIVELY. Only these sections: client initialization, store/retrieve API, three-axis scoping (user_id × agent_id × run_id). Do NOT read the whole 7.8MB dump.
- **Implementation:** `src/praxis/kernel/memory/_internal/mem0_adapter/` module
- **Wraps:** `mem0ai` pip dependency (already in lockfile from A3.3.1)
- **Maps:** Praxis tenant context → Mem0 three-axis scoping
- **Uses:** NR-SC-R2 pool via `create_memory_engine` for any SQL-side storage
- **Privacy enforcement:** every method call requires tenant context; reject calls without it
- **Tests:**
  - Round-trip store/retrieve (live Mem0 if possible, mocked if not — flag decision if mocked)
  - Cross-tenant retrieval FAILS (Murat R-01..R-06)
  - Phase 3A contract harness

#### 3B-ii(a) — Mem0 Local Mode Decision Point
- **If Mem0 requires live backend** (pgvector, Qdrant, etc.) and Amelia cannot get round-trip tests working against local mode or fixture: POST status update, proceed with mocks, continue to 3B-iii. Do NOT halt on this — note for Quinn Step 3.4.

#### 3B-iii — Atelier Decision Memory (MINIMAL)
- **Reference:** Read `robertsfeir-atelier-pipeline-8a5edab282632443.txt` SELECTIVELY. Only: decision capture schema, pgvector integration, decision retrieval. Skip: wave execution, parallel reviewers, mechanical enforcement (those are Stage 5 MAC).
- **Implementation:** `src/praxis/kernel/memory/_internal/atelier/` module
- **Minimal surface:** `capture_decision(...)` + `retrieve_decisions(...)`
- **Storage:** pgvector via NR-SC-R2 engine
- **NO:** TTL decay, auto-capture hooks (Stage 5 MAC territory)
- **Tests:**
  - Round-trip decision capture and retrieval
  - Phase 3A contract harness

### Phase 3B Halt Boundary (MANDATORY)
After 3B-iii completes and all tests pass, Amelia posts:
```
Phase 3B complete — all three backends implemented and conformance-tested.
- Beads: <test counts>
- Mem0 adapter: <test counts, note if mocked>
- Atelier minimal: <test counts>
Awaiting explicit go for Phase 3C — facade composition.
```
**She MUST NOT start Phase 3C without explicit "continue Phase 3C" from you.**

### Phase 3C (HARD-GATED, do NOT authorize without deliberate review)
- `class Memory(MemoryProtocol)` composing Beads + Mem0 + Atelier
- Privacy enforcement wrapper (structural, not trusted)
- Routing logic per operation type
- Audit log hooks (stubs, wired in Stage 7)
- Facade composition tests
- Cleo pre-check gate (ruff, pre-commit, no _internal leaks, no floats)
- Signal handoff to A3.3.5 Cleo when complete

---

## SECTION 4 — PROTOCOL CONTRACT (BINDING, Q1-Q5 APPLIED)

This is the contract Amelia's backends must satisfy. She is applying Q1-Q5 adjustments during cutover — the version below is the target state.

### Location
- `src/praxis/kernel/memory/_internal/protocol.py` — MemoryProtocol (runtime-checkable, structural)
- `src/praxis/kernel/memory/models.py` — Pydantic models + error types (public)

### Method Surface (10 methods, all async)

| Group | Method | Signature | Returns |
|-------|--------|-----------|---------|
| write | `store_task_outcome` | `(tenant_id, task: TaskSignature, outcome: OutcomeDraft)` | `TaskOutcomeRecord` |
| write | `store_decision` | `(tenant_id, decision: DecisionDraft)` | `DecisionRecord` |
| write | `store_fact` | `(tenant_id, agent_id, run_id, fact: FactDraft)` | `FactRecord` |
| read | `retrieve_similar_tasks` | `(tenant_id, signature, top_k=5, min_similarity=0.75)` | `RetrievalResult` |
| read | `retrieve_decisions` | `(tenant_id, query, top_k=10)` | `RetrievalResult` |
| read | `retrieve_facts` | `(tenant_id, agent_id, run_id, query, top_k=10)` | `RetrievalResult` |
| GDPR | `delete` | `(tenant_id, criteria)` | `DeleteResult` |
| GDPR | `export` | `(tenant_id, criteria)` | `ExportResult` |
| GDPR | `flag_and_quarantine` | `(tenant_id, entry_id, reason, free_text=None)` | `QuarantineResult` |
| obs | `health` | `()` — **NO tenant_id** | `HealthReport` |

### Model Architecture (Draft/Record pattern — Q2 adjustment)

```python
# Base building blocks
class _FrozenModel(BaseModel):
    """frozen, strict, extra='forbid'"""
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid")

class _PersistedRecord(_FrozenModel):
    """Mixin for records stamped by Memory layer."""
    entry_id: UUID
    tenant_hash: str
    schema_version: str  # storage layout version
    state_snapshot_version: str
    created_at: datetime

# Draft / Record pair (applied to all 3 store methods)
class _DecisionCore(_FrozenModel):
    context: str
    decision: str
    rationale: str
    alternatives: list[str]
    evidence: list[str]
    confidence: float

class DecisionDraft(_DecisionCore):
    """Input: caller constructs this."""

class DecisionRecord(_DecisionCore, _PersistedRecord):
    """Output: Memory layer returns this."""
    record_type: Literal["decision"] = "decision"  # Q3 Literal discriminator
```

Same pattern for:
- `TaskSignature` + `OutcomeDraft` → `TaskOutcomeRecord`
- `FactDraft` → `FactRecord`

### Retrieval Discriminators (Q3)

```python
RecordType = Literal["task_outcome", "decision", "fact"]

class RetrievalHit(_FrozenModel):
    record_type: RecordType
    record: TaskOutcomeRecord | DecisionRecord | FactRecord
    similarity: float
```

### Error Hierarchy (Q1 docstrings + MemoryQuotaExceeded addition)

```python
class TenantIdentityError(PermissionError):
    """Tenant_id ≠ manifest. §8.2 defense-in-depth. Hard-fails the process."""

class MemoryBackendError(RuntimeError):
    """Backend operational failure. Caller decides retry."""

class MemoryRecordNotFound(LookupError):
    """Lookup by id misses."""

class MemoryQuotaExceeded(Exception):
    """
    Tenant exceeded per-tenant entry ceiling (NR-Q2: 100K soft / 250K hard).
    Carries tenant_id, current_count, ceiling_type ('soft'|'hard'), ceiling_value.
    MAC (Stage 5) catches this to trigger experience library compaction.
    Base class Exception (not MemoryBackendError) — this is a policy condition,
    not an operational failure.
    """
```

**Plus:** `ValueError` reserved for pre-condition violations on numeric kwargs (top_k, min_similarity).

### Key Design Decisions (from Phase 3A review, don't re-litigate)

1. **Protocol in `_internal/`** (not public facade) — avoids circular imports. Backends + facade import from `_internal/protocol.py`. Application code only touches the public `Memory` facade class.
2. **@runtime_checkable + structural typing** — backends don't inherit from MemoryProtocol. Duck typing suffices. Conformance harness is the source of truth.
3. **All methods async** — committed at protocol level. Sync backends wrap in `asyncio.to_thread`. Self-audit test enforces.
4. **TaskSignature.schema_version is distinct from _PersistedRecord.schema_version** (Q1). Input schema vs storage schema — can legitimately diverge. Both documented.
5. **`record_type: Literal[...]`** as class-level default on each Record type (Q3). Self-describing, not a Pydantic discriminated union (backend-agnostic).
6. **`health()` has NO tenant_id** (Q4) — process-wide observability concern. Load balancers, k8s probes, monitors call it. Self-audit test enforces.
7. **`SourceDistribution` submodel** (Q5) — kept as named typed submodel per §8.4 "no raw dicts" philosophy.
8. **Conformance harness with empty registry → 0 tests**, not SKIPPED. Tests conditionally defined under `if BACKEND_FIXTURES:`. Backend registration materializes tests automatically in Phase 3B.

---

## SECTION 5 — DECISIONS IN FORCE (DO NOT RE-LITIGATE)

### 6 Round 2 Blockers — Resolved (binding for Stage 3)

| # | Decision | Position |
|---|----------|----------|
| **B1** | Deployment posture | **Managed single-tenant** (per-customer Postgres + workers, no shared SaaS, no on-prem) |
| **B2** | Embeddings as personal data | **YES** — treat as PII. Delete/quarantine must strip embeddings, not flip flags (FM3.10 override) |
| **B3** | Manifest registry | **Git-backed config file**, not a service. Each deployment pulls from private GitHub repo at boot |
| **B4** | LLM provider keys | **Tenant-scoped** (customer brings their own). Managed billing is future tier, NOT MVP |
| **B5** | Backup strategy | **Per-tenant encryption + crypto-shredding** as standard. KMS integration. Single-tenant makes it natural |
| **B6** | Seed corpus | **Use existing BMAD sessions + Tokonomics rounds NOW** as seed; Stage 6 benchmarks augment later |

### 3 Murat Gate Decisions — Ratified

1. **NR-P-R1 p99 latency matrix:** Ratified. **Guardrail:** hot-path ops (retrieve, search_similar, get_by_id, store_during_session) must stay <200ms p99 or escalate. Batch/async ops (compact, cascade_delete, crypto_shred_initiation) allowed higher p99.
2. **NR-C-A1 crypto-shred SLA:** Ratified at **7 calendar days** with structure: days 0-1 soft-delete window, days 1-2 embedding purge + cache drain, days 2-5 backup rewrite, days 5-7 KMS key destruction. At day 7, cryptographic recovery is mathematically impossible. Marketing angle: "4x faster than industry standard."
3. **Stage 3.3 advancement:** Confirmed with 3 pre-conditions as Amelia's first tasks (A3.3.1 SCA scan, A3.3.2 pool sizing, A3.3.3 banned imports). ALL COMPLETE.

### Additional Ratifications
- **NR-Q2 entry ceiling:** 100K soft / 250K hard — drives MemoryQuotaExceeded exception
- **NR-Q6 crash recovery RTO:** 5 minutes — single-tenant-per-deployment makes achievable

---

## SECTION 6 — SCOPE BOUNDS (STRICTLY ENFORCED)

### DO implement in A3.3.4 (Phase 3B + 3C)
1. Facade protocol definition (✅ done in 3A)
2. Beads core port (versioned state, hash-addressed)
3. Mem0 adapter (dependency wiring behind facade)
4. Atelier decision memory (MINIMAL — capture + retrieve only)
5. Facade composition + privacy enforcement wrapper
6. Protocol conformance tests per backend

### DO NOT implement (out of scope — belongs to Stage 5 or later)
- ❌ Cross-session learning loop (MAC cycle 1 seeding is Stage 5)
- ❌ Atelier auto-capture hooks (Stage 5 MAC triggers these)
- ❌ Atelier TTL decay logic (deferred)
- ❌ Mem0 fact extraction tuning (use defaults)
- ❌ Large-delete scalability optimizations (Stage 7 NFR)
- ❌ Caching layers, batching, pre-optimizations
- ❌ Crypto-shred execution pipeline (interface hook only; actual shred is ops/infra)
- ❌ Comprehensive test suites (Quinn's domain in Step 3.4)

**Hard rule:** If Amelia finds herself implementing something from the DO NOT list "because it would be easier now," she MUST stop and post a scope-creep flag. You grant explicit extensions if warranted.

---

## SECTION 7 — REVIEW STYLE (HOW TO RESPOND TO AMELIA)

Maintain the discipline demonstrated in prior responses:

### Tone
- **Decisive, not deliberative.** "Approved with conditions" or "Rejected because X" — not "on the one hand / on the other hand."
- **Specific, not generic.** Cite exact line numbers, exact file paths, exact rule violations.
- **Reinforce discipline.** Praise exemplary engineering judgment when it appears (e.g., Amelia's SQLAlchemy pool test pivot from live-QueuePool introspection to mock-based kwargs verification — that's sophisticated judgment and deserves explicit recognition).
- **No pingponging.** If Amelia posts a status update, respond with "continue" or "halt — here's why" — don't engage in chitchat.

### Content priorities (in order)
1. **Correctness against contract** — does the code satisfy Winston's architecture + Murat's test strategy + the protocol contract?
2. **Scope discipline** — anything from DO NOT list creeping in?
3. **Privacy enforcement** — structural, not trusted? Cross-tenant scenarios fail?
4. **Test rigor** — property tests for hash/invariants? Conformance harness passes?
5. **Python idioms** — Pydantic v2, asyncio, decimal.Decimal where applicable, no raw dicts
6. **Ruff + pre-commit** — must be green before gate advances

### Halt conditions (never wave these through)
- Any blocker-severity failure mode observed
- Scope creep into DO NOT territory
- Protocol contract violation
- Test coverage gaps in Murat's R-01..R-06 privacy-critical rubric
- Floating point anywhere cost-adjacent (must be `decimal.Decimal`)

### Status pings vs halts
- **Status ping** = "Beads in, 12 tests PASS, proceeding to Mem0" → acknowledge briefly, no review required
- **Halt** = "Phase 3B complete, awaiting Phase 3C approval" → full review before granting continue

---

## SECTION 8 — ACTIVE PARALLEL TRACKS

### Winston §4.2 Amendment (NR-SC-R2 codification)
- **Status:** NOT DELIVERED as of cutover. Amelia implemented A3.3.2 with NR-SC-R2 strawman values (Option b, authorized). Winston's amendment becomes documentation-only when it arrives.
- **Your action if Winston delivers during this session:** Verify values match (`pool_size=10, max_overflow=15, pool_pre_ping=True, pool_recycle=3600`). If match → merge doc, remove "pending ratification" comment from `db.py`. If divergent → refactor Amelia's one-liner.
- **Not blocking anything right now.** Phase 3B can proceed independently.

### A3.3.5 Cleo Invocation Brief
- **Status:** NOT DRAFTED yet. You were going to draft it during Amelia's Phase 3B work.
- **When to draft:** After Amelia signals Phase 3B complete and you approve Phase 3C, draft the Cleo brief so handoff is tight when Phase 3C closes.
- **Contents:** target directory, review scope, gate conditions (0 CRITICAL violations, WARNING addressed/deferred with rationale), auto-fix authorization, output path

### Pipeline.md Updates Pending
- Session log entry v1.8 (Stage 3.3 Phase 1 + 2 completion — was supposed to be done by Amelia)
- Section 3 tracker updates for 3.3 sub-items (A3.3.1, A3.3.2, A3.3.3 marked `[x]`, A3.3.4 still `[ ]`)
- **Verify on resume:** check if Amelia wrote these updates. If not, ask her to write them before Phase 3B completes.

---

## SECTION 9 — KEY FILE PATHS (READ AS NEEDED)

### Project root
`C:\Users\AndreyPopov\Documents\Anthropic\`

### Pipeline + stage artifacts
- `_bmad-output/planning-artifacts/Praxis/Pipeline.md` — master orchestration (always attach to session)
- `_bmad-output/planning-artifacts/Praxis/stage-3-winston-prompt.md` — stage 3 original brief
- `_bmad-output/planning-artifacts/Praxis/praxis-build-plan.md` — 7-stage overview
- `_bmad-output/planning-artifacts/Praxis/box-core-architecture.md` — full technical architecture
- **THIS FILE:** `_bmad-output/planning-artifacts/Praxis/session-handoff-20260412-stage3-phase3B.md`

### Stage 3 implementation artifacts (current state)
- `_bmad-output/implementation-artifacts/praxis/memory/architecture.md` — Winston's architecture (58 reqs, §2.1 facade surface, §2.2 record schema, §4.2 backend config, §8.2 defense-in-depth)
- `_bmad-output/implementation-artifacts/praxis/memory/requirements.md` — consolidated privacy + governance requirements (from Round 3.0.1 + 3.0.2)
- `_bmad-output/implementation-artifacts/praxis/memory/requirements-privacy.md` — Round 3.0.1 Stakeholder Round Table output
- `_bmad-output/implementation-artifacts/praxis/memory/test-strategy.md` — Murat TD Pass 1 (~1250 lines, 225 tests, 6 CRITICAL risks R-01..R-06, 88 requirement-linked scenarios)
- `_bmad-output/implementation-artifacts/praxis/memory/nfr-report.md` — Murat NR Pass 2 (~800 lines, 30+ findings, zero HARD-FAIL)

### Amelia's Phase 1 + 2 deliverables
- `_bmad-output/implementation-artifacts/praxis/memory/mem0-sca-scan.md` — A3.3.1 SCA scan (CLEAN, 0 CVEs)
- `_bmad-output/implementation-artifacts/praxis/memory/nr-s-r1-banned-api-setup.md` — A3.3.3 banned imports setup
- `_bmad-output/implementation-artifacts/praxis/memory/requirements-mem0-lock.txt` — 80-package lockfile
- `_bmad-output/implementation-artifacts/praxis/memory/pyproject.toml` — ruff TID251 config
- `_bmad-output/implementation-artifacts/praxis/memory/.pre-commit-config.yaml` — grep tripwire + ruff hook

### Amelia's Phase 3A deliverables (Q1-Q5 adjustments being applied at cutover)
- `_bmad-output/implementation-artifacts/praxis/memory/src/praxis/kernel/memory/models.py` — ~320 lines, public Pydantic + errors (TO BE ADJUSTED: Draft/Record split, MemoryQuotaExceeded, Literal record_type defaults)
- `_bmad-output/implementation-artifacts/praxis/memory/src/praxis/kernel/memory/_internal/protocol.py` — ~320 lines, MemoryProtocol (TO BE ADJUSTED: Q1 docstrings, Draft types in signatures)
- `_bmad-output/implementation-artifacts/praxis/memory/tests/memory/test_protocol_contract.py` — ~240 lines, conformance harness (empty registry, 0 conformance cases in 3A, populate in 3B)

### Amelia's A3.3.2 deliverable
- `_bmad-output/implementation-artifacts/praxis/memory/src/praxis/kernel/memory/_internal/common/db.py` — NR-SC-R2 pool sizing (carries "pending Winston §4.2 ratification" comment)
- `_bmad-output/implementation-artifacts/praxis/memory/tests/memory/test_db_engine_pool.py` — 3/3 PASS

### Reference dumps (SELECTIVE READING ONLY — Sequential Reference Reading Rule, see Pipeline.md §4.6)
- `_bmad-output/planning-artifacts/src/gastownhall-beads-8a5edab282632443.txt` — Beads reference (Phase 3B-i)
- `_bmad-output/planning-artifacts/src/mem0ai-mem0-8a5edab282632443.txt` — Mem0 reference (Phase 3B-ii, SELECTIVE, 7.8MB dump)
- `_bmad-output/planning-artifacts/src/robertsfeir-atelier-pipeline-8a5edab282632443.txt` — Atelier reference (Phase 3B-iii, SELECTIVE)

---

## SECTION 10 — LIKELY NEXT MESSAGES FROM AMELIA & RESPONSE PATTERNS

### Scenario A: "Protocol adjustments applied, Phase 3B starting with Beads"
**Likelihood:** HIGH
**Your response:**
1. Acknowledge briefly
2. Verify she applied Q1-Q5 + MemoryQuotaExceeded (ask if her summary doesn't mention them explicitly)
3. Remind about Sequential Reference Reading rule for Beads dump
4. Confirm auto-continue between 3B sub-tasks, halt only at 3B boundary
5. Go

### Scenario B: "Beads port complete, N tests PASS, proceeding to Mem0 adapter" (status ping)
**Likelihood:** MEDIUM-HIGH
**Your response:**
1. Brief acknowledgement (one line)
2. "Continue 3B-ii"
3. Reminder: read Mem0 dump SELECTIVELY, only client init / store-retrieve API / three-axis scoping sections

### Scenario C: "Mem0 requires live backend — proceeding with mocks?" (blocker-adjacent)
**Likelihood:** MEDIUM
**Your response:**
1. Authorize mocks for 3B-ii conformance tests
2. Explicit: "note this decision in the module docstring and in test strategy addendum — Quinn (Step 3.4) will add live-backend integration tests"
3. Continue to 3B-iii

### Scenario D: "Beads TypeScript pattern X doesn't translate cleanly to Python" (clarification)
**Likelihood:** MEDIUM
**Your response:**
1. Ask her to propose a Python-idiomatic alternative
2. Review against the contract (protocol.py) — does the alternative still satisfy MemoryProtocol semantics?
3. If yes: ratify. If no: help her find an approach that does.
4. Note: this is NOT a protocol change, just an implementation-level equivalent

### Scenario E: "Phase 3B complete, awaiting Phase 3C approval" (FULL HALT)
**Likelihood:** MEDIUM (comes after 3B-iii)
**Your response — full review required:**
1. Verify all three backends' conformance tests pass
2. Verify scope discipline (nothing from DO NOT list snuck in)
3. Verify privacy enforcement is structural (tenant context required at every entry point)
4. Verify Python idioms (Pydantic v2, asyncio, type hints, no raw dicts)
5. Verify ruff + pre-commit green
6. If all green: authorize Phase 3C with explicit "continue Phase 3C" + reference the Phase 3C plan in Pipeline.md / stage-3-winston-prompt.md
7. If issues: specify exactly what to fix, halt until resolved

### Scenario F: Scope creep flag from Amelia
**Likelihood:** LOW (she's disciplined)
**Your response:**
1. Assess: is the feature genuinely necessary for correctness, or nice-to-have?
2. If necessary: ratify the scope extension with a brief session log note
3. If nice-to-have: reject, file as Stage 5+ work, return to the hard scope
4. Never silently accept scope expansion without explicit ratification

### Scenario G: Winston §4.2 arrives mid-Phase-3B
**Likelihood:** MEDIUM
**Your response:**
1. Verify pool sizing values match NR-SC-R2 exactly
2. If match: tell Amelia to remove "pending ratification" comment from `db.py` after her current sub-task completes (not mid-sub-task)
3. If divergent: halt Amelia, figure out if Winston's values should win, refactor one-liner, unblock
4. Update Pipeline.md session log

---

## SECTION 11 — IMMEDIATE FIRST ACTIONS ON NEW SESSION

When you start the new session, do these in order:

1. **Verify file attachments:**
   - `Pipeline.md` attached? ✓
   - `stage-3-winston-prompt.md` attached? ✓
   - THIS handoff file attached? ✓
   - If anything missing, ask the user to attach before responding

2. **Read the user's message (Amelia's status update or question).** Classify it per Section 10 scenarios.

3. **Check current file state if needed** (do NOT re-read everything — only what's relevant to the current response):
   - If Amelia references a file change, Read that file to verify
   - If she claims tests pass, trust unless something feels off
   - If she claims scope bounds respected, spot-check the implementation against DO NOT list

4. **Respond per Section 7 Review Style.**

5. **Update Pipeline.md if a milestone is reached** (phase completion, gate ratification). Do this IMMEDIATELY at the milestone, not at end of session.

---

## SECTION 12 — CONTEXT PRESERVATION NOTES

### Max 5x rate limit reality
- ~225 messages per 5-hour window
- Stage 3 is roughly halfway through project token budget
- Stage 5 (MAC) will be the heaviest stage — reserve ~40% of remaining Max budget for it
- If rate limits tighten, downgrade non-critical steps to standard 200k context (Pipeline.md Section 4.6 guidance)

### Discipline checkpoint
- This handoff at 63% context is GOOD practice — don't wait until 85%+ to cut over
- Future cutovers: create new session-handoff-YYYYMMDD-stageN-phase file per handoff
- Chain handoff files if needed — each one references the previous via the Pipeline.md session log

### What NOT to do in the new session
- Don't re-read Tokonomics rounds, Stage 1/2 architecture, or the full Pipeline.md front-to-back. You have this handoff for that context.
- Don't re-derive decisions — they are in Section 5
- Don't re-read the full 7.8MB Mem0 dump — it's for Amelia's 3B-ii only
- Don't suggest Party Mode, brainstorming, or elicitation activities — we're deep in execution, not discovery

---

## APPENDIX — KEY NAMES & GLOSSARY

- **Praxis** — the product being built (multi-agent reasoning engine)
- **BMAD** — the framework Praxis productizes (16 specialized agents: Mary, Winston, Amelia, Quinn, Murat, Cleo, Carson, Dr. Quinn, Victor, Sophia, Maya, Caravaggio, Paige, John, Sally, Bob)
- **Amelia** — BMAD Developer agent (executor for Stage 3.3)
- **Winston** — BMAD Architect agent (delivered Stage 3.1)
- **Murat** — BMAD Test Architect agent (delivered Stage 3.2 TD + NR)
- **Cleo** — BMAD Clean Code Reviewer agent (Stage 3.3.5 next after Phase 3C)
- **Quinn** — BMAD QA Engineer agent (Stage 3.4 after Cleo)
- **Andrey** — the user (solo founder), you're playing his role
- **MAC** — Meta-Agent Controller (Stage 5, the reasoning engine — NOT in scope yet)
- **MemoryProtocol** — the binding facade contract for Stage 3 (10 methods, see Section 4)
- **NR-SC-R2** — Pool sizing constants from Murat's NFR report (pool_size=10, max_overflow=15, pool_pre_ping=True, pool_recycle=3600)
- **FM3.10** — Failure mode override: quarantine must strip embeddings in place, not flip flags
- **R-01..R-06** — Murat's 6 CRITICAL privacy risks in test-strategy.md

---

**End of handoff. New session is now equipped to resume Stage 3.3 Phase 3B review with full context.**

**Pipeline.md version at cutover:** 1.8 (or 1.7 if Amelia didn't write the v1.8 log entry — verify on resume)
**Session cutover reason:** Context preservation at 63%, before Phase 3B backend implementations begin and consume significant review context
