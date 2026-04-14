# Stage 6 Launch Prompt — Winston (Architect) for Studio Workflow Template

**Purpose:** Finalized prompt for Stage 6 — First Workflow Template (Studio / Strategic Advisory).
**Invocation:** `/bmad-agent-architect` then paste the prompt below.
**Prerequisite:** Stages 1-5 complete. Stage 6 validates the whole platform on real strategic questions.

---

## THE PROMPT (COPY-PASTE READY)

```
Design the Studio Workflow Template (Strategic Advisory) for Praxis Stage 6.

## PROJECT CONTEXT

Stages 1-5 built the foundation, compression, memory, runtime, and reasoning
engine. Stage 6 produces the FIRST USER-FACING WORKFLOW. Studio is the
strategic advisory configuration — the one you've already been running
manually across 5 rounds of BMAD roundtables.

The goal: produce a YAML-defined workflow template that reproduces the
multi-agent strategic analysis we've demonstrated manually, but fully
automated. This becomes the first sellable Praxis configuration.

Build plan:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\praxis-build-plan.md

Dependencies (your inputs):
- Pi-Mono: C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\pi-mono\architecture.md
- Compression: C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\compression\architecture.md
- Memory: C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\memory\architecture.md
- Runtime: C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\runtime\architecture.md
- MAC: C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\mac\architecture.md

## READ FIRST — WORKING EXAMPLES

The best references for Studio workflow are the MANUAL BMAD sessions already
run. Study these as ground truth for what Studio should produce:

1. **Round 1: Initial strategy** (7 agents + 10 research)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Tokonomics\1st_Round_table.md

2. **Round 2: Deep strategy** (8 agents, 10 sessions, 25+ frameworks)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Tokonomics\2nd_Round_table.md

3. **Round 3: Competitive validation** (5 research agents)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Tokonomics\3rd_Round_table.md

4. **Round 4: Red team** (6 independent sessions — the MOST important one)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Tokonomics\4th_Round_table.md

5. **Business session:** (8 parallel sessions for GTM)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Tokonomics\business_session.md

Also reference the agent-to-process mapping:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\bmad-business-process-mapping.md
(Section: "Strategic Planning" under Tier 3 — which agents map to which roles)

Pay attention to:
- Which agents contributed to which rounds
- The "wide survey → deep analysis → red team → synthesis" pattern
- How information asymmetry (red team) catches things consensus misses
- Output formats (structured briefs, comparison tables, dissenting views)

## STRATEGY

Studio is NOT a new codebase — it is a CONFIGURATION over the MAC
(Stage 5). You design:

1. The YAML schema for workflow templates (general, reusable)
2. The Studio-specific YAML (first instance of that schema)
3. Output templates (Jinja2) for strategic briefs and decks
4. An A/B harness to compare Studio vs single-agent baseline

No new runtime code beyond the YAML schema parser (which is part of Stage 5's
MAC). Your job is primarily DESIGN THE SCHEMA, then express Studio as data.

## PRAXIS REQUIREMENTS

### Schema Requirements

1. **Workflow Template Schema (YAML):**
   - `name`, `product`, `description`, `version`
   - `inputs` block: parameter definitions with types, validation, defaults
   - `cycles` block: named cycles (cycle_1, cycle_2, cycle_3) with:
     - `budget_pct` (% of total budget allocated)
     - `agents` (list with roles, outputs, dependencies)
     - `parallel` flag (true/false)
     - `asymmetry` flag (review must be from different agent)
   - `quality_gates` block: list of gates with type (rule_based/retrieval/llm_judge)
     and per-gate criteria
   - `outputs` block: format, template path, visual template path

2. **Schema must support:**
   - Conditional cycle inclusion (skip a cycle for quick mode)
   - Agent dependency specification (B runs after A)
   - Output routing (which cycle outputs feed which later cycles)
   - Budget reallocation (unused budget rolls to next cycle)

### Studio-Specific Template Requirements

3. **Studio strategic_session.yaml must implement:**
   - **Cycle 1 — Wide Survey** (20% budget):
     - Mary: market research, competitive intel
     - Victor: strategic framing, disruption analysis
     - John: customer perspective, JTBD assessment
     - Parallel execution, outputs feed Cycle 2

   - **Cycle 2 — Deep Analysis** (50% budget):
     - Winston: technical feasibility (if technical component exists)
     - Dr. Quinn: risk analysis and contradictions
     - Carson: contrarian angles, reverse brainstorming
     - Dependencies on Cycle 1 outputs

   - **Cycle 3 — Red Team + Synthesis** (30% budget):
     - Dr. Quinn: adversarial red team (information asymmetry enforced)
     - Sophia: narrative synthesis with dissenting views preserved
     - Caravaggio: visual brief (token funnel, comparison tables)

4. **Quality Gates for Studio:**
   - `completeness`: all agents produced outputs
   - `dissent_present`: at least one agent disagreed with consensus
   - `evidence_grounded`: claims traceable to sources or reasoning
   - `actionable`: has concrete recommendations AND rejected alternatives
   - `red_team_addressed`: top 3 risks from Dr. Quinn are explicitly responded to

5. **Output Formats:**
   - Structured brief (Markdown via Jinja2 template)
   - Visual deck (HTML via Jinja2, exportable to PDF)
   - Executive summary (1 page)
   - Full analysis (10-20 pages)
   - Dissenting views section (always included, never summarized away)

### A/B Validation Requirements

6. **Baseline comparison harness:**
   - Given a strategic question, run:
     a) Single-agent: Claude with a prompt asking for strategic analysis
     b) Praxis Studio: full workflow
   - Measure for each: cost, time, output length, quality (blind eval rubric)
   - Produce comparison report

7. **Benchmark question set (10 questions):**
   - Sourced from real use cases (Tokonomics rounds are good examples)
   - Diverse: market entry, pricing, product strategy, competitive positioning,
     architecture decisions
   - Each has a "gold standard" answer from the manual BMAD process

8. **Evaluation rubric:**
   - Coverage (did it consider all angles?)
   - Risk identification (did it catch what red team catches?)
   - Actionability (are recommendations concrete and traceable?)
   - Dissent preservation (does the output maintain alternative views?)
   - Honesty (does it flag uncertainty where it exists?)

### Non-Functional Requirements

9. **Schema validation:** YAML must validate against the schema at load
   time. No runtime surprises.

10. **Workflow duration:** Studio session completes in < 10 min for quick
    mode, < 30 min for deep mode.

11. **Cost target:** Studio strategic session costs < $2 for quick mode,
    < $10 for deep mode.

12. **Test coverage:** >= 80% (Studio is configuration + Jinja2, lower
    gate than core components).

## RISK CONTEXT

Studio is the FIRST DEMO that customers will see. Failures here undermine
everything built in Stages 1-5.

- **Schema complexity:** YAML too complex = users can't configure. Too
  simple = can't express real workflows. Balance needed.
- **Agent orchestration bugs:** Wrong agent for the role, wrong cycle,
  wrong dependencies. Validation at load time is critical.
- **Quality gate miscalibration:** Gates too strict = valid outputs rejected.
  Too loose = bad outputs shipped. Calibrate against manual BMAD outputs.
- **Output format regression:** If outputs don't look like what we produced
  manually, the demo falls flat. Jinja2 templates must match the quality
  bar we already demonstrated.
- **Cost blowout:** Studio that costs $50/session is not sellable at
  $500-2000/session (we need 25-100× margin). Must stay <$10.
- **Dissent loss:** If synthesis smooths over disagreements, we lose the
  differentiation. Rubric must enforce dissent preservation.
- **A/B bias:** Comparison against single-agent must be blind and fair.
  Don't cherry-pick.

## DELIVERABLES

Produce an architecture decision document with these sections:

1. **Workflow Template Schema**
   - Full YAML schema definition (JSON Schema or Pydantic)
   - Validation rules
   - Extensibility (fields that can be added later without breaking existing templates)

2. **Studio strategic_session.yaml**
   - Full YAML template for the Studio strategic session workflow
   - Cycle-by-cycle agent assignments
   - Quality gates specification
   - Output format specifications
   - Budget allocation rationale

3. **Jinja2 Output Templates**
   - `brief.md.j2` — structured brief template (show structure)
   - `deck.html.j2` — visual deck template (show structure)
   - `executive_summary.md.j2` — 1-page summary template
   - Dissenting views section specification

4. **Alternative Workflow Variants**
   - `studio/strategic_session_quick.yaml` — quick mode (fewer cycles)
   - `studio/strategic_session_deep.yaml` — deep mode (extended cycles)
   - Configuration differences documented

5. **A/B Validation Harness**
   - Design of the comparison harness
   - Single-agent baseline prompt strategy
   - Metrics captured
   - Report format

6. **Benchmark Question Set**
   - 10 strategic questions with "gold standard" answers
   - Sourcing from Tokonomics rounds + others
   - Coverage of question types

7. **Evaluation Rubric**
   - Scoring dimensions
   - Weighting
   - Blind evaluation protocol

8. **Gate Calibration Plan**
   - How to tune gates against manual BMAD outputs
   - Calibration dataset
   - Iteration approach

9. **Output Quality Standards**
   - What "good output" looks like (with examples from Tokonomics rounds)
   - How to enforce via gates and templates
   - Dissent preservation enforcement

10. **Cost Model**
    - Predicted cost per workflow mode
    - Budget allocation rationale
    - Cost control levers

11. **Observability**
    - Metrics captured per Studio session
    - How session performance is tracked over time
    - User feedback loop (future: how customers rate outputs)

12. **Testability Notes for Murat**
    - Schema validation tests
    - Benchmark question regression tests
    - Output format tests
    - Cost budget enforcement tests
    - A/B harness validation tests

13. **Open Questions**
    - Template schema decisions needing stakeholder input
    - Calibration data sourcing

## CONSTRAINTS

- Do NOT write implementation code (Amelia's job — mostly YAML authoring
  and template implementation, minimal new Python)
- DO use the existing Tokonomics rounds as ground truth
- DO make the workflow schema GENERAL enough for Stages 7+ configurations
  (Factory, Shield, Pipeline, Ops) — don't hard-code Studio specifics
- DO design the A/B harness to be brutally fair — if Studio doesn't win
  by a large margin, we need to know

## OUTPUT LOCATION

Save your architecture document to:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\studio\architecture.md

## AFTER YOU FINISH

Signal readiness for Murat (benchmark + calibration design) and Amelia
(template authoring + Jinja2 templates).

Stage 7 (POV harness) depends on Studio being demo-ready.
```

---

## PRE-SALES CHECKPOINT

After Stage 6, you can book your first POV calls. The demo:

1. Take a strategic question the prospect is currently facing
2. Run it through Praxis Studio live
3. Show: cost ($1-10), time (minutes), output with dissenting views
4. Compare to what they would normally do (hire consultant for $X, wait weeks)

**Headline: "Praxis Studio delivered a 20-page strategic analysis with red team in 12 minutes for $3.47. Your consultant quote was $15,000."**

Outbound sales starts at Stage 6 completion.
