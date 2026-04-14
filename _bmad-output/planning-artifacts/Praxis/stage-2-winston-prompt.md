# Stage 2 Launch Prompt — Winston (Architect) for Compression Layer

**Purpose:** Finalized prompt for Stage 2 — Token Compression Quick Wins (TONL + Forge + RTK + Caveman).
**Invocation:** `/bmad-agent-architect` then paste the prompt below.
**Prerequisite:** Stage 1 (Pi-Mono) must be complete. Stage 2 measures ALL savings against Pi-Mono baseline.

---

## THE PROMPT (COPY-PASTE READY)

```
Design the Compression Layer for Praxis Stage 2 (Token Compression Quick Wins).

## PROJECT CONTEXT

Stage 2 adds three compression layers on top of Stage 1's Pi-Mono measurement
foundation. Every compression added = measurable savings captured in Pi-Mono
= pre-sales asset. Target: 65-75% compound token reduction vs baseline.

Build plan:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\praxis-build-plan.md

Architecture context:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\box-core-architecture.md

Stage 1 output (Pi-Mono architecture — your dependency):
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\pi-mono\architecture.md

## READ FIRST — REFERENCE IMPLEMENTATIONS

You will design 4 components that compose into a compression pipeline:

1. **TONL** (tokenizer-aware serialization, JSON replacement)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\tonl-dev-tonl-8a5edab282632443.txt
   - Target savings: 32-45% on payloads
   - Strategy: COPY/PORT from TypeScript to Python

2. **Forge** (zero-cost deterministic compaction)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\antinomyhq-forgecode-8a5edab282632443.txt
   - Target: replace LLM-based compaction (which costs tokens) with deterministic
   - Critical: reasoning chain preservation across compactions
   - Strategy: COPY/PORT to Python

3. **RTK** (transparent CLI output compression proxy)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\rtk-ai-rtk-8a5edab282632443.txt
   - Target savings: 89% on CLI command outputs
   - Implementation: Rust binary with shell hook interception
   - Strategy: KEEP AS RUST BINARY, build Python wrapper for integration

4. **Caveman** (LLM output compression)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\juliusbrussee-caveman-8a5edab282632443.txt
   - Target savings: 75% on LLM prose output
   - Small codebase (210KB) — fully portable
   - Strategy: COPY/PORT to Python

Study all four. Pay attention to:
- Composition order (which layer applies first? how do they interact?)
- Where each layer integrates (request side vs response side)
- Quality preservation mechanisms (what does each protect?)
- Fail-safe behavior (what happens if compression corrupts data?)

## STRATEGY SUMMARY

| Component | Strategy | Language |
|-----------|----------|----------|
| TONL | Copy-and-port | Python (from TS) |
| Forge | Copy-and-port | Python (from TS) |
| RTK | Reference as Rust binary | Rust (unchanged) + Python wrapper |
| Caveman | Copy-and-port | Python (from source language) |

RTK is the only non-Python component. Design a clean subprocess boundary so
Python can invoke the RTK binary transparently (via shell hooks) without
language leakage into the main codebase.

## PRAXIS REQUIREMENTS

### Functional Requirements

1. **TONL replaces JSON for all internal data movement** between Praxis
   components. Anthropic, OpenAI, Gemini tokenizer-aware encoding (5-15%
   additional tokenizer-specific savings).
2. **Forge performs deterministic compaction** when conversations exceed
   token thresholds. Two-tier triggers: token_threshold AND max_messages.
   Retention window: last 6 messages NEVER compacted. Reasoning chain
   preservation is MANDATORY.
3. **RTK intercepts CLI output** transparently via shell hooks. Agents do
   not know RTK exists. 100+ supported commands (git, npm, cargo, pytest,
   docker, etc.). Flag-aware: `--verbose` preserves detail.
4. **Caveman compresses LLM prose output** post-generation. 6 intensity
   levels (lite → ultra). Multi-dialect support (caveman, 文言文, etc.).
   Safety circuit breaker: if compression fails validation, fall back to
   original.

### Integration Requirements

5. **Pipeline composition:** Design the order TONL → (request) → LLM →
   (response) → Caveman → RTK (on CLI outputs). Forge runs orthogonally
   when conversation size triggers it.
6. **Pi-Mono integration:** Every compression operation reports savings
   (tokens_before, tokens_after, bytes_saved, cost_delta) to Pi-Mono as
   a CostEvent with type=compression.
7. **Quality preservation:** Each component needs a quality circuit breaker.
   If validation fails, fall back to uncompressed with an alert logged.
8. **A/B benchmark harness:** Must be runnable on demand. Given a workload,
   run with compression ON vs OFF, capture Pi-Mono deltas, produce a
   savings report.

### Non-Functional Requirements

9. **Zero-cost guarantee for Forge:** Forge must NOT invoke an LLM for
   compaction. Deterministic rules only.
10. **RTK latency:** <10ms per command output (per existing benchmark).
11. **TONL streaming:** O(1) memory for large payloads.
12. **All components use Pi-Mono `decimal.Decimal` cost tracking** (inherit
    from Stage 1).
13. **Test coverage:** >= 85% (per Murat's gate for compression components).

## RISK CONTEXT

Murat flagged Forge and Caveman at RPN 15, HTTP Proxy (RTK) at RPN 12.
Specific failure patterns to design against:

- **Caveman over-compression corrupts code:** Cannot tell LLMs to write code
  "tersely." Model non-compliance is non-deterministic. MUST detect this
  class of failure and fall back.
- **Forge reasoning chain break:** If compaction drops a critical reasoning
  step, later agent turns lose context. Explicit preservation of reasoning
  blocks is mandatory.
- **TONL lossy serialization:** Perfect round-trip is REQUIRED. Any lossy
  field encoding is a bug.
- **RTK transparency violation:** If RTK's presence is visible to agents
  (via different output format), it breaks the invariant that compression
  is invisible.
- **Tokenizer drift:** Provider tokenizers change. TONL's tokenizer-aware
  encoding must version-pin and validate.
- **Cascading failures:** If TONL fails, Forge gets garbage input. If
  Caveman fails, downstream consumers get garbage. Cascade isolation
  needed.

## DELIVERABLES

Produce an architecture decision document with these sections:

1. **Reference Analysis (per component)**
   - What works in each upstream reference
   - What needs changing for Praxis
   - What we do not port

2. **Pipeline Composition**
   - ASCII diagram of the compression pipeline
   - Order of operations (request path vs response path)
   - Where Forge orthogonally triggers
   - Where RTK intercepts

3. **Per-Component Design**
   - TONL: module structure, API, tokenizer adapter protocol
   - Forge: compaction algorithm, retention rules, trigger logic
   - RTK: Rust binary interface, Python wrapper, shell hook mechanism
   - Caveman: compression rules, intensity levels, fallback protocol

4. **Integration Contracts**
   - How Pi-Mono receives compression events
   - How agents see (or don't see) compression layers
   - Configuration surface per component

5. **Quality Preservation Strategy**
   - Circuit breaker design per component
   - Validation approach (how do we know compression is safe?)
   - Fallback behavior and alerting

6. **A/B Benchmark Harness**
   - Design the harness that produces savings reports
   - What metrics are captured
   - How reports feed the "Built With Praxis" dashboard

7. **Storage & Versioning**
   - Tokenizer version pinning
   - Rule set versioning (Caveman dialects)
   - Migration when rules change

8. **Observability Hooks**
   - What events each component emits
   - How savings are attributed to workflows/agents
   - OpenTelemetry integration points

9. **Testability Notes for Murat**
   - Round-trip property tests for TONL (Hypothesis)
   - Golden file regression for Forge compaction
   - Quality preservation tests for Caveman (input/output pairs)
   - RTK performance benchmarks
   - Integration test: full pipeline on real workloads

10. **Open Questions**
    - Decisions that need stakeholder input
    - Unknowns from reference code that may affect porting

## CONSTRAINTS

- Do NOT write implementation code (Amelia's job)
- Do NOT write tests (Murat + Quinn's job)
- DO make every design decision traceable to a requirement or risk
- DO explicitly document the RTK polyglot boundary (the only non-Python part)
- DO design for COMPOUND savings measurement — the headline number is
  "compression layers combined deliver X%" not isolated numbers

## OUTPUT LOCATION

Save your architecture document to:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\compression\architecture.md

(Create the folder structure if it doesn't exist.)

## AFTER YOU FINISH

Signal readiness for Murat's test strategy review. Murat will design gates
based on your architecture, focusing on quality preservation circuit breakers
and round-trip property tests. Then Amelia implements against both documents.
```

---

## HOW TO USE THIS PROMPT

1. Verify Stage 1 is complete (Pi-Mono architecture exists at the expected path)
2. Verify billing is on Max: `echo $ANTHROPIC_API_KEY` (must be empty)
3. Invoke Winston: `/bmad-agent-architect`
4. Paste the prompt above
5. After Winston delivers → invoke Murat (`/bmad-tea`) → then Amelia (`/bmad-agent-dev`)

## PRE-SALES CHECKPOINT

After Stage 2 completes, update the "Built With Praxis" dashboard with:
- TONL savings (delta vs JSON baseline)
- Forge compaction events and token savings
- Caveman prose compression percentage
- RTK CLI output compression percentage
- **Headline: "Three compression layers combined deliver X% total token reduction"**

This is the first genuine pre-sales asset. Write a blog post about it.
