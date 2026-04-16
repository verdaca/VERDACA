# PRAXIS BUILD PIPELINE — Index

**Purpose:** Master index for the Praxis build pipeline documentation. The original monolithic Pipeline.md has been split into focused documents for easier navigation.

**Status:** All 7 stages complete. **READY TO SELL — 2026-04-16.** (Internal scoring; A4 human validation deferred.)

---

## Pipeline Documents

| Document | Contents | When to read |
|----------|----------|--------------|
| [Pipeline Stages](pipeline-stages.md) | Sections 1-3: Bootstrap protocol, dependency flow, full 7-stage status tracker with all checkboxes, ratification anchors, and gate decisions | Understanding what was built and in what order |
| [Methodology](methodology.md) | Sections 4, 4.5, 4.6: Agent invocation chain, elicitation framework per stage, model/thinking effort strategy, sequential reference reading rule | Reusing the BMAD methodology for future projects |
| [Operations](operations.md) | Sections 5, 6, 7, 8, 10, 11: Gate conditions, file path registry, context window handoff protocol, alignment review protocol, emergency reference shortcuts, command quick reference | Day-to-day operational runbook |
| [Session Log](session-log.md) | Section 9: Chronological session entries from 2026-04-12 through 2026-04-13 | Historical context on decisions and handoffs |

---

## Architecture & Planning Documents

| Document | Contents | When to read |
|----------|----------|--------------|
| [Build Plan](build-plan.md) | Full 7-stage build sequence (measure-first approach) | Understanding the overall build strategy |
| [Box Architecture](box-architecture.md) | 5-layer "box" technical specification | Understanding the Praxis kernel structure |
| [Hybrid Architecture](hybrid-architecture.md) | 8-layer best-of-breed analysis with component selection rationale | Understanding why each component was chosen |

---

## Reading Order for New Sessions

1. **This file** — orient yourself
2. **[Pipeline Stages](pipeline-stages.md)** Section 1 (Bootstrap) — verify prerequisites
3. **[Pipeline Stages](pipeline-stages.md)** Section 3 (Status Tracker) — find current state
4. **[Operations](operations.md)** Section 5 (Gate Conditions) — verify gates before starting work
5. **[Methodology](methodology.md)** — understand the agent chain and elicitation approach for the current stage

---

## Quick Lookup

| I need to know... | Find it at... |
|-------------------|---------------|
| Current stage status | [Pipeline Stages](pipeline-stages.md) Section 3 |
| Agent invocation order | [Methodology](methodology.md) Section 4 |
| Elicitation methods per stage | [Methodology](methodology.md) Section 4.5 |
| Model/thinking defaults | [Methodology](methodology.md) Section 4.6 |
| Gate conditions | [Operations](operations.md) Section 5 |
| File path registry | [Operations](operations.md) Section 6 |
| Context handoff protocol | [Operations](operations.md) Section 7 |
| Alignment review protocol | [Operations](operations.md) Section 8 |
| Session history | [Session Log](session-log.md) |
| Build plan | [Build Plan](build-plan.md) |
| Technical architecture | [Box Architecture](box-architecture.md) |
| Component selection rationale | [Hybrid Architecture](hybrid-architecture.md) |
