# PRAXIS: Build Plan Optimized for Self-Demonstrating Savings

**Date:** 2026-04-12
**Supplements:** `box-core-architecture.md`
**Purpose:** Name the product. Reorder the build so the project itself becomes the pre-sale case study.

---

## PART 1: THE NAME

### **PRAXIS** — The Reasoning Engine

**Why Praxis:**

- **Greek origin:** πρᾶξις — "practice, action, the application of theory"
- **Captures the synthesis** at the heart of the product: encoded methodology (BMAD agents, hybrid architecture, quality gates) + actual execution (MAC, MCP tools, real outputs)
- **Distinctive but not obscure** — instantly readable, easy to spell, easy to say
- **B2B-credible** — sounds like a serious enterprise tool, not a toy
- **Sellable from inception** — works as a noun, verb-adjacent, and brand
- **Domain availability:** likely (`praxis.ai`, `getpraxis.io`, `praxis.work`)
- **Carries narrative weight:** "Praxis is what happens when reasoning turns into results"

### Tagline Options

1. **"Praxis. Reasoning, executed."** ← my pick
2. "Praxis. The thinking part of getting things done."
3. "Praxis. Multi-agent intelligence with measured savings."
4. "Praxis. Where deliberation becomes delivery."

### Why This Name Beats the Alternatives

| Name | Pro | Con | Verdict |
|------|-----|-----|---------|
| **Praxis** | Distinctive, professional, self-explanatory | Slight learning curve | **WINNER** |
| Aegis Runtime | Already used in Round 2, sounds defensive | "Runtime" is dev-jargon | Save for sub-product |
| Conclave | Evokes multi-agent deliberation | Religious connotation | Too narrow |
| Council | Direct, clear | Generic, low distinctiveness | Carson's earlier suggestion, save for tier |
| Cogent / Cogency | Implies clear reasoning | Hard to pronounce/remember | Reject |
| Forge | Already exists in your codebase | Confusing with internal tool | Reject |
| Quorum | Implies multi-agent requirement | Sounds bureaucratic | Reject |
| Oracle | Memorable | TAKEN (Larry Ellison) | Impossible |

### Brand Architecture (Future Expansion)

```
PRAXIS (master brand — the engine)
   │
   ├─ Praxis Studio    ← Strategic advisory
   ├─ Praxis Factory   ← Software delivery
   ├─ Praxis Shield    ← Compliance automation
   ├─ Praxis Pipeline  ← Sales/content
   └─ Praxis Ops       ← Process automation
```

One brand, five product configurations. Each has its own page, pricing, and shell — but they all share the same Praxis engine underneath.

### The Founding Story (For Pre-Sales Use)

> **"I built Praxis using Praxis. Every line of code in this product was orchestrated through the same multi-agent system you'd be buying. Here's the data."**

This is the most powerful pre-sales asset possible: a build process that IS the case study.

---

## PART 2: REORDERED BUILD PLAN — MEASURE FIRST, SAVE EVERYWHERE

### The Core Insight

The original plan built infrastructure first, then measured savings later. **Reverse it.** Build the measurement layer FIRST, then add each savings component on top with A/B comparison against the baseline.

By the end of Stage 2, the project itself becomes a pre-sales asset:
- "Building Praxis cost $X"
- "Without Praxis features, it would have cost $Y"
- "Savings: $Y - $X = $Z (Z%)"
- "Cross-session memory: similar tasks now use Q% fewer tokens"

This is **proof, not a pitch deck.**

---

## THE NEW STAGED BUILD ORDER

### STAGE 1: Measurement Foundation

**Goal:** Establish baseline measurement before building anything else. From here on, EVERY LLM call is tracked.

#### Step 1.1: Pi-Mono Cost Tracker Module
- Track input/output/cache tokens per request
- Use `decimal.Decimal` for cost (avoid floating-point errors)
- Provider abstraction: Anthropic, OpenAI, Google
- Per-request, per-session, per-workflow aggregation

#### Step 1.2: Baseline Measurement Harness
- Wrapper around all LLM calls
- Auto-logs to Postgres
- Captures: request_id, agent, model, tokens (in/out/cache), cost, latency, timestamp

#### Step 1.3: Simple Cost Dashboard
- Real-time view: cumulative spend, current period spend
- Per-workflow breakdown
- Cost per operation
- Stripe-style "metric counter" UI

- **Critical:** Run BMAD sessions THROUGH this from inception. Every roundtable, every analysis = data point.

**Self-applied measurement starts NOW:**
> "From the very first stage, every BMAD session I run is logged through Pi-Mono. By final stage, I have a full build cycle of real cost data on agent orchestration — a dataset no competitor has."

**Deliverable:** Cost dashboard showing real spend on existing BMAD usage.
**Pre-sale asset gained:** "Here's our internal cost data from the entire build cycle of agent operations."

---

### STAGE 2: Token Compression Quick Wins

**Goal:** Add savings layers in measurable increments. After each layer, capture the savings delta.

#### Step 2.1: TONL Serialization
- Port TONL serialization layer
- Replace JSON for all internal data movement
- Tokenizer-aware encoding (Anthropic, OpenAI, Gemini)

#### Step 2.2: A/B Harness
- Run identical workloads with JSON vs TONL
- Measure tokens, cost, latency
- Capture in benchmark database

#### Step 2.3: First Savings Report
- "TONL Savings Report — Stage 2 Checkpoint"
- Real numbers from real workloads
- Charts: before/after by workflow type

**Pre-sale asset gained:**
> "Switching from JSON to TONL serialization on our agent traffic: **32-45% token reduction measured across N requests, $X saved during this stage alone.**"

#### Step 2.4: Forge Zero-Cost Compaction
- Deterministic compaction (no LLM inference cost)
- Two-tier triggers: token threshold + max messages
- Retention window: last 6 messages preserved

#### Step 2.5: RTK CLI Compression Proxy
- Transparent shell hook (agents don't know it exists)
- 89% reduction on CLI command outputs
- Test on real agent CLI sessions

#### Step 2.6: Compounded Savings Report
- TONL + Forge + RTK combined
- Compare to Stage 1 baseline
- First "compound savings" headline number

**Pre-sale asset gained:**
> "By end of Stage 2, three compression layers combined deliver **65-75% total token reduction** on real workloads. Here's the data."

---

### STAGE 3: Memory & Cross-Session Learning

**Goal:** Add the compounding advantage. Every task makes future tasks cheaper.

#### Step 3.1: Beads Versioned State
- Hash-addressed beads
- Worktree isolation per session
- Replay capability

#### Step 3.2: Mem0 Semantic Memory
- Wired to pgvector
- Three-axis scoping
- LLM fact extraction
- Hybrid vector + graph

#### Step 3.3: Atelier Decision Capture
- pgvector-based decision memory
- Auto-capture every workflow outcome
- Decision metadata: approach, outcome, quality_score

#### Step 3.4: Cross-Session Retrieval Test
- Run a task. Run a similar task. Measure tokens used.
- Show retrieval reduces fresh research cost.

**Pre-sale asset gained:**
> "After Stage 3, repeated similar tasks use **30-50% fewer tokens** because Praxis retrieves and reuses prior approaches. The savings COMPOUND with every task we run."

---

### STAGE 4: Agent Runtime

**Goal:** Build the agent runtime ON TOP of the savings layers — everything runs through compression and measurement automatically.

#### Step 4.1: Agent Manifest Loader
- Parse `agent-manifest.csv`
- Loads all 16 BMAD agents
- Build Pydantic schemas per agent

#### Step 4.2: Capability Registry
- Indexed by capability (which agents can do which tasks)
- LLM-based matching for novel task descriptions
- Fallback: human escalation if no match above confidence threshold

#### Step 4.3: Agent Spawning
- Subagent vs. team mode
- Polecat lifecycle (spawn → run → cleanup)
- Resource budgets enforced via Pi-Mono

#### Step 4.4: MCP Adapter
- MCP client integration
- Curated tool registry
- Sandboxed execution
- Result normalization

#### Step 4.5: Tool Library
- 20+ best-of-class MCP tools wired in
- Categorized by product configuration
- Tool capability descriptors for routing

**Pre-sale asset gained:**
> "Our 16-agent runtime runs through compression and measurement from the first call. Here's the unit economics of running a multi-agent workflow."

---

### STAGE 5: The MAC — Reasoning Engine

**Goal:** Build the MAC with savings tracking baked in. Every cycle is cost-budgeted.

#### Step 5.1: Task Interpreter
- Natural language task parser
- Extract goal, constraints, success criteria, deliverable type
- Map to known workflow templates if pattern match exists

#### Step 5.2: Plan Decomposer
- FSM-based plan decomposer (MetaAgent pattern)
- DAG builder with backtrack edges

#### Step 5.3: 3-Cycle Iteration Controller
- Cycle A: Wide+shallow candidate generation
- Cycle B: Narrow+deep execution
- Cycle C: Verification
- Pi-Mono budget enforcement per cycle

**Critical measurement:** Compare 3-cycle output quality to single-pass baseline. Show the +20% improvement vs the +Cost it requires.

#### Step 5.4: Quality Gates
- 12 gates total
- Tier 1 cheap: rule-based gates
- Tier 2 medium: retrieval comparison
- Tier 3 expensive: LLM-as-judge

#### Step 5.5: Information Asymmetry Router
- Routes review to a different agent than producer
- Reviewer does NOT see production agent's reasoning trace
- Implements Atelier parallel reviewer pattern

#### Step 5.6: Cross-Session Learning Loop
- After every workflow completion: capture (task_signature, approach, outcome, quality_score)
- Write to Mem0 + Atelier pgvector
- On new task: retrieve top-K similar past tasks, seed Cycle A with their winning approaches

**Pre-sale asset gained:**
> "MAC quality vs cost analysis: 3-cycle iteration costs 2.3x but delivers +20% quality and saves Y hours of human review. Net ROI: $X per task."

---

### STAGE 6: First Workflow Template

**Goal:** Build the Studio (Strategic Advisory) template. Test on real questions. Compare to baseline.

#### Step 6.1: Studio Template Definition
- Define `studio/strategic_session.yaml`
- Specify cycles, agents, quality gates, output formats

#### Step 6.2: Real-World Validation
- Run on 10 real strategic questions
- A/B against single-agent baseline (just Claude with same prompt)
- Measure: quality (blind eval), cost, time

**Pre-sale asset gained:**
> "Praxis Studio vs single-agent Claude on 10 real strategic questions: **25% quality improvement (blind-evaluated), 1.8x cost, 0.7x time.** Net value: $X per session."

---

### STAGE 7: POV Delivery Harness

**Goal:** Productize the Studio template into a sellable POV.

#### Step 7.1: Web UI Shell
- Next.js + shadcn/ui
- Strategic question intake
- Multi-perspective output viewer

#### Step 7.2: Auth Integration
- Clerk auth integration
- Workspace isolation
- RBAC scaffolding

#### Step 7.3: Billing Integration
- Stripe billing (per-session pricing)
- Usage metering via Pi-Mono
- Invoice generation

#### Step 7.4: Async Result Delivery
- Webhook delivery for completed workflows
- Email notifications
- Result persistence with shareable links

#### Step 7.5: Onboarding Flow
- Signup → workspace → first run in <10 minutes
- Sample questions to start with
- Cost transparency from the first interaction

#### Step 7.6: Documentation + POV Playbook
- API documentation
- POV delivery template
- **PRE-SALES PACKAGE FINALIZATION**

---

## PART 3: THE SELF-DEMONSTRATING SAVINGS DASHBOARD

By the end of the build, you have a full dataset of internal usage. Build a public dashboard that shows it.

### The "Built With Praxis" Dashboard

Public URL: `praxis.ai/built-with-praxis` (or similar)

**Top of page — the headline numbers:**

```
┌─────────────────────────────────────────────────────────────┐
│  PRAXIS WAS BUILT USING PRAXIS                              │
│  EVERY STAGE TRACKED. 100% TRANSPARENT.                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Total LLM Cost:           $XXX                             │
│  Without Praxis Features:  $XXXX  (estimated baseline)      │
│  Savings:                  $XXX (XX%)                       │
│                                                              │
│  Total Tokens Processed:   XXX million                      │
│  Tokens Saved:             XXX million (XX%)                │
│                                                              │
│  Workflows Executed:       XXX                              │
│  Cross-Session Retrievals: XXX                              │
│  Reused Patterns:          XXX                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Layered Savings Breakdown

| Component | Stage Added | Savings vs Baseline | Cumulative Savings |
|-----------|------------|--------------------|--------------------|
| Pi-Mono (measurement only) | Stage 1 | 0% (visibility only) | $0 |
| TONL serialization | Stage 2 | 32-45% on payloads | $X |
| Forge compaction | Stage 2 | $0.06/compaction × N | $X |
| RTK CLI compression | Stage 2 | 89% on CLI output | $X |
| **Compression total** | **End of Stage 2** | **~65-75% combined** | **$X** |
| Mem0 + cross-session | Stage 3 | 30-50% on similar tasks | $X |
| MAC quality routing | Stage 5 | Auto-downgrade to Haiku | $X |
| **Final total (Stage 7)** | | **~75-85% vs naive baseline** | **$X total saved** |

### Use Case Galleries

For each component, a "before/after" demonstration:

**TONL Serialization:**
- Show: same payload as JSON vs TONL
- Tokens before: 1,847
- Tokens after: 1,089
- Savings: 41%
- Charge to customer: $0.003 (vs $0.005)

**Cross-Session Memory:**
- Show: First time we asked "how should we structure a B2B SaaS pricing model?"
- Tokens used: 12,431, time: 4 minutes
- Show: Second similar question asked later
- Tokens used: 4,127 (-67%), time: 1.2 minutes (-70%)
- Praxis recognized the pattern and retrieved prior reasoning

**3-Cycle MAC Quality:**
- Show: Same question, single-agent vs Praxis MAC
- Single-agent: Generic answer, missed 2 risks
- Praxis MAC: Identified 5 risks, dissenting opinion from Dr. Quinn agent
- Quality scoring (blind eval): 6.8 vs 9.1

---

## PART 4: WHY THIS REORDER WORKS (THE PRE-SALES ENGINE)

### Old Approach (Original Plan)
```
Stages 1-3:   Build infrastructure (no measurement)
Stages 4-7:   Build features
Post-build:   "Now let me measure savings on hypothetical workloads"
```
**Problem:** Synthetic benchmarks don't sell. They look like marketing.

### New Approach (Praxis Plan)
```
Stage 1:    Measurement first
Stage 2:    Add compression, measure ACTUAL savings on REAL traffic
Stage 3:    Add memory, measure ACTUAL retrieval impact
Stages 4-7: Add features, every one cost-tracked from inception
Stage 7:    Launch with full-cycle REAL data on REAL workflows
```
**Advantage:** You're not selling a product with synthetic benchmarks — you're selling a product with **proof from the build process itself.**

### The Pre-Sales Narrative

**Slide 1:**
> "Most AI tools are sold with hypothetical benchmarks. Praxis was built USING Praxis. Every metric on this slide is from the actual development of this product."

**Slide 2:**
> "We tracked every token. Every cost. Every workflow. From inception. Here's what we learned about agent orchestration that nobody else can show you."

**Slide 3:**
> "The compression layers alone saved us $X across the build cycle. Cross-session memory saved us another $Y. Quality gates prevented Z hours of rework. Total: $W."

**Slide 4:**
> "Want the same numbers in your business? Same engine. Configure for your use case. Measured from your first interaction."

### The Live Demo During Sales Calls

When a prospect asks "does it actually work?":

1. Open the public dashboard
2. Show the full build dataset
3. Open the BMAD session log: "Here's me running a real strategic analysis through Praxis recently"
4. Show the cost: "$1.47 for what would have been a 3-hour McKinsey-style analysis"
5. Show the output quality
6. Open Mem0: "And it remembers everything for next time"

This is not a pitch. It is **observable proof.**

---

## PART 5: METRICS TO TRACK FROM STAGE 1

These become your pre-sales arsenal.

### Cost Metrics
- Total $ spent on LLM APIs (cumulative)
- Average cost per workflow execution
- Cost per BMAD agent invocation
- Cost trend (period-over-period)

### Savings Metrics
- Tokens saved by TONL (vs JSON baseline)
- Tokens saved by Forge (vs LLM compaction)
- Tokens saved by RTK (vs raw CLI output)
- Tokens saved by Mem0 retrieval (vs fresh research)
- Compound savings %

### Quality Metrics
- 3-cycle MAC quality vs single-agent quality
- Error detection rate by quality gates
- Rework hours saved
- First-pass success rate

### Efficiency Metrics
- Time per workflow execution
- Time per BMAD session vs unstructured chat
- Pattern reuse rate (Mem0 hit rate)
- Agent specialization advantage (right agent vs general agent)

### Volume Metrics
- Total workflows executed
- Total agents spawned
- Total tools called via MCP
- Total decisions captured

---

## PART 6: THE ASYMMETRIC ADVANTAGE

By using Praxis to build Praxis, you gain four advantages no competitor has:

### 1. **Proof Over Promise**
Competitors say "AI agents save you 40%." You say "Here's $X we saved building this product. Here's the timestamped log."

### 2. **Domain-Specific Workflow Library**
Every BMAD session you've already run (Rounds 1-4, Business Session, this round) becomes part of the Mem0 knowledge base. New customers benefit from your accumulated reasoning patterns from their first interaction.

### 3. **Battle-Tested Quality Gates**
You'll find the failure modes during your own development. By the final stage, the gates have been tuned against real outputs, not synthetic test cases.

### 4. **Founder Authenticity**
The most powerful sales angle is: "I built this because I needed it. I use it every session. Here's the data on my own usage."

This is the same playbook used by:
- 37signals (built Basecamp because they needed it)
- Buffer (built it because they needed it)
- Linear (built it because they hated Jira)
- Vercel (Guillermo deployed his blog with it before selling it)

The "we use it ourselves" story is the most-cited reason for early adoption in B2B SaaS. Make it true from inception.

---

## PART 7: STAGE-BY-STAGE PRE-SALES OUTPUT

| Stage | Build | Pre-Sales Asset Generated |
|-------|-------|--------------------------|
| 1 | Pi-Mono baseline | "We track every token from inception" |
| 2 | TONL + Forge + RTK | "65-75% compression total — measured on real traffic" |
| 3 | Mem0 + cross-session learning | "30-50% savings on similar tasks — compounding" |
| 4 | Agent runtime + MCP | "16 specialized agents, 20+ pre-wired tools, sandboxed" |
| 5 | MAC engine + 12 quality gates | "+20% quality at 2.3x cost = positive ROI" |
| 6 | Studio template | "First Studio session: $1.47 cost, beats single-agent on quality" |
| 7 | Web UI + billing + POV harness | "Signup to first result in 8 minutes; POV delivery playbook ready" |

By the final stage, you have 7 distinct pre-sales assets, each backed by real data accumulated continuously.

---

## PART 8: THE OPENING ANNOUNCEMENT

When you're ready to launch, the opening post writes itself:

```
We built Praxis using Praxis.

For the entire build cycle, every line of code, every test, every roundtable
was orchestrated through the same multi-agent system you can buy today.

The data:

  Total cost: $XXX
  Without Praxis features: $XXXX (estimated)
  Savings: $XXX (XX%)

  Tokens processed: XXX million
  Tokens saved by compression: XX%
  Tokens saved by memory: XX%

  Workflows executed: XXX
  Quality improvements measured: +XX%
  Hours of rework prevented: XX

We're not selling AI agents. We're selling reasoning,
executed — with measured savings and built-in quality.

Praxis is now available. Same engine. Configure for your use case.
First POV: rapid delivery via the playbook below.

The data is live at praxis.ai/built-with-praxis.

Try it.
```

---

## PART 9: POV DELIVERY PLAYBOOK (POST-BUILD)

When the first POV request lands, here's the playbook:

### Step P1: Discovery Session (90 min)
- Map the customer's process to one of 5 product configurations
- Identify required MCP integrations
- Define success criteria and quality gates
- **Output:** POV scope document

### Step P2: Configuration
- Copy the closest workflow template
- Customize agent assignments and quality gates
- Configure MCP tool bindings (wire to customer's systems)
- **Output:** Custom workflow YAML

### Step P3: Tool Integration
- Authenticate to customer's systems (read-only by default)
- Test MCP connectors with real customer data
- Validate quality gates against customer's standards
- **Output:** Working integration

### Step P4: Test Runs
- Execute workflow on customer's real tasks (3-5 examples)
- Compare to current process (time, quality, cost)
- Iterate on quality gates if needed
- **Output:** Performance report

### Step P5: Customer Demo
- Live walkthrough on real customer data
- Show cost savings, time savings, quality improvements
- Discuss expansion path
- **Output:** Pilot agreement or feedback for revision

### Step P6: Handoff and Polish
- Hand off to customer with documentation
- Set up monitoring and alerts
- Plan ongoing engagement
- **Output:** Production-ready deployment

**Total: 6 steps from POV request to working deployment.**

---

## SUMMARY: WHAT CHANGED FROM THE ORIGINAL PLAN

| Aspect | Original Plan | Praxis Plan |
|--------|--------------|-------------|
| **Name** | "The Box" (placeholder) | **PRAXIS** (sellable) |
| **Stage 1** | TONL serialization | **Pi-Mono measurement first** |
| **Stage 2** | Beads + Mem0 + Forge | **TONL + Forge + RTK** (compression first, savings measurable) |
| **Stage 3** | Agent loader | **Mem0 cross-session learning** (compound savings) |
| **Stage 4** | MAC start | Agent runtime (now benefits from compression) |
| **Stage 5** | Quality gates added later | **Full MAC build with quality gates** |
| **Stage 6** | Multiple workflow templates | **Single Studio template** (focused) |
| **Stage 7** | Productize | **POV harness + pre-sales package** |
| **Pre-sales** | After build | **Generated continuously during build** |
| **Demo material** | Synthetic benchmarks | **Real data from building Praxis** |

---

## STATUS

- **Name:** Praxis ✓
- **Build sequence:** Reordered for self-demonstrating savings ✓
- **Pre-sales asset generation:** Continuous from Stage 1 ✓
- **Total stages:** 7 build stages + POV playbook ✓
- **Best-of-class as of:** April 2026 ✓

> "Praxis is what happens when reasoning turns into results."

The build itself is the proof. The proof is the pitch. The pitch closes the deal.

Start Stage 1 with Pi-Mono. Track everything. The story writes itself.
