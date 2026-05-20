# Praxis Stage 6.1 — Studio Workflow Template Architecture

**Stage:** Praxis 6.1 — Studio (Strategic Advisory) first workflow template
**Author:** Winston (BMAD Architect)
**Date:** 2026-04-16
**Status:** DRAFT v0.1 — pending team-lead spot-check and ratification

**Binding upstream artifacts (three-source inheritance):**
1. `studio/customer-language-research.md` — Mary 6.0.1 (468 lines, v0.1 binding, RATIFIED 2026-04-15)
2. `studio/empathy-map.md` — Maya 6.0.2 (460 lines, v0.1 binding, RATIFIED 2026-04-15)
3. `studio/customer-requirements.md` — 6.0.3 Advanced Elicitation (582 lines, v0.1 binding, RATIFIED 2026-04-15; 11 ADRs)

**MAC integration anchor:**
- `mac/architecture.md` — Stage 5.1 Winston (2,028 lines, v0.3+ binding, RATIFIED 2026-04-14)

**Working-example references (Tokonomics rounds — output quality calibration only):**
- `Tokonomics/1st_Round_table.md` — wide survey pattern (7 agents + 10 research)
- `Tokonomics/2nd_Round_table.md` — deep analysis pattern (10 sessions, 25+ frameworks)
- `Tokonomics/3rd_Round_table.md` — competitive landscape pattern
- `Tokonomics/4th_Round_table.md` — red team pattern (6 independent agents; highest quality bar)
- `Tokonomics/business_session.md` — GTM synthesis pattern (8 parallel sessions)

**Team-lead dispositions applied (preload 2026-04-16):**
- D-1: ADRs supersede `stage-6-winston-prompt.md` where they conflict (overrides noted inline)
- D-2: Reuse Stage 5 benchmark set from `mac/benchmark-questions.md` (do not invent second set)
- D-3: Anchor Studio quality gates on Stage 5 R1–R12 rubric (prompt rubric is advisory, not binding)
- D-4: ADR-08 binds — no PDF export at Stage 6 MVP
- D-5: C-1..C-5 cross-stage drifts documented in §14 as known integration seams
- D-6: 14-section architecture outline approved
- D-7: Pipeline §4.6 mandatory context strategy executed

---

## ⚠️ §A.0 — TOKONOMICS FIREWALL + INHERITANCE DISCIPLINE (load-bearing)

This architecture document inherits all three Stage 6.0.x upstream artifacts and their load-bearing constraints:

1. **Mary §A.0 tokonomics firewall** — no tokonomics-era personas or vocabulary in any customer-facing Studio surface copy, Jinja2 template content, YAML help text, or error messages. Tokonomics-era ICP (VP-Eng / agent-builder CTO / RAG Dir-of-Eng) and vocabulary (compression / token / gateway / proxy / SDK / callback) are OUT OF SCOPE for Studio.
2. **Maya §A.0 inheritance banner rules 1–6** — segment weighting 50/30/20, muted operator-realism register, `[HYPOTHETICAL]` flag propagation, fractional C-suite operators deferred to Stage 7.
3. **§B.7 + §C.4 anti-glossaries** — producer-mechanism vocabulary (multi-agent deliberation, information asymmetry, quality gates R1–R12, 3-cycle iteration, MAC, Pi-Mono, Forge, Atelier, Beads, Mem0, Caveman, RTK, TONL, structural invariants, falsifiability gates) does NOT appear in any customer-facing output.
4. **11 ADRs from customer-requirements.md** are binding output-format contracts. Each is referenced by ADR number throughout this document.
5. **Stage 5.6 conditional headline caveat** — any pre-sales numbers carry "(internal scoring; A4 deferred)" until Stage 7 ratifies ρ ≥ 0.6.

**Producer-facing vs. customer-facing boundary:** this architecture document is a producer-facing artifact. MAC component names, gate IDs (R1–R12), and internal integration vocabulary appear in §2–§14 as architectural specifications. They do NOT appear in the Jinja2 templates (§4) that render customer-facing output. The anti-glossary applies to rendered output, not to architecture documentation.

---

## §1 — Scope & Inheritance

### §1.1 What This Document Covers

Studio is a **configuration over the MAC** (Stage 5), not a new runtime. This document specifies:

1. A **general-purpose workflow template YAML schema** (§2) — reusable for Factory, Shield, Pipeline, Ops configurations in Stages 7+
2. The **Studio-specific `strategic_session.yaml`** (§3) — first instance of that schema
3. **Jinja2 output templates** (§4) — rendering contracts per ADR-01 through ADR-11
4. **A/B comparison harness design** (§6) — blind evaluation of Studio vs. single-agent baseline
5. **Benchmark question integration** (§7) — reuses Stage 5 set per D-2
6. **Evaluation protocol** (§8) — anchored on R1–R12 per D-3
7. **Gate calibration plan** (§9) — tuned against manual Tokonomics round outputs
8. **Cost model** (§10) — budget allocation and enforcement per cycle

### §1.2 What This Document Does Not Cover

- Implementation code (Amelia 6.3)
- Test strategy (Murat 6.2)
- Pre-sales demo scripting (Stage 6.6)
- PDF/`.pptx` export (deferred to Stage 7 per ADR-08; D-4)
- "Built With Praxis" public dashboard badge (deferred to Stage 7.6 per ADR-10)
- Shareable-link delivery mechanism (Stage 7.1 shell arch scope; ADR-10 link-model primitives defined here)

---

## §2 — Workflow Template Schema

### §2.1 Design Goal

A single YAML schema that any Praxis product configuration (Studio, Factory, Shield, Pipeline, Ops) can instantiate. The schema is checked at load time by a Pydantic model — no runtime surprises.

### §2.2 Schema Definition (Pydantic)

```python
# praxis/kernel/studio/schema.py

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from enum import Enum

class RenderingMode(str, Enum):
    """ADR-02: three decision-shape rendering modes."""
    POSITION_TO_HOLD = "position_to_hold"       # founder-default
    DECISION_FRAMEWORK = "decision_framework"    # COO-default
    FIRM_VOICE = "firm_voice"                    # consultancy-default

class ProvenanceMode(str, Enum):
    """ADR-09: three tool-provenance visibility modes.
    Inferred default from rendering_mode unless explicitly overridden.
    position_to_hold → flexible, decision_framework → inspectable,
    firm_voice → invisible."""
    FLEXIBLE = "flexible"
    INSPECTABLE = "inspectable"
    INVISIBLE = "invisible"

PROVENANCE_DEFAULTS: dict[RenderingMode, ProvenanceMode] = {
    RenderingMode.POSITION_TO_HOLD: ProvenanceMode.FLEXIBLE,
    RenderingMode.DECISION_FRAMEWORK: ProvenanceMode.INSPECTABLE,
    RenderingMode.FIRM_VOICE: ProvenanceMode.INVISIBLE,
}

class AgentAssignment(BaseModel):
    model_config = ConfigDict(frozen=True)
    role: str                                  # e.g. "market_researcher", "risk_analyst"
    agent_id: str                              # maps to BMAD agent-manifest.csv agent_id
    output_label: str                          # what this agent's output is called in the cycle
    depends_on: tuple[str, ...] = ()           # output_labels from prior agents this one needs

class CycleSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str                                  # e.g. "wide_survey", "deep_analysis", "red_team_synthesis"
    budget_pct: int                            # % of total budget allocated to this cycle
    agents: tuple[AgentAssignment, ...]
    parallel: bool = True                      # agents within cycle run in parallel by default
    asymmetry: bool = False                    # if True, agents do NOT see each other's outputs
    skip_in_quick_mode: bool = False           # if True, cycle is skipped in quick mode
    reviewer_count: int = 1                    # MAC PhaseDAG reviewer_count override

class QualityGateSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    gate_id: str                               # "R1".."R12" — must match mac/quality-rubric.md
    min_score: int = 3                         # minimum passing score (1-5 scale)
    weight_override: int | None = None         # override default weight from rubric; None = use rubric default
    section_routing: str | None = None         # Req-B section to evaluate; None = use default routing

class OutputSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    format: Literal["markdown", "html"]        # ADR-08 MVP scope; PDF/pptx deferred to Stage 7
    template_path: str                         # path to Jinja2 template relative to studio/templates/
    rendering_mode: RenderingMode              # ADR-02: which decision-shape to render

class ShareableLinkSpec(BaseModel):
    """ADR-10: shareable-link model primitives."""
    model_config = ConfigDict(frozen=True)
    auth_gated: bool = True                    # always True in 6.1 MVP
    default_expiry_days: int = 30              # configurable per-link at generation time
    owner_revocable: bool = True               # always True

class WorkflowTemplate(BaseModel):
    """Top-level workflow template schema. Validated at load time."""
    model_config = ConfigDict(frozen=True)

    name: str
    product: str                               # "studio", "factory", "shield", "pipeline", "ops"
    description: str
    version: str                               # semver

    inputs: dict[str, "InputParamSpec"]        # parameter definitions with types, constraints, defaults

    rendering_mode: RenderingMode              # ADR-02 — required field, not optional
    provenance_mode: ProvenanceMode | None = None  # ADR-09 — None = infer from rendering_mode

    cycles: tuple[CycleSpec, ...]              # ordered cycle definitions
    quality_gates: tuple[QualityGateSpec, ...]  # gate specifications (subset of R1-R12 relevant to this workflow)
    outputs: tuple[OutputSpec, ...]            # output format specifications

    shareable_links: ShareableLinkSpec = ShareableLinkSpec()

    cost_budget_usd: float                     # total budget ceiling for this workflow invocation
    timeout_seconds: float                     # wall-clock timeout for entire workflow

    def resolved_provenance_mode(self) -> ProvenanceMode:
        if self.provenance_mode is not None:
            return self.provenance_mode
        return PROVENANCE_DEFAULTS[self.rendering_mode]

class InputParamSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: Literal["string", "int", "float", "bool", "enum"]
    required: bool = True
    default: str | int | float | bool | None = None
    description: str
    enum_values: tuple[str, ...] | None = None  # for type="enum"
    max_length: int | None = None               # for type="string"
```

### §2.3 Schema Extensibility

Fields can be added to `WorkflowTemplate` in Stage 7+ without breaking existing templates — Pydantic's `extra="ignore"` on a future migration model handles forward compatibility. The `product` field gates which template-specific checking rules apply.

### §2.4 Schema Validation at Load Time

`WorkflowTemplate.model_validate(yaml.safe_load(template_file))` runs at startup. Failures abort with a clear error message naming the invalid field and expected type. No template reaches the MAC without passing this check.

### §2.5 MAC Integration: Template → TaskInput

When Studio invokes the MAC, it translates the `WorkflowTemplate` + user inputs into the MAC's `TaskInput`:

```python
# praxis/kernel/studio/invoker.py

def template_to_task_input(
    template: WorkflowTemplate,
    user_inputs: dict[str, str | int | float | bool],
    customer_context: dict[str, str],
) -> TaskInput:
    return TaskInput(
        raw_prompt=user_inputs["strategic_question"],
        customer_context=customer_context,
        workflow_template_id=f"{template.product}/{template.name}/{template.version}",
        explicit_question=user_inputs.get("explicit_question"),
    )
```

The MAC's `PhaseDAG` is constructed from the template's `cycles` field — each `CycleSpec` maps to MAC `PhaseNode` entries with the appropriate `phase_kind` and `reviewer_count`. This is the Studio→MAC handoff contract.

---

## §3 — Studio `strategic_session.yaml`

### §3.1 YAML Template (Deep Mode)

```yaml
name: strategic_session
product: studio
description: >
  Multi-perspective strategic advisory session. Produces a structured
  analysis with explicit trade-offs, dissent, named scenarios, and
  scope-limits. Three cycles: wide survey, deep analysis, red team + synthesis.
version: "0.1.0"

inputs:
  strategic_question:
    type: string
    required: true
    description: "The strategic question to analyze"
    max_length: 2000
  customer_context:
    type: string
    required: false
    description: "Company stage, industry, constraints, stakeholders"
    max_length: 5000
  rendering_mode:
    type: enum
    required: true
    description: "Output shape — position_to_hold (founder), decision_framework (COO), firm_voice (consultancy)"
    enum_values:
      - position_to_hold
      - decision_framework
      - firm_voice
  provenance_mode:
    type: enum
    required: false
    description: "Tool-provenance visibility — flexible, inspectable, invisible. Defaults from rendering_mode."
    enum_values:
      - flexible
      - inspectable
      - invisible

rendering_mode: "${inputs.rendering_mode}"
provenance_mode: null  # inferred from rendering_mode unless overridden

cycles:
  - name: wide_survey
    budget_pct: 20
    parallel: true
    asymmetry: false
    skip_in_quick_mode: false
    agents:
      - role: market_researcher
        agent_id: bmad_mary
        output_label: market_intel
      - role: innovation_strategist
        agent_id: bmad_victor
        output_label: strategic_framing
      - role: product_manager
        agent_id: bmad_john
        output_label: customer_perspective

  - name: deep_analysis
    budget_pct: 50
    parallel: false  # sequential — each builds on prior outputs
    asymmetry: false
    skip_in_quick_mode: true
    agents:
      - role: architect
        agent_id: bmad_winston
        output_label: technical_feasibility
        depends_on:
          - market_intel
          - strategic_framing
      - role: risk_analyst
        agent_id: bmad_quinn
        output_label: risk_analysis
        depends_on:
          - market_intel
          - strategic_framing
          - customer_perspective
      - role: contrarian
        agent_id: bmad_carson
        output_label: contrarian_angles
        depends_on:
          - market_intel
          - strategic_framing
          - customer_perspective

  - name: red_team_synthesis
    budget_pct: 30
    parallel: false
    asymmetry: true  # red team does NOT see deep_analysis reasoning traces
    skip_in_quick_mode: false
    reviewer_count: 2
    agents:
      - role: red_team
        agent_id: bmad_quinn
        output_label: red_team_critique
      - role: narrative_synthesizer
        agent_id: bmad_sophia
        output_label: synthesis
        depends_on:
          - red_team_critique
      - role: visual_presenter
        agent_id: bmad_caravaggio
        output_label: visual_brief
        depends_on:
          - synthesis

quality_gates:
  - gate_id: R1
    min_score: 3
  - gate_id: R2
    min_score: 3
  - gate_id: R3
    min_score: 3
  - gate_id: R4
    min_score: 4   # steelman completeness — Studio's core differentiator
    weight_override: 2
  - gate_id: R5
    min_score: 4   # dissent preservation — equally critical
    weight_override: 2
  - gate_id: R6
    min_score: 3
  - gate_id: R7
    min_score: 3
  - gate_id: R8
    min_score: 3
  - gate_id: R9
    min_score: 3
  - gate_id: R10
    min_score: 3
  - gate_id: R11
    min_score: 3
  - gate_id: R12
    min_score: 3

outputs:
  - format: markdown
    template_path: "templates/brief.md.j2"
    rendering_mode: "${rendering_mode}"
  - format: html
    template_path: "templates/deck.html.j2"
    rendering_mode: "${rendering_mode}"
  - format: markdown
    template_path: "templates/executive_summary.md.j2"
    rendering_mode: "${rendering_mode}"

shareable_links:
  auth_gated: true
  default_expiry_days: 30
  owner_revocable: true

cost_budget_usd: 10.00   # deep mode ceiling
timeout_seconds: 1800     # 30 minutes wall-clock
```

### §3.2 Quick Mode Variant

Quick mode skips the `deep_analysis` cycle (`skip_in_quick_mode: true`) and runs only `wide_survey` → `red_team_synthesis`. Budget redistributes: wide_survey gets 40%, red_team_synthesis gets 60%. Cost ceiling drops to $2.00, timeout to 600 seconds.

The quick-mode variant is expressed as a separate `strategic_session_quick.yaml` file that inherits from the deep template with overrides, not as runtime logic. Template-level branching, not code-level branching.

### §3.3 Agent-to-Role Mapping Rationale

| Cycle | Role | BMAD Agent | Why This Agent |
|---|---|---|---|
| Wide Survey | Market researcher | Mary | Competitive intel, market dynamics, customer voice — same role as Tokonomics Rounds 1-3 |
| Wide Survey | Innovation strategist | Victor | Strategic framing, disruption analysis — same role as Tokonomics Round 1 |
| Wide Survey | Product manager | John | Customer perspective, JTBD assessment — PMF skepticism role from Round 4 |
| Deep Analysis | Architect | Winston | Technical feasibility assessment — same role as Tokonomics Round 4 |
| Deep Analysis | Risk analyst | Dr. Quinn | Systematic failure analysis, risk matrix — same role as Tokonomics Round 4 |
| Deep Analysis | Contrarian | Carson | Reverse brainstorming, graveyard walk — same role as Tokonomics Round 4 |
| Red Team | Red team | Dr. Quinn | Adversarial analysis with information asymmetry enforced — Round 4 pattern |
| Synthesis | Narrative synthesizer | Sophia | Dissent-preserving narrative synthesis — preserves the "multiple voices" quality |
| Synthesis | Visual presenter | Caravaggio | Deck rendering, comparison tables — visual brief generation |

**Overrides prompt §3 per D-1:** prompt specified exact agent-to-cycle mapping; this architecture preserves the same mapping because it aligns with ADR-01 (four-feature backbone) and the Tokonomics working examples. No override needed.

### §3.4 Budget Allocation Rationale

The 20/50/30 split mirrors the observed Tokonomics pattern:
- **Wide survey (20%):** parallel agents, each producing a bounded perspective — low per-agent cost because each is scoped to a single analytical lens
- **Deep analysis (50%):** sequential agents building on prior outputs — highest per-agent cost because each has richer context from prior cycle outputs
- **Red team + synthesis (30%):** information-asymmetric review + narrative assembly — moderate cost split between adversarial critique and rendering

Budget enforcement flows through MAC's `ResourceBudget` per cycle (mac/architecture.md §5.7). Unused budget from an earlier cycle rolls forward to the next — the MAC's existing budget-reallocation mechanism handles this without Studio-specific code.

---

## §4 — Output Template Contracts (Jinja2)

### §4.1 ADR-01 Four-Feature Backbone

Every Studio output renders four mandatory top-level sections in fixed order (ADR-01 O-A, ratified):

1. **Structured Trade-offs** — explicit factors, weights, alternatives
2. **Dissent** — dedicated section with equal rendering weight (ADR-05)
3. **Named Scenarios** — trigger / invalidation / decision-rule per scenario (ADR-06)
4. **Scope-Limits** — what wasn't analyzed: data gaps / adjacent questions / invalidating assumptions (ADR-07)

These four sections are present in every output regardless of rendering mode. They are Jinja2-enforced blocks that error if omitted from the reasoning trace.

### §4.2 ADR-02 Three Rendering Modes

One underlying MAC reasoning trace, three render passes:

| Mode | Template Family | Default For | Decision Shape |
|---|---|---|---|
| `position_to_hold` | `position_to_hold/*.j2` | Founders (50%) | Conditional position the founder can hold for two quarters; recommendations are commitments with trigger conditions |
| `decision_framework` | `decision_framework/*.j2` | COOs (30%) | Factor-weighted framework the team can execute against; deliverable IS the framework, not the conclusion |
| `firm_voice` | `firm_voice/*.j2` | Consultancies (20%) | Firm-voice deliverable at consultant-acceptable density; findings / alternatives / dissent / scope-limits |

All three families inherit a shared base template (`_base.j2`) that renders the ADR-01 four-feature backbone. Mode-specific templates override section presentation (ordering of sub-elements within each backbone section, emphasis patterns, density targets) without changing which sections are present.

### §4.3 Template File Structure

```
studio/templates/
├── _base.j2                        # ADR-01 backbone — 4 mandatory blocks
├── _partials/
│   ├── dissent.j2                  # ADR-05 — steelman per competing frame
│   ├── scenario.j2                 # ADR-06 — trigger / invalidation / decision-rule
│   ├── scope_limits.j2             # ADR-07 — data / adjacent-questions / invalidating-assumptions
│   ├── provenance_flexible.j2      # ADR-09 — small dismissible footer
│   ├── provenance_inspectable.j2   # ADR-09 — expandable "How this analysis was generated"
│   ├── provenance_invisible.j2     # ADR-09 — empty (no Studio identifiers anywhere)
│   └── register_check.j2           # ADR-11 — register-drift marker check
├── position_to_hold/
│   ├── brief.md.j2
│   ├── deck.html.j2
│   └── executive_summary.md.j2
├── decision_framework/
│   ├── brief.md.j2
│   ├── deck.html.j2
│   └── executive_summary.md.j2
└── firm_voice/
    ├── brief.md.j2
    ├── deck.html.j2
    └── executive_summary.md.j2
```

### §4.4 ADR-03 Brief Length Band

Target: 8–20 pages rendered output (brief mode), ~3,500–8,500 words. `[HYPOTHETICAL — band values subject to Stage 7 corroboration]`

Per-section minimums (calibrated empirically against benchmark regression set at 6.4 Quinn time):

| Section | Minimum Words | Rationale |
|---|---|---|
| Trade-offs | 800 | Must enumerate factors, weights, alternatives |
| Dissent | 600 | Equal rendering weight per ADR-05 |
| Scenarios | 500 | Minimum 2 scenarios × 3 sub-fields each |
| Scope-limits | 300 | Three sub-categories with at least one entry each |
| Remaining (findings, recommendations, executive summary) | Balance of band | Density varies by question complexity |

Outputs falling below the minimum band trigger a reasoning-trace-depth retry through the MAC's backtrack mechanism (§5.5), not a length-pad.

### §4.5 ADR-04 Deck Format

Single deck format: 10–18 slides, text-dense, no stock imagery.

| Slide Range | Content |
|---|---|
| 1 | Title + strategic question + customer context |
| 2 | Executive summary (1-slide version) |
| 3–5 | Trade-offs section (factors, weights, comparison table) |
| 6–8 | Dissent section (2–3 slides per ADR-05; steelman per competing frame) |
| 9–11 | Scenarios (named scenarios with trigger/invalidation/decision-rule tables) |
| 12–13 | Scope-limits (3 sub-categories) |
| 14 | Recommendations with confidence signals |
| 15–18 | Supporting detail (as needed by question complexity) |

Slide titles use statement-of-finding format, not category-label format (consultancy §C Focus Group reaction on ADR-04, folded into ADR-04 consequences).

### §4.6 ADR-05 Dissent Rendering

Dedicated `dissent.j2` partial renders one steelman per competing frame. Structure per frame:

```
## Competing Frame: [frame_name]

**Steelman (strongest version of this position):**
[independent steelman — generated by reviewer agent under information asymmetry, NOT by the producer]

**Evidence supporting this frame:**
[specific evidence from the reasoning trace]

**Conditions under which this frame becomes the recommendation:**
[explicit trigger conditions — COO ADR-06 §C reaction fold-back: name owner + date, not just rule]

**Confidence relative to recommended frame:**
[rubric score comparison — ADR-05 §D fold-back: confidence signal, not uncritical symmetry]
```

Minimum: one competing frame per strategic question. Zero competing frames triggers a MAC re-run with explicit red-team prompt.

### §4.7 ADR-06 Scenario Rendering

`scenario.j2` partial renders three required sub-fields per scenario:

```
### Scenario: [scenario_name]

**Trigger condition:** [what makes this scenario live]
**Invalidation condition:** [what falsifies this scenario]
**Decision rule:** [what to do if the condition fires — includes owner + date per COO fold-back]
```

Minimum two named scenarios per strategic question (matches MAC R3 rubric anchor). The word "invalidation conditions" is preserved at string level per precedent #14.

### §4.8 ADR-07 Scope-Limits Rendering

`scope_limits.j2` partial renders three required sub-categories:

```
## What This Analysis Did Not Cover

### Data not available
[specific data the analysis did not have access to]

### Adjacent questions out of scope
[specific follow-on analyses — one per item, not open-ended topic lists per ADR-07 §D fold-back]

### Assumptions that would invalidate the recommendation
[specific assumptions — if wrong, the recommendation changes]
```

Minimum one entry per sub-category. Zero-entry sub-categories trigger a retry. Rendered in muted register: "we did not have access to X" rather than "X is missing."

### §4.9 ADR-09 Provenance Rendering

Three provenance partials selected by `resolved_provenance_mode()`:

| Mode | Partial | Behavior |
|---|---|---|
| `flexible` | `provenance_flexible.j2` | Small dismissible footer: "Generated with Praxis" |
| `inspectable` | `provenance_inspectable.j2` | Expandable section: "How this analysis was generated" with reasoning-trace pointer (URL placeholder resolved by Stage 7 shell) |
| `invisible` | `provenance_invisible.j2` | Empty — no Studio identifiers in rendered text, file metadata, or HTML comments |

**Invisible mode implementation checklist** (ADR-09 §D fold-back from consultancy §C reaction): rendered text clean + file metadata stripped + HTML comment stripped + no `praxis` / `studio` string in any output byte. Amelia (6.3) must implement a metadata-strip pass in the invisible render path.

### §4.10 ADR-11 Register Contract

All Studio-facing copy — briefs, decks, executive summaries, error messages, progress indicators — uses the muted operator-realism register from Mary §A.1:

> wry, specific, hedged, risk-aware, uninterested in performing. No founder-Twitter caricature, no dramatic-stakes language, no urgency performance.

**Enforcement:** `register_check.j2` is a Jinja2 macro that flags register-drift markers in rendered output. Drift markers include: exclamation marks in analytical text, dramatic-stakes verbs (per a curated list), urgency-performing adverbs ("urgently", "immediately", "critical" in non-risk contexts), and condescending patterns.

`register_guide.md` (sibling to templates) encodes Mary §A.1 register note verbatim as the style contract. Benchmark regression tests at 6.4 Quinn time run the register-check against all 10 benchmark outputs.

---

## §5 — Quality Gates

### §5.1 Gate Anchoring (D-3)

Studio quality gates anchor on Stage 5 R1–R12 rubric (mac/quality-rubric.md §6). The prompt's ad-hoc gate list (completeness, dissent_present, evidence_grounded, actionable, red_team_addressed) is advisory context that maps onto R1–R12 as follows (overrides prompt §4 per D-1):

| Prompt Gate | Maps To | R-Gate | Priority |
|---|---|---|---|
| completeness | R1 Comprehensiveness | R1 | Critical |
| dissent_present | R5 Dissent Preservation | R5 | Critical (2× weight) |
| evidence_grounded | R2 Epistemic Calibration | R2 | Critical |
| actionable | R10 Actionability Calibration | R10 | Critical |
| red_team_addressed | R4 Steelman Completeness | R4 | Critical (2× weight) |

### §5.2 Studio-Specific Gate Configuration

Studio activates all 12 gates (R1–R12) with elevated minimums on R4 and R5:

| Gate | min_score | Weight | Rationale |
|---|---|---|---|
| R1 Comprehensiveness | 3 | 1 | Standard |
| R2 Epistemic Calibration | 3 | 1 | Standard |
| R3 Falsifiability | 3 | 1 | Scenario invalidation conditions |
| R4 Steelman Completeness | **4** | **2** | Studio's core differentiator — red team quality |
| R5 Dissent Preservation | **4** | **2** | ADR-05 binding contract — equal-weight dissent |
| R6 Scenario Coverage | 3 | 1 | ADR-06 named scenarios |
| R7 Reasoning Preservation | 3 | 1 | Standard (Forge degradation penalty applies) |
| R8 Context Utilization | 3 | 1 | Standard |
| R9 Scope-Awareness | 3 | 1 | ADR-07 scope-limits |
| R10 Actionability | 3 | 1 | Standard |
| R11 Internal Consistency | 3 | 1 | Standard |
| R12 Uncertainty Flagging | 3 | 1 | Standard |

R13 Evidence Sourcing remains deferred per SQ-3 / MAC §3.5. Studio does not re-admit R13 in 6.1 because the workflow agents operate from training knowledge, not retrieval-augmented sources. Stage 7 may reconsider if retrieval integration is added.

### §5.3 Gate-to-ADR Alignment

| ADR | Load-Bearing Gate | Enforcement |
|---|---|---|
| ADR-01 (four features) | R1 + R4 + R5 + R6 + R9 | All four backbone sections present in output |
| ADR-02 (rendering modes) | — | Template-level; not gate-scored |
| ADR-03 (brief length) | — | Per-section minimums enforced by template renderer, not by MAC gates |
| ADR-05 (dissent) | R5 (min 4, 2× weight) | At least one competing frame with steelman |
| ADR-06 (scenarios) | R3 + R6 | At least 2 scenarios with 3 sub-fields each |
| ADR-07 (scope-limits) | R9 | Three sub-categories, each with ≥1 entry |
| ADR-11 (register) | — | Register-check script, not MAC gate |

---

## §6 — A/B Comparison Harness

### §6.1 Design

Given a strategic question, the harness runs two paths:

**Path A — Single-agent baseline:** Claude (same model as Studio's producer agent) with a direct prompt asking for strategic analysis. No multi-agent orchestration, no quality gates, no rendering modes. Raw single-pass output.

**Path B — Studio:** Full `strategic_session.yaml` workflow through the MAC. Three cycles, 12 quality gates, rendering-mode output.

**Enhanced single-agent baseline (per ADR-3 from Stage 5.0.3 benchmark-questions.md):** A second baseline that provides the single agent with the same structural prompt (Req-A section labels, explicit instructions to include dissent and scenarios). This isolates the multi-agent structural advantage from the prompt-engineering advantage.

### §6.2 Metrics Captured Per Run

| Metric | Path A | Path B | Unit |
|---|---|---|---|
| Cost | Pi-Mono tracked | Pi-Mono tracked | USD |
| Wall-clock time | start→finish | start→finish | seconds |
| Output word count | rendered words | rendered words | words |
| Quality composite score | blind eval against R1–R12 | blind eval against R1–R12 | 0–100 |
| Per-gate scores | R1–R12 individual | R1–R12 individual | 1–5 |
| Backbone completeness | {0,1} per section | {0,1} per section | boolean ×4 |
| Register compliance | register-check pass/fail | register-check pass/fail | boolean |

### §6.3 Blind Evaluation Protocol

The evaluator (human or LLM-as-judge) receives **anonymized outputs** — neither labeled as "Studio" or "baseline." Evaluation uses the R1–R12 rubric from mac/quality-rubric.md with the benchmark-questions.md calibration anchors.

Order randomization: for each benchmark question, the two outputs are presented in random order. The evaluator scores both before being told which is which.

### §6.4 Comparison Report Format

```markdown
# Studio A/B Comparison Report

## Headline
Studio vs. single-agent on [N] benchmark questions:
- Quality: +X% composite (Studio [Y] vs baseline [Z])
- Cost: Studio $A vs baseline $B (ratio: C×)
- Time: Studio Dm vs baseline Em
- Beat count: Studio wins F/N questions

## Per-Question Results
[table: question | studio_score | baseline_score | enhanced_baseline_score | cost_ratio | time_ratio]

## Per-Gate Analysis
[table: gate_id | studio_avg | baseline_avg | delta | significance]

## Dissent Preservation (R5)
[specific analysis of whether Studio's red team cycle produces structurally stronger dissent]

## Cost-Quality Trade-off
[scatter plot data: cost vs composite score per question per path]
```

---

## §7 — Benchmark Question Set (D-2: Reuse Stage 5)

### §7.1 Source

The 10 benchmark questions from `mac/benchmark-questions.md` (Stage 5.0.3, RATIFIED 2026-04-14) are reused verbatim. They were selected through three elicitation rounds (Carson quality dimensions → Quinn failure mode analysis → Advanced Elicitation comparative matrix) and have gold standards, calibration anchors, and scoring protocols already defined.

**Override of prompt §7 per D-1:** prompt said "sourced from real use cases (Tokonomics rounds)." The Stage 5 set was sourced from a comparative analysis matrix scored on 5 criteria (Coverage of Rubric, Gate Coverage, Model-Gaming Difficulty, Analytical Specificity, Template Diversity) — a more rigorous selection than ad-hoc Tokonomics sourcing. Same ground truth, better methodology.

### §7.2 Benchmark Questions (Reference)

| # | Question | Domain | Type |
|---|---|---|---|
| Q1 | Pricing strategy transition (per-seat → usage-based) | SaaS pricing | CONTESTED |
| Q2 | Capital strategy under uncertainty (bridge vs. extend) | Finance | CONTESTED |
| Q3 | Acquire vs. build decision | M&A / COO | CONTESTED |
| Q4 | Strategic partnership with exclusivity | Partnerships | CONTESTED |
| Q5 | Moat building before commoditization | Strategy | CONTESTED |
| Q6 | Competitive response to aggressive pricing | Pricing | CONTESTED |
| Q7 | Market expansion timing (EU) | Growth | CONTESTED |
| Q8 | Platform threat response | Strategy | CONTESTED |
| Q9 | GTM model selection (enterprise vs. SMB) | GTM | CONTESTED |
| Q10 | Diagnostic (diverging NPS vs. retention) | Operations / COO | DIAGNOSTIC |

All questions are CONTESTED except Q10 (DIAGNOSTIC) — matching the MAC's DomainClass classification and the Mary/Maya elicitation segment anchoring (Q1-Q9 are founder-anchored, Q3/Q10 are COO-anchored).

### §7.3 Gold Standards

Gold standards exist per question in `mac/benchmark-questions.md` §4. Studio uses these for gate calibration (§9) and A/B comparison baseline (§6). The gold standards were derived from the manual Tokonomics round outputs — the same ground truth the prompt's §7 intended.

---

## §8 — Evaluation Protocol (D-3: Anchor on R1–R12)

### §8.1 Scoring Protocol

Per `mac/benchmark-questions.md` §6:

1. Run Studio on all 10 benchmark questions
2. Score each output on R1–R12 (1–5 scale per gate)
3. Apply weight multipliers (R4 and R5 at 2×)
4. Compute composite score per question: `sum(effective_score × weight) / sum(weight) × 20` → 0–100 scale
5. Compute aggregate: mean composite across 10 questions

**Override of prompt §8 per D-1:** prompt defined an ad-hoc rubric (Coverage, Risk identification, Actionability, Dissent preservation, Honesty). These are absorbed into R1–R12 per §5.1 mapping. The Stage 5 rubric is the binding evaluation framework.

### §8.2 Spearman Correlation Target

Per ADR-3 from Stage 5.0.3: Spearman ρ ≥ 0.6 between human evaluator scores and LLM-as-judge scores. This is the inter-rater reliability target for the A4 corroboration protocol. A4 is deferred to Stage 7 — Stage 6 runs the evaluation and captures the data but does NOT make the ρ claim until Stage 7 ratifies it.

### §8.3 Full Disclosure

Per Stage 5.0.3 ADR-2 (thesis defense — Practitioner concern): all 10 benchmark results are reported, including questions where Studio underperforms the baseline. No cherry-picking.

---

## §9 — Gate Calibration Plan

### §9.1 Calibration Dataset

The Tokonomics rounds serve as the calibration dataset — they are the manual BMAD sessions that Studio must match or exceed in quality. Specifically:

| Round | Calibration Purpose |
|---|---|
| Round 1 (wide survey) | Calibrates R1 (comprehensiveness) — did the wide survey cover as many angles? |
| Round 2 (deep analysis) | Calibrates R10 (actionability) — are recommendations as concrete? |
| Round 4 (red team) | Calibrates R4 (steelman), R5 (dissent) — is the red team as unflinching? |
| Business session | Calibrates R6 (scenario coverage) — are named scenarios as specific? |

### §9.2 Calibration Procedure

1. Score each Tokonomics round output on R1–R12 using the same rubric (establishes the quality bar)
2. Run Studio on the same 10 benchmark questions
3. Compare per-gate scores: Studio should match or exceed the Tokonomics calibration scores on R4, R5, R6 (the Studio differentiators)
4. If Studio falls below on any differentiator gate: tune the producer and reviewer prompts in the workflow YAML, not the gate thresholds. Gate thresholds are the contract — prompt quality is the lever.

### §9.3 Iteration Approach

Gate calibration is iterative:
1. First pass: run Studio with default prompts
2. Score against calibration set
3. Identify weakest gates (lowest per-gate scores relative to Tokonomics calibration)
4. Tune prompts for those gates
5. Re-run and re-score
6. Repeat until all differentiator gates (R4, R5, R6) meet or exceed Tokonomics quality bar

Maximum 3 calibration iterations — if R4/R5/R6 don't converge after 3 iterations, escalate to architecture revision (likely the agent assignment or cycle structure needs adjustment, not just prompt tuning).

---

## §10 — Cost Model

### §10.1 Budget Targets

| Mode | Cost Ceiling | Timeout | Rationale |
|---|---|---|---|
| Quick | $2.00 | 10 min | 2 cycles, parallel agents, scoped outputs |
| Deep | $10.00 | 30 min | 3 cycles, sequential deep analysis, full gate evaluation |

These targets were set in the build plan (Stage 6 pre-sales asset: "$1-10 per session"). They constrain agent model selection and cycle count.

### §10.2 Per-Cycle Budget Allocation

**Deep mode:**

| Cycle | Budget % | Budget USD | Agent Count | Per-Agent Budget |
|---|---|---|---|---|
| Wide survey | 20% | $2.00 | 3 (parallel) | ~$0.67 |
| Deep analysis | 50% | $5.00 | 3 (sequential) | ~$1.67 |
| Red team + synthesis | 30% | $3.00 | 3 (sequential) | ~$1.00 |

**Quick mode:**

| Cycle | Budget % | Budget USD | Agent Count | Per-Agent Budget |
|---|---|---|---|---|
| Wide survey | 40% | $0.80 | 3 (parallel) | ~$0.27 |
| Red team + synthesis | 60% | $1.20 | 3 (sequential) | ~$0.40 |

### §10.3 Model Selection Implication

At current Anthropic pricing (Sonnet 4.6: $3/$15 per M tokens in/out; Haiku 4.5: $1/$5 per M tokens):

- Wide survey agents (parallel, bounded scope): **Haiku 4.5** — adequate for market intel, strategic framing, customer perspective at this scope
- Deep analysis agents (sequential, richer context): **Sonnet 4.6** — required for technical feasibility, risk analysis, contrarian depth
- Red team agent: **Sonnet 4.6** — adversarial analysis requires deeper reasoning
- Synthesis and visual agents: **Haiku 4.5** — compilation and rendering, not novel analysis
- Quality gate evaluator (Tier 3 LLM-as-judge): **Sonnet 4.6** — calibrated judgment required

This model mix keeps the deep-mode cost within the $10 ceiling while maintaining quality on the differentiator gates (R4, R5).

### §10.4 Cost Control Levers

1. **Model downgrade:** if cost exceeds $8 on a deep session, fall back Sonnet agents to Haiku for remaining cycles
2. **Cycle skip:** if cost exceeds 80% of budget before Cycle 3, skip Caravaggio visual rendering (synthesis-only output)
3. **Budget rollover:** unused budget from Cycle 1 rolls to Cycle 2 (MAC's existing mechanism)
4. **Hard ceiling:** Pi-Mono enforces the `cost_budget_usd` field — no agent call proceeds after the ceiling is hit

---

## §11 — Observability

### §11.1 Session Metrics (Pi-Mono Integration)

Every Studio session emits the following via Pi-Mono's `CostTracker.track_cost`:

| Metric | Label Namespace | Unit |
|---|---|---|
| Total session cost | `studio.session.cost_usd` | USD |
| Per-cycle cost | `studio.cycle.{name}.cost_usd` | USD |
| Per-agent cost | `studio.agent.{role}.cost_usd` | USD |
| Session duration | `studio.session.duration_seconds` | seconds |
| Per-cycle duration | `studio.cycle.{name}.duration_seconds` | seconds |
| Composite quality score | `studio.session.composite_score` | 0–100 |
| Per-gate scores | `studio.gate.{R_id}.score` | 1–5 |
| Backtrack count | `studio.session.backtrack_count` | int |
| Rendering mode used | `studio.session.rendering_mode` | enum |
| Quick vs. deep mode | `studio.session.mode` | enum |

### §11.2 Session-Over-Time Tracking

Aggregate metrics over time enable:
- Cost-per-session trend (should decrease as prompts are tuned and memory seeds accumulate)
- Quality-per-session trend (should increase as gate calibration converges)
- Rendering mode distribution (which segments are using Studio)
- Backtrack frequency (high backtracks signal prompt-quality issues)

### §11.3 Future: User Feedback Loop

Stage 7 shell adds a feedback mechanism where customers rate outputs after reading. This feeds back into gate calibration — the Spearman ρ target (§8.2) is tested against real user ratings, not just internal scoring.

---

## §12 — Testability Notes for Murat

### §12.1 Schema Validation Tests

- `WorkflowTemplate.model_validate()` on `strategic_session.yaml` passes
- `WorkflowTemplate.model_validate()` on `strategic_session_quick.yaml` passes
- Invalid YAML (missing required fields, wrong types, invalid enum values) raises `ValidationError` with clear field-level messages
- `cycles` with circular `depends_on` references are rejected
- `quality_gates` with invalid `gate_id` (not in R1–R12) are rejected
- `cost_budget_usd` ≤ 0 is rejected
- `timeout_seconds` ≤ 0 is rejected

### §12.2 Benchmark Question Regression Tests

- Run Studio on all 10 benchmark questions in both modes (quick, deep)
- Verify all 10 outputs contain the ADR-01 four-feature backbone (4 sections present)
- Verify composite score ≥ 60 (per question, deep mode) — threshold calibrated at §9 time
- Verify R4 ≥ 4 and R5 ≥ 4 (per question, deep mode) — Studio differentiator gates
- Verify at least 1 competing frame in dissent section (per output)
- Verify at least 2 named scenarios with 3 sub-fields each (per output)
- Verify scope-limits has ≥1 entry per sub-category (per output)

### §12.3 Output Format Tests

- Brief word count falls within 3,500–8,500 band (deep mode)
- Deck slide count falls within 10–18 range
- Per-section word minimums met (§4.4 table)
- Register-check passes on all outputs (no drift markers)
- Invisible provenance mode: grep for "praxis" / "studio" / "Praxis" / "Studio" in rendered output returns 0 matches (text + metadata + HTML comments)
- All three rendering modes produce structurally distinct outputs from the same reasoning trace

### §12.4 Cost Budget Enforcement Tests

- Deep mode session cost ≤ $10.00
- Quick mode session cost ≤ $2.00
- Budget exhaustion triggers graceful degradation (partial result, not crash)
- Per-cycle cost tracking aggregates correctly to session total

### §12.5 A/B Harness Tests

- Harness runs both paths (single-agent, Studio) on a single benchmark question
- Both outputs are scorable against R1–R12
- Comparison report generates without error
- Anonymization checked: output labels stripped before evaluation

---

## §13 — Open Questions

| # | Question | Resolution Path | Blocking? |
|---|---|---|---|
| OQ-S1 | Should R13 Evidence Sourcing be re-admitted when Studio adds retrieval-grounded analysis? | Stage 7 decision after retrieval integration scoping | No (6.1) |
| OQ-S2 | Per-section minimum word counts in §4.4 — empirical values TBD at calibration time | §9 gate calibration pass against benchmark set | No (6.1), yes (6.4) |
| OQ-S3 | Register-check drift marker list — curated list TBD | Amelia (6.3) drafts initial list; Quinn (6.4) checks | No (6.1) |
| OQ-S4 | Consultancy reactions deferred on ADR-05/06/07 — how does this affect firm-voice rendering mode quality? | Stage 7 real-buyer consultancy interviews | No (6.1) |
| OQ-S5 | Quick mode quality floor — what composite score is acceptable when deep_analysis cycle is skipped? | Benchmark regression on quick mode at 6.4 time | No (6.1), yes (6.4) |

---

## §14 — Cross-Stage Integration Seams

### §14.1 C-1..C-5 from Stage 5.5 Alignment Review

Per D-5, the five cross-stage drifts identified at 5.5 are documented here as known integration seams:

| Drift | Description | Studio Impact | Resolution Timeline |
|---|---|---|---|
| C-1 | Pi-Mono label namespace convention drift between Stage 1 and Stage 4 | Studio inherits Stage 4 namespace; §11 metrics use `studio.*` prefix | Stage 7 normalization pass |
| C-2 | Memory `TaskSignature.input_hash` vs MAC `TaskInput` hashing inconsistency | Studio invokes MAC which handles the mapping; no Studio-level concern | Stage 7 |
| C-3 | Compression TONL passthrough (F-2 deferred from Stage 3) | Studio does not directly invoke compression; MAC handles via §10.4 adapter | Stage 7 optimization |
| C-4 | Memory promotion-path semantic mismatch (LATENT Stage-7 blocker) | Studio uses Memory via MAC's §8 learning loop; mismatch is invisible to Studio but becomes visible at Stage 7 when promotion logic is exercised | **Stage 7 — must be reconciled before production** |
| C-5 | AuditBuffer drain coordination (OQ-N resolved at Stage 4.7 via Path (i)) | Resolved; no Studio concern | Closed |

### §14.2 Stage 7 Debt Ledger Items Relevant to Studio

| # | Item | Source | Impact on Studio |
|---|---|---|---|
| DL-1 | PDF + `.pptx` export format | ADR-08 | Consultancy white-label workflow needs PDF; Stage 7.1 decision |
| DL-2 | "Built With Praxis" public dashboard badge | ADR-10 | Public-facing Studio demo asset; Stage 7.6 scope |
| DL-3 | A4 Spearman corroboration (ρ ≥ 0.6) | Stage 5.6 conditional | Headline numbers carry "(internal scoring; A4 deferred)" until ratified |
| DL-4 | Fractional C-suite operators as 4th segment | Mary §A.3 | Not represented in Studio templates; Stage 7 expansion |
| DL-5 | Real-buyer corroboration (Mary §D interview cycle) | Mary 6.0.1 | All Studio language decisions are HYPOTHETICAL until corroborated |
| DL-6 | C-4 Memory promotion semantic mismatch | Stage 5.5 | Must reconcile before production deployment |
| DL-7–DL-13 | Remaining Stage 5 debt items | Stage 5.5 debt ledger | See Pipeline.md §5.5 ratification |

### §14.3 Cleo WARNING Items (5, from Stage 5.3.5)

Five Cleo WARNINGs were deferred to Stage 7. None are Studio-blocking — they affect MAC implementation internals, not the Studio configuration layer.

---

## §E — Session-Close Audit

### §E.1 — Deliverable Checklist (Pipeline §6.1 checkboxes)

| # | Checkbox | Status |
|---|---|---|
| 1 | READS all 3 elicitation outputs BEFORE designing | ✓ Phase 1 complete |
| 2 | READS Tokonomics rounds as working examples | ✓ Phase 3 complete (all 5 rounds read) |
| 3 | Architecture doc at `studio/architecture.md` | ✓ This document |
| 4 | YAML workflow template schema | ✓ §2 (`WorkflowTemplate` Pydantic model) |
| 5 | `studio/strategic_session.yaml` specification ANCHORED on customer requirements | ✓ §3 (anchored on 11 ADRs) |
| 6 | Jinja2 output templates match empathy map | ✓ §4 (three rendering modes per ADR-02, ADR-05 dissent, ADR-06 scenarios, ADR-07 scope-limits, ADR-09 provenance, ADR-11 register) |
| 7 | A/B comparison harness design | ✓ §6 (three-path: single-agent, enhanced single-agent, Studio) |
| 8 | 10 benchmark question set | ✓ §7 (reused Stage 5 per D-2) |
| 9 | Context strategy executed per Pipeline §4.6 | ✓ D-7 (elicitation → MAC arch → Tokonomics → draft) |

### §E.2 — Inheritance Verification

- **§A.0 tokonomics firewall:** inherited and declared in §A.0. No tokonomics-era vocabulary in any customer-facing template specification.
- **ADR-01 through ADR-11:** all 11 ADRs addressed in §4 (templates) and §5 (quality gates). ADR-08/ADR-10 deferrals documented in §14.2 debt ledger.
- **`[HYPOTHETICAL]` flags:** propagated in §4.4 (brief length band), §10.1 (cost targets). All customer-facing content decisions remain hypothesized.
- **Segment weighting 50/30/20:** reflected in rendering-mode defaults (§2.2 `PROVENANCE_DEFAULTS`, §4.2 three-mode table).
- **Muted operator-realism register:** codified as §4.10 with enforcement via register-check.
- **Stage 5.6 caveat:** carried in §14.2 DL-3.

### §E.3 — Memory + Pipeline Discipline

- **No memory writes performed.** Proposed memory update (if any) deferred to team-lead disposition.
- **No Pipeline.md marks applied.** Pipeline §6.1 checkboxes to be updated by team-lead ratification flow.

### §E.4 — Handoff

**For Murat (6.2):** §12 testability notes provide test family structure. Key emphasis: benchmark regression tests on all 10 questions in both modes; ADR-01 four-feature backbone presence check; R4 ≥ 4 and R5 ≥ 4 differentiator gates; register-check pass/fail; invisible-mode leak tests.

**For Amelia (6.3):** implementation is primarily YAML + Jinja2 templates + a thin Python invoker (§2.5 `template_to_task_input`). The schema parser is the heaviest code component. Template files follow §4.3 structure. Register-check implementation follows §4.10.

**Signal:** 6.1 architecture ready for Murat and Amelia. Stage 7 depends on Studio being demo-ready at 6.6.

---
