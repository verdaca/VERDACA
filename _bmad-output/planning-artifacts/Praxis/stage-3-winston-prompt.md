# Stage 3 Launch Prompt — Winston (Architect) for Memory & Learning Layer

**Purpose:** Finalized prompt for Stage 3 — Memory & Cross-Session Learning (Beads + Mem0 + Atelier decision memory).
**Invocation:** `/bmad-agent-architect` then paste the prompt below.
**Prerequisite:** Stages 1-2 complete. Stage 3 builds the compounding advantage (every task makes future tasks cheaper).

---

## THE PROMPT (COPY-PASTE READY)

```
Design the Memory & Learning Layer for Praxis Stage 3.

## PROJECT CONTEXT

Stage 3 adds the COMPOUNDING ADVANTAGE. Unlike compression (which applies to
every task uniformly), memory-based learning makes repeated/similar tasks
progressively cheaper AND better. Target: 30-50% additional savings on
similar tasks via retrieval of prior approaches.

This stage is critical because it turns Praxis from "stateless agent runner"
into "self-improving system." Every workflow outcome becomes training data
for future workflows. This is what separates Praxis from every other agent
framework that starts from scratch on each task.

Build plan:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\praxis-build-plan.md

Stage 1 output (Pi-Mono — cost events flow through here):
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\pi-mono\architecture.md

Stage 2 output (Compression — persistent state gets compressed via Forge):
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\compression\architecture.md

## READ FIRST — REFERENCE IMPLEMENTATIONS

You will design 3 components that compose into a unified memory layer:

1. **Beads** (distributed versioned state)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\gastownhall-beads-8a5edab282632443.txt
   - Purpose: Hash-addressed versioned state, worktree isolation
   - Strategy: COPY/PORT (foundational, needs full control)

2. **Mem0** (hybrid vector + graph semantic memory)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\mem0ai-mem0-8a5edab282632443.txt
   - Purpose: 344x more efficient retrieval, three-axis scoping
   - Strategy: REFERENCE AS DEPENDENCY (pip install mem0ai)
   - 47K stars, mature, actively maintained — DO NOT FORK

3. **Atelier Decision Memory** (pgvector decision capture)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\robertsfeir-atelier-pipeline-8a5edab282632443.txt
   - Purpose: Capture WHY decisions were made, not just WHAT
   - Strategy: PATTERN EXTRACTION (re-implement in Python, don't copy wholesale)
   - Focus on: decision capture format, three-axis scoring, TTL-based decay

Pay particular attention to:
- How Mem0's three-axis scoping (user × agent × run) maps to Praxis sessions
- How Beads' hash-addressed state interacts with Forge's compaction
- How Atelier's decision capture differs from raw conversation history
- The research pattern from SiriuS (NeurIPS 2025): "experience libraries"

## STRATEGY SUMMARY

| Component | Strategy | Why |
|-----------|----------|-----|
| Beads | Copy-and-port | Foundational, needs full control |
| Mem0 | Reference as dependency (pip install mem0ai) | Mature, stable, 47K stars, Python-native |
| Atelier Decision Memory | Pattern extraction + new code | Re-implement for Praxis-specific semantics |

## PRAXIS REQUIREMENTS

### Functional Requirements

1. **Beads state versioning:** Every Praxis operation produces beads
   (versioned, hash-addressed, replayable snapshots). Worktree isolation
   per session so parallel agents don't conflict.

2. **Mem0 semantic memory integration:**
   - Three-axis scoping: user_id × agent_id × run_id
   - Hybrid vector + graph retrieval
   - Fact extraction from conversations
   - Provider-pluggable backends (default: pgvector)
   - Python dependency (pip install mem0ai)

3. **Atelier-style decision memory:**
   - Capture: decision, rationale, alternatives considered, evidence,
     confidence score, outcome (updated later when known)
   - Semantic search via pgvector
   - TTL-based decay (older decisions weighted lower)
   - Auto-capture hooks from the MAC (Stage 5 dependency)

4. **Cross-session retrieval API:**
   - Given a new task signature, retrieve top-K similar past tasks
   - Return: approach used, outcome quality, cost, reasoning trace
   - Seed Cycle 1 of future MAC iterations with this context

5. **Experience library pattern (SiriuS-inspired):**
   - After every workflow: capture (task_signature, approach,
     quality_score, cost) tuple
   - Build library that grows monotonically
   - Retrieval uses semantic similarity + outcome quality + recency

### Integration Requirements

6. **Pi-Mono integration:** Memory retrievals save tokens. Report savings
   as CostEvent with type=retrieval_cache_hit. Attribute savings to the
   workflow that benefited.

7. **Compression integration:** Beads state is large. Forge compaction
   applies to bead storage. TONL serialization applies to stored records.

8. **Unified query interface:** Praxis code should have ONE memory API,
   not three. Beads + Mem0 + Atelier decision memory are implementation
   details behind a unified Memory interface.

### Non-Functional Requirements

9. **Storage:** pgvector for Mem0 (default backend) + Atelier decision
   memory. SQLite acceptable for dev, Postgres for prod.

10. **Performance:** Retrieval queries < 100ms at p99 for 10K-record
    corpus. Scales to 100K records with proper indexing.

11. **Retention:** Beads state has retention policy (compact old, prune
    very old). Mem0 auto-manages. Atelier decisions have TTL-based decay.

12. **Test coverage:** >= 85% (Murat's gate). Focus on retrieval
    correctness, not performance micro-benchmarks.

## RISK CONTEXT

Memory corruption is subtle and catastrophic:

- **Wrong retrieval:** Agent uses a similar-but-wrong past approach.
  Quality degrades silently. Detection requires outcome tracking.
- **Stale decisions:** Old decisions based on obsolete facts get
  retrieved. TTL-based decay + recency weighting required.
- **Mem0 version drift:** Upstream Mem0 changes break our integration.
  Pin version, test on upgrade, abstract behind interface.
- **Beads state corruption:** Hash collision or version conflict
  corrupts replay. Hash-based collision prevention is mandatory.
- **Privacy leakage:** Cross-customer retrieval (if multi-tenant) leaks
  data. Scoping MUST be enforced at the query layer, not trusted to
  callers.
- **Retrieval cache poisoning:** Bad outcome written to memory causes
  future similar tasks to inherit the bad approach. Quality gates
  required before writing.

## DELIVERABLES

Produce an architecture decision document with these sections:

1. **Reference Analysis**
   - Beads patterns worth porting
   - Mem0 integration points (how we use it, not what we change)
   - Atelier decision memory patterns worth extracting

2. **Unified Memory Interface**
   - Single Python API surface (store, retrieve, query)
   - How the three underlying systems compose behind it
   - Scoping rules (user × agent × run × workflow × task)

3. **Beads Integration Design**
   - Module structure for Python port
   - State versioning mechanism
   - Worktree isolation semantics
   - Compaction interaction with Forge (Stage 2)

4. **Mem0 Integration Design**
   - Dependency pinning strategy
   - Backend configuration (pgvector default)
   - Three-axis scoping translation to Praxis concepts
   - Fact extraction pipeline

5. **Atelier Decision Memory Design**
   - Decision record schema (Pydantic models)
   - Capture protocol (when/what/how)
   - Retrieval scoring (semantic + recency + confidence)
   - TTL-based decay implementation

6. **Cross-Session Learning Protocol**
   - Task signature generation (how to hash a task for similarity matching)
   - Retrieval thresholds (when is a past task "similar enough"?)
   - Write-back protocol (when is an outcome good enough to record?)
   - Experience library growth policy

7. **Storage Schema**
   - Postgres tables / pgvector indices
   - SQLite dev equivalents
   - Migration approach

8. **Privacy & Scoping**
   - How multi-tenant scoping is enforced (not optional)
   - Data isolation guarantees
   - Audit trail for retrievals

9. **Observability Hooks**
   - Cache hit/miss rates
   - Retrieval latency distribution
   - Savings attribution (how much each retrieval saved)
   - OpenTelemetry integration

10. **Testability Notes for Murat**
    - Retrieval correctness tests
    - Privacy enforcement tests (multi-tenant isolation)
    - State versioning replay tests
    - Stale decision decay tests
    - Experience library growth simulation

11. **Open Questions**
    - Mem0 version pinning decisions
    - Decisions that need stakeholder input

## CONSTRAINTS

- Do NOT write implementation code (Amelia's job)
- Do NOT fork Mem0 (use it as dependency only)
- DO design the unified interface FIRST — the three underlying systems
  are implementation details
- DO make privacy/scoping enforcement non-bypassable by design

## OUTPUT LOCATION

Save your architecture document to:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\memory\architecture.md

## AFTER YOU FINISH

Signal readiness for Murat's test strategy review, then Amelia implementation.
Stage 4 (Agent Runtime) depends on this unified Memory interface.
```

---

## PRE-SALES CHECKPOINT

After Stage 3 completes, run the demonstration:

1. Ask Praxis a strategic question (record cost + time)
2. Wait (or change context)
3. Ask a SIMILAR strategic question
4. **Headline: "Second similar task used X% fewer tokens, Y seconds faster, because Praxis retrieved and reused the prior reasoning"**

This is the "compounding advantage" pre-sales asset. Record it as a GIF for the landing page.
