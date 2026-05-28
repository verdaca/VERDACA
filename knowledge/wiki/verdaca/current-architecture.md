# Verdaca — What Is Actually Built

**Compiled:** 2026-05-08 → **Updated:** 2026-05-27 (Stage 12 RATIFIED on local-only branch `stage-12.0-channel-adapters` @ `43f57ba`; Stage 13 OPEN — scope G1 ratified, no code shipped) | **HEAD (working branch):** `stage-12.0-channel-adapters @ 43f57ba` (Path A LOCAL-ONLY, never pushed to origin; 29 commits from `e0aade3`, base `f181a7e`) | **local main HEAD:** `f181a7e` (Stage 10 A7-override close, 2026-05-24) | **origin/main HEAD:** `f181a7e` (in sync; 0 ahead) | Stage 12 = Teams + Slack channel adapters + kernel/auth/ OIDC+JWKS+claims+nonce + VirtualKeyPort + LiteLLM HTTP-client virtual keys

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
    gateway.py            ✅ COMPLETE (Stage 11) — GatewayPort + ChannelAdapterPort Protocols; canonical import path `praxis.ports.gateway` ONLY (Winston #2); no re-exports via kernel.gateway
    gateway_dto.py        ✅ COMPLETE (Stage 11) — ChannelContext (frozen, FROZEN_FIELD_ALLOWLIST preserved across REFREEZE-01/02), AuthClaims, CallerKind, ChannelKind {CLI, TEAMS, SLACK, CLAUDE_DESKTOP} (4 MVP adapters per Winston #1), StartAnalysisRequest, AnalysisResult, SessionHandle, ArtifactRef
    gateway_errors.py     ✅ COMPLETE (Stage 11) — GatewayCtxError, AuthClaimsAccessError
    virtual_key.py        ✅ COMPLETE (Stage 12) — VirtualKeyPort Protocol + VirtualKeySpec + VirtualKeyInfo + BudgetExhaustedError
    common.py             Shared DTOs (Message sibling-add at 9.4.5 A.2)

adapters/                 Concrete adapter implementations
  beads/                  VersionedState adapter (264 LOC, greenfield in-tree, 10/10 M-T-VS-* GREEN)
  tonl/                   Serialization adapter (~333 LOC, wraps kernel/compression/tonl, 12 M-T-SER-* catalog; 9.4.2 deferred-work)
  mem0/                   Memory primary adapter (Mem0 SDK v1.0.11 SHA-pinned, 5 Protocol methods, OTEL spans, 18 M-T-MEM-*)
  letta/                  Memory substitute adapter (letta-client ==1.10.3 SHA-pinned; native passage-search)
  pi_mono_native/         ✅ COMPLETE (9.4.4) — in-tree-native Python pricing math; 8 M-T-COST-*; ADR-9.2-V4
  litellm/                ✅ COMPLETE (9.4.5 + Stage 12 E2) — LiteLLM PyPI library adapter (litellm==1.83.14 SHA-pinned); 7 M-T-LLM-*; ADR-9.2-V5 v0.6; sole LLMProxyPort substrate (Docker sidecar retired via H2-falsification); DIAL api_base routing landed at Phase 0 P0.3 `40dc556`; **virtual_keys.py** (Stage 12) — httpx-based LiteLLMVirtualKeyAdapter against proxy routes (/key/generate, /key/info, /spend/logs); NO Python LiteLLM SDK import; per-key budget + model allow-list + TPM/RPM caps; LiteLLMProxyError; 5 M-T-LLM-VKEY-*
  in_tree_compaction_stub/ ✅ COMPLETE (9.4.6) — 5 files, permanent CI fallback; supports `lossless` + `lossy_eviction` (downgrades `lossy_summary`); `UPSTREAM_KIND="in_tree"`
  llmlingua/              ✅ COMPLETE (9.4.6) — LLMLingua PyPI library adapter (llmlingua==0.2.2 SHA-pinned, MIT); wraps `PromptCompressor`; substrate-truth probe PASS-DEGRADED (hard-budget emulated; determinism via hardcoded seed=42); ADR-9.2-V6 v0.7
  mcp_server/             ✅ COMPLETE (Stage 11) — FastMCP-backed inbound channel adapter; server.py, http.py, stdio.py, tools.py, resources.py, prompts.py, transport.py; 5 tools + 5 resources + 1 prompt + 2 transports (stdio + Streamable HTTP, stateless_http=True PINNED); Claude-Desktop ChannelAdapter LIVE (Stage 11); Teams + Slack now LIVE (Stage 12 E1); CLI hardening deferred; adapter-local Protocol `MCPTransportPort` (NOT in praxis.ports layer)
  channels/teams/         ✅ COMPLETE (Stage 12 E1) — TeamsChannelAdapter; HMAC-SHA256 webhook signature verification + ±5min replay window; implements ChannelAdapterPort; webhook.py (Bot Framework) + events.py (event translation); VCR cassettes at tests/fixtures/vcr_cassettes/teams/
  channels/slack/         ✅ COMPLETE (Stage 12 E1) — SlackChannelAdapter; X-Slack-Signature v0 verification + URL-challenge handler; implements ChannelAdapterPort; events.py (Slack Events API); VCR cassettes at tests/fixtures/vcr_cassettes/slack/

tests/                    20 files — Contract test catalog
  src/praxis/contract_tests/ports/
    test_versioned_state_contract.py    10 M-T-VS-* (all green)
    test_serialization_contract.py      12 M-T-SER-* (10 pass + 2 pytest.skip)
    test_memory_contract.py             18 M-T-MEM-* (4 PROMO no_waiver dual-adapter parametric)
    test_cost_meter_contract.py         8 M-T-COST-* (all green)
    test_llm_proxy_contract.py          7 M-T-LLM-* (single-adapter post H2-falsification)
    test_compaction_contract.py         14 M-T-COMP-* (parametrized {in-tree stub, LLMLingua}; OD-2 inverse-downgrade asymmetry coverage; 3 bearers on no_waiver allow-list)
    test_no_waiver_inventory.py         Stage-9 enforcer (added 9.9 `ef401a2`, un-skipped at 9.6 `3e26f48`); STAGE9_NO_WAIVER_ALLOWLIST frozenset cardinality=9; **scoped to Stage 9/10 markers only** (Stage 12 compatibility fix `355f516`)
    test_gateway_contract.py            ✅ NEW (Stage 11) — GatewayPort + ChannelAdapterPort contract tests
    test_mcp_*.py                       ✅ NEW (Stage 11) — JSON-RPC golden-replay, stdio handshake, port handshake, ChannelCtx PII redaction, SessionIndex bind (38 MAC-Ts Stage 11 delta; 208 contract tests GREEN + 8 skipped env-gated DIAL live + others)
    test_kernel_auth_contract.py        ✅ NEW (Stage 12 E2) — 10 MAC-Ts for kernel/auth/ (claims, OIDC, JWT alg-pin, nonce replay)
    test_litellm_virtual_keys_contract.py ✅ NEW (Stage 12 E2) — 5 M-T-LLM-VKEY-* (budget exhausted, model allow-list, TPM/RPM caps); 5 VCR cassettes
    test_teams_channel_adapter_contract.py ✅ NEW (Stage 12 E1) — 12 MAC-Ts (HMAC tamper, replay window, contract port conformance, gateway roundtrip)
    test_slack_channel_adapter_contract.py ✅ NEW (Stage 12 E1) — 12 MAC-Ts (signing tamper, URL-challenge handler, contract port conformance, gateway roundtrip)
    test_stage12_no_waiver_count.py     ✅ NEW (Stage 12) — AST walker + frozenset strict equality; enforces exactly 9 Stage-12 no_waiver markers

tests/reference/
  spike-mcp-server-snapshot-d93f71a/    ✅ NEW (Stage 11) — CAI spike snapshot, frozen reference, non-importable per import-linter contract `spike-snapshot-not-importable`

tests/fixtures/
  vcr_cassettes/teams/    ✅ NEW (Stage 12 E1) — VCR cassettes for Teams webhook tests (synthetic, committed)
  vcr_cassettes/slack/    ✅ NEW (Stage 12 E1) — VCR cassettes for Slack webhook tests (synthetic, committed)
  auth_claims/            ✅ NEW (Stage 12 H#1.5) — 3 IdP fixture files: entra_*.json, okta_*.json, auth0_*.json (auth_claims surface frozen)

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
  gateway/                ✅ COMPLETE (Stage 11 + Stage 12 E2) — port.py, models.py, service.py (VerdacaGatewayService composes LLMProxy + Memory + Cost + Compaction + SessionIndex ports), execution.py, policy.py (**refactored Stage 12** → thin orchestrator consuming praxis.kernel.auth + VirtualKeyPort; Stage-11 bearer-MVP TODOs CLOSED; AST gate M-T-GATEWAY-WIRING-NO-AUTH-LOGIC-01 preserved + M-T-AUTH-KERNEL-NO-ADAPTER-IMPORT-01 added); WAL idempotency store + AsyncSessionIndex wrapper
  auth/                   ✅ COMPLETE (Stage 12 E2) — cross-cutting auth kernel (workspace member #22); claims.py (validate_claims, ClaimsValidationError, _REQUIRED_CLAIMS frozenset {sub,iss,aud,iat,exp}, map_claims_to_auth_claims); oidc.py (OidcMetadata, JwksCache with get_or_fetch/invalidate/_refresh/_fetch_jwks, _CacheEntry, UnknownKeyError); jwt.py (JwtVerifier with alg-filter at __init__ against _ALLOWED_ALGORITHMS {RS256/RS384/RS512/ES256/ES384/ES512}, UnsupportedAlgorithmError, typed JoseError from authlib); idp.py (discover(issuer) async — sole public API; AST gate enforces no other exports); nonce.py (NonceStore.check_and_mark() with asyncio.Lock, NonceReplayError — in-memory; SQLite persistence deferred F-12-CLEO-M3 → Stage 13); __init__.py (9-symbol public surface). Canonical import: praxis.kernel.auth ONLY.
  session_index/          ✅ COMPLETE (Stage 10) — port.py (SessionIndexPort + SkillTelemetryPort Protocols — co-located here, NOT in ports/ layer), models.py, sqlite_store.py, skill_telemetry.py, schema/; SessionFilter.source_uri_prefix added at `50fa909` (Stage 11 additive corrigendum)

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

### uv workspace members (22 active + 1 deferred — verified against root `pyproject.toml` 2026-05-27)
`ports` · `adapters/beads` · `adapters/tonl` · `adapters/in_tree_compaction_stub` · `adapters/pi_mono_native` · `adapters/litellm` · **`adapters/mcp_server`** (Stage 11) · **`adapters/channels/teams`** (Stage 12) · **`adapters/channels/slack`** (Stage 12) · `adapters/mem0` · `adapters/letta` · `adapters/llmlingua` · `tests` · `kernel/compression` · `kernel/mac` · **`kernel/gateway`** (Stage 11) · **`kernel/auth`** (Stage 12) · `kernel/memory` · `kernel/pi-mono/src` · `kernel/runtime` · **`kernel/session_index`** (Stage 10) · `kernel/studio`

`shell/` deferred from workspace (pytest-asyncio constraint conflict).

**Stage delta from prior wiki:** wiki previously listed "13 active" but actually enumerated 16 members; canonical `pyproject.toml` count was 19 active through Stage 11. Stage 10 added `kernel/session_index`; Stage 11 added `kernel/gateway` + `adapters/mcp_server`; **Stage 12 added `adapters/channels/teams` + `adapters/channels/slack` + `kernel/auth` (member #22)**.

9.6 audit added `[tool.uv.sources] workspace = true` entries for the 6 adapter members previously missing from `tests/pyproject.toml`, closing `F-9.9-CONTRACT-COLLECTION-UNRUNNABLE-01` and enabling naked `pytest` collection.

**Note:** `docs/` and `_bmad-output/` are **untracked from git** as of commit `effa9ad` (2026-05-15). Only source code under `ports/`, `adapters/`, `kernel/`, `tests/`, `scripts/`, `.github/`, and explicitly committed top-level docs remain git-tracked. Stage-9 cycle handovers since 2026-05-16 live in `docs/stage-*-handover.md` and are NOT in git history — commit bodies + close-commit messages are the canonical substance-of-record (precedent: 9.4.3, 9.4.6 Phase C `--allow-empty` close). `docs/design-system-substrate-v1.0.md` status under new policy [TBD — pending Andrey clarification]. Stage 11 close memo (`docs/stage-11-ratified-close-memo.md` committed at `e0aade3`) and the 4 Stage 12 handover drafts (`docs/stage-12-{advisor,implementation-executor,e1-channel-adapters-executor,e2-auth-integration-executor}-handover.md`) live under this gitignored-operational `docs/*.md` rule; commit bodies remain canonical substance-of-record.

**Knowledge graph state (2026-05-27, Stage-12 source scope — REFRESHED):** `graphify-out/` refreshed to Stage-12 source scope 2026-05-27 — 625 `.py` files under `ports/`, `kernel/`, `adapters/`, `tests/`, `scripts/`, `shell/` (+33 .py files vs Stage 11 close) → 6,608 nodes / 9,776 edges / 627 communities (AST-only, 0 token cost). Pre-rescope graph at `graphify-out/.graphify_pre-stage12-rescope.bak`. Per CLAUDE.md graphify rules, `graphify-out/GRAPH_REPORT.md` remains the primary map; top god nodes after re-scope: `make_memory()` (60 edges), `GateConfig` (37), `TONLDocument` (34), `rt()` (34), `CompressionLayer` (33). Stage 12 source — `kernel/auth/` (claims/oidc/jwt/idp/nonce), `adapters/channels/teams/` + `adapters/channels/slack/`, `ports/virtual_key.py`, `adapters/litellm/virtual_keys.py` — now in graph. Note: edge count dropped from Stage 11's 10,983 to 9,776 because the Stage 11 graph included INFERRED semantic edges from prior LLM extraction; this Stage 12 rescope is pure AST.

---

## Stage 10: SessionIndex + SkillTelemetry Data-Plane — RATIFIED 2026-05-24

- **RATIFIED** at merge `8ae4f87` (wiki sync `b16e25b`); A7 team-lead override close at `f181a7e` (pushed to origin/main 2026-05-24)
- Implementation landed at `d2b5670` (#42); pre-roundtable reconcile at `50ce68e` (F-10-RECONCILE-PRIOR-PORTS-01)
- New ports: `SessionIndexPort` (API_VERSION 1.0.0; SQLite + FTS5 backing; semantic = no-op stub) + `SkillTelemetryPort` (renamed from SkillObserverPort); **Protocols live in `kernel/session_index/`, NOT in `ports/`** (Stage 10 broke Stage-9 ports-consolidation convention)
- 10 DTOs; CLI `verdaca session list/show <id>`; MAC-T floor ≥18
- **PROVISIONAL VOC** via HYPOTHETICAL synthesis (zero-margin K1/K2/K3); A7 = hard Stage 11.1 charter precondition CLOSED via team-lead override 2026-05-24
- HYPOTHETICAL-VOC caveat (Stage 6.0.1 / A7 override) inherited by all downstream Stage 11+12 customer-fit claims
- F-10-ARCH-AUDIT-02 (shell workspace) reclassified Stage 10.5 debt; F10 PEP-420 RESOLVED at `d2b5670`
- **Stage 10 additive corrigendum at `50fa909` (Stage 11 cycle):** `SessionFilter.source_uri_prefix` field added (backward-compatible, default None)

---

## Stage 11: Channel-Neutral MCP Gateway — RATIFIED 2026-05-26

**Status:** RATIFIED 2026-05-26 at `e0aade3` on local-only branch `stage-11.0-mcp-gateway` (Path A, NOT yet pushed to origin/main; 20-commit chain from `a11aa67`, base `f181a7e`).

**Scope:** Transport/edge layer for MCP-native inbound. Composes ratified Stage 10 data-plane (SessionIndexPort) with Stage 9 LLMProxy + Memory + Cost + Compaction ports into a single VerdacaGatewayService.

**New ports (`ports/src/praxis/ports/`):** `gateway.py` (GatewayPort + ChannelAdapterPort Protocols); `gateway_dto.py` (ChannelContext frozen with FROZEN_FIELD_ALLOWLIST, AuthClaims, CallerKind, ChannelKind {CLI, TEAMS, SLACK, CLAUDE_DESKTOP} per Winston #1, StartAnalysisRequest, AnalysisResult, SessionHandle, ArtifactRef); `gateway_errors.py` (GatewayCtxError, AuthClaimsAccessError). **Canonical import path:** `praxis.ports.gateway` ONLY (Winston #2).

**New kernel module (`kernel/gateway/`):** port.py, models.py, service.py (`VerdacaGatewayService` composes LLMProxy + Memory + Cost + Compaction + SessionIndex ports), execution.py, policy.py MVP (bearer token + user allow-list + per-user budget cap + safety; carries TODO `STAGE-11-DEBT-AUTH-01` + `STAGE-11-DEBT-LITELLM-VKEY-01` deferred to Stage 12 E2). WAL idempotency store + `AsyncSessionIndex` wrapper added.

**New adapter (`adapters/mcp_server/`):** FastMCP-backed inbound — server.py, http.py, stdio.py, tools.py, resources.py, prompts.py, transport.py. **MCP surface live:** 5 tools (`verdaca_start_analysis`, `verdaca_estimate_cost`, `verdaca_get_result`, `verdaca_list_sessions`, `verdaca_get_artifact`) + 5 resources (`verdaca://methodology`, `verdaca://templates`, `verdaca://sessions/{id}/result/summary` + `/transcript` + `/artifacts/{id}`) + 1 prompt + 2 transports (stdio + Streamable HTTP, `stateless_http=True` PINNED). **Claude-Desktop ChannelAdapter LIVE** (Stage 11). **Teams + Slack became LIVE in Stage 12 E1.** CLI hardening still deferred.

**Contract tests:** 38 MAC-Ts in Stage 11 delta; **208 contract tests GREEN + 8 skipped** at Stage 11 close (env-gated DIAL live + others). Suite grew to **281 passed / 8 skipped / 0 failed** after Stage 12 (+47 MAC-Ts).

**5 new no_waiver entries (strict equality meta-test; Stage 11 sublist cardinality exactly 5):** `M-T-GW-JSONRPC-GOLDEN-REPLAY-01`, `M-T-GW-STDIO-HANDSHAKE-01`, `M-T-GW-PORT-HANDSHAKE-01`, `M-T-GW-CHANNELCTX-PII-REDACTION-01`, `M-T-GW-SESSIONINDEX-BIND-01`.

**REFREEZE history (FROZEN_FIELD_ALLOWLIST preserved in both):** REFREEZE-01 (`9609c29` + `121670a`) added 3 read methods (`get_session_summary`, `get_session_transcript`, `get_session_artifact`); REFREEZE-02 (`af5d4f4` + `14a31f8`) added `list_sessions`.

**Stage 11 RATIFIED outcomes:** 4 BMAD ratifications closed with amendments — Winston charter v0.5 (8), Murat MAC-T v0.2 (5), Mary buyer-language H#7 (3 tool + 2 title), Cleo H#8 V2 CODE-READY (8 findings resolved). HYPOTHETICAL-VOC caveat inherited from A7 team-lead override.

**Reference snapshot:** `tests/reference/spike-mcp-server-snapshot-d93f71a/` — CAI spike, frozen reference, non-importable per import-linter contract `spike-snapshot-not-importable`.

---

## Stage 12: Channel Adapter Expansion + Auth Integration — RATIFIED 2026-05-27

**Status:** RATIFIED 2026-05-27 at `43f57ba` on local-only branch `stage-12.0-channel-adapters` (29 commits from `e0aade3`). Path A LOCAL-ONLY; not yet pushed to origin/main.

**Scope E1 — Channel adapters:**
- `adapters/channels/teams/` — TeamsChannelAdapter; HMAC-SHA256 webhook signature verification + ±5min replay window; webhook.py (Bot Framework) + events.py (event translation); implements `ChannelAdapterPort` (Stage 11 freeze preserved; no REFREEZE-03 needed)
- `adapters/channels/slack/` — SlackChannelAdapter; X-Slack-Signature v0 verification + URL-challenge handler; events.py (Slack Events API); implements `ChannelAdapterPort`
- VCR cassettes: `tests/fixtures/vcr_cassettes/{teams,slack}/` (synthetic, committed)

**Scope E2 — Auth + virtual keys:**
- `kernel/auth/` (new workspace member #22; cross-cutting) — OIDC discovery, JWKS cache, JWT alg-pin verifier, AuthClaims validator, nonce replay protection; canonical import `praxis.kernel.auth` ONLY. See kernel/ listing above for per-file detail.
- `ports/src/praxis/ports/virtual_key.py` — VirtualKeyPort Protocol + VirtualKeySpec + VirtualKeyInfo + BudgetExhaustedError
- `adapters/litellm/src/praxis/adapters/litellm/virtual_keys.py` — httpx-based LiteLLMVirtualKeyAdapter; no Python LiteLLM SDK import; per-key budget + model allow-list + TPM/RPM; LiteLLMProxyError
- `kernel/gateway/src/praxis/kernel/gateway/policy.py` — thin-orchestrator refactor consuming `praxis.kernel.auth` + VirtualKeyPort; Stage 11 baseline AST gate M-T-GATEWAY-WIRING-NO-AUTH-LOGIC-01 preserved; M-T-AUTH-KERNEL-NO-ADAPTER-IMPORT-01 added

**Test surface:**
- 47 MAC-Ts (Stage 12 delta): 12 Teams + 12 Slack + 10 kernel/auth + 5 LiteLLM-vkeys + 7 AST gates + 1 D2 cross-window
- **281 tests PASS / 8 skipped / 0 failed** (full suite); 9 no_waiver markers (strict-equality meta-test at `test_stage12_no_waiver_count.py`); 6 AST gates green
- 12 VCR cassettes; 3 IdP fixtures (entra/okta/auth0) at `tests/fixtures/auth_claims/`

**Stage 11 debt closed:**
- STAGE-11-DEBT-AUTH-01: CLOSED by kernel/auth/
- STAGE-11-DEBT-LITELLM-VKEY-01: CLOSED by VirtualKeyPort + LiteLLMVirtualKeyAdapter
- DIAL-LIVE-SMOKE: RESOLVED (Azure-style gpt-4o probe, HTTP 200)

**Carry-forward to Stage 13 (5 findings):**
- F-12-CLEO-C2-COMPOSITION-PENDING-01 (CRITICAL) — JwtVerifier wiring at gateway composition root; production extract_claims path currently incomplete
- F-12-CLEO-M3-NONCE-RESTART-DEFER-01 (MEDIUM) — NonceStore SQLite/Redis persistence + TTL for restart-replay coverage
- F-12-CLEO-W2-SYNC-HTTPX-01 (LOW) — TeamsAdapter/SlackAdapter post_result → async httpx.AsyncClient
- F-12-OIDC-LIVE-DEFERRED-01 — Live IdP smoke deferred to first real Champion call (per `project_verdaca_strategic_sequencing` post-implementation+test VOC gate)
- F-12-CLEO-M5-FALSE-POSITIVE-01 — Informational; GatewayPort.execute is sync; may revisit async boundary at Stage 13 if needed

**HARD constraints extended (Stage 12):** `\bseamless\b` + `\benterprise-grade\b` added to forbidden-token grep (zero hits verified at H#7 + H#8.V2 close).

**Frozen port surfaces:** No Stage 12 changes to `GatewayPort` or `ChannelAdapterPort` (Stage 11 REFREEZE-01/02 preserved).

**HYPOTHETICAL-VOC caveat inherited** (A7 override `f181a7e`; compounding per `project_verdaca_strategic_sequencing` 2026-05-27 lock; real VOC gated to post-implementation+test demo).

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
| MCP gateway (inbound) | FastMCP / MCP SDK | Stage 11; transports: stdio + Streamable HTTP (`stateless_http=True` PINNED); verify exact MCP SDK version pin at `uv.lock` |
| JWT / OIDC / JWKS | authlib (PyPI) | Stage 12 `kernel/auth/`; `authlib.jose.JsonWebToken` + `authlib.jose.errors.JoseError`; alg-filter: RS256/RS384/RS512/ES256/ES384/ES512; httpx for OIDC discovery + JWKS fetch |
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

## Stage 7 Debt Ledger (19 items, originally deferred to "Stage 8"; folded into Stage 10/11/12 debt post-Stage-9 RATIFIED; Stage 11 added 2 new debt markers — STAGE-11-DEBT-AUTH-01 (OAuth/OIDC) + STAGE-11-DEBT-LITELLM-VKEY-01 (virtual keys) — **both CLOSED by Stage 12 E2**)

Not blocking forward work. Key items:

- **C-4 Memory `mac.reuse_successful` promotion path** — LATENT Stage-7 blocker; must resolve before headline becomes unconditional
- **A4 Spearman ρ ≥ 0.6 human validation** — headline caveat "(internal scoring; A4 deferred)" until resolved
- W-1..W-7 Cleo WARNINGs from Stage 5.3.5
- C-1..C-5 cross-stage architecture contradictions (C-4 is the live blocker)
- PDF + `.pptx` export (ADR-08, deferred)
- "Built With Praxis/Verdaca" public dashboard badge
