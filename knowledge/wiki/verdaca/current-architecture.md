# Verdaca — What Is Actually Built

**Compiled:** 2026-05-08 → **Updated:** 2026-05-24 (Stage 10 RATIFIED via merge `8ae4f87`) | **HEAD (local main):** `8ae4f87` (Stage 10 RATIFIED merge) | **origin/main HEAD:** `e9c0643` (local 5 commits ahead via Stage 10 RATIFIED merge — push pending team-lead authorization); Stage 10 SessionIndex + SkillTelemetry data-plane now in `main` via merge of `da47d67` (close memo) + `3d576a9` (VOC gate marker) + `d2b5670` (Stage 10 impl)

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

## Stage 9: Ports-and-Adapters Production Rewrite — RATIFIED 2026-05-20

Stage 9 is the **parallel production-grade rebuild** of the kernel internals using proper ports-and-adapters. RATIFIED at `origin/main` merge `76eea26` (CI close `3e26f48` #40). The Stage 1-7 implementation remains functional; Stage 9 replaces the internals with a clean adapter seam architecture. 9.4.2 TONL is the only sub-stage that remains deferred-work (authorized separate launch).

### What exists in the repo root (tracked, production-grade)

```
ports/                    Protocol definitions
  src/praxis/ports/
    memory.py             MemoryPort Protocol (5 methods: store, query, promote, revoke_promotion, migrate)
    serialization.py      SerializationPort (168 LOC, PEP 695 type aliases, Python ≥3.12)
    versioned_state.py    VersionedStatePort
    cost_meter.py         ✅ COMPLETE (9.4.4) — 7 DTOs (CostRecord, CostSummary, CostQuery, BillingEvent, UsageReport, ThrottleSignal, BudgetAlert)
    llm_proxy.py          ✅ COMPLETE (9.4.5) — 4 DTOs + Message sibling + 2 errors; LLMProxyPort Protocol
    compaction.py         ✅ COMPLETE (9.4.6) — 3 DTOs (CompactionRequest, CompactionResult, CompactionEstimate) + 3 errors (TokenBudgetUnreachable, PreservedSpanEvicted, DeterminismViolation); CompactionPort Protocol; v0.2.6 — no StrategyDowngrade (downgrade-as-return via CompactionResult.strategy_applied); compute_determinism_hash content-derived
    common.py             Shared DTOs (Message sibling-add at 9.4.5 A.2)

adapters/                 Concrete adapter implementations
  beads/                  VersionedState adapter (264 LOC, greenfield in-tree, 10/10 M-T-VS-* GREEN)
  tonl/                   Serialization adapter (~333 LOC, wraps kernel/compression/tonl, 12 M-T-SER-* catalog; 9.4.2 deferred-work)
  mem0/                   Memory primary adapter (Mem0 SDK v1.0.11 SHA-pinned, 5 Protocol methods, OTEL spans, 18 M-T-MEM-*)
  letta/                  Memory substitute adapter (letta-client ==1.10.3 SHA-pinned; native passage-search)
  pi_mono_native/         ✅ COMPLETE (9.4.4) — in-tree-native Python pricing math; 8 M-T-COST-*; ADR-9.2-V4
  litellm/                ✅ COMPLETE (9.4.5) — LiteLLM PyPI library adapter (litellm==1.83.14 SHA-pinned); 7 M-T-LLM-*; ADR-9.2-V5 v0.6; sole LLMProxyPort substrate (Docker sidecar retired via H2-falsification); DIAL api_base routing landed at Phase 0 P0.3 `40dc556`
  in_tree_compaction_stub/ ✅ COMPLETE (9.4.6) — 5 files, permanent CI fallback; supports `lossless` + `lossy_eviction` (downgrades `lossy_summary`); `UPSTREAM_KIND="in_tree"`
  llmlingua/              ✅ COMPLETE (9.4.6) — LLMLingua PyPI library adapter (llmlingua==0.2.2 SHA-pinned, MIT); wraps `PromptCompressor`; substrate-truth probe PASS-DEGRADED (hard-budget emulated; determinism via hardcoded seed=42); ADR-9.2-V6 v0.7

tests/                    20 files — Contract test catalog
  src/praxis/contract_tests/ports/
    test_versioned_state_contract.py    10 M-T-VS-* (all green)
    test_serialization_contract.py      12 M-T-SER-* (10 pass + 2 pytest.skip)
    test_memory_contract.py             18 M-T-MEM-* (4 PROMO no_waiver dual-adapter parametric)
    test_cost_meter_contract.py         8 M-T-COST-* (all green)
    test_llm_proxy_contract.py          7 M-T-LLM-* (single-adapter post H2-falsification)
    test_compaction_contract.py         14 M-T-COMP-* (parametrized {in-tree stub, LLMLingua}; OD-2 inverse-downgrade asymmetry coverage; 3 bearers on no_waiver allow-list)
    test_no_waiver_inventory.py         Stage-9 enforcer (added 9.9 `ef401a2`, un-skipped at 9.6 `3e26f48`); STAGE9_NO_WAIVER_ALLOWLIST frozenset cardinality=9

kernel/                   2,802 files — Original implementation (still active)
  compression/src/praxis/kernel/compression/
    orchestrator.py
    telemetry.py
    config.py
    caveman/              8 Python files (compressor, gate, boundary, models, provider, validate, errors, __init__); HaikuProvider routes via LLMProxyPort (Phase 0 P0.1 `0fef796`)
    caveman/dialects/     base.py, caveman_english.py, wenyan.py
  memory/                 MemoryProtocol facade (10-method)
  mac/                    3-cycle iteration controller + 12 quality gates; LLMJudgeClient.call_live() routes via LLMProxyPort (Phase 0 P0.2 `f75ab7b`)
  runtime/                16 BMAD agent loader + spawner + MCP adapter; repo-root pathwalk fixed at 9.5 `e7bd77d` (3 files via `git rev-parse --show-toplevel` + assert sentinels)
  pi-mono/                Cost tracker
  studio/                 Studio workflow template

scripts/
  index-sessions.py       ✅ NEW (9.4.8 `2b7cbf3`) — SQLite FTS5 indexer over knowledge/raw/session-handoffs/*.md → knowledge/sessions.db; stdlib-only (~50 LOC); idempotent; consumed by `/verdaca-wiki-update --index`

knowledge/
  sessions.db             Generated build artifact (gitignored); FTS5 session corpus

.github/                  ✅ NEW (9.6 `3e26f48`)
  renovate.json           Dependency monitoring + auto-merge policy
  workflows/contract-tests.yml  CI contract-test gate on `adapters/**` + `uv.lock` PRs
  workflows/audit.yml     Weekly `pip-audit --require-hashes` + `npm audit` cron

shell/                    POV harness (Next.js UI + API)
docs/                     Pipeline tracking + stage handovers (untracked since `effa9ad` 2026-05-15)
```

### uv workspace members (13 active + 1 deferred, audited at 9.6)
`ports` · `adapters/beads` · `adapters/tonl` · `adapters/mem0` · `adapters/letta` · `adapters/pi_mono_native` · `adapters/litellm` · `adapters/in_tree_compaction_stub` · `adapters/llmlingua` · `tests` · `kernel/compression` · `kernel/mac` · `kernel/memory` · `kernel/pi-mono/src` · `kernel/runtime` · `kernel/studio`

`shell/` deferred from workspace (pytest-asyncio constraint conflict).

9.6 audit added `[tool.uv.sources] workspace = true` entries for the 6 adapter members previously missing from `tests/pyproject.toml`, closing `F-9.9-CONTRACT-COLLECTION-UNRUNNABLE-01` and enabling naked `pytest` collection.

**Note:** `docs/` and `_bmad-output/` are **untracked from git** as of commit `effa9ad` (2026-05-15). Only source code under `ports/`, `adapters/`, `kernel/`, `tests/`, `scripts/`, `.github/`, and explicitly committed top-level docs remain git-tracked. Stage-9 cycle handovers since 2026-05-16 live in `docs/stage-*-handover.md` and are NOT in git history — commit bodies + close-commit messages are the canonical substance-of-record (precedent: 9.4.3, 9.4.6 Phase C `--allow-empty` close). `docs/design-system-substrate-v1.0.md` status under new policy [TBD — pending Andrey clarification].

---

## Stage 10 (in-flight on `stage-10.0-port-stubs`)

- **Implementation COMPLETE** at `d2b5670` (#42); pre-roundtable reconcile at `50ce68e` (F-10-RECONCILE-PRIOR-PORTS-01)
- **NOT YET RATIFIED** — gated on Mary's 3 Champion VOC calls + GO/GO-with-amendments outcome
- New ports landed: `SessionIndexPort` (API_VERSION 1.0.0; SQLite + FTS5 backing; semantic = no-op stub) + `SkillTelemetryPort` (renamed from SkillObserverPort)
- 10 DTOs; CLI `verdaca session list/show <id>`; MAC-T floor ≥18

---

## Technology Stack Active

| Layer | Tech | Version |
|---|---|---|
| Language | Python | 3.12.12 (pinned in `.python-version`) |
| Package manager | uv | workspace with `uv.lock` SHA-pinned at 9.6 |
| Memory adapter | mem0ai | 1.0.11 (PyPI, SHA-pinned) |
| Memory substitute | letta-client | ==1.10.3 (PyPI, SHA-pinned) |
| LLM Proxy adapter | litellm (PyPI) | ==1.83.14 (SHA-pinned); sole LLMProxyPort substrate per ADR-9.2-V5 v0.6 |
| Compaction adapter | llmlingua (PyPI) | ==0.2.2 (SHA-pinned, MIT) — primary; in_tree_compaction_stub permanent CI fallback |
| Session index | SQLite FTS5 (stdlib `sqlite3`) | `knowledge/sessions.db` gitignored build artifact |
| Serialization | tree-sitter + TONL in-tree | Python 3.12 |
| UI | Next.js 15 + Tailwind 4 + shadcn/ui | — |
| Auth | Clerk | — |
| Billing | Stripe | — |
| Observability | OpenTelemetry (OTEL) | provisional RATIFIED at 5.5 |
| Test framework | pytest + pytest-asyncio | — |
| Linting | ruff + mypy strict | — |
| CI / Supply-chain | GitHub Actions + Renovate Bot | `.github/{renovate.json, workflows/contract-tests.yml, workflows/audit.yml}` (added 9.6 `3e26f48`) |

---

## Design System

| Artifact | Status | Notes |
|---|---|---|
| `docs/design-system-substrate-v1.0.md` | RATIFIED 2026-05-09 (commit `d0a393b`) | body sha256 `8bff15a26289…` |
| `docs/style-dictionary.config.json` | D-8 stub | empty source/platforms; full pipeline deferred to v1.1 |
| Phase 3 Studio shell UI | CLOSED 2026-05-13 | 4 surfaces (S-1..S-4); workshop-binding at `_bmad-output/`; light-canonical F-3 deviation |
| Brand-mark cycle | CLOSED 2026-05-16 | master (a) Baseline-iter + auxiliary (c) Verdict-dial; favicon `9d145ca`; 3 v1.1 candidates (P-BM-1..3) |
| verdaca.com | LIVE 2026-05-11 | Cloudflare Pages + Spaceship + Formspree; Phase 2 landing + docs |
| `docs/architecture-diagrams.md` | refreshed 2026-05-13 (HEAD `e7c6f1d` reference) | 13 Mermaid diagrams; engineering progress tracker uses status colors |

---

## Stage 7 Debt Ledger (19 items, originally deferred to "Stage 8"; folded into Stage 10/11 debt post-Stage-9 RATIFIED)

Not blocking forward work. Key items:

- **C-4 Memory `mac.reuse_successful` promotion path** — LATENT Stage-7 blocker; must resolve before headline becomes unconditional
- **A4 Spearman ρ ≥ 0.6 human validation** — headline caveat "(internal scoring; A4 deferred)" until resolved
- W-1..W-7 Cleo WARNINGs from Stage 5.3.5
- C-1..C-5 cross-stage architecture contradictions (C-4 is the live blocker)
- PDF + `.pptx` export (ADR-08, deferred)
- "Built With Praxis/Verdaca" public dashboard badge
