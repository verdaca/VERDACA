# Stage 5 Launch Prompt — Winston (Architect) for Meta-Agent Controller (MAC)

**Purpose:** Finalized prompt for Stage 5 — The MAC Reasoning Engine (task interpreter, plan decomposer, 3-cycle iterator, quality gates, asymmetry router, learning loop).
**Invocation:** `/bmad-agent-architect` then paste the prompt below.
**Prerequisite:** Stages 1-4 complete. Stage 5 is THE core differentiation — the reasoning engine that makes Praxis better than single-agent systems.

---

## THE PROMPT (COPY-PASTE READY)

```
Design the Meta-Agent Controller (MAC) for Praxis Stage 5.

## PROJECT CONTEXT — HIGHEST IMPORTANCE STAGE

Stage 5 is the CORE DIFFERENTIATION of Praxis. Stages 1-4 built the foundation
(cost tracking, compression, memory, agent runtime). The MAC is what turns
these into a reasoning ENGINE — the thing that makes Praxis output genuinely
better than a single Claude call for the same problem.

If the MAC fails to deliver measurable quality improvement over a single-agent
baseline, Praxis has no business model. This is the stage where the claim
"multi-agent deliberation beats single-agent" must become PROVABLE.

Research foundation (from Round 5 analysis and web research):
- Self-Refine (Madaan, NeurIPS 2023): ~20% improvement via iteration
- MetaAgent (ICML 2025): FSM-based plan decomposition with backtracking
- SiriuS (NeurIPS 2025): experience libraries for self-improvement
- Tree of Thoughts (Yao, NeurIPS 2023): branching candidate exploration
- Multi-agent debate research: 5-23pp improvements with proper design
- Information asymmetry reviewer pattern (Atelier): catches what single-agent misses

Build plan:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\praxis-build-plan.md

Research context:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\box-core-architecture.md
(see "Best-of-Class Patterns Baked In" section)

Dependencies (your inputs):
- Pi-Mono (cost discipline, budget enforcement per cycle):
  C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\pi-mono\architecture.md
- Compression (Forge preserves reasoning chains across cycles):
  C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\compression\architecture.md
- Memory (retrieve past solutions as Cycle 1 seeds; write outcomes as learning):
  C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\memory\architecture.md
- Runtime (agent spawning, information asymmetry routing, tool binding):
  C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\runtime\architecture.md

## READ FIRST — REFERENCE IMPLEMENTATIONS

Stage 5 is mostly NEW DESIGN (no single reference implementation exists for
MACs). But these references contribute specific patterns:

1. **Atelier Pipeline** (quality gates + wave execution)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\robertsfeir-atelier-pipeline-8a5edab282632443.txt
   - Strategy: PATTERN EXTRACTION
   - Focus on: 12 quality gates implementation, wave-based phases,
     one-phase-per-turn, mechanical enforcement hooks, information asymmetry

2. **Forge Agent Loop** (reasoning chain preservation)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\antinomyhq-forgecode-8a5edab282632443.txt
   - Strategy: PATTERN EXTRACTION
   - Focus on: three agent modes (sage/muse/forge), reasoning block
     preservation across compaction events

3. **Gas Town** (multi-agent orchestration under load)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\gastownhall-gastown-8a5edab282632443.txt
   - Strategy: PATTERN EXTRACTION
   - Focus on: escalation routing, session continuity

Study these carefully. The MAC integrates patterns from multiple sources —
it is not porting any single system.

## CORE ARCHITECTURE: THE 3-CYCLE ITERATION PATTERN

The MAC's central contribution is the 3-cycle iteration pattern:

**CYCLE 1 — Wide + Shallow (budget: ~20%)**
- Generate 2-3 candidate approaches in parallel
- Evaluate with CHEAP quality gates (rule-based)
- Retrieve similar past tasks from Memory (Stage 3)
- Select best candidate, SAVE alternatives as backtrack options

**CYCLE 2 — Narrow + Deep (budget: ~60%)**
- Execute the selected candidate with full agent team
- Run through WAVE-based phases (Atelier pattern)
- Each phase has its own quality gates
- Backtrack to alternatives if a phase fails

**CYCLE 3 — Verify (budget: ~20%)**
- Run all 12 quality gates against final output
- Information asymmetry: reviewer agents evaluate independently
- If passes: commit outcome + reasoning trace to Memory (experience library)
- If fails: backtrack to Cycle 2 alternatives OR escalate to human

This is deliberately inspired by chess engine iterative deepening +
Self-Refine + Tree of Thoughts, but ADAPTED for business reasoning
(no perfect state representation, so tree search is bounded and the
value function is retrieval-augmented, not learned).

## PRAXIS REQUIREMENTS

### Functional Requirements

1. **Task Interpreter**
   - Parse natural language task description
   - Extract: goal, constraints, success criteria, deliverable type, budget
   - Map to known workflow templates if pattern match exists
   - Fallback: ask clarifying questions via a dedicated interpreter agent

2. **Plan Decomposer (FSM-based, MetaAgent pattern)**
   - Build task DAG with typed nodes (research, design, execute, validate, synthesize)
   - Each node: agent assignment, inputs, outputs, quality criteria
   - Backtracking edges from failure states to prior nodes
   - Plan repair: if a node fails, repair rather than regenerate full plan
   - Validation: plan must be executable, not just plausible

3. **3-Cycle Iteration Controller**
   - Implement the wide → narrow → verify pattern above
   - Budget allocation: configurable per workflow template
   - Cycle transition gates (cannot advance until current passes)
   - Backtracking state management (Beads-persisted alternatives)
   - Parallelism within cycles where safe (Cycle 1 candidate generation)

4. **Quality Gate Engine (Atelier 12-gate pattern)**
   - Tier 1 CHEAP: rule-based gates (format, schema, completeness)
     Examples: JSON validates, required fields present, length constraints
   - Tier 2 MEDIUM: retrieval comparison via Memory
     Example: "does this match known-good patterns from similar past tasks?"
   - Tier 3 EXPENSIVE: LLM-as-judge (only when Tiers 1-2 ambiguous)
     Example: "is this argument coherent and well-supported?"
   - Each gate is CONFIGURABLE per workflow template
   - Gates emit events to Pi-Mono (which gates passed, which failed, cost)

5. **Information Asymmetry Router**
   - Given a review task, routes to a different agent than producer
   - Reviewer does NOT see production agent's reasoning trace
   - Structural enforcement (not trusted to callers)
   - Parallel reviewer pattern: Poirot/Robert/Sable style from Atelier

6. **Cross-Session Learning Loop**
   - After every workflow completion, capture:
     (task_signature, approach, outcome, quality_score, cost, reasoning_trace)
   - Write to Memory (Stage 3) as new experience library entry
   - On new task: retrieve top-K similar entries, seed Cycle 1 with
     their winning approaches as starting candidates
   - Closed loop: every task makes future similar tasks faster + better

### Integration Requirements

7. **Pi-Mono integration:** Budget enforcement per cycle. Auto-escalation
   on gate failure (try more expensive tier). Hard stop if total budget
   exceeded.

8. **Memory integration:** Experience library reads (Cycle 1 seeding) and
   writes (after Cycle 3). Uses Stage 3's unified Memory interface.

9. **Runtime integration:** All agent spawning via Stage 4's runtime.
   Information asymmetry enforced via Runtime's communication bus.

10. **Compression integration:** Reasoning chains preserved across Forge
    compactions (critical — Cycle 2 often produces long traces that get
    compacted, but MAC must retrieve them in Cycle 3 verification).

### Non-Functional Requirements

11. **Quality must be MEASURABLE vs single-agent baseline.** Every MAC
    execution must be comparable to "what would Claude-solo have produced?"
    Target: consistent +15-25% quality improvement on strategic questions.

12. **Cost must be PREDICTABLE.** Given a task and workflow template,
    you can pre-estimate cost with ±20% accuracy via Pi-Mono's
    historical data.

13. **Latency budgets:** Interactive workflows complete in <5 min.
    Heavy analysis workflows complete in <30 min.

14. **Test coverage:** >= 90% (highest gate for the highest-risk component).

## RISK CONTEXT — THIS IS THE DIFFERENTIATION

Failure modes specific to the MAC (ranked by severity):

- **No measurable quality improvement:** If MAC output is not demonstrably
  better than single-agent, the product has no differentiation. MUST have
  blind evaluation harness.
- **Runaway cost from unbounded iteration:** Cycles that don't terminate
  burn money. Hard budget enforcement + max iteration count.
- **Information asymmetry violation:** Reviewer sees producer reasoning.
  Silent failure — output quality degrades invisibly. Structural fix.
- **Plan decomposer hallucination:** LLM generates plans referring to
  non-existent agents or tools. Validation against Registry required.
- **Gate false positives:** Valid output rejected. Need calibration
  against ground truth.
- **Gate false negatives:** Invalid output accepted. The more dangerous
  class — causes downstream failure cascades.
- **Experience library poisoning:** Low-quality outcomes retrieved as
  Cycle 1 seeds. Quality threshold required before write-back.
- **Backtrack explosion:** Too many alternatives stored, memory bloat.
  Limit backtrack depth.
- **Convergence to consensus:** Debate collapses into agreement
  (conformity pressure). Anti-conformity reasoning pattern required.

## DELIVERABLES

Produce an architecture decision document with these sections:

1. **Research Foundation Review**
   - Which patterns from each cited research paper we use
   - What we adapt vs accept as-is
   - Key differences between research demos and production MAC

2. **Overall MAC Architecture**
   - Component diagram
   - Data flow through 3 cycles
   - State management (what persists across cycles)
   - Failure recovery paths

3. **Task Interpreter Design**
   - Input format (natural language + optional structured hints)
   - Output: structured Task object (Pydantic)
   - Clarification protocol when ambiguous
   - Mapping to workflow templates

4. **Plan Decomposer Design**
   - FSM semantics (nodes, edges, states)
   - DAG construction algorithm
   - Plan validation (references only real agents and tools)
   - Plan repair logic on failure

5. **3-Cycle Iteration Controller**
   - State machine per cycle
   - Budget allocation and enforcement
   - Transition gates
   - Backtracking mechanism (Beads-persisted alternatives)
   - Parallelism rules (when safe, when not)

6. **Quality Gate Engine**
   - 12-gate catalog (per Atelier pattern)
   - Three-tier evaluation (rule/retrieval/LLM-judge)
   - Per-workflow configuration
   - Gate calibration protocol

7. **Information Asymmetry Router**
   - Structural enforcement mechanism
   - Producer/reviewer separation
   - Parallel reviewer orchestration
   - Conflict resolution when reviewers disagree

8. **Cross-Session Learning Loop**
   - Task signature generation
   - Write-back criteria (quality threshold)
   - Seed retrieval protocol for Cycle 1
   - Experience library growth policy
   - Anti-poisoning safeguards

9. **Evaluation Harness**
   - Single-agent baseline comparison design
   - Blind evaluation protocol
   - Quality scoring rubric
   - Benchmark task suite

10. **Integration Contracts**
    - With Pi-Mono (cost events, budget enforcement)
    - With Memory (experience library, decision capture)
    - With Runtime (agent spawning, information asymmetry)
    - With Compression (reasoning chain preservation)

11. **Observability Hooks**
    - Per-cycle metrics
    - Gate pass/fail rates
    - Iteration depth distribution
    - Cost per workflow type
    - Quality improvement tracking

12. **Testability Notes for Murat**
    - Property tests for cycle state machine
    - Backtracking correctness tests
    - Information asymmetry enforcement tests
    - Gate calibration test suite
    - End-to-end evaluation harness tests
    - Adversarial tests (can we trick the MAC into producing bad output?)

13. **Open Questions**
    - Which research pattern trade-offs need stakeholder input
    - Gate calibration data requirements

## CONSTRAINTS

- Do NOT write implementation code (Amelia's job)
- Do NOT claim capabilities the research doesn't support (ARC-AGI-3 is
  still 0.37% — don't promise novel reasoning breakthroughs)
- DO design for MEASURABLE quality improvement, not promised improvement
- DO make cost predictability a first-class concern
- DO document the evaluation harness thoroughly — it's how we prove
  the business case

## OUTPUT LOCATION

Save your architecture document to:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\mac\architecture.md

## AFTER YOU FINISH

Signal readiness for Murat (this will be the most intensive test design
in the project — the MAC has the highest risk), then Amelia implementation.

Stage 6 (first workflow template) depends on this being rock-solid.
```

---

## PRE-SALES CHECKPOINT

After Stage 5, run the killer demonstration:

1. Take 10 real strategic questions (from Tokonomics rounds, easy to source)
2. Run each through single-agent (just Claude with prompt)
3. Run each through Praxis MAC
4. Blind evaluation by a third party (or structured rubric)

**Headline: "Praxis MAC beats single-agent by X% on strategic questions, at Y× cost"**

This is the moment Praxis graduates from "interesting architecture" to "demonstrably superior product."
