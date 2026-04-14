# Stage 4 Launch Prompt — Winston (Architect) for Agent Runtime

**Purpose:** Finalized prompt for Stage 4 — Agent Runtime (BMAD loader, Registry, Spawner, MCP adapter, Tool library).
**Invocation:** `/bmad-agent-architect` then paste the prompt below.
**Prerequisite:** Stages 1-3 complete. Stage 4 brings all 16 BMAD agents to life as runnable entities.

---

## THE PROMPT (COPY-PASTE READY)

```
Design the Agent Runtime Layer for Praxis Stage 4.

## PROJECT CONTEXT

Stages 1-3 built the foundation (measurement, compression, memory). Stage 4
brings BMAD agents to life as runnable Python entities. This is where the 16
specialized agents (Mary, Winston, Amelia, Quinn, etc.) become first-class
objects that can be spawned, coordinated, and tracked by Praxis.

Stage 4 builds ON TOP of Stages 1-3:
- Every agent action is cost-tracked (Pi-Mono)
- Every LLM call goes through compression (TONL/Forge/Caveman)
- Every agent outcome is memory-persisted (Beads/Mem0/Atelier)

Build plan:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\praxis-build-plan.md

Dependencies (your inputs):
- Pi-Mono: C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\pi-mono\architecture.md
- Compression: C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\compression\architecture.md
- Memory: C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\memory\architecture.md

## READ FIRST — REFERENCE IMPLEMENTATIONS

You will design 5 sub-components that compose into the Agent Runtime:

1. **BMAD Agent Manifest** (the source of truth for agent definitions)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad\_config\agent-manifest.csv
   - 16 agents with: name, displayName, title, icon, capabilities, role,
     identity, communicationStyle, principles, module, path, canonicalId
   - This is YOUR INPUT — you load from here, not define from scratch

2. **Atomic Agents** (Pydantic schema + DSPy auto-optimization patterns)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\brainblend-ai-atomic-agents-8a5edab282632443.txt
   - Strategy: PATTERN EXTRACTION (schemas) + REFERENCE (DSPy integration)
   - Focus on: single-purpose agents, schema composition, type safety

3. **Gas Town** (multi-agent coordination, session discovery, Polecat lifecycle)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\gastownhall-gastown-8a5edab282632443.txt
   - Strategy: PATTERN EXTRACTION (coordination design)
   - Focus on: agent spawning, escalation routing, session discovery (Seance),
     Polecat lifecycle (spawn → run → cleanup), ephemeral sessions

4. **Atelier Pipeline** (wave-based execution, parallel reviewer asymmetry)
   C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\src\robertsfeir-atelier-pipeline-8a5edab282632443.txt
   - Strategy: PATTERN EXTRACTION (wave execution, quality gates concept)
   - Focus on: Poirot/Robert/Sable parallel reviewer pattern, one-phase-per-turn

5. **MCP Protocol** (tool binding standard)
   Research the current MCP spec via Claude docs or Tavily search
   - Strategy: CLIENT INTEGRATION (standard protocol, no porting)
   - Focus on: tool discovery, sandboxed execution, result normalization

## STRATEGY SUMMARY

| Component | Strategy | Notes |
|-----------|----------|-------|
| Agent Loader | New Python code | Parse manifest CSV, build Pydantic models |
| Agent Registry | New Python code | Indexed by capability, LLM-matching fallback |
| Agent Spawner | Pattern from Gas Town | Subagent vs team mode, Polecat lifecycle |
| MCP Adapter | MCP client library + Python wrapper | Standard protocol |
| Tool Library | New curation | 20+ pre-wired MCP tools, categorized |

## PRAXIS REQUIREMENTS

### Functional Requirements

1. **Agent Manifest Loader:**
   - Parse `_bmad/_config/agent-manifest.csv` at startup
   - Build Pydantic AgentDefinition for each entry
   - Validate: no duplicate names, required fields present
   - Reload support for development

2. **Agent Registry:**
   - Indexed by capability tags (e.g., "architecture", "testing", "brainstorming")
   - Query API: `find_agents(task_description: str) -> List[Agent]`
   - LLM-based matching when text-only capability search is ambiguous
   - Confidence threshold for matches; fallback to human escalation

3. **Agent Spawner (two modes):**
   - **Subagent mode:** Spawn within current session, report back to parent
     (simpler, cheaper, no cross-agent messaging)
   - **Team mode:** Spawn as independent session, allow direct messaging
     between teammates (uses CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS pattern
     where applicable)
   - Polecat lifecycle: spawn → run → cleanup with guaranteed resource
     release

4. **MCP Tool Adapter:**
   - MCP client integration (use official Python SDK)
   - Curated tool registry (20+ tools at launch — see list below)
   - Sandboxed execution (tools cannot escalate privileges)
   - Result normalization to TONL/Pydantic format
   - Cost tracking per tool call (via Pi-Mono)

5. **Tool Library (20+ at launch):**
   - Web research: Tavily (search, extract, crawl, research)
   - Filesystem: Read, Write, Edit (bounded to workspace)
   - Code execution: Python sandbox, subprocess wrapper
   - Version control: GitHub MCP
   - Database: PostgreSQL MCP
   - Browser automation: Playwright MCP
   - Documentation: Context7 MCP
   - Communication: Slack, Discord webhooks
   - Observability: OpenTelemetry exporter
   - (expand per customer needs in later stages)

### Integration Requirements

6. **Pi-Mono integration:** Every agent invocation tracked by cost. Every
   tool call tracked by cost. Aggregated per session/workflow/agent.

7. **Compression integration:** Agent conversations flow through TONL/Forge/
   Caveman. Long agent sessions benefit from Stage 2's compaction.

8. **Memory integration:** Every agent outcome writes to Stage 3's unified
   Memory interface. Similar past invocations retrievable on spawn.

9. **Communication Bus:** Inter-agent messaging (for team mode) uses an
   append-only log (Beads-backed). Information asymmetry supported:
   reviewer agents CANNOT see production agents' reasoning trace.

### Non-Functional Requirements

10. **Agent spawn time:** < 500ms for subagent mode, < 2s for team mode.
11. **Resource budgets:** Pi-Mono enforces per-agent token budgets. Budget
    exceeded → escalation.
12. **Security:** Sandboxed tool execution. Per-agent tool allowlists. No
    access to secrets files (.env, .ssh, credentials).
13. **Test coverage:** >= 85% (Murat's gate).

## RISK CONTEXT

Agent runtime is foundational for Stages 5-7. Failures here cascade.

- **Agent spawn failure:** Must be rare AND recoverable. Transient errors
  → retry. Permanent errors → escalate with full context.
- **MCP tool hallucination:** LLM invents non-existent tools. Registry
  must be bounded, LLM must select from a whitelist (not generate names).
- **Information asymmetry violation:** If reviewer agent accidentally sees
  producer's reasoning, the multi-agent quality advantage collapses.
  Enforcement must be structural, not trusted.
- **Tool sandbox escape:** A tool execution that breaks out of sandbox =
  security incident. Per-tool allowlists + process isolation mandatory.
- **Circular spawning:** Agent A spawns Agent B which spawns Agent A →
  infinite recursion. Depth limit + cycle detection required.
- **Cross-session state leakage:** Agent in Session X reads state from
  Session Y (not scoped properly). Enforcement at runtime layer.
- **Resource exhaustion:** Runaway agent burns budget. Pi-Mono hard
  budget enforcement with termination.

## DELIVERABLES

Produce an architecture decision document with these sections:

1. **Reference Analysis**
   - Atomic Agents patterns to extract
   - Gas Town coordination patterns to extract
   - Atelier wave-execution patterns to extract
   - MCP client integration approach

2. **Agent Definition Schema**
   - Pydantic AgentDefinition model
   - Capability descriptor format
   - Validation rules
   - Extensibility (adding new BMAD agents later)

3. **Agent Registry Design**
   - Indexing strategy (capability tags + semantic search)
   - Query API
   - Matching algorithm (text-based + LLM fallback)
   - Confidence scoring

4. **Agent Spawner Design**
   - Subagent mode: lifecycle, parent-child relationship
   - Team mode: lifecycle, direct messaging, session discovery
   - Polecat cleanup guarantees
   - Resource budgets enforcement

5. **MCP Tool Adapter Design**
   - Client integration (official Python SDK)
   - Tool registry data model
   - Capability matching (which agent can use which tool)
   - Sandboxing mechanism
   - Error handling and retries

6. **Tool Library Catalog**
   - Initial 20+ tool list with descriptions
   - Per-tool permissions and typical callers
   - Adding new tools protocol

7. **Inter-Agent Communication Bus**
   - Message format
   - Routing (direct vs broadcast)
   - Information asymmetry enforcement (structural)
   - Append-only log semantics

8. **Integration Contracts**
   - How Pi-Mono receives agent events
   - How Memory receives agent outcomes
   - How Compression applies to agent conversations
   - How the MAC (Stage 5) consumes this runtime

9. **Security Model**
   - Sandbox boundaries
   - Tool allowlisting per agent
   - Secret isolation
   - Privilege escalation prevention

10. **Observability Hooks**
    - Agent lifecycle events
    - Tool invocation traces
    - Cost attribution per agent
    - Performance metrics

11. **Testability Notes for Murat**
    - Agent spawning lifecycle tests
    - Information asymmetry enforcement tests
    - Tool sandbox escape tests (red team style)
    - Circular spawning prevention tests
    - Resource budget enforcement tests

12. **Open Questions**
    - MCP version pinning
    - Python MCP SDK maturity checks
    - Decisions needing stakeholder input

## CONSTRAINTS

- Do NOT write implementation code (Amelia's job)
- Do NOT invent new tools — use MCP ecosystem
- DO design for the 16 BMAD agents specifically (not generic "any agent")
- DO make information asymmetry structural, not trusted
- DO design budget enforcement as non-bypassable

## OUTPUT LOCATION

Save your architecture document to:
C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\implementation-artifacts\praxis\runtime\architecture.md

## AFTER YOU FINISH

Signal readiness for Murat review (focus: security model, asymmetry
enforcement), then Amelia implementation.
```

---

## PRE-SALES CHECKPOINT

After Stage 4, demonstrate:
- "We have 16 specialized agents loaded and ready"
- "Each agent costs $X per task, measured in real-time"
- "Agents can coordinate in teams or as subagents"
- **Headline: "Praxis runs a 16-agent BMAD organization at ~$Y/workflow"**
