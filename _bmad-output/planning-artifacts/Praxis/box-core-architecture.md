# The Box: Core Architecture for Pre-Built Agentic Delivery Platform

**Date:** 2026-04-12
**Purpose:** Build the core ahead of demand. When the first POV request lands, deliver in days, not weeks.
**Strategy:** One core, five product shells. Configuration over code. Best-of-class as of April 2026.

---

## EXECUTIVE SUMMARY

The Box is a **5-layer agentic platform** built once, then specialized per product configuration via thin shells. When a POV request arrives, the workflow is configured (not coded), MCP tools are bound (not built), and delivery happens in 3-7 days instead of 6-8 weeks.

**Build sequence:**
- **Weeks 1-3:** Kernel (foundation + persistence)
- **Weeks 4-5:** Agent Runtime (BMAD agent loader + spawning)
- **Weeks 6-8:** MAC (Meta-Agent Controller with 3-cycle reasoning)
- **Weeks 9-10:** MCP Adapter + Tool Registry
- **Week 11:** First Workflow Template (Studio — strategic advisory)
- **Week 12:** POV Playbook + delivery harness

**Total: 12 weeks to ship-ready core. POV delivery: 3-7 days per engagement.**

---

## DESIGN PRINCIPLES

1. **Build once, configure many.** All product variations are configuration over the same kernel — never duplicate code.
2. **Best-of-class today.** Use the latest 2026 patterns: MCP for tools, Self-Refine for iteration, MetaAgent FSM for orchestration, Mem0 for memory, Pi-Mono for cost discipline.
3. **POV-ready, not perfect.** Optimize for time-to-first-deployment, not for hypothetical future scale.
4. **Boring infrastructure.** Postgres, Redis, Python — not exotic stacks. Boring scales.
5. **Observability first.** Every decision is logged, every cost is tracked, every output is replayable.
6. **Human-in-the-loop is a feature.** Quality gates that escalate to humans are NOT a fallback — they ARE the value proposition.

---

## THE 5-LAYER ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 5: PRODUCT SHELLS (Last-Mile, Per Configuration)          │
│ Studio · Factory · Shield · Pipeline · Ops                      │
│ Web UI, billing, integrations, branding, output templates       │
└─────────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 4: WORKFLOW TEMPLATES (Configuration, Not Code)           │
│ YAML-defined orchestrations · Agent recipes · Quality gates     │
│ Per-product workflows reusing the same MAC engine               │
└─────────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: META-AGENT CONTROLLER (The Reasoning Engine)           │
│ Task interpreter · Plan decomposer · 3-cycle iterator           │
│ Quality gate engine · Backtracking · Information asymmetry      │
└─────────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: AGENT RUNTIME (Reusable Across All Products)           │
│ BMAD agent loader · Registry · Spawning · Communication         │
│ MCP tool binding · Sandboxed execution · Result normalization   │
└─────────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: KERNEL (Always-On Foundation)                          │
│ TONL serialization · Pi-Mono cost tracking · Beads state        │
│ Mem0 semantic memory · Forge compaction · RTK CLI compression   │
└─────────────────────────────────────────────────────────────────┘
                            ▲
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 0: INFRASTRUCTURE                                          │
│ Postgres + pgvector · Redis · Anthropic/OpenAI/Gemini APIs      │
│ Python 3.12 · FastAPI · Docker · OpenTelemetry                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## LAYER 1: THE KERNEL

**Purpose:** Always-on substrate. Every agent operation flows through it.

### Components

#### 1.1 TONL Serialization Layer
- Replaces JSON for all internal data movement
- 32-45% token savings on LLM payloads
- Tokenizer-aware encoding (5-15% additional, model-specific)
- Streaming for large payloads (O(1) memory)
- **Module:** `kernel/serialization/tonl.py`
- **Status:** Reuse from existing TONL project

#### 1.2 Pi-Mono Cost Tracker
- Real-time token cost tracking per request, per agent, per workflow
- Thinking budgets: 128 / 256 / 1024 / 4096 / 8192+ tokens
- Auto-escalation on quality gate failure
- Provider-aware pricing (Opus, Sonnet, Haiku, GPT-5, Gemini 3)
- **Module:** `kernel/cost/pi_mono.py`
- **Critical:** Use `decimal.Decimal` for ALL cost calculations (Murat's failure pattern #3)

#### 1.3 Beads Versioned State
- Every intermediate result is a "bead" — versioned, hash-addressed, replayable
- Dolt-backed for distributed state
- Hash-based collision prevention
- Worktree isolation per session
- **Module:** `kernel/state/beads.py`
- **Storage:** Postgres + Dolt

#### 1.4 Mem0 Semantic Memory
- Hybrid vector + graph memory
- 344x more efficient than alternatives
- Three-axis scoping: `user_id × agent_id × run_id`
- LLM fact extraction from conversations
- **Module:** `kernel/memory/mem0_adapter.py`
- **Storage:** pgvector (default) — pluggable to other backends

#### 1.5 Forge Zero-Cost Compaction
- Deterministic compaction (no LLM inference cost)
- Two-tier triggers: token threshold + max messages
- Retention window: last 6 messages never compacted
- **Critical:** Reasoning chain preservation across compactions
- **Module:** `kernel/compaction/forge.py`

#### 1.6 RTK CLI Compression Proxy
- 89% reduction on CLI command outputs
- Transparent — agents don't know it exists
- Rust-implemented for <10ms overhead
- 100+ supported commands
- **Module:** `kernel/proxy/rtk/` (Rust binary)

### Kernel API Surface

```python
# kernel/__init__.py
from kernel import Box

box = Box(
    storage="postgresql://...",
    memory_backend="pgvector",
    cost_tracker=True,
    compaction="forge",
)

# Every operation through the box
result = await box.run(workflow="studio.strategic_session", inputs={...})
print(result.cost, result.tokens, result.beads, result.trace_id)
```

---

## LAYER 2: THE AGENT RUNTIME

**Purpose:** Load BMAD agents from the manifest, spawn them safely, route them to tools.

### Components

#### 2.1 Agent Manifest Loader
- Reads `_bmad/_config/agent-manifest.csv` (16 BMAD agents)
- Loads persona, principles, communication style, capabilities
- Builds capability descriptors (Pydantic schemas)
- **Module:** `runtime/agents/loader.py`

#### 2.2 Agent Registry
- Indexed by capability (which agents can do which tasks)
- LLM-based matching for novel task descriptions
- Fallback: human escalation if no match above confidence threshold
- **Module:** `runtime/agents/registry.py`

#### 2.3 Agent Spawner
- Creates isolated agent sessions (Gas Town pattern)
- Subagent vs. team mode (single task vs. multi-agent collaboration)
- Polecat lifecycle: spawn → run → cleanup
- Resource budgets enforced via Pi-Mono
- **Module:** `runtime/agents/spawner.py`

#### 2.4 MCP Tool Adapter
- MCP client integration (best-of-class as of April 2026)
- Pre-curated tool registry per product configuration
- Sandboxed execution
- Result normalization to TONL format
- **Module:** `runtime/tools/mcp_adapter.py`

#### 2.5 Communication Bus
- Inter-agent messaging (Atelier wave pattern)
- Information asymmetry router — different agent for review than for production
- Append-only message log (Beads)
- **Module:** `runtime/comms/bus.py`

### Agent Runtime API

```python
from runtime import AgentRuntime

runtime = AgentRuntime(box=box)
runtime.load_agents()  # Loads all 16 BMAD agents

# Spawn one agent
result = await runtime.spawn(
    agent="winston",
    task="Design API architecture for invoice processing",
    tools=["github", "postgres", "openapi_validator"],
    budget_tokens=4096,
)

# Spawn a team with information asymmetry
team_result = await runtime.team(
    agents=["amelia", "quinn", "murat"],
    task="Implement and test payment processor",
    review_separation=True,  # Quinn doesn't see Amelia's code while testing
)
```

---

## LAYER 3: THE META-AGENT CONTROLLER (MAC)

**Purpose:** The reasoning engine. Interprets tasks, decomposes them, runs 3-cycle iteration, enforces quality.

### Components

#### 3.1 Task Interpreter
- Parses natural language task descriptions
- Extracts: goal, constraints, success criteria, deliverable type
- Maps to known workflow templates if pattern match exists (Mem0 retrieval)
- **Module:** `mac/interpreter.py`
- **Pattern source:** ReAct + planning research

#### 3.2 Plan Decomposer (FSM-based)
- Builds task DAG using MetaAgent FSM pattern (ICML 2025)
- Each node: agent assignment, inputs, outputs, quality criteria
- Backtracking edges for failure recovery
- **Module:** `mac/decomposer.py`

#### 3.3 3-Cycle Iteration Controller

The heart of the MAC. Implements wide → narrow → verify pattern.

```python
# mac/controller.py
class IterationController:
    async def run(self, task, plan, budget):
        # CYCLE 1: Wide + Shallow
        # Generate 2-3 candidate approaches, score with cheap gates
        candidates = await self.generate_candidates(task, n=3, budget=budget * 0.2)
        scored = await self.evaluate_cheap(candidates)
        winner, alternatives = scored[0], scored[1:]

        # Save alternatives as backtrack options in Beads
        await self.beads.save_backtracks(alternatives)

        # CYCLE 2: Narrow + Deep
        # Execute the winner with full agent team
        result = await self.execute_deep(winner, budget=budget * 0.6)

        # CYCLE 3: Verify
        # Quality gates + retrieval comparison + selective LLM judge
        verdict = await self.verify(result, budget=budget * 0.2)

        if verdict.passed:
            await self.persist_learning(task, winner, result, verdict)
            return result
        else:
            # Backtrack: try alternative approach from Cycle 1
            return await self.backtrack(alternatives, task, budget * 0.5)
```

#### 3.4 Quality Gate Engine (Atelier 12 Gates)
- Tier 1 — Cheap: rule-based gates (format, schema, completeness)
- Tier 2 — Medium: retrieval comparison (does this match known-good patterns?)
- Tier 3 — Expensive: LLM-as-judge (only when Tiers 1-2 are ambiguous)
- **Module:** `mac/gates/`
- **Critical:** Gates are CONFIGURABLE per product. Compliance has different gates than content.

#### 3.5 Information Asymmetry Router
- For any review task, routes to a different agent than the one that produced the output
- Reviewer does NOT see the production agent's reasoning trace
- Implements Atelier's parallel reviewer pattern (Poirot/Robert/Sable)
- **Module:** `mac/asymmetry.py`
- **Source:** Multi-agent debate research (5-23pp improvement)

#### 3.6 Cross-Session Learning Loop
- After every workflow completion: capture (task_signature, approach, outcome, quality_score)
- Write to Mem0 (for retrieval) + Atelier pgvector (for similarity matching)
- On new task: retrieve top-K similar past tasks, seed Cycle 1 with their winning approaches
- **Module:** `mac/learning.py`
- **Pattern source:** SiriuS (NeurIPS 2025) — experience libraries

### MAC API

```python
from mac import MetaAgentController

mac = MetaAgentController(runtime=runtime, box=box)

result = await mac.execute(
    task="Generate SOC 2 readiness assessment for our codebase",
    workflow_template="shield.soc2_assessment",
    max_iterations=3,
    budget_tokens=20000,
    quality_gates=["completeness", "evidence_traceability", "control_coverage"],
)
```

---

## LAYER 4: WORKFLOW TEMPLATES (CONFIGURATION, NOT CODE)

**Purpose:** Define product-specific orchestrations as YAML. The same MAC engine runs all of them.

### Template Structure

```yaml
# templates/studio/strategic_session.yaml
name: strategic_session
product: studio
description: Multi-perspective strategic analysis with red team

inputs:
  question: { type: string, required: true }
  context: { type: string, required: false }
  depth: { type: enum[quick, standard, deep], default: standard }

cycles:
  cycle_1:
    name: Wide Survey
    budget_pct: 20
    agents:
      - mary: { role: market_research, output: research_brief }
      - victor: { role: strategic_framing, output: strategic_options }
      - john: { role: customer_perspective, output: pmf_assessment }
    parallel: true

  cycle_2:
    name: Deep Analysis
    budget_pct: 50
    agents:
      - winston: { role: technical_feasibility, depends_on: [strategic_options] }
      - dr_quinn: { role: risk_analysis, depends_on: [research_brief] }
      - carson: { role: contrarian_angles, depends_on: [strategic_options] }

  cycle_3:
    name: Red Team + Synthesis
    budget_pct: 30
    agents:
      - dr_quinn: { role: red_team, mode: adversarial }
      - sophia: { role: narrative_synthesis }
      - caravaggio: { role: visual_brief }
    asymmetry: true  # Reviewers don't see production reasoning

quality_gates:
  - name: completeness
    type: rule_based
    criteria:
      - all_agents_completed
      - all_outputs_present

  - name: dissent_present
    type: rule_based
    criteria:
      - at_least_one_disagreement

  - name: actionable
    type: llm_judge
    criteria:
      - has_concrete_recommendations
      - has_rejected_alternatives

outputs:
  format: structured_brief
  template: templates/studio/brief.md.j2
  visual: templates/studio/deck.html.j2
```

### Templates by Product Configuration

| Configuration | Template File | Agents Used | Output Format |
|--------------|---------------|-------------|---------------|
| **Studio** (Strategic Advisory) | `studio/strategic_session.yaml` | Mary, Victor, John, Winston, Dr. Quinn, Carson, Sophia, Caravaggio | Structured brief + deck |
| **Factory** (Software Delivery) | `factory/feature_delivery.yaml` | John, Winston, Amelia, Quinn, Bob, Murat, Paige | PRs + tests + docs |
| **Shield** (Compliance) | `shield/soc2_assessment.yaml` | Mary, Winston, Dr. Quinn, John, Amelia, Murat, Paige | Audit package + evidence |
| **Pipeline** (Sales/Content) | `pipeline/lead_to_proposal.yaml` | Mary, John, Victor, Sophia, Caravaggio | Pitch deck + outreach |
| **Ops** (Process Automation) | `ops/document_processing.yaml` | Mary, Dr. Quinn, Barry, Quinn, Paige | Processed records + audit log |

### Template Engine

```python
# mac/templates/loader.py
from mac.templates import WorkflowTemplate

template = WorkflowTemplate.load("templates/studio/strategic_session.yaml")
result = await mac.execute(template=template, inputs={...})
```

---

## LAYER 5: PRODUCT SHELLS (LAST-MILE)

**Purpose:** Per-product UX, integrations, billing. The thinnest possible layer over the kernel.

### Shell Components (Same for All Products)

| Component | Purpose | Tech |
|-----------|---------|------|
| **Web UI** | Customer-facing dashboard | Next.js + Tailwind + shadcn/ui |
| **API Gateway** | REST endpoints for the workflow engine | FastAPI |
| **Auth** | SSO, RBAC, audit logs | Auth0 / Clerk |
| **Billing** | Stripe + usage metering (via Pi-Mono) | Stripe + custom metering |
| **Webhooks** | Async result delivery | Standard webhook pattern |
| **Observability** | Tracing, logging, cost dashboards | OpenTelemetry + Grafana |

### Per-Product Differences (the ONLY things that change)

#### Studio Shell
- **Integrations:** Tavily (web research), Slack (notifications)
- **UI:** Strategic question intake, multi-perspective output viewer
- **Billing:** Per-session ($500-2K)

#### Factory Shell
- **Integrations:** GitHub, GitLab, Jira, Linear (via MCP)
- **UI:** Sprint dashboard, PR queue, test results
- **Billing:** Monthly retainer ($5-15K/mo)

#### Shield Shell
- **Integrations:** AWS/GCP/Azure scanners, Vanta/Drata APIs, code scanners
- **UI:** Compliance dashboard, evidence package builder, gap tracker
- **Billing:** Per-audit ($10-50K)

#### Pipeline Shell
- **Integrations:** Salesforce, HubSpot, LinkedIn, Mailchimp
- **UI:** Lead inbox, content calendar, deck library
- **Billing:** Monthly retainer ($2-8K/mo)

#### Ops Shell
- **Integrations:** QuickBooks/Xero/SAP, document parsers (OCR)
- **UI:** Transaction queue, exception dashboard
- **Billing:** Per-transaction or volume tier ($1-5K/mo)

---

## TECHNOLOGY STACK (BEST-OF-CLASS, APRIL 2026)

| Layer | Choice | Why |
|-------|--------|-----|
| **Language** | Python 3.12 | Async, type hints, ecosystem |
| **API Framework** | FastAPI | Async-native, OpenAPI docs free |
| **ORM** | SQLAlchemy 2.0 | Mature, async support |
| **Database** | PostgreSQL 16 + pgvector | Boring, scales, vector search built-in |
| **Cache/Queue** | Redis 7 | Pub/sub for inter-agent messaging |
| **Vector Memory** | Mem0 (pgvector backend) | 344x efficiency, hybrid vector+graph |
| **State Versioning** | Dolt (postgres-compatible) | Git-like for data |
| **Agent Schemas** | Pydantic v2 + DSPy | Type safety + auto-optimization |
| **Workflow Definition** | YAML + Jinja2 | Human-readable, templatable |
| **Tool Protocol** | MCP (Anthropic standard) | Universal adapter |
| **LLM Providers** | Anthropic (Opus 4.6, Sonnet 4.6, Haiku 4.5) | Best agentic reasoning, 1M context |
| | Fallback: GPT-5.4, Gemini 3.1 | Multi-provider resilience |
| **Observability** | OpenTelemetry + Grafana | Standard, vendor-neutral |
| **Container** | Docker + Compose (dev), ECS Fargate (prod) | Boring, portable |
| **Web UI** | Next.js 15 + Tailwind 4 + shadcn/ui | Modern, fast to ship |
| **Auth** | Clerk (default) or Auth0 | SaaS auth, fast setup |
| **Payments** | Stripe | Universal |

---

## BUILD SEQUENCE — THE 12-WEEK HOMEWORK

### Phase 1: Kernel (Weeks 1-3)

**Week 1: Project Setup + TONL + Cost Tracking**
- Initialize repo: `box/` with poetry, ruff, mypy strict
- Postgres + Dolt setup via Docker Compose
- Port TONL serialization from existing project
- Implement Pi-Mono cost tracker with `decimal.Decimal`
- **Deliverable:** `box.serialize(payload)` and `box.track_cost(...)` working

**Week 2: Beads + Mem0**
- Beads versioned state with hash-based IDs
- Worktree isolation per session
- Mem0 adapter wired to pgvector
- Three-axis scoping (user × agent × run)
- **Deliverable:** Save and retrieve state across sessions; semantic memory queries work

**Week 3: Forge Compaction + RTK Proxy**
- Forge deterministic compaction with retention window
- Reasoning chain preservation
- RTK Rust proxy for CLI commands (port from existing)
- **Deliverable:** Long sessions survive without context loss; CLI outputs auto-compressed

### Phase 2: Agent Runtime (Weeks 4-5)

**Week 4: Agent Loader + Registry**
- Parse `agent-manifest.csv`
- Build Pydantic schemas per agent (capabilities, persona, principles)
- Capability matching index
- **Deliverable:** Load all 16 BMAD agents; query by capability

**Week 5: Spawning + MCP Adapter**
- Agent spawning (subagent + team modes)
- Polecat lifecycle (spawn, run, cleanup)
- MCP client integration with curated tool registry
- Sandboxed tool execution
- **Deliverable:** Spawn an agent that uses an MCP tool and returns a result

### Phase 3: MAC (Weeks 6-8)

**Week 6: Task Interpreter + Plan Decomposer**
- Natural language task parser
- FSM-based plan decomposer (MetaAgent pattern)
- DAG builder with backtrack edges
- **Deliverable:** Take a task, output a structured execution plan

**Week 7: 3-Cycle Iteration Controller**
- Cycle 1: Generate candidates + cheap evaluation
- Cycle 2: Deep execution
- Cycle 3: Verification
- Backtracking on failure
- **Deliverable:** Run a task end-to-end through 3 cycles with measurable improvement

**Week 8: Quality Gates + Information Asymmetry + Learning Loop**
- 12 quality gates (rule-based + retrieval + LLM judge)
- Asymmetry router (production vs review agents)
- Mem0 write-back for completed workflows
- **Deliverable:** Run a task, capture the outcome, retrieve it on a similar task next time

### Phase 4: MCP + Tool Library (Weeks 9-10)

**Week 9: Curated Tool Registry**
- Wire 20+ best-of-class MCP tools
- Categorized by product configuration
- Tool capability descriptors for routing
- **Standard tools to include:**
  - Tavily (web research) — Studio
  - GitHub MCP — Factory
  - PostgreSQL MCP — All
  - File system MCP — All
  - Slack MCP — Pipeline
  - AWS MCP — Shield
  - Stripe MCP — Ops
  - Browserbase / Playwright — Pipeline
  - Notion / Confluence MCP — Studio
  - Linear / Jira MCP — Factory

**Week 10: Tool Discovery + Sandboxing**
- Dynamic tool capability matching
- Sandboxed execution (no breakout)
- Cost tracking per tool call
- **Deliverable:** Agent dynamically selects from tool registry, executes safely

### Phase 5: First Workflow Template (Week 11)

**Week 11: Studio (Strategic Advisory)**
- Define `studio/strategic_session.yaml` workflow
- Test against 5 real strategic questions
- Compare outputs to single-agent baseline (Claude with same prompt)
- Measure: quality, cost, time
- **Deliverable:** Working Studio workflow ready to demo

### Phase 6: POV Delivery Harness (Week 12)

**Week 12: Productize for First POV**
- Minimal web UI (Next.js + shadcn/ui)
- API endpoints for workflow execution
- Stripe billing integration
- Result delivery via webhook
- Onboarding flow (auth, workspace setup, first run)
- **Deliverable:** End-to-end POV-ready system. From signup to first result in <10 minutes.

---

## POV DELIVERY PLAYBOOK (POST-HOMEWORK)

When the first POV request lands, here's the playbook:

### Day 1: Discovery Call (90 min)
- Map the customer's process to one of 5 product configurations
- Identify required MCP integrations
- Define success criteria and quality gates
- **Output:** POV scope document

### Day 2: Configuration
- Copy the closest workflow template
- Customize agent assignments and quality gates
- Configure MCP tool bindings (wire to customer's systems)
- **Output:** Custom workflow YAML

### Day 3: Tool Integration
- Authenticate to customer's systems (read-only by default)
- Test MCP connectors with real customer data
- Validate quality gates against customer's standards
- **Output:** Working integration

### Day 4: Test Runs
- Execute workflow on customer's real tasks (3-5 examples)
- Compare to current process (time, quality, cost)
- Iterate on quality gates if needed
- **Output:** Performance report

### Day 5: Customer Demo
- Live walkthrough on real customer data
- Show cost savings, time savings, quality improvements
- Discuss expansion path
- **Output:** Pilot agreement or feedback for revision

### Day 6-7: Buffer / Polish / Documentation
- Hand off to customer with documentation
- Set up monitoring and alerts
- Plan ongoing engagement
- **Output:** Production-ready deployment

**Total: 5-7 days from POV request to working deployment.**

---

## REPOSITORY STRUCTURE

```
box/
├── kernel/                          # Layer 1: Foundation
│   ├── serialization/tonl.py
│   ├── cost/pi_mono.py
│   ├── state/beads.py
│   ├── memory/mem0_adapter.py
│   ├── compaction/forge.py
│   └── proxy/rtk/                   # Rust binary
│
├── runtime/                         # Layer 2: Agent Runtime
│   ├── agents/
│   │   ├── loader.py
│   │   ├── registry.py
│   │   └── spawner.py
│   ├── tools/
│   │   ├── mcp_adapter.py
│   │   └── registry.py
│   └── comms/bus.py
│
├── mac/                             # Layer 3: Meta-Agent Controller
│   ├── interpreter.py
│   ├── decomposer.py
│   ├── controller.py                # 3-cycle iteration
│   ├── gates/
│   │   ├── rule_based.py
│   │   ├── retrieval.py
│   │   └── llm_judge.py
│   ├── asymmetry.py
│   ├── learning.py
│   └── templates/loader.py
│
├── templates/                       # Layer 4: Workflow Templates
│   ├── studio/
│   │   ├── strategic_session.yaml
│   │   └── brief.md.j2
│   ├── factory/
│   │   └── feature_delivery.yaml
│   ├── shield/
│   │   └── soc2_assessment.yaml
│   ├── pipeline/
│   │   └── lead_to_proposal.yaml
│   └── ops/
│       └── document_processing.yaml
│
├── shells/                          # Layer 5: Product Shells
│   ├── studio/
│   │   ├── api/                    # FastAPI routes
│   │   ├── ui/                     # Next.js app
│   │   └── integrations/
│   ├── factory/...
│   ├── shield/...
│   ├── pipeline/...
│   └── ops/...
│
├── _bmad/                           # BMAD agent definitions (existing)
│   └── _config/agent-manifest.csv
│
├── tests/
│   ├── kernel/
│   ├── runtime/
│   ├── mac/
│   └── e2e/
│
├── infra/
│   ├── docker-compose.yml
│   ├── terraform/                   # ECS Fargate, RDS, etc.
│   └── observability/
│
└── docs/
    ├── architecture.md              # This document
    ├── pov_playbook.md
    └── api_reference.md
```

---

## BEST-OF-CLASS PATTERNS BAKED IN

| Pattern | Source | Where in The Box |
|---------|--------|------------------|
| **Self-Refine iteration** | Madaan et al., NeurIPS 2023 | MAC 3-cycle controller |
| **MetaAgent FSM + backtracking** | ICML 2025 | MAC plan decomposer |
| **SiriuS experience libraries** | NeurIPS 2025 | MAC learning loop + Mem0 |
| **Tree of Thoughts (constrained)** | Yao et al., NeurIPS 2023 | MAC Cycle 1 candidate generation |
| **Multi-agent debate (anti-conformity)** | FREE-MAD, A-HMAD, 2025 | Information asymmetry router |
| **MCP tool protocol** | Anthropic, 2024 | Tool adapter |
| **DSPy auto-optimization** | Stanford, 2024 | Agent prompt tuning |
| **Atelier 12 quality gates** | Internal hybrid arch | MAC gate engine |
| **Zero-cost compaction** | Forge | Kernel compaction layer |
| **Hybrid vector+graph memory** | Mem0 | Kernel memory layer |
| **Information asymmetry review** | Atelier hybrid arch | MAC asymmetry router |
| **Token-aware encoding** | TONL | Kernel serialization |

---

## WHAT'S "IN THE BOX" VS "LAST MILE"

### IN THE BOX (Built Once, Reused Forever)

✅ All 8 architectural layers (kernel through shells framework)
✅ All 16 BMAD agents loaded and ready
✅ MAC engine with 3-cycle iteration
✅ 12 quality gates (configurable per workflow)
✅ Information asymmetry routing
✅ Mem0 cross-session learning
✅ MCP tool adapter + 20+ pre-wired tools
✅ Cost tracking (Pi-Mono)
✅ State versioning (Beads)
✅ Compaction (Forge)
✅ Workflow template engine (YAML-driven)
✅ Web UI shell components (reusable)
✅ Auth, billing, webhooks scaffolding
✅ Observability (OpenTelemetry + Grafana dashboards)

### LAST MILE (Per POV, ~3-5 days)

🔧 Customer-specific MCP integrations (their CRM, EHR, ERP, etc.)
🔧 Workflow template customization (which agents, in what order)
🔧 Quality gate calibration (their definition of "good")
🔧 Output template branding (their logo, format preferences)
🔧 Domain-specific knowledge loading (their compliance frameworks, glossaries)
🔧 Agent persona tuning (their brand voice for content shells)
🔧 SSO integration with their identity provider
🔧 Custom dashboards / reports

---

## RISK MITIGATION

| Risk | Mitigation |
|------|------------|
| **First POV scope creep** | Strict 5-day delivery box. Anything beyond = paid extension. |
| **Quality gate calibration takes too long** | Start with conservative gates; loosen based on customer feedback in production |
| **MCP integration brittleness** | Pre-test all 20+ tools before any POV. Maintain "supported integrations" list |
| **LLM cost overruns** | Pi-Mono enforces hard budgets per workflow. Auto-escalation needs explicit approval |
| **Customer data security** | Read-only by default. Sandboxed execution. Audit log every action |
| **The 0.37% ARC-AGI problem** | Quality gates escalate to human on novel patterns. Don't promise full autonomy |
| **Agent self-assembly hallucinations** | Phase 5 (self-assembly) deferred. Use fixed agent topologies for first 5 POVs |
| **Vendor lock-in (Anthropic)** | Multi-provider abstraction in kernel. Anthropic primary, GPT-5/Gemini fallback |

---

## SUCCESS METRICS FOR THE HOMEWORK

By end of Week 12, the box must demonstrate:

| Metric | Target |
|--------|--------|
| **Time from new task to first result** | <30 seconds |
| **Quality improvement vs single-agent baseline** | +15% (measured on Studio strategic questions) |
| **Cost per workflow execution** | <$2 for Studio session, <$20 for Shield audit |
| **Cross-session learning measurable** | 2nd similar task uses 30% fewer tokens than 1st |
| **POV delivery time** | 5-7 days from discovery to deployment |
| **Test coverage** | >80% on kernel and MAC; >70% overall |
| **Documentation completeness** | API reference + POV playbook + architecture |
| **Demo-ability** | Can demo Studio workflow live in 5 minutes |

---

## THE STRATEGIC POSITION

By having the box ready BEFORE the first POV:

1. **Sales velocity:** "Yes we can do this, here's a demo, signed agreement next week" — vs competitors who say "let us scope this"
2. **Margin:** Last-mile customization is 5 days. At $10K-50K per POV, that's 80%+ gross margin
3. **Learning compound:** Every POV adds patterns to Mem0. Box gets smarter with each delivery
4. **Configuration moat:** Competitors can copy the architecture, but not the accumulated quality gates and workflow templates
5. **Optionality:** Same box serves Studio, Factory, Shield, Pipeline, Ops. Pivot by changing config, not code

---

## NEXT STEPS

1. **Week 0 (this week):** Set up repo, CI/CD, infrastructure baseline
2. **Weeks 1-3:** Build the kernel
3. **Week 4-5:** Build the runtime
4. **Weeks 6-8:** Build the MAC
5. **Weeks 9-10:** Wire MCP and tool registry
6. **Week 11:** First workflow template (Studio)
7. **Week 12:** POV delivery harness

**At Week 12, start outbound for the first POV.** The box is ready to deliver in 5-7 days when the request arrives.

---

**Status:** Architecture Complete
**Buildability:** 100% with current technology
**Effort:** 12 weeks for 1 senior engineer (or 6-8 weeks with 2)
**First POV-ready:** Week 12
**Best-of-class as of:** April 2026

> "Build the foundation first. Twenty conversations. Two weeks."
> — From Round 4 Red Team

The box is the foundation. Build it, then have those conversations. When they're ready, you're ready.
