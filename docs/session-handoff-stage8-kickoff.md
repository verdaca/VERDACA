# Session Handoff — Stage 8 Kickoff (Production Hardening + Deployment)

**Written:** 2026-04-16
**Target session:** Fresh Claude Code context window starting Stage 8
**Author:** Team-lead coordinator (Opus 4.6 [1M])

---

## FIRST MESSAGE TO PASTE IN NEW SESSION

Copy everything below the line into a fresh Claude Code session opened in `C:\Users\AndreyPopov\Documents\Anthropic\`:

---

You are the team-lead coordinator for Praxis Stage 8 — Production Hardening + Deployment.

## Project Context

Praxis is a multi-agent reasoning engine for strategic advisory. It was built in 7 stages over 8 days using the BMAD framework. All 7 stages are complete and the repo has been restructured into a clean layout.

**Repo:** https://github.com/vospr/PRAXIS
**Local:** `C:\Users\AndreyPopov\Documents\Anthropic\`

### Repo Structure (just restructured — this is the current state)

```
/ (repo root)
├── README.md
├── .gitignore
├── kernel/
│   ├── pi-mono/          Stage 1 — cost tracking (36 .py, 3,432 LoC)
│   ├── compression/      Stage 2 — TONL+Forge+Caveman+RTK (81 .py, 8,510 LoC)
│   ├── memory/           Stage 3 — Beads+Mem0+Atelier facade (49 .py, 7,468 LoC)
│   ├── runtime/          Stage 4 — multi-agent orchestration (128 .py, 9,554 LoC)
│   ├── mac/              Stage 5 — Meta-Agent Controller (147 .py, 13,299 LoC)
│   └── studio/           Stage 6 — workflow templates (36 .py, 4,046 LoC)
├── shell/                Stage 7 — Next.js + FastAPI web app
│   ├── api/              FastAPI backend (17 .py files)
│   ├── web/              Next.js frontend (17 .tsx/.ts files)
│   └── tests/            107 tests, 91.94% backend coverage
└── docs/
    ├── pipeline.md               Index linking to split docs below
    ├── pipeline-stages.md        Stages 1-7 build history (all [x])
    ├── pipeline-stage8.md        YOUR WORKING DOCUMENT — Stage 8 checklist
    ├── methodology.md            BMAD agent chain + elicitation framework
    ├── operations.md             Runbook (paths updated to kernel/ layout)
    ├── session-log.md            Historical session entries
    ├── build-plan.md             Strategic build sequence
    ├── box-architecture.md       5-layer technical spec
    └── hybrid-architecture.md    Component selection analysis
```

### Key Metrics (Stages 1-7 complete)

- 49,700 Python LoC across 477 .py files
- 415+ tests (MAC 211, Studio 97, Shell 107)
- Coverage: MAC 94%, Studio 96%, Shell 92%
- Quality: +47% vs vanilla, +21% vs enhanced single-agent (internal scoring, A4 pending)
- Cost: ~$2.50/deep session, ~$0.80/quick
- Time: ~12 min deep, ~4 min quick

### Test Baselines to Preserve

| Module | Baseline | Location |
|---|---|---|
| MAC | 211 passed, 30 skipped | kernel/mac/tests/ |
| Studio | 97 passed, 19 deselected | kernel/studio/tests/ |
| Shell | 100 passed, 7 deselected | shell/tests/ |

These baselines must be preserved through all Stage 8 work. Verify at session start.

## Stage 8 Pipeline

Your working document is `docs/pipeline-stage8.md` (842 lines). It has:
- 8 sub-stages (8.1 Deployment → 8.8 Launch)
- Dependency flow diagram
- Checkbox tracker
- Agent assignments with model/thinking levels
- Gate conditions between sub-stages
- Pre-flight checklist

**Read it fully before starting any work.**

## What Stage 8 Builds

Stage 8 takes Praxis from "code works locally with fakes" to "customers can use it in production":

1. **8.1 Deployment Infrastructure** — Dockerfile, Docker Compose, Neon Postgres + Alembic migrations, Vercel, CI/CD
2. **8.2 Debt Ledger Resolution** — 19 carried items from Stages 5-7 (Cleo WARNINGs, naming drift, etc.)
3. **8.3 Production Wiring** — Replace ALL 7 Fake* classes with real integrations (Clerk, Stripe, Pi-Mono, Memory, Studio)
4. **8.4 Monorepo Tooling** — Root pyproject.toml, uv workspace, pre-commit hooks
5. **8.5 Credit Packs + Enterprise** — Event-triggered (not immediate)
6. **8.6 Observability** — Sentry, Plausible, health checks
7. **8.7 A4 Human Validation** — Spearman scoring (may run in parallel)
8. **8.8 Launch** — Domain, DNS, SSL, first 10-founder outreach

## Binding Constraints

1. **Billing:** CLI mode via Claude Max subscription. `ANTHROPIC_API_KEY` must be UNSET. Do NOT set it.
2. **Stage-gate enforcement:** Never advance sub-stages without Pipeline checkboxes complete + explicit "continue" from Andrey. (Memory: `feedback_praxis_stage_gates.md`)
3. **Memory writes require authorization:** Never write new memory files or update MEMORY.md on agent initiative. Propose content, wait for explicit go. (Memory: `feedback_memory_authorization.md`)
4. **Preload-first gating:** Before any BMAD agent drafts, force a structured preload report + explicit go. (Memory: `feedback_preload_first_gating.md`)
5. **no_waiver discipline:** Never add @pytest.mark.no_waiver on agent initiative. (Memory: `feedback_no_waiver_discipline.md`)
6. **Frozen artifacts:** kernel/mac/ and kernel/studio/ source code is frozen from Stages 5-6. Stage 8.2 debt resolution may unfreeze specific files — get explicit authorization per file.
7. **A4 caveat:** All headline quality figures must carry "(Internal scoring; A4 deferred)" until Stage 8.7 passes ρ ≥ 0.6.

## Architecture Documents to Read (per sub-stage)

| Sub-stage | Read first |
|---|---|
| 8.1 | `shell/architecture.md` §12 (Deployment), §14 (Launch Checklist) |
| 8.2 | `shell/alignment-review.md` §6 (19-item debt ledger), `kernel/mac/code-review.md`, `kernel/studio/code-review.md`, `shell/code-review.md` |
| 8.3 | `shell/architecture.md` §10 (Integration Contracts), each kernel module's `architecture.md` |
| 8.4 | Each module's `pyproject.toml` for dependency inventory |
| 8.6 | `shell/architecture.md` §11 (Observability) |
| 8.7 | `kernel/mac/a4-sampling-blinded.md` (DO NOT read `a4-sampling-mapping.md` — operator-only) |

## Established Precedents (from Stages 5-7)

1. **Path-A/§D hybrid for synthesis VOC** — when no real data, use synthesis + [HYPOTHETICAL] flags
2. **HARD-constraint enforcement is word-boundary** — `\bTOKEN\b` grep, not naive substring
3. **Additive-only __init__.py changes** — permitted without re-opening step-N source files
4. **Shell adapters, not MAC unfreezing** — C-2/C-3/C-4 resolved via ShellCostAdapter + ShellMemoryAdapter, NOT by modifying MAC source

## Immediate First Action

1. Read `docs/pipeline-stage8.md` fully
2. Complete the Pre-Flight Checks (verify Stages 1-7 all [x], verify repo structure, verify billing mode)
3. Report back with a structured preload summary: what you read, what you understood, any open questions
4. Wait for my "go" before any implementation work

Do NOT start implementing. Start by reading and reporting.

---

## Notes for Andrey

### Before starting the new session:
- The new session should be opened in the same working directory (`C:\Users\AndreyPopov\Documents\Anthropic\`)
- Use Opus 4.6 [1M] for the coordinator role (it needs to hold multiple architecture docs)
- The BMAD skills referenced in pipeline-stage8.md are available via the installed `.claude/skills/` directory
- The _bmad-output/ directory still exists on disk (just gitignored) — session handoffs and planning artifacts are still accessible if needed

### Account/service provisioning needed before 8.1:
- [ ] Domain name (praxis.ai or equivalent)
- [ ] Neon Postgres account (free tier)
- [ ] Clerk account (free tier)
- [ ] Stripe account (test mode)
- [ ] Vercel account (free tier)
- [ ] Sentry account (free tier)

These can be set up in parallel with the new session's preload phase.

### A4 scoring can run NOW:
The blinded package is at `kernel/mac/a4-sampling-blinded.md`. You can score the 9 outputs (27 cells, ~15-30 min) independently of Stage 8 engineering. If ρ ≥ 0.6, the caveat drops at 8.7 with zero additional work.
