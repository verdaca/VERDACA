# Verdaca — Architecture & Strategy Diagrams

**Last refreshed:** 2026-05-13 | **HEAD at refresh:** `e7c6f1d`

> **Verdaca is not an agent framework.** Agent frameworks are the substrate Verdaca runs on top of. Verdaca is **deliberation infrastructure** for organizations that need to make repeatable, auditable, compounding decisions. The closest analogue is *not* ChatGPT or LangChain — it's a structured strategy engagement with a consulting firm, except the engagement compounds and costs $2.50 instead of $250,000.

## Audience Router — start here

| You are… | Read in this order |
|---|---|
| 👔 **CTO / strategic buyer** | §1 → Diagram 2 (Buyer's Journey) → Diagram 7 (Universal Box) → Diagram 4 (Trust Stack) |
| 💼 **Investor / strategic skeptic** | §1 → Diagram 1 (Category Map) → Diagram 3 (Signal vs Proxy) → Diagram 7 (Universal Box) |
| 🛠️ **Engineer evaluating to build** | §2 → Diagram 8 (Top-level arch) → Diagram 12 (Memory dual-adapter) → Diagram 6 (LLM orchestration) |
| 🤝 **AI engineer being recruited** | §1 first to engage, §2 second to convince. Pay attention to Diagrams 5 + 6 (substitutability proofs) |
| 📋 **Engineer tracking build progress** | §2 → Diagram 9 (Stage 9 sequence) — colors track status |

---

## Legend

| Color | Status | Meaning |
|---|---|---|
| 🟢 Green | `done` | Ratified, shipped, tests green |
| 🟡 Amber | `inflight` | Currently being built |
| ⚪ Gray dashed | `planned` | On roadmap, not started |
| 🔵 Blue | `deferred` | Authorized but parked (not blocking sequence) |

To update progress: find the node in the mermaid block and change the `:::status` suffix.

---

# §1 Why This Matters

*The bet, the moat, the buyer's perspective. Read these five before the architecture.*

---

## Diagram 1 — Category Map: The Empty Quadrant

**Question this answers:** "Is Verdaca just another agent framework?"

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px', 'quadrant1Fill': '#86efac', 'quadrant2Fill': '#fef3c7', 'quadrant3Fill': '#e0e7ff', 'quadrant4Fill': '#fecaca'}}}%%
quadrantChart
    title Where Verdaca lives
    x-axis Cheap --> Expensive
    y-axis Resets --> Compounds
    quadrant-1 ⭐ Verdaca
    quadrant-2 Consulting
    quadrant-3 Direct LLMs
    quadrant-4 Agent frameworks
    ChatGPT: [0.15, 0.10]
    LangChain: [0.55, 0.20]
    Hermes: [0.35, 0.45]
    McKinsey: [0.95, 0.85]
    Verdaca: [0.20, 0.90]
```

**Caption:** *The empty quadrant is the bet. The question is no longer "why Verdaca?" — it's "why isn't anyone else here yet?" The answer is in Diagram 3.*

---

## Diagram 2 — Buyer's Journey: What $2.50 and 12 Minutes Buys

**Question this answers:** "What do I actually get?"

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart LR
    Q["Strategic Question<br/>e.g. 'Should we acquire X?'"]:::input
    S["Session Start<br/>~30 sec config"]:::process
    M["12-min deliberation<br/>8 agent perspectives<br/>3 critique cycles"]:::process
    D["Structured Deliverable<br/>Decision memo<br/>+ 12 quality scores<br/>+ minority report<br/>+ provenance"]:::output
    T["Trust Artifacts<br/>Gate scores · Beat counts<br/>Replay traceability"]:::trust

    Q --> S --> M --> D --> T

    classDef input fill:#fef3c7,stroke:#92400e,stroke-width:2px,color:#000
    classDef process fill:#e0e7ff,stroke:#4338ca,stroke-width:2px,color:#000
    classDef output fill:#86efac,stroke:#16a34a,stroke-width:3px,color:#000
    classDef trust fill:#bfdbfe,stroke:#2563eb,stroke-width:2px,color:#000
```

**Caption:** *Most AI products end at "Structured Deliverable." Verdaca delivers the trust artifacts too — every decision is replayable, every score auditable, every dissent captured. That's the difference between an answer you take to a meeting and an answer you take to a board.*

---

## Diagram 3 — Signal vs Proxy: The Moat Competitors Can't Replicate

**Question this answers:** "Why can't a competitor just copy this?"

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart LR
    subgraph COMPETITORS["Hermes · LangChain · AutoGen · CrewAI"]
        H1["Skill used"] --> H2["use_count++"]
        H2 --> H3["Curator infers quality<br/>from usage frequency"]
        H3 --> H4["Proxy signal — weak"]:::weak
        H4 -.-> H5["Patch proposal<br/>maybe right, maybe not"]:::weak
    end

    subgraph VERDACA["Verdaca"]
        V1["MAC 3 cycles"] --> V2["12 quality gates<br/>scored 0–10"]
        V2 --> V3["Beat counts<br/>+ halt dispositions"]
        V3 --> V4["Direct ground truth — strong"]:::strong
        V4 -.-> V5["Patch proposal<br/>against measured outcome"]:::strong
    end

    classDef weak fill:#fecaca,stroke:#dc2626,stroke-width:1px,color:#000
    classDef strong fill:#86efac,stroke:#16a34a,stroke-width:3px,color:#000
```

**Caption:** *Both produce skill patches. Only one knows whether the skill actually worked. To replicate Verdaca, a competitor must first build the MAC quality-gate methodology — but they're optimizing for individual-developer breadth, not enterprise deliberation depth. They're not going to.*

---

## Diagram 4 — Trust Stack: Why Outputs Are Defensible

**Question this answers:** "If I take this memo to my board, can I defend it?"

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart TB
    O["Verdaca Output<br/>(decision memo)"]:::output

    O --> L1["Layer 1 — 12 gate scores<br/>quantitative confidence"]:::layer
    O --> L2["Layer 2 — 8-agent provenance<br/>which voice said what"]:::layer
    O --> L3["Layer 3 — Minority report<br/>dissenting positions captured"]:::layer
    O --> L4["Layer 4 — Replay traceability<br/>session reproducible byte-for-byte"]:::layer
    O --> L5["Layer 5 — Human validation<br/>A4 Spearman ρ ≥ 0.6<br/>(currently deferred — caveat applied)"]:::deferred

    classDef output fill:#86efac,stroke:#16a34a,stroke-width:3px,color:#000
    classDef layer fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#000
    classDef deferred fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#000,stroke-dasharray: 5 5
```

**Caption:** *Layer 5 is dashed because A4 human validation is deferred to Stage 7 debt clearance — every Verdaca metric citation today carries the caveat "(internal scoring; A4 deferred)" verbatim. Honesty here is the sales lever. Buyers trust roadmaps they can verify.*

---

## Diagram 5 — Contract-Test Gate: The Substitutability Proof

**Question this answers:** "How do you avoid provider lock-in structurally, not aspirationally?"

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart LR
    K["kernel/memory facade<br/>calls MemoryPort"]:::done
    P["MemoryPort Protocol<br/>5 methods: store · query<br/>promote · revoke_promotion · migrate"]:::done
    G{"Contract-Test Gate<br/>18 MAC-T<br/>4 PROMO tests parametric<br/>across both adapters"}:::gate
    M["adapters/mem0/<br/>Mem0 SDK 1.0.11"]:::done
    L["adapters/letta/<br/>letta-client ≥1.10"]:::done

    K --> P
    P --> G
    G -.proves.-> M
    G -.proves.-> L
    M -.runtime swap.-> L

    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
    classDef gate fill:#fbbf24,stroke:#92400e,stroke-width:3px,color:#000
```

**Caption:** *Swapping Mem0 for Letta is a config change. The 18 contract tests are the only thing that authorizes the swap. Hermes Agent, LangChain, AutoGen — none enforce this at the type-system layer. This is what "ports-and-adapters" actually buys: provider lock-in resistance proven by CI.*

---

---

## Diagram 6 — LLM Provider Substitutability + Model Orchestration

**Question this answers:** "Are we locked into one AI provider? How do you control cost?"

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart LR
    subgraph TASKS["MAC routes by task type — match cost to need"]
        direction TB
        T1["🧠 Strategic decisions<br/>frontier max thinking"]:::task
        T2["🛠️ Implementation work<br/>frontier high thinking"]:::task
        T3["📖 File reads × 30 parallel<br/>cheapest tier"]:::task
        T4["✍️ Mechanical drafting<br/>mid-tier"]:::task
        T5["🔁 MAC inner loops<br/>local inference"]:::task
    end

    PORT[("LLMProxyPort<br/>planned 9.4.5")]:::port

    subgraph PROVIDERS["Any provider plugs in via adapter"]
        direction TB
        P1["Anthropic Claude<br/>Opus 4.7 · Sonnet 4.6 · Haiku 4.5"]:::done
        P2["OpenAI / Azure OpenAI"]:::planned
        P3["OpenRouter — 200+ models"]:::planned
        P4["Hermes-3 local llama<br/>~$5/mo VPS"]:::planned
        P5["NVIDIA NIM self-hosted"]:::planned
    end

    T1 --> PORT
    T2 --> PORT
    T3 --> PORT
    T4 --> PORT
    T5 --> PORT

    PORT -.adapter.-> P1
    PORT -.adapter.-> P2
    PORT -.adapter.-> P3
    PORT -.adapter.-> P4
    PORT -.adapter.-> P5

    classDef task fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#000
    classDef port fill:#fbbf24,stroke:#92400e,stroke-width:3px,color:#000
    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
    classDef planned fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#000,stroke-dasharray: 5 5
```

**Caption:** *Two claims in one diagram. **Left:** MAC orchestrates by task type — decisions hit the frontier model, mechanical work hits cheaper tiers, parallel reads use the cheapest model 30 at a time. This is how `~$2.50 / session` is structurally achievable. **Right:** every provider sits behind one port — swap Anthropic for OpenAI for local Hermes-3 with a config change. The same contract-test pattern from Diagram 5 enforces the swap. Provider lock-in is solved structurally, not aspirationally.*

---

## Diagram 7 — Universal Box: One Kernel, Tunable Per Client

**Question this answers:** "Do you build a new product for each vertical, or is this configurable?"

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart LR
    subgraph CORE["The Box — universal kernel (same code for every client)"]
        direction TB
        K1["MAC 3-cycle engine"]:::core
        K2["12 quality gates"]:::core
        K3["Memory facade"]:::core
        K4["Compression + cost tracking"]:::core
    end

    subgraph TUNING["Per-client configuration (no engineering)"]
        direction TB
        C1["Agent roster<br/>which voices to convene"]:::tune
        C2["Gate weights<br/>what 'good' means here"]:::tune
        C3["Memory schema<br/>client vocabulary"]:::tune
        C4["Workflow template<br/>session shape"]:::tune
    end

    subgraph VERTICALS["Same box, different clients"]
        direction TB
        V1["M&A / corp dev<br/>(PE firms)"]:::vert
        V2["Exec hiring panels<br/>(search firms)"]:::vert
        V3["Product launches<br/>(go-to-market)"]:::vert
        V4["Vendor selection<br/>(enterprise IT)"]:::vert
        V5["Strategy retreats<br/>(Fortune 500)"]:::vert
    end

    CORE -.tuned by.-> TUNING
    TUNING -.configures.-> VERTICALS

    classDef core fill:#86efac,stroke:#16a34a,stroke-width:3px,color:#000
    classDef tune fill:#fbbf24,stroke:#92400e,stroke-width:2px,color:#000
    classDef vert fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#000
```

**Caption:** *Verdaca's kernel doesn't change per client. What changes is the agent roster, gate weights, memory schema, and workflow template — all YAML, no engineering. The same code that runs an M&A deliberation runs a hiring panel. **This is what "productized BMAD" actually means: the framework is the product, the tuning is the consulting.** A new vertical = configuration, not a new build.*

---

# §2 How It's Built

*Engineering progress tracker — port wiring, adapter status, supply-chain CI. Status colors track build state.*

---

## Diagram 8 — Top-Level Architecture (everything in one view)

```mermaid
flowchart LR
    subgraph SHELL["Shell"]
        direction TB
        UI["Next.js POV harness<br/>Clerk · Stripe"]:::done
    end

    subgraph KERNEL["Kernel"]
        direction TB
        MAC["mac — 3-cycle · 12 gates"]:::done
        STU["studio — workflow"]:::done
        MEM["memory — facade"]:::done
        COMP["compression — Caveman"]:::done
        RUN["runtime — 16 agents"]:::done
        PIM["pi-mono — cost"]:::done
        MAC ~~~ STU
        STU ~~~ MEM
        MEM ~~~ COMP
        COMP ~~~ RUN
        RUN ~~~ PIM
    end

    subgraph PORTS["Ports"]
        direction TB
        PM["MemoryPort"]:::done
        PS["SerializationPort"]:::done
        PV["VersionedStatePort"]:::done
        PC["CostMeterPort"]:::inflight
        PL["LLMProxyPort"]:::planned
        PSI["SessionIndexPort"]:::planned
        PSO["SkillObserverPort"]:::planned
        PSK["SkillPort"]:::planned
        PUM["UserModelPort"]:::planned
    end

    subgraph ADAPTERS["Adapters"]
        direction TB
        AB["beads/"]:::done
        AT["tonl/"]:::done
        AM0["mem0/"]:::done
        AL["letta/"]:::done
        APM["pi_mono_native/"]:::inflight
        ARTK["rtk/"]:::planned
        AF["forge/"]:::planned
        AH3["hermes_3/"]:::planned
        ASC["skill_curator/"]:::planned
        AHC["honcho/"]:::planned
    end

    subgraph TESTS["Tests"]
        direction TB
        T1["M-T-VS · SER · MEM (40)"]:::done
        T2["M-T-COST (8)"]:::inflight
        T3["M-T-SKILL (5)"]:::planned
        T1 ~~~ T2
        T2 ~~~ T3
    end

    SHELL --> KERNEL
    KERNEL --> PORTS
    PORTS --> ADAPTERS
    ADAPTERS -.verified.-> TESTS

    PM -.impl.-> AM0
    PM -.impl.-> AL
    PS -.impl.-> AT
    PV -.impl.-> AB
    PC -.impl.-> APM
    PL -.impl.-> ARTK
    PL -.impl.-> AH3
    PSK -.impl.-> ASC
    PUM -.impl.-> AHC

    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
    classDef inflight fill:#fde68a,stroke:#d97706,stroke-width:2px,color:#000
    classDef planned fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#000,stroke-dasharray: 5 5
    classDef deferred fill:#bfdbfe,stroke:#2563eb,stroke-width:2px,color:#000
```

---

## Diagram 9 — Stage 9 Sequence (Sub-Stage Progress)

```mermaid
flowchart LR
    S91["9.1<br/>Base"]:::done
    S92["9.2<br/>Ports arch v0.2"]:::done
    S93["9.3<br/>Test strategy v0.2"]:::done
    S941["9.4.1<br/>Beads"]:::done
    S942["9.4.2<br/>TONL"]:::deferred
    S943["9.4.3<br/>Memory dual"]:::done
    S944["9.4.4<br/>Pi-Mono A.2"]:::inflight
    S945["9.4.5<br/>RTK + LLMProxy"]:::planned
    S946["9.4.6<br/>Forge"]:::planned
    S947["9.4.7<br/>Atomic PR"]:::planned
    S948["9.4.8<br/>Upstream + FTS5"]:::planned
    S95["9.5<br/>Arch review"]:::planned
    S96["9.6<br/>Cleo supply-chain"]:::planned
    S99["9.9<br/>Test ratification"]:::planned

    S91 --> S92 --> S93 --> S941
    S941 --> S942
    S941 --> S943
    S943 --> S944
    S944 --> S945 --> S946 --> S947 --> S948 --> S95 --> S96 --> S99

    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
    classDef inflight fill:#fde68a,stroke:#d97706,stroke-width:2px,color:#000
    classDef planned fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#000,stroke-dasharray: 5 5
    classDef deferred fill:#bfdbfe,stroke:#2563eb,stroke-width:2px,color:#000
```

**Estimate:** ~12–17 sessions remaining in Stage 9.

---

## Diagram 10 — Stage 10 Self-Learning Pipeline (4-Phase Roadmap)

```mermaid
flowchart TB
    subgraph P0["Phase 0 — Do Now"]
        direction TB
        P0A["Provenance frontmatter tags"]:::planned
        P0B["track-skill-usage.py"]:::planned
        P0C["MAC telemetry JSON"]:::planned
    end

    subgraph P1["Phase 1 — Stage 9.4.8"]
        direction TB
        P1A["index-sessions.py FTS5"]:::planned
        P1B["wiki-update --index"]:::planned
    end

    subgraph P2["Phase 2 — Post-9.6 ports"]
        direction TB
        P2A["SessionIndexPort"]:::planned
        P2B["SkillObserverPort"]:::planned
        P2C["SkillPort + 5 tests"]:::planned
    end

    subgraph P3["Phase 3 — Stage 10 adapters"]
        direction TB
        P3A["skill_curator adapter"]:::planned
        P3B["honcho adapter"]:::planned
        P3C["Trajectory RL Atropos"]:::planned
    end

    LP["LLMProxyPort 9.4.5"]:::planned
    OPEN["OPEN: stub SkillEvolutionPort?<br/>resolve at 9.4.5 preload"]:::planned

    P0 --> P1 --> P2 --> P3
    LP -.prereq.-> P3A
    P2 -.gate.-> OPEN

    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
    classDef inflight fill:#fde68a,stroke:#d97706,stroke-width:2px,color:#000
    classDef planned fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#000,stroke-dasharray: 5 5
```

---

## Diagram 11 — MAC Outcome-Signal Flow (engineering view)

Engineering-internal view of the same moat shown in §1 Diagram 3 — but here the focus is on the signal pipeline (where data flows today vs Stage 10) rather than the competitive contrast.

```mermaid
flowchart LR
    INPUT["User input"] --> C1["MAC Cycle 1<br/>Propose"]:::done
    C1 --> C2["MAC Cycle 2<br/>Critique"]:::done
    C2 --> C3["MAC Cycle 3<br/>Refine"]:::done
    C3 --> G["12 Quality Gates<br/>gate scores · beat counts · dispositions"]:::done
    G --> OUTPUT["Strategic Output<br/>~$2.50 · ~12 min<br/>+47% vs vanilla"]:::done

    G -.signal flow today.-> HANDOFF["Handoff prose<br/>session-handoff-*.md<br/>signal discarded"]:::done
    G -.Phase 0 planned.-> TEL["skill-telemetry JSON<br/>per session"]:::planned
    TEL -.Stage 10.-> CUR["skill_curator adapter<br/>proposes skill patches"]:::planned
    CUR -.gated by.-> AUTH["authorized_by check<br/>human approves<br/>(M-T-SKILL-PATCH-02)"]:::planned
    AUTH -.applied to.-> SK[".claude/skills/*.md<br/>versioned via Beads"]:::planned

    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
    classDef inflight fill:#fde68a,stroke:#d97706,stroke-width:2px,color:#000
    classDef planned fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#000,stroke-dasharray: 5 5
```

---

## Diagram 12 — Memory Port: Dual-Adapter Reference Pattern

Engineering-internal worked example of the substitutability shown in §1 Diagram 5. Reference pattern for how new ports get their adapters (curator, Honcho at Stage 10).

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart TB
    KMEM["kernel/memory<br/>MemoryProtocol facade<br/>(10-method Draft/Record)"]:::done
    PORT["MemoryPort<br/>5 methods: store · query<br/>promote · revoke_promotion · migrate"]:::done

    KMEM --> PORT

    PORT -.PRIMARY.-> MEM0["adapters/mem0/<br/>Mem0 SDK 1.0.11<br/>hybrid vector + graph"]:::done
    PORT -.SUBSTITUTE.-> LETTA["adapters/letta/<br/>letta-client ≥1.10<br/>native passage-search"]:::done

    MEM0 -.verified by.-> CT["18 M-T-MEM-* contract tests<br/>4 PROMO tests dual-adapter parametric"]:::done
    LETTA -.verified by.-> CT

    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
```

---

## Diagram 13 — Stage 9.6 Cleo Supply-Chain (Dependency Automation)

What lands when 9.6 ratifies. Documents the future CI/CD pipeline for keeping provider versions current.

```mermaid
%%{init: {'themeVariables': {'fontSize': '18px'}}}%%
flowchart LR
    UPSTREAM["mem0ai / letta-client<br/>upstream releases"]:::done

    UPSTREAM -.detects.-> RENOVATE["Renovate Bot<br/>.github/renovate.json"]:::planned
    RENOVATE -.opens PR.-> CI["GitHub Actions<br/>contract-tests.yml"]:::planned

    CI -.runs.-> TESTS["40+ MAC-T contract tests<br/>uv run pytest tests/"]:::planned

    TESTS -.PASS + PATCH.-> AUTO["Auto-merge<br/>(no human)"]:::planned
    TESTS -.PASS + MINOR.-> REVIEW["Winston review<br/>API delta check"]:::planned
    TESTS -.PASS + MAJOR.-> HALT["Full halt-cycle<br/>Andrey go required"]:::planned
    TESTS -.FAIL.-> BLOCK["PR blocked"]:::planned

    AUDIT["audit.yml<br/>weekly cron<br/>pip-audit + npm audit"]:::planned -.CVE detected.-> ISSUE["GitHub issue<br/>opened automatically"]:::planned

    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
    classDef planned fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#000,stroke-dasharray: 5 5
```

---

## Status Update Workflow

When a node changes state, edit the `:::status` suffix in the relevant mermaid block and update the "Last refreshed" line at the top. Status transitions:

- `planned` → `inflight` — when an executor opens a chat for that work
- `inflight` → `done` — when the close-handoff merges to main and CI is green
- `planned` → `deferred` — when team-lead authorizes deferred-work parallel launch (not blocking sequence)

Optionally commit the diagram update alongside the work — diagrams become part of the close-handoff §provenance trail.
