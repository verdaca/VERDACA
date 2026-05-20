# mac/test-strategy.md v0.3 — Full-Document Drift Inventory (Phase 1)

**Author:** Murat, Test Architect (BMAD TEA)
**Date:** 2026-04-14
**Purpose:** Phase 1 deliverable for v0.3 fresh ratification. Team-lead T-2 authorization 2026-04-14. Full-document drift classification across §1 through §17 of `mac/test-strategy.md` against `mac/architecture.md` v0.1, `mac/quality-rubric.md` v0.1, and `mac/benchmark-questions.md` v0.1. **No edits made to test-strategy.md during Phase 1.** Inventory only.

**Starting state:** v0.2 post-19-edits (§V list from DIV-5 STOP report). §3.2–§3.13 already reconciled through v0.2 edits. §1 header, §1.4, §1.7, §3.1, §13.1 row 2215, §13.4 row 2425, §15.3A already corrected. The new Phase 1 work is the full-document scan that the §N commitment did not cover.

**§N breach scope:** my prior commitment covered only §3.2–§3.13. This inventory covers §1 through §17 — every section, every subsection.

---

## §A. Classification legend

| Class | Meaning | Phase 2 disposition |
|---|---|---|
| **(a) CLEAN** | Matches arch/rubric byte-for-byte; no drift; no action | Leave as-is |
| **(b) LABEL DRIFT** | v0.1 hallucinated label name referenced in narrative/title; test logic survives a narrative rewrite | Narrative alignment against arch §6.1 names |
| **(c) SEMANTIC DRIFT** | Test body (assertions, fixture logic, anchored behavior) uses v0.1 hallucinated semantics orthogonal to ratified gate definition | C-2-style test body rewrite against arch §6.1 + rubric §6 |
| **(d) CITATION DRIFT** | Cites arch §N.M or rubric §N for content that doesn't live there; often swapped subsection numbers | Repair the citation if possible; drop/replace if not |
| **(e) FABRICATION** | References content that does not exist in arch at all (fabricated state names, fabricated exception classes, fabricated hard-fail semantics, fabricated `§12.2 items 1–12` prose mapping) | Delete or re-anchor on nearest real arch content; escalate to Winston if architectural structure is needed |
| **(f) FROZEN** | Intentionally ratified content that must not change (16-entry allow-list IDs, Option Y sidecar, fake fixture interface contracts, Decisions 1/2/3 structure, S-Q1–S-Q4 ratified answers) | Do NOT touch unless explicitly authorized |

---

## §B. Arch citation index (what actually exists where in `mac/architecture.md`)

This index is the authoritative cross-reference for classification. Any test-strategy.md citation that disagrees with this table is (d) CITATION DRIFT.

| Arch § | Actual content (from byte-for-byte scan of architecture.md) |
|---|---|
| §3.4 | `DomainClass` enum (5 values) |
| §5.1 | 3-Cycle Iteration Controller — Purpose |
| §5.2 | **State Machine** — states: `interpret`, `decompose`, `cycle_1_produce`, `cycle_2_review`, `cycle_3_verify`, `backtrack_set`, `publish`, `complete`, `failed`. Terminal transitions: BudgetExceededError → `failed`; second consecutive Critical gate failure at `cycle_3_verify` with `backtrack_count == 1` → `failed`. **No `HARD_FAIL`, `FORGE_FALLBACK`, `ADJUDICATED`, `TERMINATED`, `IDLE`, `CYCLE_N_RUNNING` states exist.** |
| §5.3 | **Phase Runner** (the executor; NOT "budget enforcement") |
| §5.4 | **Cycle 2 Parallelism** (NOT "CycleContext") |
| §5.5 | **Backtracking on Critical Gate Failure** (NOT "parallelism design") |
| §5.6 | Forge Fallback Handling — SQ-7 (prose; actual ordering logic is also in §6.3) |
| §5.7 | ResourceBudget Defaults (the actual budget enforcement section; cited incorrectly as §5.3 in test-strategy §4.3) |
| §6.1 | 12-Gate Catalog (R1–R12 ratified names + routing + priorities) |
| §6.2 | `GATE_SECTION_ROUTES` table + TRIZ-2/TRIZ-3 critical properties |
| §6.3 | **Co-Evaluation Pairs (Req-C) + SQ-4 + SQ-7 ordering**. Pair 1 = (R8, R7). Pair 2 = (R5, R4). SQ-7 step-2/3 ordering lives here. **NOT in §12.5.** |
| §6.5 | Domain Guard Conditions (Req-E) + SQ-5 — the ONLY arch section describing domain-class guards for R5 suspension and R11 suspension |
| §7.1 | Req-F Reviewer Elicitation Subsection |
| §7.2 | Binding to Runtime §4.1 Proxies (ProducerMemoryProxy / ReviewerMemoryProxy) |
| §7.3 | **Information Hiding — What the Reviewer Sees and Does Not See** (NOT "Event-bus role filter") |
| §7.4 | Aggregating Multiple Reviewers |
| §7.5 | **The Symmetric Asymmetry Boundary** — references Runtime §7.5 Layer 2 communication-bus filtering. Bus filter is a Runtime concern, not a MAC §7.3. |
| §8.1 | Bootstrap Loader Option Y sidecar, migration `0001_mac_bootstrap_metadata` |
| §10.1 | **Pi-Mono Integration** — CostTracker hot path |
| §10.2 | **Memory Integration** (NOT "Pi-Mono CostTracker") |
| §10.3 | **Runtime Integration** — MCP pin, shape guard (NOT "Memory named contracts") |
| §10.4 | **Compression Integration** — Forge F8, `reasoning_preserved` flag (NOT "Runtime integration" and NOT "MCP shape guard") |
| §10.5 | **DOES NOT EXIST in arch**. Compression is §10.4; there is no §10.5. Any test-strategy reference to `§10.5 Forge fallback` or `§10.5 Compression Forge F8` is FABRICATION. |
| §11.1 | Telemetry Label Cardinality Registry — SQ-2 Binding (label registry hard-fail) |
| §11.2 | **Metric Catalog** (NOT "dedup namespace") |
| §11.3 | **Linkage to Memory's TelemetryEvent** (NOT "metric catalog"). Dedup-key format is defined here inside the TelemetryEvent linkage narrative, not in §11.2. |
| §12.1 | Coverage Requirement (SQ-9) |
| §12.2 | **`no_waiver` Markers** — enumerated as 12 items: SQ-2 label registry / SQ-4 R8-R7 cap / SQ-5 DomainClass grep / SQ-7 Forge ordering / SQ-8 dedup_key prefix / Req-A label snapshot / Req-B routing snapshot / Req-D calibration SHA256 / Req-F protocol / InfoAsym ReviewerMemoryProxy AttributeError / Persona 3 gaming detection / R13 absence. **NOT a list of MAC gate calibration anchor tests.** |
| §12.3 | Property Tests |
| §12.4 | Calibration Tests (SHA256 of anchors, prompt-includes-anchors assertion) |
| §12.5 | **Asymmetry Tests** (NOT "SQ-7 ordering" — SQ-7 lives in §6.3) |
| §12.6 | Adversarial Tests (Persona 3 Gaming) |
| §12.7 | Mock vs Live Test Mix |
| §13.2 | Rejected Alternatives (Option X, R13 deferral) |

---

## §C. Per-section drift inventory (§1 through §17)

### §1 Context (already corrected in v0.2)

| Subsection | Class | Status | Notes |
|---|---|---|---|
| §1.1 Purpose | (a) CLEAN | Post-v0.2 | References arch §6.1 + rubric §6 + benchmark + Pipeline — all valid |
| §1.2 USR rule | (a) CLEAN | Post-v0.2 | Label-independent |
| §1.3 Stage 4 marker inheritance | (a) CLEAN | Post-v0.2 | Runtime marker list, label-independent |
| §1.3A Why MAC is most intensive | (a) CLEAN | Post-v0.2 | Architectural rationale |
| §1.4 Decision Bake-In | (a) CLEAN | v0.2 D-1 applied | Self-contained test-ID enumeration; no arch §12.2 citation |
| §1.5 Scope Boundaries | (f) FROZEN | Ratified | Leave verbatim — ratified content |
| §1.5A Inheritance from Stage 4 | (a) CLEAN | Post-v0.2 | Label-independent |
| §1.6 Success Criterion | (a) CLEAN | Post-v0.2 | Label-independent |
| §1.7 Changelog | (a) CLEAN | v0.2 applied | **REPLACE in v0.3** with v0.3 changelog documenting all 5 DIV classes (not just 3). Keep v0.2's drifted-label table verbatim as historical record; add DIV-4/DIV-5/Q-1/§4.2.4 disposition paragraphs. |

**§1 Phase 2 actions:** bump version header 0.2 → 0.3; rewrite §1.7 changelog to cover all 5 DIV classes + Q-1 allow-list rename + §4.2.4 disposition.

---

### §2 Test Taxonomy

| Subsection | Class | Notes |
|---|---|---|
| §2.1 Test Families | (a) CLEAN | Label-independent |
| §2.2 Test Tier Definitions | (a) CLEAN | Tier 1/2/3 definitions, label-independent |
| §2.3 Marker Semantics | (a) CLEAN | But line 212-213 reference "arch §12.2 item 9" (Req-F) and "arch §12.2 item 11" (Persona 3) — these are CORRECT references to arch §12.2 (the real arch §12.2 items 9 and 11 are Req-F and Persona 3 respectively). Actual (a) CLEAN. |
| §2.4 Citation Discipline | (a) CLEAN | Label-independent |
| §2.5 Test Pyramid | (a) CLEAN | Label-independent |

**§2 Phase 2 actions:** none.

---

### §3 Gate-Level Tests (§3.1 through §3.16)

| Subsection | Class | Status | Notes |
|---|---|---|---|
| §3.1 Gate Catalog Anchor Snapshot | (a) CLEAN | v0.2 applied | Regenerated against arch §6.1 |
| §3.1A Pattern macros (G-UNIT, G-CAL, G-ROUTE, G-DOMAIN, G-FORGE) | (a) CLEAN | Label-independent patterns |
| §3.1A.1 through §3.1A.5 | (a) CLEAN | Pattern definitions |
| §3.2 R1 Epistemic Calibration | (a) CLEAN | v0.2 applied |
| §3.2.1–§3.2.5 | (a) CLEAN | v0.2 applied |
| §3.3 R2 Question Fidelity | (a) CLEAN | v0.2 applied (DIV-4 §3.3.5 rewrite) |
| §3.3.1–§3.3.5 | (a) CLEAN | v0.2 applied |
| §3.4 R3 Falsifiability | (a) CLEAN | v0.2 applied (DIV-4 §3.4.5 monotonicity) |
| §3.4.1–§3.4.5 | (a) CLEAN | v0.2 applied |
| §3.5 R4 Steelman Completeness | (a) CLEAN | v0.2 applied |
| §3.5.1–§3.5.6 | (a) CLEAN | v0.2 applied; §3.5.5 anchors on arch §6.3 Pair 2 |
| §3.6 R5 Dissent Preservation | (a) CLEAN | v0.2 applied |
| §3.6.1–§3.6.6 | (a) CLEAN | v0.2 applied |
| §3.7 R6 Decision Relevance Density | (a) CLEAN | v0.2 applied (DIV-4 §3.7.5 rewrite) |
| §3.7.1–§3.7.5 | (a) CLEAN | v0.2 applied |
| §3.8 R7 Reasoning Traceability | (a) CLEAN | v0.2 applied |
| §3.8.1–§3.8.6 | (a) CLEAN | v0.2 applied; Pair 1 semantic text rewritten |
| §3.9 R8 Actionability Calibration | (a) CLEAN | v0.2 applied |
| §3.9.1–§3.9.6 | (a) CLEAN | v0.2 applied |
| §3.10 R9 Evidence Impartiality | (a) CLEAN | v0.2 applied (DIV-4 §3.10.5 rewrite) |
| §3.10.1–§3.10.5 | (a) CLEAN | v0.2 applied |
| §3.11 R10 Epistemic Scope Honesty | (a) CLEAN | v0.2 applied (DIV-4 §3.11.5 rewrite) |
| §3.11.1–§3.11.5 | (a) CLEAN | v0.2 applied |
| §3.12 R11 Scenario Coverage | (a) CLEAN | v0.2 applied (DIV-2 C-2 §3.12.5 rewrite) |
| §3.12.1–§3.12.5 | (a) CLEAN | v0.2 applied |
| §3.13 R12 Internal Consistency | (a) CLEAN | v0.2 applied (DIV-2 C-2 §3.13.5 rewrite) |
| §3.13.1–§3.13.5 | (a) CLEAN | v0.2 applied |
| §3.14 Cross-Gate Property Tests (§3.14.1–§3.14.6) | (a) CLEAN | Label-independent cross-gate properties; §3.14.3 mentions "evidence-penalty set" — minor narrative that could reference "{R7}" per arch §6.3 SQ-7 wording. Borderline (b) LABEL DRIFT. **Phase 2:** minor narrative touch-up of §3.14.3 to say "{R7}" instead of "evidence-penalty set". |
| §3.15 Mock vs Live Split (Tension #3) | (a) CLEAN | Label-independent tier split discussion |
| §3.16 Gate-Level Test Count Summary | **(b/d/e) MIXED — drift hotspot** | Lines 996–1034 contain: (1) "Decision 1 item N — R11 hard-fail" / "R12 hard-fail" narrative leak (b+d); (2) table row 1022/1023 "hard-fail structural" text (b); (3) line 1027 "calibration+hard-fail tests" phrase (b); (4) **lines 1029–1033 stray editorial draft** ("Wait — this needs a precise reconciliation... AUTHORITATIVE READING OF DECISION 2...") — authorized for deletion per team-lead item 4; (5) line 1033 "10 MAC new calibration/hard-fail (items 1–8, 10, 12)" — arch §12.2 miscitation leak (d). |
| §3.16.1 Authoritative inventory | (b+d) | Table with "hard-fail structural" phrasing; needs narrative cleanup to "structural calibration" language consistent with v0.2 §3.12.5/§3.13.5 rewrites |

**§3 Phase 2 actions:**
1. §3.14.3 narrative touch-up: "evidence-penalty set" → "{R7} per arch §6.3 SQ-7"
2. §3.16 rewrite: replace "calibration+hard-fail" with "gate calibration tests"; replace "R11 hard-fail" / "R12 hard-fail" with "R11 structural calibration (scenario coverage property)" / "R12 structural calibration (direct contradiction detector)"; delete lines 1029–1033 stray editorial draft per team-lead authorization item 4.
3. §3.16.1 table: change "hard-fail structural" rows 9/10 to "structural calibration"

---

### §4 3-Cycle Iteration Controller Tests — **CATASTROPHIC DRIFT — REQUIRES ARCHITECTURAL REALIGNMENT**

**This is the largest single-section drift surface in the document.** The entire §4.1 state machine definition is fabricated — none of the states listed in v0.1 line 1046–1063 exist in arch §5.2. The test anchors, fixture names, and fulfillment criteria in §4.2 all reference these fabricated states. Plus five separate arch §5.N citation drifts in §4.3/4/5/6.

| Subsection | Class | Drift detail | Phase 2 disposition |
|---|---|---|---|
| §4 Intro | (a) CLEAN | Narrative description |
| **§4.1 State Machine Definition** | **(e) FABRICATION** | Lines 1046–1063 define states `{IDLE, CYCLE_1_RUNNING, CYCLE_1_REVIEWED, CYCLE_2_RUNNING, CYCLE_2_REVIEWED, CYCLE_3_RUNNING, CYCLE_3_REVIEWED, ADJUDICATED, TERMINATED, FORGE_FALLBACK, HARD_FAIL}` and transitions including `* → HARD_FAIL (on R11 or R12 score=1)`. **None of these states are in arch §5.2.** Arch §5.2 states are `interpret, decompose, cycle_1_produce, cycle_2_review, cycle_3_verify, backtrack_set, publish, complete, failed`. Transitions include backtrack_set on first critical failure, `failed` on BudgetExceededError or second-consecutive critical failure. | **REGENERATE §4.1 byte-for-byte from arch §5.2 state machine.** Use arch state names verbatim. Drop HARD_FAIL, FORGE_FALLBACK, ADJUDICATED, TERMINATED, IDLE, CYCLE_N_RUNNING entirely. Keep the visual diagram but use arch §5.2 names. |
| §4.1A Hypothesis harness setup | (e) FABRICATION leakage | Line 1085 `self.visited_states: set[State] = {State.IDLE}` — State.IDLE is fabricated | Replace `State.IDLE` with `State.INTERPRET` (or arch §5.2's initial state); update `ALLOWED_TRANSITIONS` to match regenerated §4.1 |
| §4.2.1 `MAC-T-CYCLE-STATE-01` Reachability | (e) FABRICATION | Asserts three terminal states `ADJUDICATED, TERMINATED, HARD_FAIL` — none exist | Rewrite to assert reachability of arch terminal states `complete` and `failed` (the two terminals in arch §5.2) |
| §4.2.2 `MAC-T-CYCLE-STATE-02` No invalid transitions | (b) LABEL DRIFT | Test logic is valid (assert no transition outside `ALLOWED_TRANSITIONS`); only narrative needs to reference regenerated §4.1 | Narrative alignment |
| §4.2.3 `MAC-T-CYCLE-STATE-03` Early termination | (e) FABRICATION | "stability-based early termination" is not in arch §5.2; `State.TERMINATED` is fabricated. Arch §5.2 does NOT describe stability-based early termination — it shows linear cycle_1 → cycle_2 → cycle_3 → publish/backtrack. | **Delete this test** OR rewrite as a test of the `cycle_3_verify → publish` path (normal completion after cycle 3). Requires Winston sign-off on whether stability-based early termination is architecturally present or was v0.1 invention. **Recommend: re-anchor as normal-completion test (cycle_3_verify → publish).** |
| §4.2.4 `MAC-T-CYCLE-STATE-04` "Hard-fail short-circuit" | (e) FABRICATION | "R11 score=1 → HARD_FAIL without running cycles 2 or 3" — fabricated. Arch §5.2 has no hard-fail short-circuit; R11 is not a hard-fail gate; there is no single-cycle terminal path. | **Re-anchor per team-lead Special Handling item 1:** test the arch §5.2 backtrack-then-failed path. `MAC-T-CYCLE-STATE-04` becomes "Second consecutive Critical gate failure terminates to `failed`": cycle_3_verify with backtrack_count == 1 and another Critical gate (any of R1/R2/R4/R5/R7 per arch §6.1) scoring < 3 → transition to `failed`. This is a real architectural state transition worth testing. |
| §4.2.5 `MAC-T-CYCLE-STATE-05` Forge fallback transition | (e) FABRICATION | `FORGE_FALLBACK` state does not exist in arch §5.2. Arch §5.6 describes "Forge Fallback Handling" as a behavioral fallback (score degradation path), not a state machine state. | **Re-anchor as a behavioral test:** `Forge-degradation detection path — when CompressionForge.compress() returns reasoning_preserved=False, the controller applies R7 penalty per arch §6.3 SQ-7 step 3 and emits telemetry.` Delete `State.FORGE_FALLBACK` references. |
| §4.3 Budget Enforcement (§4.3.1–§4.3.3) | (d) CITATION DRIFT | Cites `arch §5.3 budget enforcement` — arch §5.3 is Phase Runner. Budget enforcement is arch §5.7 ResourceBudget Defaults. | Repair citations §5.3 → §5.7 |
| §4.4 Backtracking (§4.4.1–§4.4.2) | (d) CITATION DRIFT | `§5.4 CycleContext` — arch §5.4 is Cycle 2 Parallelism. The backtrack mechanism is in arch §5.5 | Repair citation §5.4 → §5.5 |
| §4.5 Parallelism Determinism (§4.5.1–§4.5.4) | (d) CITATION DRIFT | §4.5.4 cites `arch §5.5 parallelism design` — arch §5.5 is Backtracking. Parallelism is arch §5.4 | Repair citation §5.5 → §5.4 |
| §4.6 Forge-Degradation Ordering (§4.6.1–§4.6.3) | (d) CITATION DRIFT | §4.6.1/§4.6.2 cite `arch §12.5 SQ-7` — arch §12.5 is Asymmetry Tests. SQ-7 ordering is in §6.3 | Repair citation §12.5 → §6.3 |
| §4.6A Cycle Telemetry (§4.6A.1–§4.6A.3) | (d) CITATION DRIFT | §4.6A.1 cites `§11.3 metric catalog` — arch §11.3 is TelemetryEvent Linkage. Metric Catalog is §11.2. §4.6A.2 cites `§11.2 dedup namespace` — arch §11.2 is Metric Catalog. Dedup namespace format lives inside §11.3 TelemetryEvent linkage per the dedup-key format description | Swap citations: §11.3 → §11.2 for metric catalog; §11.2 → §11.3 for dedup namespace |
| §4.6B Cycle Cancellation (§4.6B.1–§4.6B.3) | (d) CITATION DRIFT | §4.6B.1 cites `§5.7 cancellation semantics` — arch §5.7 is ResourceBudget Defaults. Cancellation semantics are not explicitly in arch §5 — may need Winston clarification or removal of specific citation | Drop "cancellation semantics" citation; keep test if cancellation is architecturally present (check arch §5.1 purpose + Runtime §4 for cancellation hooks) |
| §4.7 Cycle Section-Level (§4.7.1–§4.7.2) | (a) CLEAN | Cites arch §6.2 correctly |
| §4.8 Cycle Test Count Summary | (b) LABEL DRIFT | Minor — table counts need no change; labels already correct |

**§4 Phase 2 actions:**
1. **§4.1 REGENERATE** the state machine definition byte-for-byte from arch §5.2 (states + transitions). This is the load-bearing rewrite.
2. **§4.1A** update `State.IDLE` → `State.INTERPRET` or whatever arch §5.2 initial state name is
3. **§4.2.1** rewrite assertions around arch's two terminal states (`complete`, `failed`)
4. **§4.2.2** narrative alignment (test logic preserved)
5. **§4.2.3** re-anchor as normal-completion test OR delete
6. **§4.2.4** re-anchor per team-lead Special Handling item 1 (backtrack-then-failed path)
7. **§4.2.5** re-anchor as behavioral Forge-degradation test (not state)
8. **§4.3/§4.4/§4.5/§4.6** repair 5 separate arch §5.N / §12.5 / §11.N citation drifts
9. **§4.6A** swap §11.2 ↔ §11.3 citations

**Winston escalation needed:** Confirm that "stability-based early termination" (§4.2.3) and "mid-cycle cancellation" (§4.6B) are architecturally present or v0.1 inventions. Arch §5.2 does not describe either. Without Winston clarification these tests need deletion, not re-anchor.

---

### §5 Information Asymmetry Tests

| Subsection | Class | Notes |
|---|---|---|
| §5.0 Asymmetry Threat Model | (a) CLEAN | References arch §12.2 item 9 (Req-F) correctly |
| §5.1 Req-F Two-Step Independence (§5.1.1–§5.1.4) | (a) CLEAN | Arch §7.1 citation correct; §12.2 item 9 citation correct (item 9 = Req-F per arch) |
| §5.2 Proxy Asymmetry (§5.2.1–§5.2.5) | (a) CLEAN | Arch §7.2 citation correct |
| §5.3 Bus Filter Tests (§5.3.1–§5.3.3) | **(d) CITATION DRIFT** | Cites `arch §7.3 Event-bus role filter` — arch §7.3 is "Information Hiding — What the Reviewer Sees and Does Not See". Bus filtering lives at Runtime §7.5 per arch §7.5 cross-reference. | Repair citation: drop `arch §7.3`; use `runtime/architecture.md §7.5 Layer 2 communication-bus filtering` or a self-contained description |
| §5.4 Asymmetry Test Count | (a) CLEAN | Count table |

**§5 Phase 2 actions:** §5.3 citation repair only.

---

### §6 Integration Tests

| Subsection | Class | Notes |
|---|---|---|
| §6.0 Integration Test Environment | (a) CLEAN | Fixture setup |
| §6.1 Pi-Mono CostTracker (§6.1.1–§6.1.3) | (d) CITATION DRIFT | §6.1.1 cites `arch §10.2` for Pi-Mono — arch §10.2 is Memory Integration, Pi-Mono is §10.1. §6.1.3 cites runtime F-13.C1 — valid |
| §6.2 Memory Named-Contract (§6.2.1–§6.2.5) | (d) CITATION DRIFT | §6.2.1 cites `arch §10.3 Memory named contracts` — arch §10.3 is Runtime, Memory is §10.2. Memory:913/914/915 line refs may also need verification |
| §6.3 Runtime Integration (§6.3.1–§6.3.2) | (d) CITATION DRIFT | §6.3.1 cites `arch §10.4 Runtime integration` — arch §10.4 is Compression, Runtime is §10.3. §6.3.2 cites `arch §10.4 MCP shape guard` — same issue; MCP pin is in Runtime §10.3 |
| §6.4 Compression Forge F8 (§6.4.1–§6.4.2) | **(d+e)** | §6.4.1 cites `arch §10.5 Compression Forge F8` — **§10.5 does not exist in arch**; Compression is §10.4. Fabrication-level citation. Also asserts FORGE_FALLBACK state transition which is fabricated | Repair citation §10.5 → §10.4; remove State.FORGE_FALLBACK assertion |
| §6.4A Cross-Module Wire-Up (§6.4A.1–§6.4A.3) | (e) FABRICATION leakage | §6.4A.1 line 1535 asserts `result.state == State.ADJUDICATED` — fabricated. §6.4A.2 cites `arch §10.4 multi-tenant isolation` — arch §10.4 is Compression, not multi-tenant isolation | Replace `State.ADJUDICATED` with arch's normal-completion state (`complete`); repair §10.4 citation or drop it |
| §6.5 Integration Test Count | (a) CLEAN |  |

**§6 Phase 2 actions:**
1. Repair arch §10 citation shifts: §10.2 (Pi-Mono → §10.1), §10.3 (Memory → §10.2), §10.4 (Runtime → §10.3), §10.5 (Compression → §10.4). This is a systematic off-by-one.
2. Remove `State.ADJUDICATED` and `State.FORGE_FALLBACK` fabricated references from §6.4A.1 and §6.4.1

---

### §7 Evaluation Harness Tests

| Subsection | Class | Notes |
|---|---|---|
| §7.0 Why Evaluation Harness Tests Exist | (a) CLEAN | Narrative |
| §7.1 Benchmark Harness Authority | (a) CLEAN | Top-5 weighting R1/R2/R4/R5/R7 — matches ratified Critical gates per arch §6.1 |
| §7.2 Scoring Logic Tests (§7.2.1–§7.2.4) | (a) CLEAN | Numeric composite math |
| **§7.2.5 `MAC-T-BENCH-SCORING-05` Hard-fail short-circuit on R11=1** | **(e) FABRICATION** | "If R11 or R12 = 1, composite is None and result is `HARD_FAIL`" — fabricated hard-fail semantics leaking from v0.1 R11=Safety / R12=Policy. Under ratified R11=Scenario Coverage, R12=Internal Consistency, no hard-fail exists | **Delete this test** (no architectural anchor) OR rewrite as an R11/R12 score=1 edge case that causes low composite score but does NOT short-circuit. Recommend: rewrite as "R11=1 or R12=1 produces minimum composite score per formula (no short-circuit)". |
| §7.3 ADR-1 Hybrid Pass (§7.3.1–§7.3.3) | (a) CLEAN | Pass 1 blind / Pass 2 open — label-independent |
| §7.4 ADR-3 Spearman (§7.4.1–§7.4.3) | (a) CLEAN | Numeric |
| §7.5 Baseline Comparison (§7.5.1–§7.5.4) | (a) CLEAN | Three-baseline framework |
| §7.6 Benchmark Question Corpus (§7.6.1–§7.6.2) | (a) CLEAN |  |
| §7.7 §5 Calibration Anchor Tests (§7.7.1–§7.7.2) | (a) CLEAN | 12 gates × 2 anchors |
| §7.8 FakeBenchmarkOutputs Harness (§7.8.1–§7.8.2) | (a) CLEAN |  |
| §7.9 PR-Gate vs Nightly Harness Split (§7.9.1–§7.9.2) | (a) CLEAN | S-Q3 ratified |
| §7.10 Release-Gate A4 (§7.10.1–§7.10.2) | (a) CLEAN | S-Q4 ratified |
| §7.10A Composite Worked Examples | (a) CLEAN | Needs verification — likely uses gate IDs with no label text, probably clean |
| §7.11 Evaluation Harness Test Count | (a) CLEAN |  |

**§7 Phase 2 actions:** rewrite §7.2.5 only.

---

### §8 Bootstrap Loader Tests

| Subsection | Class | Notes |
|---|---|---|
| §8.0 Design Context | (a) CLEAN | Option X vs Option Y |
| §8.1 Sidecar Migration (§8.1.1–§8.1.3) | (a) CLEAN | Arch §8.1, §13.2 citations valid |
| §8.2 Gold-Standard Loading (§8.2.1–§8.2.3) | (a) CLEAN |  |
| §8.3 Option X Cross-Reference | (a) CLEAN |  |
| §8.4 Idempotent Re-Run (§8.4.1–§8.4.4) | (a) CLEAN | S-Q1 ratified |
| §8.5 Facade Tests (§8.5.1–§8.5.2) | (a) CLEAN |  |
| §8.6 Test Count | (a) CLEAN |  |

**§8 Phase 2 actions:** none.

---

### §9 Observability Tests

| Subsection | Class | Notes |
|---|---|---|
| §9.0 Design Rationale | (a) CLEAN |  |
| §9.1 Label Registry Hard-Fail (§9.1.1–§9.1.4) | (a) CLEAN | SQ-2 label registry hard-fail is legitimate (arch §11.1 / §12.2 item 1) |
| §9.2.1 Dedup key format | (d) CITATION DRIFT | Cites `arch §11.2 dedup namespace` — arch §11.2 is Metric Catalog. Dedup key format lives in arch §11.3 TelemetryEvent Linkage narrative | Repair: §11.2 → §11.3 |
| §9.2.2–§9.2.3 Dedup tests | (a) CLEAN | Structural tests |
| §9.3 Violation Counter (§9.3.1–§9.3.4) | (a) CLEAN | S-Q2 ratified; legitimate SQ-2 label registry hard-fail references |
| §9.4.1 All metrics in §11.3 exist | (d) CITATION DRIFT | Cites `arch §11.3 metric catalog` — arch §11.3 is TelemetryEvent Linkage. Metric catalog is §11.2 | Repair: §11.3 → §11.2 |
| §9.4.2 Metric snapshot | (a) CLEAN |  |
| §9.5 Test Count | (a) CLEAN |  |

**§9 Phase 2 actions:** §9.2.1 and §9.4.1 citation swap (§11.2 ↔ §11.3).

---

### §10 Adversarial Tests — **DIV-5 hotspot already identified**

| Subsection | Class | Notes |
|---|---|---|
| §10.0 Scope | (a) CLEAN |  |
| §10.1 Persona 3 Gaming Resistance (§10.1.1–§10.1.5) | (a) CLEAN | Req-F + §12.2 item 11 (Persona 3) citations correct |
| **§10.2 Adversarial R11 Safety Probing** | **(e) FABRICATION — section header + 2 tests** | Header "R11 Safety Probing" + §10.2.1 "Jailbreak prompts trigger R11 hard-fail" + §10.2.2 "Indirect injection attempts blocked" all assume v0.1 R11=Safety semantics. Under ratified R11=Scenario Coverage, jailbreak / injection concerns are not R11 concerns. | **Rewrite per team-lead Special Handling item 2:** rename section to "Adversarial R11 Scenario Coverage Probing"; §10.2.1 becomes fixture with single-scenario bias; §10.2.2 becomes fixture with manufactured (non-falsifiable) trigger conditions. Jailbreak/injection concerns flagged as out-of-scope in §1.7 changelog. |
| **§10.3 Adversarial R12 Policy Probing** | **(e) FABRICATION — section header + 1 test** | Header "R12 Policy Probing" + §10.3.1 "Policy-violating outputs trigger R12 hard-fail" assume v0.1 R12=Policy Compliance. Under ratified R12=Internal Consistency, policy violations are not R12 concerns. | **Rewrite per team-lead Special Handling item 2:** rename to "Adversarial R12 Internal Consistency Probing"; §10.3.1 becomes fixture with subtle cross-section contradictions (FINDINGS establish moderate confidence; RECOMMENDATIONS treat as certain). Policy-compliance flagged as out-of-scope in §1.7 changelog. |
| §10.4 Adversarial Corpus Rotation Protocol (Tension #6) | (a) CLEAN | Rotation protocol, label-independent |
| §10.4A Adversarial Fixture Format | (a) CLEAN | Format spec |
| §10.5 Adversarial Test Count | (a) CLEAN |  |

**§10 Phase 2 actions:** rewrite §10.2 and §10.3 per team-lead Special Handling item 2.

---

### §11 Negative Tests

| Subsection | Class | Notes |
|---|---|---|
| §11.0 What Negative Tests Prove | (a) CLEAN |  |
| §11.1 No 13th Gate (§11.1.1–§11.1.2) | (a) CLEAN | Structural grep tests |
| §11.2 Option X Absence (§11.2.1–§11.2.3) | (a) CLEAN | Three-layer negative test, Tension #8 |
| §11.3 No Parallel MacTelemetryEvent (§11.3.1–§11.3.2) | (a) CLEAN |  |
| §11.4 DomainClass Singular (§11.4.1–§11.4.2) | (d) CITATION DRIFT | Cites `arch §12 Req-E + SQ-5` — Req-E is arch §6.5, not §12. §12 is Test Requirements. | Repair: §12 → §6.5 for Req-E |
| §11.5 Pinning (§11.5.1) | (d) CITATION DRIFT | Cites `arch §10.4 MCP shape guard` — arch §10.4 is Compression, not MCP. MCP is Runtime §10.3 | Repair: §10.4 → §10.3 |
| §11.6 Test Count | (a) CLEAN |  |

**§11 Phase 2 actions:** 2 citation repairs.

---

### §12 Calibration Tests — Live-Judge Drift Canary

| Subsection | Class | Notes |
|---|---|---|
| §12.1 Drift Canary Definition | (a) CLEAN |  |
| §12.2 Per-Gate Drift Canary Tests (§12.2.1–§12.2.3) | (a) CLEAN | 24 live tests by gate ID; label-independent |
| §12.3 Live-Judge Cost Budget | (a) CLEAN |  |
| §12.4 Failure Handling | (a) CLEAN |  |
| §12.5 Test Count | (a) CLEAN |  |

**§12 Phase 2 actions:** none.

---

### §13 Coverage and Markers

| Subsection | Class | Notes |
|---|---|---|
| §13.1 Pipeline.md §5.2 Gate Checklist | (a) CLEAN | v0.2 applied; self-contained citation |
| §13.2 Coverage Target | (a) CLEAN |  |
| §13.3 OQ-TS-9 Allow-List Meta-Test | (a) CLEAN (wrapper narrative) |  |
| §13.3.1 Target path | (a) CLEAN |  |
| **§13.3.2 Implementation target (allow-list code)** | **(f) FROZEN + Q-1 authorized rename** | Lines 2414–2423 contain the Python `NO_WAIVER_ALLOWLIST` frozenset with nodeid strings. Lines 2422/2423 have `test_mac_t_gate_r11_05_hard_fail_short_circuit` / `test_mac_t_gate_r12_05_hard_fail_policy` which embed fabricated "hard_fail" semantics. Team-lead Q-1 AUTHORIZED: rename to `test_mac_t_gate_r11_05_scenario_coverage_property` / `test_mac_t_gate_r12_05_direct_contradiction_detector`. Canonical allow-list IDs `MAC-T-GATE-R11-05` and `MAC-T-GATE-R12-05` preserved; 16-entry count preserved; OTEL provisional tags preserved; self-reference preserved. Also repair the "Decision 1 item N" inline comments in the code block to drop arch §12.2 miscitation (use self-contained phrasing). |
| §13.3.3 Allow-list contents — enumerated | (f) FROZEN + Q-1 | Lines 2480–2491 enumerate the 16 entries. Rows 12 and 13 have the same two fabricated function names. Apply Q-1 rename. Preserve all 16 rows, OTEL provisional (#2, #3), self-reference (#16) |
| §13.3.3.1 Ratification Block Option 1 | (f) FROZEN |  |
| §13.3.4 Self-referential bootstrap property | (f) FROZEN |  |
| §13.3.5 Retroactive Inventory (3 Runtime Entries) | (f) FROZEN | 2 OTEL provisional entries with PENDING AUDIT at 5.5 |
| §13.3.6 Meta-test spec | (f) FROZEN |  |
| §13.3.7 Operational Procedures | (a) CLEAN |  |
| §13.4 no_waiver Discipline Summary | (a) CLEAN (v0.2 applied) | Row 2425 already dropped "+ hard-fail" language |
| §13.5 Coverage Exclusion (§13.5.1–§13.5.3) | (a) CLEAN |  |
| §13.5A Coverage Measurement Implementation | (a) CLEAN |  |
| §13.5B Test Marker Selection Decision Matrix | (a) CLEAN |  |
| §13.6 Marker Registration | (a) CLEAN |  |

**§13 Phase 2 actions:**
1. Apply Q-1 nodeid renames in §13.3.2 Python code block (2 function names)
2. Apply Q-1 nodeid renames in §13.3.3 enumerated table rows 12 and 13
3. Repair "Decision 1 item N" inline comments in §13.3.2 code block to self-contained phrasing

---

### §14 Test Execution Strategy

| Subsection | Class | Notes |
|---|---|---|
| §14.1 Directory Layout | (a) CLEAN — needs pre-draft verification |  |
| §14.2 Pytest Configuration | (a) CLEAN |  |
| §14.3 Fixture Interface Contracts | (f) FROZEN | Fake fixture contracts are explicitly frozen per team-lead §V preservation rule |
| §14.3.1 `FakeLLMJudge` | (f) FROZEN + potential narrative drift | Likely contains gate ID references; **needs pre-draft verification in Phase 2** |
| §14.3.2 `FakeReviewerAgent` | (f) FROZEN |  |
| §14.3.3 `FrozenClock` | (f) FROZEN |  |
| §14.3.4 `FakeCompressor` | (f) FROZEN + potential leakage | Line 2985 mentions "to force MAC into FORGE_FALLBACK state" — fabricated state leakage in docstring. Test body is frozen but the docstring narrative is (e) FABRICATION | Update docstring to remove FORGE_FALLBACK reference; describe as "Forge degradation path trigger" |
| §14.3.5 `FakeBenchmarkOutputs` | (f) FROZEN | Likely has gate ID usage; **needs pre-draft verification** |
| §14.3.6 `MacBootstrapMetadataStore` | (f) FROZEN |  |
| §14.3.7 `ResetCounterFixture` | (f) FROZEN |  |
| §14.3.8 Composition Pattern | (a) CLEAN |  |
| §14.4 CI Budget | (a) CLEAN |  |
| §14.4A Estimated CI Wall-Clock | (a) CLEAN |  |
| §14.4B Parallelization | (a) CLEAN |  |
| §14.5 Checkpoint Cadence | (a) CLEAN |  |
| §14.6 Postgres via testcontainers | (a) CLEAN |  |
| §14.7 Mock vs Live Split | (a) CLEAN — line 3127 has `assert result.state == State.FORGE_FALLBACK` fabricated state leakage | Remove FORGE_FALLBACK assertion |

**§14 Phase 2 actions:**
1. Pre-draft deep read of §14.3.1 and §14.3.5 for gate ID / label drift
2. Remove "FORGE_FALLBACK state" from §14.3.4 docstring
3. Remove `State.FORGE_FALLBACK` assertion from §14.7 code example (line 3127)

---

### §15 Test ID Schema

| Subsection | Class | Notes |
|---|---|---|
| §15.1 Schema Definition | (a) CLEAN | `MAC-T-{section}-{seq}` |
| §15.2 ID-to-Spec-Row Mapping | (a) CLEAN |  |
| §15.3 Test Function Naming Convention | (a) CLEAN |  |
| §15.3A Worked Example | (a) CLEAN (v0.2 applied) | "Citation Integrity" → "Actionability Calibration" already fixed |
| §15.3B Worked Example 2 — Cross-Sectional | **(e) FABRICATION** | Line 3334: "§4.1 state machine — must pass through `FORGE_FALLBACK` state (or stay in `CYCLE_X_RUNNING`)"; line 3340: cites "mac/architecture.md §5.2 state machine — FORGE_FALLBACK state" — fabricated state references | Replace FORGE_FALLBACK / CYCLE_X_RUNNING with arch §5.2 state names; update cross-reference citation |
| §15.4 Cycle/SQ/Benchmark Q Mapping | (a) CLEAN — needs pre-draft verification |  |

**§15 Phase 2 actions:** rewrite §15.3B worked example against arch §5.2 state names.

---

### §16 Handoff to 5.3 Amelia

| Subsection | Class | Notes |
|---|---|---|
| §16.1 What Amelia Implements | (a) CLEAN |  |
| §16.2 Red-First Test Order | (a) CLEAN |  |
| §16.3 Checkpoint Plan | (a) CLEAN | Label-independent |
| §16.4 Preflight Checklist | (a) CLEAN | Already updated to ratified state |
| §16.5 Red-Band Definition | (a) CLEAN |  |
| §16.5A Common Pitfalls | (a) CLEAN |  |
| §16.5B Test Authoring Walkthrough | (a) CLEAN | `MAC-T-GATE-R4-06` Req-F example; arch §7.1 + §12.2 item 9 citations correct |
| §16.6 5.2 → 5.3 Transition Contract | (a) CLEAN |  |

**§16 Phase 2 actions:** none (§16 is surprisingly clean).

---

### §17 Test ID Total & Final Accounting

| Subsection | Class | Notes |
|---|---|---|
| §17 Test ID Total (header + table) | (a) CLEAN |  |
| §17.0A Test Pyramid by Tier | (a) CLEAN |  |
| **§17.1 `no_waiver` Discipline Final Count** | **(d) CITATION DRIFT** | Line 3566: "10 MAC calibration / hard-fail `no_waiver` tests (Decision 1 items 1, 2, 3, 4, 5, 6, 7, 8, 10, 12)" — both "calibration / hard-fail" language and "items 1–8, 10, 12" arch §12.2 miscitation | Rewrite to match §1.4 v0.2 self-contained prose: "10 MAC gate calibration tests: the 8 calibration-anchor tests for R1/R2/R3/R4/R5/R7/R8/R11 (`MAC-T-GATE-R{N}-02`) + 2 structural calibration tests `MAC-T-GATE-R11-05` and `MAC-T-GATE-R12-05`. See §13.3.3 entries 4–13." |
| §17.2 Gate Checklist Row Verification | (a) CLEAN |  |
| §17.2A Risk Register | (a) CLEAN |  |
| §17.2B Non-Blocking Residual Questions | (a) CLEAN |  |
| §17.3 Ratification State | (b) LABEL/VERSION DRIFT | Line 3602: "v0.1 RATIFIED 2026-04-14" — needs update to v0.3 | Update to v0.3 |
| §17.4 Spot-Check Worksheet | (a) CLEAN |  |
| §17.5 Document Provenance | (b) VERSION DRIFT | Line 3648: "Version: 0.1 RATIFIED 2026-04-14" — needs update to v0.3 | Update to v0.3 |
| End marker (line 3637) | (b) VERSION DRIFT | "END — mac/test-strategy.md v0.1 RATIFIED 2026-04-14" | Update to v0.3 |

**§17 Phase 2 actions:**
1. §17.1 rewrite to self-contained prose
2. §17.3 / §17.5 / end marker version bumps to v0.3

---

## §D. Summary of Phase 2 edit surface

**Total Phase 2 edits by section:**

| Section | Drift class | Edit count estimate |
|---|---|---|
| §1 | Version bump + §1.7 v0.3 changelog rewrite | 2 edits |
| §2 | None | 0 |
| §3 | §3.14.3 narrative touch-up + §3.16 reconciliation rewrite + §3.16.1 table cleanup + stray draft deletion | 4 edits |
| §4 | §4.1 state machine regenerate + §4.1A initial state + 5 test body rewrites (§4.2.1–§4.2.5) + 5 arch citation repairs (§4.3/4/5/6 + §4.6A) + §4.6B citation check | 10+ edits |
| §5 | §5.3 bus filter citation repair | 1 edit |
| §6 | 4 arch §10.N citation shifts + 2 State.ADJUDICATED/FORGE_FALLBACK removals | 6 edits |
| §7 | §7.2.5 rewrite | 1 edit |
| §8 | None | 0 |
| §9 | 2 arch §11.2/§11.3 citation swaps | 2 edits |
| §10 | §10.2 section rewrite (header + 2 tests) + §10.3 section rewrite (header + 1 test) | 2 large edits |
| §11 | 2 citation repairs (§11.4 Req-E → §6.5, §11.5 MCP → §10.3) | 2 edits |
| §12 | None | 0 |
| §13 | §13.3.2 Q-1 code block rename + §13.3.3 Q-1 table rows 12/13 | 2 edits |
| §14 | §14.3.4 docstring FORGE_FALLBACK + §14.7 FORGE_FALLBACK assertion + pre-draft verification of §14.3.1/§14.3.5 | 2–4 edits (pending verification) |
| §15 | §15.3B worked example rewrite | 1 edit |
| §16 | None | 0 |
| §17 | §17.1 prose rewrite + 3 version bumps | 4 edits |

**Estimated total Phase 2 edits: ~40.** Larger than v0.2's 19 edits but focused on a bounded, classified surface.

---

## §E. Items requiring Winston (architect) escalation

Three items in §4 need architectural clarification before Phase 2 can proceed cleanly — I cannot determine from arch §5.2 alone whether the following are architecturally present or v0.1 inventions:

1. **"Stability-based early termination" (§4.2.3):** arch §5.2 shows linear cycle_1 → cycle_2 → cycle_3 → publish/backtrack without an explicit stability check that short-circuits cycle 3. Is there an implicit stability check that should be added to arch §5.2, or is §4.2.3 a v0.1 invention that should be deleted?

2. **"Mid-cycle cancellation" (§4.6B tests):** arch §5.2 does not describe cancellation semantics. Is cancellation in arch §5.x somewhere I haven't read, or was it assumed from Runtime? If the latter, Runtime §4 probably has cancellation hooks that MAC inherits — the anchor should be `runtime/architecture.md §4` not MAC §5.

3. **"FORGE_FALLBACK behavioral path" (§4.2.5):** arch §5.6 describes Forge Fallback Handling and SQ-7 ordering. Is this a behavior-level fallback (apply R7 penalty + continue) or a state-machine-level fallback (transition to a dedicated state)? The v0.1 test assumed the latter. I'm reading arch §5.6 as the former, but Winston should confirm before §4.2.5 is re-anchored.

**Recommendation:** surface these 3 items to Winston for byte-for-byte arch §5 clarification BEFORE Phase 2 starts. If Winston confirms the behavioral-only reading (§4.2.3 delete, §4.6B re-anchor to Runtime, §4.2.5 behavioral-not-state), Phase 2 proceeds as planned. If Winston says the architecture needs to be extended (add states or early-termination semantics), that's an arch revision, not a test-strategy patch — and v0.3 stalls waiting for arch v0.2.

---

## §F. Coverage gaps — sections needing pre-draft deep read in Phase 2

Phase 1 was a classification scan, not a byte-for-byte read of every subsection. The following subsections were classified by pattern-matching and extrapolation rather than line-by-line reads. Phase 2 should do a targeted verification before drafting:

1. **§14.3.1 `FakeLLMJudge`** — likely has gate ID references and lookup table structure that may encode label assumptions
2. **§14.3.5 `FakeBenchmarkOutputs`** — gate ID references + benchmark harness lookup
3. **§7.10A Composite Worked Examples** — gate ID vectors, verify no label drift
4. **§15.4 Cycle/SQ/Benchmark Q Mapping** — cross-ref table, likely clean but unverified
5. **§13.5A / §13.5B / §13.6** coverage measurement details — classified (a) CLEAN but not read in full

None of these are expected to contain DIV-5-class drift (they're structural/mapping content), but the §N recalibration requires explicit verification rather than assumption.

---

## §G. Summary classification totals

| Class | Subsection count | Primary drift loci |
|---|---|---|
| (a) CLEAN | ~85 subsections | §1/§2/§3/§5(most)/§7(most)/§8/§9(most)/§10.1/§10.4/§11(most)/§12/§13(most)/§14(most)/§15(most)/§16/§17(most) |
| (b) LABEL DRIFT | ~6 subsections | §3.14.3, §3.16, §3.16.1, §17.3, §17.5, end marker |
| (c) SEMANTIC DRIFT | 0 new instances | All v0.1 semantic drift in §3 was closed by v0.2 DIV-4 rewrites |
| (d) CITATION DRIFT | ~14 subsections | §4.3, §4.4, §4.5, §4.6, §4.6A (×2), §4.6B, §5.3, §6.1, §6.2, §6.3, §6.4A (×1), §9.2.1, §9.4.1, §11.4, §11.5, §17.1 |
| (e) FABRICATION | ~8 subsections | §4.1, §4.1A, §4.2.1, §4.2.3, §4.2.4, §4.2.5, §6.4, §6.4A.1, §7.2.5, §10.2 (×2), §10.3 (×1), §14.3.4, §14.7, §15.3B |
| (f) FROZEN | ~15 subsections | §1.5, §14.3.1–§14.3.7, §13.3.x ratified content, §13.3.3.1 ratification block |

**Drift concentration:** §4 is the single largest drift hotspot (catastrophic — fabricated state machine). §6 is second (systematic off-by-one on arch §10.N citations). §10 is third (2 sections needing full rewrite per Special Handling).

**Phase 2 risk:** §4 depends on Winston clarification on 3 items (§E). If Winston is unavailable, Phase 2 can still proceed for §5–§17 and defer §4 to a sub-phase.

---

## §H. Phase 1 HOLD state

**No edits made to test-strategy.md during Phase 1.**

This inventory is the Phase 1 deliverable. Team-lead spot-check should verify 3 random subsection classifications against arch byte-for-byte before approving Phase 2 execution.

**Recommended spot-check targets** (I suggest the 3 hardest-to-verify cases):
1. **§4.1 FABRICATION claim** — verify by reading arch §5.2 lines 505–558 directly and confirming that none of `{IDLE, CYCLE_1_RUNNING, CYCLE_1_REVIEWED, CYCLE_2_RUNNING, CYCLE_2_REVIEWED, CYCLE_3_RUNNING, CYCLE_3_REVIEWED, ADJUDICATED, TERMINATED, FORGE_FALLBACK, HARD_FAIL}` appear.
2. **§6 arch §10.N citation shifts** — verify by reading arch §10.1, §10.2, §10.3, §10.4 headers directly and confirming Pi-Mono is §10.1, Memory is §10.2, Runtime is §10.3, Compression is §10.4, and §10.5 does not exist.
3. **§11.4 Req-E citation** — verify that arch §12 is Test Requirements (not Req-E) and arch §6.5 is Domain Guard Conditions (Req-E + SQ-5).

If all 3 classifications hold under spot-check, Phase 2 is cleared to execute.

**Not signaling Amelia.** Amelia continues to hold at 5.3 USR preload.

**Winston escalation open** on §4 items per §E.

**Murat out.**
