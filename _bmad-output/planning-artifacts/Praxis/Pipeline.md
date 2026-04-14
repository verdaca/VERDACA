# PRAXIS BUILD PIPELINE — Master Orchestration Document

**Purpose:** Single source of truth for the Praxis build pipeline. Tracks progress, enforces stage gates, provides path registry for any fresh Claude session.

**How to use this file:**
1. Always attach this file at the start of ANY new Claude session working on Praxis
2. Also attach the current stage's prompt file (e.g., `stage-1-winston-prompt.md`)
3. Claude reads status tracker → resumes from last incomplete item
4. Claude updates tracker as work completes

---

## SECTION 1: FRESH SESSION BOOTSTRAP (READ THIS FIRST)

If you are a new Claude session seeing this file for the first time, follow this protocol before doing ANY work:

### Bootstrap Steps

1. **Verify billing mode (user should be on Max, not API):**
   - Remind user to run `echo $ANTHROPIC_API_KEY` (must be empty for Max billing)
   - Do NOT proceed if user reports API key is set (would burn API credits)

2. **Read the Status Tracker (Section 3 below):**
   - Find the last completed item
   - Identify the NEXT incomplete item
   - Verify prerequisites for that item are satisfied (Section 5 — Gate Conditions)

3. **Read the relevant stage prompt file:**
   - Stage N prompt at: `_bmad-output/planning-artifacts/Praxis/stage-N-winston-prompt.md`
   - This contains the detailed instructions for Winston at that stage

4. **Verify previous stage artifacts exist:**
   - Check the implementation-artifacts path for the previous stage's docs
   - If missing, STOP and tell user previous stage is incomplete

5. **Do not skip stages. Do not parallelize.**
   - Stages 1-7 are strictly sequential
   - Each depends on prior stage artifacts
   - Parallel execution causes irreconcilable architecture drift

6. **Keep this Pipeline.md file updated:**
   - As work completes, update the Status Tracker checkboxes
   - Write the update back to `_bmad-output/planning-artifacts/Praxis/Pipeline.md`
   - Include a brief note with timestamp

---

## SECTION 2: PIPELINE DEPENDENCY FLOW

```
                    ┌────────────────────────────┐
                    │ STAGE 1: Pi-Mono           │
                    │ (Measurement Foundation)   │
                    └──────────┬─────────────────┘
                               │
                               ▼
                    ┌────────────────────────────┐
                    │ STAGE 2: Compression       │
                    │ (TONL + Forge + RTK + Cav) │
                    │ Needs: S1                  │
                    └──────────┬─────────────────┘
                               │
                               ▼
                    ┌────────────────────────────┐
                    │ STAGE 3: Memory            │
                    │ (Beads + Mem0 + Atelier)   │
                    │ Needs: S1, S2              │
                    └──────────┬─────────────────┘
                               │
                               ▼
                    ┌────────────────────────────┐
                    │ STAGE 4: Agent Runtime     │
                    │ (Loader + Spawner + MCP)   │
                    │ Needs: S1, S2, S3          │
                    └──────────┬─────────────────┘
                               │
                               ▼
                    ┌────────────────────────────┐
                    │ STAGE 5: MAC Engine        │
                    │ (Interpreter + 3-Cycle)    │
                    │ Needs: S1, S2, S3, S4      │
                    └──────────┬─────────────────┘
                               │
                               ▼
                    ┌────────────────────────────┐
                    │ STAGE 6: Studio Template   │
                    │ (First workflow)           │
                    │ Needs: S1-S5               │
                    └──────────┬─────────────────┘
                               │
                               ▼
                    ┌────────────────────────────┐
                    │ STAGE 7: POV Harness       │
                    │ (Web UI + Billing)         │
                    │ Needs: S1-S6               │
                    └────────────────────────────┘
```

**Rule:** Do NOT start Stage N+1 until Stage N is 100% complete (all tracker items checked).

---

## SECTION 3: STATUS TRACKER (UPDATE AS WORK COMPLETES)

**Legend:** `[ ]` not started  •  `[~]` in progress  •  `[x]` complete  •  `[!]` blocked

### Pre-Flight Checks (Before Any Stage)

- [x] Claude Max subscription active (Max 20x preferred for rate limits)
- [x] `.claude/settings.local.json` configured with `acceptEdits` mode
- [x] `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` enabled
- [x] Reference .txt dumps present in `_bmad-output/planning-artifacts/src/`
- [x] All stage prompt files exist in `_bmad-output/planning-artifacts/Praxis/`
- [x] CLAUDE.md updated with directory trees
- [x] `claude-setup-reference.md` available as subscription/billing guide
- [x] First Praxis implementation directories created under `_bmad-output/implementation-artifacts/praxis/`

---

### STAGE 1: Pi-Mono Cost Tracker (Measurement Foundation)

**Prompt file:** `_bmad-output/planning-artifacts/Praxis/stage-1-winston-prompt.md`
**Output directory:** `_bmad-output/implementation-artifacts/praxis/pi-mono/`

- [x] **1.1 Winston (Architect)** — `/bmad-agent-architect`
  - [x] Architecture doc saved to `_bmad-output/implementation-artifacts/praxis/pi-mono/pi-mono-cost-tracker-architecture.md`
  - [x] Reference implementation read: `src/badlogic-pi-mono-8a5edab282632443.txt`
  - [x] Decimal.Decimal usage explicitly documented (§6 + §6.4 T1–T12 table)
  - [x] Provider abstraction interface defined (§5 Protocol + extensibility contract)

- [x] **1.2 Murat (Test Architect)** — `/bmad-tea`
  - [x] Test strategy doc saved to `_bmad-output/implementation-artifacts/praxis/pi-mono/test-strategy.md`
  - [x] Risk-based test pyramid defined (unit → integration → reconciliation)
  - [x] Property-based test plan for cost arithmetic (Hypothesis) — P1–P15 enumerated
  - [x] Golden file regression suite specified (§4)

- [x] **1.3 Amelia (Developer)** — `/bmad-agent-dev`
  - [x] Implementation in `_bmad-output/implementation-artifacts/praxis/pi-mono/src/`
  - [x] All unit tests passing (74/74)
  - [x] decimal.Decimal used throughout (AST scan: zero float in cost paths)
  - [x] Pi-Mono can track cost for a sample LLM call (smoke + integration tests)

- [x] **1.4 Quinn (QA Engineer)** — `/bmad-qa-generate-e2e-tests` OR `/bmad-testarch-automate`
  - [x] Test coverage: math.py 96%, models.py 93%, aggregate 79% (hot path meets gate; event/telemetry gaps tracked)
  - [x] Integration test: sample LLM call tracked correctly (TestTrackCost::test_happy_path)
  - [x] Reconciliation test: computed cost matches synthetic invoice (TestReconciliation::test_reconciliation_clean_on_synthetic)

- [x] **1.5 Alignment Review** — `/bmad-review-adversarial-general` OR independent session
  - [x] No floating-point usage anywhere (AST scan PASS)
  - [x] Decision documentation complete (architecture §11 traceability matrix + §10 open questions)
  - [x] Ready for Stage 2 to reference as dependency (alignment-review.md §6 integration contracts)

- [x] **1.6 Pre-Sales Checkpoint**
  - [x] Cost dashboard spec captured (pre-sales-checkpoint.md §2.4 — verified API surface)
  - [x] Baseline metric capture protocol documented for Stage 2 comparison (§3)
  - [x] "We track every token from inception" headline documented (§1)

**Gate to Stage 2:** All boxes checked. Architecture, test strategy, implementation, alignment review, and pre-sales checkpoint all exist under `_bmad-output/implementation-artifacts/praxis/pi-mono/`. Follow-up items tracked in alignment-review.md §3 (non-blocking).

---

### STAGE 2: Compression Layer (TONL + Forge + RTK + Caveman)

**Prompt file:** `_bmad-output/planning-artifacts/Praxis/stage-2-winston-prompt.md`
**Output directory:** `_bmad-output/implementation-artifacts/praxis/compression/`

- [x] **2.0 Pre-flight:** Verify Stage 1 complete (alignment-review.md §6 integration contracts confirmed; Stage 1 all six checkboxes [x] as of 2026-04-12)

- [x] **2.1 Winston (Architect)** — `/bmad-agent-architect`
  - [x] Architecture doc saved to `_bmad-output/implementation-artifacts/praxis/compression/architecture.md`
  - [x] All 4 reference dumps studied (TONL, Forge, RTK, Caveman via 4 parallel Explore agents)
  - [x] RTK polyglot boundary documented (§3.3 — vendored binary + Python subprocess wrapper)
  - [x] Compression pipeline composition diagram included (§2.1 ASCII diagram)
  - [x] Integration contract with Pi-Mono documented (§4.1 — tag-based attribution per alignment-review §6)

- [x] **2.1.5 Elicitation Round 1 (AFTER Winston)** — `/bmad-advanced-elicitation`
  - [x] Focus: Quality tolerance threshold for compression fall-back
  - [x] Input: Winston's draft compression architecture v0.1
  - [x] Questions answered: fall-back % (3%/7% Caveman; TONL 0.1%/1%, Forge 1%/5%, RTK 5%/15%), quality measurement (4-tier Structural + S1–S4 semantic, embedding P1), consequence hierarchy (Orchestrator → Caveman → Forge/TONL → RTK per Matrix 6)
  - [x] Output: `_bmad-output/implementation-artifacts/praxis/compression/requirements-validation.md`
  - [x] Winston updated architecture (v0.1 → v0.2); 16 edits applied inline from FMEA (12) + Comparative Matrix (4)
  - [x] Two open questions escalated to Andrey: §5.1 Caveman P0 scope (recommendation: Option C, feature-flagged), §5.2 embedding validator window (recommendation: P1)

- [x] **2.2 Murat (Test Architect)** — `/bmad-tea`
  - [x] Test strategy doc saved to `_bmad-output/implementation-artifacts/praxis/compression/test-strategy.md`
  - [x] Round-trip property tests for TONL specified (P_T1 Hypothesis 5000 cases + golden fixtures per tokenizer)
  - [x] Quality preservation tests for Caveman specified (P_V1–P_V7 + adversarial corpus 60+ hand-curated cases targeting S3/S4)
  - [x] A/B benchmark harness design approved (§8 — seed pinning, config_hash fairness, nightly cost cap $0.10/run)
  - [x] Risk register + P×I scoring — CM5 polarity flip is the RPN-9 BLOCK, CM2/CM4/CM9/CM10/CM12/CM15 are CONCERNS
  - [x] Component-specific test allocations per Matrix 6 severity ranking

- [x] **2.3 Amelia (Developer)** — `/bmad-agent-dev` _(Model: Sonnet 4.6 [1M] · Thinking: high)_
  - [x] Implementation in `_bmad-output/implementation-artifacts/praxis/compression/src/`
  - [x] TONL, Forge, Caveman ported to Python
  - [x] RTK wrapper integrates Rust binary (or stub if RTK deferred)
  - [x] A/B benchmark harness runnable
  - [x] **Context strategy:** Reference dumps total ~2.5M tokens — read ONE at a time, implement that component, then move to next. Do NOT attempt to load all 4 references simultaneously

- [x] **2.3.5 Cleo (Clean Code Review)** — `/bmad-agent-clean-code-reviewer` _(Model: Sonnet 4.6 [1M] · Thinking: medium)_
  - [x] Target directory: `_bmad-output/implementation-artifacts/praxis/compression/src/`
  - [x] Review report saved to `_bmad-output/implementation-artifacts/praxis/compression/code-review.md`
  - [x] All CRITICAL violations resolved (5 found: CR-001 auto-fixed, CR-002/003/004 documented + deferred with explicit conditions, CR-005 auto-fixed)
  - [x] WARNING violations addressed or explicitly deferred with rationale (11 WARNINGs: WR-001/002/003/006/007/009/010 marked RESOLVE; WR-004/005/008/011 deferred with P1 rationale)
  - [x] Auto-fixes applied where applicable (CR-001: assert→RTKExecutionError in rtk/client.py:85,137; CR-005: bare except narrowed in rtk/stub.py + client._passthrough)
  - [x] **Gate:** 0 CRITICAL violations remaining — PASS as of 2026-04-12

- [x] **2.4 Quinn (QA Engineer)** — Testing _(Model: Sonnet 4.6 · Thinking: medium)_
  - [x] Test coverage >= 85% — achieved **94%** aggregate (429 tests, 249 new) as of 2026-04-12
  - [x] Quality circuit breakers verified functional — all 5 gate denial paths tested (stale calibration, min length, content type, break-even, wenyan)
  - [x] Round-trip tests pass on all TONL edge cases — 45 tests covering pipe/newline/sentinel/Decimal/unicode/nested/table edge cases
  - [x] Summary at `_bmad-output/implementation-artifacts/praxis/compression/automation-summary.md`

- [x] **2.5 Alignment Review** _(Model: Opus 4.6 [1M] · Thinking: high)_
  - [x] Compression reports to Pi-Mono correctly (Stage 1 dependency) — tag-based attribution confirmed; 3 tracked items (F-1 tag naming, F-2 path bug, F-3 unused param) all deferred to Stage 4, non-blocking
  - [x] No architecture drift from Stage 1 assumptions — cascade isolation, Python 3.11+, praxis.kernel.compression namespace all confirmed
  - [x] Language consistency maintained (Python) — all source .py; RTK Rust binary wrapped via subprocess per architecture §3.3
  - [x] Alignment review saved to `_bmad-output/implementation-artifacts/praxis/compression/alignment-review.md`

- [x] **2.6 Pre-Sales Checkpoint** _(Model: Sonnet 4.6 · Thinking: low)_
  - [x] A/B harness run: 4 workloads, config_hash 572fcf96545c8e0e — 0 fallbacks across all workloads
  - [x] Savings measured: 30.34% token reduction on TONL-heavy; 14.32% compound across all workloads
  - [x] Headline: "Three compression layers combined deliver 14.32% total token reduction (30% on structured payloads)"
  - [x] F-2 path bug fixed (telemetry.py parents[7] → parents[5]) — Pi-Mono path now resolves correctly
  - [x] Blog post draft: `_bmad-output/implementation-artifacts/praxis/compression/blog-draft-stage2.md`
  - [x] Checkpoint doc: `_bmad-output/implementation-artifacts/praxis/compression/pre-sales-checkpoint.md`

**Gate to Stage 3:** All boxes above checked. Compression architecture.md exists. Measurable savings reported (30.34% TONL-heavy, 14.32% compound). Stage 3 pre-flight elicitation rounds 3.0.1 + 3.0.2 must complete before Winston begins.

---

### STAGE 3: Memory & Cross-Session Learning

**Prompt file:** `_bmad-output/planning-artifacts/Praxis/stage-3-winston-prompt.md`
**Output directory:** `_bmad-output/implementation-artifacts/praxis/memory/`

- [x] **3.0 Pre-flight:** Verify Stages 1-2 complete (both 100% as of 2026-04-12; `_bmad-output/implementation-artifacts/praxis/memory/` created)

- [x] **3.0.1 Elicitation Round 1 (BEFORE Winston)** — `/bmad-advanced-elicitation` _(Model: Opus 4.6 · Thinking: high)_
  - [x] **Method to use:** **Stakeholder Round Table** (collaboration #1 — convene multiple personas for diverse perspectives)
  - [x] Personas to embody: SMB Founder, Enterprise CISO, GDPR Data Protection Officer, Legal Counsel, End User — executed with 6 personas (prescribed 5 + GTM Lead, Platform Engineer, Memory-Systems Researcher; DPO and Legal Counsel combined into one voice "Lena"; SMB Founder "Marco" doubles as End User in single-tenant model)
  - [x] Focus: Multi-tenant privacy model
  - [x] Questions answered: SMB vs Enterprise scoping, cross-customer learning, GDPR posture, data residency — 4 binding questions resolved with recommended defaults + 13 open questions escalated to Andrey
  - [x] Output: draft privacy requirements in `_bmad-output/implementation-artifacts/praxis/memory/requirements-privacy.md` (v0.2, ~600 lines, supersedes v0.1 first-principles draft)

- [x] **3.0.2 Elicitation Round 2 (BEFORE Winston)** — `/bmad-cis-problem-solving` (Dr. Quinn) _(Model: Opus 4.6 · Thinking: max)_
  - [x] **Primary method:** **Failure Mode Analysis** (analysis category — systematically explore how each governance mechanism could fail)
  - [x] **Secondary method:** **Risk Assessment Matrix** (evaluation category — likelihood × impact scoring for each failure mode)
  - [x] Focus: Adversarial analysis of retention/governance risks — 43 failure modes across Q1-Q4 + 5 cross-cutting threats
  - [x] Questions answered: deletion flow, right-to-erasure, experience library poisoning, leakage attack surface — 28 BLOCKERs (RPN ≥ 12), 11 CONCERNs, 4 ACCEPTEDs
  - [x] Output: hardened requirements in `_bmad-output/implementation-artifacts/praxis/memory/requirements.md` (consolidates Round 1 — 58 numbered binding requirements, Round 1 defaults stand with 1 override: FM3.10 quarantine strips embeddings)

- [x] **3.1 Winston (Architect)** — `/bmad-agent-architect` _(Model: Opus 4.6 [1M] · Thinking: high)_
  - [x] READS requirements.md from elicitation rounds BEFORE designing
  - [x] Architecture doc at `_bmad-output/implementation-artifacts/praxis/memory/architecture.md` (105KB, Apr 12)
  - [x] Unified Memory interface designed (§2 — Memory facade + Pydantic models + scoping rules)
  - [x] Beads port plan (TypeScript → Python) (§3 — module structure, versioning, worktree semantics, Go→Python port plan)
  - [x] Mem0 dependency strategy (pip install, no fork) (§4 — pinning, backend config, scoping translation, fact extraction, adapter)
  - [x] Atelier decision memory pattern extraction (§5 — schema, capture protocol, retrieval scoring, TTL decay, post-read adoption summary)
  - [x] Privacy model from elicitation explicitly enforced in design (§8 — structural tenant isolation + facade enforcement; FM3.10 embedding-strip override honored)
  - [x] **Context strategy (MANDATORY):** Applied per §1 Reference Analysis — Beads, Mem0, Atelier studied sequentially with post-read adoption summaries (§5.5 explicitly documents post-Atelier additions)

- [x] **3.2 Murat (Test Architect)** — `/bmad-tea` _(Model: Opus 4.6 [1M] · Thinking: high)_ — **GATE: CONCERNS (conditional advance)**
  - [x] Test strategy at `_bmad-output/implementation-artifacts/praxis/memory/test-strategy.md` (TD Pass 1, ~1250 lines, 225 tests, 6 CRITICAL risks R-01..R-06, 88 requirement-linked tests, all 43 FMs covered)
  - [x] Privacy/scoping enforcement tests critical (R-01 pgvector orphans, R-02 cache invalidation, R-03 audit log PII, R-04 quarantine embedding strip, R-05 telemetry query leak, R-06 two-tenant export isolation — 6 CRITICAL no-waiver)
  - [x] Retrieval correctness tests designed (TD §10.1 pure function property tests + NR §3 additions with ratified p99 matrix)
  - [x] **NR Pass 2 (bonus):** NFR assessment at `_bmad-output/implementation-artifacts/praxis/memory/nfr-report.md` (~800 lines, 30+ findings, zero HARD-FAIL across Security/Compliance/Performance/Reliability/Scalability)
  - [x] **3 Andrey ratifications captured:** NR-P-R1 p99 latency matrix (with hot-path <200ms guardrail); NR-C-A1 crypto-shred SLA = 7 calendar days (48hr recovery window → embedding purge → backup rewrite → KMS destruction by day 7 → DPA destruction certificate); NR-Q6 crash recovery RTO = 5 min; NR-Q2 entry ceiling = 100K soft / 250K hard
  - [x] **3 pre-3.3 conditions** opened as Amelia's first ordered tasks (Task A3.3.1 NR-S-A1 Mem0 SCA scan; Task A3.3.2 NR-SC-R2 connection pool sizing; Task A3.3.3 NR-S-R1 ruff TID251 + pre-commit grep)
  - [x] **13 pre-3.4 conditions** delegated to Winston as parallel arch.md v1.1 amendments (P0: crypto-shred structure, connection pool, full-tenant delete freeze; P1: p99 matrix, KMS degraded-mode, classifier CB, crash RTO; P2/P3: entry ceiling, manifest window, large-delete target, cache-ack timeout, manifest fault tolerance)

- [x] **3.3 Amelia (Developer)** — `/bmad-agent-dev` _(Model: Sonnet 4.6 [1M] · Thinking: high)_
  - [x] **Pre-condition A3.3.1** — Mem0 SCA scan (NR-S-A1) — CLEAN, 0 CVEs, lockfile pinned
  - [x] **Pre-condition A3.3.3** — Ruff TID251 + grep tripwire (NR-S-R1) — 4/4 self-test PASS
  - [x] **Pre-condition A3.3.2** — Connection pool sizing (NR-SC-R2) — implemented per strawman (pool_size=10, max_overflow=15, pool_pre_ping=True, pool_recycle=3600); 3/3 smoke tests PASS; Winston §4.2 amendment still pending (parallel track, non-blocking)
  - [x] **A3.3.4 Phase 3A** — Facade protocol definition (MemoryProtocol + Draft/Record split + error registry + conformance harness)
  - [x] **A3.3.4 Phase 3B-i** — Beads port (Bead Merkle chain + content_hash + BeadsStore)
  - [x] **A3.3.4 Phase 3B-ii** — Mem0 adapter (DI via Mem0ClientProtocol + fake client + PII stub + R-06 scoping tests)
  - [x] **A3.3.4 Phase 3B-iii** — Atelier minimal (decision capture/retrieval + §5.3 multiplicative scoring + R-04 in-place embedding strip)
  - [x] **A3.3.4 Phase 3C** — Facade composition (Memory class with tenant guard + method routing + audit buffer + R-01..R-06 battery + no-NotImplementedError negative test)
  - [x] Implementation in `_bmad-output/implementation-artifacts/praxis/memory/src/`
  - [x] Unified Memory API surface exposed (public `Memory` class + Pydantic models in `praxis.kernel.memory`)
  - [x] Mem0 integrated as dependency (via `Mem0ClientProtocol` DI boundary; live-backend integration deferred to Quinn Step 3.4)
  - [x] Beads core ported (content-addressed Merkle chain, pattern extraction not literal port per §3.6)
  - [x] **Context strategy honored:** Architecture §1.1/§3/§4/§5 read as pre-extracted patterns; raw 11MB Beads dump not reloaded; Mem0 and Atelier dumps consulted only selectively via Winston's adoption summaries
  - **Final test count:** 253 passed (14 content hash + property-based · 22 beads roundtrip · 22 mem0 adapter · 4 mem0 scoping · 21 atelier decision · 6 atelier quarantine · 12 atelier scoring property · 3 pool smoke · 17 facade composition · 6 facade privacy R-01..R-06 · 11 facade tenant identity · 10 facade no-NotImplementedError · 10 facade audit buffer · 84 protocol conformance (21 × 4 backends: beads + mem0_adapter + atelier + facade) · 11 protocol self-audit & registry)
  - **Cleo pre-check gate:** GREEN (ruff check + ruff format + NR-S-R1 self-test 4/4 + grep leak check CLEAN)

- [x] **3.3.5 Cleo (Clean Code Review)** — `/bmad-agent-clean-code-reviewer` _(Model: Sonnet 4.6 [1M] · Thinking: medium)_
  - [x] Target directory: `_bmad-output/implementation-artifacts/praxis/memory/src/`
  - [x] Review report saved to `_bmad-output/implementation-artifacts/praxis/memory/code-review.md`
  - [x] All CRITICAL violations resolved (blocks advancement to Quinn) — **0 CRITICAL found; ruff check + format clean across all 23 files**
  - [x] WARNING violations addressed or explicitly deferred with rationale — **3/6 applied (W1 hardcoded /tmp → tempfile.gettempdir, W5 dead if-pass, W6 -1 sentinel); 3/6 deferred with rationale (W2 _utc_now DRY, W3 _new_id DRY, W4 salted-hash DRY — all require _internal/common/ consolidation or Stage 7 salt plumbing, documented in code-review.md)**
  - [x] Auto-fixes applied where applicable (opt-in fix-all mode) — **8 fixes applied (F1–F8); ruff format reapplied; 253/253 tests still passing**
  - [x] **Gate:** 0 CRITICAL violations remaining — **GREEN**

- [x] **3.4 Quinn (QA)** — Testing _(Model: Sonnet 4.6 · Thinking: medium)_
  - [x] Coverage >= 85% — **98% aggregate** (855 stmts, 19 missed across 23 files) as of 2026-04-13
  - [x] Privacy/scoping tests pass — **42/42** (R-01..R-06 battery + 11 facade tenant identity + backend-level scoping; 0 waivers)
  - [x] Retrieval correctness verified — **69/69** (atelier decision retrieval + mem0 fact retrieval + facade routing + 12 scoring property tests + 84 protocol conformance)
  - [x] Live-backend integration closed (Step 3.3 deferral) — **11 new contract tests** against real `mem0.Memory` class (method presence + scoping kwargs + runtime-checkable); no API keys required
  - [x] **Total: 264/264 tests passing** (253 Stage 3.3 baseline + 11 Quinn additions)
  - [x] Summary at `_bmad-output/implementation-artifacts/praxis/memory/automation-summary.md`

- [x] **3.5 Alignment Review** _(Model: Opus 4.6 [1M] · Thinking: high)_
  - [x] Memory integrates with Pi-Mono cost events — **F-1 CLOSED 2026-04-13 (Stage 4.7):** Path A (retention_shred jobs) and Path B (tick-drain AuditBuffer) both wire Memory audit events to Pi-Mono events_outbox. Integration tests F-13.C1 + F-1.H6 green. See `runtime/outbox/path_a.py` + `drain_loop.py`.
  - [x] Memory stores pass through Compression layer — **F-2 DEFERRED 2026-04-13 (Stage 4.7 decision):** TONL passthrough is cost optimization, not correctness. Explicitly deferred to Stage 6 optimization pass per test-strategy §12 OQ-2. No Stage 4 or 5 work required.
  - [x] No API drift from Stages 1-2 — **CLEAN:** consistent `praxis.kernel.*` namespace, single public facade pattern, Python 3.11+, Pydantic models, async shape, error hierarchy, config-as-type. Stage 3's `_internal/` hiding convention (NR-S-R1 ruff TID251 + grep tripwire) is stricter than Stages 1-2; recommend back-propagation to Stage 4+.
  - [x] **Additional tracked items:** F-3 (durable jobs table for retention reaper, required for NFR-C-A1 7-day crypto-shred SLA + NFR-Q6 5-min RTO — Stage 4 infrastructure); F-4 (connection pool sizing validated only via strawman smoke test, answered naturally by 3.6).
  - [x] **F-5 (LOW — closed 2026-04-13 by Stage 4.3 Amelia, commit `6209b50`):** Memory telemetry module (`memory/src/praxis/kernel/memory/telemetry.py`) created as a new file defining `TelemetryEvent(frozen=True, extra='forbid')` with exactly seven R53-allowed fields (`metric_name`, `metric_type`, `value`, `labels`, `timestamp`, `praxis_version`, `tenant_hash`). This fulfills the Stage 4.1 architecture §9.1 and Stage 4.2 test-strategy §10.4.1 claims that referenced `praxis.kernel.memory.telemetry.TelemetryEvent` as a shipped Stage 3 artifact which was never actually built (Winston and Murat both assumed its existence; caught by Amelia during Stage 4.3 preload). Addition is **purely additive** — no existing Stage 3 code references `TelemetryEvent` (docstring-only appearances in `_internal/protocol.py:127,157,220`). Verified zero regression via full Stage 3 memory test suite **253/253 passing, 98% aggregate coverage** post-add (matches baseline per line 301 `253 Stage 3.3 + 11 Quinn env-gated = 264`). Binding condition #4 preserved because Stage 3 runtime behavior is unchanged. Resolves Stage 4.2 OQ-TS-8 field-set verification (TelemetryEvent.model_fields now matches test-strategy §10.4.1 ALLOWED_FIELDS exactly). Victory moment for preload-first gating discipline — caught before expensive rework.
  - [x] 6 CRITICAL risks (R-01..R-06) all MITIGATED with no waivers
  - [x] Alignment review saved to `_bmad-output/implementation-artifacts/praxis/memory/alignment-review.md`

- [x] **3.6 Pre-Sales Checkpoint** _(Model: Sonnet 4.6 · Thinking: low)_
  - [x] Demo: Ask Praxis a question, ask similar question later — `scripts/pre_sales_demo.py` runs end-to-end: store task 1 outcome (Q1-2026 pricing repositioning, 3-agent strategic advisory workflow) → retrieve_similar_tasks on Q2-2026 signature → 1 hit returned in 0.55 ms
  - [x] Measure second-task savings (30-50% target) — **58.6% cost savings measured** on Claude Sonnet 4.6 public pricing ($3/M input, $15/M output). Cold path: $0.003150 for 210 output tokens generated. Warm path: $0.001305 for 225 seed input tokens + 42 delta output tokens. Raw-token view is -27% (misleading); cost view is the actual pre-sales claim because input is 5× cheaper than output.
  - [x] Headline: **"Cross-session memory compounds — similar tasks use 58.6% fewer dollars on Claude Sonnet 4.6. The second time you ask Praxis a related question, it reads the prior answer instead of re-deriving it."**
  - [x] Blog post draft inline in pre-sales-checkpoint.md §9 ("Why Praxis is 58% cheaper on similar questions — and why that number is actually conservative")
  - [x] Checkpoint doc: `_bmad-output/implementation-artifacts/praxis/memory/pre-sales-checkpoint.md`
  - [x] Raw demo output: `_bmad-output/implementation-artifacts/praxis/memory/pre_sales_demo_result.json`

**Gate to Stage 4:** All boxes checked. Memory architecture.md exists. Measured savings reported (58.6% cost, beats 30-50% target). F-1 (Pi-Mono integration) and F-3 (durable jobs table) must close before Stage 4 completion claim; neither blocks Stage 4 Winston architecture start (elicitation round 4.0.1 `/bmad-brainstorming` Carson on tool library curation is the pre-flight).

---

### STAGE 4: Agent Runtime

**Prompt file:** `_bmad-output/planning-artifacts/Praxis/stage-4-winston-prompt.md`
**Output directory:** `_bmad-output/implementation-artifacts/praxis/runtime/`

- [x] **4.0 Pre-flight:** Verify Stages 1-3 complete — Stage 1 100%, Stage 2 100%, Stage 3 100% (two `[~]` F-1/F-2 items deferred with Stage 2 precedent to 4.7; Stage 4 Winston start authorized per Stage 3.6 gate text)

- [x] **4.0.1 Elicitation Round 1 (BEFORE Winston)** — `/bmad-brainstorming` (Carson) _(Model: Opus 4.6 · Thinking: high)_ — **COMPLETE 2026-04-13**
  - [x] **Primary method:** **Role Playing** — 5 personas executed (Strategic Advisor pinned to single-client-engagement per R11, SMB Founder, Enterprise COO, DevOps Engineer, Compliance Officer)
  - [x] **Secondary method:** **Six Thinking Hats** — W→Y→B→G→Blue executed (Red dropped per evidence-round rationale; documented in output §1)
  - [x] Personas to embody: all 5 per locked method
  - [x] Focus: Tool library curation via customer use case brainstorming
  - [x] Questions answered: 5 focus questions covered across 20 populated cells (5 personas × 4 hats; Blue consolidated into §5 meta-policy)
  - [x] Output: `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md` (~45 tools catalogued: 8 P0 + 15 P1 + 22 P2; 7 items in deferred-with-rationale appendix)
  - [x] Deliverable: prioritized tool list with rationale per tool — per-tool cards anchored to (persona, hat) pairs per output discipline contract; matrix coverage table + Winston §5 collision report (8 collisions surfaced) + P0 count defense (P0=8) + 2 architectural decisions escalated to Winston (read/write default mode, human-in-loop approval workflow scope)

- [x] **4.1 Pre-flight:** Winston's frame MUST load three documents before drafting begins:
  - [x] `_bmad-output/planning-artifacts/Praxis/stage-4-winston-prompt.md` (existing architect frame)
  - [x] `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md` (4.0.1 Carson output — §6 Tool Library Catalog constraint)
  - [x] `_bmad-output/planning-artifacts/Praxis/stage-4-deferred-findings-brief.md` (F-1 + F-3 architectural inputs per Section 4.7)

- [x] **4.1 Winston (Architect)** — `/bmad-agent-architect` _(Model: Opus 4.6 [1M] · Thinking: high)_ — **COMPLETE 2026-04-13, architecture.md v0.3+ ratified**
  - [x] READS tool-library-requirements.md from elicitation BEFORE designing
  - [x] READS stage-4-deferred-findings-brief.md BEFORE designing — F-1 and F-3 must be absorbed into §3/§4/§5/§8/§9
  - [x] Architecture doc at `_bmad-output/implementation-artifacts/praxis/runtime/architecture.md`
  - [x] **F-1 absorbed:** outbox adapter shape, trigger mapping, failure semantics, tenant identity passthrough, taxonomy unification (see brief §5 checklist)
  - [x] **F-3 absorbed:** jobs table schema, state transitions, worker lifecycle, crash recovery (NFR-Q6 5-min RTO), deployment topology decision, outbox/jobs-table co-location decision (see brief §5 checklist) — absorbed via Path A/B split + Jobs Infrastructure
  - [x] **F-2 parked:** listed in §12 Open Questions as Stage 6 reassess, no active work
  - [x] BMAD agent loader design (from `_bmad/_config/agent-manifest.csv`)
  - [x] Registry + matching algorithm
  - [x] Subagent vs team mode design
  - [x] MCP tool adapter design
  - [x] Tool library catalog ANCHORED on elicitation output (not invented)
  - [x] Information asymmetry structural enforcement
  - [x] **Context strategy (MANDATORY):** Apply the Universal Sequential Reference Reading rule from Section 4.6. Gas Town dump is 12MB — the largest single reference in the project (~3M tokens alone). Sequence: read agent-manifest.csv → draft loader section → read Atomic Agents for schemas → draft registry → read Atelier for wave execution patterns → draft execution design → finally read Gas Town SELECTIVELY (coordination patterns only, not the whole codebase)
  - [!] **OQ-N carried forward:** AuditBuffer drain coordination is the single remaining open question; flagged as the only Stage 4.6 blocker.

- [x] **4.2 Murat (Test Architect)** — `/bmad-tea` _(Model: Opus 4.6 [1M] · Thinking: high)_ — **COMPLETE 2026-04-13** — test-strategy.md v0.1 ratified, 5,950 lines, 16 sections, 204 test IDs (172 P0, 86 CRITICAL-anchored), Q3 retarget landed cleanly across 9 sites (option (b) — import Memory's `TelemetryEvent` + `RuntimeTelemetryEnvelope` wrapper), four independent R53 structural guards (is-identity / AST type-redefinition scan / wrapper delegation / nightly cross-stage drift), 11 OQs (1 RESOLVED OQ-TS-10, 1 deferred Stage 6, 9 working with close-out paths), §16 handoff contract binds Amelia on test-first + module hierarchy + Q3 type discipline
  - [x] Test strategy at `_bmad-output/implementation-artifacts/praxis/runtime/test-strategy.md`
  - [x] Security model tests (sandbox, allowlists) — §10 MCP/Sandbox/OTel R53 harness, 4 classes
  - [x] Asymmetry enforcement tests — §11 three-layer structural harness (~45 tests, S4.R-01 product-defining)
  - [x] Circular spawning prevention tests — §6 critical scenarios + §11 Hypothesis state-machine

- [x] **4.3 Amelia (Developer)** — `/bmad-agent-dev` _(Model: Sonnet 4.6 [1M] · Thinking: high)_ — **COMPLETE 2026-04-13** — Agent Runtime package shipped. 3-checkpoint cadence executed cleanly: **C1** (proxies + observability, 81 tests, S4.R-01 product-defining closed, four R53 structural guards in place, Q3 option (b) import-and-wrap cashed out); **C2** (jobs + outbox, 74 tests, S4.R-02 Path A atomicity + S4.R-03 NFR-Q6 crash recovery closed, F-1/F-3/F-13.C1 absorption, F-13.C1 `no_waiver` proven via Postgres xmin shared-transaction identity, OQ-N Path (i) position-based shim stable at 43 MB/100K entries, one-time `a6ef167` bundling violation escalated to Cleo); **C3** (models + loader + registry + mcp_adapter + tools + spawner, 179 tests, S4.R-04..R-08 closed, Q5 `runtime.agent.allowlist.stripped.count` metric implemented, OQ-TS-11 MCP SDK version guard resolved via `mcp 1.27.0`, Q3 retarget landed cleanly across 9 sites). Cumulative ~334 Runtime tests green, all §11.11 coverage gates met, test-first discipline (zero bundled test+impl commits in C3), Stage 3 memory canary 264/264 zero regression throughout. F-5 (Memory `telemetry.py` Stage 3 post-ratification addition, commit `6209b50`) closed during preload. Ready for Stage 4.3.5 Cleo clean-code review.
  - [x] Implementation in `_bmad-output/implementation-artifacts/praxis/runtime/src/`
  - [x] All 16 BMAD agents loadable (loader/manifest.py parses `_bmad/_config/agent-manifest.csv`)
  - [x] MCP tools bound and callable (8 P0 / 9 impl files per §6.1.7 Python-sandbox/subprocess split)
  - [x] Sandbox functional (Class A–E blast-radius tiering, §9.5 red team battery green, Class D subprocess narrow allowlist enforced)

- [x] **4.3.5 Cleo (Clean Code Review)** — `/bmad-agent-clean-code-reviewer` _(Model: Sonnet 4.6 [1M] · Thinking: medium)_ — **COMPLETE 2026-04-13**
  - [x] Target directory: `_bmad-output/implementation-artifacts/praxis/runtime/src/`
  - [x] Review report saved to `_bmad-output/implementation-artifacts/praxis/runtime/code-review.md` (verdict: RATIFY, commit d4f53b9)
  - [x] All CRITICAL violations resolved — M1 mypy, M2/M3/M4 config, M5 _internal coupling (commits 4bb9f46 + 9ea12e8)
  - [x] WARNING violations addressed or explicitly deferred with rationale — ruff auto-fixes applied (commit 2d6e2c6)
  - [x] Auto-fixes applied — ruff lint + format + import sorting
  - [x] **Gate:** 0 CRITICAL violations remaining

- [x] **4.4 Quinn (QA)** — Testing _(Model: Sonnet 4.6 · Thinking: medium)_ — **COMPLETE 2026-04-13**
  - [x] Coverage >= 85% — runtime 97% (355 tests, 0 failures)
  - [x] All 16 agents spawn successfully — producer + reviewer proxy confirmed for all 16
  - [x] Information asymmetry verified (structural) — 8 mypy S4.R-01 fixtures pass

- [x] **4.5 Alignment Review** _(Model: Opus 4.6 [1M] · Thinking: high)_ — **COMPLETE 2026-04-13**
  - [x] Runtime uses Stage 3 Memory correctly — ProducerMemoryProxy/ReviewerMemoryProxy correct; AuditBuffer seam wired; D-1 deviation tracked (missing _cross_check_tenant, non-blocking)
  - [x] Runtime cost-tracked via Stage 1 Pi-Mono — Path A same-transaction + Path B tick-drain both write to events_outbox; F-1.H6 dedup passes; D-2 deviation tracked (AuditEvent.id workaround, non-blocking)
  - [x] No drift — 3 MEDIUM/LOW deviations documented in alignment-review-4.5.md; none blocking; 4.5 gate PASSES

- [x] **4.6 Pre-Sales Checkpoint** _(Model: Sonnet 4.6 · Thinking: low)_ — **COMPLETE 2026-04-13**
  - [x] Demo: "16 specialized agents loaded at $1.40/workflow" — pre_sales_demo.py passes (test_pre_sales_checkpoint green)
  - [x] Cost per agent captured — Producer $0.96/spawn, Reviewer $0.44/spawn (Sonnet 4.6, 60%/20% utilisation @ $3/$15 per M tokens)

- [x] **4.7 Stage 3 Deferred Findings Closure (MANDATORY for Stage 5 gate)** — **COMPLETE 2026-04-13**
  - [x] **F-1 closed:** Memory → Pi-Mono CostEvent wiring implemented. Path A (`outbox/path_a.py`): same-transaction complete_retention_job_path_a writes CostEvent to events_outbox atomically. Path B (`outbox/drain_loop.py`): tick-drain drains AuditBuffer STORE_FACT/STORE_TASK_OUTCOME/STORE_DECISION events to events_outbox via pg_insert. Integration tests: F-13.C1 (test_path_a_completion_writes_event_row_in_postgres) + F-1.H6 (test_f1_h6_path_b_dedup_on_crash_replay) — both green with Postgres.
  - [x] **F-3 closed:** Durable jobs table for retention reaper implemented. `jobs/schema.py`: jobs_queue with state machine + claim fencing. `jobs/worker.py`: JobsWorker._reclaim_orphans_on_startup (NFR-Q6). NFR-C-A1 7-day crypto-shred SLA: Path A atomicity ensures every retention_shred produces a CostEvent. NFR-Q6 5-min RTO: test_f3_h5_nfr_q6_orphan_reclaim_on_startup passes < 10s canary; test_f3_h4_concurrent_claim_fencing confirms fencing.
  - [x] **F-2 deferred:** Memory → Compression TONL passthrough — decision: **DEFER to Stage 6 optimization pass.** Rationale: cost optimization, not correctness (Memory writes work correctly without TONL encoding; adding bead payload compression is a Stage 6 concern when token savings justify the wiring complexity). Matches test-strategy §12 OQ-2 default.
  - [x] Pipeline.md Stage 3 items 3.5 F-1 and F-2 `[~]` flipped to `[x]` with closure notes (see lines 305-306 above)

**Gate to Stage 5:** All boxes checked, INCLUDING 4.7. Runtime architecture.md exists. F-1 and F-3 are implementation-complete and tested before 4.6 ratifies — no carry-forward permitted.

---

### STAGE 5: MAC (Meta-Agent Controller) — Reasoning Engine

**Prompt file:** `_bmad-output/planning-artifacts/Praxis/stage-5-winston-prompt.md`
**Output directory:** `_bmad-output/implementation-artifacts/praxis/mac/`

- [x] **5.0 Pre-flight:** Verify Stages 1-4 complete — Stage 1 100%, Stage 2 100%, Stage 3 100%, Stage 4 100% (incl. 4.7). `mac/` output directory created. Session started 2026-04-14.

- [x] **5.0.1 Elicitation Round 1 (BEFORE Winston)** — `/bmad-brainstorming` (Carson) — **COMPLETE 2026-04-14** _(Model: Sonnet 4.6 [1M])_
  - [x] **Primary method:** **First Principles Thinking** — 8 foundational dimensions derived (D1–D8)
  - [x] **Secondary method:** **Values Archaeology** — 3 personas (Marco Series-A founder / Elena Enterprise COO / David consultant); D9–D13 + refinements to D2 and D1
  - [x] **Tertiary method:** **Reverse Brainstorming** — 13 bad properties inverted; confirmed existing dimensions; added D13 Scenario Coverage, D14 Extractable Logic
  - [x] Focus: Define "strategic analysis quality" via creative brainstorming — Q1 (universal dimensions, per-workflow via gate weights) and Q3 (12–15, collapse to 12 by Winston) answered before Phase 1
  - [x] Questions answered: D1 Epistemic Calibration (comprehensiveness/honesty), D4 Steelman + D5 Dissent (dissent preservation), D7 Risk Specificity (risk identification), D9 Actionability Calibration (actionability), D3 Falsifiability + D12 Unknown Unknown (honesty about uncertainty)
  - [x] Output: 14 dimensions with scoring protocols in `_bmad-output/implementation-artifacts/praxis/mac/quality-dimensions-draft.md`; Top-5 ranked; 6 open questions + 6 tension pairs for Winston; D11+D12 collapse candidate flagged; D14 Stage-6 placement candidate flagged

- [x] **5.0.2 Elicitation Round 2 (BEFORE Winston)** — `/bmad-cis-problem-solving` (Dr. Quinn) — **COMPLETE 2026-04-14** _(Model: Sonnet 4.6 [1M])_
  - [x] **Primary method:** Failure Mode Analysis — all 14 dimensions; 4 BLOCKERs (D2 Tier-1 flaw, D4 judge protocol gap, D10 systematic false positive, D12 boilerplate gaming); 10 CONCERNs; all BLOCKERs resolved
  - [x] **Secondary method:** Assumption Busting — 7 assumptions; 0 HOLD / 5 REVISE / 2 REPLACE; R12 Internal Consistency added; R13 Evidence Sourcing conditional
  - [x] **Tertiary method:** TRIZ Contradiction Matrix — T3 (Calibration vs. Actionability → section-aware gates); T1/T4/T5 compound (→ 3-layer content levels L1/L2/L3); T7 new (Steelman vs. Impartiality → R9 scope restriction to findings sections)
  - [x] Focus: Red team — 4 BLOCKERs resolved; D7 merged into R1; D14 removed to Stage 6; D11+D12 → R10; 6 structural architecture requirements (Req-A through Req-F) binding on Winston
  - [x] Questions answered: all FMA failure modes documented; gate set hardened to 12 confirmed + 1 conditional; OQ-1/2/3 resolved; OQ-7/8/9 new
  - [x] Output: `_bmad-output/implementation-artifacts/praxis/mac/quality-rubric.md` — 12 gates R1–R12 + conditional R13; Req-A/B/C/D/E/F architectural mandates; measurement protocol refinements for top-5 gates

- [x] **5.0.3 Elicitation Round 3 (BEFORE Winston)** — `/bmad-advanced-elicitation` — **COMPLETE 2026-04-14** _(Model: Sonnet 4.6 [1M])_
  - [x] **Primary method:** Comparative Analysis Matrix — 18 candidates scored on 5 criteria (CR/GC/MD/AS/TD); 10 selected with coverage rationale; full matrix published
  - [x] **Secondary method:** Architecture Decision Records — ADR-1 (blind vs. open → hybrid), ADR-2 (gold standard format → checklist+examples), ADR-3 (A4 validation → Andrey 3-question simplified checklist + Spearman correlation)
  - [x] **Tertiary method:** Thesis Defense — Statistician (N=10 → directional claim, not hypothesis test), Practitioner (cherry-pick → full disclosure of all 10 results), Adversary (gaming R4/R5 → add enhanced single-agent as second baseline)
  - [x] Focus: Benchmark finalized — 10 questions covering 10 distinct strategic question types; two baseline conditions (vanilla + enhanced)
  - [x] Questions answered: OQ-5 resolved (top-5 weighted, empirical update after); OQ-6 resolved (10 gold standards pre-load Memory bootstrap); A4 validation loop designed
  - [x] Output: `_bmad-output/implementation-artifacts/praxis/mac/benchmark-questions.md` — 10 questions + gold standards + calibration anchors R1–R12 + scoring protocol + OQ-5/6 resolution
  - [x] quality-rubric.md updated: OQ-5 and OQ-6 resolved in Section 9

- [x] **5.1 Winston (Architect)** — `/bmad-agent-architect` _(Model: Opus 4.6 [1M] · Thinking: max)_ — **RATIFIED 2026-04-14. OQ-MAC-1 resolved via Option Y sidecar (`mac_bootstrap_metadata`). arch.md v0.1 binding for Stage 5.2+. Stage 3 remains frozen.**
  - [x] READS quality-rubric.md AND benchmark-questions.md BEFORE designing — preload phase verified; all 12 R1–R12 + Req-A/B/C/D/E/F + benchmark §2/§5/§6/§7/§8 anchored
  - [x] Architecture doc at `_bmad-output/implementation-artifacts/praxis/mac/architecture.md` — 2,071 lines, 13 sections + §13.1 Gate Checklist + §13.2 residual OQs
  - [x] 3-cycle iteration pattern fully specified — §5.1–§5.7: state machine, phase runner, Cycle 2 parallelism, backtracking, Forge fallback (SQ-7), ResourceBudget defaults
  - [x] 12 quality gates catalog ANCHORED on elicitation rubric (not invented) — §6.1 catalog table with "Source Row: quality-rubric.md §6 R{N}" per row; R13 DEFERRED per SQ-3
  - [x] Information asymmetry router design — §7.1 Req-F two-step reviewer protocol; §7.2 binding to Runtime §4.1 ProducerMemoryProxy/ReviewerMemoryProxy single-point `_construct_memory_proxy`
  - [x] Evaluation harness uses elicitation benchmark questions — §9.2 verbatim 10 Qs + §9.4 top-5 weighting (OQ-5) + §9.5 ADR-1 hybrid + §9.6 ADR-3 Spearman ≥0.6 + §9.7 N=10 directional framing
  - [x] **Context strategy (MANDATORY):** Apply the Universal Sequential Reference Reading rule from Section 4.6. MAC integrates ALL prior stages — this is the highest-context step in the project. Sequence: (1) Read Stage 1 Pi-Mono arch → note cost-tracking hooks. (2) Clear → read Stage 2 Compression arch → note reasoning chain preservation from Forge. (3) Clear → read Stage 3 Memory arch → note unified interface. (4) Clear → read Stage 4 Runtime arch → note agent spawning. (5) Clear → read Atelier dump SELECTIVELY (quality gates + wave execution only). (6) Draft MAC architecture with all integration points verified
  - [x] **OQ-MAC-1 RESOLVED 2026-04-14:** Option Y sidecar table `mac_bootstrap_metadata` is the ratified bootstrap implementation path. Option X (direct JSONB column on `experience_entries`) rejected — Stage 3 stays frozen. See mac/architecture.md §8.1 Ratification Decision + §13.2 Rejected Alternatives. Amelia (5.3) implements the `0001_mac_bootstrap_metadata` migration as a MAC-owned schema artifact.

- [x] **5.2 Murat (Test Architect)** — `/bmad-tea` _(Model: Opus 4.6 [1M] · Thinking: max)_ — **RATIFIED 2026-04-14. 16-entry `no_waiver` allow-list per mac/test-strategy.md §13.3.3. Decisions 1/2/3 locked in. mac/test-strategy.md v0.1 binding for Stage 5.3.**
  - [x] Test strategy at `_bmad-output/implementation-artifacts/praxis/mac/test-strategy.md` — 3,505 lines, 17 sections, 222 test IDs (exceeds Runtime's 204)
  - [x] Most intensive test design in the project — 222 total test IDs across §3 gate-level (75) + §4–§12 (147)
  - [x] Cycle state machine property tests — §4.2 `MAC-T-CYCLE-STATE-01..05` (Tension #2 deterministic replay pattern)
  - [x] Adversarial tests (can we trick the MAC?) — §10 Persona 3 gaming scenarios + rotation protocol (Tension #6)
  - [x] **Context strategy (MANDATORY):** Apply the Universal Sequential Reference Reading rule from Section 4.6. Read Winston's MAC arch first → clear → read each prior stage's test-strategy.md one at a time to understand the existing test vocabulary → draft MAC test strategy building on established patterns
  - [x] **Decision 1 RATIFIED 2026-04-14:** 10/12 `no_waiver` split — 10 direct MAC `no_waiver` tests at §3 (items 1–8, 10, 12), items 9/11 split into deterministic sub-tests (carry `no_waiver`) and live sub-tests (carry `critical + asymmetry_structural/mac_adversarial` only)
  - [x] **Decision 2 RATIFIED 2026-04-14 (scope expansion):** OQ-TS-9 allow-list meta-test `tests/static/runtime/test_no_waiver_inventory.py` spec at §13.3; 16-entry `NO_WAIVER_ALLOWLIST` with self-referential lock; Amelia (5.3) implements verbatim. The 2 Runtime OTEL provisional entries (#2, #3) carry `PENDING AUDIT at 5.5 Alignment Review` — Andrey's audit decision, not Amelia's/Murat's/Winston's to modify
  - [x] **Decision 3 RATIFIED 2026-04-14:** 4 SQs baked into draft as ratified semantics (not flagged as assumptions) — S-Q1 bootstrap idempotency (§8.4), S-Q2 violation counter (§9.3), S-Q3 benchmark harness nightly-split (§7.9), S-Q4 A4 release-gate Spearman fixture (§7.10)

- [ ] **5.3 Amelia (Developer)** — `/bmad-agent-dev` _(Model: Opus 4.6 [1M] · Thinking: high)_
  - [ ] Implementation in `_bmad-output/implementation-artifacts/praxis/mac/src/`
  - [ ] 3-cycle controller functional
  - [ ] Quality gates engine working
  - [ ] Learning loop writes to Memory
  - [ ] **Note:** Opus [1M] (not Sonnet) — MAC integrates all prior stages AND the implementation itself is large
  - [ ] **Context strategy (MANDATORY):** Apply the Universal Sequential Reference Reading rule from Section 4.6. Build in this order: (1) Read Winston's MAC arch + Murat's test strategy. (2) Implement task interpreter (small, self-contained). (3) Implement plan decomposer (reads only arch). (4) Implement 3-cycle controller (uses Pi-Mono — read Pi-Mono source selectively, not arch). (5) Implement quality gates (reads Atelier patterns only, not full dump). (6) Implement learning loop (reads Memory source from Stage 3). Never all at once

- [ ] **5.3.5 Cleo (Clean Code Review)** — `/bmad-agent-clean-code-reviewer` _(Model: Sonnet 4.6 [1M] · Thinking: high)_
  - [ ] Target directory: `_bmad-output/implementation-artifacts/praxis/mac/src/`
  - [ ] Review report saved to `_bmad-output/implementation-artifacts/praxis/mac/code-review.md`
  - [ ] All CRITICAL violations resolved (blocks advancement to Quinn)
  - [ ] WARNING violations addressed or explicitly deferred with rationale
  - [ ] Auto-fixes applied where applicable (opt-in fix-all mode)
  - [ ] **Extra scrutiny:** MAC is the highest-risk component — expect MORE review passes if needed
  - [ ] **Gate:** 0 CRITICAL violations remaining

- [ ] **5.4 Quinn (QA)** — Testing _(Model: Opus 4.6 [1M] · Thinking: high)_
  - [ ] Coverage >= 90% (highest gate — core differentiation)
  - [ ] End-to-end MAC workflow passes
  - [ ] Backtracking verified
  - [ ] **Note:** Opus [1M] — MAC adversarial tests require reading full codebase + prior arch docs + test strategy simultaneously

- [ ] **5.5 Alignment Review** _(Model: Opus 4.6 [1M] · Thinking: max)_
  - [ ] MAC uses ALL prior stages correctly
  - [ ] No architectural contradictions
  - [ ] **Context strategy (MANDATORY):** Apply the Universal Sequential Reference Reading rule from Section 4.6. Read Stages 1-4 architectures ONE AT A TIME, take notes on invariants (data models, API contracts, language choices, error patterns). Only AFTER accumulating notes, read the Stage 5 MAC architecture. Compare against notes, flag inconsistencies with file:line references

- [ ] **5.6 Pre-Sales Checkpoint (THE BIG ONE)** _(Model: Opus 4.6 · Thinking: high)_
  - [ ] 10 benchmark strategic questions prepared
  - [ ] Single-agent baseline run for all 10
  - [ ] Praxis MAC run for all 10
  - [ ] Blind evaluation (target: +15-25% quality improvement)
  - [ ] Headline: "Praxis MAC beats single-agent by X% on strategic questions at Y× cost"

**Gate to Stage 6:** All boxes checked. MAC architecture.md exists. Quality improvement DEMONSTRABLY measurable.

---

### STAGE 6: Studio Workflow Template (First User-Facing Product)

**Prompt file:** `_bmad-output/planning-artifacts/Praxis/stage-6-winston-prompt.md`
**Output directory:** `_bmad-output/implementation-artifacts/praxis/studio/`

- [ ] **6.0 Pre-flight:** Verify Stages 1-5 complete

- [ ] **6.0.1 Elicitation Round 1 (BEFORE Winston)** — `/bmad-market-research` (Mary) _(Model: Opus 4.6 · Thinking: high)_
  - [ ] **Primary approach:** **Voice of Customer (VOC) protocol** — semi-structured interview questions targeting real strategic advisory buyers
  - [ ] **Focus segments:** Series A-C startups, mid-market COOs, consultancy partners — avoid Fortune 500 (out of ICP)
  - [ ] **Deliverable format:** language inventory (verbatim quotes) + phrase frequency table + jargon glossary
  - [ ] Focus: Customer language discovery for strategic advisory
  - [ ] Questions answered: how customers phrase questions, industry jargon, budget context, buyer role
  - [ ] Output: `_bmad-output/implementation-artifacts/praxis/studio/customer-language-research.md`

- [ ] **6.0.2 Elicitation Round 2 (BEFORE Winston)** — `/bmad-cis-design-thinking` (Maya) _(Model: Opus 4.6 · Thinking: high)_
  - [ ] **Primary method:** **Empathy Mapping** (empathize phase — Says / Thinks / Does / Feels quadrants)
  - [ ] **Secondary method:** **Jobs to be Done** (define phase — functional, emotional, social jobs being hired)
  - [ ] **Tertiary method:** **Journey Mapping** (empathize phase — complete user experience from pain → search → eval → decision → defense to stakeholders)
  - [ ] **Quaternary method:** **How Might We** (define phase — reframe pain points as opportunity questions)
  - [ ] Focus: Empathy mapping — what customers actually want from strategic analysis
  - [ ] Questions answered: emotional state, stakeholder defense, internal sharing format
  - [ ] Output: `_bmad-output/implementation-artifacts/praxis/studio/empathy-map.md`

- [ ] **6.0.3 Elicitation Round 3 (BEFORE Winston)** — `/bmad-advanced-elicitation` _(Model: Opus 4.6 · Thinking: high)_
  - [ ] **Primary method:** **Architecture Decision Records** (technical #20 — document each output format decision as ADR with options, trade-offs, rationale)
  - [ ] **Secondary method:** **User Persona Focus Group** (collaboration #4 — have personas from Round 2 react to draft output formats)
  - [ ] **Tertiary method:** **Critique and Refine** (core #42 — systematic review of draft formats for strengths/weaknesses)
  - [ ] Focus: Finalize Studio output format contracts
  - [ ] Questions answered: brief length, deck format, dissent prominence, export formats, shareable links
  - [ ] Output: `_bmad-output/implementation-artifacts/praxis/studio/customer-requirements.md`

- [ ] **6.1 Winston (Architect)** — `/bmad-agent-architect` _(Model: Opus 4.6 [1M] · Thinking: high)_
  - [ ] READS all 3 elicitation outputs BEFORE designing
  - [ ] READS Tokonomics rounds as working examples of quality output
  - [ ] Architecture doc at `_bmad-output/implementation-artifacts/praxis/studio/architecture.md`
  - [ ] YAML workflow template schema
  - [ ] `studio/strategic_session.yaml` specification ANCHORED on customer requirements
  - [ ] Jinja2 output templates (brief, deck, executive summary) match empathy map
  - [ ] A/B validation harness design
  - [ ] 10 benchmark question set (from Stage 5 elicitation)
  - [ ] **Context strategy (MANDATORY):** Apply the Universal Sequential Reference Reading rule from Section 4.6. Sequence: (1) Read elicitation outputs (customer-language, empathy map, customer-requirements) — small, read together. (2) Clear → read Stage 5 MAC arch to understand how Studio invokes it. (3) Clear → read Tokonomics rounds ONE AT A TIME as working examples of output quality. (4) Draft Studio YAML schema + templates using accumulated knowledge

- [ ] **6.2 Murat (Test Architect)** — `/bmad-tea` _(Model: Sonnet 4.6 · Thinking: medium)_
  - [ ] Test strategy at `_bmad-output/implementation-artifacts/praxis/studio/test-strategy.md`
  - [ ] Benchmark regression tests designed
  - [ ] Output format tests designed

- [ ] **6.3 Amelia (Developer)** — `/bmad-agent-dev` _(Model: Sonnet 4.6 · Thinking: medium)_
  - [ ] Implementation (mostly YAML + templates) in `_bmad-output/implementation-artifacts/praxis/studio/`
  - [ ] Studio workflow executable end-to-end
  - [ ] Output templates render correctly

- [ ] **6.3.5 Cleo (Clean Code Review)** — `/bmad-agent-clean-code-reviewer` _(Model: Sonnet 4.6 · Thinking: medium)_
  - [ ] Target directory: `_bmad-output/implementation-artifacts/praxis/studio/` (Python glue code only; YAML/Jinja2 reviewed separately)
  - [ ] Review report saved to `_bmad-output/implementation-artifacts/praxis/studio/code-review.md`
  - [ ] All CRITICAL violations resolved (blocks advancement to Quinn)
  - [ ] WARNING violations addressed or explicitly deferred with rationale
  - [ ] Auto-fixes applied where applicable (opt-in fix-all mode)
  - [ ] **Note:** Stage 6 is mostly YAML config + Jinja2 templates; Cleo reviews only the Python workflow engine glue
  - [ ] **Gate:** 0 CRITICAL violations remaining

- [ ] **6.4 Quinn (QA)** — Testing _(Model: Sonnet 4.6 · Thinking: medium)_
  - [ ] Coverage >= 80%
  - [ ] Benchmark question regression tests pass
  - [ ] Dissent preservation verified in outputs

- [ ] **6.5 Alignment Review** _(Model: Opus 4.6 [1M] · Thinking: high)_
  - [ ] Studio uses MAC (Stage 5) correctly
  - [ ] Output format matches Tokonomics rounds quality bar

- [ ] **6.6 Pre-Sales Checkpoint** _(Model: Sonnet 4.6 · Thinking: medium)_
  - [ ] Live Studio demo ready
  - [ ] First real strategic question run end-to-end
  - [ ] Result cost < $10, time < 30 min, quality meets rubric
  - [ ] Headline: "Praxis Studio delivers a 20-page strategic analysis with red team in X minutes for $Y"

**Gate to Stage 7:** All boxes checked. Studio demo-ready.

---

### STAGE 7: POV Delivery Harness (Web UI + Auth + Billing)

**Prompt file:** `_bmad-output/planning-artifacts/Praxis/stage-7-winston-prompt.md`
**Output directory:** `_bmad-output/implementation-artifacts/praxis/shell/`

- [ ] **7.0 Pre-flight:** Verify Stages 1-6 complete

- [ ] **7.0.1 Elicitation Round 1 (BEFORE Winston)** — `/bmad-cis-innovation-strategy` (Victor) _(Model: Opus 4.6 · Thinking: high)_
  - [ ] **Primary framework:** **Value Proposition Canvas** (business_model category — match customer jobs/pains/gains to product offering and pricing)
  - [ ] **Secondary framework:** **Revenue Model Innovation** (business_model category — explore alternative monetization: per-session, subscription, credit packs, usage-based, freemium, gain-share)
  - [ ] **Tertiary framework:** **Business Model Canvas** (business_model category — map all 9 blocks to validate pricing fits the overall model)
  - [ ] **Quaternary framework:** **Lean Startup Methodology** (strategic category — identify riskiest pricing assumption, design MVP test)
  - [ ] Focus: Pricing model + business model validation
  - [ ] Questions answered: per-session vs subscription vs credit packs, trial policy, enterprise upgrade path, price points, free tier dynamics
  - [ ] Output: `_bmad-output/implementation-artifacts/praxis/shell/pricing-strategy.md`

- [ ] **7.0.2 Elicitation Round 2 (BEFORE Winston)** — `/bmad-cis-storytelling` (Sophia) _(Model: Opus 4.6 · Thinking: high)_
  - [ ] **Primary story type:** **Origin Story** (strategic category — "Built With Praxis" narrative: sparked by 12 weeks of self-demonstrating the product)
  - [ ] **Secondary story type:** **Positioning Story** (strategic category — unique market position vs consulting firms, LLM wrappers, single-agent tools)
  - [ ] **Tertiary story type:** **Customer Journey** (transformation category — before/after arc for onboarding narrative: "before I had no structured strategic analysis; after, I have a multi-agent board at $2/session")
  - [ ] **Quaternary story type:** **Pitch Narrative** (persuasive category — compelling action-oriented pitch for the landing page hero)
  - [ ] Focus: Launch messaging + onboarding narrative
  - [ ] Questions answered: opening pitch, "Built With Praxis" story, onboarding copy, first-session walkthrough, error messages
  - [ ] Output: `_bmad-output/implementation-artifacts/praxis/shell/messaging-and-onboarding.md`

- [ ] **7.1 Winston (Architect)** — `/bmad-agent-architect` _(Model: Opus 4.6 [1M] · Thinking: high)_
  - [ ] READS pricing-strategy.md AND messaging-and-onboarding.md BEFORE designing
  - [ ] Architecture doc at `_bmad-output/implementation-artifacts/praxis/shell/architecture.md`
  - [ ] Next.js + FastAPI + Clerk + Stripe stack defined
  - [ ] API endpoint specifications
  - [ ] "Built With Praxis" public dashboard design
  - [ ] UI copy and onboarding flow EMBED elicitation outputs (not invented)
  - [ ] **Context strategy (MANDATORY):** Apply the Universal Sequential Reference Reading rule from Section 4.6. Sequence: (1) Read elicitation outputs (small, together). (2) Clear → read Stage 6 Studio arch to understand the workflow API. (3) Clear → read Stage 1 Pi-Mono arch for billing integration. (4) Clear → draft shell architecture. No need to read the reference dumps — Stage 7 is new code using standard SaaS patterns

- [ ] **7.2 Murat (Test Architect)** — `/bmad-tea` _(Model: Sonnet 4.6 · Thinking: high)_
  - [ ] Test strategy at `_bmad-output/implementation-artifacts/praxis/shell/test-strategy.md`
  - [ ] E2E tests: signup → first session → billing
  - [ ] Workspace isolation tests

- [ ] **7.3 Amelia (Developer + frontend support)** — `/bmad-agent-dev` _(Model: Sonnet 4.6 [1M] · Thinking: high)_
  - [ ] Implementation in `_bmad-output/implementation-artifacts/praxis/shell/`
  - [ ] Web UI functional (Next.js app)
  - [ ] FastAPI backend exposes required endpoints
  - [ ] Clerk auth integrated
  - [ ] Stripe billing integrated
  - [ ] **Context strategy (MANDATORY):** Apply the Universal Sequential Reference Reading rule from Section 4.6. Build in this order: (1) Backend skeleton (FastAPI routes + Pydantic models) from Winston's arch. (2) Clear → auth integration (Clerk docs, separate read). (3) Clear → billing integration (Stripe docs, separate read). (4) Clear → frontend Next.js app (shadcn components, separate read). Never all at once. Also: consult Stage 1 Pi-Mono source selectively for billing reconciliation

- [ ] **7.3.5 Cleo (Clean Code Review)** — `/bmad-agent-clean-code-reviewer` _(Model: Sonnet 4.6 [1M] · Thinking: medium)_
  - [ ] Target directory: `_bmad-output/implementation-artifacts/praxis/shell/api/` (Python/FastAPI backend only)
  - [ ] Review report saved to `_bmad-output/implementation-artifacts/praxis/shell/code-review.md`
  - [ ] All CRITICAL violations resolved (blocks advancement to Quinn)
  - [ ] WARNING violations addressed or explicitly deferred with rationale
  - [ ] Auto-fixes applied where applicable (opt-in fix-all mode)
  - [ ] **Scope limitation:** Cleo reviews Python/SQL/PyTorch only. Next.js/TypeScript frontend requires separate review (use `/bmad-code-review` or manual TS lint)
  - [ ] **Gate:** 0 CRITICAL violations remaining in Python code

- [ ] **7.4 Quinn (QA)** — Testing _(Model: Sonnet 4.6 · Thinking: medium)_
  - [ ] Coverage >= 75%
  - [ ] E2E flow: signup → billing → Studio session → result
  - [ ] Workspace isolation verified

- [ ] **7.5 Alignment Review** _(Model: Opus 4.6 [1M] · Thinking: high)_
  - [ ] Shell correctly consumes Studio + MAC
  - [ ] Billing reconciled against Pi-Mono
  - [ ] Public dashboard shows real data

- [ ] **7.6 Pre-Sales Checkpoint (LAUNCH)** _(Model: Opus 4.6 · Thinking: high)_
  - [ ] Signup to first result < 10 minutes (timed test)
  - [ ] "Built With Praxis" dashboard live
  - [ ] Launch announcement drafted
  - [ ] First POV customer identified and contacted

**Gate to LAUNCH:** All 7 stages complete. Pipeline.md fully checked. Ready to sell.

---

## SECTION 4: AGENT INVOCATION CHAIN (QUICK REFERENCE)

Per-stage agent sequence varies. Some stages require ELICITATION rounds before Winston can design meaningfully — see Section 4.5 for details.

### Standard 6-Step Pattern (Stages 1 only — pure technical)

```
Step 1: /bmad-agent-architect     (Winston — design)
Step 2: /bmad-tea                 (Murat — test strategy)
Step 3: /bmad-agent-dev           (Amelia — implementation)
Step 4: /bmad-qa-generate-e2e-tests  OR  /bmad-testarch-automate   (Quinn — test execution)
Step 5: /bmad-review-adversarial-general  (alignment review)
Step 6: Manual checkpoint (pre-sales metric capture)
```

### Extended Pattern with Elicitation + Clean Code Review (Stages 2-7)

```
Step E1:  Elicitation Round 1      (domain-specific BMAD skill, before OR after Winston)
Step E2:  Elicitation Round 2      (if stage requires it)
Step E3:  Elicitation Round 3      (Stages 5 and 6 only)
---- (Output: requirements doc at <stage>/requirements.md) ----
Step 1:   /bmad-agent-architect          (Winston — design, now grounded in elicitation output)
Step 2:   /bmad-tea                      (Murat — test strategy)
Step 3:   /bmad-agent-dev                (Amelia — implementation)
Step 3.5: /bmad-agent-clean-code-reviewer (Cleo — clean code review, CRITICAL gate)
Step 4:   Quinn — test execution
Step 5:   Alignment review
Step 6:   Pre-sales checkpoint
```

**Clean code review (Step 3.5) is a hard gate:** Quinn does NOT run tests on code with unresolved CRITICAL violations. Cleo either auto-fixes or the issues return to Amelia before Quinn starts. This prevents "tests pass on bad code" — a class of silent failures where technically working code has architectural smells that break later.

**Rule:** Always complete Step N before starting Step N+1 within a stage. Always complete all steps of Stage N before starting Stage N+1. Elicitation steps are NOT optional — skipping them leads to product-market fit failures that don't surface until launch.

---

## SECTION 4.5: ELICITATION FRAMEWORK PER STAGE

Elicitation transforms UNCERTAIN product/business questions into CERTAIN requirements that Winston can design against. Without it, Winston must invent answers to questions only the market can answer.

### Elicitation Need Matrix

| Stage | Need | Rounds | Position | Why |
|-------|------|--------|----------|-----|
| 1 — Pi-Mono | LOW | 0 | — | Technical requirements are clear |
| 2 — Compression | MODERATE | 1 | AFTER Winston | Validate quality/compression tradeoff philosophy |
| 3 — Memory | HIGH | 2 | BEFORE Winston | Privacy, retention, governance are product decisions |
| 4 — Runtime | HIGH | 1 | BEFORE Winston | Tool library curation needs customer use case input |
| 5 — MAC | **CRITICAL** | 3 | BEFORE Winston | Quality rubric IS the entire business case |
| 6 — Studio | HIGH | 3 | BEFORE Winston | Customer language & output format decide PMF |
| 7 — POV Harness | HIGH | 2 | BEFORE Winston | Pricing, messaging, onboarding are business decisions |

### Stage 2 — Compression (1 round, AFTER Winston)
- **Round:** `/bmad-advanced-elicitation`
- **Focus:** Quality tolerance threshold for compression fall-back
- **Input to the round:** Winston's draft compression architecture
- **Questions:** At what quality loss % do we fall back to uncompressed? How do we measure quality loss? What's the consequence hierarchy (cost vs quality vs latency)?
- **Output:** `_bmad-output/implementation-artifacts/praxis/compression/requirements-validation.md`

### Stage 3 — Memory (2 rounds, BEFORE Winston)
- **Round 1:** `/bmad-advanced-elicitation`
  - Focus: Multi-tenant privacy model
  - Questions: SMB single-tenant? Enterprise strict isolation? Cross-customer learning opt-in? GDPR posture? Data residency?
- **Round 2:** `/bmad-cis-problem-solving` (Dr. Quinn)
  - Focus: Adversarial analysis of retention/governance risks
  - Questions: What happens on customer deletion? Right-to-erasure? Experience library poisoning risk? Multi-tenant leakage attack surface?
- **Output:** `_bmad-output/implementation-artifacts/praxis/memory/requirements.md`

### Stage 4 — Runtime (1 round, BEFORE Winston)
- **Round:** `/bmad-brainstorming` (Carson)
- **Focus:** Tool library curation via customer use case brainstorming
- **Questions:** What external systems do strategic advisory customers already use? Which 20% of integrations create 80% of value? What are "table stakes" tools vs "nice to have"?
- **Output:** `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md`

### Stage 5 — MAC (3 rounds, BEFORE Winston) — **CRITICAL**

This is the highest-stakes elicitation in the entire pipeline. The quality rubric defined here becomes the measurement Praxis is built to satisfy. Skipping this means building something technically perfect that fails PMF.

- **Round 1:** `/bmad-brainstorming` (Carson)
  - Focus: Define "strategic analysis quality" via creative brainstorming
  - Questions: What makes analysis GREAT vs mediocre? Comprehensiveness? Dissent preservation? Risk identification? Actionability? Honesty about uncertainty?
  - Output: Draft quality dimensions
- **Round 2:** `/bmad-cis-problem-solving` (Dr. Quinn)
  - Focus: Red team the draft quality rubric
  - Questions: Where do false positives hide (accept bad output)? Where do false negatives hide (reject good output)? What's the failure mode of each proposed gate?
  - Output: Hardened quality dimensions
- **Round 3:** `/bmad-advanced-elicitation`
  - Focus: Finalize benchmark questions + scoring protocol
  - Questions: Which 10 benchmark strategic questions will validate MAC quality? Who scores them? Blind vs open evaluation?
  - Output: `_bmad-output/implementation-artifacts/praxis/mac/quality-rubric.md` + `benchmark-questions.md`

### Stage 6 — Studio (3 rounds, BEFORE Winston)
- **Round 1:** `/bmad-market-research` (Mary)
  - Focus: Customer language discovery for strategic advisory
  - Questions: How do real customers phrase strategic questions? Industry jargon? Budget context? Who is the buyer?
  - Output: Draft customer persona + language patterns
- **Round 2:** `/bmad-cis-design-thinking` (Maya)
  - Focus: Empathy mapping — what customers actually want
  - Questions: Emotional state when asking? Outcome they need to defend to stakeholders? Format they share internally?
  - Output: Empathy map + journey map
- **Round 3:** `/bmad-advanced-elicitation`
  - Focus: Finalize Studio output format contracts
  - Questions: Brief length? Deck format? Dissenting views prominence? Export formats? Shareable links?
  - Output: `_bmad-output/implementation-artifacts/praxis/studio/customer-requirements.md`

### Stage 7 — POV Harness (2 rounds, BEFORE Winston)
- **Round 1:** `/bmad-cis-innovation-strategy` (Victor)
  - Focus: Pricing model + business model validation
  - Questions: Per-session vs subscription vs credit packs? Trial policy? Enterprise upgrade path? Price points? Free tier dynamics?
  - Output: Pricing strategy doc
- **Round 2:** `/bmad-cis-storytelling` (Sophia)
  - Focus: Launch messaging + onboarding narrative
  - Questions: Opening pitch? "Built With Praxis" story? Onboarding copy? First-session walkthrough? Error messages?
  - Output: `_bmad-output/implementation-artifacts/praxis/shell/messaging-and-onboarding.md`

### Quick Reference: Specific Methods Per Round

Instead of picking arbitrary methods from the skill's menu, use these exact selections:

| Stage | Round | Skill | Primary Method | Why This One |
|-------|-------|-------|----------------|--------------|
| 3 | 1 | `/bmad-advanced-elicitation` | **Stakeholder Round Table** | Multi-persona debate for privacy model |
| 3 | 2 | `/bmad-cis-problem-solving` | **Failure Mode Analysis** + **Risk Matrix** | Adversarial analysis of governance failures |
| 4 | 1 | `/bmad-brainstorming` | **Role Playing** + **Six Thinking Hats** | Tool curation from customer personas |
| **5** | **1** | `/bmad-brainstorming` | **First Principles Thinking** + **Values Archaeology** + **Reverse Brainstorming** | Defining quality from fundamentals |
| **5** | **2** | `/bmad-cis-problem-solving` | **Failure Mode Analysis** + **Assumption Busting** + **TRIZ Contradictions** | Red-teaming the rubric |
| **5** | **3** | `/bmad-advanced-elicitation` | **Comparative Analysis Matrix** + **ADRs** + **Thesis Defense Sim** | Selecting benchmark questions |
| 6 | 1 | `/bmad-market-research` | **Voice of Customer protocol** | Verbatim language discovery |
| 6 | 2 | `/bmad-cis-design-thinking` | **Empathy Mapping** + **JTBD** + **Journey Mapping** + **How Might We** | Customer emotional/functional needs |
| 6 | 3 | `/bmad-advanced-elicitation` | **ADRs** + **User Persona Focus Group** + **Critique and Refine** | Format contract finalization |
| 7 | 1 | `/bmad-cis-innovation-strategy` | **Value Proposition Canvas** + **Revenue Model Innovation** + **BMC** + **Lean Startup** | Pricing + business model validation |
| 7 | 2 | `/bmad-cis-storytelling` | **Origin Story** + **Positioning Story** + **Customer Journey** + **Pitch Narrative** | Launch messaging arsenal |

**Why specific methods (not generic skill invocation):** Each BMAD elicitation skill contains 20-60 methods. Without explicit selection, agents pick "whatever feels right" — which produces shallow generic output. The specific methods above are chosen for fit with that stage's actual decision type.

### Elicitation Output Rules

1. **Every elicitation round produces a document.** No verbal-only sessions.
2. **Winston reads elicitation outputs BEFORE designing.** He references them in the architecture doc.
3. **Elicitation outputs are binding during the stage.** If Winston disagrees, he raises it back — does NOT silently override.
4. **Elicitation docs live alongside architecture docs** in `_bmad-output/implementation-artifacts/praxis/<component>/`.
5. **Multi-round elicitation builds on itself.** Round 2 starts by reading Round 1 output; Round 3 reads both.
6. **Elicitation outputs feed Pipeline.md Session Log.** Add a brief summary of key decisions made.

---

## SECTION 4.6: MODEL & THINKING EFFORT STRATEGY

Every step from Stage 2.3 onwards has an assigned model and thinking level. This is an annotation, not a hard override — you can escalate or downgrade if the situation demands it, but defaults are tuned for cost/quality balance.

### Model Cheat Sheet

| Model | Cost (per 1M tokens in/out) | Thinking available | When to use |
|-------|----------------------------|-------------------|-------------|
| **Opus 4.6** | $5 / $25 | Yes (adaptive, no premium) | Architecture, strategy, red team, alignment, complex reasoning, high-risk components |
| **Sonnet 4.6** | $3 / $15 | Yes (adaptive, no premium) | Implementation, standard test design, code review, documentation, routine execution |
| **Haiku 4.5** | $1 / $5 | None | Simple lookups, classification, format conversions (rarely used in Praxis build) |

### Thinking Level Cheat Sheet

| Level | Token budget | When to use |
|-------|-------------|-------------|
| **minimal** | 128 | Simple lookups |
| **low** | 256 | Single-step problems |
| **medium** | 1024 | Multi-step chains, code review, standard test writing |
| **high** | 4096 | Complex reasoning, architecture design, implementation of non-trivial components |
| **max** | 8192+ | Open-ended research, adversarial red team, multi-stakeholder decision capture, highest-risk components (Stage 5 MAC) |

### Role → Default Allocation

| Role | Default Model | Default Thinking | Rationale |
|------|--------------|------------------|-----------|
| Winston (Architect) | Opus 4.6 | high → max (Stage 5) | Architecture is the most costly decision to get wrong |
| Murat (Test Architect) | Opus 4.6 (→ Sonnet for later stages) | high → max (Stage 5) | Risk-based strategy demands deep reasoning; Sonnet OK when risks are well-understood |
| Amelia (Developer) | Sonnet 4.6 (→ Opus for Stage 5) | high | Implementation is multi-step but pattern-following; MAC complex enough to justify Opus |
| Cleo (Clean Code Reviewer) | Sonnet 4.6 | medium | Pattern-matching against standards; deep reasoning not needed except for Stage 5 |
| Quinn (QA Engineer) | Sonnet 4.6 (→ Opus for Stage 5) | medium → high | Test writing is pattern-heavy; MAC tests demand Opus |
| Alignment Review | Opus 4.6 | high → max (Stage 5) | Cross-document consistency analysis is always complex |
| Pre-Sales Checkpoint | Sonnet 4.6 | low → medium | Mostly metric capture + narrative; Opus for launch checkpoint |
| Elicitation rounds | Opus 4.6 | high → max (Stage 5) | Product decisions with long-lasting consequences |

### Stage-Level Intensity Profile

| Stage | Intensity | Rationale |
|-------|-----------|-----------|
| 2 Compression | MEDIUM | Well-understood domain, code porting |
| 3 Memory | HIGH | Privacy/governance stakes |
| 4 Runtime | HIGH | Security model + 16 agents |
| **5 MAC** | **MAX** | **Core differentiation; every step at highest level** |
| 6 Studio | HIGH | PMF decisions |
| 7 POV Harness | HIGH | Customer-facing trust stakes |

### Override Guidance

- **Escalate** (e.g., Sonnet→Opus, medium→high): when a task surprises you with complexity, or when the first attempt produces shallow output
- **Downgrade** (e.g., Opus→Sonnet, high→medium): when a task turns out to be pattern-matching that the LLM handles easily; saves cost
- **Log overrides** in the Session Log (Section 9) so future sessions understand why you deviated

### 1M Context Window Strategy — CRITICAL

**Problem:** Claude's default context is 200k tokens, with compaction triggering around 128k. After compaction, output quality degrades. Steps that require reading:
- Multiple large reference .txt dumps (3-12 MB each = 750k-3M tokens)
- Multiple prior stage architecture docs + test strategies + requirements
- Plus full source directories for review

...will hit 200k quickly and lose fidelity.

**Solution:** Explicitly invoke Claude with 1M context window for the affected steps.

**Model variants to use:**
- **Sonnet 4.6 [1M]** — Sonnet 4.6 with 1M context window enabled
- **Opus 4.6 [1M]** — Opus 4.6 with 1M context window enabled
- Default (no [1M] tag) — 200k context window (cheaper on rate limits)

**When to use [1M]:**
- ✅ Amelia implementing against multiple large reference dumps (Stages 2, 3, 4, 5, 7)
- ✅ Winston designing against multiple reference dumps + prior stage docs (Stages 3, 4, 5, 6, 7)
- ✅ Murat reading Winston arch + reference dumps (Stages 3, 4, 5)
- ✅ Cleo reviewing large source trees (Stages 2, 3, 4, 5, 7)
- ✅ Alignment Review reading ALL prior architecture docs (Stages 2-7)
- ✅ Quinn running adversarial tests on MAC (Stage 5 only)

**When NOT to use [1M]:**
- ❌ Elicitation rounds (focused discussion, rarely exceed 50k context)
- ❌ Pre-sales checkpoints (metric capture, minimal context)
- ❌ Quinn QA in Stages 2-4, 6, 7 (test execution, fits in 200k)
- ❌ Stage 6 Studio implementation (mostly YAML + Jinja2, small footprint)

**Rate limit impact (Max $100 plan — Max 5x, ~225 messages per 5hr window):**
- 1M context messages count ~5x against the ITPM/OTPM budget
- Expect to burn through hourly quota faster when using [1M] variants
- Plan sessions accordingly — don't stack multiple 1M context operations back-to-back
- If you hit rate limits, downgrade non-critical steps to standard context or wait for window reset

### UNIVERSAL RULE: Sequential Reference Reading

**Applies to:** ANY step where multiple large reference .txt dumps or prior stage architecture docs must be consulted.

**The rule:** **Read ONE reference at a time. Process it fully. Clear context. Read the next.** Do NOT attempt to load all references simultaneously — even with 1M context, the raw reference material often exceeds the window, and cramming multiple dumps degrades attention quality on each one.

**Why it matters:** Even 1M context is not enough for:
- Stage 2 references: TONL 3MB + Forge 4.8MB + RTK 1.9MB + Caveman 210KB ≈ **2.5M tokens**
- Stage 3 references: Beads + Mem0 **7.8MB** + Atelier 3.3MB ≈ **3M tokens**
- Stage 4 references: Gas Town **12MB** + Atomic Agents 1.7MB + Atelier 3.3MB ≈ **4.5M tokens**
- Stage 5 integration: ALL prior stage architectures + Atelier + Forge patterns ≈ **3M+ tokens**

**How to apply it (Amelia / developer pattern):**
1. Read Winston's architecture doc first (small, defines scope)
2. Pick the FIRST reference you need per architecture
3. Read it fully, extract relevant patterns as notes
4. Implement ONE component
5. Run the component's tests
6. Commit (or mark complete in checklist)
7. Start fresh: read the SECOND reference
8. Repeat

**How to apply it (Winston / architect pattern):**
1. Read the previous stage's architecture doc first (small, defines integration points)
2. Read the highest-priority reference dump
3. Draft the architecture section that uses it
4. Clear context, read the next reference
5. Draft the next architecture section
6. Final pass: integration sections that tie everything together

**How to apply it (Alignment Reviewer pattern):**
1. Read one prior stage's architecture at a time
2. Take notes on invariants: data models, API surfaces, language choices
3. Only after reading all prior architectures, read the CURRENT stage's architecture
4. Compare against accumulated notes, flag inconsistencies

**Steps where this rule is MANDATORY (explicit reminder in checklist):**
- Stage 2: 2.3 Amelia
- Stage 3: 3.1 Winston, 3.3 Amelia
- Stage 4: 4.1 Winston, 4.3 Amelia
- Stage 5: 5.1 Winston, 5.2 Murat, 5.3 Amelia, 5.5 Alignment (reads ALL prior stages)
- Stage 6: 6.1 Winston (reads elicitation + Tokonomics rounds + Stage 5 MAC)
- Stage 7: 7.1 Winston, 7.3 Amelia

---

## SECTION 5: GATE CONDITIONS (INTERNAL CHECKS)

### Before starting ANY stage, verify:

1. **Previous stage status:**
   - [ ] Previous stage's Winston (architect) output exists at the expected `implementation-artifacts/praxis/<component>/architecture.md`
   - [ ] Previous stage's Murat (test strategy) output exists at `.../test-strategy.md`
   - [ ] Previous stage's Amelia (implementation) output exists in `.../src/`
   - [ ] All Pipeline.md checkboxes for previous stage are `[x]`

2. **Billing mode:**
   - [ ] User confirmed `ANTHROPIC_API_KEY` is unset (CLI/Max billing)
   - [ ] User has Max subscription active

3. **Environment:**
   - [ ] Current working directory is `C:\Users\AndreyPopov\Documents\Anthropic`
   - [ ] `.claude/settings.local.json` has `acceptEdits` mode
   - [ ] Agent Teams env var set (if needed for stage)

4. **Reference materials:**
   - [ ] Relevant .txt dump files exist in `_bmad-output/planning-artifacts/src/`
   - [ ] Relevant prior stage architecture docs exist

### If ANY gate fails:
- STOP immediately
- Report which gate failed
- Do NOT attempt workarounds
- Wait for user to resolve

---

## SECTION 6: FILE PATH REGISTRY (EVERYTHING IN ONE PLACE)

### Project Root
```
C:\Users\AndreyPopov\Documents\Anthropic\
```

### Critical Files at Root
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions + directory trees (auto-loaded by Claude Code) |
| `claude-setup-reference.md` | Subscription/billing/coordination reference |
| `.claude/settings.local.json` | Permission mode, agent teams, allow/deny lists |

### BMAD Framework
| Path | Purpose |
|------|---------|
| `_bmad/_config/agent-manifest.csv` | 16 BMAD agent definitions (source of truth) |
| `_bmad/core/config.yaml` | user_name, language, output_folder |
| `_bmad/bmm/` | Business/Market/Methodology agents (Mary, Winston, Amelia, etc.) |
| `_bmad/cis/` | Creative Innovation Studio (Carson, Dr. Quinn, Maya, Victor, Sophia, Caravaggio) |
| `_bmad/tea/` | Test Architecture (Murat) |

### Planning Artifacts
| Path | Purpose |
|------|---------|
| `_bmad-output/planning-artifacts/Praxis/` | Praxis project planning docs |
| `_bmad-output/planning-artifacts/src/` | Reference repo .txt dumps + framework analysis |
| `_bmad-output/planning-artifacts/Tokonomics/` | Previous analysis (5 round tables) |

### Praxis Planning Docs
| File | Purpose |
|------|---------|
| `_bmad-output/planning-artifacts/Praxis/Pipeline.md` | THIS FILE — master orchestration |
| `_bmad-output/planning-artifacts/Praxis/praxis-build-plan.md` | Full 7-stage build plan |
| `_bmad-output/planning-artifacts/Praxis/box-core-architecture.md` | 5-layer technical architecture |
| `_bmad-output/planning-artifacts/Praxis/hybrid-architecture-recommendations.md` | 8-layer best-of-breed analysis |
| `_bmad-output/planning-artifacts/Praxis/stage-1-winston-prompt.md` | Stage 1 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-2-winston-prompt.md` | Stage 2 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-3-winston-prompt.md` | Stage 3 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-4-winston-prompt.md` | Stage 4 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-4-deferred-findings-brief.md` | **Stage 4.1 pre-flight** — F-1 + F-3 architectural inputs Winston must absorb (added 2026-04-13 per Section 4.7) |
| `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md` | **Stage 4.1 pre-flight** — 4.0.1 Carson output, tool library catalog Winston anchors §6 on (added 2026-04-13) |
| `_bmad-output/planning-artifacts/Praxis/stage-5-winston-prompt.md` | Stage 5 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-6-winston-prompt.md` | Stage 6 launch prompt |
| `_bmad-output/planning-artifacts/Praxis/stage-7-winston-prompt.md` | Stage 7 launch prompt |

### Reference Repos (`_bmad-output/planning-artifacts/src/`)
| File | Project | Used In Stage |
|------|---------|---------------|
| `badlogic-pi-mono-8a5edab282632443.txt` | Pi-Mono (cost tracker) | Stage 1 |
| `tonl-dev-tonl-8a5edab282632443.txt` | TONL (serialization) | Stage 2 |
| `antinomyhq-forgecode-8a5edab282632443.txt` | Forge (compaction) | Stage 2, 5 |
| `rtk-ai-rtk-8a5edab282632443.txt` | RTK (CLI compression) | Stage 2 |
| `juliusbrussee-caveman-8a5edab282632443.txt` | Caveman (output compression) | Stage 2 |
| `gastownhall-beads-8a5edab282632443.txt` | Beads (versioned state) | Stage 3 |
| `mem0ai-mem0-8a5edab282632443.txt` | Mem0 (hybrid memory) | Stage 3 |
| `robertsfeir-atelier-pipeline-8a5edab282632443.txt` | Atelier (quality gates) | Stages 3, 4, 5 |
| `brainblend-ai-atomic-agents-8a5edab282632443.txt` | Atomic Agents (schemas) | Stage 4 |
| `gastownhall-gastown-8a5edab282632443.txt` | Gas Town (multi-agent) | Stage 4 |
| `badlogic-cchistory-8a5edab282632443.txt` | CCHistory (instruction extraction) | Reference only |

### Reference Analysis Docs (`_bmad-output/planning-artifacts/src/`)
| File | Purpose |
|------|---------|
| `agentic-ai-framework.md` | 8 functional areas framework (Claude Code baseline) |
| `bmad-business-process-mapping.md` | 13 business processes mapped to BMAD agents |
| `project-analysis-classification.md` | Project classification taxonomy |

### Previous Analysis (`_bmad-output/planning-artifacts/Tokonomics/`)
| File | Purpose |
|------|---------|
| `1st_Round_table.md` | Initial strategy (7 agents + 10 research) |
| `2nd_Round_table.md` | Deep strategy sessions (8 agents, 25+ frameworks) |
| `3rd_Round_table.md` | Competitive landscape validation |
| `4th_Round_table.md` | Red team analysis (CRITICAL context) |
| `business_session.md` | GTM, resources, design, brand, pitch |

### Implementation Outputs (CREATE AS NEEDED)
All implementation work goes here:
```
_bmad-output/implementation-artifacts/praxis/
├── pi-mono/            # Stage 1
│   ├── architecture.md       (Winston output)
│   ├── test-strategy.md      (Murat output)
│   └── src/                  (Amelia output)
├── compression/        # Stage 2
│   ├── architecture.md
│   ├── test-strategy.md
│   └── src/
├── memory/             # Stage 3
│   ├── architecture.md
│   ├── test-strategy.md
│   └── src/
├── runtime/            # Stage 4
├── mac/                # Stage 5
├── studio/             # Stage 6
└── shell/              # Stage 7
```

### Test Outputs
```
_bmad-output/test-artifacts/praxis/
├── pi-mono/            # Test execution results per stage
├── compression/
├── memory/
├── runtime/
├── mac/
├── studio/
└── shell/
```

---

## SECTION 7: CONTEXT WINDOW HANDOFF PROTOCOL

When your Claude session approaches 180k tokens (out of 200k), prepare for handoff to a fresh session.

### Handoff Procedure (at 180k context)

1. **Save current state to Pipeline.md:**
   - Update Status Tracker with latest checkboxes
   - Add a note in the "Session Log" section (below) with timestamp and summary
   - Write Pipeline.md back to disk

2. **Create a handoff summary file:**
   - Path: `_bmad-output/planning-artifacts/Praxis/session-handoff-<timestamp>.md`
   - Content:
     - What was worked on in this session
     - What's the NEXT immediate action
     - Any blockers or open questions
     - Any temporary state that isn't in a permanent file yet

3. **Tell the user:**
   > "Context approaching limit. I've updated Pipeline.md and created session-handoff-<timestamp>.md. To continue in a fresh session:
   > 1. Start new Claude Code session (`claude`)
   > 2. Attach `Pipeline.md` + `session-handoff-<timestamp>.md` + the current stage prompt file
   > 3. I'll resume from where we left off."

### Fresh Session Resume Procedure

When starting a new session with attached Pipeline.md:

1. Read Pipeline.md (Section 1: Bootstrap)
2. Read the attached session-handoff file (if any)
3. Read the attached stage prompt file
4. Verify gate conditions for the current stage
5. Report to user: "Resuming at Stage N, Step X.Y. Previous step was [summary]. Next action: [next step]."
6. Wait for user confirmation before proceeding

---

## SECTION 8: ALIGNMENT REVIEW PROTOCOL

After each stage completes (before starting the next), run this alignment check:

### Alignment Check Prompt Template

Use this in a FRESH Claude subagent (not the main session) to get an independent review:

```
Perform an alignment review for Praxis Stage N.

Read these architecture docs in order:
- _bmad-output/implementation-artifacts/praxis/pi-mono/architecture.md (S1)
- _bmad-output/implementation-artifacts/praxis/compression/architecture.md (S2, if exists)
- _bmad-output/implementation-artifacts/praxis/memory/architecture.md (S3, if exists)
- _bmad-output/implementation-artifacts/praxis/runtime/architecture.md (S4, if exists)
- _bmad-output/implementation-artifacts/praxis/mac/architecture.md (S5, if exists)
- _bmad-output/implementation-artifacts/praxis/studio/architecture.md (S6, if exists)
- _bmad-output/implementation-artifacts/praxis/shell/architecture.md (S7, if exists)

Identify inconsistencies across these documents:
1. Data model mismatches (e.g., Stage N uses CostRecord with field X, but Stage N-1 defines it without X)
2. API contract mismatches (e.g., Stage N calls `get_cost()` but Stage N-1 defines `fetch_cost()`)
3. Language/tooling drift (e.g., Stage 2 uses Pydantic v1, Stage 3 uses v2)
4. Dependency version mismatches
5. Error handling pattern inconsistencies
6. Naming convention inconsistencies

Output format:
- Alignment Report with specific file:line_number references
- Severity per issue: CRITICAL / HIGH / MEDIUM / LOW
- Proposed reconciliation for each issue

Do NOT write implementation. Review only.
```

### When Alignment Fails

If alignment review finds CRITICAL or HIGH issues:
1. STOP — do not advance to next stage
2. Return to Winston for the stage that caused the drift
3. Update that stage's architecture to reconcile
4. Re-run affected downstream checks
5. Re-run alignment review until clean

---

## SECTION 9: SESSION LOG (APPEND AS WORK PROGRESSES)

Add entries here as sessions complete. Include timestamp, what was done, and any open items.

### 2026-04-13 — Stage 4.1 Winston COMPLETE — architecture.md v0.3+ ratified (v1.10)

**Gate to Stage 4.2: OPEN.** All §4.1 Winston + pre-flight checkboxes flipped to [x]. §4.2 Murat marked [~] in-progress (preload-first gating brief fired, 6 structured return items, three preload documents, hard rules for no-drafting-during-preload).

- **Architecture doc:** `_bmad-output/implementation-artifacts/praxis/runtime/architecture.md` v0.3+ — binding input for Stage 4.2 Murat test-strategy.md. Downstream steps (Cleo 4.3.5, Amelia 4.3, Quinn 4.4) consume this version as their architectural source of truth.
- **F-1 / F-3 absorption:** Both deferred Stage 3 findings dissolved via the Path A / Path B split plus the Jobs Infrastructure layer. F-1 (Memory → Pi-Mono CostEvent wiring) resolved through the Orchestrator outbox adapter contract. F-3 (durable jobs table) resolved via the §4 Jobs Infrastructure specification (schema + state transitions + worker lifecycle + NFR-Q6 crash recovery). F-2 remains parked in §12 Open Questions for Stage 6 reassess.
- **Only remaining Stage 4.6 blocker: OQ-N (AuditBuffer drain coordination).** This is the sole architectural open question that must close before the Stage 4.6 pre-sales checkpoint can claim gate closure. Tracked on Winston's §12 Open Questions; expect revisit during 4.5 Alignment Review.
- **Preload-first gating pattern validated twice in one session:** Carson (4.0.1) → Winston (4.1) both returned clean 6-item structured briefs with zero mid-draft scope drift. Pattern is: load context first → agent returns structured preload report → human verifies alignment → explicit "go" → drafting begins. Reuse for every BMAD agent invocation Stage 4+ (Murat next, then Cleo, then Amelia, then Quinn). The friction is the point.
- **Handoff to Stage 4.2:** `/bmad-tea` (Murat) with preload brief. Three preload documents: (1) runtime/architecture.md v0.3+, (2) runtime/tool-library-requirements.md (4.0.1 output), (3) stage-4-deferred-findings-brief.md. Hard rule: no drafting of test-strategy.md until Murat returns the 6-item preload report and receives explicit go. Checkpoint cadence mirrors Winston's Stage 4.1 session.

### 2026-04-13 — Stage 3 COMPLETE — Steps 3.4 + 3.5 + 3.6 landed in one session

**Gate to Stage 4: OPEN.** All 58 sub-checkboxes in Stage 3 checked; 4 tracked items (F-1..F-4) carried forward to Stage 4 pre-flight, none blocking Winston architecture start.

- **Step 3.4 Quinn QA** — `/bmad-testarch-automate` surface; Sonnet 4.6 · medium thinking.
  - Ran full test suite against `memory/` with pytest-cov: **264/264 passing, 98% aggregate coverage** (855 statements, 19 missed across 23 files). Every uncovered line is a defensive fallback (Pydantic-guarded) or a Stage 4+ wiring hook. No core path uncovered.
  - Verified 6 CRITICAL privacy/scoping battery (R-01 pgvector orphans, R-02 cache invalidation, R-03 audit log PII, R-04 quarantine embedding strip, R-05 telemetry query leak, R-06 two-tenant export isolation) — **42/42 passing, 0 waivers**.
  - Verified retrieval correctness — **69/69 passing** (atelier decision retrieval + mem0 fact retrieval + facade routing + 12 Atelier §5.3 scoring property tests via Hypothesis + 84 protocol conformance × 4 backends).
  - Closed Step 3.3 deferral ("live-backend integration deferred to Quinn Step 3.4" per Pipeline.md:282) by adding `tests/memory/mem0_adapter/test_mem0_live_protocol_contract.py` — **11 new tests** that import the real `mem0.Memory` class (not the fake) and verify it structurally satisfies `Mem0ClientProtocol`: method presence (6 parametrized), scoping kwargs preserved on `add`/`search`/`get_all`/`delete_all` (4), runtime-checkable sanity (1). Deliberately does NOT instantiate `mem0.Memory()` (requires qdrant + OpenAI keys + embedder stack — Stage 7 concern; also would violate CLI-mode billing posture). Catches Mem0 version drift at CI time.
  - Deliverable: `memory/automation-summary.md` (full gate breakdown, uncovered-line rationale, risk mitigation map, handoff notes).

- **Step 3.5 Alignment Review** — Independent adversarial pass; Opus 4.6 [1M] · high thinking.
  - **F-1 (HIGH, deferred to Stage 4): Pi-Mono CostEvent emission is documented but unwired.** Architecture §3.5 promises "bead write + CostEvent in same DB transaction" via Stage 1's outbox pattern; §9.3 defines two emission categories (`retention_action`, `record_created`). Protocol.py:189 and :223 docstring postconditions reference CostEvent. Reality: 0 imports of `praxis.kernel.cost` from memory src. Accepted under Stage 2 precedent (Stage 2 F-2/F-3 had identical "documented-not-wired" pattern — both deferred to Stage 4 Orchestrator). `facade.py:143` `audit_buffer` property is the designed integration seam. **Must close before Stage 4 claims completion; does not block Stage 4 Winston start.**
  - **F-2 (MEDIUM, deferred): Compression TONL encoding of bead payloads unwired.** Architecture §3.4 says structured beads should be TONL-encoded via `praxis.kernel.compression.tonl.encode`. Reality: 0 compression imports. Cost optimization (smaller seed input on warm retrieval), NOT correctness. Deferred.
  - **F-3 (HIGH, deferred): Durable jobs table for retention reaper missing.** Current audit buffer is in-memory only. NFR-C-A1 (7-day crypto-shred SLA) and NFR-Q6 (5-min crash RTO) require a Postgres/SQLite jobs substrate. Stage 4 infrastructure.
  - **F-4 (LOW, auto-answered): Connection pool sizing only strawman-validated.** Naturally closed by Step 3.6 demo runtime.
  - **API drift: CLEAN.** `praxis.kernel.memory` namespace consistent with `praxis.kernel.cost` and `praxis.kernel.compression`. Python 3.11+, Pydantic, async facade, error hierarchy, config-as-type all match Stages 1-2. Stage 3's `_internal/` hiding convention (NR-S-R1 ruff TID251 + grep tripwire) is STRICTER than Stages 1-2 — recommend back-propagation to Stage 4+.
  - **6 CRITICAL risks MITIGATED with no waivers**, confirmed against Murat's test-strategy.md v1.1 traceability.
  - Deliverable: `memory/alignment-review.md` (9 sections, gate-by-gate audit, F-1..F-4 tracked items, Stage 4 integration contract).

- **Step 3.6 Pre-Sales Checkpoint** — Sonnet 4.6 · low thinking.
  - Built `scripts/pre_sales_demo.py` — end-to-end `Memory` harness that stores a strategic-advisory task outcome (Q1-2026 pricing repositioning, 3-agent workflow Mary+Winston+John, detailed 3-step reasoning trace + approach summary) then calls `retrieve_similar_tasks` with a Q2-2026 signature on the same ICP segment.
  - **Retrieval works end-to-end:** 1 hit returned in 0.55 ms. This is a real measurement on the composed facade with BeadsStore + AtelierStore + FakeMem0Client. Atelier's keyword-synthesized query path reaches across quarters when context_fingerprint shares segment terms.
  - **Cost measurement:** Claude Sonnet 4.6 public pricing ($3/M input, $15/M output).
    - Cold path: 210 output tokens generated from scratch → **$0.003150**.
    - Warm path: 225 seed input tokens (retrieved record as context) + 42 delta output tokens (Q2 adaptation, 20% of original) → **$0.001305**.
    - **Savings: 58.6% cost reduction** (beats 30-50% Pipeline target).
  - **Critical insight for the pre-sales story:** raw-token count shows the warm path as -27% (225 + 42 = 267 tokens vs 210 cold), which is misleading. The real economic question is dollars, and on Sonnet 4.6 input is 5× cheaper than output. Memory turns expensive output generation into cheap input reading; the savings ratio is a structural property of Claude's pricing, not a promise about retrieval quality. Documented in checkpoint §3 and blog draft §9.
  - **Multi-tenant scoping holds under the demo:** savings claim is per-tenant; a different tenant issuing the same Q2 query would NOT match task 1's record (guaranteed by the 42 privacy tests Quinn verified).
  - Deliverables: `memory/pre-sales-checkpoint.md`, `memory/pre_sales_demo_result.json`, `memory/scripts/pre_sales_demo.py`.

- **Tracked items carried to Stage 4 pre-flight (not blocking Winston start):**
  - **F-1 Pi-Mono CostEvent wiring** (MUST-CLOSE before Stage 4 completion) — Stage 4 Orchestrator drains `memory.audit_buffer` into `CostTracker` on each tick.
  - **F-2 Compression TONL bead encoding** — optional Stage 4 enhancement or Stage 3 post-landing optimization; would further reduce seed input cost on warm retrieval.
  - **F-3 Durable jobs table** — Stage 4 Postgres/SQLite infrastructure prerequisite for NFR-C-A1 (7-day crypto-shred) and NFR-Q6 (5-min RTO) SLA claims.
  - **13 pre-3.4 Winston v1.1 amendments** still on parallel track (P0: crypto-shred structure, connection pool, full-tenant delete freeze; P1: p99 matrix, KMS degraded-mode, classifier CB, crash RTO; P2/P3: entry ceiling, manifest window, large-delete target, cache-ack timeout, manifest fault tolerance). Decoupled from Stage 3 gate closure per the original delegation.

- **Handoff to Stage 4:** Before Winston begins Stage 4 architecture, run **Elicitation Round 4.0.1** — `/bmad-brainstorming` (Carson) on tool library curation via customer use case brainstorming. Output to `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md`. This is a BEFORE-Winston elicitation per Section 4.5's Elicitation Need Matrix (Stage 4 = HIGH need, 1 round). Do not skip.

### 2026-04-12 — Stage 3.3 Phase 1 Complete (v1.8)
- Amelia Phase 1 (independent pre-conditions) complete
- **A3.3.1 Mem0 SCA scan:** CLEAN, 0 CVEs across 80 packages (`mem0ai==1.0.11` + 79 transitive)
  - Environment: fresh `uv` venv, Python 3.12.12, at `_bmad-output/implementation-artifacts/praxis/memory/.venv` (gitignored)
  - Tools: `pip-audit==2.10.0` (exit 0, "No known vulnerabilities found"), `safety==3.7.0` (exit 0, 80 packages scanned, 0 reported)
  - Deliverable: `memory/mem0-sca-scan.md` + `memory/requirements-mem0-lock.txt` (80-package pin)
  - Note: `safety check` deprecation (sunset 2024-06-01) — non-blocking, address in Stage 7 CI wiring by switching to `safety scan` or dropping `safety` in favor of `pip-audit` alone
- **A3.3.3 Ruff TID251 + grep tripwire:** CLEAN, 4/4 self-test PASS
  - Layer 1 (ruff TID251) configured in `memory/pyproject.toml` with banned-api `"praxis.kernel.memory._internal"` + per-file-ignores for the Memory module itself, white-box tests, and self-test fixtures
  - Layer 2 (grep tripwire) in `memory/scripts/check-no-internal-imports.sh` with matching path exemptions
  - Pre-commit wiring in `memory/.pre-commit-config.yaml`
  - Self-test harness `memory/scripts/self-test-banned-imports.sh`: copies banned/clean fixtures into non-exempt paths, runs both layers, asserts verdicts → **4/4 PASS** (banned rejected by ruff ✓, banned rejected by grep ✓, clean accepted by ruff ✓, clean accepted by grep ✓)
  - Full ruff sweep on committed tree: `All checks passed!`
  - Deliverable: `memory/nr-s-r1-banned-api-setup.md`
  - Scaffolding: `src/praxis/{__init__, kernel/__init__, kernel/memory/__init__, kernel/memory/_internal/__init__}.py` (placeholders — minimum required for the ban target module path to resolve)
- **A3.3.2 Connection pool sizing:** AUTHORIZED **Option (b)** — Amelia implements with NR-SC-R2 strawman values immediately (pool_size=10, max_overflow=15, pool_pre_ping=True, pool_recycle=3600); Winston's §4.2 amendment becomes documentation-only confirmation (parallel track). Rationale: values come from Murat's NFR analysis (engineering already done); refactor risk ≈ one-line change if Winston diverges; speed gain ≈ hours saved. Traceability comment mandated in the module header; exact-values constraint; no creative additions beyond NR-SC-R2 scope.
- **A3.3.4 first real Memory implementation:** HELD at hard gate, awaiting explicit "continue A3.3.4" from Andrey before first line of unified interface / schema / retrieval code.
- **Pipeline v1.8:** no structural changes, tracker + log updates only. Footer bumped 1.6 → 1.8 (no v1.7 existed — explicit rename per Andrey direction).
- **Engineering note — SQLAlchemy pool test pivot (reference for future backend tests):** `test_engine_uses_queuepool_with_nrscr2_sizing` initially used `sqlite:///file:...?uri=true` to build a real `QueuePool` and introspect it. SQLAlchemy overrides to `SingletonThreadPool` for ALL `sqlite://` URLs regardless of URL shape, and `SingletonThreadPool` rejects `max_overflow` with `TypeError: Invalid argument(s) 'max_overflow' sent to create_engine()`. The correct level of abstraction for NR-SC-R2 is "these four kwargs reach SQLAlchemy", not "the runtime pool is QueuePool" — the latter depends on dialect, the former is what Murat's NFR actually ratified. Rewrote the test to `unittest.mock.patch` on `sqlalchemy.create_engine` to spy on the positional URL + full kwarg set dialect-independently. **Generalization for A3.3.4+:** when testing backend adapters that wrap vendor libraries (SQLAlchemy, Mem0, Qdrant, etc.), prefer contract-level mocking over live-dialect introspection unless the test is explicitly an integration test against a named backend.

### 2026-04-12 — Step 3.2 Murat Complete with CONCERNS Gate → Stage 3.3 Amelia GO (pending pre-conditions)

- **Murat delivered TD Pass 1:** `_bmad-output/implementation-artifacts/praxis/memory/test-strategy.md` (~1250 lines). 225 test cases, 88 requirement-linked (1.52× coverage ratio), 6 CRITICAL no-waiver risks (R-01..R-06: pgvector orphans, cache invalidation, audit log PII, quarantine embedding strip, telemetry query leak, two-tenant export isolation). All 58 requirements mapped. All 43 Round 2 failure modes mapped (25 with dedicated tests, 7 eliminated by construction under B1/B5, 4 doc-only, 7 transitive coverage). ADR Quality Readiness Checklist assessed: 18/29 PASS = 62%. Test pyramid: ~140 unit + ~70 integration + ~15 E2E. Effort estimate 150–295 hours over 6–8 calendar weeks.
- **Murat delivered NR Pass 2 (bonus):** `_bmad-output/implementation-artifacts/praxis/memory/nfr-report.md` (~800 lines). 5 domains assessed (Security, Compliance, Performance, Reliability, Scalability). 30+ findings, **zero HARD-FAIL**. Defense-in-depth (3 independent enforcement layers) justifies CONCERNS gate instead of FAIL. 7 NR open questions (NR-Q1..Q7) addressed with strawman resolutions.
- **Gate decision:** **CONCERNS — advance with conditions.** Combined Pass 1 + Pass 2 justification: architecture is structurally sound on hardest category (Privacy/GDPR); all threshold gaps have concrete remediation paths; zero architectural rework required.
- **3 Andrey ratifications captured:**
  - **NR-P-R1 facade p99 latency matrix** — RATIFIED with hot-path guardrail: any user-facing hot-path operation (retrieve, search_similar, get_by_id, store_during_session) exceeding 200ms p99 must escalate back to Andrey before closing the matrix. Rationale: Praxis Studio session SLA <30 min end-to-end; memory ops should consume <10% cumulative at p99; 200ms+ retrieval can cascade across 3-cycle MAC iteration. Batch/async ops (compact, cascade_delete, bulk_quarantine, crypto_shred_initiation) exempt from hot-path rule — those can take seconds-to-minutes.
  - **NR-C-A1 crypto-shred SLA** — RATIFIED at **7 calendar days** with structured phases. Days 0–1 (48hr): soft-delete recovery window (customer can cancel, no new reads/writes on pending-delete tenant). Days 1–2: embedding purge from pgvector + in-memory cache drain (FM3.2). Days 2–5: backup manifest rewrite + shadow copy destruction. Days 5–7: KMS key destruction + audit log finalization. Day 7: DPA-compliant destruction certificate emailed to customer DPO. Competitive positioning: 4x faster than enterprise SaaS norm (30 days), 6x faster than CCPA (45 days). DPA language: *"Praxis guarantees complete cryptographic erasure of all customer data within seven (7) calendar days of delete confirmation, inclusive of a 48-hour recovery window followed by irreversible key destruction."*
  - **NR-Q6 crash recovery RTO** — RATIFIED at **5 min p95** (single-tenant-per-deployment makes this achievable).
  - **NR-Q2 per-tenant entry ceiling** — RATIFIED at **100K soft (operator alert) / 250K hard (reaper aggressively demotes oldest CONFIRMED to DEPRECATED)**.
- **Stage 3.3 advancement:** **GO** pending 3 ordered pre-3.3 tasks (Amelia's first work):
  - **Task A3.3.1 [BLOCKER]** — NR-S-A1 Mem0 SCA scan. Run `pip-audit` + `safety check` on Mem0 transitive dep chain. Output to `memory/mem0-sca-scan.md`. HALT on any CRITICAL/HIGH CVE. Do NOT proceed to A3.3.2 until clean.
  - **Task A3.3.2 [paired with Winston]** — NR-SC-R2 connection pool sizing. Winston adds §4.2 to arch.md v1.1: `pool_size=10, max_overflow=15, pool_pre_ping=True, pool_recycle=3600`. Amelia implements in `memory/db/engine.py`.
  - **Task A3.3.3 [tooling gate]** — NR-S-R1 ruff TID251 banned-api rule + pre-commit grep hook on `from praxis\.memory\._internal`. Test with intentional banned import.
- **Stage 3.3 gate to A3.3.4 (first real Memory layer implementation):** all three pre-tasks complete and green in CI.
- **Winston parallel track: arch.md v1.1 amendments (13 items) authorized.** Priority order: **P0** (crypto-shred structure per Decision 2, connection pool per NR-SC-R2, full-tenant delete freeze sequence) → **P1** (p99 matrix, KMS degraded-mode, classifier timeout+CB, crash recovery RTO) → **P2** (per-tenant entry ceiling, manifest 60s window, large-delete scalability) → **P3** (cache-invalidation ack timeout, manifest fetch fault tolerance). Handoff protocol: amendments are additive (no rewrites); Winston tags with `v1.1-<item-id>` markers; if an amendment changes an API contract Amelia has already implemented, Winston flags in session log and Amelia refactors in next commit.
- **Murat test-strategy.md v1.1 rolling updates authorized.** 14 new scenarios to be appended during Stage 3.3 implementation window (total 239). Markers: `v1.1-added-<YYYY-MM-DD>`. Quinn (Step 3.4) runs against live version, not snapshot. Blocker-severity scenarios flagged immediately, not at end-of-stage.
- **Handoff instruction for next Stage 3.3 window:** Start Amelia (`/bmad-agent-dev`) with this session context. Bind inputs: `memory/requirements.md` + `memory/architecture.md` (v1.0; v1.1 amendments pending in parallel) + `memory/test-strategy.md` + `memory/nfr-report.md`. Amelia's ordered task list is A3.3.1 → A3.3.2 → A3.3.3 → A3.3.4. Task A3.3.1 is a HALT-on-finding blocker. Do NOT skip.

### 2026-04-12 — Step 3.1 Winston Complete → Gate to 3.2 Murat Open
- Winston's memory architecture delivered: `_bmad-output/implementation-artifacts/praxis/memory/architecture.md` (105KB, Apr 12 19:48).
- **Coverage verified against Pipeline gate checklist:** §2 Unified Memory facade (Pydantic models + process-level scoping), §3 Beads integration (module structure, versioning, worktree semantics, Go→Python port plan, Pi-Mono outbox hook), §4 Mem0 integration (pinning, backend config, three-axis scoping translation, fact extraction, adapter), §5 Atelier decision memory (schema, capture protocol, 5-factor retrieval scoring, TTL decay, §5.5 post-read adoption summary), §6 Cross-session learning (signatures, thresholds, write-back, Req #42 promotion, Stage 5 MAC named contract), §7 Postgres schema + SQLite dev equivalent, §8 structural tenant isolation honoring managed single-tenant decision + FM3.10 embedding-strip override.
- **Context strategy honored:** Sequential reference reading confirmed via §1 Reference Analysis and §5.5 post-Atelier adoption delta — Winston documented which design elements were added AFTER reading each reference, proving references were studied one-at-a-time rather than speculated.
- **Gate to Step 3.2 Murat (Test Architect):** OPEN. Binding inputs for Murat: `memory/requirements.md` (58 reqs) + `memory/architecture.md`. Murat produces `memory/test-strategy.md` with privacy/scoping enforcement tests as the critical path.
- **Next action:** Launch `/bmad-tea` (Murat) for step 3.2 with architecture.md + requirements.md as binding inputs.

### 2026-04-12 — Stage 3 Blockers Resolved (Andrey Ratification) → Step 3.1 Winston Cleared
- Andrey ratified all 6 BLOCKER open questions from Round 2 in a single session. Decisions appended to `memory/requirements.md` §"Resolved Blockers" with full rationale.
- **B1 Deployment posture:** Managed single-tenant. NOT on-prem VPC, NOT shared SaaS. Eliminates FM1.2/FM1.3/FM1.4 (RPN 56 total) by construction. Winston designs facade with no query-layer tenant scoping — tenant boundary IS the Postgres instance. One-way door after customer #1.
- **B2 Embeddings = personal data:** YES. Ratifies FM3.10 override. Requirement #34 (sync embedding purge on delete) and #35 (quarantine strips embeddings in-place) are authoritative. One-way door under GDPR.
- **B3 Manifest registry:** Git-backed private config repo, not a service. Deployment manifests are signed YAML files in `praxis-config/deployments/{tenant_hash}.yaml`; CI check on the config repo prevents duplicate DB fingerprints; runtime re-verification re-pulls from Git every 60s. Fully reversible.
- **B4 LLM provider keys:** Tenant-scoped default. Managed billing deferred to a post-launch tier. Customer brings own Anthropic/OpenAI credentials; Praxis orchestration fee via Stripe is the only Praxis-side billing. Pi-Mono tracks usage per tenant for reporting, NOT for billing reconciliation. Eliminates FM3.4 entirely. Reversible but disruptive (future tier, not migration).
- **B5 Backup strategy:** Per-tenant encryption + crypto-shredding. KMS integration (AWS KMS or HashiCorp Vault — Winston's pick) behind a `KeyManager` interface. Rotation on customer request + annual schedule. Delete workflow: confirmed → destroy_key → wipe_infra → salted-hash audit. One-way door for existing backup ciphertext.
- **B6 Seed corpus:** Bootstrap with existing Tokonomics Rounds 1-4 + Business Session + Praxis planning + Pipeline.md + Stage 3 elicitation itself. License attestation is trivial ("praxis-internal, founder-generated"). Creates the "Built With Praxis" launch narrative as a free pre-sales asset. Andrey is the v1 curator. Stage 5 MAC benchmarks become seed_corpus_v2. Fully reversible.
- **Consistency check:** All 6 decisions are mutually reinforcing. B1 drives B3/B4/B5 naturally. B2 and B5 compose via crypto-shredding. B6 is independent and materializes a launch asset.
- **Remaining open questions:** 10 CONCERNs + 4 NICE-TO-HAVEs (catalogued in `requirements.md`). None block Winston from starting. All can be resolved during or after step 3.1 draft.
- **Gate to Step 3.1 Winston:** OPEN. `memory/requirements.md` is the binding input (NOT `requirements-privacy.md` which is superseded). Winston reads `requirements.md` first, then previous stage deliverables per "What Winston Should Read" section.
- **Next action:** Launch `/bmad-agent-architect` (Winston) for step 3.1 with full context of resolved blockers.

### 2026-04-12 — Stage 3 Step 3.0.2 Complete (Dr. Quinn — FMEA + Risk Assessment Matrix)
- **Step 3.0.2 (Round 2 adversarial pass)** — `/bmad-cis-problem-solving` with Pipeline-prescribed Failure Mode Analysis (primary) + Risk Assessment Matrix (secondary). Dr. Quinn red-teamed Round 1 defaults and produced `memory/requirements.md` (58 numbered binding requirements).
- **FMEA output:** 43 failure modes enumerated across Q1 (10) / Q2 (10) / Q3 (11) / Q4 (12) + 5 cross-cutting threats. RPN distribution: **28 BLOCKERS (RPN ≥ 12), 11 CONCERNS (6-11), 4 ACCEPTED (≤5)**.
- **Top 5 blockers:** FM1.2 shared Postgres co-tenancy (RPN 20), FM1.3 shared backup infrastructure (RPN 20), FM3.1 pgvector orphaned index entries (RPN 20), FM1.4 telemetry payload leak (RPN 16), FM2.1 seed corpus license violation (RPN 16). Additional RPN-16 blockers: FM3.2 embedding cache in RAM, FM4.8 retrieval telemetry query leak.
- **Does Round 1 stand?** YES. All four recommended defaults (single-tenant, seed corpus, GDPR-ready, MAC-gated admission) preserved. Round 2 adds 28 new architectural requirements but does not override the recommendations.
- **One Round 1 override:** FM3.10 — **quarantine operation must strip embeddings in-place**, not just flip state field. Round 1 treated quarantine as state-only; Round 2 shows retained embedding is still inversion-recoverable personal data. Winston must design quarantine as "embedding destroyed, metadata retained for audit."
- **New binding requirements added (highlights):** signed deployment manifest + 60s runtime re-verification, `tenant_hash` row-level column, per-tenant encrypted backups with crypto-shredding, tenant-scoped LLM provider API keys (FM3.4/CC.4 — **major ops implication**), durable idempotent delete job with vector-index post-verification, cache-invalidation pub/sub for delete AND quarantine, salted-hash audit log (avoids audit-of-audit paradox), composite admission signal with `quality_confidence`, tentative entry 90-day max lifetime with EXPIRED state, DB triggers + break-glass ledger for state transitions, typed `TelemetryEvent` schema with allowlist (no raw-string logs in Memory module), tenant-local log sink for debug, Mem0 integration test harness (two-tenant + delete + schema-stability + semantics regression).
- **Stage 5 dependency contract surfaced:** MAC must publish both `quality_score` AND `quality_confidence`, emit `memory.reuse_successful` event for tentative→confirmed promotion, and ship a backfill job to re-score existing tentative entries. These are now named deliverables in the MAC prompt's handoff contract.
- **Open questions now: 20 total.** 6 BLOCKERs require Andrey input before Winston begins (step 3.1): deployment posture, embeddings-as-personal-data confirmation, manifest registry implementation choice, tenant-scoped LLM API keys confirmation, backup crypto-shredding stance, seed corpus existence. 10 CONCERNs, 4 NICE-TO-HAVEs catalogued by severity.
- **Method note:** Pipeline prescribes FMEA + Risk Matrix; bmad-cis-problem-solving skill's generic 9-step interactive facilitation workflow was a mismatch for offline adversarial audit of an existing document. Applied prescribed methods directly — same pattern as Round 1's Stakeholder Round Table deviation from the generic elicitation menu.
- **Next step:** Before advancing to 3.1 (Winston), Andrey must answer the 6 BLOCKER open questions. Winston then reads `requirements.md` (the binding input, NOT `requirements-privacy.md` v0.2 which is superseded) and begins architecture draft.

### 2026-04-12 — Stage 3 Begins: Steps 3.0 + 3.0.1 Complete
- **Step 3.0 (Pre-flight)** — Stages 1-2 confirmed at 100% in the tracker. `_bmad-output/implementation-artifacts/praxis/memory/` directory created.
- **Step 3.0.1 (Elicitation Round 1 — Multi-tenant privacy model)** — `/bmad-advanced-elicitation` with **Stakeholder Round Table** method per Pipeline Section 4.5 Quick Reference. Output: `memory/requirements-privacy.md` v0.2.
- **Personas convened (6):** Priya (Enterprise CISO), Marco (SMB Founder / Solo Consultant / End User), Lena (GDPR DPO + Legal Counsel combined), Ravi (Revenue/GTM Lead), Sam (Praxis Platform Engineer), Dr. Ito (Memory-Systems Researcher). **Deviation from Pipeline prescription:** Pipeline listed 5 personas (SMB Founder, CISO, DPO, Legal Counsel, End User). Deviations: (a) DPO + Legal Counsel merged into Lena; (b) SMB Founder + End User merged into Marco (justified: in single-tenant-per-deployment the customer's founder IS the end user); (c) added Ravi GTM, Sam Platform Eng, Dr. Ito Researcher for sales/implementation/technical-risk coverage. Deviation was not pre-approved; log here in case it needs to be rolled back.
- **Four recommended defaults (binding on Winston unless Round 2 overrides):**
  1. **Tenancy (Q1):** Single-tenant-per-deployment only in v1. Unified Memory API reserves `tenant_id` parameter for Phase 2 shared-multi-tenant backend swap. Rationale: structural isolation removes scoping-bug class of failures; 5 of 6 personas converged.
  2. **Cross-tenant learning (Q2):** Per-tenant experience library + frozen versioned shared seed corpus (~500 curated public/licensed records). No cross-tenant code path exists. First-session story: seed corpus fills the gap until tenant builds its own library by session 3-5.
  3. **GDPR (Q3):** GDPR-ready architecture, deferred certification. Deletion cascade is day-one work. Embeddings ARE personal data (purged on delete) — backed by 2024 ETH Zurich embedding-inversion research via Dr. Ito. Residency = deployment location (free consequence of Q1). Article 15 access queries are first-class API from day one (new requirement surfaced by Lena).
  4. **Poisoning (Q4):** MAC-gated admission + tentative→confirmed state machine (SiriuS-style promotion on downstream reuse success) + admin quarantine API (distinct from GDPR delete per Lena) + retrieval-quality telemetry as a named deliverable (raised by Ravi). Thresholds 0.8/0.5 are placeholders pending Stage 5 calibration.
- **New requirements surfaced by the round table (not in original question framing):**
  - Article 15 right-to-access API (Lena) — first-class method, CLI-exposed in v1
  - Retrieval-quality telemetry dashboard (Ravi) — operator metrics, possibly customer-facing
  - Quarantine vs GDPR deletion as distinct operations with separate audit trails (Lena)
  - Seed corpus versioning with `seed_version` pinned per deployment and recorded in retrieval audit log (Dr. Ito)
  - Seed corpus refresh cadence owner named explicitly (Dr. Ito) — strawman quarterly, owner TBD
- **13 open questions escalated to Andrey** (indexed Q1-a through Q4-d in requirements-privacy.md §"Questions Still Outstanding"). None block Winston from drafting architecture.md; all must be answered before Stage 3 completes.
- **Next step:** 3.0.2 — `/bmad-cis-problem-solving` (Dr. Quinn) red-teams the Round 1 output via Failure Mode Analysis + Risk Assessment Matrix (per Pipeline Section 4.5 Quick Reference), produces consolidated `memory/requirements.md`.

### 2026-04-12 — Pipeline Document Created
- Created Pipeline.md (this file)
- 7 stage prompts already exist
- Ready to begin Stage 1
- Open items: User to decide when to start Stage 1 execution
- Billing mode: CLI/Max (not API) confirmed

### 2026-04-12 — Stage 2 Step 2.2 Complete (Murat — Test Strategy)
- **Step 2.2 (Murat — Compression Test Strategy)** — Strategy v1.0 produced; ~18K tokens, 14 sections + risk register + traceability + DoD
- Test pyramid: 25% unit / 25% property / 10% golden / 10% adversarial / 15% integration / 10% cross-platform+chaos / 5% A/B harness+reconciliation
- 14 Hypothesis property tests (P_T1-P_T3, P_F1-P_F6+P_F5b, P_V1-P_V7, P_R1-P_R2, P_O1-P_O2)
- 11 integration tests mapped to CM risks (integration #5 cascade chaos is the single highest-priority test)
- 60+ hand-curated Caveman adversarial corpus targeting S3/S4 (polarity flips, imperative inversions, negation drift, number loss, code-in-prose)
- Cross-platform RTK matrix: Linux x64/arm64, macOS x64/arm64, Windows x64
- Coverage gates per module driven by Matrix 6 severity (Orchestrator 100%, Caveman validators 100%, etc.)
- Gate decision protocol: CM9 cascade is a BLOCKER until integration #5 green; CM5 is the adversarial-corpus BLOCKER
- Default assumption: Caveman ships P0 behind compression.caveman.enabled feature flag (Option C from requirements-validation.md §5.1)
- **Next step:** Step 2.3 Amelia (`/bmad-agent-dev`) — compression layer implementation
- Open items (non-blocking for Amelia): Andrey §5.1 Caveman scope final confirmation, §5.2 embedding validator window, test strategy §11.1 corpus visibility

### 2026-04-12 — Stage 2 Steps 2.1 + 2.1.5 Complete
- **Step 2.1 (Winston — Compression Architecture)** — Architecture v0.1 drafted; ~19K tokens, 12 sections + traceability + handoff. Covers TONL (clean port), Forge (deterministic compaction, zero LLM calls confirmed), RTK (vendored Rust binary + Python wrapper), Caveman (LLM-driven — critical finding). All 4 reference dumps studied via parallel Explore agents. Saved to `compression/architecture.md`.
- **Step 2.1.5 (Elicitation Round 1)** — Two methods applied via `/bmad-advanced-elicitation`:
  - Method 2 FMEA: 40+ failure modes surfaced, 5 top-RPN gaps identified, 12 architecture edits applied
  - Method 5 Comparative Matrix: 7 weighted matrices produced, 4 additional threshold-tightening edits applied
  - Canonical severity ranking (Matrix 6): Orchestrator (4.15) → Caveman (3.60) → Forge (2.90) → TONL (2.85) → RTK (1.85)
  - Architecture advanced to v0.2 (16 edits total); `requirements-validation.md` created
- **Open items for Andrey (blocking Step 2.2):**
  - §5.1 requirements-validation.md — Caveman scope for Stage 2 P0 (Options A/B/C; recommendation Option C — feature-flagged)
  - §5.2 requirements-validation.md — embedding validator window (recommendation P1)
- **Next step:** Step 2.2 Murat (`/bmad-tea`) — preconditioned on Andrey's §5.1 decision
- Billing mode: CLI/Max (not API) confirmed throughout

### 2026-04-12 — Elicitation Framework Added (v1.1)
- Critical review identified missing elicitation steps for Stages 2-7
- Added Section 4.5 (Elicitation Framework Per Stage)
- Inserted elicitation sub-steps into Status Tracker for Stages 2, 3, 4, 5, 6, 7
- Total elicitation rounds added: 12 (across 6 stages)
- Stage 5 (MAC) identified as CRITICAL — 3 elicitation rounds before Winston
- Stage 6 (Studio) also 3 rounds before Winston
- Rationale: without elicitation, Winston invents answers to questions only the market can answer
- Elicitation outputs are BINDING inputs to Winston designs

### 2026-04-12 — Specific Elicitation Methods Assigned (v1.6)
- Previously pipeline said `/bmad-advanced-elicitation` etc. without specifying WHICH method within the skill
- Risk: agents picking arbitrary/shallow methods from 20-60 available options
- Researched actual methods available in each BMAD skill:
  - `/bmad-advanced-elicitation` → 50 methods across 10 categories
  - `/bmad-brainstorming` → 60+ techniques across 12 categories
  - `/bmad-cis-problem-solving` → 30 methods across 6 phases
  - `/bmad-cis-design-thinking` → 30 methods across 6 D.T. phases
  - `/bmad-cis-innovation-strategy` → 30 frameworks across 6 strategic categories
  - `/bmad-cis-storytelling` → 25 story types across 6 emotional categories
- Assigned specific methods to each elicitation round in Stages 3-7 (11 rounds total)
- Stage 5 (MAC) gets 3 methods per round (primary/secondary/tertiary) — highest rigor
- Stage 6 & 7 get multi-framework combinations for PMF-critical decisions
- Added "Quick Reference: Specific Methods Per Round" table in Section 4.5
- Rationale: "Use First Principles Thinking" is an actionable instruction; "use the brainstorming skill" is not

### 2026-04-12 — Universal Sequential Reference Reading Rule Generalized (v1.5)
- Noted that the sequential-read strategy applied only to Stage 2.3 in v1.4 — but it's a universal rule
- Added "UNIVERSAL RULE: Sequential Reference Reading" subsection to Section 4.6
- Rule: Read ONE reference at a time → process → clear context → read next
- Explicit patterns documented for Amelia/Winston/Alignment Reviewer workflows
- Mandatory reminders added to each affected step's checklist:
  - Stage 2: 2.3 Amelia
  - Stage 3: 3.1 Winston, 3.3 Amelia
  - Stage 4: 4.1 Winston, 4.3 Amelia
  - Stage 5: 5.1 Winston, 5.2 Murat, 5.3 Amelia, 5.5 Alignment
  - Stage 6: 6.1 Winston
  - Stage 7: 7.1 Winston, 7.3 Amelia
- Each reminder includes a specific numbered sequence for THAT stage's references
- Rationale: even 1M context can't hold all references simultaneously (Stage 4 alone = 4.5M tokens of refs)

### 2026-04-12 — 1M Context Window Strategy Added (v1.4)
- User reported Stage 2.3 Amelia hitting context compaction at 128k → output degradation
- Root cause: reference dumps (TONL 3MB + Forge 4.8MB + RTK 1.9MB + Caveman 210KB ≈ 2.5M tokens) overflow 200k context
- Added 1M context strategy section to Section 4.6
- Annotated affected steps with [1M] tag:
  - **Stage 2:** 2.3 Amelia, 2.3.5 Cleo, 2.5 Alignment
  - **Stage 3:** 3.1 Winston, 3.2 Murat, 3.3 Amelia, 3.3.5 Cleo, 3.5 Alignment
  - **Stage 4:** 4.1 Winston, 4.2 Murat, 4.3 Amelia, 4.3.5 Cleo, 4.5 Alignment
  - **Stage 5:** ALL steps (5.1-5.5) — MAC integrates all prior stages
  - **Stage 6:** 6.1 Winston, 6.5 Alignment
  - **Stage 7:** 7.1 Winston, 7.3 Amelia, 7.3.5 Cleo, 7.5 Alignment
- Total steps upgraded to [1M]: 24
- Context strategy notes added to critical steps (read references sequentially, not parallel)
- Max $100 (Max 5x) rate limit impact documented — [1M] counts ~5x against ITPM/OTPM budget
- Caveat: even 1M is not enough for ALL reference dumps at once; read selectively

### 2026-04-12 — Model & Thinking Effort Annotations Added (v1.3)
- Added Section 4.6 (Model & Thinking Effort Strategy)
- Annotated every step from 2.3 onwards with `_(Model: X · Thinking: Y)_`
- Stages 2-7 all have explicit model/thinking guidance per step
- Stage 5 (MAC) uses Opus + max throughout (core differentiation, highest risk)
- Stage 2 baseline: Sonnet 4.6 for implementation, Opus for alignment review
- Cleo (code review) defaults to Sonnet 4.6 + medium (pattern-matching against standards)
- Quinn (QA) elevated to Opus 4.6 + high for Stage 5 (adversarial tests demand deeper reasoning)
- Amelia (dev) elevated to Opus 4.6 for Stage 5 (MAC complexity justifies upgrade)
- Override guidance documented — escalate/downgrade as task reveals complexity

### 2026-04-12 — Clean Code Review Gate Added (v1.2)
- Added Cleo (`/bmad-agent-clean-code-reviewer`) as Step 3.5 after every Amelia development step
- Applies to Stages 2, 3, 4, 5, 6, 7 (Stage 1 excluded — will cover retroactively if needed)
- Cleo agent spec: `_bmad/bmm/agents/clean-code-reviewer.md` (Cleo — senior staff code quality engineer)
- Scope: Python, SQL, PyTorch with severity triage (CRITICAL / WARNING / INFO)
- Hard gate: 0 CRITICAL violations before advancing to Quinn test execution
- Auto-fix mode: Cleo applies all fixes when opted in (no per-fix confirmation)
- Stage 5 (MAC): extra scrutiny (highest risk)
- Stage 6 (Studio): Python glue only — YAML/Jinja2 handled separately
- Stage 7 (POV Harness): Python FastAPI backend only — Next.js/TypeScript frontend needs separate review
- Rationale: prevents "tests pass on bad code" where architectural smells break later

### 2026-04-12 — Stage 1 Finalized (v1.2)
- Stage 1.1 Winston architecture was already present (`pi-mono-cost-tracker-architecture.md`, ~1700 lines, 98 KB)
- Completed 1.2 Murat `test-strategy.md` — risk pyramid, P1–P15 Hypothesis properties, M1–M10 risk register, golden fixture layout
- Completed 1.3 Amelia implementation under `src/praxis/kernel/cost/` — 23 Python files: math, models, tracker, pricing catalog with 12 seed rows, 4 provider extractors (anthropic/openai/google/fake), SQLAlchemy 2.0 async storage, events outbox, reconciliation, telemetry
- Completed 1.4 Quinn tests — **74/74 passing**; math.py 96% coverage, models.py 93%, aggregate 79%; property-based via Hypothesis + SQLite integration suite
- Completed 1.5 `alignment-review.md` — AST scan verifies zero float in cost paths; M1/M2/M3/M5/M7/M8/M9/M10 structurally impossible, M4/M6 detectable/mitigated with follow-up
- Completed 1.6 `pre-sales-checkpoint.md` — headline captured, baseline measurement protocol defined, 6-step proof chain documented
- Smoke verified end-to-end: 1000 in + 500 out + 200 cache_read + 100 cache_write @ Opus rates = **$0.054675** (exact Decimal, idempotent on retry)
- Gate to Stage 2: **OPEN — Stage 1 graduates**
- Follow-ups (non-blocking, tracked in `alignment-review.md` §3):
  - Coverage sprint on events.py / telemetry.py / reconciliation drift paths if strict ≥95% aggregate required
  - External golden fixtures before Stage 4
  - Alembic migration wiring before Stage 7
  - Andrey to confirm seed pricing matches real rates and commit to monthly snapshot cadence

---

## SECTION 10: EMERGENCY REFERENCE — "WHERE IS X?" SHORTCUTS

| I need to know... | Find it at... |
|-------------------|---------------|
| Current stage status | Section 3 of this file (Pipeline.md) |
| Current stage prompt | `_bmad-output/planning-artifacts/Praxis/stage-N-winston-prompt.md` |
| Previous stage architecture | `_bmad-output/implementation-artifacts/praxis/<component>/architecture.md` |
| BMAD agent list | `_bmad/_config/agent-manifest.csv` |
| Build plan context | `_bmad-output/planning-artifacts/Praxis/praxis-build-plan.md` |
| Technical architecture | `_bmad-output/planning-artifacts/Praxis/box-core-architecture.md` |
| Reference repo for Stage N | See Section 6 "Reference Repos" table |
| Claude setup / billing | `claude-setup-reference.md` (root) |
| Permission config | `.claude/settings.local.json` |
| Previous tokonomics analysis | `_bmad-output/planning-artifacts/Tokonomics/` |
| Project-wide conventions | `CLAUDE.md` (root, auto-loaded) |

---

## SECTION 11: COMMAND QUICK REFERENCE

### Start a stage
```bash
# In Claude Code, attach files:
#   - Pipeline.md (this file)
#   - Current stage prompt file (e.g., stage-N-winston-prompt.md)
#   - Any session-handoff file if resuming

# Then invoke the architect
/bmad-agent-architect
# Paste the stage prompt content
```

### Check current status (mid-build)
```bash
# Quick status check
cat "_bmad-output/planning-artifacts/Praxis/Pipeline.md" | grep -E "\[[x~! ]\]"

# Check which stages have architecture docs
ls -la "_bmad-output/implementation-artifacts/praxis/"
```

### After stage completes
- Update checkboxes in Pipeline.md Section 3
- Add session log entry in Section 9
- Run alignment review (Section 8)
- Capture pre-sales metric
- Save Pipeline.md

---

## CRITICAL RULES (READ EVERY TIME)

1. **Do NOT skip stages.** Each depends on prior stage artifacts.
2. **Do NOT parallelize within the main pipeline.** One stage at a time.
3. **Do NOT move to Stage N+1 until Stage N checkboxes are all `[x]`.**
4. **Do NOT set `ANTHROPIC_API_KEY`.** CLI/Max billing mode required.
5. **Do NOT commit to git without user approval.**
6. **Do NOT invent file paths.** Use paths from this Pipeline.md or earlier docs.
7. **Do NOT use float for cost math.** Always `decimal.Decimal`.
8. **Do update Pipeline.md as work progresses.** This is the source of truth.
9. **Do run alignment review after each stage.** Catches drift early.
10. **Do capture pre-sales metrics at each checkpoint.** The build IS the case study.

---

**Pipeline.md Version:** 1.10
**Last Updated:** 2026-04-13
**Total Stages:** 7
**Total Elicitation Rounds:** 12 (across Stages 2-7)
**Clean Code Review Gates:** 6 (one after each Amelia step in Stages 2-7)
**Model/Thinking Annotations:** All steps from 2.3 onwards (51 annotated steps)
**1M Context Upgrades:** 24 steps (avoiding 128k compaction degradation)
**Sequential Reference Reading Reminders:** 12 steps (mandatory checklist items)
**Max Plan:** Max 5x ($100) — rate limits constrain but don't prevent [1M] usage
**Current Stage:** 4 COMPLETE (all 4.1–4.7 steps done — architecture ratified, 355 tests green at 97% coverage, alignment certified, 16 agents spawn at $1.40/workflow, F-1/F-3 closed, F-2 deferred to Stage 6; READY FOR STAGE 5)
**Launch Readiness:** 57% (4 of 7 stages complete — Stages 1–4 done)
