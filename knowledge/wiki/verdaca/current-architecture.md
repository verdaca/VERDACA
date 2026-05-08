# Verdaca — What Is Actually Built

**Compiled:** 2026-05-08 | **HEAD:** `1a42896`

---

## Stages 1–7: COMPLETE (original pipeline)

All seven original stages shipped as of **2026-04-16**. These are production-level implementations.

| Stage | What shipped | Key metric |
|---|---|---|
| 1 Pi-Mono | Cost tracker with `decimal.Decimal`, per-agent/session/workflow aggregation | Baseline measurement live |
| 2 Compression | `kernel/compression/` — Caveman dialect system (caveman_english + wenyan + base), orchestrator, telemetry, gate, boundary, config | 14.32% token reduction measured |
| 3 Memory | Full `kernel/memory/` module — MemoryProtocol facade, 10-method Draft/Record pattern | 58.6% cost savings on similar tasks |
| 4 Agent Runtime | 16 BMAD agents loadable; capability registry; spawner; MCP adapter scaffold | 16 agents loadable |
| 5 MAC | 3-cycle MAC with 12 quality gates; information asymmetry router; cross-session learning loop | +47% vs vanilla (internal; A4 deferred) |
| 6 Studio | `strategic_session.yaml` workflow template; Mary/Victor/John/Winston/Dr.Quinn/Carson/Sophia/Caravaggio | ~$2.50 / ~12 min / 95.79% coverage |
| 7 POV Harness | Next.js UI shell; Clerk auth; Stripe billing; webhook delivery; onboarding | Signup→result ~5.5 min; 91.94% coverage |

---

## Stage 9: Ports-and-Adapters Production Rewrite

Stage 9 is a **parallel production-grade rebuild** of the kernel internals using proper ports-and-adapters. The Stage 1-7 implementation remains functional; Stage 9 replaces the internals with a clean adapter seam architecture.

### What exists in the repo root (tracked, production-grade)

```
ports/                    25 files — Protocol definitions
  src/praxis/ports/
    memory.py             MemoryPort Protocol (5 methods: store, query, promote, revoke_promotion, migrate)
    serialization.py      SerializationPort (168 LOC, PEP 695 type aliases, Python ≥3.12)
    versioned_state.py    VersionedStatePort
    cost_meter.py         IN PROGRESS (9.4.4 Phase A.2)

adapters/                 47 files — Concrete adapter implementations
  beads/                  VersionedState adapter (264 LOC, greenfield in-tree, 10/10 M-T-VS-* GREEN)
  tonl/                   Serialization adapter (~333 LOC, wraps kernel/compression/tonl, 12 M-T-SER-* catalog)
  mem0/                   Memory primary adapter (Mem0 SDK v1.0.11, 5 Protocol methods, OTEL spans)
  letta/                  Memory substitute adapter (letta-client ≥1.10, <2.0; native passage-search)
  pi_mono_native/         IN PROGRESS (9.4.4 Phase B)

tests/                    18 files — Contract test catalog
  src/praxis/contract_tests/ports/
    test_versioned_state_contract.py    10 M-T-VS-* (all green)
    test_serialization_contract.py      12 M-T-SER-* (10 pass + 2 pytest.skip)
    test_memory_contract.py             18 M-T-MEM-* (4 PROMO no_waiver dual-adapter parametric)

kernel/                   2,802 files — Original implementation (still active)
  compression/src/praxis/kernel/compression/
    orchestrator.py
    telemetry.py
    config.py
    caveman/              8 Python files (compressor, gate, boundary, models, provider, validate, errors, __init__)
    caveman/dialects/     base.py, caveman_english.py, wenyan.py
  memory/                 MemoryProtocol facade (10-method)
  mac/                    3-cycle iteration controller + 12 quality gates
  runtime/                16 BMAD agent loader + spawner + MCP adapter
  pi-mono/                Cost tracker
  studio/                 Studio workflow template

shell/                    POV harness (Next.js UI + API)
scripts/                  Build tooling
docs/                     Pipeline tracking (Pipeline.md = 168KB — ground truth)
```

### uv workspace members
`ports` · `adapters/beads` · `adapters/tonl` · `adapters/mem0` · `adapters/letta` · `tests` · `kernel/compression` · `kernel/mac` · `kernel/memory` · `kernel/pi-mono/src` · `kernel/runtime` · `kernel/studio`

`shell/` deferred from workspace (pytest-asyncio constraint conflict).

---

## Technology Stack Active

| Layer | Tech | Version |
|---|---|---|
| Language | Python | 3.12.12 (pinned in `.python-version`) |
| Package manager | uv | workspace with `uv.lock` (87 pkgs, 10 members) |
| Memory adapter | mem0ai | 1.0.11 (PyPI) |
| Memory substitute | letta-client | ≥1.10, <2.0 |
| Serialization | tree-sitter + TONL in-tree | Python 3.12 |
| UI | Next.js 15 + Tailwind 4 + shadcn/ui | — |
| Auth | Clerk | — |
| Billing | Stripe | — |
| Observability | OpenTelemetry (OTEL) | provisional RATIFIED at 5.5 |
| Test framework | pytest + pytest-asyncio | — |
| Linting | ruff + mypy strict | — |

---

## Stage 7 Debt Ledger (19 items, deferred to "Stage 8")

Not blocking forward work. Key items:

- **C-4 Memory `mac.reuse_successful` promotion path** — LATENT Stage-7 blocker; must resolve before headline becomes unconditional
- **A4 Spearman ρ ≥ 0.6 human validation** — headline caveat "(internal scoring; A4 deferred)" until resolved
- W-1..W-7 Cleo WARNINGs from Stage 5.3.5
- C-1..C-5 cross-stage architecture contradictions (C-4 is the live blocker)
- PDF + `.pptx` export (ADR-08, deferred)
- "Built With Praxis/Verdaca" public dashboard badge
