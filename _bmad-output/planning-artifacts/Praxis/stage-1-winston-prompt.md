# Stage 1 Launch Prompt — Winston (Architect) for Pi-Mono Cost Tracker

**Purpose:** Finalized prompt to invoke Winston as the first BMAD agent for Praxis Stage 1.
**Invocation:** `/bmad-agent-architect` then paste the prompt below.
**Language decision:** Python (see rationale at bottom).

---

## THE PROMPT (COPY-PASTE READY)

```
Design the Pi-Mono cost tracker module for Praxis Stage 1 (measurement foundation).

## PROJECT CONTEXT

I am building PRAXIS, a multi-agent reasoning engine that productizes the BMAD
framework. This is Stage 1 of a 7-stage build plan. Pi-Mono is the FIRST component
because every subsequent stage depends on it — we measure everything from inception
so the build process itself becomes a pre-sales case study (self-demonstrating savings).

Full build plan:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\praxis-build-plan.md

Technical architecture:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\box-core-architecture.md

Hybrid-of-best-approaches source analysis:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\hybrid-architecture-recommendations.md

## READ FIRST — REFERENCE IMPLEMENTATION

Primary reference (badlogic/pi-mono — TypeScript monorepo):
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\badlogic-pi-mono-8a5edab282632443.txt

Study the existing architecture carefully. Pay particular attention to:
- packages/ai/src/providers/*.ts — provider abstraction patterns (Anthropic,
  OpenAI, Google, Bedrock, Azure). The multi-provider pattern is production-tested;
  adapt it, don't reinvent.
- packages/agent/src/*.ts — agent loop integration, how cost tracking is wired
  into the request/response flow.
- packages/*/test/*.test.ts — test patterns for cost correctness, especially
  any property-based tests or golden files.

Do NOT copy the code. Understand the PATTERNS, then design the Praxis version
which will be ported to Python.

## STRATEGY: COPY-AND-PORT (Not Dependency)

Praxis OWNS this code. We extract proven patterns from badlogic/pi-mono and
adapt them to Praxis's specific needs. Upstream pi-mono updates do NOT flow in.
This module is the foundation every other Praxis component reports through,
so we need full control.

## LANGUAGE: PYTHON

Praxis is a Python codebase. Pi-Mono reference is TypeScript. Port the concepts,
don't translate line-by-line. Use Python-idiomatic patterns:
- Pydantic v2 for data models (not TypeBox)
- asyncio for async (not Promises)
- SQLAlchemy 2.0 for storage (not raw SQL clients)
- decimal.Decimal for ALL cost arithmetic (NEVER float)

## PRAXIS REQUIREMENTS (Module Must Support)

### Functional
1. Track input tokens, output tokens, cache tokens per request
2. Providers (launch set): Anthropic, OpenAI, Google Gemini
3. Extensible provider interface (Bedrock, Azure later)
4. Per-request, per-session, per-workflow, per-agent aggregation
5. Real-time cost as stream of events (for dashboards)
6. Historical queries by time range, agent, workflow, provider

### Non-Functional
7. All cost math in decimal.Decimal — NEVER float — billing-critical
8. Storage: SQLite for dev, Postgres-ready interface (async SQLAlchemy)
9. Zero runtime dependencies on other Praxis components (foundation layer)
10. <1ms overhead per tracked call (measurement must be cheap)
11. Test coverage >= 95% (per Murat's gate for high-risk components)

### API Surface (Minimum)
- `track_cost(request: LLMRequest, response: LLMResponse) -> CostRecord`
- `get_session_cost(session_id: str) -> CostSummary`
- `get_workflow_cost(workflow_id: str) -> CostSummary`
- `get_agent_cost(agent: str, time_range: TimeRange) -> CostSummary`
- `stream_events(filter: Filter) -> AsyncIterator[CostEvent]`
- `reconcile(provider_invoice: Invoice) -> ReconciliationReport`

## RISK CONTEXT

Murat flagged Pi-Mono at RPN 20 — the HIGHEST risk in the entire Praxis
architecture. The failure mode is "billing errors destroy trust permanently."
Specific failure patterns Murat called out:
- Floating-point cost calculations (the #1 killer — must use decimal.Decimal)
- Rounding errors on cache token pricing (10% of base rate)
- Async race conditions in concurrent cost aggregation
- Cross-provider price drift (provider pricing changes invalidate cached rates)
- Currency precision (fractions of a cent matter at scale)

Your design must make these failure modes IMPOSSIBLE, not just unlikely.

## DELIVERABLES

Produce an architecture decision document with these sections:

1. **Reference Analysis**
   - What WORKS in badlogic/pi-mono that we keep conceptually
   - What needs CHANGING for Praxis (list specific deltas)
   - What we DO NOT port (irrelevant to Praxis needs)

2. **Module Structure**
   - File layout (which modules, which responsibilities)
   - Package/import boundaries
   - Dependency direction rules

3. **Data Model**
   - Pydantic v2 models for: Provider, ModelPricing, LLMRequest, LLMResponse,
     CostRecord, CostSummary, CostEvent, TimeRange, Filter, ReconciliationReport
   - Relationships and invariants
   - Storage schema (SQLAlchemy mapped classes)

4. **API Surface Contracts**
   - Each public function: signature, pre/post conditions, error cases
   - Async vs sync decisions and rationale
   - Event streaming protocol

5. **Provider Abstraction**
   - Interface definition (Protocol class)
   - Per-provider responsibilities
   - How to add a new provider (extensibility contract)

6. **Cost Math Strategy**
   - Exact decimal.Decimal usage rules
   - Rounding policy (banker's rounding, context precision)
   - Currency handling
   - Cache token pricing formula
   - Explicit call-out of EVERY place floating-point would be tempting and why
     we avoid it

7. **Storage Strategy**
   - SQLite-to-Postgres interface
   - Migration approach
   - Indexing for time-range queries
   - Retention/archival policy

8. **Observability Hooks**
   - OpenTelemetry integration points
   - Log formats
   - Metrics exposed (Prometheus-compatible)

9. **Testability Notes for Murat**
   - What property-based tests should cover (Hypothesis library)
   - What golden file regression fixtures should exist
   - Reconciliation test strategy against real provider invoices
   - Edge cases to cover

10. **Open Questions**
    - Decisions that need stakeholder input
    - Assumptions that should be validated with real provider data

## CONSTRAINTS

- Do NOT write implementation code (that's Amelia's job)
- Do NOT write tests (that's Quinn's job after Murat designs the strategy)
- Do NOT make UI decisions (dashboard is Step 1.3, later in Stage 1)
- DO make every design decision traceable to a requirement or a risk

## OUTPUT LOCATION

Save your architecture document to:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\pi-mono\architecture.md

(Create the folder structure if it doesn't exist. This path is the convention
for all Praxis implementation artifacts per CLAUDE.md.)

## AFTER YOU FINISH

Signal that the design is ready for Murat's test strategy review. Murat will
add test gates based on your design, then Amelia will implement against both.
```

---

## HOW TO USE THIS PROMPT

1. **Verify billing is on Max, not API:**
   ```bash
   echo $ANTHROPIC_API_KEY    # must be empty
   claude login               # confirm Max credentials
   ```

2. **Invoke Winston:**
   ```
   /bmad-agent-architect
   ```

3. **Paste the prompt above** (everything between the triple-backtick lines).

4. **Expected Winston output:**
   - Architecture document at `_bmad-output/implementation-artifacts/praxis/pi-mono/architecture.md`
   - Typically 2000-4000 lines of design (thorough but no code)
   - Should take 15-30 minutes of interactive work

5. **When Winston finishes, invoke Murat next:**
   ```
   /bmad-tea
   ```
   Tell Murat: "Review Winston's Pi-Mono architecture at
   `_bmad-output/implementation-artifacts/praxis/pi-mono/architecture.md`. Design
   the test strategy per your risk-based methodology. Pi-Mono is RPN 20."

6. **After Murat, invoke Amelia:**
   ```
   /bmad-agent-dev
   ```
   Tell Amelia: "Implement Pi-Mono per Winston's architecture and Murat's test
   plan. Both are at `_bmad-output/implementation-artifacts/praxis/pi-mono/`."

---

## LANGUAGE DECISION RATIONALE

**Decision:** Python (not TypeScript, not polyglot).

**Why:**
1. **Mem0 is Python-native.** It's the only mature production dependency we're
   keeping as a library (not porting). Python avoids cross-language plumbing.
2. **BMAD agent ecosystem is Python-friendly.** DSPy, Pydantic, FastAPI, SQLAlchemy
   are best-in-class for the kernel layer.
3. **1-week target demands simplicity.** Polyglot (TS kernel + Python shell) adds
   2-3 days of plumbing complexity that steals from actual feature work.
4. **Target customers are Python-centric.** AI/ML teams, data scientists, devops
   — the primary buyers run Python stacks.

**Trade-off:** Porting Pi-Mono from TS to Python takes time. But it's a
high-fidelity translation of concepts, not line-by-line — and Winston will
guide the port to Python-idiomatic patterns.

**If you change your mind later:** The biggest cost is re-porting Pi-Mono,
TONL, Forge (days of work). Don't change after Stage 2 unless absolutely
necessary.
