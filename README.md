<p align="center">
  <img src="assets/verdaca-banner-dark-2x.png" alt="Verdaca — governed AI decision workflow with contract-tested vendor seams" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-prototype-6B1F25?style=flat-square" alt="status: prototype">
  <img src="https://img.shields.io/badge/version-v0.13.0-1F2226?style=flat-square" alt="version: v0.13.0">
  <img src="https://img.shields.io/badge/substrate-v1.0-1F2226?style=flat-square" alt="substrate: v1.0">
  <img src="https://img.shields.io/badge/python-3.12%2B-1F2226?style=flat-square" alt="python: 3.12+">
  <img src="https://img.shields.io/badge/license-proprietary-967853?style=flat-square" alt="license: proprietary">
</p>

**Governed AI decision workflow — every vendor behind a contract-tested seam.**

Verdaca is an auth-first gateway that runs an AI request end to end against real services: identity (OIDC/JWT, replay protection), per-key budget check, memory retrieval, compaction, model call, cost ledger and session index. Every vendor sits behind a typed port; memory (Mem0 ↔ Letta) and compaction (LLMLingua ↔ in-tree stub) swaps are proven by shared contract suites. A multi-agent deliberation loop (producer, isolated reviewer, quality gates) is designed and implemented as a tested state machine, but it is not yet wired to live model calls.

> **Codename note:** The internal codename is **Praxis** (Stages 1–6). The Python namespace `praxis` (under each workspace package's `src/praxis/`) preserves that name as the internal module path.

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

The uv workspace has **24 active members** managed under a single `uv.lock` with SHA-pinned dependencies.

## Channels

| Channel | Status | Auth |
|---|---|---|
| **Claude Desktop** | Contract-tested | MCP stdio / Streamable HTTP |
| **Microsoft Teams** | Contract-tested | HMAC-SHA256 webhook |
| **Slack** | Contract-tested | X-Slack-Signature v0 webhook |

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

### Measured

| Metric | Value |
|---|---|
| Tests passed | 420+ (19 skipped, 0 failed) |
| `no_waiver` markers | 23 |
| uv workspace members | 24 |
| Python | 3.12.12 (pinned) |

### Design-stage estimates

The multi-agent deliberation is not yet wired to live model calls, so these figures are not from real runs. The quality figures come from internal scoring; validation against human rankings (A4 Spearman ρ) is still pending. Cite them only with the "(internal scoring; A4 Spearman pending)" caveat.

| Metric | Value | Basis |
|---|---|---|
| Quality vs. vanilla single-agent | +47% composite | Self-graded, N=10, emulated in one session |
| Quality vs. enhanced single-agent | +21% composite | Same run |
| Deep session cost | ~$2.50 | Estimated from word counts and budget ratios; not metered |
| Deep session time | ~12 minutes | Estimate; not metered |
| Quick session time | ~4 minutes | Estimate; not metered |

## Stack

- **Package manager:** uv (workspace, SHA-pinned `uv.lock`)
- **Backend:** Python 3.12.12, FastAPI, Pydantic v2, SQLAlchemy (earlier modules) + raw sqlite3
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS
- **Auth:** authlib (OIDC discovery, JWKS cache, JWT alg-pin), httpx; HMAC-SHA256 (Teams); X-Slack-Signature v0 (Slack); Clerk (shell)
- **LLM:** Model-agnostic via LiteLLM (tested with gpt-4o) — virtual keys with per-key budget, TPM, and RPM caps
- **MCP gateway:** FastMCP / MCP SDK
- **Compaction:** LLMLingua (primary) + in-tree stub (CI fallback)
- **Serialization:** TONL adapter (deferred)
- **Session store:** SQLite FTS5
- **Billing:** Stripe client interface only (no SDK wired) — shell only
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

## How it was designed

Architecture decisions were made in multi-agent BMAD sessions in Claude Code; their trade-off records, red-team critiques and scope limits live in `docs/`. These were not produced by the Verdaca engine itself.

## Module documentation

Each kernel module and adapter ships with:

- `architecture.md` — design decisions and rationale
- `test-strategy.md` — testing approach and coverage targets
- `code-review.md` — review findings

Top-level cross-cutting decisions live in `docs/`.

## License

Proprietary. All rights reserved.
