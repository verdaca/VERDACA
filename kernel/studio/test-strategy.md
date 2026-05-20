# Studio Test Strategy — Stage 6.2

**Version:** 0.1
**Status:** DRAFT v0.1 — pending team-lead spot-check and ratification
**Author:** Murat, Test Architect (BMAD TEA)
**Date:** 2026-04-16
**Binding Inputs:**
- `_bmad-output/implementation-artifacts/praxis/studio/architecture.md` v0.1 (RATIFIED 2026-04-16)
- `_bmad-output/implementation-artifacts/praxis/mac/quality-rubric.md` §6 (R1–R12)
- `_bmad-output/implementation-artifacts/praxis/mac/benchmark-questions.md` §2 + §5 + §6 + §7 + §8
- `_bmad-output/implementation-artifacts/praxis/mac/test-strategy.md` v0.3 (vocabulary + tier inheritance)
- `_bmad-output/planning-artifacts/Praxis/Pipeline.md` §6.2 (deliverable criteria)

**Stage 5 continuation:** This strategy inherits marker vocabulary, fixture patterns, test-ID conventions, and tier hierarchy from `mac/test-strategy.md` v0.3 (215 test IDs) and `runtime/test-strategy.md` v0.3 (204 test IDs). Studio tests are a NEW test family (`STUDIO-T-*` prefix), not extensions of MAC-T-*.

**Preload gating discipline:** This document was authored under the preload-first gating pattern — architecture.md v0.1 was fully absorbed + structured preload report produced + human alignment verified before drafting began. Zero mid-draft scope drift, per Stage 5.2 Murat precedent.

**Ratification target:** Stage 6.2 → Stage 6.3 (Amelia implements against this spec)

---

## §1 — Context

### §1.1 Purpose

This document defines the test strategy for Stage 6 — the Studio Workflow Template at `praxis/kernel/studio/`. Per Pipeline.md §6.2, this covers schema validation tests, benchmark regression tests, and output format tests.

Studio is **configuration over the MAC** (arch §1.1). The test surface is fundamentally different from MAC's: primarily YAML schema validation, Jinja2 template rendering, cost budget enforcement, A/B comparison harness logic, and output-format contract verification. There is minimal new Python beyond the schema parser, template-to-task-input invoker, and register-check utility.

### §1.2 What This Strategy Tests

1. **Schema validation** — `WorkflowTemplate` Pydantic model (arch §2)
2. **Template rendering** — Jinja2 output templates across 3 rendering modes × 3 output types (arch §4)
3. **Quality gate configuration** — 12-gate activation with R4/R5 elevated minimums (arch §5)
4. **A/B comparison harness** — blind evaluation, anonymization, scoring integration (arch §6)
5. **Benchmark regression** — 10 Qs × 2 modes, quality floor enforcement (arch §7, §8)
6. **Cost budget enforcement** — $10 deep / $2 quick ceilings, per-cycle allocation, degradation (arch §10)
7. **Observability** — Pi-Mono label emission, session-over-time metrics (arch §11)
8. **Register compliance** — ADR-11 muted operator-realism register-check (arch §4.10)
9. **Provenance mode correctness** — invisible-mode leak detection (arch §4.9)

### §1.3 What This Strategy Does NOT Test

- MAC internal logic (covered by mac/test-strategy.md v0.3)
- Pi-Mono cost-tracking internals (covered by pi-mono/test-strategy.md)
- Memory subsystem (covered by memory/test-strategy.md)
- Runtime agent spawning (covered by runtime/test-strategy.md)
- Jinja2 template engine internals (framework trust)
- YAML parser internals (framework trust)

### §1.4 Stage 5 Vocabulary Inherited

From `mac/test-strategy.md §1.3` and `runtime/pyproject.toml:29–40`:

| Marker | Meaning | Inherited as-is |
|---|---|---|
| `critical` | Failure blocks release; deterministic | yes |
| `integration` | Multi-component wire-up test | yes |
| `static` | Collection-time / grep-based structural test | yes |
| `wall_clock` | Real-time sensitive test | yes |

**Studio-specific new markers** (registered in `praxis/kernel/studio/pyproject.toml` at 6.3):

| New Marker | Meaning |
|---|---|
| `studio_schema` | Schema validation test (Pydantic `model_validate` + negative cases) |
| `studio_template` | Jinja2 template rendering test |
| `studio_benchmark` | Benchmark regression test (unit vs nightly — see §5) |
| `studio_ab_harness` | A/B comparison harness test |
| `studio_register` | Register-check compliance test |
| `studio_provenance` | Provenance-mode leak detection test |
| `studio_cost` | Cost budget enforcement test |
| `nightly_only` | Runs in nightly CI pipeline, NOT PR gate (inherited from MAC) |

All Studio tests live under `tests/studio/` in the Praxis monorepo, with subdirectories per section:

```
tests/studio/
├── schema/           # §3 — Schema validation
├── templates/        # §4 — Output format tests
├── gates/            # §5 — Quality gate configuration
├── harness/          # §6 — A/B comparison harness
├── benchmark/        # §7 — Benchmark regression
├── cost/             # §8 — Cost budget enforcement
├── observability/    # §9 — Pi-Mono label emission
├── register/         # §10 — Register-check compliance
├── provenance/       # §11 — Provenance-mode leak detection
└── integration/      # §12 — End-to-end Studio invocation
```

---

## §2 — Risk Register

### §2.1 FMEA Risk Assessment

| # | Risk | Probability | Impact | Score | Priority | Mitigation |
|---|---|---|---|---|---|---|
| R-S1 | Invalid YAML template reaches MAC, causing runtime crash | 2 | 3 | 6 | P0 | Schema validation at load time (arch §2.4); negative-case test battery |
| R-S2 | ADR-01 four-feature backbone missing from rendered output | 2 | 3 | 6 | P0 | Structural presence check per output (§4) |
| R-S3 | Invisible provenance mode leaks "praxis"/"studio" strings | 2 | 3 | 6 | P0 | Byte-level grep on rendered output (§11) |
| R-S4 | Cost budget exceeded without graceful degradation | 2 | 2 | 4 | P1 | Budget enforcement tests with Pi-Mono fake (§8) |
| R-S5 | Benchmark quality regression below R4 ≥ 4 / R5 ≥ 4 floor | 2 | 3 | 6 | P0 | 10-question regression suite with floor assertions (§7) |
| R-S6 | A/B harness anonymization leaks path labels to evaluator | 1 | 3 | 3 | P1 | Anonymization unit test + structural check (§6) |
| R-S7 | Register-check misses drift markers in output | 2 | 2 | 4 | P1 | Register-drift corpus test with known-bad examples (§10) |
| R-S8 | Rendering-mode / provenance-mode coupling broken | 2 | 2 | 4 | P1 | `resolved_provenance_mode()` property test (§3) |
| R-S9 | Quick mode quality floor too low — ships poor output | 2 | 2 | 4 | P1 | Quick-mode benchmark regression (OQ-S5 calibration at 6.4 time) |
| R-S10 | Template-to-TaskInput conversion drops fields | 1 | 2 | 2 | P2 | Round-trip conversion test (§12) |

### §2.2 Test Depth by Risk Score

| Risk Score | Test Depth |
|---|---|
| 6–9 (P0) | Comprehensive: unit + property + integration + regression |
| 4–5 (P1) | Standard: unit + negative + basic integration |
| 1–3 (P2) | Smoke: happy-path unit test |

---

## §3 — Schema Validation Tests

**Anchor:** arch §2 (WorkflowTemplate Pydantic model), arch §2.4 (load-time validation)

### §3.1 Positive Validation

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-SCHEMA-01` | `WorkflowTemplate.model_validate()` on `strategic_session.yaml` succeeds | `studio_schema, critical` | 1 |
| `STUDIO-T-SCHEMA-02` | `WorkflowTemplate.model_validate()` on `strategic_session_quick.yaml` succeeds | `studio_schema, critical` | 1 |
| `STUDIO-T-SCHEMA-03` | `resolved_provenance_mode()` returns correct inferred default for each `RenderingMode` value | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-04` | Explicit `provenance_mode` override takes precedence over inferred default | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-05` | `InputParamSpec` validates all 5 types (`string`, `int`, `float`, `bool`, `enum`) with valid defaults | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-06` | `OutputSpec.format` restricted to `Literal["markdown", "html"]` — no PDF/pptx at 6.1 MVP (ADR-08) | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-07` | `ShareableLinkSpec` defaults match ADR-10: `auth_gated=True`, `default_expiry_days=30`, `owner_revocable=True` | `studio_schema` | 1 |

### §3.2 Negative Validation

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-SCHEMA-NEG-01` | Missing required field (`name`) raises `ValidationError` with field-level message | `studio_schema, critical` | 1 |
| `STUDIO-T-SCHEMA-NEG-02` | Wrong type for `cost_budget_usd` (string instead of float) raises `ValidationError` | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-NEG-03` | Invalid `rendering_mode` enum value raises `ValidationError` | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-NEG-04` | Invalid `gate_id` (not R1–R12) in `quality_gates` raises `ValidationError` | `studio_schema, critical` | 1 |
| `STUDIO-T-SCHEMA-NEG-05` | `cost_budget_usd` ≤ 0 is rejected | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-NEG-06` | `timeout_seconds` ≤ 0 is rejected | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-NEG-07` | Circular `depends_on` references in `cycles` are rejected | `studio_schema, critical` | 1 |
| `STUDIO-T-SCHEMA-NEG-08` | `depends_on` referencing non-existent `output_label` is rejected | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-NEG-09` | `enum_values` required when `InputParamSpec.type == "enum"`, missing raises error | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-NEG-10` | Duplicate `gate_id` in `quality_gates` tuple is rejected | `studio_schema` | 1 |

### §3.3 Property-Based Validation

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-SCHEMA-PROP-01` | Hypothesis: for all valid `(RenderingMode, ProvenanceMode|None)` pairs, `resolved_provenance_mode()` returns a `ProvenanceMode` value consistent with `PROVENANCE_DEFAULTS` table | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-PROP-02` | Hypothesis: random valid `WorkflowTemplate` round-trips through `model_dump() → model_validate()` without data loss | `studio_schema` | 1 |
| `STUDIO-T-SCHEMA-PROP-03` | Hypothesis: `budget_pct` values across all cycles in a valid template sum to 100 | `studio_schema` | 1 |

**Total §3: 20 tests (7 positive + 10 negative + 3 property)**

---

## §4 — Output Format Tests

**Anchor:** arch §4 (Output Template Contracts), ADR-01 through ADR-11

### §4.1 ADR-01 Four-Feature Backbone Presence

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-TPL-BACKBONE-01` | Brief output contains all 4 mandatory sections: Trade-offs, Dissent, Scenarios, Scope-Limits | `studio_template, critical` | 1 |
| `STUDIO-T-TPL-BACKBONE-02` | Deck output contains all 4 mandatory sections | `studio_template, critical` | 1 |
| `STUDIO-T-TPL-BACKBONE-03` | Executive summary output contains all 4 mandatory sections | `studio_template, critical` | 1 |
| `STUDIO-T-TPL-BACKBONE-04` | All 3 rendering modes produce 4-section backbone for brief | `studio_template` | 1 |

### §4.2 ADR-02 Three Rendering Modes

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-TPL-RENDER-01` | `position_to_hold` brief uses conditional-position framing (keyword detection in output) | `studio_template` | 1 |
| `STUDIO-T-TPL-RENDER-02` | `decision_framework` brief uses factor-weighted framing | `studio_template` | 1 |
| `STUDIO-T-TPL-RENDER-03` | `firm_voice` brief uses consultant-density framing | `studio_template` | 1 |
| `STUDIO-T-TPL-RENDER-04` | All 3 rendering modes produce structurally distinct outputs from the same reasoning trace fixture | `studio_template, critical` | 1 |

### §4.3 ADR-03 Brief Length Band

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-TPL-LENGTH-01` | Deep-mode brief word count falls within 3,500–8,500 band | `studio_template, studio_benchmark` | 3 |
| `STUDIO-T-TPL-LENGTH-02` | Per-section word minimums met (Trade-offs ≥ 800, Dissent ≥ 600, Scenarios ≥ 500, Scope-limits ≥ 300) | `studio_template, studio_benchmark` | 3 |

### §4.4 ADR-04 Deck Format

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-TPL-DECK-01` | Deck slide count falls within 10–18 range (deep mode) | `studio_template, studio_benchmark` | 3 |
| `STUDIO-T-TPL-DECK-02` | Slide titles use statement-of-finding format, not category-label format (heuristic check) | `studio_template` | 3 |

### §4.5 ADR-05 Dissent Rendering

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-TPL-DISSENT-01` | Dissent section contains at least 1 competing frame with steelman | `studio_template, critical` | 1 |
| `STUDIO-T-TPL-DISSENT-02` | Each competing frame renders 4 required sub-fields: steelman, evidence, conditions, confidence | `studio_template` | 1 |
| `STUDIO-T-TPL-DISSENT-03` | Zero competing frames triggers re-run signal (not silent empty section) | `studio_template` | 1 |

### §4.6 ADR-06 Scenario Rendering

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-TPL-SCENARIO-01` | At least 2 named scenarios per output | `studio_template, critical` | 1 |
| `STUDIO-T-TPL-SCENARIO-02` | Each scenario renders 3 required sub-fields: trigger, invalidation, decision-rule | `studio_template` | 1 |
| `STUDIO-T-TPL-SCENARIO-03` | Decision-rule sub-field includes owner + date (COO fold-back check) | `studio_template` | 1 |

### §4.7 ADR-07 Scope-Limits Rendering

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-TPL-SCOPE-01` | Scope-limits section renders 3 sub-categories: data gaps, adjacent questions, invalidating assumptions | `studio_template, critical` | 1 |
| `STUDIO-T-TPL-SCOPE-02` | Each sub-category has ≥ 1 entry | `studio_template` | 1 |
| `STUDIO-T-TPL-SCOPE-03` | Zero-entry sub-category triggers retry signal | `studio_template` | 1 |

### §4.8 ADR-09 Provenance Mode Selection

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-TPL-PROV-01` | `flexible` mode renders dismissible footer with "Generated with Praxis" | `studio_template` | 1 |
| `STUDIO-T-TPL-PROV-02` | `inspectable` mode renders expandable "How this analysis was generated" section | `studio_template` | 1 |
| `STUDIO-T-TPL-PROV-03` | `invisible` mode renders no provenance content (see §11 for leak test) | `studio_template, studio_provenance` | 1 |

### §4.9 ADR-11 Register Contract

(see §10 for full register-check tests)

**Total §4: 24 tests**

---

## §5 — Quality Gate Configuration Tests

**Anchor:** arch §5 (Quality Gates), mac/quality-rubric.md §6

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-GATE-01` | Studio template activates all 12 gates (R1–R12) | `studio_schema, critical` | 1 |
| `STUDIO-T-GATE-02` | R4 `min_score` is 4 (elevated, per arch §5.2) | `studio_schema, critical` | 1 |
| `STUDIO-T-GATE-03` | R5 `min_score` is 4 (elevated, per arch §5.2) | `studio_schema, critical` | 1 |
| `STUDIO-T-GATE-04` | R4 `weight_override` is 2 (2× weight, per arch §5.2) | `studio_schema` | 1 |
| `STUDIO-T-GATE-05` | R5 `weight_override` is 2 (2× weight, per arch §5.2) | `studio_schema` | 1 |
| `STUDIO-T-GATE-06` | All non-R4/R5 gates have `min_score` = 3 and no `weight_override` | `studio_schema` | 1 |
| `STUDIO-T-GATE-07` | R13 is NOT present in `quality_gates` (deferred per arch §5.2 final paragraph) | `studio_schema` | 1 |
| `STUDIO-T-GATE-08` | Gate-to-ADR alignment table (arch §5.3): R1+R4+R5+R6+R9 collectively enforce ADR-01 | `studio_schema` | 1 |

**Total §5: 8 tests**

---

## §6 — A/B Comparison Harness Tests

**Anchor:** arch §6 (A/B Comparison Harness)

### §6.1 Harness Structure

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-AB-01` | Harness runs both paths (single-agent baseline + Studio) on a single benchmark question | `studio_ab_harness, integration` | 2 |
| `STUDIO-T-AB-02` | Enhanced single-agent baseline (structural prompt, no multi-agent) also runs | `studio_ab_harness, integration` | 2 |
| `STUDIO-T-AB-03` | Both outputs are scorable against R1–R12 (produce `GateScores` data structure) | `studio_ab_harness` | 1 |
| `STUDIO-T-AB-04` | Comparison report generates without error from scored pair | `studio_ab_harness` | 1 |

### §6.2 Blind Evaluation Integrity

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-AB-BLIND-01` | Anonymization strips "Studio"/"baseline"/"enhanced" labels before evaluation | `studio_ab_harness, critical` | 1 |
| `STUDIO-T-AB-BLIND-02` | Output order randomized per question (not always Studio-first) | `studio_ab_harness` | 1 |
| `STUDIO-T-AB-BLIND-03` | Evaluator input contains no path-identifying metadata | `studio_ab_harness` | 1 |

### §6.3 Metrics Capture

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-AB-METRIC-01` | Per-run metrics include: cost, wall-clock time, word count, composite score, per-gate scores | `studio_ab_harness` | 1 |
| `STUDIO-T-AB-METRIC-02` | Backbone completeness (4 × boolean) captured per run | `studio_ab_harness` | 1 |
| `STUDIO-T-AB-METRIC-03` | Register compliance (boolean) captured per run | `studio_ab_harness` | 1 |

### §6.4 Comparison Report Format

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-AB-REPORT-01` | Report contains: headline, per-question table, per-gate table, R5 dissent analysis, cost-quality section | `studio_ab_harness` | 1 |
| `STUDIO-T-AB-REPORT-02` | All 10 benchmark results reported (no cherry-picking — ADR-2 full disclosure) | `studio_ab_harness, studio_benchmark` | 3 |

**Total §6: 12 tests**

---

## §7 — Benchmark Regression Tests

**Anchor:** arch §7 (Benchmark Question Set, D-2), arch §8 (Evaluation Protocol), arch §12.2

### §7.1 Benchmark Harness Unit Tests (Tier 1, PR-gate)

These test the **scoring and reporting logic** using `FakeBenchmarkOutputs`, NOT real LLM output.

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-BENCH-SCORE-01` | Composite score formula: `sum(score × weight) / sum(weight) × 20 → 0–100` correct for known fixture | `studio_benchmark` | 1 |
| `STUDIO-T-BENCH-SCORE-02` | R4 and R5 weight multiplier (2×) applied correctly in composite calculation | `studio_benchmark` | 1 |
| `STUDIO-T-BENCH-SCORE-03` | Per-question quality floor: composite ≥ 60 assertion fires when score drops below 60 | `studio_benchmark` | 1 |
| `STUDIO-T-BENCH-SCORE-04` | Differentiator gate assertion: R4 ≥ 4 AND R5 ≥ 4 fires correctly | `studio_benchmark, critical` | 1 |
| `STUDIO-T-BENCH-SCORE-05` | Aggregate mean composite calculation across 10-question fixture set | `studio_benchmark` | 1 |

### §7.2 Benchmark Regression (Tier 3, Nightly — Real LLM)

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-BENCH-DEEP-01` | Deep mode: run all 10 benchmark Qs, all outputs contain ADR-01 four-feature backbone | `studio_benchmark, nightly_only` | 3 |
| `STUDIO-T-BENCH-DEEP-02` | Deep mode: composite score ≥ 60 per question | `studio_benchmark, nightly_only` | 3 |
| `STUDIO-T-BENCH-DEEP-03` | Deep mode: R4 ≥ 4 and R5 ≥ 4 per question | `studio_benchmark, nightly_only, critical` | 3 |
| `STUDIO-T-BENCH-DEEP-04` | Deep mode: at least 1 competing frame in dissent per output | `studio_benchmark, nightly_only` | 3 |
| `STUDIO-T-BENCH-DEEP-05` | Deep mode: at least 2 named scenarios with 3 sub-fields per output | `studio_benchmark, nightly_only` | 3 |
| `STUDIO-T-BENCH-DEEP-06` | Deep mode: scope-limits has ≥ 1 entry per sub-category per output | `studio_benchmark, nightly_only` | 3 |
| `STUDIO-T-BENCH-QUICK-01` | Quick mode: run all 10 benchmark Qs, all outputs contain ADR-01 four-feature backbone | `studio_benchmark, nightly_only` | 3 |
| `STUDIO-T-BENCH-QUICK-02` | Quick mode: composite score ≥ OQ-S5 floor (calibrated at 6.4 Quinn time; initial placeholder: ≥ 40) | `studio_benchmark, nightly_only` | 3 |
| `STUDIO-T-BENCH-QUICK-03` | Quick mode: at least 1 competing frame in dissent per output | `studio_benchmark, nightly_only` | 3 |

### §7.3 Spearman Correlation Tracking (Tier 4, Release — Deferred to Stage 7)

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-BENCH-A4-01` | A4 Spearman ρ ≥ 0.6 between human and LLM-as-judge scores | `studio_benchmark` | 4 |

**Note:** STUDIO-T-BENCH-A4-01 is defined here for completeness but is NOT expected to run until Stage 7 POV Harness ratifies A4 per Pipeline §5.6 conditional.

**Total §7: 15 tests (5 unit + 9 nightly + 1 release)**

---

## §8 — Cost Budget Enforcement Tests

**Anchor:** arch §10 (Cost Model)

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-COST-01` | Deep mode `strategic_session.yaml` has `cost_budget_usd` = 10.00 | `studio_cost, studio_schema` | 1 |
| `STUDIO-T-COST-02` | Quick mode `strategic_session_quick.yaml` has `cost_budget_usd` = 2.00 | `studio_cost, studio_schema` | 1 |
| `STUDIO-T-COST-03` | Per-cycle budget allocation sums to total budget (deep: 20+50+30 = 100%) | `studio_cost` | 1 |
| `STUDIO-T-COST-04` | Per-cycle budget allocation sums to total budget (quick: 40+60 = 100%) | `studio_cost` | 1 |
| `STUDIO-T-COST-05` | Budget exhaustion triggers graceful degradation (partial result with degradation marker, not crash) | `studio_cost, critical, integration` | 2 |
| `STUDIO-T-COST-06` | Per-cycle cost tracking aggregates correctly to session total via FakeCostTracker | `studio_cost, integration` | 2 |
| `STUDIO-T-COST-07` | Deep-mode session cost ≤ $10.00 across all 10 benchmark Qs | `studio_cost, nightly_only` | 3 |
| `STUDIO-T-COST-08` | Quick-mode session cost ≤ $2.00 across all 10 benchmark Qs | `studio_cost, nightly_only` | 3 |
| `STUDIO-T-COST-09` | Cost control lever: model-downgrade triggers when cost > 80% of budget before Cycle 3 (arch §10.4) | `studio_cost, integration` | 2 |

**Total §8: 9 tests**

---

## §9 — Observability Tests

**Anchor:** arch §11 (Observability — Pi-Mono Integration)

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-OBS-01` | Session emits `studio.session.cost_usd` label to Pi-Mono | `integration` | 2 |
| `STUDIO-T-OBS-02` | Session emits `studio.cycle.{name}.cost_usd` for each cycle | `integration` | 2 |
| `STUDIO-T-OBS-03` | Session emits `studio.session.composite_score` after evaluation | `integration` | 2 |
| `STUDIO-T-OBS-04` | Session emits `studio.gate.{R_id}.score` for each active gate (12 labels) | `integration` | 2 |
| `STUDIO-T-OBS-05` | `studio.session.rendering_mode` label matches the rendering mode used | `integration` | 2 |
| `STUDIO-T-OBS-06` | `studio.session.mode` label distinguishes "deep" vs "quick" | `integration` | 2 |
| `STUDIO-T-OBS-07` | `studio.session.backtrack_count` label emitted (may be 0) | `integration` | 2 |
| `STUDIO-T-OBS-08` | Label namespace uses `studio.*` prefix (not `mac.*` or raw names) — C-1 integration seam per arch §14.1 | `integration, static` | 1 |

**Total §9: 8 tests**

---

## §10 — Register-Check Tests

**Anchor:** arch §4.10 (ADR-11 Register Contract)

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-REG-01` | Register-check detects exclamation marks in analytical text | `studio_register` | 1 |
| `STUDIO-T-REG-02` | Register-check detects dramatic-stakes verbs (curated list from `register_guide.md`) | `studio_register` | 1 |
| `STUDIO-T-REG-03` | Register-check detects urgency-performing adverbs ("urgently", "immediately", "critical" in non-risk contexts) | `studio_register` | 1 |
| `STUDIO-T-REG-04` | Register-check detects condescending patterns | `studio_register` | 1 |
| `STUDIO-T-REG-05` | Register-check PASSES on a known-good fixture matching Mary §A.1 muted register | `studio_register, critical` | 1 |
| `STUDIO-T-REG-06` | Register-check runs on all 10 benchmark outputs (nightly, deep mode) and reports pass/fail per output | `studio_register, nightly_only` | 3 |

**Total §10: 6 tests**

---

## §11 — Provenance Leak Detection Tests

**Anchor:** arch §4.9 (ADR-09 Provenance Rendering)

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-PROV-LEAK-01` | Invisible mode: grep for `praxis` / `studio` / `Praxis` / `Studio` in rendered text returns 0 matches | `studio_provenance, critical` | 1 |
| `STUDIO-T-PROV-LEAK-02` | Invisible mode: grep for `praxis` / `studio` / `Praxis` / `Studio` in file metadata returns 0 matches | `studio_provenance, critical` | 1 |
| `STUDIO-T-PROV-LEAK-03` | Invisible mode: grep for `praxis` / `studio` / `Praxis` / `Studio` in HTML comments returns 0 matches | `studio_provenance, critical` | 1 |
| `STUDIO-T-PROV-LEAK-04` | Invisible mode: full byte scan — no occurrence of "praxis" or "studio" (case-insensitive) in any output byte | `studio_provenance, critical` | 1 |
| `STUDIO-T-PROV-LEAK-05` | Flexible mode: "Generated with Praxis" footer IS present | `studio_provenance` | 1 |
| `STUDIO-T-PROV-LEAK-06` | Inspectable mode: "How this analysis was generated" section IS present | `studio_provenance` | 1 |
| `STUDIO-T-PROV-LEAK-07` | Invisible-mode leak test on all 10 benchmark outputs (nightly, deep mode) | `studio_provenance, nightly_only` | 3 |

**Total §11: 7 tests**

---

## §12 — End-to-End Integration Tests

**Anchor:** arch §2.5 (Template → TaskInput), arch §3 (strategic_session.yaml)

| Test ID | Description | Marker | Tier |
|---|---|---|---|
| `STUDIO-T-INT-01` | `template_to_task_input()` converts `WorkflowTemplate` + user inputs into valid `TaskInput` | `integration` | 1 |
| `STUDIO-T-INT-02` | `TaskInput.workflow_template_id` format is `"studio/strategic_session/0.1.0"` | `integration` | 1 |
| `STUDIO-T-INT-03` | Full Studio pipeline: load YAML → validate → convert → FakeMAC → render brief → assert backbone | `integration, critical` | 2 |
| `STUDIO-T-INT-04` | Quick-mode pipeline: load quick YAML → validate → convert → FakeMAC → render brief → assert backbone | `integration` | 2 |
| `STUDIO-T-INT-05` | Deep-mode pipeline: all 3 cycles execute in order (wide_survey → deep_analysis → red_team_synthesis) | `integration` | 2 |
| `STUDIO-T-INT-06` | Quick-mode pipeline: `deep_analysis` cycle is skipped (`skip_in_quick_mode: true`) | `integration, critical` | 2 |
| `STUDIO-T-INT-07` | Rendering-mode propagates from template through MAC to output template selection | `integration` | 2 |

**Total §12: 7 tests**

---

## §13 — Tier Hierarchy & Execution Strategy

### §13.1 Tier Definitions (Inherited from MAC §2.2)

| Tier | Scope | CI Stage | Speed |
|---|---|---|---|
| **Tier 1** | Deterministic unit / property / contract. No LLM. Fake fixtures. | PR gate | < 30s total |
| **Tier 2** | Integration. FakeMAC + FakeCostTracker. No live LLM. | PR gate | < 3 min total |
| **Tier 3** | Live-LLM benchmark regression. Real Studio invocations. | Nightly only | < 60 min total |
| **Tier 4** | Release gate. A4 human corroboration. | Release candidate | Manual trigger |

### §13.2 Test Pyramid

```
                        ╭──────────────────────────╮
                        │  Tier 4 release           │  ~1 test (A4 Spearman)
                        ╰──────────────────────────╯
                    ╭──────────────────────────────────╮
                    │  Tier 3 nightly benchmark         │  ~18 tests
                    │  (nightly_only)                   │
                    ╰──────────────────────────────────╯
                ╭──────────────────────────────────────────╮
                │  Tier 2 integration (PR gate)             │  ~17 tests
                ╰──────────────────────────────────────────╯
            ╭──────────────────────────────────────────────────╮
            │  Tier 1 unit + property + contract (PR gate)      │  ~80 tests
            ╰──────────────────────────────────────────────────╯
```

Ratio: ~69% Tier 1, ~15% Tier 2, ~15% Tier 3, ~1% Tier 4. Lighter Tier 2 share than MAC because Studio has fewer integration seams (configuration-over-MAC, not a new subsystem).

### §13.3 Coverage Target

**Pipeline §6.4 gate: ≥ 80%.** Studio has less production code to cover than MAC (estimated ~400–600 LoC Python glue + schema parser + register-check utility). YAML templates and Jinja2 templates are tested via structural assertions, not line-coverage.

**Exclusion from coverage:** `LLMJudgeClient.call_live()` path excluded via `# pragma: no cover` (same precedent as MAC §13.5). A/B harness live-LLM path excluded similarly.

---

## §14 — Fixture Architecture

### §14.1 Fake Dependencies

| Fake | Purpose | Anchor |
|---|---|---|
| `FakeMAC` | Returns deterministic `MACResult` from a fixture lookup table keyed by `TaskInput.raw_prompt` | MAC test-strategy §14.3 pattern |
| `FakeCostTracker` | Records label emissions without touching Pi-Mono; assertable via `tracker.emitted_labels()` | Pi-Mono test-strategy fixture pattern |
| `FakeLLMJudge` | Returns deterministic R1–R12 scores from fixture lookup table | MAC test-strategy §14.3.1 |
| `FakeBenchmarkOutputs` | Pre-rendered brief/deck/summary text for all 10 benchmark Qs × 3 rendering modes × 2 modes | New — Studio-specific |
| `FakeRegisterChecker` | Configurable pass/fail for register-drift markers | New — Studio-specific |

### §14.2 Fixture Data Files

```
tests/studio/fixtures/
├── strategic_session_deep.yaml           # Copy of production YAML for Tier 1 load tests
├── strategic_session_quick.yaml          # Copy of production quick-mode YAML
├── invalid_templates/                    # §3.2 negative-case YAML files
│   ├── missing_name.yaml
│   ├── circular_depends_on.yaml
│   ├── invalid_gate_id.yaml
│   ├── negative_budget.yaml
│   └── ...
├── reasoning_traces/                     # Deterministic reasoning trace fixtures
│   ├── q1_position_to_hold.json
│   ├── q1_decision_framework.json
│   ├── q1_firm_voice.json
│   └── ...
├── rendered_outputs/                     # Pre-rendered outputs for format tests
│   ├── brief_position_to_hold.md
│   ├── deck_decision_framework.html
│   └── ...
├── register_corpus/                      # §10 register-check test corpus
│   ├── good_muted_register.md            # Known-pass
│   ├── bad_exclamation_marks.md          # Known-fail
│   ├── bad_dramatic_verbs.md             # Known-fail
│   └── bad_urgency_adverbs.md            # Known-fail
└── benchmark_scores/                     # §7 scoring fixture lookup tables
    ├── deep_mode_scores.json
    └── quick_mode_scores.json
```

### §14.3 Reasoning Trace Fixture Contract

For Tier 1 template tests, a `ReasoningTrace` fixture provides the structured data that Jinja2 templates render. This fixture is deterministic — no LLM involved. Shape:

```python
@dataclass(frozen=True)
class ReasoningTraceFixture:
    trade_offs: list[TradeOff]         # ≥ 1 entry
    dissent_frames: list[DissentFrame]  # ≥ 1 entry with 4 sub-fields
    scenarios: list[Scenario]           # ≥ 2 entries with 3 sub-fields each
    scope_limits: ScopeLimits           # 3 sub-categories, each ≥ 1 entry
    recommendations: list[Recommendation]
    rendering_mode: RenderingMode
    provenance_mode: ProvenanceMode
```

Fixtures are hand-authored to exercise boundary conditions:
- **Minimal fixture:** exactly 1 dissent frame, 2 scenarios, 1 entry per scope-limits sub-category
- **Rich fixture:** 4 dissent frames, 5 scenarios, multiple entries per sub-category
- **Edge fixture:** unicode characters, long text (near 8,500-word ceiling), empty optional fields

---

## §15 — Open Questions

| # | Question | Resolution Path | Blocking? |
|---|---|---|---|
| OQ-TS-S1 | Quick-mode quality floor (OQ-S5) — what composite threshold? | Quinn 6.4 calibration against benchmark set | No (6.2), yes (6.4) |
| OQ-TS-S2 | Per-section word minimums in §4.4 — empirical values or arch defaults? | Quinn 6.4 calibration (arch §4.4 provides defaults; may adjust at 6.4 time) | No (6.2) |
| OQ-TS-S3 | Register-check drift marker curated list (OQ-S3) — what triggers fail? | Amelia 6.3 drafts initial list; Quinn 6.4 validates | No (6.2) |
| OQ-TS-S4 | Should `STUDIO-T-PROV-LEAK-04` (full byte scan) include base64-encoded metadata? | Amelia 6.3 implementation of metadata-strip pass determines scope | No (6.2) |

---

## §16 — Test Count Summary

| Section | Family | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Total |
|---|---|---|---|---|---|---|
| §3 | Schema validation | 20 | — | — | — | 20 |
| §4 | Output format | 20 | — | 4 | — | 24 |
| §5 | Quality gates | 8 | — | — | — | 8 |
| §6 | A/B harness | 9 | 2 | 1 | — | 12 |
| §7 | Benchmark regression | 5 | — | 9 | 1 | 15 |
| §8 | Cost budget | 4 | 3 | 2 | — | 9 |
| §9 | Observability | 1 | 7 | — | — | 8 |
| §10 | Register-check | 5 | — | 1 | — | 6 |
| §11 | Provenance leak | 6 | — | 1 | — | 7 |
| §12 | E2E integration | 2 | 5 | — | — | 7 |
| **Total** | | **80** | **17** | **18** | **1** | **116** |

**116 test IDs** — appropriately lighter than MAC's 215 (Studio is configuration-over-MAC, not a new subsystem). Every test traces to an architecture section via anchor citations.

---

## §17 — Handoff Contract

### §17.1 For Amelia (6.3)

- Implement all production code in `praxis/kernel/studio/`
- Register Studio markers in `praxis/kernel/studio/pyproject.toml`
- Create fixture files per §14.2 layout
- Implement `register_check.j2` macro per arch §4.10 + the drift-marker curated list (OQ-TS-S3)
- Implement invisible-mode metadata-strip pass per arch §4.9 (ADR-09 §D fold-back)
- Test directory structure per §1.4 (`tests/studio/` with subdirectories)

### §17.2 For Quinn (6.4)

- Coverage gate: ≥ 80% aggregate (§13.3)
- Benchmark regression: all 10 Qs pass in deep and quick modes (§7.2)
- Calibrate OQ-TS-S1 (quick-mode quality floor) and OQ-TS-S2 (per-section word minimums) against benchmark outputs
- Validate register-check drift-marker list (OQ-TS-S3) against nightly outputs

### §17.3 For Alignment Review (6.5)

- Verify Studio test strategy covers all arch §12 testability notes
- Verify no Studio test extends MAC behavior (Studio-over-MAC boundary respected)
- Cross-check provenance-leak test coverage against arch §4.9 invisible-mode checklist

---

## §E — Session-Close Audit

### §E.1 — Deliverable Checklist (Pipeline §6.2 checkboxes)

| # | Checkbox | Status |
|---|---|---|
| 1 | Test strategy at `studio/test-strategy.md` | This document |
| 2 | Benchmark regression tests designed | §7 (15 tests: 5 unit + 9 nightly + 1 release) |
| 3 | Output format tests designed | §4 (24 tests across ADR-01 through ADR-11) + §3 ADR-08/ADR-10 schema coverage |

### §E.2 — Inheritance Verification

- **Marker vocabulary:** inherited `critical`, `integration`, `static`, `wall_clock`, `nightly_only` from MAC/Runtime. 7 new `studio_*` markers added. No marker renamed or repurposed.
- **Tier hierarchy:** Tier 1/2/3/4 definitions inherited verbatim from MAC §2.2.
- **Fixture pattern:** `FakeMAC` / `FakeLLMJudge` / `FakeCostTracker` patterns inherited from MAC §14.3.
- **Test-ID convention:** `STUDIO-T-*` prefix follows `MAC-T-*` / `RT-T-*` convention.
- **`no_waiver` discipline:** zero `no_waiver` markers added. Studio has no deterministic structural invariants that rise to the `no_waiver` level — schema validation is `critical` but waivable in extremis (the YAML template can be updated). Per ratified discipline, no `no_waiver` markers on agent initiative.

### §E.3 — Memory + Pipeline Discipline

- **No memory writes performed.** Proposed memory update (if any) deferred to team-lead disposition.
- **No Pipeline.md marks applied.** Pipeline §6.2 checkboxes to be updated by team-lead ratification flow.

### §E.4 — Risk Summary

Highest risks: R-S1 (schema validation bypass, P0), R-S2 (backbone omission, P0), R-S3 (provenance leak, P0), R-S5 (quality regression, P0). All have dedicated test batteries in §3, §4, §11, §7 respectively. No unmitigated P0 risks.

---
