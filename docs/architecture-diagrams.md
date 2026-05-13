# Verdaca — Architecture Diagrams

**Purpose:** Visual progress tracker for the Verdaca build. Update the status class on a node when it moves between states. Renders in GitHub, GitLab, VS Code preview, Obsidian, and most markdown viewers with mermaid support.

**Last refreshed:** 2026-05-13 | **HEAD at refresh:** `97ceb6d`

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

## 1. Top-Level Architecture (everything in one view)

```mermaid
flowchart TB
    subgraph SHELL["Shell — User-Facing"]
        UI["Next.js 15 POV harness<br/>Clerk · Stripe · Webhooks"]:::done
    end

    subgraph KERNEL["Kernel — Domain Logic"]
        MAC["kernel/mac<br/>3-cycle · 12 quality gates"]:::done
        STU["kernel/studio<br/>Strategic session workflow"]:::done
        MEM["kernel/memory<br/>MemoryProtocol facade"]:::done
        COMP["kernel/compression<br/>Caveman dialects"]:::done
        RUN["kernel/runtime<br/>16 BMAD agents · MCP"]:::done
        PIM["kernel/pi-mono<br/>Decimal cost tracker"]:::done
    end

    subgraph PORTS["Ports — Protocol Contracts"]
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

    subgraph ADAPTERS["Adapters — Concrete Implementations"]
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

    subgraph TESTS["Contract Tests — tests/"]
        T1["M-T-VS-* (10)<br/>M-T-SER-* (12)<br/>M-T-MEM-* (18)"]:::done
        T2["M-T-COST-* (8)"]:::inflight
        T3["M-T-SKILL-* (5)"]:::planned
    end

    SHELL --> KERNEL
    KERNEL --> PORTS
    PORTS --> ADAPTERS
    ADAPTERS -.contract verified by.-> TESTS

    PM -.implemented by.-> AM0
    PM -.implemented by.-> AL
    PS -.implemented by.-> AT
    PV -.implemented by.-> AB
    PC -.implemented by.-> APM
    PL -.implemented by.-> ARTK
    PL -.implemented by.-> AH3
    PSK -.implemented by.-> ASC
    PUM -.implemented by.-> AHC

    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
    classDef inflight fill:#fde68a,stroke:#d97706,stroke-width:2px,color:#000
    classDef planned fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#000,stroke-dasharray: 5 5
    classDef deferred fill:#bfdbfe,stroke:#2563eb,stroke-width:2px,color:#000
```

---

## 2. Stage 9 Sequence — Sub-Stage Progress

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

## 3. Stage 10 Self-Learning Pipeline (4-Phase Roadmap)

```mermaid
flowchart TB
    subgraph P0["Phase 0 — Do Now (zero LLM cost)"]
        P0A["Provenance frontmatter<br/>on all .claude/skills/*.md"]:::planned
        P0B["scripts/track-skill-usage.py<br/>.usage.json sidecars"]:::planned
        P0C["MAC telemetry capture<br/>knowledge/raw/skill-telemetry/"]:::planned
    end

    subgraph P1["Phase 1 — at Stage 9.4.8"]
        P1A["scripts/index-sessions.py<br/>SQLite FTS5 over handoffs<br/>knowledge/sessions.db"]:::planned
        P1B["/verdaca-wiki-update --index<br/>flag added"]:::planned
    end

    subgraph P2["Phase 2 — Post-9.6 (port stubs)"]
        P2A["SessionIndexPort<br/>ports/session_index.py"]:::planned
        P2B["SkillObserverPort<br/>ports/skill_observer.py"]:::planned
        P2C["SkillPort<br/>ports/skill.py<br/>+ 5 M-T-SKILL-* tests"]:::planned
        P2D["⚠️ OPEN: stub SkillEvolutionPort now?<br/>Victor vs Winston debate<br/>Resolve at 9.4.5 preload"]:::planned
    end

    subgraph P3["Phase 3 — Stage 10 (adapters)"]
        P3A["adapters/skill_curator/<br/>uses LLMProxyPort + MAC signal<br/>apply_patch requires authorized_by"]:::planned
        P3B["adapters/honcho/<br/>UserModelPort behavioral profile"]:::planned
        P3C["Trajectory RL via Atropos<br/>after 500+ rated MAC sessions"]:::planned
    end

    P0 --> P1 --> P2 --> P3
    P3A -.depends on.-> LP["LLMProxyPort 9.4.5"]:::planned

    classDef done fill:#86efac,stroke:#16a34a,stroke-width:2px,color:#000
    classDef inflight fill:#fde68a,stroke:#d97706,stroke-width:2px,color:#000
    classDef planned fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#000,stroke-dasharray: 5 5
```

---

## 4. MAC Outcome-Signal Flow (the moat, today vs planned)

This diagram shows Verdaca's structural advantage over competitor agent frameworks: MAC produces **direct quality signals** that today flow to handoff prose and get discarded. Stage 10 captures them and feeds a curator.

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

## 5. Memory Port — Adapter Strategy (worked example of dual-adapter pattern)

Reference pattern for how new ports get adapters. Useful for understanding how Stage 10 curator + Honcho adapters will land.

```mermaid
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

## 6. Stage 9.6 Cleo Supply-Chain — Dependency Automation

What lands when 9.6 ratifies. Documents the future CI/CD pipeline for keeping provider versions current.

```mermaid
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
