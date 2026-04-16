# MAC Test Strategy — Stage 5.2

**Version:** 0.3
**Status:** RATIFIED v0.3 — 2026-04-14 — fresh ratification replacing v0.1/v0.2 corrigendum stack; full-document drift reconciliation per DIV-1 through DIV-5; Q-1 allow-list nodeid rename applied; canonical IDs `MAC-T-GATE-R11-05` / `MAC-T-GATE-R12-05` preserved; 16-entry `no_waiver` allow-list preserved verbatim (entry IDs, count, OTEL provisional tags PENDING AUDIT at 5.5, self-reference all unchanged); Decisions 1/2/3 structure locked; S-Q1–S-Q4 ratified answers locked; binding for Stage 5.3 (Amelia implementation). See §1.7 v0.3 changelog for full reconciliation history.
**Author:** Murat, Test Architect (BMAD TEA)
**Date:** 2026-04-14
**Binding Inputs:**
- `_bmad-output/implementation-artifacts/praxis/mac/architecture.md` v0.1 (RATIFIED 2026-04-14)
- `_bmad-output/implementation-artifacts/praxis/mac/quality-rubric.md` §6 (R1–R12)
- `_bmad-output/implementation-artifacts/praxis/mac/benchmark-questions.md` §2 + §5 + §6 + §7 + §8
- `_bmad-output/implementation-artifacts/praxis/Pipeline.md` §5.2 (deliverable criteria)
**Stage 4 continuation:** This strategy is the direct continuation of `_bmad-output/implementation-artifacts/praxis/runtime/test-strategy.md` (v0.3, 5,950 lines, 204 test IDs) and inherits its marker vocabulary, fixture patterns, and test-ID conventions.
**Ratification target:** Stage 5.2 → Stage 5.3 (Amelia implements against this spec)

---

## §1 Context

### §1.1 Purpose

This document defines the test strategy for Stage 5 — the Multi-Agent Cognition (MAC) kernel at `praxis/kernel/mac/`. Per Pipeline.md §5.2, this is "the most intensive test design in the project": 12 gates, an evaluation harness, an adversarial corpus, a bootstrap loader, and a 3-cycle iteration controller with information asymmetry guarantees — all of which must ratify against `mac/architecture.md` §6.1's 12-gate catalog, `quality-rubric.md` §6 R1–R12, and `benchmark-questions.md` §2/§5/§6/§7/§8.

The strategy is the deliverable of Stage 5.2. It does NOT write code; it defines the contract Amelia implements at Stage 5.3. Every test carries a test ID, a marker set, a fulfillment criterion, and a double-anchored citation (both `quality-rubric.md §6 R{N}` AND `mac/architecture.md §6.1 row` for gate-level tests).

### §1.2 Universal Sequential Reference Reading (USR) Rule

Per the stage-gate discipline inherited from Runtime Stage 4.x, the preload phase of 5.2 verified sequential reading of:
1. `mac/architecture.md` v0.1 (ratified) — binding structure
2. `mac/quality-rubric.md` §1–§7 — gate definition authority
3. `mac/benchmark-questions.md` §2 + §5 + §6 + §7 + §8 — benchmark harness authority
4. `Pipeline.md` §5.2 — deliverable criteria
5. Stage 4 prior-art: `runtime/test-strategy.md` (5,950 lines), `runtime/architecture.md`, `memory/test-strategy.md`, `pi-mono/test-strategy.md`

The USR rule is reasserted here: every test in this strategy traces to at least one of the binding inputs via explicit citation. No invented tests. No orphan tests. When a test appears to require a new architectural primitive, the strategy STOPS and escalates — it does not silently extend the architecture.

### §1.3 Stage 4 Test Vocabulary Inherited

From `runtime/pyproject.toml:29–40` and `runtime/test-strategy.md §13`:

| Marker | Meaning | Inherited as-is |
|---|---|---|
| `critical` | Failure blocks release; deterministic | yes |
| `no_waiver` | Deterministic invariant; cannot be waived in any PR | yes (extended — see §13) |
| `asyncio_structural` | Async structural invariant (task group, cancellation) | yes |
| `f1_absorption` | Forge F1 absorption boundary test | yes |
| `f3_absorption` | Forge F3 absorption boundary test | yes |
| `integration` | Multi-component wire-up test | yes |
| `oqn_escalation_canary` | OQ-N escalation canary (Runtime convention) | yes |
| `r53_structural` | Req-5.3 structural invariant | yes |
| `static` | Collection-time / grep-based structural test | yes |
| `wall_clock` | Real-time sensitive test (uses `FrozenClock` to isolate) | yes |
| `asymmetry_structural` | Proxy/bus asymmetry structural invariant | yes (extended — see §5) |

**MAC-specific new markers** (registered in `praxis/kernel/mac/pyproject.toml` at 5.3):

| New Marker | Meaning |
|---|---|
| `mac_gate_calibration` | Gate calibration anchor test (deterministic or live-judge split) |
| `mac_benchmark_harness` | Benchmark harness test (unit vs nightly — see §7) |
| `mac_bootstrap_loader` | Bootstrap loader test (sidecar migration, idempotent re-run) |
| `mac_adversarial` | Adversarial test (Persona 3 gaming corpus) |
| `mac_self_consistency` | Self-consistency invariant test (cycle 2 determinism, reviewer independence) |
| `mac_label_registry` | Observability label-registry hard-fail test |
| `nightly_only` | Runs in nightly CI pipeline, NOT PR gate |
| `release_gate` | Runs on release candidate only; A4 Andrey-in-the-loop + full harness |

All MAC tests live under `tests/mac/` in the Praxis monorepo, with subdirectories per section (`tests/mac/gates/`, `tests/mac/cycle/`, `tests/mac/asymmetry/`, etc.) — see §14 for the full layout.

### §1.3A Why MAC's Test Strategy Is the "Most Intensive" in Praxis

Pipeline.md §5.2 calls this "the most intensive test design in the project." The reason is structural: MAC is the first Praxis kernel that combines all of the following:

1. **A 12-gate evaluation rubric** — each gate has its own scoring logic, calibration, and section routing. Multiplied by 5 standard test types (unit, calibration, routing, domain, edge), that's 60+ gate tests minimum.
2. **A 3-cycle iteration controller** — state machine, budget enforcement, parallelism, Forge fallback, telemetry, cancellation. Property-based testing over the state machine alone yields 5+ tests.
3. **An information-asymmetry guarantee** — Req-F two-step protocol, proxy asymmetry, bus filter. These are structural invariants that need both deterministic and live versions.
4. **An evaluation harness** — 30 scored runs, ADR-1 hybrid pass, ADR-3 Spearman, top-5 weighting. The harness has its own logic that needs unit tests separate from the gates.
5. **A bootstrap loader** — sidecar table, idempotent re-run, named contract events to Memory.
6. **An adversarial corpus** — Persona 3 gaming, R11/R12 probing, rotation protocol.
7. **An observability layer** — label registry hard-fail, dedup namespace, violation counter.
8. **Cross-stage `no_waiver` enforcement** — the OQ-TS-9 allow-list meta-test crosses the MAC/Runtime stage boundary.

Each of these eight concerns adds tests. The cumulative test count exceeds Runtime's 204 IDs because MAC has more concerns. If any of the eight is shortchanged, MAC's claim of "multi-agent cognition with quantitative quality" falls apart at the seam.

The total count of 211+ test IDs is NOT padding; it's the minimum to honor the architecture's commitments.

### §1.4 Decision Bake-In (Ratified)

Three binding decisions from the 5.2 preload approval are baked into this strategy as ratified answers (not flagged as assumptions):

- **Decision 1 — `no_waiver` expansion:** 10 tests carry `no_waiver`: the 8 gate calibration-anchor tests for R1/R2/R3/R4/R5/R7/R8/R11 (`MAC-T-GATE-R{N}-02`), plus the 2 structural calibration tests `MAC-T-GATE-R11-05` and `MAC-T-GATE-R12-05`. Items 9 (Req-F live reviewer) and 11 (Persona 3 live judge) split into deterministic sub-tests (`no_waiver`) + live sub-tests (`critical + asymmetry_structural` only). See §13.3.3 for the ratified allow-list and §3, §5, §10 for test details.
- **Decision 2 — OQ-TS-9 allow-list meta-test:** In-scope for 5.2. Spec lives in §13.3. Target path `tests/static/runtime/test_no_waiver_inventory.py` (crosses stage boundary intentionally). 14-entry allow-list (1 Runtime ratified + 2 Runtime provisional + 10 MAC new + 1 self-reference). Self-referential bootstrap property noted in §13.3.
- **Decision 3 — Soft questions resolved:** S-Q1 (bootstrap idempotency) → §8.4. S-Q2 (violation counter) → §9.3. S-Q3 (benchmark harness split) → §7.9. S-Q4 (A4 release gate) → §7.10. All four are ratified — do NOT re-debate.

### §1.5 Scope Boundaries

**IN SCOPE for 5.2 test strategy:**
- Unit, property, contract, integration, negative, adversarial, calibration tests for `praxis/kernel/mac/`
- Test-design spec for the allow-list meta-test `tests/static/runtime/test_no_waiver_inventory.py` (Decision 2)
- Test ID catalog, marker vocabulary, fixture interface contracts, execution strategy
- Coverage target, exclusion policy, CI budget, PR-gate vs nightly vs release-gate split

**OUT OF SCOPE for 5.2 (deferred to 5.3 or later):**
- Writing the actual test code (Stage 5.3 Amelia)
- Auditing the 2 Runtime OTEL tests at lines 41/62 (Stage 5.5 Alignment Review — team-lead)
- Running the full benchmark harness end-to-end with real LLMs (5.4 nightly CI)
- The manual Andrey-in-the-loop scoring step (out-of-band; only the automated math is tested — see §7.10)
- Changes to `mac/architecture.md` or `quality-rubric.md` (frozen inputs)

### §1.5A How This Strategy Inherits From Stage 4

Stage 4 produced `runtime/test-strategy.md` (5,950 lines, 204 test IDs). This MAC strategy inherits from Stage 4 in three concrete ways:

1. **Marker vocabulary inheritance.** Markers `critical`, `no_waiver`, `asyncio_structural`, `f1_absorption`, `f3_absorption`, `integration`, `oqn_escalation_canary`, `r53_structural`, `static`, `wall_clock`, `asymmetry_structural` are defined in `runtime/pyproject.toml:29–40` and reused without renaming. MAC adds 8 new markers prefixed with `mac_*` plus `nightly_only` and `release_gate`.

2. **Fixture pattern inheritance.** The Deterministic Replay Pattern at §4.5 inherits directly from `runtime/test-strategy.md §6.4`. The proxy asymmetry inherited test `MAC-T-ASYM-PROXY-05` (§5.2.5) inherits the S4.R-01 invariant from `runtime/test-strategy.md §6.3`. The xmin identity test `MAC-T-INT-COSTTRACKER-03` (§6.1.3) inherits F-13.C1 from `runtime/test-strategy.md §7.2`.

3. **Cross-stage `no_waiver` enforcement.** The OQ-TS-9 allow-list meta-test (§13.3) lives at `tests/static/runtime/test_no_waiver_inventory.py`, in the Runtime tests directory. This is intentional cross-stage placement — Runtime owns the static-runtime bucket, and the meta-test enforces `no_waiver` discipline across BOTH Runtime and MAC tests in a single allow-list. The 16 entries in §13.3.3 span both stages.

These inheritance points mean MAC does NOT re-invent the test infrastructure; it extends what Runtime built. The continuity is by design — the same Murat voice, the same disciplines, the same patterns.

### §1.6 Success Criterion for 5.2 Ratification

The team-lead spot-check at Stage 5.2 → 5.3 transition must be able to verify:
1. Every gate-level test has a double-anchored citation (`quality-rubric.md §6 R{N}` + `mac/architecture.md §6.1 row`).
2. Exactly 10 MAC tests are marked `no_waiver` — matching Decision 1's list.
3. The OQ-TS-9 allow-list meta-test spec contains 14 entries with correct source tags (§13.3).
4. All 4 S-Qs are baked in at their stated sections (§7.9, §7.10, §8.4, §9.3).
5. All 8 preload tensions appear as named subsections with their ratified resolutions (§13.1 gate checklist).
6. The strategy's §13.1 gate checklist maps every Pipeline.md §5.2 sub-check to a fulfilling section.

### §1.7 v0.1 → v0.3 Changelog (Fresh Ratification)

v0.3 is a team-lead-authorized **fresh ratification** replacing the v0.1 → v0.2 corrigendum stack. v0.1 (initial draft) was ratified 2026-04-14, then patched in v0.2 (corrigendum, also 2026-04-14) when DIV-1/2/3 surfaced, then re-ratified as v0.3 (also 2026-04-14) after a full-document drift scan surfaced DIV-4 and DIV-5 layers and a Q-1 allow-list rename necessity. v0.3 is the binding input for Stage 5.3 Amelia implementation. The 16-entry `no_waiver` allow-list (§13.3.3) is **preserved verbatim** at the canonical-ID level (`MAC-T-GATE-R{1..12}-XX` IDs unchanged, count = 16, OTEL provisional entries #2/#3 still PENDING AUDIT at 5.5, self-reference #16 unchanged); only the Python nodeid implementation strings for entries #12 and #13 are updated under Q-1 authorization. Decision 2, Decision 3, S-Q1–S-Q4 ratified answers, Option Y sidecar bootstrap, fake fixture interface contracts (§14.3), the asymmetry router (§5), Option X rejection, and R13 absence are **NOT modified** in v0.3.

**Detection chain (5 cascading STOPs across 3 ratification rounds):**

1. **DIV-1 (label drift) — Amelia detected at 5.3 USR preload.** v0.1 §3.1 Gate Catalog row for R1 cited "Faithfulness / Factual Accuracy" but `quality-rubric.md §6` line 211 and `mac/architecture.md §6.1` line 670 both say "Epistemic Calibration". All 12 rows diverged. Routing differed for 6 rows. Team-lead ratification Option R1: `architecture.md` wins, `quality-rubric.md §6` is upstream authority.

2. **DIV-2 (hard-fail fabrication) — Murat detected during v0.2 transcription-prep.** v0.1 §3.12.5 / §3.13.5 asserted `SafetyHardFailError` / `PolicyHardFailError` exception classes and "hard-fail gate" semantics tied to v0.1's R11=Safety / R12=Policy labels. Neither error class nor hard-fail gate semantics exist anywhere in `mac/architecture.md`. Murat STOPPED before writing edits.

3. **DIV-3 (Decision 1 prose miscitation) — Murat detected during v0.2 transcription-prep, same STOP as DIV-2.** v0.1 §1.4 Decision 1 bullet said "10 tests carry `no_waiver` (MAC arch §12.2 items 1, 2, 3, 4, 5, 6, 7, 8, 10, 12)". Arch §12.2 items 1–12 enumerate SQ invariants and Req snapshots (SQ-2 label registry, SQ-4 R8/R7 cap, etc.) — NOT MAC gate calibration tests. The v0.1 pointer pointed at unrelated content sharing ordinal positions. Same v0.2 STOP.

4. **DIV-4 (specialty test bodies in §3) — Murat detected mid-v0.2-execution.** During v0.2 §3 rewrites, 5 specialty `§3.x.5` tests had test bodies (assertions, fixture logic) anchored to v0.1 hallucinated semantics orthogonal to the ratified labels: §3.3.5 (R2 Question Fidelity vs v0.1 "cross-section consistency"), §3.4.5 (R3 Falsifiability vs v0.1 "task-context-free fallback"), §3.7.5 (R6 Decision Relevance Density vs v0.1 "confidence coherence"), §3.10.5 (R9 Evidence Impartiality vs v0.1 "novelty-vs-prior-work"), §3.11.5 (R10 Epistemic Scope Honesty vs v0.1 "owner/deadline/measurable"). Murat STOPPED mid-execution. Team-lead authorized DIV4-A C-2-style rewrites for all 5.

5. **DIV-5 (cross-section drift outside §3) — Murat detected mid-v0.2-execution after DIV-4.** Post-DIV-4 grep surfaced 4 additional drift surfaces outside §3: §4.2.4 hard-fail short-circuit state-machine test, §4.6B mid-cycle cancellation tests, §10.2/§10.3 adversarial Safety/Policy probes, §3.16/§13.3.2/§13.3.3 narrative leakage. Each was the same fabrication-iceberg pattern as DIV-2 propagated into other sections. Murat STOPPED — §N commitment was scoped to §3.2–§3.13, didn't cover §4/§10/cross-section narrative leakage. Team-lead authorized **T-2 fresh ratification** (replacing the v0.2 corrigendum stack with v0.3 full-document scan).

**Scope of v0.3 — DIV-1 through DIV-5 + Q-1 + 3 §E architectural escalations:**

#### DIV-1 — Label / routing / priority drift (12 gates × 3 columns + 6 routing migrations)

All 12 gate names, section routings, and priorities regenerated byte-for-byte from `mac/architecture.md §6.1` (lines 668–681) and §6.2 `GATE_SECTION_ROUTES` (lines 702–715). Priority column migrated from numeric "1/2" encoding to categorical Critical/High/Medium. Per-gate §3.x subsection titles, test descriptions, and `G-ROUTE` assertions rewritten against ratified labels. R7/R8 co-evaluation pair semantic text rewritten to describe "actionability cannot exceed reasoning traceability + 1"; the pair math `R8_effective = min(R8_raw, R7_raw + 1)` and SQ-7 ordering are UNCHANGED per arch §6.3 Pair 1.

| v0.1 (REMOVED v0.3 — label drift) | v0.3 ratified (arch §6.1 / rubric §6) | Arch anchor |
|---|---|---|
| "Faithfulness / Factual Accuracy" | Epistemic Calibration | §6.1 R1 line 670 |
| "Internal Consistency" (mis-assigned to R2 in v0.1) | Question Fidelity | §6.1 R2 line 671 |
| "Relevance to Task" | Falsifiability | §6.1 R3 line 672 |
| "Steelman Strength (Dissent Absorption)" | Steelman Completeness | §6.1 R4 line 673 |
| "Dissent Signal" | Dissent Preservation | §6.1 R5 line 674 |
| "Recommendation Confidence Coherence" | Decision Relevance Density | §6.1 R6 line 675 |
| "Evidence Density" | Reasoning Traceability | §6.1 R7 line 676 |
| "Citation Integrity" | Actionability Calibration | §6.1 R8 line 677 |
| "Novel Information Yield" | Evidence Impartiality | §6.1 R9 line 678 |
| "Recommendation Actionability" | Epistemic Scope Honesty | §6.1 R10 line 679 |
| "Safety / Harm Avoidance" | Scenario Coverage | §6.1 R11 line 680 |
| "Policy Compliance" (mis-assigned to R12 in v0.1) | Internal Consistency | §6.1 R12 line 681 |

**Routing migrations** (6 rows where `GATE_SECTION_ROUTES` differed in v0.1):
- R2: `("FULL",)` → `("RECOMMENDATIONS",)`
- R6: `("RECOMMENDATIONS",)` → `("L1",)`
- R7: `("FINDINGS",)` → `("L2",)`
- R8: `("L2_CITATIONS",)` → `("RECOMMENDATIONS",)`
- R10: `("RECOMMENDATIONS",)` → `("FULL",)`
- R11: `("FULL",)` → `("L2",)`

#### DIV-2 — Hard-fail fabrication (R11/R12 + §7.2.5 + §4.2.4 leakage)

v0.1 §3.12.5 `MAC-T-GATE-R11-05` asserted `with pytest.raises("SafetyHardFailError")` and v0.1 §3.13.5 `MAC-T-GATE-R12-05` asserted `with pytest.raises("PolicyHardFailError")`. Both exception classes and "hard-fail gate" semantics are fabrications: arch §6.1 marks R11 and R12 priority = High, not hard-fail; arch §12.2 does not define safety or policy hard-fail; neither error class appears anywhere in `mac/architecture.md`. The §7.2.5 `MAC-T-BENCH-SCORING-05` test asserted `composite is None AND result.status == "HARD_FAIL"` for `R11=1 OR R12=1` — same fabrication leaked into the benchmark harness. The §4.2.4 `MAC-T-CYCLE-STATE-04` test asserted a `State.HARD_FAIL` state-machine transition on R11 score=1 — same fabrication leaked into the cycle controller.

**v0.3 resolutions:**
- §3.12.5 REWRITTEN as Scenario Coverage property test (≥3 distinct scenarios with differentiated implications + observable trigger conditions). Test ID and allow-list entry #12 preserved.
- §3.13.5 REWRITTEN as direct cross-section contradiction detector (FINDINGS premise vs RECOMMENDATIONS conclusion premise denial, T1 specific text-span flagging). Test ID and allow-list entry #13 preserved.
- §7.2.5 RETIRED v0.3 (gap preserved at `MAC-T-BENCH-SCORING-05`); §7.2.4 already covers the all-1 → 20.0 minimum-composite boundary correctly.
- §4.2.4 REWRITTEN as second-consecutive-Critical-failure → `FAILED` test, anchored on arch §5.2 footnote (lines 555–557). Test ID preserved.
- §13.4 table row updated to drop "+ hard-fail" language.

**REMOVED v0.3 — fabricated, no architectural anchor:** `"SafetyHardFailError"`, `"PolicyHardFailError"`, `"State.HARD_FAIL"`, `"hard-fail gate — scores of 1 are blocking releases, not just down-weighted"`, `"composite is None AND result.status == 'HARD_FAIL'"`.

#### DIV-3 — Decision 1 prose miscitation (§1.4 + §13.1 + 10 per-gate callouts)

v0.1 §1.4 said "10 tests carry `no_waiver` (MAC arch §12.2 items 1, 2, 3, 4, 5, 6, 7, 8, 10, 12)" and §13.1 row cited "`mac/architecture.md §12.2 items 1-8, 10, 12`". Arch §12.2 (lines 1875–1892) enumerates SQ-2 label registry hard-fail (4 tests in §11.1) / SQ-4 R8-R7 cap / SQ-5 DomainClass grep / SQ-7 Forge ordering / SQ-8 dedup_key prefix / Req-A label snapshot / Req-B routing snapshot / Req-D anchor SHA256 / Req-F protocol / InfoAsym ReviewerMemoryProxy AttributeError / Persona 3 gaming detection / R13 absence — NOT MAC gate calibration tests. The pointer was wrong.

**v0.3 repairs:**
- §1.4 Decision 1 bullet rewritten with self-contained test-ID enumeration.
- §13.1 row citation column changed to `§13.3.3 ratified allow-list entries 4–13 (self-contained; see §1.4 prose)`.
- 10 per-gate `MAC-T-GATE-R{N}-02` callouts in §3.2.2/§3.3.2/§3.4.2/§3.5.2/§3.6.2/§3.8.2/§3.9.2/§3.12.2 + §3.12.5/§3.13.5 repaired to "Decision 1 — see §1.4 and §13.3.3 entry #{N}".
- §13.3.2 Python code block inline comments updated.
- §13.3.3 enumerated table descriptive column updated to gate-anchored phrasing (R1 calibration anchor, etc.).
- §17.1 prose rewritten with self-contained Decision 1 references.

**REMOVED v0.3 — miscitation:** `"MAC arch §12.2 items 1, 2, 3, 4, 5, 6, 7, 8, 10, 12"`, `"mac/architecture.md §12.2 items 1-8, 10, 12"`.

#### DIV-4 — Specialty test bodies orthogonal to ratified labels (5 §3.x.5 tests)

5 specialty `§3.x.5` tests in v0.1 had test bodies anchored to v0.1 hallucinated semantics. Under ratified labels these tests would fail correctness — the assertions reference fixture properties that are not architectural concerns of the relabeled gate.

| Subsection | v0.1 test body (REMOVED v0.3) | v0.3 rewrite (arch anchor) |
|---|---|---|
| §3.3.5 `MAC-T-GATE-R2-05` | "R2Gate must evaluate consistency across ALL sections simultaneously"; `fixture.full_document_tokens` assertion | Question Fidelity OR-logic + 5/5 meta-evaluation: 4 fixtures (verbatim / named-reformulation / tangent-unnamed / meta-eval). Anchor: arch §6.1 R2 |
| §3.4.5 `MAC-T-GATE-R3-05` | "Task-context-free fallback"; `task_context == None → score=1` | Falsifiability monotonicity property: Hypothesis property over `(n, k)` count of conclusions with observable invalidation conditions. Anchor: arch §6.1 R3 |
| §3.7.5 `MAC-T-GATE-R6-05` | "Confidence-stated vs confidence-implied coherence"; `[RECOMMENDATIONS]` hedge detection | L1 density differential (padded vs lean L1, identical L2): assert R6(lean) > R6(padded); routing check via FakeLLMJudge.last_call.input. Anchor: arch §6.1 R6 (L1 only) |
| §3.10.5 `MAC-T-GATE-R9-05` | "Novelty-vs-prior-work detector"; `prior_work_corpus_ref` parameter; `novel_fraction` Hypothesis range | Evidence Impartiality proportionality + STEELMAN/DISSENT exemption: identical FINDINGS, vary recommendation strength (under-committed/proportional/over-committed); STEELMAN exemption check. Anchor: arch §6.1 R9 (FINDINGS only) |
| §3.11.5 `MAC-T-GATE-R10-05` | "Owner/deadline/measurable criterion check"; 2³ Hypothesis property over `(has_owner, has_deadline, has_measurable)` | Epistemic Scope Honesty 2² property + boilerplate detection: `(has_specific_exclusion, has_specific_blindspot)` with boilerplate sub-test per rubric §6 R10 "boilerplate fails". Anchor: arch §6.1 R10 |

Test IDs preserved (`MAC-T-GATE-R2-05`, `MAC-T-GATE-R3-05`, `MAC-T-GATE-R6-05`, `MAC-T-GATE-R9-05`, `MAC-T-GATE-R10-05`); none of the 5 are in the 16-entry allow-list, so no allow-list impact. R7/R8 co-eval semantic text in §3.5/§3.6/§3.8/§3.9 rewritten in DIV-1 scope.

**REMOVED v0.3 — DIV-4 fixture keywords (these strings have 0 occurrences outside this changelog):** `"fixture.full_document_tokens"`, `"task_context == None"`, `"novel_fraction"`, `"has_owner"`, `"prior_work_corpus_ref"`.

#### DIV-5 — Cross-section drift outside §3 (§4 state machine + §6 §10.N off-by-one + §10.2/§10.3 adversarial + §3.16 narrative + §15/§17 leakage)

The largest single drift surface in v0.1 was §4.1 — a fabricated state machine. v0.1 §4.1 listed states `{IDLE, CYCLE_1_RUNNING, CYCLE_1_REVIEWED, CYCLE_2_RUNNING, CYCLE_2_REVIEWED, CYCLE_3_RUNNING, CYCLE_3_REVIEWED, ADJUDICATED, TERMINATED, FORGE_FALLBACK, HARD_FAIL}` with transitions including `* → HARD_FAIL (on R11 or R12 score=1)`. **None of these 11 state names exist in arch §5.2.** Arch §5.2 (lines 505–558) defines 9 states: `interpret, decompose, cycle_1_produce, cycle_2_review, cycle_3_verify, backtrack_set, publish, complete, failed`, with terminal transitions via `BudgetExceededError → failed` or second-consecutive Critical gate failure → `failed`. The fabricated state names propagated into §4.1A (initial state), §4.2.1–§4.2.5 (5 STATE tests), §4.6B (3 CANCEL tests built on a non-existent `controller.cancel()` API), §6.4/§6.4A.1 (`State.ADJUDICATED` / `State.FORGE_FALLBACK` leakage), §14.3.4 docstring, §14.7 example, §15.3B worked example.

**v0.3 §4 reconciliation:**
- §4.1 REGENERATED byte-for-byte from arch §5.2 (9 states, linear cycle flow, single backtrack loop, terminal `FAILED` per footnote).
- §4.1A initial state `State.IDLE` → `State.INTERPRET`.
- §4.2.1 rewritten: `{ADJUDICATED, TERMINATED, HARD_FAIL}` → `{COMPLETE, FAILED}` reachability.
- §4.2.2 narrative alignment to regenerated §4.1.
- **§4.2.3 RETIRED** (per §E item 1): "stability-based early termination" path is fabricated; arch §5.2 has no stability check. Test ID `MAC-T-CYCLE-STATE-03` left as gap.
- **§4.2.4 REWRITTEN** (per §E item 1): no longer "hard-fail short-circuit"; now exercises arch §5.2 footnote second-consecutive-Critical-failure → `FAILED` path. Test ID preserved.
- **§4.2.5 REWRITTEN as cycle-level behavioral integration** (per §E item 3): no `State.FORGE_FALLBACK`; now asserts arch §5.6 + §6.3 SQ-7 step 3 behavioral path through normal §5.2 states; complements §3.8.5 at cycle level.
- §4.3/§4.4/§4.5/§4.6/§4.6A: 8+ arch §5.N citation repairs — `§5.3 budget` → `§5.7 ResourceBudget`; `§5.4 CycleContext` → `§5.5 Backtracking` + `§5.3 Phase Runner`; `§5.5 parallelism` → `§5.4 Cycle 2 Parallelism`; `§12.5 SQ-7` → `§6.3 SQ-7 ordering`; `§11.3 metric catalog` → `§11.2 Metric Catalog`; `§11.2 dedup namespace` → `§11.3 Linkage to Memory's TelemetryEvent`.
- **§4.6B RETIRED** (per §E item 2): all 3 `MAC-T-CYCLE-CANCEL-*` tests deleted. v0.1 described a `controller.cancel(reason="user_requested")` API that does not exist in arch §5 OR Runtime §4 (narrow Runtime §4.3 read confirmed; cancellation is via `BudgetExceededError` path tied to spawn lifecycle, not user action). Budget-driven cancellation cleanup is already covered by §4.3 budget tests. Test IDs `MAC-T-CYCLE-CANCEL-01/02/03` left as gaps.
- §4.8 test count: 24 → 20 (−1 STATE-03 retired, −3 CANCEL retired).

**v0.3 §6 systematic §10.N off-by-one repair** (4 citations + 2 state leakage removals): v0.1 was off by one on every arch §10.N citation. Arch §10.1 = Pi-Mono Integration; §10.2 = Memory; §10.3 = Runtime; §10.4 = Compression; **§10.5 does not exist**. v0.1 cited these as §10.2/§10.3/§10.4/§10.5 respectively. Repairs: §6.1.1 §10.2 → §10.1; §6.2.1 §10.3 → §10.2; §6.3.1/§6.3.2 §10.4 → §10.3; §6.4.1 §10.5 → §10.4 (fabrication). §6.4A.1 `State.ADJUDICATED` → `State.COMPLETE` + arch §5.2 progression narrative. §6.4A.2 `arch §10.4 multi-tenant isolation` → `arch §7.2 Proxy binding to Runtime §4.1` + `§10.3 Runtime`.

**v0.3 §9 / §11 citation repairs:**
- §9.2.1 / §9.4.1: §11.2 ↔ §11.3 swap (arch §11.2 = Metric Catalog, §11.3 = TelemetryEvent Linkage, dedup-key format inside §11.3).
- §11.4.1: `arch §12 Req-E` → `arch §6.5 Domain Guard Conditions (Req-E + SQ-5)`.
- §11.5.1: `arch §10.4 MCP shape guard` → `arch §10.3 Runtime Integration`.
- §15.4: 4 arch §5.N citations (same off-by-one as §4) + `arch §12.5 stakeholder-questions` → `§6.5 + §6.3` self-contained.
- §5.3: `arch §7.3 Event-bus role filter` → `runtime/architecture.md §7.5 Layer 2 communication-bus filtering` + `mac/architecture.md §7.5 Symmetric Asymmetry Boundary` (arch §7.3 is "Information Hiding", not bus filter).

**v0.3 §10.2/§10.3 adversarial REWRITE** (per team-lead Special Handling item 2):
- §10.2 header: "Adversarial R11 Safety Probing" → "Adversarial R11 Scenario Coverage Probing".
- §10.2.1 `MAC-T-ADV-R11-01`: "Jailbreak prompts trigger R11 hard-fail" → **single-scenario bias disguised as multi-scenario** (3 headers, same future, R11 ≤ 2).
- §10.2.2 `MAC-T-ADV-R11-02`: "Indirect injection attempts blocked" → **manufactured non-falsifiable trigger conditions** (3 distinct scenarios, unfalsifiable triggers).
- §10.3 header: "Adversarial R12 Policy Probing" → "Adversarial R12 Internal Consistency Probing".
- §10.3.1 `MAC-T-ADV-R12-01`: "Policy-violating outputs trigger R12 hard-fail" → **subtle cross-section contradiction** (FINDINGS 60% confidence / RECOMMENDATIONS certain / STEELMAN refuted-but-unacknowledged; T1 direct-contradiction text-span flagging).
- **Out-of-scope declaration** added: jailbreak resistance, prompt injection, PII disclosure prevention, copyright-infringement detection are NOT gate-level concerns under the ratified 12-gate catalog. If Praxis needs jailbreak resistance or policy-compliance gating, these belong to a pre-gate input-filtering layer or post-gate output-filtering layer; architectural decision deferred to Stage 6 or separate RFC.

**v0.3 §3.16 / §3.16.1 / §17.1 / §16 narrative reconciliation:**
- §3.16 reconciliation bullets and §3.16.1 table column rewritten to drop "Decision 1 item N" arch §12.2 framing; now self-contained gate-anchored phrasing.
- **Stray editorial draft DELETED v0.3** at v0.1 §3.16.1 lines 1029–1033: `"Wait — this needs a precise reconciliation, because the brief asks for '10 MAC new entries' in the allow-list. Let me re-read Decision 2 carefully and commit to the correct count. AUTHORITATIVE READING OF DECISION 2: ... Resolution (RATIFIED 2026-04-14): ..."` — this was an in-line authorial thought that escaped into v0.1 ratification. Editorial cleanup authorized.
- §17.1 prose rewritten with self-contained Decision 1 references and v0.3 corrigendum context.
- **§17.2B item 4 REMOVED v0.3** (orphaned after §4.6B retirement): `"4. MAC-T-CYCLE-CANCEL-* tests in §4.6B — do they belong here or in Stage 6 (full async surface)? ..."` — orphaned residual OQ pointing at retired tests.

**v0.3 §14.3.4 / §14.7 / §15.3B FORGE_FALLBACK state leakage cleanup:**
- §14.3.4 `FakeCompressor` docstring: "to force MAC into FORGE_FALLBACK state" → behavioral reference to arch §5.6 + §6.3 SQ-7 step 3.
- §14.7 example: `assert result.state == State.FORGE_FALLBACK` → `assert result.final_state == State.COMPLETE` + R7 penalty assertion + behavioral telemetry event name.
- §15.3B worked example: §4.1 cross-reference + arch §5.2 / §12.5 citation drifts repaired.

**v0.3 §13.5A.1 hypothetical CI output example update:** `praxis/kernel/mac/cycle/iteration_controller.py:217-220 (cancellation cleanup)` → `praxis/kernel/mac/gates/r7.py:44-47 (Forge penalty post-co-eval-cap path per arch §6.3 SQ-7 step 3)`. Cancellation cleanup reference orphaned by §4.6B retirement; Forge penalty post-co-eval-cap is a real architectural concern that better illustrates the "uncovered subtle path" pedagogical purpose.

#### Q-1 — Allow-list Python nodeid rename (canonical IDs preserved)

The 16-entry §13.3.3 allow-list contains `MAC-T-GATE-R11-05` and `MAC-T-GATE-R12-05` as ratified canonical IDs (entries #12 and #13). v0.1/v0.2 implemented these as Python function names `test_mac_t_gate_r11_05_hard_fail_short_circuit` / `test_mac_t_gate_r12_05_hard_fail_policy` — embedding the fabricated hard-fail semantics. After the v0.2 C-2 rewrites of §3.12.5 / §3.13.5, the function names contradicted their own test bodies (a "scenario_coverage_property" test inside a function called "hard_fail_short_circuit"). v0.3 Q-1 authorization: rename Python nodeids to match the rewritten semantics. **Canonical allow-list IDs preserved.** 16-entry count preserved. OTEL provisional entries #2/#3 preserved with PENDING AUDIT tag. Self-reference entry #16 preserved.

| Allow-list entry | v0.1/v0.2 nodeid (REMOVED v0.3) | v0.3 nodeid |
|---|---|---|
| #12 (`MAC-T-GATE-R11-05`) | `test_mac_t_gate_r11_05_hard_fail_short_circuit` | `test_mac_t_gate_r11_05_scenario_coverage_property` |
| #13 (`MAC-T-GATE-R12-05`) | `test_mac_t_gate_r12_05_hard_fail_policy` | `test_mac_t_gate_r12_05_direct_contradiction_detector` |

#### Three §E architectural escalations resolved (no Winston handoff)

Team-lead adjudicated all 3 §E items directly based on byte-for-byte arch §5.2 reads + Murat's §B arch citation index + a narrow Runtime §4.3 read. Winston was not in the loop:

1. **§4.2.3 stability-based early termination** — DELETED. No stability short-circuit exists in arch §5.2.
2. **§4.6B mid-cycle cancellation** — DELETED (all 3 tests). User-initiated `controller.cancel()` API does not exist in arch §5 or Runtime §4. Budget-driven cancellation already covered by §4.3.
3. **§4.2.5 FORGE_FALLBACK state vs behavior** — REWRITTEN as cycle-level behavioral integration, anchored on arch §5.6 + §6.3 SQ-7 step 3. Not a state transition; not a duplicate of §3.8.5 (gate unit) but the cycle-level wire-up complement.

#### Test count changes (v0.2 → v0.3)

- §4 cycle tests: 24 → 20 (−1 STATE-03 retired, −3 CANCEL-01/02/03 retired)
- §7 evaluation harness: −1 SCORING-05 retired
- §3 gate tests: count unchanged (5 §3.x.5 specialty tests rewritten in place, IDs preserved)
- §10 adversarial: count unchanged (3 tests rewritten in place, IDs preserved)
- All other sections: count unchanged
- **Net change: −5 test IDs total** (4 from §4, 1 from §7); replaced with 5 retirement gap markers documenting deletion rationale.

#### Scope expansion acknowledgment

v0.3 touches ratified content in §1.4 Decision 1 prose, §13.4 table row, §13.3.2 / §13.3.3 allow-list nodeid strings (Q-1), §3.12.5 / §3.13.5 / §3.3.5 / §3.4.5 / §3.7.5 / §3.10.5 / §3.11.5 test bodies, §4.1 state machine definition, §4.2.1–§4.2.5 cycle state tests, §4.6B cancellation tests (deleted), §7.2.5 hard-fail test (deleted), §10.2 / §10.3 adversarial test bodies. Authorization rationale: every touched piece of "ratified" content was either (a) incoherent with upstream arch (§4.1 fabricated state machine, §3.12.5/§3.13.5 fabricated exception classes, §10.2/§10.3 fabricated safety semantics), (b) based on miscitation (§1.4 Decision 1 prose, §13.4 row), or (c) implementing fabricated semantics in nodeid strings (Q-1). The corrected content is strictly more arch-anchored than v0.1/v0.2. The 16-entry allow-list at the canonical-ID level is preserved verbatim; only Python implementation strings change under Q-1.

#### Trust recalibration governance lesson

**Partial-scope agent commitments miss cross-section fabrication leakage.** Murat's §N commitment in the v0.2 work was scoped to §3.2–§3.13 — execution-correct within scope but blind to §4 / §10 / §3.16 / §13.3.2 / §15 leakage. The cascading STOP discipline (DIV-1 → DIV-2 → DIV-3 → DIV-4 → DIV-5 across 3 ratification rounds) was textbook detection; the root cause was scope horizon. Going forward, agent scope commitments for document patches MUST cover the full document (every section, every subsection), not partial scopes. Phase 1 produces a complete drift inventory before any edits; team-lead spot-checks the inventory before approving Phase 2 execution. This costs more upfront but is strictly cheaper than N rounds of cascading STOPs. See `memory/feedback_preload_first_gating.md` for the layered-iceberg lesson.

**v0.3 fresh ratification complete:** 2026-04-14. Binding for Stage 5.3 (Amelia implementation) on team-lead final spot-check clearance + Phase 3 (Pipeline.md flip + memory updates).

---

## §2 Test Taxonomy

### §2.1 Test Families

MAC tests are grouped into 10 families. Each family has a primary section in this document, a target subdirectory, and a canonical marker set.

| Family | Section | Subdirectory | Canonical markers | Rough count |
|---|---|---|---|---|
| Gate-level | §3 | `tests/mac/gates/` | `critical` + per-R{N} markers | 70+ |
| 3-Cycle iteration | §4 | `tests/mac/cycle/` | `critical`, `mac_self_consistency` | 30+ |
| Information asymmetry | §5 | `tests/mac/asymmetry/` | `asymmetry_structural`, `critical` | 15+ |
| Integration | §6 | `tests/mac/integration/` | `integration`, `wall_clock` | 25+ |
| Evaluation harness | §7 | `tests/mac/benchmark/` | `mac_benchmark_harness`, `nightly_only`, `release_gate` | 35+ |
| Bootstrap loader | §8 | `tests/mac/bootstrap/` | `mac_bootstrap_loader` | 15+ |
| Observability | §9 | `tests/mac/observability/` | `mac_label_registry`, `critical` | 15+ |
| Adversarial | §10 | `tests/mac/adversarial/` | `mac_adversarial`, `nightly_only` (where live) | 20+ |
| Negative | §11 | `tests/mac/negative/` | `static`, `critical` | 15+ |
| Calibration (drift canary) | §12 | `tests/mac/calibration/` | `mac_gate_calibration`, `nightly_only` | 24 (12 gates × 2 anchors) |
| **Total (minimum)** | | | | **264+** |

The total test count exceeds Runtime's 204 test IDs, consistent with Pipeline.md §5.2's "most intensive test design in the project" framing.

### §2.2 Test Tier Definitions

From `mac/architecture.md` §12.4 (binding):

- **Tier 1 — Deterministic unit / property / contract tests.** Pure. No LLM. Use fake fixtures (see §14.3). Run on every PR. Fast (<60s per family).
- **Tier 2 — Integration tests.** Wire up real Postgres via testcontainers, real Pi-Mono CostTracker, real Memory proxy scaffolding. No live LLM calls — use `FakeLLMJudge` / `FakeReviewerAgent`. Run on every PR. Medium (<5 min total).
- **Tier 3 — Live-judge calibration + full benchmark harness.** Real LLM calls. Runs in the nightly CI pipeline ONLY. Cost budget documented in §12.3. NOT in PR gate.
- **Tier 4 — Release gate.** A4 Andrey-in-the-loop fixture verification + full 30-score benchmark replay. Runs once per release candidate. NOT in PR gate.

### §2.3 Marker Semantics and `no_waiver` Discipline

`no_waiver` marks a deterministic invariant that cannot be waived in any PR. The marker is enforced at test collection time by the OQ-TS-9 allow-list meta-test (see §13.3). Live-judge tests CANNOT carry `no_waiver` because live judges drift (Decision 1 structural boundary). The split for items 9 and 11 is explicit:

- **Req-F (arch §12.2 item 9):** deterministic sub-test `MAC-T-ASYM-R-F-02` (schema-only check) carries `no_waiver`. Live sub-test `MAC-T-ASYM-R-F-03` (real LLM run) carries `critical + asymmetry_structural` ONLY.
- **Persona 3 (arch §12.2 item 11):** deterministic sub-test `MAC-T-ADV-P3-01` (fixture corpus inventory) carries `no_waiver`. Live sub-test `MAC-T-ADV-P3-02` (real judge run) carries `critical + mac_adversarial` ONLY.

### §2.4 Citation Discipline (Mandatory)

Every test in this strategy has:
- A **test ID** matching the `MAC-T-{section}-{seq}` schema (see §15).
- A **primary anchor** to `quality-rubric.md §6 R{N}` where applicable.
- A **secondary anchor** to `mac/architecture.md §X.Y` or `benchmark-questions.md §X`.
- A **fulfillment criterion** stated as an assertion (not prose).
- A **marker set**.

Test rows that fail to double-anchor are REJECTED by the test architect. The citation auditor (Murat, this document) enforces this rule at ratification.

### §2.5 Test Pyramid (Effective)

```
                    ┌─────────────────────┐
                    │  Tier 4 release     │  ~5 tests (A4, 30-score)
                    │  (release gate)     │
                    └─────────────────────┘
                ┌───────────────────────────┐
                │  Tier 3 live-judge nightly │  ~30 tests (12-gate canary × 2 + 6 live reviewer/adv)
                │  (nightly_only)            │
                └───────────────────────────┘
            ┌───────────────────────────────────┐
            │  Tier 2 integration (PR gate)      │  ~55 tests (Pi-Mono/Memory/Runtime/Forge wire-ups)
            │                                    │
            └───────────────────────────────────┘
    ┌───────────────────────────────────────────────┐
    │  Tier 1 unit + property + contract (PR gate)   │  ~175 tests (gates, cycle, bootstrap, obs, negative, cal)
    │                                                │
    └───────────────────────────────────────────────┘
```

Ratio: ~66% Tier 1, ~21% Tier 2, ~11% Tier 3, ~2% Tier 4. Matches Runtime's pyramid with slightly higher Tier 3 share due to MAC's evaluation-harness and live-judge calibration demands.

---

## §3 Gate-Level Tests (R1–R12)

This section specifies tests for the 12 gates defined in `mac/architecture.md` §6.1 and `quality-rubric.md` §6 R1–R12. Every gate has at minimum **5 tests** (6 for gates with co-eval constraints):

1. **Unit scoring test** — `FakeLLMJudge` returns a deterministic score; assert gate outputs the correct effective score.
2. **Calibration anchor test (deterministic)** — `FakeLLMJudge` replays `benchmark-questions.md §5` score-2 and score-4 anchors; assert bucketing.
3. **Section-routing test** — asserts the gate is applied only to the section(s) listed in `mac/architecture.md §6.1` (via `GATE_SECTION_ROUTES` snapshot).
4. **Co-eval cap test** (where applicable) — asserts paired-gate min-cap semantics (R7/R8 and R4/R5).
5. **Domain-guard test** — asserts `DomainClass` enum routes gates to the correct domain-specific config.
6. **Drift canary (nightly only, live judge)** — specified in §12, NOT in §3; referenced here for completeness.

### §3.1 Gate Catalog Anchor Snapshot

The 12-gate catalog is defined in `mac/architecture.md §6.1` with rows indexed R1–R12. This strategy references each gate by `R{N}` and, where disambiguation is needed, by the catalog's name.

| Gate | Name (from arch §6.1) | Rubric anchor | Section applied | Priority | Co-eval pair |
|---|---|---|---|---|---|
| R1 | Epistemic Calibration | quality-rubric.md §6 R1 | Full document | Critical | — |
| R2 | Question Fidelity | quality-rubric.md §6 R2 | `[RECOMMENDATIONS]` | Critical | — |
| R3 | Falsifiability | quality-rubric.md §6 R3 | Full document | High | — |
| R4 | Steelman Completeness | quality-rubric.md §6 R4 | `[STEELMAN]` | Critical | (R5, R4) |
| R5 | Dissent Preservation | quality-rubric.md §6 R5 | `[DISSENT]` | Critical | (R5, R4) |
| R6 | Decision Relevance Density | quality-rubric.md §6 R6 | L1 only | Medium | — |
| R7 | Reasoning Traceability | quality-rubric.md §6 R7 | L2 main body | Critical | (R8, R7) |
| R8 | Actionability Calibration | quality-rubric.md §6 R8 | `[RECOMMENDATIONS]` | High | (R8, R7) |
| R9 | Evidence Impartiality | quality-rubric.md §6 R9 | `[FINDINGS]` only | Medium | — |
| R10 | Epistemic Scope Honesty | quality-rubric.md §6 R10 | Full document | High | — |
| R11 | Scenario Coverage | quality-rubric.md §6 R11 | L2 main body | High | — |
| R12 | Internal Consistency | quality-rubric.md §6 R12 | Full document | High | — |

**`MAC-T-GATE-CATALOG-SNAPSHOT-01`** (`static`, `no_waiver` candidate NO — structural but not invariant-critical enough; `critical` only)
- **Purpose:** Assert the 12-gate catalog in `mac/architecture.md §6.1` matches a frozen byte-equality snapshot `tests/mac/gates/snapshots/gate_catalog_v0_1.yaml`.
- **Anchor:** `mac/architecture.md §6.1` (primary), `quality-rubric.md §6` (secondary).
- **Fulfillment:** `parse_gate_catalog(load_architecture_md()) == load_yaml(snapshot_path)`. Byte-equality on `(gate_id, name, rubric_anchor, section_applied, priority, co_eval_pair)` tuples.
- **Marker set:** `static`, `critical`.
- **Rationale for NO no_waiver:** this is a structural sentinel, but the snapshot is updated with architecture v-bumps; `no_waiver` would block legitimate architecture evolution.

### §3.1A Gate Test Pattern Macros — Shared Setup

Every gate-level test in §3.2–§3.13 follows a canonical pattern. To keep the 73-test catalog readable, the patterns are specified here once; individual test rows cite the pattern and vary only the inputs.

#### §3.1A.1 Pattern G-UNIT — Unit scoring test

**Pattern name:** `G-UNIT({gate_id}, {fixture_id}, {expected_score})`

**Setup:**
1. Instantiate `FakeLLMJudge` with a lookup table containing a single entry:
   `(gate_id, fingerprint(fixture.text)) → JudgeResponse(score=expected_score, rationale="§3 {gate_id} unit fixture")`
2. Instantiate `{gate_id}Gate(judge=FakeLLMJudge(table))`.
3. Load `fixture` via `FixtureLoader.load("§3.x", fixture_id)`.

**Assertions:**
- `gate.score(output=fixture).effective == expected_score`
- `FakeLLMJudge.call_log == [(gate_id, fp(fixture.text))]` (exactly one call)
- `telemetry.last_event.name == f"mac.gate.{gate_id.lower()}.scored"`
- `telemetry.last_event.attributes == {"gate_id": gate_id, "score": expected_score, "forge_degraded": False}`

**Failure mode:** `AssertionError` with the actual vs expected score, plus the `FakeLLMJudge.call_log` contents for diagnosis.

#### §3.1A.2 Pattern G-CAL — Calibration anchor test

**Pattern name:** `G-CAL({gate_id}, {score_level_2_anchor_id}, {score_level_4_anchor_id})`

**Setup:**
1. Load both anchors from `benchmark-questions.md §5 {gate_id}` via `CalibrationAnchorLoader.load(gate_id)`. Two fixtures: one score-2, one score-4.
2. Build `FakeLLMJudge` lookup table with BOTH anchors pre-scored:
   `(gate_id, fp(anchor_2.text)) → JudgeResponse(score=2, rationale="§5 anchor_2")`
   `(gate_id, fp(anchor_4.text)) → JudgeResponse(score=4, rationale="§5 anchor_4")`
3. Instantiate `{gate_id}Gate(judge=FakeLLMJudge(table))`.

**Assertions:**
- `gate.score(output=anchor_2).effective <= 2`
- `gate.score(output=anchor_4).effective >= 4`
- `FakeLLMJudge.call_log` has exactly 2 entries, one per anchor.

**Marker set:** `critical`, `mac_gate_calibration`, and `no_waiver` if and only if Decision 1 lists the gate in items 1–8, 10, or 12.

**Failure mode:** If bucketing fails, print the anchor text excerpt and both the expected and actual bucket. Hard-fail; no retry.

#### §3.1A.3 Pattern G-ROUTE — Section routing snapshot

**Pattern name:** `G-ROUTE({gate_id}, {expected_selector})`

**Setup:**
1. Load `GATE_SECTION_ROUTES` from `praxis.kernel.mac.cycle.section_router`.
2. Load snapshot from `tests/mac/gates/snapshots/section_routes_v0_1.yaml`.

**Assertions:**
- `GATE_SECTION_ROUTES[gate_id] == expected_selector` (enum equality)
- Byte-equality of the serialized routes against the snapshot.

**Marker set:** `static`, `critical`.

#### §3.1A.4 Pattern G-DOMAIN — Domain guard test

**Pattern name:** `G-DOMAIN({gate_id})`

**Setup:**
1. For each `DomainClass` value in `{TECHNICAL, LEGAL, MEDICAL, POLICY, GENERAL}` (5 per preload item 6):
   - Construct `{gate_id}Gate(judge=FakeLLMJudge(...), domain=DomainClass.X)`
   - Inspect `gate.judge_prompt.source` attribute.

**Assertions:**
- For each domain, `gate.judge_prompt.source == f"§6.3 {gate_id} {domain.name.lower()}_variant"`.
- No two domains yield the same source (uniqueness test).

**Marker set:** `critical`, `mac_gate_calibration`.

#### §3.1A.5 Pattern G-FORGE — Forge degradation path

**Pattern name:** `G-FORGE({gate_id}, {is_in_penalty_set})`

**Setup:**
1. Build `FakeLLMJudge` returning score=4 for the fixture.
2. Instantiate `{gate_id}Gate`.

**Assertions (penalty set member, e.g., R7):**
- `gate.score(fixture, forge_degraded=False).effective == 4`
- `gate.score(fixture, forge_degraded=True).effective == 3`

**Assertions (non-member, e.g., R1):**
- `gate.score(fixture, forge_degraded=False).effective == 4`
- `gate.score(fixture, forge_degraded=True).effective == 4` (unchanged)

**Marker set:** `critical`, `mac_gate_calibration`; add `f1_absorption` if in penalty set.

These patterns are the vocabulary. Every `§3.x.y` test row cites its pattern in the Purpose line.

### §3.2 R1 — Epistemic Calibration

Rubric anchor: `quality-rubric.md §6 R1`. Architecture anchor: `mac/architecture.md §6.1 R1 row`. Section applied: Full document. Priority: Critical (Top-5 weighted).

#### §3.2.1 Unit scoring — `MAC-T-GATE-R1-01`

- **Purpose:** With `FakeLLMJudge` returning score=3 for a fixture output whose claims are partially labeled by evidential basis and whose confidence language is proportional to evidence in 6 of 10 claims (2 unlabeled inferences presented as facts, 2 entity-non-specific risk references), assert `R1Gate.score()` returns effective score 3, no co-eval adjustment, no Forge-degradation adjustment.
- **Anchor:** `quality-rubric.md §6 R1` + `mac/architecture.md §6.1 R1 row` + `mac/architecture.md §6.3 R1 judge prompt`.
- **Fulfillment:** `R1Gate.score(output=fixture.sample_10_claims_2_unsupported, forge_degraded=False).effective == 3`
- **Marker set:** `critical`, `mac_gate_calibration`.

#### §3.2.2 Calibration anchor (deterministic) — `MAC-T-GATE-R1-02`

- **Purpose:** Replay `benchmark-questions.md §5 R1 score-2` and `§5 R1 score-4` anchors through `FakeLLMJudge`; assert bucketing.
- **Anchor:** `benchmark-questions.md §5 R1` + `quality-rubric.md §6 R1` + `mac/architecture.md §6.3 R1`.
- **Fulfillment:** `R1Gate.score(§5_R1_score_2_anchor).effective <= 2 AND R1Gate.score(§5_R1_score_4_anchor).effective >= 4`
- **Marker set:** `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #4**
- **Allow-list entry:** yes (see §13.3).

#### §3.2.3 Section routing — `MAC-T-GATE-R1-03`

- **Purpose:** Assert `GATE_SECTION_ROUTES["R1"] == SectionSelector.FULL_DOCUMENT`.
- **Anchor:** `mac/architecture.md §6.2 GATE_SECTION_ROUTES`.
- **Fulfillment:** byte-equality against snapshot `tests/mac/gates/snapshots/section_routes_v0_1.yaml`.
- **Marker set:** `static`, `critical`.

#### §3.2.4 Domain guard — `MAC-T-GATE-R1-04`

- **Purpose:** For each `DomainClass` enum value, assert the correct R1 judge prompt variant is loaded from `mac/architecture.md §6.3 R1 domain variants`.
- **Anchor:** `mac/architecture.md §6.3 R1 domain matrix` + Req-E + SQ-5.
- **Fulfillment:** `R1Gate.judge_prompt(domain=DomainClass.TECHNICAL).source == "§6.3_R1_technical_variant"`, and analogous for all 5 domains.
- **Marker set:** `critical`, `mac_gate_calibration`.

#### §3.2.5 Forge-degradation path — `MAC-T-GATE-R1-05`

- **Purpose:** With `forge_degraded=True` and raw R1=4, assert R1 effective stays 4 (R1 is not in Forge-penalty set per SQ-7; degradation applies to evidence-family gates R7/R8).
- **Anchor:** `mac/architecture.md §12.5 SQ-7 Forge-Degradation Ordering`.
- **Fulfillment:** `R1Gate.score(fixture, forge_degraded=True).effective == 4`
- **Marker set:** `critical`, `mac_gate_calibration`.

### §3.3 R2 — Question Fidelity

Rubric anchor: `quality-rubric.md §6 R2`. Architecture anchor: `mac/architecture.md §6.1 R2 row`. Section applied: `[RECOMMENDATIONS]`. Priority: Critical (Top-5 weighted).

#### §3.3.1 Unit scoring — `MAC-T-GATE-R2-01`

- **Purpose:** `FakeLLMJudge` returns score=2 for an output whose `[RECOMMENDATIONS]` answers a tangent rather than the stated question and makes no attempt to name or reformulate the question; assert `R2Gate.score().effective == 2`.
- **Anchor:** `quality-rubric.md §6 R2` + `mac/architecture.md §6.1 R2` + `§6.3 R2 judge prompt`.
- **Fulfillment:** `R2Gate.score(fixture.tangent_answer).effective == 2`
- **Fixture setup:** `fixture.tangent_answer` is a pre-built MAC document whose `[RECOMMENDATIONS]` block answers a different question than the one asked (e.g., task question "should we enter the EU market this quarter?", recommendation answers "how should we structure the EU entity?"). `FakeLLMJudge` lookup table entry: `(gate_id="R2", fingerprint=fp(fixture_text)) → JudgeResponse(score=2, rationale="§3.3.1 tangent_not_reformulated")`.
- **Telemetry assertion:** After the call, `telemetry.events` contains a single `mac.gate.r2.scored` event with attributes `{gate_id: "R2", score: 2, forge_degraded: False}`.
- **Marker set:** `critical`, `mac_gate_calibration`.

#### §3.3.2 Calibration anchor — `MAC-T-GATE-R2-02`

- **Purpose:** Replay `benchmark-questions.md §5 R2` anchors; assert bucketing.
- **Anchor:** `benchmark-questions.md §5 R2` + `quality-rubric.md §6 R2`.
- **Fulfillment:** `R2Gate.score(§5_R2_score_2).effective <= 2 AND R2Gate.score(§5_R2_score_4).effective >= 4`.
- **Marker set:** `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #5**
- **Allow-list entry:** yes.

#### §3.3.3 Section routing — `MAC-T-GATE-R2-03`

- **Purpose:** Assert `GATE_SECTION_ROUTES["R2"] == SectionSelector.RECOMMENDATIONS`. R2 judge receives only the `[RECOMMENDATIONS]` block; question-answer mapping is verifiable from that section alone. Verified via `FakeLLMJudge.last_call.input == fixture.recommendations_block_only`.
- **Anchor:** `mac/architecture.md §6.2 GATE_SECTION_ROUTES` (`R2 → ("RECOMMENDATIONS",)`).
- **Fulfillment:** byte-equality snapshot check against `tests/mac/gates/snapshots/section_routes_v0_1.yaml`.
- **Marker set:** `static`, `critical`.

#### §3.3.4 Domain guard — `MAC-T-GATE-R2-04`

- **Purpose:** Per-domain R2 prompt variants load correctly — each domain's question-fidelity prompt loads its domain-specific reformulation guidance.
- **Anchor:** `mac/architecture.md §6.3 R2 domain matrix`.
- **Fulfillment:** `R2Gate.judge_prompt(domain=D).source == §6.3 matching row` for all 5 domains.
- **Marker set:** `critical`, `mac_gate_calibration`.

#### §3.3.5 Question fidelity OR-logic + meta-evaluation — `MAC-T-GATE-R2-05`

- **Purpose:** Validate R2's OR-logic structural check (stated question OR named reformulation answered) and the 5/5 meta-evaluation threshold per rubric §6 R2. Four fixtures:
  1. `fixture.answers_stated_verbatim` — analysis answers the stated question verbatim → `R2Gate.score().effective >= 3`.
  2. `fixture.answers_named_reformulation` — analysis opens `[RECOMMENDATIONS]` with "reframing this as 'should we X instead of Y?' — addressing the reformulated question…" and answers the reformulation → `R2Gate.score().effective >= 3` (OR branch satisfied).
  3. `fixture.answers_tangent_unnamed` — analysis answers a tangential question without naming any reformulation → `R2Gate.score().effective <= 2`.
  4. `fixture.answers_with_meta_evaluation` — analysis answers the stated question AND includes explicit meta-evaluation ("note: the question as posed conflates X and Y; the more decision-relevant question would be Z, which we address as follows…") → `R2Gate.score().effective == 5`. This exercises the 5/5 threshold that arch §6.1 R2 explicitly calls out.
- **Anchor:** `mac/architecture.md §6.1 R2 row` + `quality-rubric.md §6 R2` (OR-logic + meta-evaluation at 5/5).
- **Fulfillment:**
  ```python
  assert R2Gate.score(fixture.answers_stated_verbatim).effective >= 3
  assert R2Gate.score(fixture.answers_named_reformulation).effective >= 3
  assert R2Gate.score(fixture.answers_tangent_unnamed).effective <= 2
  assert R2Gate.score(fixture.answers_with_meta_evaluation).effective == 5
  ```
- **Tier layering:** T1 (OR-logic structural check: is the answered question either the stated question verbatim OR a named reformulation?) + T2 (retrieval-based question-mapping consistency for the reformulation branch).
- **Marker set:** `critical`, `mac_gate_calibration`.

### §3.4 R3 — Falsifiability

Rubric anchor: `quality-rubric.md §6 R3`. Architecture anchor: `mac/architecture.md §6.1 R3 row`. Section applied: Full document. Priority: High.

#### §3.4.1 `MAC-T-GATE-R3-01` Unit scoring — `G-UNIT(R3, "r3_score_3_partial_falsifiable", 3)`
- **Purpose:** Pattern `G-UNIT`. Fixture `r3_score_3_partial_falsifiable` is a document whose 3 conclusions include 2 with observable invalidation conditions ("this conclusion will be invalidated if metric X drops below threshold Y within Z days") and 1 vague ("this may not hold if conditions change"). `FakeLLMJudge` returns score=3.
- **Anchor:** `quality-rubric.md §6 R3` + `mac/architecture.md §6.1 R3` + `§6.3 R3 judge prompt`.
- **Fulfillment:** `R3Gate.score(fixture.r3_score_3_partial_falsifiable).effective == 3`
- **Telemetry assertion:** `mac.gate.r3.scored` event with score=3.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.4.2 `MAC-T-GATE-R3-02` Calibration anchor — `G-CAL(R3, "§5_R3_score_2", "§5_R3_score_4")`
- **Purpose:** Pattern `G-CAL`. Replay §5 R3 score-2 (vague contingencies) and score-4 (per-conclusion observable invalidation conditions) anchors; assert bucketing holds.
- **Anchor:** `benchmark-questions.md §5 R3` + `quality-rubric.md §6 R3`.
- **Fulfillment:** `R3Gate.score(§5_R3_score_2).effective <= 2 AND R3Gate.score(§5_R3_score_4).effective >= 4`.
- **Markers:** `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #6**
- **Allow-list entry:** yes.

#### §3.4.3 `MAC-T-GATE-R3-03` Section routing — `G-ROUTE(R3, SectionSelector.FULL_DOCUMENT)`
- **Purpose:** Pattern `G-ROUTE`. Assert R3 operates on the full document per arch §6.2 `R3 → ("FULL",)` — falsifiability is a whole-document property (any conclusion, anywhere in the output, must carry its invalidation conditions).
- **Anchor:** `mac/architecture.md §6.2`.
- **Markers:** `static`, `critical`.

#### §3.4.4 `MAC-T-GATE-R3-04` Domain guard — `G-DOMAIN(R3)`
- **Purpose:** Pattern `G-DOMAIN`. Per-domain R3 prompt variants load correctly for all 5 `DomainClass` values — each domain has its own observable-metric vocabulary (TECHNICAL = measurable performance thresholds; LEGAL = specific rulings / enactments; MEDICAL = clinical trial endpoints).
- **Anchor:** `mac/architecture.md §6.3 R3 domain matrix`.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.4.5 `MAC-T-GATE-R3-05` Falsifiability monotonicity (property-based)
- **Purpose:** R3 score is monotonic in the count of conclusions that specify observable invalidation conditions. For any fixture with `n` total conclusions and `k` of them carrying per-conclusion observable invalidation conditions, `R3(k observable) >= R3(k-1 observable)` for all `k >= 1`. Three-conclusion fixture with 2 observable + 1 vague scores as 3 per §3.4.1; property test exercises the full `n ∈ [1,5]` × `k ∈ [0,n]` grid via Hypothesis.
- **Anchor:** `mac/architecture.md §6.1 R3 row` + `quality-rubric.md §6 R3` definition: "Conclusions specify monitorable, observable invalidation conditions — not vague contingencies."
- **Fulfillment:**
  ```python
  from hypothesis import given, strategies as st

  @given(n=st.integers(min_value=1, max_value=5),
         k=st.integers(min_value=0, max_value=5))
  def test_mac_t_gate_r3_05_monotonicity(n, k):
      k = min(k, n)
      fixture_k   = build_fixture_with_observable_invalidation_count(n_total=n, k_observable=k)
      fixture_kp1 = build_fixture_with_observable_invalidation_count(n_total=n, k_observable=min(k+1, n))
      assert R3Gate.score(fixture_kp1).effective >= R3Gate.score(fixture_k).effective
  ```
- **Tier layering:** T1 (presence-of-per-conclusion-invalidation-condition count) + T2 (retrieval comparison for specificity).
- **Markers:** `critical`, `mac_gate_calibration`.

### §3.5 R4 — Steelman Completeness

Rubric anchor: `quality-rubric.md §6 R4`. Architecture anchor: `mac/architecture.md §6.1 R4 row + §7.1 Req-F + §6.3 Pair 2`. Section applied: `[STEELMAN]`. Priority: Critical (Top-5 weighted). **Co-eval pair: (R5, R4) — Req-C manufactured-dissent cap per arch §6.3 Pair 2.**

#### §3.5.1 `MAC-T-GATE-R4-01` Unit scoring — `G-UNIT(R4, "r4_score_3_partial_steelman", 3)`
- **Purpose:** Pattern `G-UNIT`. Fixture `r4_score_3_partial_steelman` is a `[STEELMAN]` block where the producer engages with 2 of 4 likely counter-positions substantively. Scored 3.
- **Anchor:** `quality-rubric.md §6 R4` + `mac/architecture.md §6.1 R4` + `§6.3 R4`.
- **Fulfillment:** `R4Gate.score(fixture).effective == 3`.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.5.2 `MAC-T-GATE-R4-02` Calibration anchor — `G-CAL(R4, ...)`
- **Purpose:** Pattern `G-CAL`. R4 is Top-5 weighted; `no_waiver` enforced.
- **Anchor:** `benchmark-questions.md §5 R4` + `quality-rubric.md §6 R4`.
- **Fulfillment:** `R4Gate.score(§5_R4_score_2).effective <= 2 AND R4Gate.score(§5_R4_score_4).effective >= 4`.
- **Markers:** `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #7**
- **Allow-list entry:** yes.

#### §3.5.3 `MAC-T-GATE-R4-03` Section routing — `G-ROUTE(R4, SectionSelector.STEELMAN)`
- **Purpose:** Pattern `G-ROUTE`. `GATE_SECTION_ROUTES["R4"] == ("STEELMAN",)` per arch §6.2. R4 applied ONLY to `[STEELMAN]` block. Assert R4 judge receives only `[STEELMAN]` section text, not full document. Verified via `FakeLLMJudge.last_call.input == fixture.steelman_block_only`.
- **Anchor:** `mac/architecture.md §6.2 GATE_SECTION_ROUTES`.
- **Markers:** `static`, `critical`.

#### §3.5.4 `MAC-T-GATE-R4-04` Domain guard — `G-DOMAIN(R4)`
- **Purpose:** Pattern `G-DOMAIN`. Per-domain R4 prompt variants. TECHNICAL R4 expects technical-counter steelman; LEGAL R4 expects opposing-counsel steelman.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.5.5 `MAC-T-GATE-R4-05` Co-eval pair (R5, R4) manufactured-dissent cap
- Purpose: when a dissent position does not correspond to task-context positions (from the R5 manufactured-dissent structural check per arch §6.3 Pair 2), R5 is capped at 2 but R4 (Steelman Completeness) is NOT capped by the (R5, R4) relationship. This test asserts R4 effective is unchanged by whether the R5 cap fires.
- Anchor: `mac/architecture.md §6.3 Pair 2 (R5, R4) — Manufactured Dissent Detection`.
- Fulfillment: `R4Gate.score(fixture, r5_uncapped=4, r5_capped=2).effective == R4Gate.score(fixture, r5_uncapped=4).effective` (R4 unaffected by R5 cap).
- Markers: `critical`, `mac_gate_calibration`.

#### §3.5.6 `MAC-T-GATE-R4-06` Req-F two-step independence (deterministic structural)
- Purpose: the R4 judge payload sent to the reviewer carries both `independent_steelman` AND `gap_assessment` fields, and `independent_steelman` appears BEFORE `gap_assessment` in the serialized JSON (field ordering matters for the reviewer-reads-own-steelman-first protocol per Req-F).
- Anchor: `mac/architecture.md §7.1 Req-F` + arch §12.2 item 9 (Req-F independent-steelman protocol) deterministic sub-test.
- Fulfillment: `schema = R4Gate.reviewer_payload_schema(); keys = list(schema.__fields__.keys()); assert keys.index("independent_steelman") < keys.index("gap_assessment")`.
- Markers: `critical`, `asymmetry_structural`, `static`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #14 (Decision 1 item 9 deterministic carrier)**
- Allow-list entry: yes.
- **NOTE:** The live version of this test is `MAC-T-ASYM-R-F-03` in §5.1, which carries `critical + asymmetry_structural` ONLY (no `no_waiver`).

### §3.6 R5 — Dissent Preservation

Rubric anchor: `quality-rubric.md §6 R5`. Architecture anchor: `mac/architecture.md §6.1 R5 row + §6.3 Pair 2`. Section applied: `[DISSENT]`. Priority: Critical (Top-5 weighted). **Co-eval pair: (R5, R4) — manufactured-dissent detection, R5 capped at 2 when dissent positions don't correspond to task context.**

#### §3.6.1 `MAC-T-GATE-R5-01` Unit scoring — `G-UNIT(R5, "r5_score_3_partial_dissent", 3)`
- **Purpose:** Pattern `G-UNIT`. Fixture `r5_score_3_partial_dissent` is a `[DISSENT]` block with 3 dissent positions; 2 correspond to task-context positions and 1 is off-topic. Scored 3.
- **Anchor:** `quality-rubric.md §6 R5` + `mac/architecture.md §6.1 R5`.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.6.2 `MAC-T-GATE-R5-02` Calibration anchor — `G-CAL(R5, ...)`
- **Purpose:** Pattern `G-CAL`. R5 is Top-5 weighted.
- **Anchor:** `benchmark-questions.md §5 R5` + `quality-rubric.md §6 R5`.
- **Markers:** `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #8**
- **Allow-list entry:** yes.

#### §3.6.3 `MAC-T-GATE-R5-03` Section routing — `G-ROUTE(R5, SectionSelector.DISSENT)`
- **Purpose:** Pattern `G-ROUTE`. `GATE_SECTION_ROUTES["R5"] == ("DISSENT",)` per arch §6.2. R5 judge receives only `[DISSENT]` block.
- **Markers:** `static`, `critical`.

#### §3.6.4 `MAC-T-GATE-R5-04` Domain guard — `G-DOMAIN(R5)`
- **Purpose:** Pattern `G-DOMAIN`. Dissent norms differ: TECHNICAL accepts minority technical opinions; LEGAL has formal dissent conventions. Also: R5 is guarded per arch §6.5 Req-E — if `domain_class == DomainClass.CONSENSUS`, R5 is suspended.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.6.5 `MAC-T-GATE-R5-05` Manufactured-dissent cap (Req-C Pair 2)
- Purpose: when a dissent position does NOT correspond to a task-context position (i.e., the dissent is manufactured / off-topic), R5 raw=4 is capped to 2 per arch §6.3 Pair 2 manufactured-dissent detection. This requires the R5 evaluator to run in two passes (blind + task-context) per arch §6.3.
- Anchor: `mac/architecture.md §6.3 Pair 2 — Manufactured Dissent Detection`.
- Fulfillment: `R5Gate.score(fixture.off_topic_dissent_raw4, task_context=standard_task).effective == 2`.
- Markers: `critical`, `mac_gate_calibration`.

#### §3.6.6 `MAC-T-GATE-R5-06` (placeholder — authoritative R7/R8 worked example moved to §3.8.6)
- Purpose: NOTE — this test is misnamed at R5; the Reasoning Traceability / Actionability Calibration co-eval worked example (R7=2, R8=4 → R8_eff=3) belongs to Pair 1, not Pair 2. Moved to §3.8.6. This row is a placeholder to preserve sequential numbering.
- **REMOVED** — see §3.8.6.

### §3.7 R6 — Decision Relevance Density

Rubric anchor: `quality-rubric.md §6 R6`. Architecture anchor: `mac/architecture.md §6.1 R6 row`. Section applied: **L1 layer only** (executive summary + key recommendations). Priority: Medium.

#### §3.7.1 `MAC-T-GATE-R6-01` Unit scoring — `G-UNIT(R6, "r6_score_3_padded_l1", 3)`
- **Purpose:** Pattern `G-UNIT`. Fixture `r6_score_3_padded_l1` has an L1 layer with a mix of hedged generalities and 2 explicitly priority-marked key findings, over a dense L2. Expected score 3 — partial L1 density with some but not all findings prioritized.
- **Anchor:** `quality-rubric.md §6 R6` + `mac/architecture.md §6.1 R6`.
- **Fulfillment:** `R6Gate.score(fixture).effective == 3`.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.7.2 `MAC-T-GATE-R6-02` Calibration anchor (NOT no_waiver — R6 is Medium priority) — `G-CAL(R6, ...)`
- **Purpose:** Pattern `G-CAL`. R6 is Medium priority, not in the Top-5 weighted set, so its calibration test is `critical` + `mac_gate_calibration` but NOT `no_waiver`.
- **Anchor:** `benchmark-questions.md §5 R6` + `quality-rubric.md §6 R6`.
- **Note:** No `no_waiver`. The `no_waiver` calibration anchors are limited to: Top-5 R1/R2/R3/R4/R5 + R7/R8 (co-eval pair) + R11 + the 2 structural calibration tests `MAC-T-GATE-R11-05`/`MAC-T-GATE-R12-05` = 10 items total, exactly matching Decision 1 (see §1.4 and §13.3.3).
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.7.3 `MAC-T-GATE-R6-03` Section routing — `G-ROUTE(R6, SectionSelector.L1)`
- **Purpose:** Pattern `G-ROUTE`. `GATE_SECTION_ROUTES["R6"] == ("L1",)` per arch §6.2. R6 sees ONLY the L1 layer — never the full document. Verified by inspecting `FakeLLMJudge.last_call.input == fixture.l1_layer_only`. Per arch §6.2 critical property: "Padding bodies cannot mask a poor exec summary, and dense exec summaries cannot be punished for verbose appendices" (TRIZ-2 resolution).
- **Anchor:** `mac/architecture.md §6.2 GATE_SECTION_ROUTES` (`R6 → ("L1",)`) + TRIZ-2 resolution.
- **Markers:** `static`, `critical`.

#### §3.7.4 `MAC-T-GATE-R6-04` Domain guard — `G-DOMAIN(R6)`
- **Purpose:** Pattern `G-DOMAIN`. Per-domain R6 prompt variants. Each domain has different conventions for what "decision-relevant signal" means in an L1 summary — TECHNICAL = specific metrics + recommended action; LEGAL = specific rulings + required actions; MEDICAL = specific clinical endpoints + recommended interventions.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.7.5 `MAC-T-GATE-R6-05` L1-density differential (padded vs lean)
- **Purpose:** Exercise R6's core signal — L1 layer density with explicit priority markers on key findings. Two fixtures sharing **identical L2 content**:
  - `fixture.padded_l1` — L1 is hedge-heavy generalities ("we explored several dimensions of this question and found multiple considerations worth noting; various factors may warrant further attention…") with NO explicit priority markers on findings.
  - `fixture.lean_l1` — L1 uses explicit priority markers per Req-A label set (`[PRIORITY 1]: X → action Y. [PRIORITY 2]: Z → action W.`) with a dense, decision-relevant structure.
  - Assert `R6Gate.score(lean_l1).effective > R6Gate.score(padded_l1).effective` strictly.
- **Critical routing assertion:** The test MUST verify via `FakeLLMJudge.last_call.input` that the R6 judge receives **only** the L1 layer, never the identical L2 content. If the test accidentally feeds the full document to the gate, `padded_l1` and `lean_l1` would be indistinguishable from L2 and the test would pass for the wrong reason. This is the §3.7.3 `G-ROUTE` assertion exercised through a semantic test.
- **Anchor:** `mac/architecture.md §6.1 R6 row` + `quality-rubric.md §6 R6` definition: "L1 layer (executive summary + key recommendations) is dense with decision-relevant signal; key findings explicitly prioritized."
- **Fulfillment:**
  ```python
  padded = load_fixture("r6_padded_l1_identical_l2")
  lean   = load_fixture("r6_lean_l1_identical_l2")
  assert padded.l2_content == lean.l2_content   # shared L2
  assert R6Gate.score(lean).effective > R6Gate.score(padded).effective
  # Routing check: judge saw only L1, not full document
  assert FakeLLMJudge.last_call.input == lean.l1_only
  ```
- **Tier layering:** T1 (priority marker presence check in L1 — regex or structural scan for `[PRIORITY N]` or equivalent Req-A labels) + T3 (LLM-judge assesses L1 density only; L2 not passed to judge).
- **Markers:** `critical`, `mac_gate_calibration`.

### §3.8 R7 — Reasoning Traceability

Rubric anchor: `quality-rubric.md §6 R7`. Architecture anchor: `mac/architecture.md §6.1 R7 row + §6.3 Pair 1`. Section applied: L2 main body. Priority: Critical (Top-5 weighted). **Co-eval pair: (R8, R7)** per arch §6.3 Pair 1, where `R8_effective = min(R8_raw, R7_raw + 1)` — actionability cannot exceed reasoning traceability + 1 (you cannot give actionable recommendations grounded in reasoning you didn't trace).

#### §3.8.1 `MAC-T-GATE-R7-01` Unit scoring — `G-UNIT(R7, "r7_score_3_thin_trace", 3)`
- **Purpose:** Pattern `G-UNIT`. Fixture `r7_score_3_thin_trace` is an L2 main-body section with 5 conclusions whose logic chains contain inference markers ("therefore", "because", "given that") but where only 3 of the 5 chains present a step-by-step logical validity that a reader can follow — the other 2 jump from premise to conclusion without intermediate steps. `FakeLLMJudge` returns score=3 for partial traceability.
- **Anchor:** `quality-rubric.md §6 R7` + `mac/architecture.md §6.1 R7`.
- **Fulfillment:** `R7Gate.score(fixture).effective == 3`.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.8.2 `MAC-T-GATE-R7-02` Calibration anchor — `G-CAL(R7, ...)`
- **Purpose:** Pattern `G-CAL`. R7 is Top-5 weighted; `no_waiver` enforced.
- **Anchor:** `benchmark-questions.md §5 R7`.
- **Markers:** `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #9**
- **Allow-list entry:** yes.

#### §3.8.3 `MAC-T-GATE-R7-03` Section routing — `G-ROUTE(R7, SectionSelector.L2)`
- **Purpose:** Pattern `G-ROUTE`. `GATE_SECTION_ROUTES["R7"] == ("L2",)` per arch §6.2. R7 sees only the L2 main analysis body; not L1, not `[RECOMMENDATIONS]`, not `[STEELMAN]`, not `[DISSENT]`, not `[FINDINGS]`. Reasoning traceability is a main-body property — the step-by-step logic chain lives in L2.
- **Anchor:** `mac/architecture.md §6.2 GATE_SECTION_ROUTES` (`R7 → ("L2",)`).
- **Markers:** `static`, `critical`.

#### §3.8.4 `MAC-T-GATE-R7-04` Domain guard — `G-DOMAIN(R7)`
- **Purpose:** Pattern `G-DOMAIN`. Per-domain R7 prompt variants. Different domains use different inference markers and different standards for "logical validity of chain" (TECHNICAL = formal derivations or code-level traces; LEGAL = statutory + case reasoning; MEDICAL = differential-diagnosis chains).
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.8.5 `MAC-T-GATE-R7-05` Forge-degradation penalty applies LAST
- Purpose: With R7_raw=4 and `forge_degraded=True`, R7 effective = 3 (penalty of −1 applied AFTER Req-C co-eval caps per arch §6.3 SQ-7 ordering). Semantically: Forge compression removes reasoning traces → R7 degraded. The penalty is applied to `R7_effective` only and MUST NOT propagate back into the R8 cap.
- Anchor: `mac/architecture.md §6.3 SQ-7 ordering` (step 3 of the three-step order of operations).
- Fulfillment: `R7Gate.score(fixture, raw=4, forge_degraded=True).effective == 3`.
- Markers: `critical`, `mac_gate_calibration`, `f1_absorption`.

#### §3.8.6 `MAC-T-GATE-R7-06` Co-eval worked example (R7_raw=2, R8_raw=4) → R8_eff=3
- Purpose: Authoritative worked example for the (R8, R7) co-eval rule. With `R7_raw = 2` (weak reasoning traceability) and `R8_raw = 4` (specific, actionable recommendation), R8 is capped to `min(4, 2+1) = 3` per arch §6.3 Pair 1 SQ-4 Option (b). R7 stays at 2 (R7 is not capped; it caps R8). Semantic interpretation: "actionable but not traceable" — the recommendation is specific but the supporting reasoning chain is too thin for a reviewer to verify, so actionability cannot exceed reasoning traceability + 1.
- Anchor: `mac/architecture.md §6.3 Pair 1 (R8, R7) — Actionability vs. Traceability` + SQ-4 Option (b).
- Fulfillment: `score_all(fixture, r7_raw=2, r8_raw=4).R8.effective == 3 AND .R7.effective == 2`.
- Markers: `critical`, `mac_gate_calibration`.

### §3.9 R8 — Actionability Calibration

Rubric anchor: `quality-rubric.md §6 R8`. Architecture anchor: `mac/architecture.md §6.1 R8 row + §6.3 Pair 1`. Section applied: `[RECOMMENDATIONS]`. Priority: High (Top-5 weighted). **Co-eval pair: (R8, R7)** per arch §6.3 Pair 1 — R8 is the capped gate; `R8_effective = min(R8_raw, R7_raw + 1)`.

#### §3.9.1 `MAC-T-GATE-R8-01` Unit scoring
- Purpose: Given a fixture `[RECOMMENDATIONS]` block with 9 of 10 recommendations carrying specific next-concrete-action language (named method, named owner, specific timeframe, or specific measurable criterion) and 1 recommendation falling into the "further analysis without conditional recommendation" failure mode per rubric §6 R8, assert R8 score = 4.
- Anchor: `quality-rubric.md §6 R8` + `mac/architecture.md §6.1 R8`.
- Markers: `critical`, `mac_gate_calibration`.

#### §3.9.2 `MAC-T-GATE-R8-02` Calibration anchor
- Anchor: `benchmark-questions.md §5 R8`.
- Markers: `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #10**
- Allow-list entry: yes.

#### §3.9.3 `MAC-T-GATE-R8-03` Section routing — `G-ROUTE(R8, SectionSelector.RECOMMENDATIONS)`
- Purpose: `GATE_SECTION_ROUTES["R8"] == ("RECOMMENDATIONS",)` per arch §6.2. R8 evaluates the `[RECOMMENDATIONS]` section — the decision-section, not the findings narrative — per arch §6.2 "R2, R8 receive ('RECOMMENDATIONS',) — they evaluate the decision sections, not the findings narrative."
- Anchor: `mac/architecture.md §6.2 GATE_SECTION_ROUTES` (`R8 → ("RECOMMENDATIONS",)`).
- Markers: `static`, `critical`.

#### §3.9.4 `MAC-T-GATE-R8-04` Domain guard
- Purpose: Per-domain R8 prompt variants. "Actionable" differs by domain: TECHNICAL R8 requires runnable code / concrete engineering steps; MEDICAL R8 requires named intervention + dosage/schedule; POLICY R8 requires named accountable party + timeframe.
- Markers: `critical`, `mac_gate_calibration`.

#### §3.9.5 `MAC-T-GATE-R8-05` Co-eval cap with R7 uses RAW R7
- Purpose: assert `R8_effective = min(R8_raw, R7_raw + 1)` is computed using **raw** R7 (pre-Forge-penalty), per arch §6.3 SQ-7 step-2 ordering (Req-C caps computed from raw scores; Forge penalty applied last to `R7_effective` only). Semantic: actionability is capped by how much of the reasoning the Forge-degraded chain could carry at **full** fidelity, not by the degraded trace.
- Anchor: `mac/architecture.md §6.3 SQ-7 ordering` step 2.
- Fulfillment: `score_all(fixture, r7_raw=4, r8_raw=4, forge_degraded=True).R8.effective == 4` (R8 uses raw R7=4, not Forge-penalized R7=3; R8 = min(4, 4+1) = 4).
- Markers: `critical`, `mac_gate_calibration`, `f1_absorption`.

#### §3.9.6 `MAC-T-GATE-R8-06` Forge-degradation does NOT directly penalize R8
- Purpose: With `R8_raw = 4`, Req-C cap inactive (`R7_raw = 4`), and `forge_degraded = True`, R8 effective stays 4 per arch §6.3 SQ-7 — only R7 is in the Forge-degradation penalty set; R8 is NOT directly penalized. R8 can still be capped indirectly if raw R7 was low enough, but Forge alone does not touch R8.
- Anchor: `mac/architecture.md §6.3 SQ-7 ordering` (penalty applies to `R7_effective` only).
- Markers: `critical`, `mac_gate_calibration`, `f1_absorption`.

### §3.10 R9 — Evidence Impartiality

Rubric anchor: `quality-rubric.md §6 R9`. Architecture anchor: `mac/architecture.md §6.1 R9 row`. Section applied: `[FINDINGS]` only (STEELMAN/DISSENT explicitly exempt per TRIZ-3 resolution). Priority: Medium.

#### §3.10.1 `MAC-T-GATE-R9-01` Unit scoring — `G-UNIT(R9, "r9_score_3_partial_proportional", 3)`
- **Purpose:** Pattern `G-UNIT`. Fixture `r9_score_3_partial_proportional` is a `[FINDINGS]` block where 3 of 5 recommendation-findings pairs exhibit conclusion strength proportional to evidence strength, while 2 pairs show mild narrative bias (conclusion over-commits relative to the findings evidence). Scored 3.
- **Anchor:** `quality-rubric.md §6 R9` + `mac/architecture.md §6.1 R9`.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.10.2 `MAC-T-GATE-R9-02` Calibration anchor (NOT no_waiver — Medium priority)
- **Purpose:** Pattern `G-CAL`. R9 is Medium priority, so `no_waiver` is NOT applied. Nightly drift canary catches live drift.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.10.3 `MAC-T-GATE-R9-03` Section routing — `G-ROUTE(R9, SectionSelector.FINDINGS)`
- **Purpose:** Pattern `G-ROUTE`. `GATE_SECTION_ROUTES["R9"] == ("FINDINGS",)` per arch §6.2, with explicit exemption: `[STEELMAN]` and `[DISSENT]` sections are NOT passed to R9 (TRIZ-3 resolution per arch §6.2 critical property).
- **Markers:** `static`, `critical`.

#### §3.10.4 `MAC-T-GATE-R9-04` Domain guard — `G-DOMAIN(R9)`
- **Purpose:** Pattern `G-DOMAIN`. Per-domain "proportional to evidence" thresholds differ (TECHNICAL = quantitative effect-size alignment; LEGAL = precedent-weight alignment; MEDICAL = effect-size × sample-size alignment).
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.10.5 `MAC-T-GATE-R9-05` Proportionality + STEELMAN/DISSENT exemption
- **Purpose:** Exercise R9's core signal in two sub-tests.
- **Sub-test 5a (proportionality):** Three fixtures sharing **identical `[FINDINGS]` content**:
  - `fixture.under_committed_recommendation` — strong findings + weak/under-committed recommendation ("the evidence is clear that X, but we should probably consider possibly doing Y").
  - `fixture.proportional_recommendation` — strong findings + proportionally strong recommendation ("X is established by the findings above; therefore Y").
  - `fixture.over_committed_recommendation` — strong findings + over-committed recommendation (recommendation stronger than the findings justify, e.g., "X is established" pushed to "X is inevitable and decisive").
  - Assert `R9Gate.score(proportional).effective > R9Gate.score(under_committed).effective` AND `R9Gate.score(over_committed).effective <= 2` (over-commitment is a symmetric failure mode — conclusion strength NOT proportional to evidence strength).
- **Sub-test 5b (STEELMAN/DISSENT exemption):** Fixture with an aggressively narratively-biased `[STEELMAN]` section (the STEELMAN itself over-states the counter-position) AND impartial `[FINDINGS]`. Assert `R9Gate.score(fixture).effective >= 4` (the biased STEELMAN must NOT drag R9 down) AND via `FakeLLMJudge.last_call.input` assert the R9 judge received **only** the `[FINDINGS]` section text — not the STEELMAN. This is the semantic exemption: if the router accidentally included STEELMAN content in R9's input, the biased STEELMAN would drag R9 down and the test would fail. This cross-checks §3.10.3 G-ROUTE at the semantic level.
- **Anchor:** `mac/architecture.md §6.1 R9 row` + `quality-rubric.md §6 R9` definition: "Conclusion strength in recommendations is proportional to evidence strength in findings; findings sections not narratively biased; steelman/dissent sections exempt." + TRIZ-3 resolution (arch §6.2 critical property).
- **Fulfillment:**
  ```python
  under = load_fixture("r9_under_committed_identical_findings")
  prop  = load_fixture("r9_proportional_identical_findings")
  over  = load_fixture("r9_over_committed_identical_findings")
  assert under.findings_content == prop.findings_content == over.findings_content
  assert R9Gate.score(prop).effective > R9Gate.score(under).effective
  assert R9Gate.score(over).effective <= 2

  biased = load_fixture("r9_biased_steelman_impartial_findings")
  assert R9Gate.score(biased).effective >= 4
  assert FakeLLMJudge.last_call.input == biased.findings_only  # STEELMAN not passed
  ```
- **Tier layering:** T3 only per rubric §6 R9 (no T1/T2 — judge applied to `[FINDINGS]` only with question "is conclusion proportional to evidence?", not "is analysis neutral?").
- **Markers:** `critical`, `mac_gate_calibration`.

### §3.11 R10 — Epistemic Scope Honesty

Rubric anchor: `quality-rubric.md §6 R10`. Architecture anchor: `mac/architecture.md §6.1 R10 row`. Section applied: Full document. Priority: High.

#### §3.11.1 `MAC-T-GATE-R10-01` Unit scoring — `G-UNIT(R10, "r10_score_3_partial_scope", 3)`
- **Purpose:** Pattern `G-UNIT`. Fixture includes a specific scope declaration (what was examined AND what was explicitly NOT examined) but the blind spot acknowledgment is generic ("other perspectives may apply") rather than naming a specific method / expertise / perspective gap. Partial R10 satisfaction: one component present, one component boilerplate. `FakeLLMJudge` returns score=3.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.11.2 `MAC-T-GATE-R10-02` Calibration anchor (NOT no_waiver — High priority but outside Top-5)
- **Purpose:** Pattern `G-CAL`. R10 is High priority but not among the Top-5 Critical gates, so `no_waiver` is NOT applied.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.11.3 `MAC-T-GATE-R10-03` Section routing — `G-ROUTE(R10, SectionSelector.FULL_DOCUMENT)`
- **Purpose:** Pattern `G-ROUTE`. `GATE_SECTION_ROUTES["R10"] == ("FULL",)` per arch §6.2. Scope honesty (specific exclusion + specific blind spot acknowledgment) can appear anywhere in the document — executive summary, findings caveats, scope note — so R10 scans the full document.
- **Anchor:** `mac/architecture.md §6.2 GATE_SECTION_ROUTES` (`R10 → ("FULL",)`).
- **Markers:** `static`, `critical`.

#### §3.11.4 `MAC-T-GATE-R10-04` Domain guard — `G-DOMAIN(R10)`
- **Purpose:** Pattern `G-DOMAIN`. Per-domain "specific blind spot" vocabularies differ — TECHNICAL = named methodology gaps ("we did not profile under production load"); LEGAL = jurisdictional or case-type gaps; MEDICAL = named patient-population or comorbidity gaps.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.11.5 `MAC-T-GATE-R10-05` 2² property + boilerplate detection
- **Purpose:** R10 requires BOTH components (specific scope exclusion AND specific blind spot acknowledgment) per rubric §6 R10. Property-based test over `2² = 4` combinations of `(has_specific_exclusion, has_specific_blindspot)`, plus a dedicated boilerplate-detection fixture:
  - `(True, True)`  → `score >= 4` (both components present and specific)
  - `(True, False)` → `score <= 2` (specific exclusion present but blind spot missing or absent)
  - `(False, True)` → `score <= 2` (specific blind spot present but scope exclusion missing)
  - `(False, False)` → `score <= 2` (neither component)
  - **Boilerplate fixture:** both components present as strings ("limitations apply", "there may be gaps in our analysis") but neither is specific. Per rubric §6 R10 "boilerplate fails": `R10Gate.score(boilerplate_fixture).effective <= 2` even though T1 string-presence passes.
- **Anchor:** `mac/architecture.md §6.1 R10 row` + `quality-rubric.md §6 R10` definition: "Specific scope declaration (what examined AND what not); specific blind spot acknowledgment (named method/expertise/perspective gap) — both components required, boilerplate fails."
- **Fulfillment:**
  ```python
  from hypothesis import given, strategies as st

  @given(st.booleans(), st.booleans())
  def test_mac_t_gate_r10_05_both_components(has_exclusion, has_blindspot):
      fx = build_fixture(specific_exclusion=has_exclusion, specific_blindspot=has_blindspot)
      score = R10Gate.score(fx).effective
      if has_exclusion and has_blindspot:
          assert score >= 4
      else:
          assert score <= 2

  def test_mac_t_gate_r10_05_boilerplate():
      fx = build_fixture(
          specific_exclusion=True, specific_blindspot=True,
          exclusion_text="limitations apply",
          blindspot_text="there may be gaps in our analysis",
      )
      assert R10Gate.score(fx).effective <= 2
  ```
- **Tier layering:** T1 (structural both-components presence check — neither component may be absent) + T3 (LLM-judge: blind spot quality assessment, specific vs boilerplate detection per rubric §6 R10 T3 clause).
- **Markers:** `critical`, `mac_gate_calibration`.

### §3.12 R11 — Scenario Coverage

Rubric anchor: `quality-rubric.md §6 R11`. Architecture anchor: `mac/architecture.md §6.1 R11 row + §6.5 Req-E deterministic-domain guard`. Section applied: L2 main body. Priority: High.

#### §3.12.1 `MAC-T-GATE-R11-01` Unit scoring — `G-UNIT(R11, "r11_score_4_multi_scenario", 4)`
- **Purpose:** Pattern `G-UNIT`. Fixture is an L2 main-body section containing 3 distinct named scenarios ("base case", "aggressive downside", "upside with tailwinds") with non-overlapping trigger conditions and differentiated decision implications. Minor differentiation gap in one scenario's trigger condition keeps it from a 5. Scored 4.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.12.2 `MAC-T-GATE-R11-02` Calibration anchor — `G-CAL(R11, ...)`
- **Purpose:** Pattern `G-CAL`. R11 calibration anchors distinguish score-2 (single-scenario or undifferentiated-implications defect) from score-4 (multiple named scenarios with differentiated implications and distinct triggers).
- **Anchor:** `benchmark-questions.md §5 R11`.
- **Markers:** `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #11**
- **Allow-list entry:** yes.

#### §3.12.3 `MAC-T-GATE-R11-03` Section routing — `G-ROUTE(R11, SectionSelector.L2)`
- **Purpose:** Pattern `G-ROUTE`. `GATE_SECTION_ROUTES["R11"] == ("L2",)` per arch §6.2. Scenario coverage is an L2 main-body concern — the differentiated futures and their trigger conditions live in the main analysis, not in the executive summary or findings caveats.
- **Anchor:** `mac/architecture.md §6.2 GATE_SECTION_ROUTES` (`R11 → ("L2",)`).
- **Markers:** `static`, `critical`.

#### §3.12.4 `MAC-T-GATE-R11-04` Domain guard — `G-DOMAIN(R11)`
- **Purpose:** Pattern `G-DOMAIN`. Per arch §6.5 Req-E + SQ-5: if `domain_class ∈ {DomainClass.DETERMINISTIC, DomainClass.BINARY}`, R11 is suspended (`GateScore.suspended=True`) and a note is added to `GateScore.rationale` saying scenarios don't apply. For non-deterministic domains, per-domain "plausible future" definitions differ — TECHNICAL = system states under different load / failure modes; LEGAL = ruling outcomes across plausible court compositions; MEDICAL = patient-response distributions across sub-populations.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.12.5 `MAC-T-GATE-R11-05` Scenario-coverage property — ≥3 distinct scenarios with differentiated implications
- **Purpose:** Exercise R11's core signal via property-based testing. For R11 to score `>= 4`, the L2 main body MUST contain **≥3 distinct named scenarios** with:
  - Non-overlapping trigger conditions (what set of observables tips the situation into each scenario)
  - Differentiated decision implications (each scenario recommends a different action or different magnitude of the same action)
- For scores `<= 2`, inject fixtures with defects: single-scenario ("in all likelihood..."), undifferentiated-implications (3 named scenarios but all lead to the same recommendation), or missing-triggers (3 named scenarios with decision implications but no observable trigger conditions for distinguishing which is unfolding).
- **Hypothesis property layer:** over `(n_scenarios, has_differentiated_implications, has_distinct_triggers)` generate fixtures and assert the R11 score satisfies the monotonicity `R11(n=k, both=True) > R11(n=k-1, both=True)` and `R11(n=k, both=True) > R11(n=k, either=False)`.
- **Anchor:** `mac/architecture.md §6.1 R11 row` + `quality-rubric.md §6 R11` definition: "Multiple plausible futures with differentiated decision implications and trigger conditions; guard condition for deterministic domains."
- **Fulfillment:**
  ```python
  from hypothesis import given, strategies as st

  @given(n_scenarios=st.integers(min_value=1, max_value=5),
         has_differentiated_implications=st.booleans(),
         has_distinct_triggers=st.booleans())
  def test_mac_t_gate_r11_05_scenario_coverage(n_scenarios, has_differentiated_implications, has_distinct_triggers):
      fx = build_fixture_with_scenarios(
          n=n_scenarios,
          differentiated_implications=has_differentiated_implications,
          distinct_triggers=has_distinct_triggers,
      )
      score = R11Gate.score(fx).effective
      if n_scenarios >= 3 and has_differentiated_implications and has_distinct_triggers:
          assert score >= 4
      elif n_scenarios <= 1 or not has_differentiated_implications or not has_distinct_triggers:
          assert score <= 2
  ```
- **Tier layering:** T1 (scenario presence + differential implications verification + deterministic-domain guard from §6.5) + T2 (retrieval: scenario differentiation quality) + T3 (FakeLLMJudge for the judge layer). This is a structural calibration property test; R11 is priority High per arch §6.1 and does not carry release-blocking semantics.
- **Anchor cross-reference:** `mac/architecture.md §6.1 R11 row` + `quality-rubric.md §6 R11` + arch §6.5 Req-E deterministic-domain guard. NOT arch §12.2 (which does not describe this test).
- **Markers:** `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #12 (structural calibration test)**
- **Allow-list entry:** yes. Entry #12 position preserved verbatim from v0.1; test body REWRITTEN v0.2 per team-lead DIV-2 C-2 authorization.

### §3.13 R12 — Internal Consistency

Rubric anchor: `quality-rubric.md §6 R12`. Architecture anchor: `mac/architecture.md §6.1 R12 row`. Section applied: Full document. Priority: High.

#### §3.13.1 `MAC-T-GATE-R12-01` Unit scoring — `G-UNIT(R12, "r12_score_4_minor_tension", 4)`
- **Purpose:** Pattern `G-UNIT`. Fixture is an output with one minor cross-section tension that does not rise to a direct contradiction (e.g., `[FINDINGS]` assigns moderate confidence to X and `[RECOMMENDATIONS]` treats X as more likely than the findings support, but the gap is small and not a premise-denial). Scored 4.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.13.2 `MAC-T-GATE-R12-02` Calibration anchor — `G-CAL(R12, ...)`
- **Purpose:** Pattern `G-CAL`. R12 calibration is `critical` but NOT `no_waiver` — only the structural cross-section contradiction test (§3.13.5) carries `no_waiver`.
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.13.3 `MAC-T-GATE-R12-03` Section routing — `G-ROUTE(R12, SectionSelector.FULL_DOCUMENT)`
- **Purpose:** Pattern `G-ROUTE`. `GATE_SECTION_ROUTES["R12"] == ("FULL",)` per arch §6.2. Internal consistency is a whole-document property — contradictions between `[FINDINGS]`, L2 main body, and `[RECOMMENDATIONS]` can only be detected by looking at all sections jointly.
- **Anchor:** `mac/architecture.md §6.2 GATE_SECTION_ROUTES` (`R12 → ("FULL",)`).
- **Markers:** `static`, `critical`.

#### §3.13.4 `MAC-T-GATE-R12-04` Domain guard — `G-DOMAIN(R12)`
- **Purpose:** Pattern `G-DOMAIN`. Per-domain R12 prompt variants — each domain has different conventions for what counts as a "direct contradiction" (TECHNICAL = measurable claims whose numeric ranges don't overlap; LEGAL = mutually-exclusive legal positions; MEDICAL = mutually-exclusive clinical interpretations).
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.13.5 `MAC-T-GATE-R12-05` Direct cross-section contradiction detector (structural calibration)
- **Purpose:** Exercise R12's core signal — direct contradiction detection across sections per rubric §6 R12 T1 clause. Inject a fixture with a deliberate cross-section contradiction: `[FINDINGS]` asserts "X is stable across all observed conditions" and `[RECOMMENDATIONS]` opens with "because X is unstable, consider Y". Premise accepted in findings (stability) is directly denied in conclusions (instability). This is the canonical R12 failure mode per rubric §6 R12 definition: "premises accepted in findings are not denied in conclusions."
- **Assertions:**
  - `R12Gate.score(fixture.contradiction_findings_recs).effective <= 2` (direct contradiction present).
  - The `GateScore.rationale` field contains a span reference identifying both contradicted text locations (`[FINDINGS]` claim "X is stable…" AND `[RECOMMENDATIONS]` claim "X is unstable…"). This verifies the T1 direct-contradiction detector flags specific text, not just a global pass/fail.
  - Negative control: `R12Gate.score(fixture.consistent_analysis).effective >= 4` — identical structural shape, no contradiction, same `FakeLLMJudge` stub, R12 passes.
  - `FakeLLMJudge.last_call.input` contains the full assembled document (routing check — R12 requires full-document visibility to detect cross-section premise/conclusion conflicts).
- **Anchor:** `mac/architecture.md §6.1 R12 row` + `quality-rubric.md §6 R12` definition: "Analysis does not contradict itself; premises accepted in findings are not denied in conclusions. T1 (direct contradiction detection: flag specific text contradictions) + T3 (LLM-judge: implicit contradiction assessment across sections)." NOT arch §12.2 (which does not describe this test).
- **Fulfillment:**
  ```python
  bad  = load_fixture("r12_contradiction_findings_recs")
  good = load_fixture("r12_consistent_analysis")

  bad_result = R12Gate.score(bad)
  assert bad_result.effective <= 2
  assert "X is stable" in bad_result.rationale and "X is unstable" in bad_result.rationale
  assert FakeLLMJudge.last_call.input == bad.full_document   # full-document routing check

  good_result = R12Gate.score(good)
  assert good_result.effective >= 4
  ```
- **Tier layering:** T1 (direct contradiction detection: flag specific text contradictions across sections) + T3 (FakeLLMJudge: implicit contradiction assessment across sections). This is a structural calibration test; R12 is priority High per arch §6.1 and does not carry release-blocking semantics.
- **Markers:** `critical`, `mac_gate_calibration`, `no_waiver`  ← **Decision 1 — see §1.4 and §13.3.3 entry #13 (structural calibration test)**
- **Allow-list entry:** yes. Entry #13 position preserved verbatim from v0.1; test body REWRITTEN v0.2 per team-lead DIV-2 C-2 authorization.

### §3.14 Cross-Gate Property Tests

#### §3.14.1 `MAC-T-GATE-PROP-01` Score idempotency
- Purpose: `GateEvaluator.score_all(fixture)` called twice returns identical results (no mutation of fixture, no hidden state).
- Property: `hypothesis.strategies.from_regex(benchmark_question_id_regex)` → assert `score_all(id)(x) == score_all(id)(x)`.
- Markers: `critical`, `mac_gate_calibration`.

#### §3.14.2 `MAC-T-GATE-PROP-02` Section-routing projection commutes
- Purpose: For every gate G, `G.score(full_document) == G.score(full_document.project(GATE_SECTION_ROUTES[G]))`. The judge sees the same subset regardless of whether the caller pre-projects.
- Markers: `critical`, `mac_gate_calibration`.

#### §3.14.3 `MAC-T-GATE-PROP-03` Forge degradation monotonicity
- Purpose: For every gate G in the evidence-penalty set, `G.score(x, forge_degraded=True) <= G.score(x, forge_degraded=False)`. Forge degradation never increases a score.
- Markers: `critical`, `mac_gate_calibration`, `f1_absorption`.

#### §3.14.4 `MAC-T-GATE-PROP-04` Co-eval cap respects ordering
- **Purpose:** Property — for all `(r7_raw, r8_raw) in [1..5]²`, `R8.effective == min(R8.effective_uncapped, r7_raw + 1)` when `forge_degraded=False`.
- **Implementation pseudocode:**
  ```python
  from hypothesis import given, strategies as st

  @given(r7_raw=st.integers(min_value=1, max_value=5),
         r8_raw=st.integers(min_value=1, max_value=5))
  def test_mac_t_gate_prop_04_co_eval_cap(r7_raw, r8_raw):
      gates = score_all(fixture(r7=r7_raw, r8=r8_raw), forge_degraded=False)
      assert gates.R8.effective == min(r8_raw, r7_raw + 1)
      # Also assert R7 is not affected by the cap
      assert gates.R7.effective == r7_raw
  ```
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.14.5 `MAC-T-GATE-PROP-05` Score range invariant
- **Purpose:** Property — for any input, every gate's effective score is in `[1, 5]`.
- **Implementation pseudocode:**
  ```python
  @given(fixture_id=st.sampled_from(ALL_FIXTURE_IDS))
  def test_mac_t_gate_prop_05_score_range(fixture_id):
      gates = score_all(load_fixture(fixture_id))
      for gate_id in ["R1","R2","R3","R4","R5","R6","R7","R8","R9","R10","R11","R12"]:
          score = getattr(gates, gate_id).effective
          assert 1 <= score <= 5, f"{gate_id} effective score out of range: {score}"
  ```
- **Markers:** `critical`, `mac_gate_calibration`.

#### §3.14.6 `MAC-T-GATE-PROP-06` Telemetry event count matches gate count
- **Purpose:** Property — running `score_all()` emits exactly 12 `mac.gate.{rN}.scored` events, one per gate.
- **Implementation:**
  ```python
  @given(fixture_id=st.sampled_from(ALL_FIXTURE_IDS))
  def test_mac_t_gate_prop_06_telemetry_count(fixture_id):
      telemetry.reset()
      _ = score_all(load_fixture(fixture_id))
      gate_events = [e for e in telemetry.events
                     if e.name.startswith("mac.gate.") and e.name.endswith(".scored")]
      assert len(gate_events) == 12
  ```
- **Markers:** `critical`, `mac_gate_calibration`, `mac_label_registry`.

### §3.15 Gate Tests: Tension #3 — Mock vs Live Split Subsection

**Tension #3 (T3 LLM-judge):** The gate tests must run fast in PR-gate without real LLM calls, but must also catch judge drift when real LLMs are used. Preload resolution: **split**.

- **Tier 1 (PR gate, deterministic):** All `MAC-T-GATE-*` tests in §3.2–§3.14 use `FakeLLMJudge` with a lookup table built from `benchmark-questions.md §5` anchors (see §14.3.1). Deterministic, fast, no LLM calls. These tests validate gate LOGIC (co-eval rules, section routing, Forge degradation, domain guards, calibration bucketing).
- **Tier 3 (nightly, live judge):** The drift canary tests in §12 replay the same §5 anchors through a REAL LLM judge; if real scores drift outside the §5 buckets, the nightly build fails. These tests validate that the CALIBRATION remains anchored over time as LLM providers ship new model versions.

The split is structural: the Tier 1 tests depend on `FakeLLMJudge` being a faithful oracle, while the Tier 3 tests verify that the oracle is still faithful. If the Tier 3 tests ever fail, the §5 calibration corpus is updated in `benchmark-questions.md` and the `FakeLLMJudge` lookup table is regenerated (see §14.3.1 lookup-table generation pseudocode).

No `no_waiver` on Tier 3 — live judges drift. The Tier 3 drift canary failing is expected occasionally; it's a signal, not a blocker.

### §3.16 Gate-Level Test Count Summary

| Gate | Tests in §3 | `no_waiver` tests | Priority | Top-5 |
|---|---|---|---|---|
| R1 | 5 (01–05) | 1 (`R1-02`) | 1 | yes |
| R2 | 5 (01–05) | 1 (`R2-02`) | 1 | yes |
| R3 | 5 (01–05) | 1 (`R3-02`) | 2 | — |
| R4 | 6 (01–06) | 2 (`R4-02`, `R4-06`) | 1 | yes |
| R5 | 5 (01–05) | 1 (`R5-02`) | 1 | yes |
| R6 | 5 (01–05) | 0 | 2 | — |
| R7 | 6 (01–06) | 1 (`R7-02`) | 1 | yes |
| R8 | 6 (01–06) | 1 (`R8-02`) | 1 | — |
| R9 | 5 (01–05) | 0 | 2 | — |
| R10 | 5 (01–05) | 0 | 2 | — |
| R11 | 5 (01–05) | 2 (`R11-02`, `R11-05`) | 1 | — |
| R12 | 5 (01–05) | 1 (`R12-05`) | 1 | — |
| Catalog snapshot | 1 (`GATE-CATALOG-SNAPSHOT-01`) | 0 | — | — |
| Cross-gate property | 6 (`GATE-PROP-01..06`) | 0 | — | — |
| **Total** | **75** | **11** | | |

**Note on `no_waiver` count in §3:** 11 tests. One of those (`MAC-T-GATE-R4-06`, the R4 Req-F deterministic structural test) is also referenced from §5.1. The total number of `no_waiver` tests in MAC is 10, because `R4-06` is counted in §5.1 as `MAC-T-ASYM-R-F-02` alias. **Resolved — see §13.3 allow-list for the canonical count.** Only one of the two IDs appears in the allow-list; the other is a cross-reference alias in the doc.

**Authoritative `no_waiver` count reconciliation** (Decision 1 — see §1.4 prose and §13.3.3 ratified allow-list entries 4–13):
- `MAC-T-GATE-R1-02` — R1 calibration anchor (§13.3.3 entry #4)
- `MAC-T-GATE-R2-02` — R2 calibration anchor (§13.3.3 entry #5)
- `MAC-T-GATE-R3-02` — R3 calibration anchor (§13.3.3 entry #6)
- `MAC-T-GATE-R4-02` — R4 calibration anchor (§13.3.3 entry #7)
- `MAC-T-GATE-R5-02` — R5 calibration anchor (§13.3.3 entry #8)
- `MAC-T-GATE-R7-02` — R7 calibration anchor (§13.3.3 entry #9)
- `MAC-T-GATE-R8-02` — R8 calibration anchor (§13.3.3 entry #10)
- `MAC-T-GATE-R11-02` — R11 calibration anchor (§13.3.3 entry #11)
- `MAC-T-GATE-R11-05` — R11 structural calibration (Scenario Coverage property test; §13.3.3 entry #12)
- `MAC-T-GATE-R12-05` — R12 structural calibration (direct contradiction detector; §13.3.3 entry #13)

That is **10 MAC `no_waiver` tests** carrying Decision 1's `no_waiver` discipline. The Req-F deterministic sub-test (`MAC-T-GATE-R4-06` / `MAC-T-ASYM-R-F-02`) is ADDITIONAL — it's a split deterministic carrier per Decision 1, ratified in §13.3.3 entry #14 but NOT counted as one of the 10 calibration items. See §13.3 for the full allow-list expansion and §3.16.1 below for the exact reconciliation.

#### §3.16.1 Final `no_waiver` MAC inventory (authoritative)

| # | Test ID | Section | Type | Allow-list entry (§13.3.3) |
|---|---|---|---|---|
| 1 | `MAC-T-GATE-R1-02` | §3.2.2 | calibration anchor | #4 |
| 2 | `MAC-T-GATE-R2-02` | §3.3.2 | calibration anchor | #5 |
| 3 | `MAC-T-GATE-R3-02` | §3.4.2 | calibration anchor | #6 |
| 4 | `MAC-T-GATE-R4-02` | §3.5.2 | calibration anchor | #7 |
| 5 | `MAC-T-GATE-R5-02` | §3.6.2 | calibration anchor | #8 |
| 6 | `MAC-T-GATE-R7-02` | §3.8.2 | calibration anchor | #9 |
| 7 | `MAC-T-GATE-R8-02` | §3.9.2 | calibration anchor | #10 |
| 8 | `MAC-T-GATE-R11-02` | §3.12.2 | calibration anchor | #11 |
| 9 | `MAC-T-GATE-R11-05` | §3.12.5 | structural calibration (Scenario Coverage property) | #12 |
| 10 | `MAC-T-GATE-R12-05` | §3.13.5 | structural calibration (direct contradiction detector) | #13 |

Total: **10 MAC `no_waiver` tests** (8 gate calibration anchors + 2 structural calibration tests). Items 9 (Req-F) and 11 (Persona 3) are split per §2.3 and land in §5 and §10 respectively — their DETERMINISTIC sub-tests (`MAC-T-ASYM-R-F-02`, `MAC-T-ADV-P3-01`) carry `no_waiver` but are NOT counted in the 10; they are documented as "split deterministic carriers" and tracked separately in §13.3's allow-list as entries #14 and #15.

**Allow-list total reconciliation:** The §13.3.3 ratified allow-list has **16 entries** — 1 Runtime ratified (entry #1) + 2 Runtime provisional PENDING AUDIT at 5.5 (entries #2, #3) + 10 MAC gate calibration tests above (entries #4–#13) + 2 MAC split deterministic carriers (entries #14, #15) + 1 self-reference (entry #16) = 16 total. Ratification rationale in §13.3.3.1 — Option 1 ratified 2026-04-14.

---

## §4 3-Cycle Iteration Controller Tests

The 3-cycle iteration controller at `praxis/kernel/mac/cycle/iteration_controller.py` is the heart of MAC. It runs a 3-pass cycle over Producer → Reviewer → Adjudicator, with state-machine semantics, budget enforcement, backtracking, parallelism determinism, and Forge fallback. Tests in this section are property-based where possible, state-transition-based where not.

### §4.1 State Machine Definition

Regenerated byte-for-byte from `mac/architecture.md §5.2 State Machine` (arch lines 505–558). The nine states and their transitions are the ratified architectural structure:

```
states = {INTERPRET, DECOMPOSE, CYCLE_1_PRODUCE, CYCLE_2_REVIEW,
          CYCLE_3_VERIFY, BACKTRACK_SET, PUBLISH, COMPLETE, FAILED}

transitions = {
  INTERPRET       → DECOMPOSE,
  DECOMPOSE       → CYCLE_1_PRODUCE,
  CYCLE_1_PRODUCE → CYCLE_2_REVIEW,
  CYCLE_2_REVIEW  → CYCLE_3_VERIFY,           # arch §5.4 parallelism runs inside this phase
  CYCLE_3_VERIFY  → PUBLISH                   # normal path: all Critical gates ≥ 3
                  | BACKTRACK_SET             # first Critical gate failure (any R1/R2/R4/R5/R7 raw score < 3) AND backtrack_count == 0
                  | FAILED,                   # second consecutive Critical gate failure when backtrack_count == 1
  BACKTRACK_SET   → CYCLE_1_PRODUCE,          # re-enter cycle_1 with backtrack_count = 1
  PUBLISH         → COMPLETE,                 # §8 Learning Loop write via Memory.mac.publish
  # Terminal failure transitions (arch §5.2 footnote):
  CYCLE_1_PRODUCE → FAILED,                   # BudgetExceededError from Runtime (§5.7 ResourceBudget)
  CYCLE_2_REVIEW  → FAILED,                   # BudgetExceededError from Runtime
  CYCLE_3_VERIFY  → FAILED,                   # BudgetExceededError from Runtime
}

terminal_states = {COMPLETE, FAILED}
initial_state   = INTERPRET
```

**State name policy:** these state identifiers are transcribed verbatim from arch §5.2 (upper-cased for Python `State` enum convention). The arch prose uses snake-case node names (`interpret`, `decompose`, etc.); the Python enum uses upper-case. Either representation refers to the same architectural state.

**Critical properties from arch §5.2:**

1. The state machine is **linear** through cycles 1/2/3 in order — there is no stability-based early termination, no per-cycle abort, no user-initiated mid-cycle cancel. The only ways to leave the cycle path before `CYCLE_3_VERIFY` are (a) `BudgetExceededError` from Runtime → `FAILED`, and (b) the backtrack loop on first-Critical-failure.
2. `BACKTRACK_SET` is entered **exactly once per task** (arch §5.2 footnote: "second consecutive Critical gate failure when `backtrack_count == 1`"). The loop bound is built into the state machine — after one backtrack, the next Critical failure terminates to `FAILED`.
3. `PUBLISH` and `COMPLETE` are two distinct states in arch §5.2 — `PUBLISH` is the Learning Loop write, `COMPLETE` is the terminal acknowledgment. Tests must distinguish them.
4. There is **no `HARD_FAIL` state.** Arch §6.1 marks R11 and R12 as priority High and High respectively — not hard-fail gates. The "score=1 short-circuit" pattern from v0.1 §4.1 was fabricated. Forge-degradation is handled behaviorally per arch §5.6 + §6.3 SQ-7 step 3 (R7 penalty applied last), not as a state transition.
5. There is **no `FORGE_FALLBACK` state.** Arch §5.6 describes Forge Fallback Handling as a behavioral path (apply R7 penalty, continue the cycle); it does not introduce a new state.

### §4.1A Property-Test Harness Setup

The state machine property tests use `hypothesis.stateful.RuleBasedStateMachine`. Setup:

```python
# tests/mac/cycle/test_state_machine.py
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, Bundle
from hypothesis import strategies as st
from praxis.kernel.mac.cycle.iteration_controller import IterationController, State

class MacCycleStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.controller = IterationController(
            judge=FakeLLMJudge(lookup_table=build_default_table()),
            reviewer=FakeReviewerAgent(lookup_table=build_default_reviewer_table()),
            clock=FrozenClock(initial=datetime(2026, 4, 14)),
            compressor=FakeCompressor(force_degradation=False),
            metadata_store=InMemoryMacBootstrapMetadataStore(),
        )
        self.visited_states: set[State] = {State.INTERPRET}
        self.transitions_taken: list[tuple[State, State]] = []

    @rule(fixture_id=st.sampled_from(FIXTURE_IDS))
    def feed_fixture(self, fixture_id: str):
        prev = self.controller.state
        self.controller.advance(fixture_id)
        post = self.controller.state
        self.visited_states.add(post)
        self.transitions_taken.append((prev, post))

    @invariant()
    def all_transitions_allowed(self):
        assert all((a, b) in ALLOWED_TRANSITIONS for a, b in self.transitions_taken), \
            f"Invalid transition found: {self.transitions_taken}"

    @invariant()
    def never_negative_cycle(self):
        assert self.controller.cycle_count >= 0

TestMacCycleStateMachine = MacCycleStateMachine.TestCase
```

The `ALLOWED_TRANSITIONS` constant is the set of `(state_before, state_after)` tuples defined in §4.1. Hypothesis will attempt to drive the machine into illegal states; the invariants will catch any slip.

**Minimization:** When Hypothesis finds a failing sequence, it minimizes to the smallest reproducing trace. That trace is logged to `tests/mac/cycle/failures/` with a timestamp, so a re-run can replay the exact sequence.

### §4.2 State Machine Property Tests

#### §4.2.1 `MAC-T-CYCLE-STATE-01` Reachability of both terminal states
- **Purpose:** Using `hypothesis.stateful.RuleBasedStateMachine`, drive random fixtures and assert both arch §5.2 terminal states (`COMPLETE`, `FAILED`) are reachable. `COMPLETE` is reached via the normal path (`CYCLE_3_VERIFY → PUBLISH → COMPLETE`). `FAILED` is reached via either of arch §5.2's two terminal failure transitions: (a) `BudgetExceededError` from Runtime, or (b) second consecutive Critical gate failure at `CYCLE_3_VERIFY` with `backtrack_count == 1`.
- **Anchor:** `mac/architecture.md §5.2 state machine` (lines 505–558) + §5.2 terminal transitions footnote (lines 555–557).
- **Fulfillment:** Hypothesis state machine reaches both `State.COMPLETE` and `State.FAILED` within 500 steps. Failure mode: Hypothesis minimizes to smallest failing trace and logs to `tests/mac/cycle/failures/`.
- **Marker set:** `critical`, `mac_self_consistency`.

#### §4.2.2 `MAC-T-CYCLE-STATE-02` No invalid transitions
- **Purpose:** Property test — no state transition occurs outside the `transitions` relation defined in §4.1 (regenerated from arch §5.2). Every `IterationController.advance()` call either follows an allowed edge or raises `InvalidStateTransitionError`.
- **Anchor:** `mac/architecture.md §5.2`.
- **Fulfillment:** `hypothesis.stateful` property asserts `for all (s_before, input) → s_after: (s_before, s_after) in ALLOWED_TRANSITIONS OR isinstance(result, InvalidStateTransitionError)`.
- **Markers:** `critical`, `mac_self_consistency`.

#### §4.2.3 — RETIRED v0.3
- **MAC-T-CYCLE-STATE-03 retired.** The v0.1/v0.2 test asserted a "stability-based early termination" path (cycle 2 score equilibrium → `State.TERMINATED` without running cycle 3). **No such path exists in arch §5.2**: the state machine is linear through `CYCLE_1_PRODUCE → CYCLE_2_REVIEW → CYCLE_3_VERIFY` in order, with no stability check. The v0.1 test was a fabrication. If cycle_3 early-exit is ever needed, arch §5 must be extended first (Winston-owned decision, not a test-strategy patch). The test ID `MAC-T-CYCLE-STATE-03` is left as an intentional gap in the sequential numbering; see §1.7 v0.3 changelog for the deletion rationale.

#### §4.2.4 `MAC-T-CYCLE-STATE-04` Second consecutive Critical gate failure terminates to `FAILED`
- **Purpose:** Arch §5.2 footnote (lines 555–557) defines the second-terminal-failure transition: `cycle_3_verify → failed on second consecutive Critical gate failure when backtrack_count == 1`. This test exercises exactly that path. In cycle 1, any Critical gate (R1 Epistemic Calibration, R2 Question Fidelity, R4 Steelman Completeness, R5 Dissent Preservation, R7 Reasoning Traceability — the 5 Critical gates per arch §6.1) scores raw < 3, triggering `BACKTRACK_SET` and re-entry to `CYCLE_1_PRODUCE` with `backtrack_count = 1`. In the second attempt, another (or the same) Critical gate again scores raw < 3, and because `backtrack_count == 1` the controller transitions to `FAILED` rather than back-tracking again.
- **Anchor:** `mac/architecture.md §5.2 state machine footnote` (lines 555–557) + `§6.1 R1/R2/R4/R5/R7 Critical priorities`.
- **Fulfillment:**
  ```python
  fixture = build_fixture_where_r4_fails_both_cycles()  # R4 raw = 2 in both cycle 1 and cycle 2
  result = controller.run(fixture)
  assert result.final_state == State.FAILED
  assert result.backtrack_count == 1
  assert result.terminal_reason == "second_consecutive_critical_gate_failure"
  # Verify backtrack actually fired between the two CYCLE_3_VERIFY visits
  assert result.state_transition_log.count(State.BACKTRACK_SET) == 1
  assert result.state_transition_log.count(State.CYCLE_3_VERIFY) == 2
  ```
- **Critical architectural property:** this is NOT a hard-fail short-circuit. Both cycles run to `CYCLE_3_VERIFY` before the terminal transition fires. There is no early exit from cycle 1 on R11 or R12 score 1 — those gates are not hard-fail per arch §6.1.
- **Markers:** `critical`, `mac_self_consistency`.

#### §4.2.5 `MAC-T-CYCLE-STATE-05` Forge-degradation behavioral path (cycle-level integration)
- **Purpose:** Arch §5.6 describes Forge Fallback Handling as a **behavioral** path, not a state-machine state. When `CompressionForge.compress()` returns `reasoning_preserved=False`, the controller does NOT transition to a dedicated "fallback" state — instead, it proceeds through the normal cycle and the Quality Gate Engine applies the R7 penalty per arch §6.3 SQ-7 step 3 (penalty applied to `R7_effective` only, AFTER Req-C co-eval caps). The telemetry event `mac.cycle.forge_degradation_detected` is emitted when the flag is observed. This test exercises the cycle-level wire-up of Forge-degradation → R7 penalty, complementing the gate-level test `MAC-T-GATE-R7-05` (§3.8.5 — which is the unit-level test of the same semantic).
- **Anchor:** `mac/architecture.md §5.6 Forge Fallback Handling (behavioral)` + `§6.3 SQ-7 ordering step 3`.
- **Fulfillment:**
  ```python
  fixture = build_fixture_where_r7_raw_is_4()
  # Force CompressionForge to return reasoning_preserved=False on cycle 2 boundary
  fake_compressor = FakeCompressor(force_degradation=True)
  result = controller.run(fixture, compressor=fake_compressor)
  # Normal path — no fabricated FORGE_FALLBACK state
  assert result.final_state in (State.COMPLETE, State.FAILED)
  # R7_effective reflects the penalty applied AFTER Req-C caps
  assert result.final_scores.R7.effective == 3  # raw 4 minus Forge penalty per SQ-7 step 3
  assert result.final_scores.R7.forge_degraded == True
  # Telemetry observation
  assert any(e.name == "mac.cycle.forge_degradation_detected" for e in telemetry.events)
  # Critical ordering property: R8 cap is computed from RAW R7 (pre-Forge), not penalized R7
  if result.final_scores.R8.raw == 4:
      assert result.final_scores.R8.effective == 4  # min(4, raw R7 + 1) = min(4, 5) = 4; NOT min(4, 3+1)
  ```
- **Markers:** `critical`, `mac_self_consistency`, `f1_absorption`.
- **Note:** this test is the cycle-level complement to `MAC-T-GATE-R7-05` (§3.8.5). §3.8.5 is the gate-unit test asserting `R7Gate.score(fixture, raw=4, forge_degraded=True).effective == 3` in isolation. §4.2.5 asserts the same semantic propagates through the full 3-cycle pipeline with the SQ-7 step-ordering enforced by the cycle controller (not just the gate evaluator).

### §4.3 Budget Enforcement Tests

#### §4.3.1 `MAC-T-CYCLE-BUDGET-01` Token budget halt transitions to `FAILED` via `BudgetExceededError`
- **Purpose:** When cumulative token usage exceeds `ResourceBudget.token_budget`, Runtime's Spawner raises `BudgetExceededError` per runtime/architecture.md §4.3 ResourceBudget enforcement. The MAC controller catches this at the next cycle boundary and transitions to `State.FAILED` per arch §5.2 footnote terminal transition.
- **Anchor:** `mac/architecture.md §5.7 ResourceBudget Defaults` + `runtime/architecture.md §4.3 ResourceBudget` + `mac/architecture.md §5.2 terminal transition footnote`.
- **Fulfillment:** `result = controller.run(fixture, token_budget=1000); assert result.final_state == State.FAILED AND result.terminal_reason == "budget_exceeded" AND result.total_tokens <= 1000 + cycle_1_overhead`.
- **Markers:** `critical`, `integration`.

#### §4.3.2 `MAC-T-CYCLE-BUDGET-02` Wall-clock budget halt
- **Purpose:** Using `FrozenClock`, advance time past `ResourceBudget.wall_clock_budget` from arch §5.7; assert Runtime raises `BudgetExceededError` and the controller transitions to `State.FAILED` at the next cycle boundary.
- **Anchor:** `mac/architecture.md §5.7 ResourceBudget Defaults` + `runtime/architecture.md §4.3`.
- **Fulfillment:** `result = controller.run(fixture, wall_clock_budget=30s); assert result.final_state == State.FAILED AND result.elapsed_seconds <= 30 + cycle_overhead`.
- **Markers:** `critical`, `wall_clock`.

#### §4.3.3 `MAC-T-CYCLE-BUDGET-03` Pi-Mono CostTracker integration
- **Purpose:** Every cycle emits a `CostTracker.record_call()` event for each producer/reviewer/adjudicator invocation. Assert `CostTracker.total_cost` matches the sum of per-call costs.
- **Anchor:** `mac/architecture.md §10.1 Pi-Mono Integration` + `pi-mono/architecture.md §4.2 CostTracker hot path`.
- **Fulfillment:** `CostTracker.total_cost == sum(FakeLLMJudge.call_log_costs)`.
- **Markers:** `critical`, `integration`.

### §4.4 Backtracking Tests

#### §4.4.1 `MAC-T-CYCLE-BACKTRACK-01` Backtrack re-entry to cycle 1 re-uses prior cycle artifacts
- **Purpose:** When `CYCLE_3_VERIFY` fires `BACKTRACK_SET` (first Critical gate failure, `backtrack_count == 0`) and re-enters `CYCLE_1_PRODUCE`, the producer receives the prior-cycle reviewer critique AND the prior-cycle producer output via the DeliberationState threaded through the Phase Runner. Assert both are passed to the re-entry producer prompt.
- **Anchor:** `mac/architecture.md §5.5 Backtracking on Critical Gate Failure` + `§5.3 Phase Runner` (state threading) + `§7.1 Req-F`.
- **Fulfillment:** `FakeProducer.call_log[1].input contains fixture.pre_backtrack_reviewer_critique AND fixture.pre_backtrack_producer_output`.
- **Markers:** `critical`.

#### §4.4.2 `MAC-T-CYCLE-BACKTRACK-02` Backtrack only fires once per task
- **Purpose:** Per arch §5.2 footnote (lines 555–557), `BACKTRACK_SET` is entered exactly once per task — after `backtrack_count == 1`, a second Critical failure terminates to `FAILED` rather than re-entering `BACKTRACK_SET`. Assert this via a fixture where cycle 1 and cycle 2 both fail Critical gates: `state_transition_log.count(State.BACKTRACK_SET) == 1` and `final_state == State.FAILED`.
- **Anchor:** `mac/architecture.md §5.2 footnote` + `§5.5 Backtracking on Critical Gate Failure`.
- **Markers:** `critical`.

### §4.5 Parallelism Determinism — Tension #2 Resolution

**Tension #2 (Cycle 2 parallelism):** The architecture allows cycle 2 to run multiple reviewer agents in parallel (for quorum-style review). How do we test determinism when the underlying execution is parallel? Preload resolution: **Deterministic Replay Pattern**.

#### §4.5.1 Deterministic Replay Pattern (subsection — design-level)

**Pattern:** All parallel reviewer agents are invoked via `ParallelReviewerPool.submit_all(reviewer_indices)`, which under test conditions substitutes a `DeterministicReplayPool` that:
1. Accepts all submissions.
2. Executes them in **strict sequential order of `reviewer_index`** (NOT in wall-clock submission order).
3. Collects results in a deterministic tuple keyed by `reviewer_index`.
4. Injects a `FrozenClock.advance(1s)` between each submission to synchronize virtual time.

This pattern removes all sources of non-determinism from cycle 2 under test while leaving the production code path unchanged. In production, `ParallelReviewerPool.submit_all()` uses a real `asyncio.gather`; under test, a fixture monkeypatches it to `DeterministicReplayPool`.

The pattern is inherited from `runtime/test-strategy.md §6.4 Deterministic Async Replay` with MAC-specific adaptations for reviewer-index keying.

#### §4.5.2 `MAC-T-CYCLE-PARALLEL-01` Replay determinism
- **Purpose:** Running the same cycle 2 input 1000 times through `DeterministicReplayPool` produces 1000 identical outputs.
- **Fulfillment:** `set(run_cycle_2(fixture) for _ in range(1000)) == {expected_single_output}` (cardinality 1).
- **Markers:** `critical`, `mac_self_consistency`.

#### §4.5.3 `MAC-T-CYCLE-PARALLEL-02` Reviewer-index ordering is strict
- **Purpose:** Reviewer outputs are ordered by `reviewer_index`, not by submission time. Assert output tuple ordering matches `sorted(reviewer_indices)`.
- **Fulfillment:** `[r.reviewer_index for r in pool.results()] == sorted([r.reviewer_index for r in pool.results()])`.
- **Markers:** `critical`, `mac_self_consistency`.

#### §4.5.4 `MAC-T-CYCLE-PARALLEL-03` Production code path uses real `asyncio.gather`
- **Purpose:** Negative test — assert that without the test fixture, `ParallelReviewerPool.submit_all()` calls `asyncio.gather` (verified via `inspect.getsource` grep on `asyncio.gather` substring, since we can't easily test concurrency in CI).
- **Anchor:** `mac/architecture.md §5.4 Cycle 2 Parallelism`.
- **Markers:** `static`, `critical`.

### §4.6 Forge-Degradation Ordering — Tension #4 Resolution

**Tension #4 (Forge fallback):** Forge-degradation can trigger at any cycle boundary, and SQ-7 specifies a strict ordering: (1) raw scores → (2) co-eval caps using RAW R7 → (3) Forge penalty LAST. Tests must verify this ordering is observed even under cycle backtracking.

#### §4.6.1 `MAC-T-CYCLE-FORGE-01` SQ-7 ordering worked example
- **Purpose:** With `(R7_raw=4, R8_raw=4, forge_degraded=True)`, assert final `R7_eff=3`, `R8_eff=4` per arch §6.3 SQ-7 three-step ordering.
- **Anchor:** `mac/architecture.md §6.3 SQ-7 ordering` (raw → Req-C caps using raw R7 → Forge penalty last on `R7_effective` only).
- **Fulfillment:** `gates = controller.score_final(r7_raw=4, r8_raw=4, forge_degraded=True); assert gates.R7.effective == 3 AND gates.R8.effective == 4`.
- **Markers:** `critical`, `mac_self_consistency`, `f1_absorption`.

#### §4.6.2 `MAC-T-CYCLE-FORGE-02` Ordering property
- **Purpose:** Property test — for all `(r7_raw, r8_raw, forge_degraded)`, the final scores match the 3-step SQ-7 algorithm, not any interleaved ordering.
- **Fulfillment:** Hypothesis property over `(r7_raw ∈ [1..5], r8_raw ∈ [1..5], forge_degraded ∈ {True, False})`.
- **Markers:** `critical`, `mac_self_consistency`, `f1_absorption`.

#### §4.6.3 `MAC-T-CYCLE-FORGE-03` Telemetry on Forge fallback
- **Purpose:** When Forge fallback triggers, telemetry event sequence is `[mac.cycle.forge_degradation_detected, mac.cycle.forge_fallback_triggered, mac.cycle.forge_single_pass_started]`.
- **Markers:** `critical`, `integration`, `f1_absorption`.

### §4.6A Cycle Telemetry Tests

#### §4.6A.1 `MAC-T-CYCLE-TELEMETRY-01` Per-cycle event sequence
- **Purpose:** A complete normal-path run emits a known sequence of telemetry events through the arch §5.2 state progression: `[mac.cycle.started, mac.cycle.cycle_1_produce_entered, mac.cycle.cycle_2_review_entered, mac.cycle.cycle_3_verify_entered, mac.cycle.publish_entered, mac.cycle.complete]`.
- **Anchor:** `mac/architecture.md §11.2 Metric Catalog` (metric registry) + `§5.2 state machine` (state progression).
- **Fulfillment:** capture `telemetry.events` after a complete run; assert sequence equality (not just set equality — order matters).
- **Markers:** `critical`, `integration`.

#### §4.6A.2 `MAC-T-CYCLE-TELEMETRY-02` Dedup keys are unique within a cycle
- **Purpose:** Within a single cycle run, all emitted events have unique `dedup_key` values. The dedup-key format is defined inside arch §11.3 TelemetryEvent Linkage (format `"mac:" + cycle_id + ":" + event_type + ":" + monotonic_seq` per SQ-8).
- **Anchor:** `mac/architecture.md §11.3 Linkage to Memory's TelemetryEvent` (dedup-key format).
- **Fulfillment:** `len({e.dedup_key for e in telemetry.events}) == len(telemetry.events)`.
- **Markers:** `critical`, `mac_label_registry`.

#### §4.6A.3 `MAC-T-CYCLE-TELEMETRY-03` `monotonic_seq` is sequential
- **Purpose:** The `monotonic_seq` portion of dedup keys for a single cycle is `1, 2, 3, ...` with no gaps.
- **Markers:** `critical`, `mac_label_registry`.

### §4.6B — RETIRED v0.3

**`MAC-T-CYCLE-CANCEL-01`, `MAC-T-CYCLE-CANCEL-02`, `MAC-T-CYCLE-CANCEL-03` retired v0.3.** The v0.1/v0.2 tests described a user-initiated `controller.cancel(reason="user_requested")` API with a `cancellation_reason` field and a `State.TERMINATED` transition. **None of this exists in arch**: arch §5.2 has no `controller.cancel()` method; arch §5.7 is "ResourceBudget Defaults" (not "cancellation semantics"); there is no `State.TERMINATED` in the ratified state machine. A narrow Runtime read (runtime/architecture.md §4.3 + grep for "cancel") confirms that cancellation in Runtime is tied to `BudgetExceededError` and spawn lifecycle — there is no user-initiated mid-cycle cancel API on the MAC controller. Budget-driven termination is already covered by `MAC-T-CYCLE-BUDGET-01` / `BUDGET-02` / `BUDGET-03` in §4.3, which now correctly anchor on arch §5.7 + runtime §4.3. Resource cleanup on budget-driven termination (Postgres connection release, in-flight LLM cancellation) remains a legitimate concern and is tested through the §4.3 budget path and §6 integration tests, not through a fabricated `controller.cancel()` API.

If a user-initiated mid-cycle cancel API is ever needed, arch §5 must be extended first (Winston-owned decision, not a test-strategy patch). Test IDs `MAC-T-CYCLE-CANCEL-01/02/03` are left as intentional gaps in the sequential numbering; see §1.7 v0.3 changelog for the deletion rationale.

### §4.7 Cycle Section-Level Tests

#### §4.7.1 `MAC-T-CYCLE-SEC-01` Section-aware gate router invocation
- **Purpose:** In each cycle, the gate router invokes each gate on its `GATE_SECTION_ROUTES` subset, not the full document (unless the gate is `FULL_DOCUMENT`). Assert `FakeLLMJudge.call_log` contains the correctly-projected subset per gate.
- **Anchor:** `mac/architecture.md §6.2`.
- **Markers:** `critical`, `integration`.

#### §4.7.2 `MAC-T-CYCLE-SEC-02` `GATE_SECTION_ROUTES` byte-equality snapshot
- **Purpose:** `GATE_SECTION_ROUTES` is a frozen Pydantic mapping; assert byte-equality against snapshot `tests/mac/cycle/snapshots/gate_section_routes_v0_1.bin`.
- **Anchor:** `mac/architecture.md §6.2`.
- **Markers:** `static`, `critical`.

### §4.8 Cycle Test Count Summary

| Subsection | Tests | Notes |
|---|---|---|
| §4.2 State machine | 4 (STATE-01, -02, -04, -05) | property-based; STATE-03 retired v0.3 (fabricated stability short-circuit) |
| §4.3 Budget | 3 (BUDGET-01..03) | terminal via `BudgetExceededError` → `State.FAILED` |
| §4.4 Backtracking | 2 (BACKTRACK-01..02) | backtrack fires exactly once per task |
| §4.5 Parallelism (Tension #2) | 3 (PARALLEL-01..03) | |
| §4.6 Forge ordering (Tension #4) | 3 (FORGE-01..03) | |
| §4.6A Telemetry | 3 (TELEMETRY-01..03) | |
| §4.6B Cancellation | 0 | CANCEL-01/02/03 retired v0.3 (user-initiated cancel not in arch) |
| §4.7 Section-level | 2 (SEC-01..02) | |
| **Total** | **20** | (was 24 in v0.2; net −4 from retirements: STATE-03, CANCEL-01, -02, -03) |

---

## §5 Information Asymmetry Tests

Information asymmetry is MAC's core epistemic guarantee. Reviewers must not see producer memory. Producers must not see reviewer critique BEFORE cycle 2 starts. Req-F enforces two-step independence: reviewers construct steelman independently BEFORE reading the producer's `[STEELMAN]` block.

### §5.0 Asymmetry Threat Model

Before specifying tests, the asymmetry threat model articulates what information-leak paths the tests are guarding against. Each path is a concrete attack surface.

| # | Leak path | Attacker | Guard | Test |
|---|---|---|---|---|
| A1 | Producer memory leaks into reviewer prompt | Producer's retrieval augments reviewer's prompt unintentionally | Proxy asymmetry — reviewer proxy lacks `retrieve_similar_tasks` | `MAC-T-ASYM-PROXY-01` |
| A2 | Producer's steelman leaks into reviewer's turn 0 | Reviewer reads producer's output before constructing its own steelman | Req-F two-step protocol; prompt ordering test | `MAC-T-ASYM-R-F-04` |
| A3 | Reviewer critique leaks into producer's cycle 1 | Cycle 1 producer sees reviewer critique from cycle 0 (there is no cycle 0; this is a negative) | Cycle controller state machine | `MAC-T-CYCLE-BACKTRACK-01` (inverse) |
| A4 | Adjudicator publishes to Memory before cycle finishes | Adjudicator's `publish` call races with cycle completion | Event bus role filter | `MAC-T-ASYM-BUS-03` |
| A5 | Reviewer writes to `events_outbox` | Reviewer's proxy has a hidden `publish` method | Proxy role guard | `MAC-T-ASYM-PROXY-03` |
| A6 | `DomainClass` enum mutated at runtime | Hot-patch adds a 6th domain, routing evades domain guards | Enum immutability (Python enum semantics) | `MAC-T-NEG-DOMAIN-CLASS-02` |
| A7 | `GATE_SECTION_ROUTES` mutated at runtime | Routing is changed mid-run, gate sees wrong section | Frozen Pydantic mapping + snapshot | `MAC-T-CYCLE-SEC-02` |

### §5.1 Req-F Two-Step Independence — Reviewer Steelman Protocol

From `mac/architecture.md §7.1 Req-F` and `§12.2 item 9`.

#### §5.1.1 `MAC-T-ASYM-R-F-01` Schema field presence (static)
- **Purpose:** `ReviewerCritique` Pydantic model has both `independent_steelman: str` and `gap_assessment: str` fields. Schema introspection test.
- **Anchor:** `mac/architecture.md §7.1 Req-F reviewer payload`.
- **Fulfillment:** `'independent_steelman' in ReviewerCritique.__fields__ AND 'gap_assessment' in ReviewerCritique.__fields__`.
- **Markers:** `static`, `critical`, `asymmetry_structural`.

#### §5.1.2 `MAC-T-ASYM-R-F-02` Field ordering — deterministic structural (Decision 1 item 9 deterministic)
- **Purpose:** In the serialized JSON payload, `independent_steelman` MUST appear BEFORE `gap_assessment`. This is enforced at the schema level via Pydantic's field order.
- **Anchor:** `mac/architecture.md §7.1 Req-F ordering clause` + `§12.2 item 9 deterministic sub-test`.
- **Fulfillment:** `keys = list(ReviewerCritique.__fields__.keys()); assert keys.index("independent_steelman") < keys.index("gap_assessment")`.
- **Marker set:** `static`, `critical`, `asymmetry_structural`, `no_waiver`  ← **Decision 1 item 9 deterministic portion**
- **Allow-list entry:** yes (as a split deterministic carrier — see §13.3).
- **Note:** This is the same assertion as `MAC-T-GATE-R4-06`. To avoid double-counting, `MAC-T-ASYM-R-F-02` is the canonical ID used in the allow-list; `R4-06` is a cross-reference.

#### §5.1.3 `MAC-T-ASYM-R-F-03` Live reviewer run (critical + asymmetry_structural ONLY)
- **Purpose:** Run a real LLM reviewer on a fixture task. Assert the reviewer's returned `ReviewerCritique` has:
  (a) non-empty `independent_steelman` field;
  (b) the `independent_steelman` token-count > 50 (substantive, not stub);
  (c) the `gap_assessment` field references specific content from BOTH the reviewer's own steelman AND the producer's `[STEELMAN]` (dual-anchor check).
- **Anchor:** `mac/architecture.md §7.1 Req-F live enforcement` + `§12.2 item 9 live sub-test`.
- **Fulfillment:** live assertions above.
- **Marker set:** `critical`, `asymmetry_structural`, `nightly_only`, `mac_gate_calibration`.
- **NOT `no_waiver`** — live judges drift. This test may fail occasionally due to model variance; it is a signal, not a blocker.

#### §5.1.4 `MAC-T-ASYM-R-F-04` Reviewer prompt does NOT contain producer steelman at turn 0
- **Purpose:** At the start of the reviewer's prompt (turn 0), assert the prompt template does NOT include the producer's `[STEELMAN]` block. Only the task description is present. The `[STEELMAN]` block is appended at turn 1 AFTER the reviewer commits to an `independent_steelman`.
- **Anchor:** `mac/architecture.md §7.1 two-step protocol`.
- **Fulfillment:** `reviewer.prompt_at_turn(0) not contains fixture.producer_steelman_block`.
- **Markers:** `critical`, `asymmetry_structural`.

### §5.2 Proxy Asymmetry — Memory Access Guard

From `mac/architecture.md §7.2` and `runtime/architecture.md _construct_memory_proxy` pattern.

#### §5.2.1 `MAC-T-ASYM-PROXY-01` Reviewer proxy lacks `retrieve_similar_tasks`
- **Purpose:** Type-level test — the reviewer's memory proxy object MUST NOT have a `retrieve_similar_tasks` attribute.
- **Anchor:** `mac/architecture.md §7.2 proxy asymmetry` + `memory/architecture.md §4 _construct_memory_proxy`.
- **Fulfillment:** `proxy = _construct_memory_proxy(role=Role.REVIEWER); assert not hasattr(proxy, 'retrieve_similar_tasks')`.
- **Markers:** `static`, `critical`, `asymmetry_structural`.

#### §5.2.2 `MAC-T-ASYM-PROXY-02` Producer proxy has `retrieve_similar_tasks`
- **Purpose:** Complementary — the producer's memory proxy MUST have `retrieve_similar_tasks`.
- **Fulfillment:** `proxy = _construct_memory_proxy(role=Role.PRODUCER); assert hasattr(proxy, 'retrieve_similar_tasks')`.
- **Markers:** `static`, `critical`, `asymmetry_structural`.

#### §5.2.3 `MAC-T-ASYM-PROXY-03` Adjudicator proxy lacks writes
- **Purpose:** Type-level — the adjudicator's proxy has NO write methods (`publish`, `backfill`, etc.).
- **Fulfillment:** `proxy = _construct_memory_proxy(role=Role.ADJUDICATOR); assert not any(hasattr(proxy, m) for m in ['publish', 'backfill', 'write_result'])`.
- **Markers:** `static`, `critical`, `asymmetry_structural`.

#### §5.2.4 `MAC-T-ASYM-PROXY-04` All agent spawns route through `_construct_memory_proxy`
- **Purpose:** Source-level grep test — every agent spawn site in `praxis/kernel/mac/` calls `_construct_memory_proxy` with a role parameter. No agent receives a raw memory client.
- **Fulfillment:** grep `praxis/kernel/mac/` for `Memory\(`; assert all matches are inside `_construct_memory_proxy` OR are test fixtures.
- **Markers:** `static`, `critical`, `asymmetry_structural`.

#### §5.2.5 `MAC-T-ASYM-PROXY-05` S4.R-01 inherited structural invariant
- **Purpose:** Inherited from `runtime/test-strategy.md §6.3 S4.R-01` — the proxy factory returns a concrete `Protocol` implementation, not a raw client. MAC extends the invariant to cover reviewer/adjudicator roles.
- **Markers:** `static`, `critical`, `asymmetry_structural`.

### §5.3 Bus Filter Tests

From `runtime/architecture.md §7.5 Layer 2 communication-bus filtering` (bus filtering is a Runtime concern; MAC inherits the filter via `mac/architecture.md §7.5 The Symmetric Asymmetry Boundary` cross-reference to Runtime §7.5). Arch §7.3 is "Information Hiding" and does not describe the bus filter.

#### §5.3.1 `MAC-T-ASYM-BUS-01` Reviewer cannot publish `mac.publish` events
- **Purpose:** The event bus filter rejects `mac.publish` events published by any agent with `role=REVIEWER`.
- **Anchor:** `runtime/architecture.md §7.5 Layer 2 communication-bus filtering` + `mac/architecture.md §7.5 Symmetric Asymmetry Boundary`.
- **Fulfillment:** `with pytest.raises(BusFilterReject): bus.publish("mac.publish", payload={...}, role=Role.REVIEWER)`.
- **Markers:** `critical`, `asymmetry_structural`.

#### §5.3.2 `MAC-T-ASYM-BUS-02` Only producer can publish `mac.publish`
- **Purpose:** Complementary — producer CAN publish.
- **Fulfillment:** `bus.publish("mac.publish", payload={...}, role=Role.PRODUCER)` succeeds.
- **Markers:** `critical`, `asymmetry_structural`.

#### §5.3.3 `MAC-T-ASYM-BUS-03` Only adjudicator can publish `mac.adjudication_complete`
- **Markers:** `critical`, `asymmetry_structural`.

### §5.4 Asymmetry Test Count

| Subsection | Tests |
|---|---|
| §5.1 Req-F two-step | 4 |
| §5.2 Proxy asymmetry | 5 |
| §5.3 Bus filter | 3 |
| **Total** | **12** |

---

## §6 Integration Tests

Integration tests wire up real Postgres (via `testcontainers`), real Pi-Mono `CostTracker`, real Memory proxy scaffolding, but use `FakeLLMJudge` / `FakeReviewerAgent` — no live LLM calls.

### §6.0 Integration Test Environment

Integration tests run in **Tier 2** per §2.2: real Postgres via `testcontainers`, real Pi-Mono `CostTracker` wired to the real Postgres instance, real Memory proxy with the sidecar `mac_bootstrap_metadata` migration applied, real Runtime spawner STUB (the Stage 4 runtime scaffolding), real MCP shape guard. NO live LLM calls — the LLM endpoint in integration tests is `FakeLLMJudge` with a lookup table pre-built from §5 anchors and §3 fixtures.

**Environment setup (tests/mac/integration/conftest.py):**

```python
import pytest
from testcontainers.postgres import PostgresContainer
from praxis.kernel.mac.bootstrap import BootstrapLoader
from praxis.kernel.mac.testing.fakes import (
    FakeLLMJudge, FakeReviewerAgent, FakeCompressor, FrozenClock
)

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        conn_str = pg.get_connection_url()
        # Apply migrations in order:
        #   1. Memory base migrations (from memory/migrations/)
        #   2. Pi-Mono events_outbox migration
        #   3. MAC sidecar mac_bootstrap_metadata migration
        _apply_migrations(conn_str)
        yield pg

@pytest.fixture
def pg_conn(postgres_container):
    conn = _get_connection(postgres_container)
    sp = conn.savepoint()
    yield conn
    conn.rollback_to_savepoint(sp)

@pytest.fixture
def mac_pipeline(pg_conn):
    """
    Fully-wired MAC pipeline with Fake LLM judges but real Postgres, real
    CostTracker, real Memory proxy, real bus filter.
    """
    return build_mac_pipeline(
        pg=pg_conn,
        judge=FakeLLMJudge(lookup_table=DEFAULT_INTEGRATION_TABLE),
        reviewer=FakeReviewerAgent(lookup_table=DEFAULT_REVIEWER_TABLE),
        compressor=FakeCompressor(force_degradation=False),
        clock=FrozenClock(initial=datetime(2026, 4, 14)),
    )
```

The `DEFAULT_INTEGRATION_TABLE` is pre-built at session start from both `benchmark-questions.md §5` anchors AND the fixtures declared by each `§3.x.y` test. Integration tests that need different scores subclass the fixture.

### §6.1 Pi-Mono CostTracker Integration

#### §6.1.1 `MAC-T-INT-COSTTRACKER-01` `events_outbox` write on every LLM call
- **Purpose:** Every call to `FakeLLMJudge` or `FakeReviewerAgent` through MAC triggers a `CostTracker.record_call()` which writes to Pi-Mono's `events_outbox` table.
- **Anchor:** `mac/architecture.md §10.1 Pi-Mono Integration` + `pi-mono/architecture.md §3 events_outbox`.
- **Fulfillment:** `pg.execute("SELECT COUNT(*) FROM events_outbox WHERE event_type='mac.llm_call'").fetchone()[0] == expected_call_count`.
- **Markers:** `integration`, `critical`.

#### §6.1.2 `MAC-T-INT-COSTTRACKER-02` Cost aggregation matches
- **Purpose:** `CostTracker.get_cycle_cost(cycle_id)` returns the sum of per-call costs for that cycle.
- **Fulfillment:** `abs(tracker.get_cycle_cost(cid) - sum_fixture_costs) < 0.0001`.
- **Markers:** `integration`, `critical`.

#### §6.1.3 `MAC-T-INT-COSTTRACKER-03` xmin identity preserved on outbox writes
- **Purpose:** Inherited from runtime `F-13.C1` — assert `events_outbox.xmin` is set on every MAC insert (atomicity proof via Postgres system column).
- **Anchor:** `runtime/test-strategy.md §7.2 F-13.C1` inheritance.
- **Markers:** `integration`, `critical`.

### §6.2 Memory Named-Contract Integration

#### §6.2.1 `MAC-T-INT-MEMORY-PUBLISH-01` `mac.publish` contract shape
- **Purpose:** When MAC completes the verify-publish-complete path (arch §5.2 `CYCLE_3_VERIFY → PUBLISH`), it publishes `mac.publish` with payload schema matching `memory/architecture.md:913`. Assert the payload fields match the contract.
- **Anchor:** `memory/architecture.md:913` + `mac/architecture.md §10.2 Memory Integration`.
- **Fulfillment:** `payload = capture_publish_event(); assert set(payload.keys()) == MAC_PUBLISH_REQUIRED_FIELDS`.
- **Markers:** `integration`, `critical`.

#### §6.2.2 `MAC-T-INT-MEMORY-PUBLISH-02` Publish triggers Memory upsert
- **Purpose:** After `mac.publish` is received, Memory's `tasks` table contains a row with `task_id` and `status='completed'`.
- **Fulfillment:** Postgres assertion.
- **Markers:** `integration`, `critical`.

#### §6.2.3 `MAC-T-INT-MEMORY-REUSE-01` `mac.reuse_successful` contract
- **Purpose:** When the producer reuses a retrieved successful task, `mac.reuse_successful` event is published to Memory with `source_task_id` and `target_task_id`.
- **Anchor:** `memory/architecture.md:914`.
- **Fulfillment:** event capture + field assertion.
- **Markers:** `integration`, `critical`.

#### §6.2.4 `MAC-T-INT-MEMORY-BACKFILL-01` `mac.backfill` contract
- **Purpose:** On bootstrap-loader run, `mac.backfill` events are published in batches of 100 gold-standard items per `memory/architecture.md:915`.
- **Anchor:** `memory/architecture.md:915`.
- **Markers:** `integration`, `mac_bootstrap_loader`.

#### §6.2.5 `MAC-T-INT-MEMORY-ASYMMETRY-WIRE-01` Producer proxy wired to writer role, reviewer to reader
- **Purpose:** Integration — assert that when MAC asks Memory for a producer proxy, Memory returns a writer-role proxy; reviewer gets a reader-role proxy.
- **Markers:** `integration`, `asymmetry_structural`.

### §6.3 Runtime Integration

#### §6.3.1 `MAC-T-INT-RUNTIME-SPAWNER-01` Runtime spawner respects MAC role
- **Purpose:** `RuntimeSpawner.spawn(role=Role.REVIEWER)` injects the reviewer proxy. Test uses real Runtime stub (from Stage 4).
- **Anchor:** `runtime/architecture.md §4` + `mac/architecture.md §10.3 Runtime Integration`.
- **Markers:** `integration`, `critical`.

#### §6.3.2 `MAC-T-INT-RUNTIME-MCP-SHAPE-GUARD-01` `verify_mcp_sdk_shape()` passes
- **Purpose:** MAC calls `verify_mcp_sdk_shape()` at startup; assert version pin `mcp>=1.9.0` holds.
- **Anchor:** `mac/architecture.md §10.3 Runtime Integration` (MCP shape guard + SQ-1 MCP pin inheritance).
- **Markers:** `integration`, `static`, `critical`.

### §6.4 Compression Forge F8 Integration

#### §6.4.1 `MAC-T-INT-FORGE-F8-01` `reasoning_preserved` flag propagates
- **Purpose:** When `CompressionForge.compress()` returns `reasoning_preserved=False`, MAC observes the flag and applies the Forge-degradation behavioral path per arch §5.6 — R7 penalty applied to `R7_effective` only, via arch §6.3 SQ-7 step 3 ordering. This integration test verifies the wire-up between Compression and the MAC Quality Gate Engine; the cycle-level behavioral assertion lives in §4.2.5.
- **Anchor:** `mac/architecture.md §10.4 Compression Integration` + `§5.6 Forge Fallback Handling` + `§6.3 SQ-7 ordering` + `forge/architecture.md F8`.
- **Markers:** `integration`, `f1_absorption`.

#### §6.4.2 `MAC-T-INT-FORGE-F8-02` F8 absorption boundary
- **Purpose:** When Forge absorbs a payload that retains full reasoning chains, `reasoning_preserved=True` and MAC proceeds normally.
- **Markers:** `integration`, `f1_absorption`.

### §6.4A Cross-Module Wire-Up Tests

#### §6.4A.1 `MAC-T-INT-WIREUP-01` Full pipeline smoke test
- **Purpose:** Run a complete MAC pipeline end-to-end with `FakeLLMJudge` (Tier 2). Producer → Reviewer → Adjudicator across the arch §5.2 state progression (`INTERPRET → DECOMPOSE → CYCLE_1_PRODUCE → CYCLE_2_REVIEW → CYCLE_3_VERIFY → PUBLISH → COMPLETE`). Assert the final telemetry log contains the expected event sequence and the Postgres state is consistent with the `COMPLETE` outcome.
- **Anchor:** `mac/architecture.md §5 3-Cycle Iteration Controller` + `§10 Integration Contracts`.
- **Fulfillment:**
  ```python
  result = mac_pipeline.run(fixture.simple_q1_task)
  assert result.final_state == State.COMPLETE
  assert result.composite_score > 60.0
  assert pg.execute("SELECT COUNT(*) FROM events_outbox WHERE event_type LIKE 'mac.%'").scalar() > 0
  assert pg.execute("SELECT COUNT(*) FROM mac_bootstrap_metadata").scalar() > 0  # bootstrap loaded earlier
  ```
- **Markers:** `integration`, `critical`, `wall_clock`.

#### §6.4A.2 `MAC-T-INT-WIREUP-02` Multi-tenant isolation
- **Purpose:** Two MAC pipelines running concurrently with different `task_id`s do not contaminate each other's state. Producer A's memory does not leak into Producer B's prompt.
- **Anchor:** `mac/architecture.md §7.2 Proxy binding to Runtime §4.1` (per-spawn memory proxy isolation) + `§10.3 Runtime Integration`.
- **Fulfillment:** parallel execution of two pipelines; assert the two `events_outbox` traces are independent (no events from cycle A appear in cycle B's dedup namespace, and vice versa).
- **Markers:** `integration`, `critical`, `asyncio_structural`.

#### §6.4A.3 `MAC-T-INT-WIREUP-03` Bootstrap-then-cycle ordering
- **Purpose:** Bootstrap loader runs FIRST, populates the sidecar table, then a cycle runs and uses the bootstrap data via retrieval. Assert ordering and observable side effects.
- **Markers:** `integration`, `mac_bootstrap_loader`, `critical`.

### §6.5 Integration Test Count

| Subsection | Tests |
|---|---|
| §6.1 Pi-Mono CostTracker | 3 |
| §6.2 Memory contracts | 5 |
| §6.3 Runtime spawner | 2 |
| §6.4 Forge F8 | 2 |
| §6.4A Cross-module wire-up | 3 |
| **Total** | **15** |

---

## §7 Evaluation Harness Tests

The evaluation harness is MAC's self-assessment: 10 benchmark questions × 3 baselines (vanilla/enhanced/MAC) = 30 scored runs, with ADR-1 hybrid pass (blind R1–R4/R6–R12 + open R5), ADR-3 Spearman validation (Andrey-checklist on 3 random Qs), top-5 weighted composite, and N=10 directional framing.

### §7.0 Why Evaluation Harness Tests Exist at All

The evaluation harness is MAC's only quantitative self-assessment. Without it, MAC's R3 claim ("MAC outputs are better than enhanced") is unfalsifiable. The 10-Q corpus + 3 baselines + top-5 weighting + ADR-1 hybrid + ADR-3 Spearman mechanism is designed to give MAC a repeatable, directional signal.

But the harness itself has failure modes:
1. **Scoring bug** — composite formula wrong, wins miscount.
2. **ADR-1 leakage** — Pass 1 accidentally sees baseline identity, leading to bias.
3. **Spearman drift** — machine scores miscorrelate with Andrey's manual scores; the automation is secretly broken.
4. **Corpus drift** — a question's text is edited without a v-bump, breaking reproducibility.
5. **Weighting drift** — someone changes weights thinking they're tuning, breaking inter-release comparability.

Each of these failure modes has a test in this section. The §7 tests are "tests for the tests" — they validate the harness logic itself, so that R3 claims from the harness are trustworthy.

### §7.1 Benchmark Harness Authority

From `benchmark-questions.md §2 (10-Q corpus)` + `§6 (baselines)` + `§7 (weighting)` + `§8 (ADR-1 + ADR-3)`:

- **10 questions (verbatim from §2):** Q1–Q10, fixed across releases.
- **3 baselines (from §6):** vanilla (no MAC, no enhancements), enhanced (prompt engineering only), MAC (full 12-gate kernel).
- **Top-5 weighting (§7):** R1, R2, R4, R5, R7 × weight 2; all others × weight 1. Total weight units = 5×2 + 7×1 = 17.
- **Composite score:** `Σ(score × weight) / (17 × 5) × 100`. Max = 100.
- **ADR-1 hybrid pass (§8):** Pass 1 blind R1–R4 + R6–R12 (11 gates), Pass 2 open R5 only (dissent signal, needs producer context).
- **ADR-3 Spearman (§8):** Andrey scores 3 random Qs × 9 outputs = 27 manual scores; Spearman ρ of machine vs manual ≥ 0.6 to validate.
- **N=10 framing:** directional signal, NOT hypothesis test. R3 invalidation triggers: <7-of-10 wins OR <10% average improvement.

### §7.2 Scoring Logic Tests (Unit — FakeBenchmarkOutputs)

These tests exercise the scoring/weighting/ADR-1 hybrid pipeline using `FakeBenchmarkOutputs` (§14.3.5). Deterministic, no live LLM. **S-Q3 bake-in: these are PR-gate tests.**

#### §7.2.1 `MAC-T-BENCH-SCORING-01` Top-5 weighting composite math
- **Purpose:** Given a known `(R1..R12)` score vector, assert composite matches the formula.
- **Anchor:** `benchmark-questions.md §7`.
- **Fulfillment:** `composite(R1=4,R2=4,R3=3,R4=4,R5=3,R6=3,R7=4,R8=4,R9=3,R10=3,R11=5,R12=5) == (4*2+4*2+3*1+4*2+3*2+3*1+4*2+4*1+3*1+3*1+5*1+5*1)/(17*5)*100 == correct_value`.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.2.2 `MAC-T-BENCH-SCORING-02` Weight unit sum = 17
- **Purpose:** Assert weight units sum to 17 (5 top gates × 2 + 7 others × 1 = 10 + 7 = 17).
- **Fulfillment:** `sum(WEIGHTS.values()) == 17`.
- **Markers:** `static`, `critical`, `mac_benchmark_harness`.

#### §7.2.3 `MAC-T-BENCH-SCORING-03` Max composite = 100 when all gates = 5
- **Purpose:** Edge case — all-5 vector scores 100.0.
- **Fulfillment:** `composite(all_fives) == 100.0`.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.2.4 `MAC-T-BENCH-SCORING-04` Min composite = 20 when all gates = 1
- **Purpose:** Edge case — all-1 vector scores 20.0 (5 × 17 / (17 × 5) × 100 = 20).
- **Fulfillment:** `composite(all_ones) == 20.0`.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.2.5 — RETIRED v0.3
- **`MAC-T-BENCH-SCORING-05` retired.** The v0.1/v0.2 test asserted `composite(fixture, r11=1) is None AND result.status == "HARD_FAIL"` — a fabricated hard-fail semantic. Under ratified arch §6.1, **no gate carries release-blocking / hard-fail / short-circuit semantics**; R11 (Scenario Coverage) is priority High, R12 (Internal Consistency) is priority High, neither terminates the composite score to `None`. The composite formula per `benchmark-questions.md §7` is `Σ(score × weight) / (17 × 5) × 100` and is always a well-defined number in `[20, 100]` for any legal score vector. The minimum-composite boundary (all gates = 1 → 20.0) is already covered by §7.2.4 `MAC-T-BENCH-SCORING-04`. The test ID `MAC-T-BENCH-SCORING-05` is left as an intentional gap in the sequential numbering; see §1.7 v0.3 changelog for the deletion rationale.

### §7.3 ADR-1 Hybrid Pass Tests

#### §7.3.1 `MAC-T-BENCH-ADR1-01` Pass 1 is blind to producer identity
- **Purpose:** In Pass 1 (R1–R4, R6–R12), the judge prompt does NOT include producer identity ("vanilla", "enhanced", "MAC"). Only the output text is passed.
- **Anchor:** `benchmark-questions.md §8 ADR-1`.
- **Fulfillment:** `pass1_judge.call_log[i].prompt not contains baseline_id for all i`.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.3.2 `MAC-T-BENCH-ADR1-02` Pass 2 is open for R5 only
- **Purpose:** In Pass 2, only R5 is evaluated, AND the judge receives the producer's full context (including prior iterations) because R5 dissent signal requires context awareness.
- **Fulfillment:** `pass2_judge.gates_evaluated == {"R5"}`.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.3.3 `MAC-T-BENCH-ADR1-03` Pass 1 and Pass 2 scores merge correctly
- **Purpose:** Final score vector is Pass 1 vector for R1–R4/R6–R12 + Pass 2 vector for R5.
- **Fulfillment:** `merged.R5 == pass2.R5 AND merged.R4 == pass1.R4`.
- **Markers:** `critical`, `mac_benchmark_harness`.

### §7.4 ADR-3 Spearman Validation Tests

#### §7.4.1 `MAC-T-BENCH-SPEARMAN-01` Computation correctness
- **Purpose:** Given `andrey_scores.yaml` fixture with known scores, assert `spearman_rho(machine_scores, andrey_scores) == expected`.
- **Anchor:** `benchmark-questions.md §8 ADR-3`.
- **Fulfillment:** numeric assertion within 1e-6 tolerance.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.4.2 `MAC-T-BENCH-SPEARMAN-02` Threshold enforcement
- **Purpose:** `spearman_rho >= 0.6` → validation passes; else validation fails with `SpearmanValidationFailed`.
- **Fulfillment:** `validate(machine, andrey_with_rho_0_55)` raises.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.4.3 `MAC-T-BENCH-SPEARMAN-03` Sample size = 3 questions × 9 outputs = 27 pairs
- **Purpose:** Assert the Spearman computation uses exactly 27 pairs.
- **Fulfillment:** `len(machine_vs_andrey_pairs) == 27`.
- **Markers:** `critical`, `mac_benchmark_harness`.

### §7.5 Baseline Comparison Tests

#### §7.5.1 `MAC-T-BENCH-BASELINE-01` Three baselines produce independent scores
- **Purpose:** The vanilla, enhanced, and MAC baselines produce three independent composites (no cross-contamination).
- **Fulfillment:** three score vectors, three composites; assert no shared mutable state.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.5.2 `MAC-T-BENCH-BASELINE-02` R3 directional win condition
- **Purpose:** For the N=10 directional framing, "MAC wins" is defined as `composite(MAC, Q) > composite(enhanced, Q)`. Assert counter logic: `wins = sum(composite(MAC, q) > composite(enhanced, q) for q in Qs)`.
- **Fulfillment:** `count_wins(fixture.all_win_vs_enhanced) == 10`.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.5.3 `MAC-T-BENCH-BASELINE-03` R3 invalidation trigger — <7-of-10 wins
- **Purpose:** When MAC wins fewer than 7 of 10 questions, result is `R3_INVALIDATION_SUGGESTED`.
- **Anchor:** `benchmark-questions.md §8 R3 invalidation` + `mac/architecture.md §9.5`.
- **Fulfillment:** `run_full_harness(fixture.6_of_10_wins).r3_status == "INVALIDATION_SUGGESTED"`.
- **Markers:** `critical`, `mac_benchmark_harness`.

#### §7.5.4 `MAC-T-BENCH-BASELINE-04` R3 invalidation trigger — <10% average improvement
- **Purpose:** When average composite improvement (MAC vs enhanced) is <10%, result is `R3_INVALIDATION_SUGGESTED`.
- **Fulfillment:** `run_full_harness(fixture.9_pct_avg_improvement).r3_status == "INVALIDATION_SUGGESTED"`.
- **Markers:** `critical`, `mac_benchmark_harness`.

### §7.6 Benchmark Question Corpus Tests

#### §7.6.1 `MAC-T-BENCH-CORPUS-01` Exactly 10 questions loaded
- **Purpose:** `BenchmarkQuestions.load()` returns exactly 10 questions, IDs Q1–Q10.
- **Anchor:** `benchmark-questions.md §2`.
- **Fulfillment:** `set(q.id for q in load()) == {"Q1","Q2",...,"Q10"}`.
- **Markers:** `static`, `critical`, `mac_benchmark_harness`.

#### §7.6.2 `MAC-T-BENCH-CORPUS-02` Question text byte-equality vs §2 snapshot
- **Purpose:** Each question's text matches `benchmark-questions.md §2` byte-for-byte (via snapshot file extracted from the markdown).
- **Markers:** `static`, `critical`, `mac_benchmark_harness`.

### §7.7 §5 Calibration Anchor Tests (Unit)

#### §7.7.1 `MAC-T-BENCH-CALIBRATION-01` 12 gates × 2 anchors = 24 anchors loaded
- **Purpose:** `CalibrationAnchors.load()` returns exactly 24 anchors, keyed by (gate_id, score_level).
- **Anchor:** `benchmark-questions.md §5`.
- **Fulfillment:** `len(load()) == 24`.
- **Markers:** `static`, `critical`, `mac_gate_calibration`.

#### §7.7.2 `MAC-T-BENCH-CALIBRATION-02` Anchor byte-equality vs §5 snapshot
- **Purpose:** Each anchor text byte-equal to source markdown.
- **Markers:** `static`, `critical`, `mac_gate_calibration`.

### §7.8 FakeBenchmarkOutputs Harness Smoke Tests

#### §7.8.1 `MAC-T-BENCH-FAKE-01` End-to-end harness run with deterministic outputs
- **Purpose:** Run the full 30-score pipeline with `FakeBenchmarkOutputs`; assert composite sums and R3 status produce expected values.
- **Fulfillment:** full pipeline deterministic result assertion.
- **Markers:** `integration`, `mac_benchmark_harness`.

#### §7.8.2 `MAC-T-BENCH-FAKE-02` `FakeBenchmarkOutputs` lookup table completeness
- **Purpose:** For each (question_id, baseline) in the 30 combinations, `FakeBenchmarkOutputs.get(qid, baseline)` returns a non-empty pre-scored output.
- **Fulfillment:** no `KeyError` on any of the 30 combinations.
- **Markers:** `static`, `critical`, `mac_benchmark_harness`.

### §7.9 PR-Gate vs Nightly Harness Split (S-Q3 Bake-In)

**S-Q3 ratified answer:** Full 30-score benchmark harness run (10 Qs × 3 baselines) is `nightly_only + mac_benchmark_harness`, NOT PR-gate. Unit tests exercise harness LOGIC using `FakeBenchmarkOutputs`. PR-gate runs only unit/property/contract layer.

#### §7.9.1 `MAC-T-BENCH-NIGHTLY-01` Full 30-score nightly harness
- **Purpose:** In nightly CI, run the full 30-score pipeline with REAL LLM calls. Assert the 30 results are produced, composites are computed, R3 directional status is determined, and the run completes within the wall-clock budget.
- **Anchor:** S-Q3 ratification.
- **Marker set:** `mac_benchmark_harness`, `nightly_only`.
- **NOT in PR gate.**

#### §7.9.2 `MAC-T-BENCH-NIGHTLY-02` Cost budget enforcement on nightly run
- **Purpose:** Nightly harness run budget is capped at ~$X per run (documented in §14.4 CI budget); assert `tracker.total_cost <= budget`.
- **Marker set:** `mac_benchmark_harness`, `nightly_only`, `wall_clock`.

### §7.10 Release-Gate A4 Andrey-in-the-Loop Test (S-Q4 Bake-In)

**S-Q4 ratified answer:** Release-gate test at `tests/release/test_a4_validation.py` with persisted `andrey_scores.yaml` fixture. Automated test verifies Spearman computation is correct GIVEN a sample fixture with known ρ. The human-scoring step is OUT-OF-BAND (manual); only the math is tested here.

#### §7.10.1 `MAC-T-BENCH-A4-01` Release-gate A4 Spearman fixture verification
- **Purpose:** Load `fixtures/a4_andrey_scores_rc1.yaml`; compute Spearman ρ against the machine scores from the same release candidate; assert ρ == known fixture value within tolerance.
- **Anchor:** `benchmark-questions.md §8 ADR-3` + `mac/architecture.md §9.7 A4 release gate`.
- **Target path:** `tests/release/test_a4_validation.py::test_a4_spearman_fixture`.
- **Fulfillment:** `abs(compute_spearman(machine, andrey) - fixture.expected_rho) < 1e-6`.
- **Marker set:** `release_gate`, `mac_benchmark_harness`.
- **NOT in PR gate. NOT in nightly. Runs ONLY on release-candidate tagging.**

#### §7.10.2 `MAC-T-BENCH-A4-02` A4 fixture schema validation
- **Purpose:** `andrey_scores.yaml` matches a Pydantic schema — 3 questions × 9 outputs = 27 scored rows, each with integer score 1–5.
- **Fulfillment:** schema parse + row count.
- **Marker set:** `release_gate`, `static`, `mac_benchmark_harness`.

### §7.10A Composite Score Worked Examples

To make the §7.2 scoring tests concrete, here are three worked examples of the composite formula:

**Example 1 — All gates score 4:**
```
Top-5 (R1, R2, R4, R5, R7) × weight 2: 5 × 4 × 2 = 40
Other 7 gates × weight 1:                7 × 4 × 1 = 28
Sum:                                                 68
Composite = 68 / (17 × 5) × 100 = 68 / 85 × 100 = 80.0
```

**Example 2 — Top-5 score 5, others score 3:**
```
Top-5 × weight 2:    5 × 5 × 2 = 50
Others × weight 1:   7 × 3 × 1 = 21
Sum:                              71
Composite = 71 / 85 × 100 = 83.5
```

**Example 3 — Mixed: R1=5, R2=4, R3=3, R4=4, R5=4, R6=3, R7=4, R8=4, R9=2, R10=2, R11=5, R12=5:**
```
R1 × 2 = 10
R2 × 2 =  8
R3 × 1 =  3
R4 × 2 =  8
R5 × 2 =  8
R6 × 1 =  3
R7 × 2 =  8
R8 × 1 =  4
R9 × 1 =  2
R10 × 1 = 2
R11 × 1 = 5
R12 × 1 = 5
Sum:     66
Composite = 66 / 85 × 100 = 77.6
```

These three examples are baked into `MAC-T-BENCH-SCORING-01` as fixture inputs with `expected_composite ∈ {80.0, 83.5, 77.6}`. The unit test parameterizes over them.

### §7.11 Evaluation Harness Test Count

| Subsection | Tests | Tier |
|---|---|---|
| §7.2 Scoring logic | 5 | 1 |
| §7.3 ADR-1 hybrid | 3 | 1 |
| §7.4 ADR-3 Spearman | 3 | 1 |
| §7.5 Baseline comparison | 4 | 1 |
| §7.6 Corpus | 2 | 1 |
| §7.7 Calibration anchors | 2 | 1 |
| §7.8 Fake harness smoke | 2 | 2 |
| §7.9 Nightly split | 2 | 3 |
| §7.10 A4 release gate | 2 | 4 |
| **Total** | **25** | |

---

## §8 Bootstrap Loader Tests

The bootstrap loader populates the gold-standard corpus into Memory at MAC initialization. From `mac/architecture.md §8.1 Bootstrap Loader Option Y`: sidecar `mac_bootstrap_metadata` table with MAC-owned migration `0001_mac_bootstrap_metadata`. Option X (injection into Memory's schema) is REJECTED.

### §8.0 Bootstrap Loader Design Context

The bootstrap loader is the mechanism that seeds MAC's gold-standard corpus into Memory at MAC first-run. Two design options were considered in the architecture:

- **Option X (REJECTED):** Inject bootstrap metadata directly into Memory's `tasks` table via a Memory-owned migration that adds columns `mac_bootstrap_*`.
- **Option Y (RATIFIED):** Create a sidecar table `mac_bootstrap_metadata` in the Memory schema via a MAC-owned migration `0001_mac_bootstrap_metadata.py` at `praxis/kernel/mac/migrations/`.

Option X was rejected because it would force Memory's schema to change whenever MAC's bootstrap semantics evolve, coupling the two modules. Option Y keeps the coupling minimal: MAC owns its sidecar table, Memory is untouched.

The test suite verifies BOTH that Option Y is implemented correctly AND that Option X is absent. The absence tests are in §11.2 (three-layer negative tests); the presence tests are in §8.1–§8.5.

### §8.1 Sidecar Table Migration Tests

#### §8.1.1 `MAC-T-BOOT-MIGRATION-01` Migration creates sidecar table
- **Purpose:** Running `0001_mac_bootstrap_metadata.py` creates the `mac_bootstrap_metadata` table with the expected columns.
- **Anchor:** `mac/architecture.md §8.1 migration 0001`.
- **Target path:** `praxis/kernel/mac/migrations/0001_mac_bootstrap_metadata.py`.
- **Fulfillment:** `pg.execute("SELECT column_name FROM information_schema.columns WHERE table_name='mac_bootstrap_metadata'")` returns the expected column set.
- **Markers:** `mac_bootstrap_loader`, `integration`, `critical`.

#### §8.1.2 `MAC-T-BOOT-MIGRATION-02` Migration is idempotent (re-run yields no error)
- **Purpose:** Running the migration twice is a no-op.
- **Fulfillment:** migration.apply() twice succeeds without raising.
- **Markers:** `mac_bootstrap_loader`, `integration`, `critical`.

#### §8.1.3 `MAC-T-BOOT-MIGRATION-03` Migration lives under `praxis/kernel/mac/migrations/`
- **Purpose:** Source-level test — assert the migration file is NOT in Memory's migrations directory (that would be Option X). Grep structural check.
- **Anchor:** `mac/architecture.md §13.2 Option X rejected`.
- **Fulfillment:** `not exists("memory/migrations/0001_mac_bootstrap_metadata.py") AND exists("praxis/kernel/mac/migrations/0001_mac_bootstrap_metadata.py")`.
- **Markers:** `static`, `critical`, `mac_bootstrap_loader`.

### §8.2 Gold-Standard Loading Tests

#### §8.2.1 `MAC-T-BOOT-LOAD-01` Gold-standard corpus size
- **Purpose:** `BootstrapLoader.load_gold_standards()` inserts N rows into the sidecar table (N matches the count in `mac/architecture.md §8.1 gold corpus size`).
- **Fulfillment:** `pg.execute("SELECT COUNT(*) FROM mac_bootstrap_metadata").fetchone()[0] == N`.
- **Markers:** `mac_bootstrap_loader`, `integration`.

#### §8.2.2 `MAC-T-BOOT-LOAD-02` Retrieval annotation written
- **Purpose:** Each gold-standard row has `source='mac_bootstrap'` annotation for retrieval filtering.
- **Fulfillment:** `all(row.source == 'mac_bootstrap' for row in query())`.
- **Markers:** `mac_bootstrap_loader`, `integration`.

#### §8.2.3 `MAC-T-BOOT-LOAD-03` Batched `mac.backfill` events emitted
- **Purpose:** During loading, events are emitted in batches of 100 (matching `memory/architecture.md:915` contract).
- **Markers:** `mac_bootstrap_loader`, `integration`.

### §8.3 Rejected-Alternative Negative Tests (Option X absence)

See §11.2 for the full three-layer negative test suite. Cross-reference here: `MAC-T-NEG-OPTION-X-01`, `MAC-T-NEG-OPTION-X-02`, `MAC-T-NEG-OPTION-X-03`.

### §8.4 Idempotent Re-Run Semantics — S-Q1 Bake-In (Tension #5 Resolution)

**S-Q1 ratified answer:** `BootstrapLoader.load_gold_standards()` on second call returns 0, logs `mac.bootstrap.already_loaded` telemetry event, does NOT raise. Tension #5 preload resolution: idempotency is a first-class property, tested explicitly.

#### §8.4.1 `MAC-T-BOOT-IDEMPOTENT-01` Second call returns 0 and logs
- **Purpose:** First `load_gold_standards()` returns N. Second call returns 0, emits `mac.bootstrap.already_loaded`.
- **Anchor:** S-Q1 ratification + `mac/architecture.md §8.1 idempotent re-run`.
- **Fulfillment:**
  ```python
  first = loader.load_gold_standards()
  assert first == N
  telemetry.reset()
  second = loader.load_gold_standards()
  assert second == 0
  assert any(e.name == "mac.bootstrap.already_loaded" for e in telemetry.events)
  ```
- **Markers:** `mac_bootstrap_loader`, `critical`.

#### §8.4.2 `MAC-T-BOOT-IDEMPOTENT-02` No duplicate rows
- **Purpose:** After two `load_gold_standards()` calls, the sidecar table has exactly N rows, not 2N.
- **Fulfillment:** row count assertion.
- **Markers:** `mac_bootstrap_loader`, `critical`.

#### §8.4.3 `MAC-T-BOOT-IDEMPOTENT-03` No-raise semantics
- **Purpose:** Second call does NOT raise `AlreadyLoadedError` or any other exception.
- **Fulfillment:** `loader.load_gold_standards()` returns normally on second call.
- **Markers:** `mac_bootstrap_loader`, `critical`.

#### §8.4.4 `MAC-T-BOOT-IDEMPOTENT-04` Telemetry event shape
- **Purpose:** `mac.bootstrap.already_loaded` event has attributes `{sidecar_row_count, elapsed_ms, run_id}`.
- **Fulfillment:** event dict assertion.
- **Markers:** `mac_bootstrap_loader`, `critical`.

### §8.5 Bootstrap Facade Tests

#### §8.5.1 `MAC-T-BOOT-FACADE-01` `BootstrapLoader` has no `load_into_memory_schema` method
- **Purpose:** Negative — the rejected Option X method name does not exist on the public facade.
- **Anchor:** `mac/architecture.md §13.2 Option X rejected`.
- **Fulfillment:** `not hasattr(BootstrapLoader, 'load_into_memory_schema')`.
- **Markers:** `static`, `critical`, `mac_bootstrap_loader`.

#### §8.5.2 `MAC-T-BOOT-FACADE-02` `BootstrapLoader.load_gold_standards` signature
- **Purpose:** Signature is `load_gold_standards(self, *, run_id: str | None = None) -> int`. Test uses `inspect.signature`.
- **Fulfillment:** signature dict matches.
- **Markers:** `static`, `critical`, `mac_bootstrap_loader`.

### §8.6 Bootstrap Test Count

| Subsection | Tests |
|---|---|
| §8.1 Migration | 3 |
| §8.2 Gold-standard loading | 3 |
| §8.4 Idempotency (S-Q1, Tension #5) | 4 |
| §8.5 Facade | 2 |
| **Total** | **12** |

---

## §9 Observability Tests

From `mac/architecture.md §11 Observability`: MAC-owned label allowlist registry at `praxis.kernel.mac.observability.telemetry_labels` with hard-fail `LabelRegistryError`. Dedup namespace: `dedup_key = "mac:" + cycle_id + ":" + event_type + ":" + monotonic_seq`.

### §9.0 Observability Design Rationale

MAC's observability layer has three guarantees:
1. **Label allowlist enforcement** — all telemetry labels must be in a frozen allowlist. Unknown labels raise `LabelRegistryError` at validation time, BEFORE the telemetry event is emitted. This prevents label-explosion cardinality issues in observability backends.
2. **Dedup namespace** — every MAC Path B event carries a `dedup_key` that uniquely identifies it across redelivery. The key format is `"mac:" + cycle_id + ":" + event_type + ":" + monotonic_seq`.
3. **Violation counter** — `mac.label_registry.violations` counter increments on every `LabelRegistryError`. The counter is the production-drift signal: if violations tick upward in prod, someone added a label without updating the allowlist.

The tests in §9 verify all three guarantees with unit-level rigor. The violation counter test (§9.3) is the S-Q2 bake-in from Decision 3.

### §9.1 Label Registry Hard-Fail Tests

#### §9.1.1 `MAC-T-OBS-LABEL-REG-01` Registry loads with allowlist
- **Purpose:** `TelemetryLabelRegistry.load()` loads the allowed labels from the static list.
- **Anchor:** `mac/architecture.md §11.1 telemetry_labels`.
- **Markers:** `critical`, `mac_label_registry`.

#### §9.1.2 `MAC-T-OBS-LABEL-REG-02` Hard-fail on unknown label
- **Purpose:** `registry.validate(label="mac.unknown.thing", value="x")` raises `LabelRegistryError` at validation time.
- **Anchor:** `mac/architecture.md §11.1 hard-fail contract`.
- **Fulfillment:** `with pytest.raises(LabelRegistryError): registry.validate(label="mac.unknown.thing", value="x")`.
- **Markers:** `critical`, `mac_label_registry`.

#### §9.1.3 `MAC-T-OBS-LABEL-REG-03` Known labels validate successfully
- **Purpose:** All labels in `telemetry_labels.py::ALLOWED_LABELS` validate without raising.
- **Fulfillment:** loop over allowed list; assert no raise.
- **Markers:** `critical`, `mac_label_registry`.

#### §9.1.4 `MAC-T-OBS-LABEL-REG-04` Registry is immutable at runtime
- **Purpose:** `ALLOWED_LABELS` is a `frozenset`; attempting `.add()` raises `AttributeError`.
- **Fulfillment:** `isinstance(ALLOWED_LABELS, frozenset)` and runtime mutation test.
- **Markers:** `static`, `critical`, `mac_label_registry`.

### §9.2 Dedup Namespace Tests

#### §9.2.1 `MAC-T-OBS-DEDUP-01` Dedup key format
- **Purpose:** `build_dedup_key(cycle_id="C1", event_type="gate_scored", monotonic_seq=42) == "mac:C1:gate_scored:42"`.
- **Anchor:** `mac/architecture.md §11.3 Linkage to Memory's TelemetryEvent` (dedup-key format per SQ-8).
- **Fulfillment:** string equality.
- **Markers:** `critical`, `mac_label_registry`.

#### §9.2.2 `MAC-T-OBS-DEDUP-02` Monotonic seq increments per cycle
- **Purpose:** Within a single cycle, `monotonic_seq` increments 1, 2, 3, ... across events. Reset between cycles.
- **Markers:** `critical`, `mac_label_registry`.

#### §9.2.3 `MAC-T-OBS-DEDUP-03` No cross-cycle collisions
- **Purpose:** Dedup keys from two different cycles never collide. Verified via hash-set property test.
- **Markers:** `critical`, `mac_label_registry`.

### §9.3 Violation Counter — S-Q2 Bake-In

**S-Q2 ratified answer:** `mac.label_registry.violations` counter increments unconditionally on every `LabelRegistryError`. Unit tests use `ResetCounterFixture` (§14.3.7) to clear between tests. Integration tests that exercise a single violation assert `count == 1` post-violation.

#### §9.3.1 `MAC-T-OBS-VIOLATION-01` Counter increments on hard-fail
- **Purpose:** After a `LabelRegistryError` is raised, `mac.label_registry.violations` counter value is `pre_count + 1`.
- **Anchor:** S-Q2 ratification.
- **Fulfillment:**
  ```python
  pre = counter.get("mac.label_registry.violations")
  with pytest.raises(LabelRegistryError):
      registry.validate(label="mac.bad", value="x")
  post = counter.get("mac.label_registry.violations")
  assert post == pre + 1
  ```
- **Markers:** `critical`, `mac_label_registry`.

#### §9.3.2 `MAC-T-OBS-VIOLATION-02` `ResetCounterFixture` clears between tests
- **Purpose:** Verify `ResetCounterFixture` sets counter to 0 on setup. Integration-level test.
- **Fulfillment:** `counter.get("mac.label_registry.violations") == 0` after fixture setup.
- **Markers:** `mac_label_registry`, `integration`.

#### §9.3.3 `MAC-T-OBS-VIOLATION-03` Counter is unconditional (not bypassed by exception handling)
- **Purpose:** Even if the `LabelRegistryError` is caught upstream, the counter still increments (the counter is the production drift signal; tests must not bypass it).
- **Fulfillment:** wrap validation in try/except; assert counter still increments.
- **Markers:** `critical`, `mac_label_registry`.

#### §9.3.4 `MAC-T-OBS-VIOLATION-04` Counter unit is "violations per process lifetime"
- **Purpose:** Document & verify — the counter aggregates across requests in a single process. Reset only on process restart or `ResetCounterFixture`.
- **Markers:** `mac_label_registry`.

### §9.4 Metric Catalog Tests

#### §9.4.1 `MAC-T-OBS-METRIC-01` All metrics in `mac/architecture.md §11.2` exist
- **Purpose:** For every metric listed in §11.2 Metric Catalog, assert `metrics_registry.get(metric_name)` returns a live metric.
- **Anchor:** `mac/architecture.md §11.2 Metric Catalog`.
- **Markers:** `critical`, `mac_label_registry`.

#### §9.4.2 `MAC-T-OBS-METRIC-02` Metric snapshot byte-equality
- **Purpose:** List of registered metrics matches `tests/mac/observability/snapshots/metrics_v0_1.yaml`.
- **Markers:** `static`, `critical`, `mac_label_registry`.

### §9.5 Observability Test Count

| Subsection | Tests |
|---|---|
| §9.1 Label registry | 4 |
| §9.2 Dedup namespace | 3 |
| §9.3 Violation counter (S-Q2) | 4 |
| §9.4 Metric catalog | 2 |
| **Total** | **13** |

---

## §10 Adversarial Tests

From `mac/architecture.md §12.6 Adversarial Corpus` + `benchmark-questions.md §4 Persona 3`: MAC must resist gaming attempts where the producer deliberately manufactures dissent to pass R5, or floods evidence to pass R7 without substance. The adversarial corpus is a set of hand-crafted outputs designed to probe MAC's edge cases.

### §10.0 Adversarial Test Scope

The adversarial test suite addresses one question: **can an adversarial producer, knowing MAC's rubric, manufacture outputs that pass the 12 gates without genuine substance?**

Three adversarial strategies are in scope:
1. **Manufactured dissent** — producer invents a fake dissent position to pass R5 without genuine disagreement. Test: R5 section-routing + co-eval cap forces off-topic dissent to cap at 2.
2. **Evidence flooding** — producer cites many irrelevant sources to pass R7 density. Test: R7 calibration anchor requires substantive citation density, not raw count.
3. **Steelman mimicry** — producer copies the reviewer's likely steelman to pass R4. Test: Req-F two-step independence; reviewer's `independent_steelman` would diverge, triggering `gap_assessment`.

Out of scope (for 5.2 but listed for future expansion):
- Coordinated multi-agent attacks where producer and reviewer are both adversarial.
- Prompt injection via the task description (covered partially by R11/R12 probing).
- Sybil attacks where many producers flood the pipeline.

The rotation protocol (§10.4) addresses the meta-concern: adversarial fixtures committed to the repo could be memorized by future models trained on it. The rotating set ensures every release has at least 5 novel fixtures.

### §10.1 Persona 3 Gaming Resistance

**Persona 3** (from `benchmark-questions.md §4`) is the "gaming" persona — an adversary who knows MAC's rubric and tries to pass each gate by surface-level mimicry rather than substance.

#### §10.1.1 `MAC-T-ADV-P3-01` Gaming prompt fixture corpus inventory (deterministic — Decision 1 item 11 deterministic)
- **Purpose:** Static check — assert the gaming-prompt fixture corpus is present on disk at `tests/mac/adversarial/fixtures/persona_3/` with the expected fixture IDs.
- **Anchor:** `benchmark-questions.md §4 Persona 3` + `mac/architecture.md §12.6` + `§12.2 item 11 deterministic sub-test`.
- **Fulfillment:** `sorted(os.listdir("tests/mac/adversarial/fixtures/persona_3/")) == EXPECTED_FIXTURE_IDS` (snapshot).
- **Marker set:** `static`, `critical`, `mac_adversarial`, `no_waiver`  ← **Decision 1 item 11 deterministic portion**
- **Allow-list entry:** yes (as a split deterministic carrier — see §13.3).

#### §10.1.2 `MAC-T-ADV-P3-02` Live adversarial judge run (critical + mac_adversarial ONLY)
- **Purpose:** Run a REAL LLM judge against the gaming-prompt corpus. For each adversarial fixture, assert the manufactured-dissent detection fires (R5 cap triggers due to off-topic dissent, R7 score is not artificially inflated by evidence-flooding).
- **Anchor:** `mac/architecture.md §12.2 item 11 live sub-test` + `§12.6`.
- **Fulfillment:**
  ```python
  for fixture_id in P3_GAMING_FIXTURES:
      result = real_judge.score(load_fixture(fixture_id))
      assert result.R5.effective <= 2, f"R5 gaming not detected in {fixture_id}"
      assert result.R7.effective <= 3, f"R7 evidence-flooding not detected in {fixture_id}"
  ```
- **Marker set:** `critical`, `mac_adversarial`, `nightly_only`.
- **NOT `no_waiver`** — live judges drift.

#### §10.1.3 `MAC-T-ADV-P3-03` Manufactured dissent detection (unit)
- **Purpose:** Deterministic version — `FakeLLMJudge` with a lookup of manufactured-dissent outputs returns R5 ≤ 2 for each.
- **Markers:** `critical`, `mac_adversarial`, `mac_gate_calibration`.

#### §10.1.4 `MAC-T-ADV-P3-04` Evidence flooding detection (unit)
- **Purpose:** Deterministic version — `FakeLLMJudge` with flood-evidence outputs returns R7 ≤ 3.
- **Markers:** `critical`, `mac_adversarial`, `mac_gate_calibration`.

#### §10.1.5 `MAC-T-ADV-P3-05` Gaming attempts on R4 steelman
- **Purpose:** Adversarial fixture where producer copies reviewer's likely steelman verbatim, hoping to pass R4. Assert R4 Req-F detection fires (reviewer's independent_steelman would diverge from producer's, so `gap_assessment` flags).
- **Markers:** `critical`, `mac_adversarial`, `asymmetry_structural`.

### §10.2 Adversarial R11 Scenario Coverage Probing

Per arch §6.1 R11 definition: "Multiple plausible futures with differentiated decision implications and trigger conditions; guard condition for deterministic domains." Adversarial probes target the three failure modes a producer might use to game Scenario Coverage: single-scenario bias disguised as multi-scenario analysis, manufactured-but-unfalsifiable trigger conditions, and narratively indistinct "plausible futures" that collapse to one scenario on inspection.

#### §10.2.1 `MAC-T-ADV-R11-01` Single-scenario bias disguised as multi-scenario
- **Purpose:** Adversarial fixture where the producer output contains three section headers labeled "Scenario A / Scenario B / Scenario C" but all three sections describe essentially the same future (e.g., "base case moderate growth", "likely moderate growth", "expected moderate growth") with indistinguishable decision implications. Assert R11 detects the collapse and scores ≤2 — the surface multi-scenario structure must not fool the gate.
- **Anchor:** `mac/architecture.md §6.1 R11 row` + `quality-rubric.md §6 R11` + `mac/architecture.md §12.6 adversarial corpus`.
- **Fulfillment:**
  ```python
  fx = load_fixture("r11_adv_single_scenario_three_labels")
  assert R11Gate.score(fx).effective <= 2
  assert "scenarios not differentiated" in R11Gate.score(fx).rationale.lower()
  ```
- **Markers:** `critical`, `mac_adversarial`.

#### §10.2.2 `MAC-T-ADV-R11-02` Manufactured non-falsifiable trigger conditions
- **Purpose:** Adversarial fixture where three distinct scenarios are present with differentiated decision implications BUT the trigger conditions are manufactured unfalsifiable narratives ("if market sentiment shifts meaningfully", "if leadership concludes the landscape has changed", "if the situation warrants reassessment"). These triggers are plausible-sounding but offer no observable way to distinguish which scenario is unfolding in practice. Assert R11 detects the lack of observable differentiation and scores ≤2. Cross-references the R3 Falsifiability gate (§3.4) which checks individual-conclusion invalidation conditions; this test is specifically R11's scenario-level observable-differentiation check.
- **Anchor:** `mac/architecture.md §6.1 R11 row` + `mac/architecture.md §12.6 adversarial corpus`.
- **Fulfillment:**
  ```python
  fx = load_fixture("r11_adv_manufactured_triggers")
  assert R11Gate.score(fx).effective <= 2
  ```
- **Markers:** `critical`, `mac_adversarial`.

### §10.3 Adversarial R12 Internal Consistency Probing

Per arch §6.1 R12 definition: "Analysis does not contradict itself; premises accepted in findings are not denied in conclusions." Adversarial probes target producers that pass at the unit level but smuggle subtle cross-section contradictions — the kind that look coherent on single-section read but break when a reviewer reads `[FINDINGS]` + `[RECOMMENDATIONS]` + `[STEELMAN]` jointly.

#### §10.3.1 `MAC-T-ADV-R12-01` Subtle cross-section contradiction
- **Purpose:** Adversarial fixture where `[FINDINGS]` establishes a claim with moderate confidence ("evidence suggests X with significant uncertainty; confidence 60%"), `[RECOMMENDATIONS]` treats the same claim as certain ("because X holds, the team should commit to strategy Y"), and `[STEELMAN]` presents a counter-position that the `[RECOMMENDATIONS]` implicitly assumes refuted without acknowledging it. All three sections pass their individual gate checks in isolation but contradict each other when read together. Assert R12 detects the cross-section inconsistency and scores ≤2. The R12 direct-contradiction detector must flag specific contradicting text spans.
- **Anchor:** `mac/architecture.md §6.1 R12 row` + `quality-rubric.md §6 R12` + `mac/architecture.md §12.6 adversarial corpus`.
- **Fulfillment:**
  ```python
  fx = load_fixture("r12_adv_cross_section_contradiction")
  result = R12Gate.score(fx)
  assert result.effective <= 2
  # Direct-contradiction detector flags specific text spans (T1 layer per rubric §6 R12)
  assert "60%" in result.rationale or "moderate confidence" in result.rationale
  assert "should commit" in result.rationale or "because X holds" in result.rationale
  ```
- **Markers:** `critical`, `mac_adversarial`.

**Out-of-scope declaration for §10.2/§10.3:** Jailbreak resistance, prompt injection, PII disclosure prevention, copyright-infringement detection, and other input-filter / output-filter safety concerns are NOT gate-level responsibilities under the ratified 12-gate catalog (arch §6.1). If Praxis requires jailbreak resistance or policy-compliance gating, these belong to a pre-gate input-filtering layer or a post-gate output-filtering layer and are architectural decisions deferred to Stage 6 or a separate RFC. The v0.1 `MAC-T-ADV-R11-01/02` and `MAC-T-ADV-R12-01` tests that exercised these concerns were built on the fabricated v0.1 R11=Safety / R12=Policy labels and have been rewritten v0.3 per team-lead authorization. See §1.7 v0.3 changelog for full removal context.

### §10.4 Adversarial Corpus Rotation Protocol — Tension #6 Resolution

**Tension #6 (adversarial leakage):** If adversarial fixtures are committed to the repo, producers/reviewers trained on the repo could "memorize" them and pass trivially. Preload resolution: **rotation protocol**.

#### §10.4.1 Rotation Protocol Definition

- The adversarial corpus is split into two sets:
  - **Public fixture set** (`tests/mac/adversarial/fixtures/persona_3/public/`): committed to repo. Used for PR-gate and nightly deterministic tests. Known to models. Serves as a baseline.
  - **Rotating fixture set** (`tests/mac/adversarial/fixtures/persona_3/rotating/`): rotated every release (V-bumped). NEW fixtures added each release; old fixtures archived to the `public` set after 2 releases.
- A release cannot ship unless the rotating set has at least 5 new fixtures vs the previous release.

#### §10.4.2 `MAC-T-ADV-ROTATION-01` Rotating set has ≥5 new fixtures per release
- **Purpose:** Static check — compare current release's rotating set to previous release's rotating set; assert ≥5 new fixture IDs.
- **Anchor:** Tension #6 rotation protocol.
- **Fulfillment:** `len(set(current_rotating) - set(previous_rotating)) >= 5`.
- **Markers:** `static`, `release_gate`, `mac_adversarial`.

#### §10.4.3 `MAC-T-ADV-ROTATION-02` Archive promotion rule
- **Purpose:** After 2 releases, rotating fixtures move to `public/`. Assert the promotion policy: for fixtures in previous-previous rotating set, they are now in current public set.
- **Markers:** `static`, `release_gate`, `mac_adversarial`.

#### §10.4.4 `MAC-T-ADV-ROTATION-03` Nightly runs use both sets
- **Purpose:** The nightly adversarial live-judge run iterates over `public ∪ rotating`.
- **Markers:** `mac_adversarial`, `nightly_only`.

### §10.4A Adversarial Fixture Format

Each adversarial fixture is a YAML file with the following schema:

```yaml
# tests/mac/adversarial/fixtures/persona_3/public/p3_001_manufactured_dissent.yaml
fixture_id: p3_001_manufactured_dissent
persona: persona_3
attack_type: manufactured_dissent
target_gates: [R5]
expected_result:
  R5: {raw: 4, effective: 2}  # Capped due to off-topic
  R7: {raw: null, effective: null}  # Not the focus
description: >
  Producer fabricates a dissent position that does not correspond to any
  task-context position. R5 should detect off-topic dissent and cap the
  raw score of 4 down to 2.
task_context: |
  Question Q3: What are the trade-offs of adopting framework X for backend services?
  Constraints: latency, observability, team familiarity.
producer_output:
  steelman: |
    [STEELMAN] Adopting X gives unified observability across services...
  dissent: |
    [DISSENT] However, the cuneiform writing system is poorly understood...
    [DISSENT] Continued: Mesopotamian merchants struggled with grain accounting...
gold_standard_judge_output: |
  R5 score 2: dissent positions are about cuneiform / Mesopotamian
  history, not the technical question of framework X. Off-topic by Req-E
  domain guard. Raw R5=4, capped to R5=2 by (R5, R4) co-eval.
```

The `expected_result` field is the ground truth — what MAC's gates SHOULD produce when given this fixture. The deterministic adversarial test (e.g., `MAC-T-ADV-P3-03`) wires this fixture through `FakeLLMJudge` (with the lookup table populated to return the gold-standard score) and asserts the gate logic produces the expected effective score.

The live adversarial test (`MAC-T-ADV-P3-02`) uses a REAL judge, not the fake, and asserts the real judge produces a score within tolerance of the expected.

### §10.5 Adversarial Test Count

| Subsection | Tests |
|---|---|
| §10.1 Persona 3 | 5 |
| §10.2 R11 probing | 2 |
| §10.3 R12 probing | 1 |
| §10.4 Rotation (Tension #6) | 3 |
| **Total** | **11** |

---

## §11 Negative Tests

Negative tests verify what MUST NOT exist: rejected architectural alternatives, absence of deprecated code paths, structural invariants that assert the shape of the code base rather than its behavior.

### §11.0 What Negative Tests Prove

Negative tests are "this does NOT exist" assertions. They catch architectural drift — the slow slide where someone adds a feature outside the architecture's boundaries and no test stops them. Negative tests are cheap (mostly grep-based static checks) but high-leverage: each negative test is a lever preventing a specific failure mode.

The five negative-test clusters in §11:
1. **No 13th gate** — prevents scope creep ("let's add an R13 for creativity").
2. **Option X absence** — prevents the rejected bootstrap alternative from silently reappearing in a refactor.
3. **No parallel `MacTelemetryEvent`** — prevents a shadow event class in tests from masking production events.
4. **`DomainClass` singular** — prevents a hot-patch that adds a 6th domain, bypassing the domain guard.
5. **MCP pin** — prevents a dependency drift that would break `verify_mcp_sdk_shape()`.

Each cluster has a clear triggering failure mode. If any of these tests ever fails, the investigation starts from "what architectural boundary was crossed?", not "what did we break?"

### §11.1 No 13th Gate Module

#### §11.1.1 `MAC-T-NEG-GATE13-01` No gate module `R13`
- **Purpose:** Structural grep — `praxis/kernel/mac/gates/` contains exactly 12 gate modules, named `r1.py` through `r12.py`. No `r13.py`, no `r0.py`.
- **Fulfillment:** `set(os.listdir("praxis/kernel/mac/gates/")) == EXPECTED_12_GATE_MODULES`.
- **Markers:** `static`, `critical`.

#### §11.1.2 `MAC-T-NEG-GATE13-02` No reference to R13 in code
- **Purpose:** Grep `praxis/kernel/mac/` for literal `"R13"`; assert zero matches (outside test files).
- **Markers:** `static`, `critical`.

### §11.2 Option X Absence — Three-Layer Negative Test (Tension #8 Resolution)

**Tension #8 (Option X negative test):** Option X is the rejected bootstrap alternative (inject into Memory's schema). Must have strong absence proof at three layers. Preload resolution: **three-layer negative test**.

#### §11.2.1 `MAC-T-NEG-OPTION-X-01` Layer 1 — Grep no Memory schema injection
- **Purpose:** Grep `praxis/kernel/mac/` for any reference to `memory.migrations`, `memory.schema`, or `memory.tasks.add_column`. Assert zero matches.
- **Anchor:** `mac/architecture.md §13.2 Option X rejected`.
- **Fulfillment:** grep assertions.
- **Markers:** `static`, `critical`, `mac_bootstrap_loader`.

#### §11.2.2 `MAC-T-NEG-OPTION-X-02` Layer 2 — Schema introspection
- **Purpose:** Query Postgres `information_schema.columns` for the `memory.tasks` table. Assert no columns named like MAC bootstrap metadata (`mac_bootstrap_*` prefix).
- **Fulfillment:** `pg.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='memory' AND table_name='tasks' AND column_name LIKE 'mac_bootstrap_%'").fetchall() == []`.
- **Markers:** `static`, `integration`, `critical`, `mac_bootstrap_loader`.

#### §11.2.3 `MAC-T-NEG-OPTION-X-03` Layer 3 — Facade signature check
- **Purpose:** `BootstrapLoader` facade has no methods with the rejected signatures (`load_into_memory_schema`, `inject_into_memory_migrations`, etc.).
- **Fulfillment:** `inspect.getmembers(BootstrapLoader)` filtered for rejected method names yields empty list.
- **Markers:** `static`, `critical`, `mac_bootstrap_loader`.

### §11.3 No Parallel `MacTelemetryEvent`

#### §11.3.1 `MAC-T-NEG-TELEMETRY-01` No parallel event type definition
- **Purpose:** There is exactly ONE definition of `MacTelemetryEvent` in `praxis/kernel/mac/observability/`. Grep-based.
- **Fulfillment:** `grep_count("class MacTelemetryEvent") == 1`.
- **Markers:** `static`, `critical`.

#### §11.3.2 `MAC-T-NEG-TELEMETRY-02` No shadow event class in tests
- **Purpose:** No test fixture defines a `MacTelemetryEvent` subclass that shadows the production class.
- **Markers:** `static`, `critical`.

### §11.4 `DomainClass` Singular Definition

#### §11.4.1 `MAC-T-NEG-DOMAIN-CLASS-01` Only one `DomainClass` enum
- **Purpose:** Structural grep — `DomainClass` enum is defined exactly once, at `praxis.kernel.mac.task.DomainClass`. No other definitions.
- **Anchor:** `mac/architecture.md §6.5 Domain Guard Conditions (Req-E + SQ-5)` + `§3.4 DomainClass enum` + preload item 6.
- **Fulfillment:** `grep_count("class DomainClass") == 1 AND grep_match_path("class DomainClass") == "praxis/kernel/mac/task.py"`.
- **Markers:** `static`, `critical`.

#### §11.4.2 `MAC-T-NEG-DOMAIN-CLASS-02` Exactly 5 enum values
- **Purpose:** `DomainClass` has exactly 5 members (per preload item 6).
- **Fulfillment:** `len(list(DomainClass)) == 5`.
- **Markers:** `static`, `critical`.

### §11.5 Pinning & Dependency Negative Tests

#### §11.5.1 `MAC-T-NEG-MCP-PIN-01` `mcp` package pinned ≥1.9.0
- **Purpose:** `pyproject.toml` pins `mcp>=1.9.0`.
- **Anchor:** `mac/architecture.md §10.3 Runtime Integration` (MCP shape guard + SQ-1 MCP pin inheritance).
- **Markers:** `static`, `critical`.

### §11.6 Negative Test Count

| Subsection | Tests |
|---|---|
| §11.1 No 13th gate | 2 |
| §11.2 Option X (Tension #8) | 3 |
| §11.3 No parallel telemetry | 2 |
| §11.4 DomainClass singular | 2 |
| §11.5 Pinning | 1 |
| **Total** | **10** |

---

## §12 Calibration Tests — Live-Judge Drift Canary (Tier 3, Nightly)

Every gate has a LIVE calibration canary. The canary replays `benchmark-questions.md §5` anchors through a REAL LLM judge and asserts the buckets still hold. If a real model's scoring drifts outside the expected bucket, the nightly build fails and humans investigate.

### §12.1 Drift Canary Definition

- **Schedule:** nightly CI pipeline, dedicated job outside PR gate.
- **Cost budget:** ~60 live judge calls per night (12 gates × 2 anchors × ~2.5 average retries). Documented in §14.4.
- **Anchor set size:** exactly 24 anchors (12 gates × 2 each, from `benchmark-questions.md §5`).
- **Failure mode:** If any §5 score-2 anchor scores >2 OR any §5 score-4 anchor scores <4, the nightly build fails with a named gate in the error.
- **NOT `no_waiver`** — live judges drift.
- **Markers:** `mac_gate_calibration`, `nightly_only`.

### §12.2 Per-Gate Drift Canary Tests

For each gate R1–R12, two live tests:
- `MAC-T-CAL-R{N}-DRIFT-LOW-01` — score-2 anchor must score ≤2
- `MAC-T-CAL-R{N}-DRIFT-HIGH-01` — score-4 anchor must score ≥4

Total: 12 × 2 = **24 tests**.

#### §12.2.1 Template — `MAC-T-CAL-R1-DRIFT-LOW-01`
- **Purpose:** Replay `benchmark-questions.md §5 R1 score-2 anchor` through REAL LLM judge. Assert the returned score is ≤2.
- **Anchor:** `benchmark-questions.md §5 R1 score-2` + `quality-rubric.md §6 R1`.
- **Fulfillment:** `real_llm_judge.score(§5_R1_score_2_anchor) <= 2`.
- **Markers:** `mac_gate_calibration`, `nightly_only`.

#### §12.2.2 Template — `MAC-T-CAL-R1-DRIFT-HIGH-01`
- **Purpose:** Replay `§5 R1 score-4 anchor`. Assert score ≥4.
- **Fulfillment:** `real_llm_judge.score(§5_R1_score_4_anchor) >= 4`.
- **Markers:** `mac_gate_calibration`, `nightly_only`.

#### §12.2.3 Enumerated IDs

Following the template, the 24 live drift canary test IDs are:

| # | Test ID | Gate | Bucket |
|---|---|---|---|
| 1 | `MAC-T-CAL-R1-DRIFT-LOW-01` | R1 | ≤2 |
| 2 | `MAC-T-CAL-R1-DRIFT-HIGH-01` | R1 | ≥4 |
| 3 | `MAC-T-CAL-R2-DRIFT-LOW-01` | R2 | ≤2 |
| 4 | `MAC-T-CAL-R2-DRIFT-HIGH-01` | R2 | ≥4 |
| 5 | `MAC-T-CAL-R3-DRIFT-LOW-01` | R3 | ≤2 |
| 6 | `MAC-T-CAL-R3-DRIFT-HIGH-01` | R3 | ≥4 |
| 7 | `MAC-T-CAL-R4-DRIFT-LOW-01` | R4 | ≤2 |
| 8 | `MAC-T-CAL-R4-DRIFT-HIGH-01` | R4 | ≥4 |
| 9 | `MAC-T-CAL-R5-DRIFT-LOW-01` | R5 | ≤2 |
| 10 | `MAC-T-CAL-R5-DRIFT-HIGH-01` | R5 | ≥4 |
| 11 | `MAC-T-CAL-R6-DRIFT-LOW-01` | R6 | ≤2 |
| 12 | `MAC-T-CAL-R6-DRIFT-HIGH-01` | R6 | ≥4 |
| 13 | `MAC-T-CAL-R7-DRIFT-LOW-01` | R7 | ≤2 |
| 14 | `MAC-T-CAL-R7-DRIFT-HIGH-01` | R7 | ≥4 |
| 15 | `MAC-T-CAL-R8-DRIFT-LOW-01` | R8 | ≤2 |
| 16 | `MAC-T-CAL-R8-DRIFT-HIGH-01` | R8 | ≥4 |
| 17 | `MAC-T-CAL-R9-DRIFT-LOW-01` | R9 | ≤2 |
| 18 | `MAC-T-CAL-R9-DRIFT-HIGH-01` | R9 | ≥4 |
| 19 | `MAC-T-CAL-R10-DRIFT-LOW-01` | R10 | ≤2 |
| 20 | `MAC-T-CAL-R10-DRIFT-HIGH-01` | R10 | ≥4 |
| 21 | `MAC-T-CAL-R11-DRIFT-LOW-01` | R11 | ≤2 |
| 22 | `MAC-T-CAL-R11-DRIFT-HIGH-01` | R11 | ≥4 |
| 23 | `MAC-T-CAL-R12-DRIFT-LOW-01` | R12 | ≤2 |
| 24 | `MAC-T-CAL-R12-DRIFT-HIGH-01` | R12 | ≥4 |

### §12.3 Live-Judge Cost Budget

From §12.1: cost budget ~60 calls per night. Calculation:
- 24 anchors × ~2.5 retries (for retry-on-rate-limit and drift-stability sampling) = 60.

The retry count of 2.5 represents: 1 base call + 0.5 expected retries for stability (a call that returns a score on a boundary may be repeated once to confirm) + 1 retry for transient rate-limit / network errors.

### §12.4 Drift Canary Failure Handling

When a drift canary fails, the nightly CI:
1. Emits a Slack notification with the failing gate and the anchor ID.
2. Tags the build as `drift_detected` but does NOT block the PR gate (live drift is a signal, not a blocker).
3. Adds a calendar item for the team-lead to review within 48 hours.
4. If the drift persists across 3 consecutive nightly runs, escalates to `blocking_pr_gate` (promotion rule).

The 3-run rule prevents flaky drift detection from blocking work, while still catching genuine model regressions.

### §12.5 Calibration Test Count

| Subsection | Tests |
|---|---|
| §12.2 Per-gate drift canary | 24 |
| **Total** | **24** |

---

## §13 Coverage and Markers

### §13.1 Pipeline.md §5.2 Gate Checklist

| Pipeline.md §5.2 sub-check | Fulfilling section(s) | Key citation |
|---|---|---|
| Test strategy at `mac/test-strategy.md` | (this document) | deliverable |
| Most intensive test design in the project | §3 (75 gate tests) + §4–§12 (all families) | 222 test IDs total exceeds Runtime's 204 |
| Cycle state machine property tests | §4.2 (`STATE-01..05`) | `mac/architecture.md §5.2` |
| Adversarial tests ("can we trick the MAC?") | §10 (`ADV-P3-*`, R11/R12 probing, rotation protocol) | `benchmark-questions.md §4 Persona 3`; `mac/architecture.md §12.6` |
| Context strategy (USR rule applied) | §1.2 USR documented | preload phase verified sequential reading |
| Decision 1 — 10 MAC `no_waiver` tests | §3.16.1 (8 calibration anchors + 2 structural calibration), §5.1 (item 9 split), §10.1 (item 11 split) | §13.3.3 ratified allow-list entries 4–13 (self-contained; see §1.4 prose) |
| Label drift reconciliation RESOLVED 2026-04-14 | §1.7 v0.2 changelog + §3.1 regeneration + §3.2–§3.13 per-gate regeneration + §3.12.5/§3.13.5 rewrite | Option R1 + C-2 + D-1 ratified by team-lead 2026-04-14; `mac/architecture.md` §6.1 authoritative; upstream `quality-rubric.md` §6 binding |
| Decision 2 — OQ-TS-9 allow-list meta-test | §13.3 (new subsection) | Target `tests/static/runtime/test_no_waiver_inventory.py` |
| Decision 3 — S-Q1 in §8.4 | §8.4 `BOOT-IDEMPOTENT-*` | S-Q1 ratification |
| Decision 3 — S-Q2 in §9.3 | §9.3 `OBS-VIOLATION-*` | S-Q2 ratification |
| Decision 3 — S-Q3 in §7.9 | §7.9 `BENCH-NIGHTLY-*` | S-Q3 ratification |
| Decision 3 — S-Q4 in §7.10 | §7.10 `BENCH-A4-*` | S-Q4 ratification |
| 8 tensions as named subsections | §4.5 (#2), §4.6 (#4), §3.15 (#3), §8.4 (#5), §10.4 (#6), §13.5 (#7), §11.2 (#8), §13.3 (#1) | preload Item 3 |
| Coverage target ≥90% on `praxis/kernel/mac/` | §13.2 | Coverage exclusion policy §13.5 |
| Fake fixture interface contracts | §14.3 | Amelia implements verbatim at 5.3 |
| Test ID schema | §15 | `MAC-T-{section}-{seq}` |
| Handoff plan to 5.3 Amelia | §16 | red-first order + checkpoint plan |
| **Allow-list count reconciliation RESOLVED 2026-04-14** | §13.3.3 Ratification Block | Option 1 (16 entries) ratified; reasoning: 10/12 Decision 1 + 2 split deterministic carriers + 2 Runtime provisional + 1 Runtime ratified + 1 self-reference = 16 |

### §13.2 Coverage Target

- **Target:** ≥90% line + branch coverage on `praxis/kernel/mac/`.
- **Measurement:** `pytest --cov=praxis.kernel.mac --cov-report=term-missing --cov-branch` with `--cov-fail-under=90`.
- **Scope:** all modules under `praxis/kernel/mac/` EXCEPT the exclusions in §13.5.
- **Reported in CI:** coverage report uploaded to the nightly pipeline and posted to the 5.3 checkpoint review.

### §13.3 OQ-TS-9 Allow-List Meta-Test — `tests/static/runtime/test_no_waiver_inventory.py` (Decision 2, Tension #1 Resolution)

**This is the scope-expansion item from Decision 2.** The meta-test enforces the `no_waiver` discipline at collection time. It walks the test tree, collects every test marked `no_waiver`, and asserts its ID is in the allow-list. If not in the allow-list, collection fails with a clear error. If an allow-list entry is NOT found in the tree, collection fails (no silent removal).

#### §13.3.1 Target path
`tests/static/runtime/test_no_waiver_inventory.py` — this lives under the RUNTIME tests directory intentionally (Decision 2: crosses stage boundary to enforce cross-stage `no_waiver` discipline; Runtime currently owns the `static/runtime/` bucket so this is co-located with other static enforcement tests).

#### §13.3.2 Implementation target (Amelia writes at 5.3)

```python
# tests/static/runtime/test_no_waiver_inventory.py
# PURPOSE: Enforce the no_waiver allow-list at pytest collection time.
# AUTHORED: Stage 5.3 per Stage 5.2 test-strategy §13.3.

import pytest
from _pytest.mark.structures import MarkDecorator

NO_WAIVER_ALLOWLIST: frozenset[str] = frozenset({
    # --- 1 Runtime ratified ---
    "tests/runtime/outbox/test_path_a_atomicity.py::test_f13_c1_xmin_identity_proof",

    # --- 2 Runtime provisionally_grandfathered ---
    # PENDING AUDIT at 5.5 Alignment Review — ratify or strip no_waiver;
    # reason for provisional: Amelia added at Stage 4.3 without Pipeline ratification.
    "tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 41>",
    # Same PENDING AUDIT comment.
    "tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 62>",

    # --- 10 MAC new (ratified 2026-04-14, Stage 5.2) ---
    "tests/mac/gates/test_r1.py::test_mac_t_gate_r1_02_calibration_anchor",      # Decision 1 — §13.3.3 entry #4
    "tests/mac/gates/test_r2.py::test_mac_t_gate_r2_02_calibration_anchor",      # Decision 1 — §13.3.3 entry #5
    "tests/mac/gates/test_r3.py::test_mac_t_gate_r3_02_calibration_anchor",      # Decision 1 — §13.3.3 entry #6
    "tests/mac/gates/test_r4.py::test_mac_t_gate_r4_02_calibration_anchor",      # Decision 1 — §13.3.3 entry #7
    "tests/mac/gates/test_r5.py::test_mac_t_gate_r5_02_calibration_anchor",      # Decision 1 — §13.3.3 entry #8
    "tests/mac/gates/test_r7.py::test_mac_t_gate_r7_02_calibration_anchor",      # Decision 1 — §13.3.3 entry #9
    "tests/mac/gates/test_r8.py::test_mac_t_gate_r8_02_calibration_anchor",      # Decision 1 — §13.3.3 entry #10
    "tests/mac/gates/test_r11.py::test_mac_t_gate_r11_02_calibration_anchor",    # Decision 1 — §13.3.3 entry #11
    "tests/mac/gates/test_r11.py::test_mac_t_gate_r11_05_scenario_coverage_property",  # Decision 1 — see §13.3.3 entry #12
    "tests/mac/gates/test_r12.py::test_mac_t_gate_r12_05_direct_contradiction_detector",  # Decision 1 — see §13.3.3 entry #13

    # --- 2 MAC split deterministic carriers (Decision 1 items 9/11 deterministic sub-tests) ---
    "tests/mac/asymmetry/test_req_f.py::test_mac_t_asym_r_f_02_field_ordering_deterministic",     # item 9 deterministic
    "tests/mac/adversarial/test_persona_3.py::test_mac_t_adv_p3_01_fixture_inventory_deterministic",  # item 11 deterministic

    # --- 1 self-reference (bootstrap self-enclosure) ---
    "tests/static/runtime/test_no_waiver_inventory.py::test_mac_t_meta_no_waiver_inv_01_allowlist_check",
})

# The meta-test itself carries no_waiver.
# The self-reference above locks the meta-test: if a PR strips no_waiver from
# this function, the remaining allow-list entries no longer have an enforcer,
# but the bootstrap property still holds — the meta-test's own entry must be
# present, so it cannot be silently removed without the removal being visible
# to reviewers (the allow-list mutates).

@pytest.mark.no_waiver
def test_mac_t_meta_no_waiver_inv_01_allowlist_check(pytestconfig):
    """
    At collection time, walk the full test tree. For each test carrying
    @pytest.mark.no_waiver, assert its ID is in NO_WAIVER_ALLOWLIST.
    Fail collection with a clear message if any test is outside the list,
    or if any allow-list entry is not found in the tree.
    """
    collected_no_waiver_ids: set[str] = set()
    # pytestconfig-based collection introspection (Amelia: use
    # pytestconfig.pluginmanager or similar to enumerate collected items).
    for item in _iter_collected_items(pytestconfig):
        if _has_marker(item, "no_waiver"):
            collected_no_waiver_ids.add(item.nodeid)

    unauthorized = collected_no_waiver_ids - NO_WAIVER_ALLOWLIST
    missing = NO_WAIVER_ALLOWLIST - collected_no_waiver_ids

    errors = []
    if unauthorized:
        errors.append(
            f"Unauthorized no_waiver tests (not in NO_WAIVER_ALLOWLIST): "
            f"{sorted(unauthorized)}"
        )
    if missing:
        errors.append(
            f"Allow-list entries missing from test tree (silent removal?): "
            f"{sorted(missing)}"
        )
    if errors:
        raise AssertionError("\n".join(errors))
```

#### §13.3.3 Allow-list contents — enumerated

| # | Source | Entry | Status | Audit note |
|---|---|---|---|---|
| 1 | Runtime ratified | `tests/runtime/outbox/test_path_a_atomicity.py::test_f13_c1_xmin_identity_proof` | ratified | F-13.C1 |
| 2 | Runtime provisional | `tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 41>` | provisional | PENDING AUDIT at 5.5 |
| 3 | Runtime provisional | `tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 62>` | provisional | PENDING AUDIT at 5.5 |
| 4 | MAC Decision 1 (R1 calibration anchor) | `MAC-T-GATE-R1-02` → `test_mac_t_gate_r1_02_calibration_anchor` | ratified | §3.2.2 |
| 5 | MAC Decision 1 (R2 calibration anchor) | `MAC-T-GATE-R2-02` → `test_mac_t_gate_r2_02_calibration_anchor` | ratified | §3.3.2 |
| 6 | MAC Decision 1 (R3 calibration anchor) | `MAC-T-GATE-R3-02` → `test_mac_t_gate_r3_02_calibration_anchor` | ratified | §3.4.2 |
| 7 | MAC Decision 1 (R4 calibration anchor) | `MAC-T-GATE-R4-02` → `test_mac_t_gate_r4_02_calibration_anchor` | ratified | §3.5.2 |
| 8 | MAC Decision 1 (R5 calibration anchor) | `MAC-T-GATE-R5-02` → `test_mac_t_gate_r5_02_calibration_anchor` | ratified | §3.6.2 |
| 9 | MAC Decision 1 (R7 calibration anchor) | `MAC-T-GATE-R7-02` → `test_mac_t_gate_r7_02_calibration_anchor` | ratified | §3.8.2 |
| 10 | MAC Decision 1 (R8 calibration anchor) | `MAC-T-GATE-R8-02` → `test_mac_t_gate_r8_02_calibration_anchor` | ratified | §3.9.2 |
| 11 | MAC Decision 1 (R11 calibration anchor) | `MAC-T-GATE-R11-02` → `test_mac_t_gate_r11_02_calibration_anchor` | ratified | §3.12.2 |
| 12 | MAC Decision 1 (R11 structural calibration) | `MAC-T-GATE-R11-05` → `test_mac_t_gate_r11_05_scenario_coverage_property` | ratified | §3.12.5 |
| 13 | MAC Decision 1 (R12 structural calibration) | `MAC-T-GATE-R12-05` → `test_mac_t_gate_r12_05_direct_contradiction_detector` | ratified | §3.13.5 |
| 14 | MAC Decision 1 (Req-F deterministic carrier) | `MAC-T-ASYM-R-F-02` → `test_mac_t_asym_r_f_02_field_ordering_deterministic` | ratified (split carrier) | §5.1.2 |
| 15 | MAC Decision 1 (Persona 3 deterministic carrier) | `MAC-T-ADV-P3-01` → `test_mac_t_adv_p3_01_fixture_inventory_deterministic` | ratified (split carrier) | §10.1.1 |
| 16 | Self-reference | `MAC-T-META-NO-WAIVER-INV-01` → `test_mac_t_meta_no_waiver_inv_01_allowlist_check` | ratified (bootstrap) | §13.3 |

**Count: 16 entries total.**
- 1 Runtime ratified (entry 1)
- 2 Runtime provisional (entries 2, 3)
- 10 MAC new calibration/hard-fail (entries 4–13)
- 2 MAC split deterministic carriers (entries 14, 15) — Decision 1 items 9 and 11 deterministic sub-tests
- 1 self-reference (entry 16)

### §13.3.3.1 Ratification Block — Option 1 (16 entries) RATIFIED 2026-04-14

The 16-entry allow-list above is the **ratified final count** for Stage 5.2. Rationale (verbatim from the team-lead ratification directive):

- The "14" in the 5.2 binding brief was an arithmetic error on the team-lead side — the brief forgot that the 2 split deterministic sub-tests (`MAC-T-ASYM-R-F-02` and `MAC-T-ADV-P3-01`) themselves require allow-list entries. Structural boundary was correct; count was wrong.
- Option 2 is incoherent with Decision 1: Decision 1's principle is "`no_waiver` = deterministic invariants only." The split carriers are deterministic by construction (that's why they were split). Stripping `no_waiver` from them creates arbitrary asymmetry with `MAC-T-GATE-R{1-8,10,12}` and breaks the principle.
- Option 3 defeats Decision 2: the self-reference is what makes the meta-test tamper-evident. Without it, a future agent could silently delete `test_no_waiver_inventory.py` with no failing test to catch it — exactly the governance hole this decision was closing.
- Option 1 is the only choice consistent with both decisions. The 16-entry count is the correct number; the structural boundary is honored; self-enclosure is preserved.

**Ownership of the Runtime provisional entries (#2 and #3):** OTEL exporter allow-list entries #2 and #3 are tagged PENDING AUDIT. Audit resolution is **Andrey's decision at 5.5 Alignment Review** — not Amelia's, not Murat's, not Winston's. **No agent is authorized to remove the provisional tag without Andrey's explicit ratification.** Any code change that strips the provisional tag, moves the entries to ratified status, or removes them from the allow-list constitutes an unauthorized modification and must be rejected at code review.

**Ratification target:** the 16-entry allow-list is the binding input for Stage 5.3 Amelia implementation of `tests/static/runtime/test_no_waiver_inventory.py`. Amelia implements all 16 entries verbatim; no entry is added, removed, or reordered without an explicit team-lead ratification message.

#### §13.3.4 Self-referential bootstrap property

The meta-test carries `no_waiver` and its own test ID is entry 16 in the allow-list. This is a **bootstrap self-enclosure**: the meta-test passes if and only if it finds itself in the allow-list. Without this self-reference, a PR could strip `no_waiver` from the meta-test, and the meta-test would still pass (because the allow-list enforcement would be disabled), but the other 15 entries would be unenforced — a silent weakening.

With the self-reference, stripping `no_waiver` from the meta-test makes the meta-test NOT collect as `no_waiver`, BUT entry 16 of the allow-list is expected to be there. The result: `missing = {entry_16}` and the meta-test fails. The self-reference is a fixed-point — the meta-test is its own enforcer.

**Chicken-and-egg note:** On first run (before the meta-test exists), the allow-list enforcement is trivially satisfied because no tests are yet marked `no_waiver`. As tests are added, the allow-list is populated atomically with each test addition. This is NOT a bootstrap problem because the test infrastructure is built in dependency order: static tests first, then gate tests, then meta-test. Amelia implements the meta-test at the END of 5.3, after all other `no_waiver` tests exist.

#### §13.3.5 Retroactive Inventory — 3 Runtime Entries with Audit Flag

The 2 Runtime OTEL tests at lines 41/62 are in the allow-list with `provisionally_grandfathered` status and PENDING AUDIT inline comment. The reason for provisional: Amelia added them at Stage 4.3 without Pipeline ratification or 4.5 alignment review documentation. The team-lead will audit at 5.5.

**This strategy does NOT investigate those tests. It wires them into the allow-list with the provisional tag. That is the complete scope.**

#### §13.3.6 `MAC-T-META-NO-WAIVER-INV-01` Meta-test spec
- **Test ID:** `MAC-T-META-NO-WAIVER-INV-01`
- **Function name:** `test_mac_t_meta_no_waiver_inv_01_allowlist_check`
- **Purpose:** Enforce the `NO_WAIVER_ALLOWLIST` at collection time. See §13.3.2 for the full implementation.
- **Failure modes:**
  1. Unauthorized `no_waiver` test present in tree (not in allow-list) → AssertionError listing offenders.
  2. Allow-list entry absent from tree (silent removal) → AssertionError listing missing.
- **Self-referential lock:** meta-test's own ID is in allow-list (entry 16).
- **Marker set:** `static`, `critical`, `no_waiver`.
- **Target path:** `tests/static/runtime/test_no_waiver_inventory.py`

### §13.3.7 Operational Procedures for Allow-List Maintenance

When the allow-list needs to be modified (rare but unavoidable):

**Adding a new `no_waiver` test:**
1. Write the test code with `@pytest.mark.no_waiver`.
2. In the SAME PR, add the test's nodeid to `NO_WAIVER_ALLOWLIST` in `tests/static/runtime/test_no_waiver_inventory.py`.
3. Document the rationale in §13.3.3 of `mac/test-strategy.md` (or open a 5.5 alignment review for a Pipeline ratification).
4. Run `pytest tests/static/runtime/test_no_waiver_inventory.py` locally to confirm the meta-test passes.
5. Submit PR for review. Review checklist: (a) test is genuinely deterministic, (b) test is structurally invariant (not "feels like an invariant"), (c) allow-list and test code are added in same PR.

**Removing an existing `no_waiver` test (rare):**
1. Strip the `@pytest.mark.no_waiver` marker from the test.
2. In the SAME PR, remove the nodeid from `NO_WAIVER_ALLOWLIST`.
3. Document the rationale (the test is being demoted because... usually because it's been refactored into a higher-level test).
4. Run `pytest tests/static/runtime/test_no_waiver_inventory.py` to confirm the meta-test passes (allow-list still consistent).
5. PR review checklist: removal must be justified to the test architect (Murat).

**The 2 OTEL provisional entries (entries 2, 3 in §13.3.3):**
- These are PENDING AUDIT at 5.5 Alignment Review.
- The team-lead audits at 5.5 and decides: ratify (move from provisional to ratified) OR strip `no_waiver` (remove from allow-list and remove marker from test code).
- The 5.5 audit outcome updates this strategy and the allow-list in the same PR.

**Renaming a `no_waiver` test:**
1. Rename the test function.
2. Update the nodeid in `NO_WAIVER_ALLOWLIST`.
3. PR review: confirm both rename and allow-list update are in same PR.

The discipline is uncompromising because `no_waiver` is the strongest invariant marker. A test that should be `no_waiver` but isn't, OR a test that's `no_waiver` but shouldn't be, both represent silent failures of the invariant system. The allow-list meta-test catches the arithmetic; the operational procedures catch the semantics.

### §13.4 `no_waiver` Discipline Summary

| Source | # `no_waiver` tests | Allow-list entries |
|---|---|---|
| Runtime ratified (existing) | 1 | 1 (entry 1) |
| Runtime provisional (PENDING AUDIT at 5.5) | 2 | 2 (entries 2, 3) |
| MAC calibration anchor (Decision 1 — 10 gate calibration tests) | 10 | 10 (entries 4–13) |
| MAC split deterministic carriers (Decision 1 items 9, 11 det) | 2 | 2 (entries 14, 15) |
| Meta-test self-reference | 1 | 1 (entry 16) |
| **Total** | **16** | **16** |

### §13.5 Coverage Exclusion Policy — Tension #7 Resolution

**Tension #7 (coverage vs live mock):** `LLMJudgeClient.call_live()` is the gateway to real LLM calls. In PR-gate tests it is NEVER executed (only `FakeLLMJudge` runs), so any coverage measurement would show `call_live()` at 0%. Excluding it would lower the coverage floor slightly but correctly. Preload resolution: **explicit exclusion with documented precedent**.

#### §13.5.1 Excluded from coverage

```toml
# pyproject.toml [tool.coverage.run]
omit = [
    "praxis/kernel/mac/judge/llm_judge_client.py:call_live",
    # Rationale: this method is the real-LLM gateway; only invoked from nightly
    # CI live-judge tests, never from PR-gate tests. Excluding it keeps the
    # ≥90% coverage floor honest. Follows pi-mono/test-strategy.md §7
    # generated-file exclusion precedent.
]
```

#### §13.5.2 Exclusion precedent

From `pi-mono/test-strategy.md §7`: generated protobuf files are excluded from coverage because they are auto-generated and not hand-tested. The MAC exclusion follows the same principle: code that is exclusively exercised by Tier 3 nightly tests is excluded from PR-gate coverage because the PR gate cannot exercise it.

#### §13.5.3 What is NOT excluded

- `FakeLLMJudge` — not excluded (exercised by Tier 1 tests).
- `LLMJudgeClient.__init__` — not excluded (construction is testable).
- `LLMJudgeClient.build_prompt` — not excluded (prompt building is pure logic).
- ONLY `LLMJudgeClient.call_live()` is excluded, and only because it requires a real network call.

### §13.5A Coverage Measurement Implementation Detail

The 90% line + branch coverage target is measured against the production code at `praxis/kernel/mac/` (and only that directory). Test fixture code at `praxis/kernel/mac/testing/fakes/` is included in the measured set per Stage 4 convention.

**Measurement command:**
```bash
pytest --cov=praxis.kernel.mac \
       --cov-report=term-missing \
       --cov-report=xml:coverage.xml \
       --cov-branch \
       --cov-fail-under=90 \
       --strict-markers \
       --strict-config \
       tests/mac/
```

**Expected output (excerpt):**
```
Name                                                 Stmts   Miss Branch BrPart   Cover   Missing
-----------------------------------------------------------------------------------------------
praxis/kernel/mac/__init__.py                            5      0      0      0  100.00%
praxis/kernel/mac/cycle/iteration_controller.py        180      8     42      4   94.59%   141, 217-220, 305-307
praxis/kernel/mac/gates/r1.py                           42      0     12      0  100.00%
praxis/kernel/mac/gates/r4.py                           67      2     18      1   96.47%   88-89
praxis/kernel/mac/gates/r11.py                          54      1     14      0   98.51%   72
praxis/kernel/mac/judge/llm_judge_client.py             38     12      6      0   72.73%   call_live (excluded)
praxis/kernel/mac/observability/telemetry_labels.py     22      0      4      0  100.00%
[...]
TOTAL                                                  890     61    198     17   91.74%
```

The exclusion of `LLMJudgeClient.call_live` is reflected in the `Missing` column but does NOT count against the 90% floor (per `pyproject.toml [tool.coverage.run] omit`).

#### §13.5A.1 Coverage Failure Mode

If coverage falls below 90%, the PR-gate CI fails with:
```
FAIL: Coverage 87.3% is below required minimum 90.0%.
Top missing lines:
  praxis/kernel/mac/gates/r7.py:44-47 (Forge penalty post-co-eval-cap path per arch §6.3 SQ-7 step 3)
  praxis/kernel/mac/gates/r4.py:88-89 (Req-F fallback)
```

The CI message names the missing lines, so Amelia can immediately add tests targeting them.

### §13.5B Test Marker Selection Decision Matrix

When Amelia is implementing a new test, the marker selection process is:

1. **Is the test deterministic and a hard structural invariant?** → `no_waiver` (and add to allow-list).
2. **Is the test release-blocking on failure?** → `critical`.
3. **Is the test compile-time / collection-time / grep-based?** → `static`.
4. **Does the test require Postgres or other external services?** → `integration`.
5. **Is the test sensitive to wall-clock timing?** → `wall_clock` (and use `FrozenClock`).
6. **Does the test verify async task structure?** → `asyncio_structural`.
7. **Does the test exercise Forge F1/F3 boundaries?** → `f1_absorption` or `f3_absorption`.
8. **Is the test a calibration anchor for a gate?** → `mac_gate_calibration`.
9. **Is the test part of the benchmark harness?** → `mac_benchmark_harness`.
10. **Is the test for the bootstrap loader?** → `mac_bootstrap_loader`.
11. **Is the test for the adversarial corpus?** → `mac_adversarial`.
12. **Is the test enforcing reviewer-producer asymmetry?** → `asymmetry_structural`.
13. **Is the test for cycle determinism / state self-consistency?** → `mac_self_consistency`.
14. **Is the test for the label registry?** → `mac_label_registry`.
15. **Is the test too expensive for PR-gate?** → `nightly_only`.
16. **Is the test only run on release-candidate tagging?** → `release_gate`.

Multiple markers can apply. For example, a test for the live R4 reviewer carries `critical + asymmetry_structural + nightly_only + mac_gate_calibration` (4 markers).

### §13.6 Marker Registration

To be added to `praxis/kernel/mac/pyproject.toml` at Stage 5.3 by Amelia:

```toml
[tool.pytest.ini_options]
markers = [
    # Inherited from runtime
    "critical: test is release-blocking if failing",
    "no_waiver: deterministic invariant — cannot be waived in any PR; enforced by test_no_waiver_inventory.py",
    "asyncio_structural: async structural invariant",
    "f1_absorption: Forge F1 absorption boundary",
    "f3_absorption: Forge F3 absorption boundary",
    "integration: multi-component wire-up test",
    "oqn_escalation_canary: OQ-N escalation canary",
    "r53_structural: Req-5.3 structural invariant",
    "static: collection-time / grep-based structural test",
    "wall_clock: real-time sensitive test",
    "asymmetry_structural: proxy / bus asymmetry structural invariant",

    # MAC-new
    "mac_gate_calibration: MAC gate calibration anchor test",
    "mac_benchmark_harness: MAC benchmark harness test",
    "mac_bootstrap_loader: MAC bootstrap loader test",
    "mac_adversarial: MAC adversarial test",
    "mac_self_consistency: MAC self-consistency invariant",
    "mac_label_registry: MAC observability label registry test",
    "nightly_only: runs in nightly CI only, NOT PR gate",
    "release_gate: runs on release candidate only",
]
```

---

## §14 Test Execution Strategy

### §14.1 Directory Layout

```
tests/
├── mac/
│   ├── gates/
│   │   ├── conftest.py
│   │   ├── snapshots/
│   │   │   ├── gate_catalog_v0_1.yaml
│   │   │   └── section_routes_v0_1.yaml
│   │   ├── test_r1.py
│   │   ├── test_r2.py
│   │   ├── test_r3.py
│   │   ├── test_r4.py
│   │   ├── test_r5.py
│   │   ├── test_r6.py
│   │   ├── test_r7.py
│   │   ├── test_r8.py
│   │   ├── test_r9.py
│   │   ├── test_r10.py
│   │   ├── test_r11.py
│   │   ├── test_r12.py
│   │   ├── test_gate_catalog_snapshot.py
│   │   └── test_gate_cross_properties.py
│   ├── cycle/
│   │   ├── conftest.py
│   │   ├── snapshots/
│   │   │   └── gate_section_routes_v0_1.bin
│   │   ├── test_state_machine.py
│   │   ├── test_budget.py
│   │   ├── test_backtracking.py
│   │   ├── test_parallelism.py
│   │   ├── test_forge_ordering.py
│   │   └── test_section_router.py
│   ├── asymmetry/
│   │   ├── conftest.py
│   │   ├── test_req_f.py
│   │   ├── test_proxy_asymmetry.py
│   │   └── test_bus_filter.py
│   ├── integration/
│   │   ├── conftest.py                     # testcontainers Postgres fixture
│   │   ├── test_cost_tracker.py
│   │   ├── test_memory_contracts.py
│   │   ├── test_runtime_spawner.py
│   │   ├── test_mcp_shape_guard.py
│   │   └── test_forge_f8.py
│   ├── benchmark/
│   │   ├── conftest.py
│   │   ├── fixtures/
│   │   │   ├── fake_benchmark_outputs.py
│   │   │   └── andrey_scores_rc1.yaml
│   │   ├── test_scoring.py
│   │   ├── test_adr1_hybrid.py
│   │   ├── test_adr3_spearman.py
│   │   ├── test_baselines.py
│   │   ├── test_corpus.py
│   │   ├── test_calibration_anchors.py
│   │   ├── test_fake_harness_smoke.py
│   │   └── test_nightly_harness.py           # nightly_only
│   ├── bootstrap/
│   │   ├── conftest.py
│   │   ├── test_migration.py
│   │   ├── test_gold_standard_loading.py
│   │   ├── test_idempotency.py
│   │   └── test_facade.py
│   ├── observability/
│   │   ├── conftest.py
│   │   ├── snapshots/
│   │   │   └── metrics_v0_1.yaml
│   │   ├── test_label_registry.py
│   │   ├── test_dedup_namespace.py
│   │   ├── test_violation_counter.py
│   │   └── test_metric_catalog.py
│   ├── adversarial/
│   │   ├── conftest.py
│   │   ├── fixtures/
│   │   │   └── persona_3/
│   │   │       ├── public/
│   │   │       └── rotating/
│   │   ├── test_persona_3.py
│   │   ├── test_r11_probing.py
│   │   ├── test_r12_probing.py
│   │   └── test_rotation_protocol.py
│   ├── negative/
│   │   ├── conftest.py
│   │   ├── test_no_gate_13.py
│   │   ├── test_option_x_absence.py
│   │   ├── test_no_parallel_telemetry.py
│   │   ├── test_domain_class_singular.py
│   │   └── test_pinning.py
│   └── calibration/
│       ├── conftest.py                    # nightly_only
│       ├── test_r1_drift.py
│       ├── test_r2_drift.py
│       ├── test_r3_drift.py
│       ├── test_r4_drift.py
│       ├── test_r5_drift.py
│       ├── test_r6_drift.py
│       ├── test_r7_drift.py
│       ├── test_r8_drift.py
│       ├── test_r9_drift.py
│       ├── test_r10_drift.py
│       ├── test_r11_drift.py
│       └── test_r12_drift.py
├── release/
│   └── test_a4_validation.py              # release_gate
└── static/
    └── runtime/
        └── test_no_waiver_inventory.py    # §13.3 meta-test (cross-stage)
```

### §14.2 Pytest Configuration

```toml
# pyproject.toml [tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "strict"
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
    "--cov=praxis.kernel.mac",
    "--cov-branch",
    "--cov-report=term-missing",
    "--cov-fail-under=90",
]
```

### §14.3 Fixture Interface Contracts (Amelia Implements Verbatim at 5.3)

#### §14.3.1 `FakeLLMJudge`

```python
# praxis/kernel/mac/testing/fakes/fake_llm_judge.py
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class JudgeResponse:
    score: int         # 1..5
    rationale: str

class FakeLLMJudge:
    """
    Deterministic judge — lookup-table backed.

    Lookup key: (gate_id: str, output_fingerprint: str)
    Lookup value: JudgeResponse

    Fingerprint is computed via a stable hash of the canonical-JSON
    serialization of the input (not raw bytes, to tolerate whitespace).
    """

    def __init__(self, lookup_table: dict[tuple[str, str], JudgeResponse]):
        self._table = lookup_table
        self._call_log: list[tuple[str, str]] = []

    def score(self, *, gate_id: str, input_payload: dict) -> JudgeResponse:
        fp = self._fingerprint(input_payload)
        key = (gate_id, fp)
        self._call_log.append(key)
        if key not in self._table:
            raise KeyError(
                f"FakeLLMJudge lookup miss: gate={gate_id}, fp={fp[:16]}... "
                f"Either regenerate the lookup table or provide the fixture."
            )
        return self._table[key]

    @property
    def call_log(self) -> list[tuple[str, str]]:
        return list(self._call_log)

    @staticmethod
    def _fingerprint(payload: dict) -> str:
        import hashlib, json
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

# --- Lookup table generation (pseudocode for Amelia) ---
# def build_lookup_table_from_calibration_anchors() -> dict:
#     """
#     Walk benchmark-questions.md §5; for each (gate_id, score_level, text),
#     insert a lookup row keyed by (gate_id, fingerprint(text)) mapping to
#     JudgeResponse(score=score_level, rationale=f"§5 {gate_id} score_{score_level}").
#     Also add gate-level fixture outputs per §3.x unit scoring tests.
#     """
#     table = {}
#     for gate_id, score_level, text in parse_calibration_anchors():
#         fp = FakeLLMJudge._fingerprint(text)
#         table[(gate_id, fp)] = JudgeResponse(score=score_level, rationale=f"§5 {gate_id} {score_level}")
#     for gate_id, fixture_name, score, text in parse_gate_fixtures():
#         fp = FakeLLMJudge._fingerprint(text)
#         table[(gate_id, fp)] = JudgeResponse(score=score, rationale=fixture_name)
#     return table
```

#### §14.3.2 `FakeReviewerAgent`

```python
# praxis/kernel/mac/testing/fakes/fake_reviewer_agent.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ReviewerCritique:
    independent_steelman: str      # MUST come before gap_assessment (Req-F ordering)
    gap_assessment: str
    gate_scores: dict[str, int]    # {"R1": 4, "R2": 3, ...}

class FakeReviewerAgent:
    """
    Deterministic reviewer — seeded by (task_hash, reviewer_index).

    The tuple (task_hash, reviewer_index) uniquely determines the returned
    ReviewerCritique. Used by the Deterministic Replay Pattern (§4.5).
    """

    def __init__(self, lookup_table: dict[tuple[str, int], ReviewerCritique]):
        self._table = lookup_table
        self._call_log: list[tuple[str, int]] = []

    def review(self, *, task_hash: str, reviewer_index: int,
               task_payload: dict) -> ReviewerCritique:
        key = (task_hash, reviewer_index)
        self._call_log.append(key)
        if key not in self._table:
            raise KeyError(
                f"FakeReviewerAgent lookup miss: task_hash={task_hash}, "
                f"reviewer_index={reviewer_index}"
            )
        return self._table[key]

    @property
    def call_log(self) -> list[tuple[str, int]]:
        return list(self._call_log)
```

#### §14.3.3 `FrozenClock`

```python
# praxis/kernel/mac/testing/fakes/frozen_clock.py
from datetime import datetime, timedelta

class FrozenClock:
    """
    Injectable clock for wall_clock tests. Replaces datetime.utcnow().
    Advance is explicit.
    """

    def __init__(self, initial: datetime):
        self._now = initial

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: int) -> None:
        self._now += timedelta(seconds=seconds)
```

#### §14.3.4 `FakeCompressor`

```python
# praxis/kernel/mac/testing/fakes/fake_compressor.py
from dataclasses import dataclass

@dataclass(frozen=True)
class CompressionResult:
    compressed: bytes
    reasoning_preserved: bool

class FakeCompressor:
    """
    Deterministic compressor — used to exercise the Forge-degradation path
    (Tension #4) per arch §5.6 + §6.3 SQ-7 step 3. Given a specific fixture
    payload, returns reasoning_preserved=False to trigger the R7 penalty
    behavioral path. The controller stays in normal arch §5.2 states; the
    Forge-degradation effect is applied to gate scores via SQ-7 ordering,
    not via a dedicated state transition.
    """

    def __init__(self, force_degradation: bool = False):
        self._force = force_degradation

    def compress(self, payload: bytes) -> CompressionResult:
        return CompressionResult(
            compressed=payload,  # no-op compression
            reasoning_preserved=not self._force,
        )
```

#### §14.3.5 `FakeBenchmarkOutputs`

```python
# praxis/kernel/mac/testing/fakes/fake_benchmark_outputs.py
from dataclasses import dataclass

@dataclass(frozen=True)
class PreScoredOutput:
    """
    A pre-scored benchmark output with the 12 gate scores already
    computed. Used in §7 tests to exercise the composite / ADR-1 /
    ADR-3 logic without calling any LLM.
    """
    question_id: str          # "Q1".."Q10"
    baseline: str             # "vanilla" | "enhanced" | "mac"
    text: str                 # the output text (used by Pass 1 blind)
    gate_scores: dict[str, int]  # {"R1": 4, ..., "R12": 5}

class FakeBenchmarkOutputs:
    """
    30-item lookup table (10 questions × 3 baselines) of pre-scored outputs.
    """

    def __init__(self, outputs: dict[tuple[str, str], PreScoredOutput]):
        self._outputs = outputs

    def get(self, *, question_id: str, baseline: str) -> PreScoredOutput:
        key = (question_id, baseline)
        if key not in self._outputs:
            raise KeyError(f"FakeBenchmarkOutputs miss: {key}")
        return self._outputs[key]

    def all(self) -> list[PreScoredOutput]:
        return list(self._outputs.values())
```

#### §14.3.6 `MacBootstrapMetadataStore` (test double)

```python
# praxis/kernel/mac/testing/fakes/fake_metadata_store.py
class InMemoryMacBootstrapMetadataStore:
    """
    In-memory double for the sidecar table `mac_bootstrap_metadata`.
    Used by unit tests that don't need a real Postgres. Integration tests
    use the real Postgres implementation via testcontainers.
    """

    def __init__(self):
        self._rows: list[dict] = []
        self._loaded = False

    def mark_loaded(self) -> None:
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def insert_batch(self, rows: list[dict]) -> None:
        self._rows.extend(rows)

    def count(self) -> int:
        return len(self._rows)

    def reset(self) -> None:
        self._rows = []
        self._loaded = False
```

#### §14.3.7 `ResetCounterFixture`

```python
# tests/mac/observability/conftest.py
import pytest
from praxis.kernel.mac.observability.counters import MacCounters

@pytest.fixture(autouse=True)
def reset_counter_fixture():
    """
    Resets mac.label_registry.violations to 0 before each test in
    tests/mac/observability/. Autouse — applied to every test.
    S-Q2 bake-in.
    """
    MacCounters.reset("mac.label_registry.violations")
    yield
    # Post-test assertion available via MacCounters.get()
```

### §14.3.8 Fixture Composition Pattern

Tests often need multiple fakes wired together. The `mac_test_environment` fixture composes them:

```python
# tests/mac/conftest.py
import pytest
from datetime import datetime
from praxis.kernel.mac.testing.fakes import (
    FakeLLMJudge, FakeReviewerAgent, FakeCompressor,
    FrozenClock, InMemoryMacBootstrapMetadataStore,
    build_default_lookup_table, build_default_reviewer_table,
)

@pytest.fixture
def mac_test_environment():
    """
    Composed test environment with all 7 fakes wired together.
    Used by Tier 1 tests that need a fully-instantiated MAC pipeline
    without any real services.
    """
    return MacTestEnvironment(
        judge=FakeLLMJudge(lookup_table=build_default_lookup_table()),
        reviewer=FakeReviewerAgent(lookup_table=build_default_reviewer_table()),
        compressor=FakeCompressor(force_degradation=False),
        clock=FrozenClock(initial=datetime(2026, 4, 14, 12, 0, 0)),
        metadata_store=InMemoryMacBootstrapMetadataStore(),
    )

@pytest.fixture
def mac_test_environment_forge_degraded(mac_test_environment):
    """Variant: Forge fallback path."""
    mac_test_environment.compressor = FakeCompressor(force_degradation=True)
    return mac_test_environment
```

Tests use the fixture by injection:

```python
def test_mac_t_cycle_state_05_forge_degradation_behavioral(mac_test_environment_forge_degraded):
    controller = build_controller(mac_test_environment_forge_degraded)
    result = controller.run(fixture.simple_task)
    # Normal arch §5.2 terminal state — no fabricated state transition
    assert result.final_state == State.COMPLETE
    # Forge penalty applied to R7 per arch §6.3 SQ-7 step 3
    assert result.final_scores["R7"].effective == 3
    assert result.final_scores["R7"].forge_degraded == True
    assert "mac.cycle.forge_degradation_detected" in [e.name for e in telemetry.events]
```

Composition keeps individual tests terse (one line of setup) while the fixture file documents the full wiring.

### §14.4 CI Budget

| Tier | Gate | Wall-clock budget | Cost budget (LLM calls) | Scope |
|---|---|---|---|---|
| 1 (unit + property + contract) | PR gate | <60s per family | 0 | 175+ tests |
| 2 (integration with Postgres/Memory) | PR gate | <5 min total | 0 | ~55 tests |
| 3 (live-judge drift canary + nightly harness) | nightly | 30–60 min | ~90 calls per night (60 canary + 30 harness) | ~30 tests |
| 4 (release gate) | release | ~5 min | ~30 calls (A4 verification, one-shot) | ~5 tests |

Total nightly cost envelope per run: **~$X** (to be computed at 5.3 Amelia with concrete model pricing). The 5.3 implementation scales the retry count in §12.3 based on the observed cost and model availability.

### §14.4A Estimated CI Wall-Clock Per Tier

| Tier | Tests | Estimated wall-clock (clean run) | Estimated wall-clock (with retries) |
|---|---|---|---|
| 1 unit + property + contract | ~175 | 60–90 seconds | 90–120 seconds |
| 2 integration (Postgres) | ~55 | 3–5 minutes | 5–7 minutes |
| 3 nightly drift canary | 24 + ~6 live | 20–35 minutes | 30–60 minutes |
| 3 nightly benchmark harness | 30 baseline runs | 25–45 minutes | 35–60 minutes |
| 4 release gate | ~5 | 3–5 minutes | 5–10 minutes |

The PR-gate (Tier 1 + Tier 2) totals ~5–8 minutes with retries — within the team's PR cycle SLA of <10 minutes.

Nightly Tier 3 totals ~50–120 minutes, scheduled at 02:00 UTC outside business hours.

Release gate Tier 4 totals ~10 minutes, run on tag push (rare).

### §14.4B Test Parallelization

- **Tier 1:** parallelized via `pytest-xdist -n auto` (one worker per CPU core). State-machine property tests use `hypothesis` with deterministic seeds, so parallelization doesn't introduce non-determinism.
- **Tier 2:** parallelized at the FILE level only (not test level), because each file gets its own session-scoped Postgres container. `pytest-xdist -n 4` typical.
- **Tier 3:** sequential. Live LLM calls have rate limits; concurrent calls would burn budget without speedup.
- **Tier 4:** sequential. A4 Andrey-in-the-loop test reads a single fixture file.

### §14.5 Checkpoint Cadence

From the 5.3 build plan, checkpoints in order:
- **C1: Gate skeleton** — §3.1 (catalog snapshot) + §3.2–§3.13 R1 only + §11.1 (no gate 13).
- **C2: All 12 gates unit + calibration** — complete §3.2–§3.13 unit tests and deterministic calibration. 60+ tests.
- **C3: Cycle controller** — §4.2 (state machine) + §4.3 (budget) + §4.4 (backtracking).
- **C4: Information asymmetry** — §5 complete.
- **C5: Integration** — §6 complete.
- **C6: Bootstrap loader + negative** — §8 + §11 complete.
- **C7: Observability** — §9 complete.
- **C8: Evaluation harness (unit, Tier 1 + 2)** — §7.2 through §7.8.
- **C9: Adversarial (unit + rotation)** — §10 complete.
- **C10: Calibration nightly + meta-test** — §12 and §13.3 allow-list meta-test. This is the final checkpoint because the meta-test depends on all other `no_waiver` tests being present.

Red-first order: every checkpoint starts with the negative tests (§11 subset for that checkpoint's domain), then the structural tests, then the unit tests, then the integration tests.

### §14.6 Postgres via testcontainers

Integration tests (Tier 2) use `testcontainers[postgres]` for an isolated Postgres instance per test session. Schema is migrated at session start; rolled back between tests via savepoints.

```python
# tests/mac/integration/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.fixture
def pg_connection(postgres_container, request):
    conn = postgres_container.get_connection()
    # Apply migrations in order: Memory, Pi-Mono, MAC sidecar
    apply_migrations(conn)
    savepoint = conn.savepoint()
    yield conn
    conn.rollback_to_savepoint(savepoint)
```

### §14.7 Mock vs Live Split — Execution View

| Scenario | PR gate | Nightly | Release |
|---|---|---|---|
| Gate logic (unit) | Tier 1 — `FakeLLMJudge` | — | — |
| Gate calibration bucket | Tier 1 — `FakeLLMJudge` replay | Tier 3 — real LLM drift canary | — |
| Cycle state machine | Tier 1 — property | — | — |
| Integration (Postgres) | Tier 2 — testcontainers | — | — |
| Benchmark harness logic | Tier 1 — `FakeBenchmarkOutputs` | — | — |
| Full 30-score benchmark | — | Tier 3 — real LLM | Tier 4 — real LLM verification |
| Req-F structural | Tier 1 — schema check | Tier 3 — live reviewer | — |
| Adversarial Persona 3 fixture inventory | Tier 1 — static | Tier 3 — live adversarial | — |
| A4 Andrey Spearman math | — | — | Tier 4 — fixture replay |
| `no_waiver` allow-list meta-test | Tier 1 — collection-time | — | — |

---

## §15 Test ID Schema

### §15.1 Schema Definition

**Format:** `MAC-T-{section}-{seq}`

Where:
- `MAC-T` is the prefix (differentiates from Runtime's `TS-` prefix inherited from Stage 4).
- `{section}` is one of:
  - `GATE-R{N}` — gate-level test for R{1..12}
  - `GATE-CATALOG-SNAPSHOT` — catalog snapshot test
  - `GATE-PROP` — cross-gate property test
  - `CYCLE-STATE` — cycle state machine
  - `CYCLE-BUDGET` — cycle budget enforcement
  - `CYCLE-BACKTRACK` — cycle backtracking
  - `CYCLE-PARALLEL` — cycle parallelism / deterministic replay
  - `CYCLE-FORGE` — cycle Forge-degradation ordering
  - `CYCLE-SEC` — cycle section routing
  - `ASYM-R-F` — Req-F reviewer two-step
  - `ASYM-PROXY` — proxy asymmetry
  - `ASYM-BUS` — bus filter
  - `INT-COSTTRACKER` — integration Pi-Mono CostTracker
  - `INT-MEMORY-PUBLISH` — integration Memory publish contract
  - `INT-MEMORY-REUSE` — integration Memory reuse contract
  - `INT-MEMORY-BACKFILL` — integration Memory backfill contract
  - `INT-MEMORY-ASYMMETRY-WIRE` — integration Memory asymmetry wire
  - `INT-RUNTIME-SPAWNER` — integration Runtime spawner
  - `INT-RUNTIME-MCP-SHAPE-GUARD` — integration MCP shape guard
  - `INT-FORGE-F8` — integration Forge F8
  - `BENCH-SCORING` — benchmark scoring logic
  - `BENCH-ADR1` — benchmark ADR-1 hybrid pass
  - `BENCH-SPEARMAN` — benchmark ADR-3 Spearman
  - `BENCH-BASELINE` — benchmark baseline comparison
  - `BENCH-CORPUS` — benchmark question corpus
  - `BENCH-CALIBRATION` — benchmark §5 calibration anchors
  - `BENCH-FAKE` — benchmark with FakeBenchmarkOutputs
  - `BENCH-NIGHTLY` — benchmark nightly harness
  - `BENCH-A4` — benchmark A4 release gate
  - `BOOT-MIGRATION` — bootstrap migration
  - `BOOT-LOAD` — bootstrap gold standard loading
  - `BOOT-IDEMPOTENT` — bootstrap idempotency (S-Q1)
  - `BOOT-FACADE` — bootstrap facade
  - `OBS-LABEL-REG` — observability label registry
  - `OBS-DEDUP` — observability dedup namespace
  - `OBS-VIOLATION` — observability violation counter (S-Q2)
  - `OBS-METRIC` — observability metric catalog
  - `ADV-P3` — adversarial Persona 3
  - `ADV-R11` — adversarial R11 probing
  - `ADV-R12` — adversarial R12 probing
  - `ADV-ROTATION` — adversarial corpus rotation
  - `NEG-GATE13` — negative no 13th gate
  - `NEG-OPTION-X` — negative Option X absence
  - `NEG-TELEMETRY` — negative no parallel telemetry
  - `NEG-DOMAIN-CLASS` — negative DomainClass singular
  - `NEG-MCP-PIN` — negative MCP version pin
  - `CAL-R{N}-DRIFT-{LOW|HIGH}` — live drift canary
  - `META-NO-WAIVER-INV` — allow-list meta-test
- `{seq}` is a zero-padded 2-digit sequence number: `01`, `02`, ..., `99`.

### §15.2 ID-to-Spec-Row Mapping

Every test ID maps back to one or more of:
- **`quality-rubric.md §6 R{N}`** — the rubric rule being validated.
- **`mac/architecture.md §{X.Y}`** — the architectural commitment being tested.
- **`benchmark-questions.md §{X}`** — for benchmark/calibration tests.
- **`Pipeline.md §5.2`** — for top-level gate checklist traceability.

### §15.3 Test Function Naming Convention

Python test functions are named `test_{lowercase_id_with_underscores}_{description}`:

- `MAC-T-GATE-R1-02` → `def test_mac_t_gate_r1_02_calibration_anchor(...)`
- `MAC-T-META-NO-WAIVER-INV-01` → `def test_mac_t_meta_no_waiver_inv_01_allowlist_check(...)`
- `MAC-T-BOOT-IDEMPOTENT-01` → `def test_mac_t_boot_idempotent_01_second_call_returns_zero(...)`

This convention is inherited from `runtime/test-strategy.md §15` with the `mac_t_` prefix substitution.

### §15.3A Worked Example — Test ID Anatomy

Take `MAC-T-GATE-R8-05`:

- **Prefix:** `MAC-T` — MAC test (vs Runtime's `TS-`).
- **Section:** `GATE-R8` — gate-level test for R8 (Actionability Calibration).
- **Sequence:** `05` — fifth test in the R8 sub-section.

Mapping to specs:
- `quality-rubric.md §6 R8` — actionability calibration rubric.
- `mac/architecture.md §6.1 R8 row` — gate catalog entry.
- `mac/architecture.md §12.5 SQ-7` — Forge degradation ordering (this test is the (R8, R7) co-eval cap with SQ-7 ordering).
- `mac/architecture.md §6.3 R8 judge prompt` — the prompt template.

Marker stack:
- `critical` (release-blocking)
- `mac_gate_calibration` (gate-level)
- `f1_absorption` (uses Forge degradation)
- NOT `no_waiver` (R8 is co-eval-capped, not on the Decision 1 list — only the R8 calibration anchor `R8-02` is `no_waiver`)

Function name: `def test_mac_t_gate_r8_05_co_eval_with_raw_r7(...)`

File: `tests/mac/gates/test_r8.py`

### §15.3B Worked Example 2 — Cross-Sectional Test

Take `MAC-T-CYCLE-FORGE-01`:

- **Prefix:** `MAC-T`
- **Section:** `CYCLE-FORGE` — cycle-level Forge ordering test
- **Sequence:** `01`

This test exercises:
- §4.1 state machine — controller stays in the normal arch §5.2 path (`CYCLE_3_VERIFY → PUBLISH/BACKTRACK_SET/FAILED`); §4.2.5 tests the Forge-degradation behavioral integration per arch §5.6 + §6.3 SQ-7 step 3 (no fabricated state transition).
- §4.6 SQ-7 ordering — verifies the (raw → Req-C co-eval → Forge penalty last) sequence.
- §3.8.5 R7 Forge degradation — uses R7 as a witness gate.
- §3.9.5 R8 co-eval cap — uses R8 as the second witness.

Mapping to multiple specs:
- `mac/architecture.md §5.2 State Machine` — controller normal-path semantics.
- `mac/architecture.md §5.6 Forge Fallback Handling` — behavioral fallback (apply R7 penalty, continue cycle; not a state transition).
- `mac/architecture.md §6.3 SQ-7 ordering` — three-step ordering rule (raw → Req-C caps → Forge penalty last on R7_effective).
- `quality-rubric.md §6 R7 + §6 R8` — gate definitions (Reasoning Traceability + Actionability Calibration).

This kind of cross-sectional test is named at the cycle level (CYCLE-FORGE) rather than the gate level because the dominant concern is cycle-controller orchestration, not gate-individual logic.

### §15.4 Cycle/SQ/Benchmark Q Mapping

- **Cycle tests** (§4) map to `mac/architecture.md §5.2 State Machine` + `§5.4 Cycle 2 Parallelism` + `§5.5 Backtracking on Critical Gate Failure` + `§5.7 ResourceBudget Defaults`.
- **SQ tests** (SQ-5 `DomainClass`, SQ-7 Forge ordering) map to `mac/architecture.md §6.5 Domain Guard Conditions (Req-E + SQ-5)` + `§6.3 Co-Evaluation Pairs (Req-C + SQ-4 + SQ-7 ordering)`.
- **Benchmark Q tests** (Q1–Q10) map to `benchmark-questions.md §2 question corpus`.
- **S-Q tests** (S-Q1 bootstrap, S-Q2 counter, S-Q3 harness split, S-Q4 A4 gate) map to the 5.2 decision-3 ratifications in §7.9, §7.10, §8.4, §9.3.

---

## §16 Handoff to 5.3 Amelia

### §16.1 What Amelia Implements

Amelia (5.3 Dev) implements the test code AGAINST this strategy. Every test in this document is a contract: Amelia does NOT invent tests, does NOT skip tests, does NOT rename tests.

Scope of 5.3:
1. Create directory structure per §14.1.
2. Implement fake fixtures per §14.3 (all 7: `FakeLLMJudge`, `FakeReviewerAgent`, `FrozenClock`, `FakeCompressor`, `FakeBenchmarkOutputs`, `InMemoryMacBootstrapMetadataStore`, `ResetCounterFixture`).
3. Implement each test function per §3–§12 using the fixture interfaces.
4. Register markers in `praxis/kernel/mac/pyproject.toml` per §13.6.
5. Implement the allow-list meta-test at `tests/static/runtime/test_no_waiver_inventory.py` per §13.3.2 — **LAST**, after all other `no_waiver` tests exist, to avoid bootstrap collection failures.
6. Set up nightly CI pipeline for Tier 3 tests per §14.4.
7. Ensure PR-gate coverage ≥90% per §13.2 with exclusions per §13.5.
8. Checkpoint cadence per §14.5.

### §16.2 Red-First Test Order

For each checkpoint, Amelia writes tests in this order:
1. **Negative/static** — the "this must NOT exist" and "this must be shaped like X" tests (§11 subset for the checkpoint).
2. **Unit** — pure logic tests with fake fixtures.
3. **Property** — Hypothesis-based property tests.
4. **Contract** — schema and payload shape tests.
5. **Integration** — Postgres + Memory + Pi-Mono wire-ups.

The negative-first order catches architectural drift early: if Amelia accidentally creates a 13th gate module while working on C1, the NEG-GATE13 test from checkpoint C1 will fail immediately.

### §16.3 Checkpoint Plan (Red-First)

| # | Checkpoint | Target count | Dependencies |
|---|---|---|---|
| C1 | Gate skeleton (R1 + catalog + no-gate-13) | ~10 tests | — |
| C2 | All 12 gate unit + calibration | ~75 tests | C1 |
| C3 | Cycle controller | ~18 tests | C2 |
| C4 | Information asymmetry | ~12 tests | C3 |
| C5 | Integration (Pi-Mono/Memory/Runtime/Forge) | ~12 tests | C4 |
| C6 | Bootstrap + negative | ~22 tests | C5 |
| C7 | Observability | ~13 tests | C5 |
| C8 | Evaluation harness (Tier 1 + 2) | ~17 tests | C2, C5 |
| C9 | Adversarial | ~11 tests | C2, C8 |
| C10 | Calibration nightly + meta-test | ~25 tests | ALL prior |
| **Total** | — | **~215 tests** | |

### §16.4 Amelia Preflight Checklist

Before starting 5.3, Amelia must:
- [ ] Read this strategy in full (§1–§16).
- [ ] Verify `mac/architecture.md` v0.1 is ratified and the 4 binding inputs exist at the paths cited.
- [x] `NO_WAIVER_ALLOWLIST` count resolved — 16 entries ratified 2026-04-14 per §13.3.3.1. Amelia implements all 16 entries verbatim; no entry is added, removed, or reordered without an explicit team-lead ratification message.
- [ ] Stand up the `tests/mac/` directory with empty `conftest.py` files.
- [ ] Install `testcontainers[postgres]`, `hypothesis`, `pytest-cov` with version pins matching the Stage 5.3 `pyproject.toml`.
- [ ] Run `pytest --collect-only tests/mac/` and verify it yields 0 test items (empty scaffolding).

### §16.5 Red-Band Definition for 5.3 Ratification

5.3 ratification requires:
1. All tests in §3–§12 exist in the code base with the IDs defined in this strategy.
2. All fake fixtures in §14.3 exist and are used by the tests.
3. Tier 1 + Tier 2 tests pass in PR-gate CI.
4. Tier 3 nightly tests pass in the first nightly run.
5. Coverage ≥90% on `praxis/kernel/mac/` (with §13.5 exclusions).
6. `no_waiver` allow-list meta-test passes (i.e., every `no_waiver` test is in the allow-list and every allow-list entry is found).
7. `§13.1 gate checklist` has every sub-check fulfilled (inherited from 5.2 at ratification time; re-verified at 5.5 alignment review).

### §16.5A Common Pitfalls for 5.3 Amelia

Based on the Stage 4 retrospective and the soft questions raised in Stage 5.2 preload, the following pitfalls are flagged for Amelia at 5.3 implementation time:

1. **Don't add `no_waiver` outside the allow-list.** The OQ-TS-9 meta-test in §13.3 will fail collection if any `no_waiver` test is not in `NO_WAIVER_ALLOWLIST`. Before adding any new `no_waiver` marker, update the allow-list in the same PR. The meta-test enforces this atomically.

2. **Don't bypass the violation counter for tests.** S-Q2 ratification (§9.3) says the `mac.label_registry.violations` counter increments unconditionally, even in tests. Use `ResetCounterFixture` to clear between tests, NOT a try/except that swallows `LabelRegistryError`.

3. **Don't add tests outside the taxonomy without a 5.3 checkpoint review.** If you discover a test that needs to exist but doesn't have an ID in §3–§12, STOP and propose the test at the next checkpoint. Don't sneak it in.

4. **Don't make `FakeLLMJudge` smart.** The fake judge MUST be a pure lookup table. If you find yourself adding logic to `FakeLLMJudge` to handle new fixture variants, you're conflating fake-judge logic with gate logic. Add new entries to the lookup table instead.

5. **Don't run the full benchmark harness in PR-gate.** S-Q3 ratification (§7.9) is explicit: full 30-score is `nightly_only`. PR-gate uses `FakeBenchmarkOutputs` for harness LOGIC tests only.

6. **Don't shortcut the meta-test self-reference.** §13.3.4 self-referential bootstrap: the meta-test's own ID is in the allow-list. Don't comment it out "to fix the bootstrap order"—the order is handled by writing the meta-test LAST in checkpoint C10.

7. **Don't change the test ID schema.** If you need a new family, propose a new prefix to the test architect (Murat). Don't invent `MAC-T-NEW-FAMILY-01` ad hoc.

8. **Don't skip the negative tests.** The §11 cluster catches architectural drift. If a negative test fails, treat it as a "what boundary was crossed?" investigation, not a "fix the test" task.

9. **Don't bypass the section router.** Every gate evaluation must go through `GATE_SECTION_ROUTES`. Don't directly call `judge.score(full_document)` for a gate that should see only a section. The cycle controller test `MAC-T-CYCLE-SEC-01` will catch this.

10. **Don't use real LLMs in Tier 1 or Tier 2.** Live LLM calls are reserved for Tier 3 (nightly) and Tier 4 (release gate). If a Tier 1/2 test fails because `FakeLLMJudge` lookup is missing a fixture, ADD THE FIXTURE to the lookup table — don't fall back to a real call.

### §16.5B Test Authoring Walkthrough — One Example End-to-End

To illustrate the discipline expected at 5.3, here is the full implementation of one test (`MAC-T-GATE-R4-06`, the Req-F deterministic structural test) from spec to code:

**Spec (from §3.5.6):**
- Test ID: `MAC-T-GATE-R4-06`
- Purpose: The R4 judge payload sent to the reviewer carries `independent_steelman` AND `gap_assessment` fields, with `independent_steelman` BEFORE `gap_assessment` in serialized JSON.
- Anchor: `mac/architecture.md §7.1 Req-F` + `§12.2 item 9 deterministic sub-test`.
- Fulfillment: `keys = list(ReviewerCritique.__fields__.keys()); assert keys.index("independent_steelman") < keys.index("gap_assessment")`.
- Marker set: `critical`, `asymmetry_structural`, `static`, `no_waiver`.
- Allow-list entry: yes (as `MAC-T-ASYM-R-F-02` canonical alias).

**Implementation:**

```python
# tests/mac/gates/test_r4.py

import pytest
from praxis.kernel.mac.gates.r4 import R4Gate, ReviewerCritique
from praxis.kernel.mac.testing.fakes import FakeLLMJudge

@pytest.mark.critical
@pytest.mark.asymmetry_structural
@pytest.mark.static
@pytest.mark.no_waiver
def test_mac_t_gate_r4_06_req_f_deterministic_structural():
    """
    MAC-T-GATE-R4-06 (alias: MAC-T-ASYM-R-F-02)
    Req-F two-step independence — deterministic structural sub-test.

    Asserts that the R4 reviewer payload schema has:
      1. Both `independent_steelman` AND `gap_assessment` fields.
      2. `independent_steelman` appears BEFORE `gap_assessment` in field
         order (Pydantic preserves declaration order in __fields__).

    Anchor: mac/architecture.md §7.1 Req-F + §12.2 item 9 deterministic
    Allow-list entry: yes (carries no_waiver).
    """
    fields = ReviewerCritique.__fields__
    assert "independent_steelman" in fields, (
        "Req-F violation: ReviewerCritique missing independent_steelman field"
    )
    assert "gap_assessment" in fields, (
        "Req-F violation: ReviewerCritique missing gap_assessment field"
    )
    keys = list(fields.keys())
    idx_ind = keys.index("independent_steelman")
    idx_gap = keys.index("gap_assessment")
    assert idx_ind < idx_gap, (
        f"Req-F violation: field ordering wrong. "
        f"independent_steelman at {idx_ind}, gap_assessment at {idx_gap}. "
        f"Per §7.1, independent_steelman MUST precede gap_assessment so "
        f"the reviewer commits to its own steelman before reading the "
        f"producer's [STEELMAN]."
    )
```

**Allow-list entry (in `tests/static/runtime/test_no_waiver_inventory.py`):**

```python
NO_WAIVER_ALLOWLIST: frozenset[str] = frozenset({
    # ... other entries ...
    "tests/mac/gates/test_r4.py::test_mac_t_gate_r4_06_req_f_deterministic_structural",
    # alias canonical name for §13.3 tracking: MAC-T-ASYM-R-F-02
    # ... other entries ...
})
```

The walkthrough demonstrates: (1) test ID in docstring with cross-reference, (2) marker stack including `no_waiver`, (3) clear failure messages naming the architectural rule violated, (4) allow-list synchronization in the same PR.

### §16.6 5.2 → 5.3 Transition Contract

This strategy is the frozen input for 5.3. Changes to this strategy require a 5.2 re-ratification loop. Amelia is NOT authorized to:
- Rename test IDs.
- Add tests outside the taxonomy.
- Strip `no_waiver` from any test listed in §13.3.
- Weaken the coverage target below 90%.
- Add files to the `tests/static/runtime/` directory other than the allow-list meta-test.

Amelia IS authorized to:
- Choose concrete function signatures within the interface contracts of §14.3.
- Add additional fixture helper methods that do not change the public interface.
- Expand a test with additional assertions as long as the test ID's purpose is unchanged.
- Propose NEW tests via a 5.3 checkpoint review — but those tests do NOT go into `no_waiver` without a 5.5 alignment review.

---

## §17 Test ID Total & Final Accounting

Summarizing the test counts from §3 through §12:

| Section | Test family | Count |
|---|---|---|
| §3 | Gate-level (R1–R12 + catalog + properties) | 75 |
| §4 | 3-cycle iteration controller | 24 |
| §5 | Information asymmetry | 12 |
| §6 | Integration | 15 |
| §7 | Evaluation harness | 25 |
| §8 | Bootstrap loader | 12 |
| §9 | Observability | 13 |
| §10 | Adversarial | 11 |
| §11 | Negative | 10 |
| §12 | Live drift canary | 24 |
| §13.3 | Allow-list meta-test | 1 |
| **Total** | | **222 test IDs** |

**Total test ID count: 222** — exceeds Runtime's 204; consistent with Pipeline.md §5.2's "most intensive test design in the project" framing.

### §17.0A Test Pyramid by Test Tier

```
Tier 4 (release_gate)              ~5 tests
Tier 3 (nightly_only)             ~30 tests
Tier 2 (integration)              ~55 tests
Tier 1 (unit + property + contract) ~175 tests
                                  -----------
                                  ~265 tests
```

Total test ID count is 211 (sum of §3–§13.3 counts), but Tier counts include some duplicate accounting because some tests carry multiple tier markers (e.g., the live R4 reviewer is BOTH a `critical` test AND a `nightly_only` test).

### §17.1 `no_waiver` Discipline Final Count

- **10 MAC calibration-anchor and structural tests** `no_waiver` (Decision 1 — see §1.4 prose and §13.3.3 entries 4–13). Composition: 8 gate calibration anchor tests for R1/R2/R3/R4/R5/R7/R8/R11 (`MAC-T-GATE-R{N}-02`) + 2 structural calibration tests `MAC-T-GATE-R11-05` (Scenario Coverage property) and `MAC-T-GATE-R12-05` (direct contradiction detector).
- **2 MAC split deterministic carriers** `no_waiver` tests: `MAC-T-ASYM-R-F-02` (Req-F deterministic sub-test, §13.3.3 entry #14) + `MAC-T-ADV-P3-01` (Persona 3 deterministic sub-test, §13.3.3 entry #15).
- **1 MAC meta-test self-reference** `no_waiver`: `MAC-T-META-NO-WAIVER-INV-01` (§13.3.3 entry #16).
- **Total MAC `no_waiver`: 13.**
- **Total allow-list entries: 16** (13 MAC + 1 Runtime ratified entry #1 + 2 Runtime provisional PENDING AUDIT at 5.5 entries #2/#3). RATIFIED 2026-04-14 per §13.3.3.1 — the "14" in the v0.1 binding brief was an arithmetic slip; the structural boundary "`no_waiver` = deterministic invariants only" is preserved. **v0.3 corrigendum:** the v0.1 prose that pointed this count at `arch §12.2` was a miscitation — arch §12.2 actually enumerates SQ invariants and Req snapshots (per arch §B citation index), not MAC calibration tests. v0.3 uses self-contained ratified-allow-list references; see §1.7 v0.3 changelog DIV-3 subsection for full reconciliation.

### §17.2 Gate Checklist Row Verification

The §13.1 gate checklist has **16 rows** covering every Pipeline.md §5.2 sub-check plus the Decision 1–3 bake-ins and the 8 tension resolutions.

### §17.2A Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Allow-list `no_waiver` count (16 vs brief's 14) | RESOLVED 2026-04-14 | — | Ratified Option 1 (16 entries) per §13.3.3.1; no residual risk |
| R2 | Live LLM drift causes nightly drift canary to fail intermittently | High (model providers ship updates frequently) | Low (3-run promotion rule) | §12.4 promotion rule prevents flaky-blocker; manual review on persistent drift |
| R3 | `FakeBenchmarkOutputs` lookup table goes stale relative to actual gate scoring logic | Medium | Medium | §7.8.2 completeness test catches missing entries; rebuild table on every R{N} change |
| R4 | Postgres testcontainers slow down CI | Medium | Low | Session-scoped container fixture; savepoint rollback between tests |
| R5 | Hypothesis state machine takes too long in PR-gate | Low | Medium | `--hypothesis-deadline=5000ms` and `max_examples=200` for PR-gate; full property suite in nightly |
| R6 | Adversarial fixture rotation lapses (no new fixtures per release) | Medium | High (memorization risk) | `MAC-T-ADV-ROTATION-01` enforces ≥5 new per release as a release-gate check |
| R7 | Bootstrap loader's idempotency test passes locally but fails in shared CI | Low | Medium | Use isolated Postgres testcontainer per session; never share state across test runs |
| R8 | Coverage exclusion list expands silently | Medium | Medium | Snapshot test on `pyproject.toml [tool.coverage.run] omit` (add to §13.5 if not present at 5.3 ratification) |
| R9 | The 2 OTEL provisional tests get audit-rejected at 5.5 | Possible (depends on team-lead audit) | Low | They carry PENDING AUDIT comment; if rejected, they're stripped from allow-list and `no_waiver` removed in a 5.5 cleanup PR |
| R10 | A4 Andrey-in-the-loop scoring is delayed for a release | Possible (manual step) | Medium (release-gate blocker) | A4 is a release-gate test, not a PR-gate test; release waits if Andrey unavailable |

### §17.2B Non-Blocking Residual Questions (Deferred to 5.5 Alignment Review)

All questions in this subsection are explicitly **non-blocking** for Stage 5.2 ratification and deferred to 5.5 Alignment Review for stakeholder decision. None require action from Amelia at Stage 5.3.

1. **Allow-list count — RESOLVED 2026-04-14.** Ratified Option 1 (16 entries) per §13.3.3.1. Non-blocking (closed).
2. **Pattern macros in §3.1A — abstract enough?** The G-UNIT, G-CAL, G-ROUTE, G-DOMAIN, G-FORGE patterns are documentation-level; they don't change the test code. Non-blocking, deferred to 5.5 Alignment Review for convention-vs-code-abstraction decision.
3. **Tier 3 cost budget at §12.3 — needs concrete dollars?** Currently expressed as call counts (~60/night). Non-blocking, deferred to 5.5 Alignment Review for dollar-figure commitment vs defer to 5.3 actual model pricing.

### §17.3 Ratification State

This strategy is **RATIFIED v0.3 2026-04-14** at the Stage 5.2 → 5.3 transition. v0.3 is a fresh ratification replacing the v0.1 → v0.2 corrigendum stack — full-document drift reconciliation across DIV-1 (label drift), DIV-2 (hard-fail fabrication), DIV-3 (Decision 1 prose miscitation), DIV-4 (specialty test bodies), and DIV-5 (cross-section drift in §4 state machine, §6 §10.N off-by-one, §10.2/§10.3 adversarial). Q-1 allow-list function name renames applied with canonical IDs preserved. The 16-entry `no_waiver` allow-list, Decisions 1/2/3 structure, S-Q1–S-Q4 ratified answers, Option Y sidecar, fake fixture interface contracts, and asymmetry router are all preserved verbatim from v0.2/v0.1. Amelia (Stage 5.3) implements against v0.3 as the binding input. The 3 non-blocking residual questions in §17.2B are deferred to 5.5 Alignment Review. See §1.7 v0.3 changelog for full reconciliation history.

---

### §17.4 Stage 5.2 → 5.3 Spot-Check Worksheet

The team-lead spot-check at the 5.2 → 5.3 transition should verify the following items in order. Each item is mapped to its location in this strategy.

| # | Spot-check item | Location | Verification |
|---|---|---|---|
| 1 | File exists at `_bmad-output/implementation-artifacts/praxis/mac/test-strategy.md` | filesystem | `ls` |
| 2 | Length ≥ 3,500 lines | `wc -l` | run the command |
| 3 | 17 `## §N` sections | `grep -c '^## §'` | `17` |
| 4 | All 12 gates have at least 5 tests in §3 | §3.16 count summary | row sums |
| 5 | All 10 MAC `no_waiver` tests listed in §3.16.1 | §3.16.1 table | 10 rows |
| 6 | OQ-TS-9 meta-test spec at §13.3 | §13.3 | full implementation present |
| 7 | Allow-list has 16 entries (RATIFIED Option 1) | §13.3.3 table | 16 rows |
| 8 | 8 tensions appear as named subsections | §3.15, §4.5, §4.6, §8.4, §10.4, §11.2, §13.3, §13.5 | grep `Tension #` |
| 9 | S-Q1 baked at §8.4 | §8.4 | 4 idempotency tests present |
| 10 | S-Q2 baked at §9.3 | §9.3 | 4 violation counter tests present |
| 11 | S-Q3 baked at §7.9 | §7.9 | nightly split documented |
| 12 | S-Q4 baked at §7.10 | §7.10 | A4 release-gate test present |
| 13 | §13.1 gate checklist row count = 16 | §13.1 | row count |
| 14 | Test ID schema documented at §15 | §15 | `MAC-T-{section}-{seq}` defined |
| 15 | Coverage target ≥90% at §13.2 | §13.2 | floor stated |
| 16 | Coverage exclusion list at §13.5 | §13.5 | `LLMJudgeClient.call_live` listed |
| 17 | Fake fixture interfaces at §14.3 | §14.3 | 7 fixtures specified |
| 18 | Handoff plan to 5.3 at §16 | §16 | red-first order, 10 checkpoints |
| 19 | Risk register at §17.2A | §17.2A | risks enumerated |
| 20 | Allow-list count ratification landed (16 entries per §13.3.3.1) | §13.3.3.1 | ratified 2026-04-14 |

If any item fails, the spot-check returns to drafting; the strategy is NOT advanced to 5.3 ratification.

---

**END — mac/test-strategy.md v0.3 RATIFIED 2026-04-14**

*Authored by Murat (BMAD Test Architect, TEA), 2026-04-14, Stage 5.2 — v0.3 fresh ratification replacing v0.1/v0.2 corrigendum stack.*

### §17.5 Document Provenance

| Field | Value |
|---|---|
| Author | Murat (BMAD Test Architect, TEA) |
| Stage | 5.2 (test strategy) |
| Date | 2026-04-14 |
| Version | 0.3 RATIFIED 2026-04-14 (replaces v0.1 / v0.2 corrigendum stack via full-document drift reconciliation) |
| Inputs frozen at | mac/architecture.md v0.1 RATIFIED 2026-04-14 |
| Continuation of | runtime/test-strategy.md v0.3 (5,950 lines, 204 test IDs) |
| Next stage | 5.3 Amelia (test implementation) |
| Spot-check | team-lead at 5.2 → 5.3 transition |
| Final ratification | 5.5 Alignment Review |
| Version history | v0.1 (initial; label drift Amelia-detected) → v0.2 (corrigendum patch DIV-1/2/3/4 §3 reconciliation) → v0.3 (fresh ratification covering all 5 DIV classes + Q-1 allow-list rename + 3 §E architectural escalations resolved) |






