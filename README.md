<p align="center">
  <img src="assets/verdaca-banner-dark-2x.png" alt="Verdaca — multi-agent reasoning engine for strategic advisory" width="100%">
</p>

<p align="center">
  <a href="https://verdaca.com"><img src="https://img.shields.io/badge/status-LIVE-6B1F25?style=flat-square" alt="status: LIVE"></a>
  <a href="https://verdaca.com"><img src="https://img.shields.io/badge/site-verdaca.com-6B1F25?style=flat-square" alt="site: verdaca.com"></a>
  <img src="https://img.shields.io/badge/version-v0.13.0-1F2226?style=flat-square" alt="version: v0.13.0">
  <img src="https://img.shields.io/badge/substrate-v1.0-1F2226?style=flat-square" alt="substrate: v1.0">
  <img src="https://img.shields.io/badge/python-3.12%2B-1F2226?style=flat-square" alt="python: 3.12+">
  <img src="https://img.shields.io/badge/coverage-90%25%2B-1F2226?style=flat-square" alt="coverage: 90%+">
  <img src="https://img.shields.io/badge/license-proprietary-967853?style=flat-square" alt="license: proprietary">
</p>

**Multi-agent reasoning engine for strategic advisory.**

Verdaca runs a structured panel of AI agents over your question and returns explicit trade-offs, red-team dissent, named scenarios, and scope limits — in minutes, not weeks.

> **Codename note:** The internal codename is **Praxis** (Stages 1–6). The Python namespace `src/praxis/` preserves that name as the internal module path. See `docs/rename-praxis-to-verdaca.md`.

## Architecture

Verdaca follows a ports-and-adapters pattern. Protocol definitions stay separate from implementations, so you can swap an adapter without touching domain logic.

```
ports/                  Port Protocols and DTOs — the canonical interface contracts
adapters/               Concrete implementations of each port
  beads/                Versioned state adapter
  tonl/                 TONL serialization adapter
  mem0/                 Mem0 memory adapter
  letta/                Letta memory adapter
  litellm/              LiteLLM LLM proxy (sole LLM substrate)
  llmlingua/            LLMLingua token-compaction adapter (primary)
  in_tree_compaction_stub/  Lightweight CI fallback for compaction
  pi_mono_native/       Native cost-meter adapter
  mcp_server/           FastMCP MCP gateway adapter
  channels/
    teams/              Microsoft Teams webhook adapter (HMAC-SHA256)
    slack/              Slack webhook adapter (X-Slack-Signature v0)
    webhook_app/        ASGI app — Teams and Slack share one composed gateway
composition/            Wiring layer — builds the runtime and auth quartet; no domain logic here
kernel/
  pi-mono/              Cost tracking and metering
  compression/          Token compression (Caveman dialects)
  memory/               MemoryProtocol facade over pluggable backends
  runtime/              Multi-agent orchestration and tool library
  mac/                  Meta-Agent Controller — runs the 3-cycle deliberation loop
  studio/               Workflow templates (YAML + Jinja2)
  gateway/              VerdacaGatewayService — composes all ports into one entry point
  auth/                 Cross-cutting auth (OIDC, JWKS, JWT, nonce)
  session_index/        SQLite FTS5 session index and skill telemetry
shell/                  POV delivery harness (Next.js + FastAPI + Clerk + Stripe)
```

The uv workspace has **23 active members** managed under a single `uv.lock` with SHA-pinned dependencies.

## Channels

| Channel | Status | Auth |
|---|---|---|
| **Claude Desktop** | LIVE | MCP stdio / Streamable HTTP |
| **Microsoft Teams** | LIVE | HMAC-SHA256 webhook |
| **Slack** | LIVE | X-Slack-Signature v0 webhook |

## MCP integration

The `adapters/mcp_server/` FastMCP adapter exposes five tools:

- `verdaca_start_analysis`
- `verdaca_estimate_cost`
- `verdaca_get_result`
- `verdaca_list_sessions`
- `verdaca_get_artifact`

It also exposes 5 resources and 1 prompt.

**Transports:** stdio (Claude Desktop) and Streamable HTTP (`stateless_http=True`).

## Key metrics

| Metric | Value |
|---|---|
| Quality vs. vanilla single-agent | **+47%** composite improvement |
| Quality vs. enhanced single-agent | **+21%** composite improvement |
| Deep session cost (internal) | ~$2.50 |
| Deep session time | ~12 minutes |
| Quick session time | ~4 minutes |
| Tests passed | 411+ (19 skipped, 0 failed) |
| `no_waiver` markers | 23 |
| Coverage | 90%+ across modules |
| uv workspace members | 23 |
| Python | 3.12.12 (pinned) |

*Quality metrics are from internal scoring (A4 Spearman ρ validation pending). Cite these numbers only with the "(internal scoring; A4 Spearman pending)" caveat.*

## Stack

- **Package manager:** uv (workspace, SHA-pinned `uv.lock`)
- **Backend:** Python 3.12.12, FastAPI, Pydantic v2, SQLAlchemy
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS
- **Auth:** authlib (OIDC discovery, JWKS cache, JWT alg-pin), httpx; HMAC-SHA256 (Teams); X-Slack-Signature v0 (Slack); Clerk (shell)
- **LLM:** Anthropic Claude (Opus 4.6 / Sonnet 4.6) via LiteLLM — virtual keys with per-key budget, TPM, and RPM caps
- **MCP gateway:** FastMCP / MCP SDK
- **Compaction:** LLMLingua (primary) + in-tree stub (CI fallback)
- **Serialization:** tree-sitter + TONL
- **Session store:** SQLite FTS5
- **Billing:** Stripe (per-session: $29 quick / $149 deep) — shell only
- **CI:** GitHub Actions + Renovate Bot (supply-chain gates, pip-audit)

## Quick start

**Prerequisites:** [uv](https://docs.astral.sh/uv/) installed, Python 3.12+, Node.js 18+ (shell frontend only).

```bash
# Clone the repository
git clone <repo-url>
cd verdaca

# Install all workspace packages
uv sync

# Run the full contract test suite
uv run pytest tests/

# Run tests for a specific module
uv run pytest kernel/mac/
uv run pytest adapters/mcp_server/
uv run pytest adapters/channels/

# Start the shell frontend (development mode)
cd shell/web
npm install
npm run dev
```

## Built with Verdaca

The architecture of this product was designed using the product itself. Every major decision — port ratification, adapter selection, auth design, channel onboarding — went through a Verdaca multi-agent session. The deliberation outputs are captured in the `docs/` and per-module `architecture.md` files throughout the repo.

That means the trade-off records, red-team dissents, and scope limits you see in the documentation are not retrospective write-ups. They are the actual session outputs.

## Module documentation

Each kernel module and adapter ships with:

- `architecture.md` — design decisions and rationale
- `test-strategy.md` — testing approach and coverage targets
- `code-review.md` — review findings

Top-level cross-cutting decisions live in `docs/`.

## License

Proprietary. All rights reserved.
