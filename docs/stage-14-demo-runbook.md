# Verdaca Demo Runbook — Buyer Contact Surface (Stage 14 Phase-1)

**Audience:** a Champion (technical buyer) evaluating Verdaca on their own Teams or Slack tenant, plus the engineer who stands the demo up for them.
**What this covers:** how to bring up the auth-first buyer transport, send a first message, read the result, and tear it back down.
**What this is not:** not a certification artifact and not a claim of full production wiring. The auth → nonce → budget-gate → replay **spine executes live**; cost metering, the LLM model output, virtual-key budget enforcement, durable memory, and durable nonce persistence are **Tier-1 demo stubs** on this path, each with a named follow-up. See §8 for the honest scope ledger.

> **Status caveat (carry verbatim downstream):** every buyer-facing claim in this runbook is **HYPOTHETICAL-VOC** until the first Champion call lands. After N=1 it downgrades to PROVISIONAL-SINGLE-SAMPLE for existence/disqualification claims only; population/magnitude/pricing stay HYPOTHETICAL pending N≥3.

---

## §1 Prerequisites

### 1.1 Runtime
- Python 3.12, `uv` installed, repository checked out at the Stage 14 branch.
- One `uv sync` from the repository root (never run two `uv` processes at once — the editable cache lock will not land).
- Network egress to your IdP's discovery endpoint and to the LiteLLM proxy.

### 1.2 Identity provider (IdP)
- An OIDC issuer that serves `/.well-known/openid-configuration` + a JWKS endpoint signing tokens with **RS256**.
- A registered application whose tokens carry the audience you will set in `OIDC_AUDIENCE`.
- Tokens MUST include a `nonce` (or `jti`) claim — standard for Entra / Okta / Auth0. The replay check keys on it.

### 1.3 Virtual-key proxy
- A reachable LiteLLM proxy (`LITELLM_PROXY_URL`) and its master key (`LITELLM_MASTER_KEY`). The onboarding step issues a scoped per-user virtual key with a conservative budget cap.

### 1.4 Environment variables (all required unless marked optional)

| Variable | Purpose | Read by |
|---|---|---|
| `OIDC_ISSUER_URL` | IdP issuer; OIDC discovery root | `compose_auth_quartet()` → `discover()` |
| `OIDC_AUDIENCE` | Expected token audience | `OidcPolicy` |
| `VERDACA_ALLOWED_USER_IDS` | Deny-by-default caller allow-list (comma/space separated) | `evaluate_user_allowlist` |
| `TEAMS_WEBHOOK_SECRET` | Teams inbound HMAC-SHA256 secret | `load_webhook_secret()` |
| `SLACK_SIGNING_SECRET` | Slack inbound signing secret (`v0` scheme) | `load_signing_secret()` |
| `VERDACA_DEPLOY_PROFILE` | `production` makes the vkey-presence check fail-closed | `policy_health_check()` |
| `VERDACA_GATEWAY_BEARER_TOKEN` | Gateway bearer (warns if unset) — optional for the demo | `policy_health_check()` |
| `LITELLM_PROXY_URL` | LiteLLM proxy base URL | `vkey-provision` step |
| `LITELLM_MASTER_KEY` | LiteLLM master key (issues scoped keys) | `vkey-provision` step |

---

## §2 Onboarding — the 5-minute path

Run the four checks in order; each stops on the first failure with a specific message. The POSIX orchestrator `scripts/onboarding/onboard.sh` runs them halt-on-failure.

1. **env-check** — `python scripts/onboarding/env-check.py` confirms every required variable above is present; exits non-zero naming the first missing one.
2. **vkey-provision** — `python scripts/onboarding/vkey-provision.py` issues a per-user virtual key via `LiteLLMVirtualKeyAdapter.create_virtual_key(...)` with a conservative `max_budget`; prints the key prefix and how to revoke it.
3. **policy-smoke** — `python scripts/onboarding/policy-smoke.py` builds a `GatewayPolicy` (allow-list + virtual keys) and calls `policy_health_check(policy=...)`. Exit 0 = healthy; exit 1 = fail-closed fired (read the diagnostic — usually a missing vkey under `VERDACA_DEPLOY_PROFILE=production`).
4. **first-message** — `python scripts/onboarding/first-message.py` sends a synthetic signed message through the gateway and asserts the full traversal order (bearer → `OidcPolicy.authenticate` → nonce → budget-gate → execute), printing round-trip time and cost.

> The onboarding scripts land at **[Phase-1-H#2]**; until then, §5 below shows the manual equivalent against the local OIDC stub.

---

## §3 Teams app installation

1. In the Teams Developer Portal, create a bot/app and point its messaging endpoint at your deployment's `POST /webhooks/teams` route (served by `create_teams_app()` in `praxis.adapters.channels.webhook_app`).
2. Generate a shared secret and set it as `TEAMS_WEBHOOK_SECRET` on the deployment.
3. The inbound signature is **HMAC-SHA256** over `timestamp + "." + body`, carried in `x-teams-signature` with the unix `x-teams-request-timestamp`. Requests outside a **300-second** window are rejected.
4. The caller's OIDC bearer travels in the `Authorization` header; it is verified against your IdP (RS256/JWKS) by the gateway, not at the channel layer.

References in code: Stage 12 `TeamsAdapter`, Stage 13 fail-closed channel events, and the Phase-0.6 `webhook_app` transport.

---

## §4 Slack app installation

> **Status — Slack served.** The Slack route (`POST /webhooks/slack`) is served by `webhook_app` alongside Teams on ONE composed gateway (build via `create_webhook_app`). Both routes share a single execution lock.

1. Create a Slack app; enable Event Subscriptions and point the request URL at the `POST /webhooks/slack` route.
2. On first registration Slack issues a one-time **URL-verification challenge** — `receive_webhook` echoes the `challenge` value inline (after the signature check, before dispatch).
3. Set the app's signing secret as `SLACK_SIGNING_SECRET`. Inbound requests are verified with Slack's **`v0`** scheme: `x-slack-signature` + `x-slack-request-timestamp`. The secret is **optional-until-wired**: a Teams-only deploy boots without it, and the `/webhooks/slack` route returns `503` until it is set.
4. As with Teams, the caller identity is an OIDC bearer verified at the gateway.

> Both channels share the neutral `praxis.composition` runtime apex — the composition-root hoist landed, so neither channel pulls the MCP server / FastMCP. A live boundary guard (`test_channel_webhook_composition_boundary.py`) keeps the wrong-direction `channels → mcp_server` arrow from ever returning.

---

## §5 First-message smoke

**Goal:** a caller sends one message and receives one structured card back, having traversed real authentication.

Shape of the request to `POST /webhooks/teams`:
- Body: a Teams `message` activity (JSON) with `from.aadObjectId`, `conversation.id`, `text`.
- Headers: `x-teams-request-timestamp`, `x-teams-signature` (HMAC-SHA256 of the body), and `Authorization: Bearer <oidc-token>`.

Expected outcome:
- **200** with a JSON body whose `type` is `"AdaptiveCard"` — the result rendered for the channel.
- The request flowed bearer → `OidcPolicy.authenticate` (RS256/JWKS) → nonce replay check → budget gate → `execute()` and back.

Negative cases worth showing a Champion (each returns a 4xx, never a 500):
- **No bearer** → `401`.
- **Tampered signature** → `401`, rejected before `execute()` runs.
- **Replayed token/nonce** → `401` (replay rejection is live).
- **Malformed (but correctly signed) body** → `400`, not masked as an auth failure.

For a self-contained demo without a live IdP, the integration harness at `tests/src/praxis/contract_tests/ports/test_channel_webhook_wiring_integration.py` boots the transport against a **local OIDC stub** (real RS256 crypto, local issuer) and drives all four cases.

---

## §6 Rollback

1. **Revoke the virtual key** issued in §2.2 (the `vkey-provision` output prints the exact revoke step against `LITELLM_PROXY_URL`).
2. **Uninstall the channel app** (remove the Teams/Slack app from the tenant; the inbound route stops receiving).
3. **Clear environment** — unset the variables from §1.4 on the deployment, including the channel secrets.

Rollback is independent of any stored state; the demo path keeps nonce state in memory, so a process restart also clears it.

---

## §7 Troubleshooting — the five expected failure modes

| Symptom | Likely cause | First check |
|---|---|---|
| `402` / budget diagnostic | **vkey budget exhausted** | the issued key's spend vs its `max_budget`; re-provision with a higher cap |
| `401` with audience message | **IdP audience mismatch** | `OIDC_AUDIENCE` equals the `aud` your IdP stamps |
| intermittent `401` after a key roll | **JWKS rotation race** | the JwksCache TTL vs how recently the IdP rotated; retry after the cache refreshes |
| `401` "unauthorized" before execute | **webhook signature drift** | clock skew vs the 300s window; the secret matches on both sides; HMAC input is `timestamp + "." + body` |
| two callers collide on one session | **gateway session-id collision** | the channel session id derivation per caller/conversation |

---

## §8 Honest scope ledger (what is live vs substituted)

Per the B-6 auditor-floor attestation (RATIFIED — PROVISIONAL, 2026-05-29):

- **Live on this path:** per-user OIDC token verification (RS256/JWKS), inbound HMAC/`v0` signature verification, authorization ordering (allow-list → auth → nonce → budget), replay rejection, prod-fail-closed posture check.
- **Demo-profile (dev/test) Tier-1 stubs:** per-tenant budget **enforcement** (vkey), cost metering, durable memory, LLM model output, and nonce persistence across restart (in-memory on the live path; the durable SQLite store stays pinned by a non-waivable test).
- **Production profile (`VERDACA_DEPLOY_PROFILE=production`):** these substrates wire to REAL adapters (LiteLLM vkey, DIAL LLM, pi_mono cost, Letta memory), **fail-closed if creds are absent**. They are construction-wired + fail-closed + gating-tested, but **NOT live-exercised** (no creds/VPN in this demo window) — a VPN-on staging smoke is the live-verification step.
- **Identity provider:** a local OIDC stub in the self-contained demo (real crypto; commercial-IdP integration is config-only and untested here).
- **Channel coverage:** **both** the **Teams** and **Slack** inbound routes are served today on one composed gateway (the composition-root hoist landed, so both share the neutral `praxis.composition` apex without the wrong-direction arrow).

Each substituted row carries a real-deploy follow-up in the B-4 Tier-1 Substitute Ledger. The auth-first spine genuinely executes; the backing behind it is named, not concealed.

---

*Authored at Stage 14 Phase-1 [H#1]; Slack-served + production-profile updates folded at [H#9]. Tracked at [H#9] via the `!docs/stage-14-demo-runbook.md` gitignore negation. M3 buyer-language audit run at each edit — zero hits.*
