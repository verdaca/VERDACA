# Verdaca

**Multi-agent reasoning engine for strategic advisory.**

Verdaca delivers structured multi-perspective strategic analysis -- explicit trade-offs, red team dissent, named scenarios, and scope-limits -- in minutes, not weeks.

> Internal codename: **Praxis** (Stages 1-6). The Python namespace `src/praxis/` preserves the codename as internal module path. See `docs/rename-praxis-to-verdaca.md`.

## Architecture

Verdaca is a 7-layer system built in strict dependency order:

```
kernel/
  pi-mono/       Stage 1 - Cost tracking & metering (measurement foundation)
  compression/   Stage 2 - Token compression (TONL + Forge + Caveman + RTK)
  memory/        Stage 3 - Experience store (Beads + Mem0 + Atelier facade)
  runtime/       Stage 4 - Multi-agent orchestration & tool library
  mac/           Stage 5 - Meta-Agent Controller (3-cycle deliberation)
  studio/        Stage 6 - Workflow templates (YAML + Jinja2 rendering)

shell/           Stage 7 - POV Delivery Harness (Next.js + FastAPI + Clerk + Stripe)
```

Each layer is a self-contained Python package with its own `pyproject.toml`, test suite, and architecture documentation.

## Key metrics

| Metric | Value |
|---|---|
| Quality vs vanilla single-agent | **+47%** composite improvement |
| Quality vs enhanced single-agent | **+21%** composite improvement |
| Deep session cost (internal) | ~$2.50 |
| Deep session time | ~12 minutes |
| Quick session time | ~4 minutes |
| Test count | 415+ across all modules |
| Coverage | 90%+ (MAC 94%, Studio 96%, Shell 92%) |
| Python LoC | ~49,700 |

*Quality metrics are from internal scoring. Human validation (A4 Spearman) pending.*

## Stack

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy, Pydantic v2
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS
- **Auth:** Clerk
- **Billing:** Stripe (per-session: $29 quick / $149 deep)
- **Database:** Neon Postgres
- **LLM:** Anthropic Claude (Opus 4.6 / Sonnet 4.6)

## Quick start

```bash
# Clone
git clone <repo-url>
cd verdaca

# Backend (each kernel module)
cd kernel/mac
pip install -e ".[test]"
pytest

# Shell backend
cd shell
pip install -e ".[test]"
pytest

# Shell frontend
cd shell/web
npm install
npm run dev
```

## Built With Verdaca

Every architectural decision in the 7-stage build pipeline was run through the same multi-agent deliberation process the product delivers. See `docs/pipeline.md` for the full build history.

## Documentation

- `docs/pipeline.md` -- Master orchestration pipeline (7 stages, ~40 sub-steps)
- `docs/build-plan.md` -- Strategic build sequence rationale
- `docs/box-architecture.md` -- 5-layer technical architecture
- `docs/hybrid-architecture.md` -- Component selection analysis

Each module also contains:
- `architecture.md` -- System design
- `test-strategy.md` -- Testing approach
- `code-review.md` -- Review findings
- `alignment-review.md` -- Cross-stage verification

## License

Proprietary. All rights reserved.
