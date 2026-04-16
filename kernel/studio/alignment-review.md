# Praxis Stage 6.5 — Studio Alignment Review

**Author:** Alignment Review agent (Opus 4.6 [1M], high thinking)
**Date:** 2026-04-16
**Binding inputs:** `studio/architecture.md` v0.1 (RATIFIED 2026-04-16), `studio/code-review.md` (Cleo 6.3.5), Quinn 6.4 QA report (97/97 PR-gate, 95.79% coverage), `pi-mono/pi-mono-cost-tracker-architecture.md`, `compression/architecture.md`, `memory/architecture.md`, `runtime/architecture.md`, `mac/architecture.md` v0.3+, `mac/alignment-review.md` (Stage 5.5), `project_praxis_stage6.md`, `project_praxis_stage5_5.md`
**Frozen artifacts touched:** NONE

---

## §1. Executive Summary

**Gate recommendation: GO — advance to 6.6 Pre-Sales Checkpoint.**

| Finding class | Count | Severity |
|---|---|---|
| Cross-stage API contract mismatch | 1 | MEDIUM — architecture text claims Pi-Mono integration, implementation uses a decoupled observability protocol; behaviorally correct but naming-confusing |
| Architecture-vs-implementation YAML divergence | 1 | LOW — arch §3.1 uses `${inputs.rendering_mode}` pseudo-interpolation, actual YAML hardcodes `position_to_hold` default; resolved at design level |
| Missing template mode coverage in YAML | 1 | LOW — both YAML files hardcode `position_to_hold` rendering mode in outputs; `decision_framework` and `firm_voice` templates exist but are not exercised by the shipped YAML |
| C-1..C-5 inheritance from Stage 5.5 | 5 | All correctly documented in §14; none Studio-blocking |
| New Stage 7 debt items | 2 | Studio-specific additions to the debt ledger |
| Positive alignment signals | 8 | Correct MAC usage, gate anchoring, ADR compliance, tokonomics firewall, register enforcement, test coverage |

**What this means for 6.6 advancement:**

6.6 Pre-Sales Checkpoint is a live demo of Studio running a strategic question end-to-end. The 1 MEDIUM finding (CostTrackerProtocol naming) does not affect the demo — Studio's `FakeCostTracker` test double satisfies the protocol, and the real Pi-Mono integration is MAC-internal. The 2 LOW findings are design-level awareness items. No frozen artifact was modified. All 23 ratified Stage 5 decisions remain honored.

---

## §2. USR Reading Log

Sequential USR read per Pipeline §4.6:

| Step | Artifact | Focus | Status |
|---|---|---|---|
| 1 | `pi-mono/pi-mono-cost-tracker-architecture.md` | `CostTracker.track_cost` signature, `LLMRequest`/`LLMResponse` contracts | ✓ |
| 2 | `compression/architecture.md` | Facade contract, Forge `reasoning_preserved` flag | ✓ |
| 3 | `memory/architecture.md` | Memory Protocol facade, named MAC contract §6.6 | ✓ |
| 4 | `runtime/architecture.md` | `AgentSpawner`, `ResourceBudget`, MCP pin | ✓ |
| 5 | `mac/architecture.md` v0.3+ | §5 Quality Gate Engine (R1–R12), §6 Co-evaluation (SQ-4/SQ-7), §10 Integration Contracts, §8 Learning Loop | ✓ |
| 6 | `studio/architecture.md` v0.1 | Full read (977 lines, 14 sections + §E) | ✓ |
| 7 | `studio/src/praxis/kernel/studio/*.py` (7 files) | Implementation verification against arch contracts | ✓ |
| 8 | `studio/templates/**/*.j2` (17 files) | ADR-01 backbone, ADR-02 rendering modes, ADR-05/06/07/09/11 partials | ✓ |
| 9 | `studio/strategic_session.yaml` + `strategic_session_quick.yaml` | YAML-vs-arch consistency, gate specs, cycle structure | ✓ |
| 10 | `studio/code-review.md` + Quinn 6.4 ratification in Pipeline.md | Closed-item boundary, Stage 7 debt state | ✓ |
| 11 | `mac/alignment-review.md` (Stage 5.5) | C-1..C-5 inherited drifts, OTEL dispositions, 10-item debt ledger | ✓ |

---

## §3. Pi-Mono Alignment (Stage 1 ↔ Studio)

### Finding S6-A1: CostTrackerProtocol signature mismatch — MEDIUM

**Pi-Mono contract** (pi-mono/tracker.py:89–92):
```python
async def track_cost(self, request: LLMRequest, response: LLMResponse) -> CostRecord
```

**Studio protocol** (studio/invoker.py:77–81):
```python
class CostTrackerProtocol(Protocol):
    def track_cost(self, label: str, amount_usd: float) -> None: ...
```

**Architecture claim** (studio/architecture.md §11.1): "Every Studio session emits the following via Pi-Mono's `CostTracker.track_cost`"

**Reality:** Studio's `CostTrackerProtocol` is a simplified observability/metrics facade. It takes a label string and a float amount — incompatible with Pi-Mono's actual `track_cost(LLMRequest, LLMResponse) -> CostRecord` signature. Studio uses this protocol for observability metrics emission (session cost, gate scores, backtrack count, duration), NOT for actual LLM cost tracking.

The actual LLM cost tracking happens inside the MAC when it calls Pi-Mono's real API via `MacCostHook.emit_cycle_cost()` (mac/architecture.md §10.1). Studio never directly invokes Pi-Mono's hot path — it receives the cost total from the MAC's `DeliberationResult.cost_usd` attribute (invoker.py:188).

**Impact on 6.6:** None. Studio's `FakeCostTracker` satisfies the simplified protocol in tests. The real Pi-Mono integration is MAC-internal and already verified at Stage 5.5.

**Reconciliation for Stage 7:** Rename Studio's protocol to `ObservabilityProtocol` or `MetricsSinkProtocol` to avoid confusion with Pi-Mono's `CostTracker`. Update architecture §11.1 to say "emits via a metrics sink adapter" rather than "via Pi-Mono's CostTracker.track_cost."

**Severity:** MEDIUM — naming confusion only; no behavioral impact.

---

## §4. Compression Alignment (Stage 2 ↔ Studio)

**No direct integration.** Studio does not import or reference any Compression module. The MAC handles Forge/TONL/Caveman internally per mac/architecture.md §5.6 (SQ-7 Forge fallback). Studio inherits the Forge-degraded R7 penalty indirectly through the MAC's gate scores.

**Verification:** `grep -r "compression\|tonl\|forge\|caveman" studio/src/` returns zero hits outside architecture documentation and `__pycache__`.

**Status:** CLEAN.

---

## §5. Memory Alignment (Stage 3 ↔ Studio)

**No direct integration.** Studio does not import or reference any Memory module. The MAC manages Memory via `MacMemoryAdapter` (mac/architecture.md §10.2). Studio's `StudioSession` receives retrieval context and publish results through the MAC's `DeliberationResult` — it never touches the Memory facade directly.

**C-4 (Memory promotion semantic mismatch) propagation:** Studio architecture §14.1 correctly documents C-4 as "invisible to Studio but becomes visible at Stage 7 when promotion logic is exercised." This is accurate — Studio uses Memory via MAC's §8 learning loop; the tentative→confirmed promotion path is not exercised during the 6.6 demo (single-session benchmark, no cross-session reuse).

**Status:** CLEAN.

---

## §6. Runtime Alignment (Stage 4 ↔ Studio)

**No direct integration.** Studio does not import or reference Runtime's `AgentSpawner`, `ResourceBudget`, or MCP tools. The MAC orchestrates agent spawning internally. Studio's `WorkflowTemplate.cost_budget_usd` and `timeout_seconds` fields are passed to the MAC, which translates them into Runtime's `ResourceBudget` constraints (mac/architecture.md §5.7).

**Verification:** `grep -r "runtime\|spawner\|resource_budget\|mcp" studio/src/` returns zero hits outside architecture documentation.

**Status:** CLEAN.

---

## §7. MAC Alignment (Stage 5 ↔ Studio) — Primary Check

### §7.1 TaskInput Handoff

Studio's `TaskInput` stub (invoker.py:38–58) is a Pydantic `BaseModel` with fields: `raw_prompt`, `customer_context`, `workflow_template_id`, `explicit_question`. This follows DQ-1 Option B (USR isolation — no compile-time dependency on `praxis-mac`).

**Cross-check against MAC §3.2:** MAC's `TaskInput` accepts `raw_prompt` (str) and `customer_context` (dict). Studio constructs both correctly in `template_to_task_input()` (invoker.py:90–127). The `workflow_template_id` field (`"{product}/{name}/{version}"`) is a Studio addition that MAC ignores (Pydantic's frozen model with extra fields is forward-compatible).

**Status:** ALIGNED.

### §7.2 Quality Gate Configuration

Studio YAML activates all 12 gates R1–R12 (strategic_session.yaml:111–137). R4 and R5 are elevated to `min_score: 4` with `weight_override: 2`, matching architecture §5.2.

**Cross-check against MAC §6.1:** MAC implements exactly 12 gate evaluators R1–R12 in `praxis/kernel/mac/gates/r1.py` through `r12.py`. R13 is deferred per SQ-3. Studio correctly excludes R13 from its gate list.

**Gate-to-ADR alignment (arch §5.3):** Verified — ADR-01 backbone maps to R1+R4+R5+R6+R9, ADR-05 dissent maps to R5 (min 4, 2× weight), ADR-06 scenarios maps to R3+R6, ADR-07 scope-limits maps to R9.

**Status:** ALIGNED.

### §7.3 Co-evaluation and Forge Degradation (SQ-4 / SQ-7)

Studio does not implement its own gate evaluation — it delegates entirely to the MAC's Quality Gate Engine. The MAC handles SQ-4 (R8 capped by R7+1) and SQ-7 (Forge degradation R7 penalty applied last) internally. Studio receives the `gate_scores` dict with effective (post-cap, post-penalty) values.

**Studio's `gate_scores` extraction** (invoker.py:190–193):
```python
gate_scores: dict[str, int] = {
    gid: (gs.effective_score if hasattr(gs, "effective_score") else int(gs))
    for gid, gs in (getattr(result, "gate_scores", {}) or {}).items()
}
```

This correctly reads `effective_score` (the post-cap value), not `raw_score`. The `hasattr` guard and `int()` fallback handle both production MAC (which returns gate result objects with `.effective_score`) and test doubles (which may return plain ints).

**Status:** ALIGNED.

### §7.4 Information Asymmetry

Studio's YAML sets `asymmetry: true` on the `red_team_synthesis` cycle (strategic_session.yaml:92). This maps to MAC's information-asymmetry contract (mac/architecture.md §4.5) — the red team agent does NOT see prior cycle reasoning traces. The `depends_on: []` on the red_team role (line 99) reinforces this: no explicit dependency on deep_analysis outputs.

**Status:** ALIGNED.

### §7.5 Budget Enforcement

Studio's `cost_budget_usd: 10.00` (deep) / `2.00` (quick) flows through MAC's `ResourceBudget` mechanism. MAC §5.7 defines `DEFAULT_MAC_BUDGET` with `max_tokens=400_000`, but the Studio-provided budget overrides via the `cost_budget_usd` field.

Pi-Mono enforces the ceiling — "no agent call proceeds after the ceiling is hit" (arch §10.4). Studio's graceful degradation path (invoker.py:183–186) catches budget-exceeded exceptions and returns a `DEGRADED` partial result.

**Status:** ALIGNED.

### §7.6 Benchmark Question Set (D-2)

Studio reuses the Stage 5 benchmark set from `mac/benchmark-questions.md` per D-2 disposition (arch §7). No second set invented.

**Status:** ALIGNED.

---

## §8. ADR Compliance Verification

| ADR | Arch Section | Implementation | Status |
|---|---|---|---|
| ADR-01 (four-feature backbone) | §4.1 | `_base.j2` renders 4 mandatory blocks in order; `models.py` `ReasoningTrace` carries all 4 | ✓ |
| ADR-02 (three rendering modes) | §4.2 | `schema.py` `RenderingMode` enum with 3 values; 3 template families present | ✓ |
| ADR-03 (brief length band) | §4.4 | 8–20 page target documented; per-section minimums in arch | ✓ |
| ADR-04 (deck format) | §4.5 | 10–18 slides; `deck.html.j2` present for all 3 modes | ✓ |
| ADR-05 (dissent) | §4.6 | `dissent.j2` renders 4 sub-fields per frame; R5 min=4 weight=2 | ✓ |
| ADR-06 (scenarios) | §4.7 | `scenario.j2` renders 3 sub-fields; min 2 scenarios enforced | ✓ |
| ADR-07 (scope-limits) | §4.8 | `scope_limits.j2` renders 3 sub-categories; retry signal on empty | ✓ |
| ADR-08 (export formats) | §1.2 | MVP = markdown + html only; PDF/pptx deferred to Stage 7 (D-4) | ✓ |
| ADR-09 (provenance) | §4.9 | 3 provenance partials; `PROVENANCE_DEFAULTS` coupling; invisible-mode strip in `renderer.py` | ✓ |
| ADR-10 (shareable links) | §2.2 | `ShareableLinkSpec` with auth_gated=True, 30-day expiry, revocable | ✓ |
| ADR-11 (register) | §4.10 | `register_check.py` with 4 drift-marker categories; `register_guide.md` present | ✓ |

**Status:** All 11 ADRs fully addressed.

---

## §9. Tokonomics Firewall Verification

**Architecture §A.0:** Inherited all three upstream artifacts' load-bearing constraints. Producer-vs-customer boundary correctly delineated — MAC component names (R1–R12, PhaseDAG, etc.) appear in architecture docs and Python code but NOT in Jinja2 templates.

**Template scan:** Read all 17 `.j2` template files. Zero instances of: `multi-agent`, `MAC`, `Pi-Mono`, `Forge`, `Atelier`, `Beads`, `Mem0`, `Caveman`, `RTK`, `TONL`, `quality gate`, `R1`–`R12`, `information asymmetry`, `deliberation`.

The `_base.j2` comment block (line 4) says "Producer-facing vocabulary does NOT appear in this file per §A.0 firewall" — correctly self-documenting.

**Status:** FIREWALL INTACT.

---

## §10. Stage 5.6 Headline Caveat Verification

**Caveat text:** "(internal scoring; A4 deferred)"

**Studio architecture §14.2 DL-3:** Correctly carries the caveat. No +47% / +21% / 10-of-10 / 25.2 / 13.7 numbers appear anywhere in Studio artifacts.

**A/B harness headline** (harness.py:284): `generate_report()` appends `"(internal scoring; A4 deferred)"` to every comparison report headline. This is correct — any Studio-generated comparison report automatically carries the caveat.

**Status:** CAVEAT PRESERVED.

---

## §11. Cross-Stage Seams (C-1..C-5 from Stage 5.5)

| Drift | Studio §14.1 Documentation | Independent Verification | Status |
|---|---|---|---|
| C-1 (Pi-Mono label namespace) | "Studio inherits Stage 4 namespace; §11 metrics use `studio.*` prefix" | Confirmed: `invoker.py` emits `studio.*` labels; no `pi_mono.*` or `mac:` prefix confusion | ✓ |
| C-2 (Memory TaskSignature hashing) | "Studio invokes MAC which handles the mapping; no Studio-level concern" | Confirmed: Studio never constructs `TaskSignature` directly | ✓ |
| C-3 (Compression TONL passthrough) | "Studio does not directly invoke compression; MAC handles via §10.4 adapter" | Confirmed: zero compression imports in Studio | ✓ |
| C-4 (Memory promotion semantic mismatch) | "Invisible to Studio but becomes visible at Stage 7" | Confirmed: single-session benchmark at 6.6 does not exercise promotion | ✓ |
| C-5 (AuditBuffer drain coordination) | "Resolved; no Studio concern" | Confirmed: closed at Stage 4.7 | ✓ |

**Status:** All 5 correctly documented and independently verified.

---

## §12. Architecture-vs-Implementation Divergences

### Finding S6-A2: YAML output paths hardcode `position_to_hold` — LOW

**Architecture §3.1** uses `rendering_mode: "${inputs.rendering_mode}"` pseudo-interpolation and `template_path: "templates/brief.md.j2"` with implied mode substitution.

**Actual YAML** (strategic_session.yaml:37,141–148): `rendering_mode: "position_to_hold"` hardcoded; output paths are `"position_to_hold/brief.md.j2"`, `"position_to_hold/deck.html.j2"`, `"position_to_hold/executive_summary.md.j2"`.

**Impact:** The YAML is a static template validated by Pydantic at load time. The `${inputs.rendering_mode}` interpolation in the architecture is design pseudocode — no YAML preprocessor exists in the implementation. For the 6.6 demo, the `position_to_hold` default is fine (founder segment, 50% weighting).

**For production (Stage 7):** The invoker or a YAML preprocessor must resolve `rendering_mode` from user inputs and select the correct template family. Currently all outputs render in `position_to_hold` mode regardless of the user's `rendering_mode` input parameter.

**Severity:** LOW for 6.6 demo; Stage 7 debt item.

### Finding S6-A3: `decision_framework` and `firm_voice` templates not exercised by shipped YAML — LOW

Both `strategic_session.yaml` and `strategic_session_quick.yaml` hardcode `position_to_hold` output paths. The `decision_framework/` and `firm_voice/` template families (6 templates total) exist and were tested by Quinn 6.4 (backbone tests STUDIO-T-TPL-BACKBONE-01..04 cover all 4 families), but no YAML configuration exercises them at runtime.

**Impact on 6.6:** None — demo uses `position_to_hold` mode per founder segment focus.

**Severity:** LOW. Stage 7 must add mode-routing logic.

---

## §13. Positive Alignment Signals

1. **DQ-1 Option B isolation pattern** correctly applied — Studio has no compile-time dependency on `praxis-mac`, `praxis-runtime`, `praxis-memory`, `praxis-compression`, or `praxis-pi-mono`. All cross-package interactions are protocol-based stubs.

2. **Quality gate anchoring (D-3)** correctly implemented — Studio anchors on MAC's R1–R12 rubric, not its own ad-hoc gates. The mapping from prompt-level gates to R-gates (arch §5.1) is documented and verified.

3. **ADR-01 four-feature backbone** is structurally enforced in `_base.j2` and verified by Quinn's STUDIO-T-TPL-BACKBONE-01..04 tests.

4. **R4/R5 elevation** (min_score=4, weight=2) correctly implements Studio's core differentiator promise — steelman completeness and dissent preservation are the highest-weighted gates.

5. **Invisible-mode provenance strip** (`renderer.py:102–126`) correctly removes YAML frontmatter, HTML comments, HTML meta tags, and performs a final assertion scan for forbidden strings (`praxis`, `studio`).

6. **Register-check enforcement** (`register_check.py`) implements 4 drift-marker categories with curated pattern catalogs, matching ADR-11 and Mary §A.1 register note.

7. **A/B harness blind evaluation** (`harness.py:122–142`) correctly anonymizes output labels and randomizes presentation order per arch §6.3.

8. **Test coverage** at 95.79% (Quinn 6.4) exceeds the 80% gate with comprehensive template backbone, benchmark regression, and provenance leak testing.

---

## §14. Stage 7 Debt Ledger Updates

### New Studio-specific items (add to existing 17-item ledger):

| # | Item | Source | Impact |
|---|---|---|---|
| DL-14 | Rename `CostTrackerProtocol` to `MetricsSinkProtocol` and update §11.1 wording | S6-A1 (this review) | Naming confusion between Studio's observability adapter and Pi-Mono's actual cost-tracking API |
| DL-15 | Add rendering-mode routing from user input to template path selection | S6-A2 + S6-A3 (this review) | Currently all YAML outputs hardcode `position_to_hold`; `decision_framework` and `firm_voice` templates exist but are not reachable via the shipped YAML |

### Pre-existing items confirmed still outstanding (no change):

- DL-1 through DL-13 from Studio arch §14.2 — all verified as still applicable
- 5 Cleo WARNINGs from Stage 5.3.5 (W-2, W-3, W-4, W-5, W-7) — none Studio-blocking
- 4 Cleo WARNINGs from Stage 6.3.5 (W-1..W-4) — forwarded to Stage 7

**Total Stage 7 debt ledger after 6.5:** 17 (pre-existing) + 2 (new) = **19 items**

---

## §15. Gate Decision

**Gate: GO to 6.6 Pre-Sales Checkpoint.**

| Check | Result |
|---|---|
| Studio uses MAC (Stage 5) correctly | **YES** — TaskInput handoff, gate configuration, co-evaluation, information asymmetry, budget enforcement all aligned |
| Output format matches Tokonomics rounds quality bar | **YES** — ADR-01 four-feature backbone, three rendering modes, dissent/scenario/scope-limit contracts, register enforcement all verified |
| Cross-stage contradictions blocking 6.6 | **NONE** — the 1 MEDIUM finding (CostTrackerProtocol naming) is observability-layer only; no behavioral impact on the demo |
| Frozen artifacts modified | **NONE** |
| 23 ratified Stage 5 decisions honored | **YES** — all verified |
| C-1..C-5 inherited drifts | **All correctly documented in §14; none blocking** |
| Tokonomics firewall intact | **YES** — zero producer vocabulary in customer-facing templates |
| Stage 5.6 headline caveat preserved | **YES** — harness auto-appends caveat; zero numbers cited |
| New debt items identified and tracked | **YES** — 2 new items (DL-14, DL-15) added to Stage 7 ledger |

**Pipeline §6.5 checkboxes can be marked `[x]`:**
- [x] Studio uses MAC (Stage 5) correctly
- [x] Output format matches Tokonomics rounds quality bar

---
