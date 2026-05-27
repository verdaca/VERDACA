# Handover B.E1 — Stage 12 Channel Adapters (Teams + Slack)

**Path of record:** `docs/stage-12-e1-channel-adapters-executor-handover.md` (gitignored-operational)
**Persona:** Executor — clean session
**Authored:** 2026-05-26 by Stage 11 RATIFIED close advisor (Opus 4.7 1M, MAX thinking)
**REFRESHED:** 2026-05-27 — applied BMAD roundtable opening positions (Murat MAC-T expansion + VCR-cassette discipline, Mary HARD-constraint additions, Winston `kernel/auth/` consumer-side path correction, contract-artifact handshake) + wiki sync + graphify Stage 11 source-scope refresh
**Parent handover:** `docs/stage-12-implementation-executor-handover.md`
**Sibling handover:** `docs/stage-12-e2-auth-integration-executor-handover.md`
**Window:** E1 — **commit-authority window** (receives E2 surfaces for landing per `feedback_concurrent_executor_orchestration`)
**Routing tag:** `[E1-H{N}]` for all findings, surfaces, halt markers, and commit messages
**Halt class:** GATE-CHANNELS (Teams + Slack adapters)

**Scope is TENTATIVE — Winston + roundtable ratifies at parent §3.1 charter halt; revise this handover before [E1-H#1] preload if scope shifts.**

**REFRESH NOTE — load-bearing deltas from 2026-05-27 BMAD roundtable:**
- **Winston #2026-05-27:** E1's consumer-side import path for auth shifts from `praxis.kernel.gateway.auth` → **`praxis.kernel.auth`** (E2's new cross-cutting module). See §6 integration handshake — code samples updated.
- **Murat #2026-05-27:** MAC-T scope expansion to **~20 entries for E1** (was 10-15): M-T-CHANNEL-teams-{1..10} + M-T-CHANNEL-slack-{1..10}. Webhook signature, event dedup, ack-window SLA, attachment passthrough, error envelope, rate-limit backoff per channel.
- **Murat #2026-05-27:** **VCR-cassette discipline (NOT Pact)** for Teams Bot Framework + Slack Events API consumer contracts. Microsoft + Slack won't run our provider verification, so Pact doesn't fit. VCR/recorded-fixture with periodic re-record cron is the right call. Pact would only make sense if we ship our own provider stub for partner integrations later.
- **Murat #2026-05-27:** **2-3 of the 7-9 Stage 12 no_waiver candidates land in E1** — webhook signature validation per-channel (impersonation surface): `M-T-CHANNEL-teams-WEBHOOK-SIG-01` + `M-T-CHANNEL-slack-WEBHOOK-SIG-01`.
- **Murat #2026-05-27:** **Cross-window contract artifact** — `[E2-H#2-COMPLETE]` is defined as a contract artifact (auth_claims schema frozen + 3-5 fixture claims published at `tests/fixtures/auth_claims/`), NOT a vibes-check. E1 codes against these fixtures and unblocks immediately upon E2 publishing them; integration test runs post-merge.
- **Mary #2026-05-27:** HARD-constraint expansion — `\bseamless\b` + `\benterprise-grade\b` added to forbidden-token grep (word-boundary, case-sensitive) for any Teams/Slack user-facing copy (adaptive card text, Slack Block Kit text, app manifest descriptions, README fragments). `\bstrategic analysis\b` from Stage 11 carries forward.
- **Mary #2026-05-27:** Buyer-language H#7 repeat is non-negotiable for any Teams/Slack-facing surface. Budget that into the E1 close + H#7 phase.

**Authorized models:**
- Advisor: Opus 4.7 (1M context), MAX thinking
- Executor: advisor-set per phase. Default — Codex/GPT-5 high reasoning for impl; Opus 4.7 (1M) for sub-charter / amendment phases. Surface actual model in [E1-H#1].

**Memory authorization:** Per `feedback_memory_authorization` — executor proposes; advisor authorizes; team-lead "save" writes.

---

## §1 Preload — session-surface audit ([E1-H#1])

Surface in first response, before any action:

1. **Session ID / model / JSONL path / working directory** (per `feedback_session_surface_audit`).
2. **Active branch** — `stage-12.0-channel-adapters` (cut from `stage-11.0-mcp-gateway @ e0aade3`; verify with `git log --oneline -1`).
3. **Memory state** — confirm loaded: `project_verdaca_stage11_ratified`, `project_verdaca_stage10_ratified`, `project_verdaca_stage10_11_decision`, `feedback_concurrent_executor_orchestration`, `feedback_memory_authorization`, `feedback_advisor_executor_model_effort`, `feedback_provenance_pin`, `feedback_handover_template_discipline`, `feedback_hard_constraint_word_boundary`.
4. **Handover-template drift check** — surface `F-12-E1-HANDOVER-{N}` at [E1-H#1] if any path / section-role / SHA does not resolve.
5. **Stage 12 charter loaded** — `_bmad-output/implementation-artifacts/verdaca/stage12/ports-architecture-delta.md` v0.1+ ratified.
6. **Frozen Stage 11 ports verified** — `python -c "from praxis.ports.gateway import GatewayPort, ChannelAdapterPort; from praxis.ports.gateway_dto import ChannelContext, AuthClaims, CallerKind, ChannelKind; print('OK')"` succeeds; `ChannelKind.TEAMS` + `ChannelKind.SLACK` enum values present (per Winston #1 at Stage 11).
7. **Sibling-window coordination** — confirm E2 status (auth integration in flight / not yet started); cross-window drift surfaced via `F-12-E1-E2-DRIFT-*`.

---

## §2 Entry preconditions (BLOCKING — verify before [E1-H#2.1])

Parent §3 H#A12 (if applicable) + H#1 + H#2 + H#3 MUST be CLOSED before E1 opens.

| # | Precondition | Verification |
|---|---|---|
| 1 | A12 closed (if abbreviated VOC chosen) | `docs/stage-12-voc-gate.md` shows `provisional_voc=False` OR (if HYPOTHETICAL inherited per team-lead G2) parent charter §VOC documents inheritance |
| 2 | H#1 §3.0 substrate probes GREEN | botbuilder + slack-sdk + authlib + litellm virtual_keys API surface tests passing |
| 3 | H#2 §3.1 charter ratified | Stage 12 v0.1+ charter exists; advisor + Winston party-mode ratification confirmed |
| 4 | H#3 §3.2 MAC-T catalog ratified | Stage 12 v0.1+ test-strategy delta exists; advisor + Murat party-mode ratification confirmed; allow-list delta strict equality meta-test in place |
| 5 | `stage-12.0-channel-adapters` branch exists | `git rev-parse stage-12.0-channel-adapters` |
| 6 | Working tree clean within E1 path scope | `git status` shows no uncommitted changes under `adapters/channels/` or E1 test files |
| 7 | Stage 11 frozen ports surface intact | ports/README.md carries 3 freeze lines (1fc37c2 + 9609c29 + af5d4f4); no diff to gateway.py / gateway_dto.py / gateway_errors.py |
| 8 | E2 status known | Either (a) E2 not started — E1 proceeds independently; auth-claims wiring deferred to E2 [E2-H#2.x-COMPLETE], OR (b) E2 surfaces auth APIs ready — E1 wires AuthClaims population in TeamsChannelAdapter + SlackChannelAdapter |

If any precondition fails → HALT, surface `F-12-E1-PRELOAD-{N}` to advisor.

---

## §3 E1 Scope

**Parent §§:** §3.3 (TENTATIVE) — channel adapter implementations
**Halt class:** GATE-CHANNELS
**Blast radius:** `adapters/channels/teams/` + `adapters/channels/slack/` + channel-specific test seams in `tests/` + VCR cassette fixtures at `tests/fixtures/vcr_cassettes/{teams,slack}/`
**MAC-Ts owned (REVISED per Murat #2026-05-27):** Expected **~20 entries**:
- **M-T-CHANNEL-teams-{1..10}** (~10): webhook signature verification, event dedup, ack-window SLA, attachment passthrough, error envelope, rate-limit backoff, adaptive card payload shape, conversationId mapping to channel_session_id, aadObjectId mapping to caller_id, Bot Framework activity type routing
- **M-T-CHANNEL-slack-{1..10}** (~10): X-Slack-Signature HMAC-SHA256 verification, Events API replay rejection (X-Slack-Request-Timestamp ±5min), Block Kit payload shape, threadTs mapping to channel_session_id, user.id mapping to caller_id, channel.id capture, event subtype routing, retry-after honor, rate-limit backoff, app_mention vs message event distinction

**no_waiver candidates owned (REVISED per Murat #2026-05-27):** 2-3 of the 7-9 Stage 12 candidates land in E1 (strong priors — impersonation surface):
- `M-T-CHANNEL-teams-WEBHOOK-SIG-01` — Teams webhook signature validation
- `M-T-CHANNEL-slack-WEBHOOK-SIG-01` — Slack X-Slack-Signature validation
- Final list ratified in Stage 12 allow-list delta — strict equality meta-test; never on initiative per `feedback_no_waiver_discipline`.

**Out of E1 scope (E2 owns, REVISED per Winston #2026-05-27 — `kernel/auth/` pivot):** `kernel/auth/` (NEW — cross-cutting auth substrate; not gateway-local auth), `adapters/litellm/virtual_keys.py`, `kernel/gateway/policy.py` refactor. **NEVER touch these paths.**

**Out of E2 scope but informational:** if E2's `praxis.kernel.auth.*` API or LiteLLM virtual keys API surfaces force a ChannelContext / AuthClaims signature change → REFREEZE-03 ceremony (advisor + Winston party-mode); not E1's call.

**Other E2 work:** Stage 11 MCP adapter at `adapters/mcp_server/` — DO NOT TOUCH (Stage 11 RATIFIED scope).

---

## §4 E1 Halt sequence (TENTATIVE)

- **[E1-H#1]** — preload + entry preconditions (§§1+2)

- **[E1-H#2]** — Teams adapter:
  - **[E1-H#2.1]** RED: `tests/.../test_teams_channel_adapter_contract.py` fails by `NotImplementedError`/`ImportError`
  - **[E1-H#2.2]** package skeleton:
    ```
    adapters/channels/teams/
      pyproject.toml
      src/praxis/adapters/channels/teams/
        __init__.py
        adapter.py             # TeamsChannelAdapter implementing ChannelAdapterPort
        webhook.py             # MS Teams bot framework webhook handler
        manifest.py            # Teams app manifest helper (descriptive only, not auto-installed)
    ```
  - **[E1-H#2.3]** Wire TeamsChannelAdapter:
    - implements ChannelAdapterPort from praxis.ports.gateway (canonical path per Winston #2)
    - populates ChannelContext with caller_id (Teams aadObjectId), caller_kind (HUMAN), channel (ChannelKind.TEAMS), channel_session_id (Teams conversationId), request_id (UUIDv4), auth_claims (from `praxis.kernel.auth.validate_jwt` + `map_claims_to_auth_claims` per Winston #2026-05-27 kernel/auth/ pivot — code against E2's published fixtures at `tests/fixtures/auth_claims/entra_*.json` until [E2-H#2-COMPLETE] lands)
    - delegates to GatewayPort.execute injected at bootstrap
    - serializes AnalysisResult to Teams-friendly adaptive card payload
  - **[E1-H#2.4]** webhook.py: HTTP endpoint receiving Teams bot framework events; HMAC signature verification (M-T-CHANNEL-teams-WEBHOOK-SIG-01 no_waiver candidate); routes to adapter.py.execute
  - **[E1-H#2.5]** VCR cassette discipline (Murat #2026-05-27): record fixture interactions with MS Teams Bot Framework at `tests/fixtures/vcr_cassettes/teams/` — periodic re-record cron documented in `tests/fixtures/vcr_cassettes/README.md`. NOT Pact (Microsoft won't run provider verification).
  - Contract tests GREEN (10 MAC-Ts per Murat breakdown — webhook sig, event dedup, ack SLA, attachment passthrough, error envelope, rate-limit backoff, adaptive card shape, conversationId mapping, aadObjectId mapping, Bot Framework activity-type routing).

- **[E1-H#3]** — Slack adapter (mirrors §H#2 structure):
  - **[E1-H#3.1]** RED: `test_slack_channel_adapter_contract.py`
  - **[E1-H#3.2]** package skeleton (`adapters/channels/slack/`)
  - **[E1-H#3.3]** Wire SlackChannelAdapter with ChannelKind.SLACK + channel_session_id (Slack threadTs or channelId); auth_claims via `praxis.kernel.auth` (consumes E2's published fixtures at `tests/fixtures/auth_claims/`)
  - **[E1-H#3.4]** events.py: Slack Events API handler with signature verification (X-Slack-Signature HMAC-SHA256 — M-T-CHANNEL-slack-WEBHOOK-SIG-01 no_waiver candidate) + X-Slack-Request-Timestamp ±5min replay rejection
  - **[E1-H#3.5]** VCR cassette discipline (Murat #2026-05-27): record fixture interactions with Slack Events API at `tests/fixtures/vcr_cassettes/slack/` — periodic re-record cron documented.
  - Contract tests GREEN (10 MAC-Ts per Murat breakdown). **This is the E2 unblock point if E2 wires bearer-replacement via OAuth at [E2-H#3].** Surface `[E1-H#3.3-COMPLETE]` to E2.

- **[E1-H#4]** — Integration handshake:
  - Confirm GatewayPort + ChannelAdapterPort signatures still stable (no drift from Stage 11 freeze)
  - Confirm E2 OAuth/OIDC auth.py + LiteLLM virtual_keys.py APIs satisfied by adapter calls
  - If E2 surfaced drift `F-12-E1-E2-DRIFT-*`, resolve before close

- **[E1-H#5]** — Commit-authority window: land E1 path-scoped commits + accept E2 surfaces.

Advisor confirms at every halt. Memory writes only on explicit team-lead "save" per `feedback_memory_authorization`.

---

## §5 Path-scoped commit discipline

Per `feedback_concurrent_executor_orchestration` shared-index H#4 hardening (precedent: F-9.4.6-B.1-W3-COMMIT-CONTAM-01 + Stage 11 zero-contamination record):

**E1 commits — explicit pathspec, NEVER `git commit -a` or `git commit .`:**

```powershell
git add adapters/channels/teams/
git add tests/src/praxis/contract_tests/ports/test_teams_channel_adapter_contract.py
git status   # MUST show only adapters/channels/teams/ and E1 test paths staged
git commit -m "feat: Stage 12 E1 — Teams channel adapter (Phase A.{N})"
```

For Slack similarly. **E2 surfaces commits via `F-12-E2-COMMIT-SURFACE-{N}` posts.** E1 inspects, confirms E2 path scope (`kernel/auth/` + `adapters/litellm/virtual_keys.py` + `kernel/gateway/policy.py` refactor), then lands as separate commit.

**Two separate confirm-then-commit tool calls per surface** — never combine E1 + E2 staging.

---

## §6 Integration handshake with E2

E1 consumes E2's published surface at adapter `auth_claims` population (REVISED per Winston #2026-05-27 — `kernel/auth/` pivot):

```python
from praxis.kernel.auth import validate_jwt, map_claims_to_auth_claims  # E2's kernel/auth/ public API
# in TeamsChannelAdapter.execute (Stage 13+ consumers use the same import path):
claims = validate_jwt(incoming_jwt_token, issuer=os.environ["VERDACA_OIDC_ISSUER"])
auth_claims = map_claims_to_auth_claims(claims)
```

**Canonical import path:** `praxis.kernel.auth` ONLY (mirrors Winston #2 Stage 11 `praxis.ports.gateway` discipline). No re-exports through `praxis.kernel.gateway`.

**E1 stability contract:** Signatures of `praxis.ports.gateway` + `praxis.ports.gateway_dto` MUST not change. If a charter amendment forces a signature change (e.g., new AuthClaims field), surface `F-12-E1-SIG-DRIFT-{N}` and pause E2 until reconciled via REFREEZE-03 ceremony (advisor + Winston coordinates).

**E1's cross-window dependency (REVISED per Murat #2026-05-27 — contract artifact discipline):** E1 BLOCKS at `auth_claims` population in TeamsChannelAdapter + SlackChannelAdapter on E2's **`[E2-H#2-COMPLETE]` as contract artifact** — NOT a vibes-check. Unblock conditions:
1. `praxis.kernel.auth.validate_jwt` + `map_claims_to_auth_claims` + `discover_idp` signatures FROZEN at a freeze SHA stamp commit (mirrors Stage 11 REFREEZE pattern)
2. **3-5 fixture claims published** at `tests/fixtures/auth_claims/{entra,okta,auth0}_*.json`
3. AuthClaims schema documented at `_bmad-output/implementation-artifacts/verdaca/stage12/auth-claims-contract.md`

E1 codes against these fixtures immediately upon publication. Integration test runs post-merge. Earlier E1 work (package skeleton, adapter signatures, webhook/events handlers) does NOT block on E2.

**Drift escalation:** Any cross-window interface mismatch surfaces as `F-12-E1-E2-DRIFT-{N}` and escalates to advisor.

---

## §7 E1 Close criteria

Before signaling E1 complete to advisor (REVISED per BMAD roundtable 2026-05-27):

1. All E1 MAC-Ts GREEN (count per Murat #2026-05-27: **~20 entries** — M-T-CHANNEL-teams-{1..10} + M-T-CHANNEL-slack-{1..10})
2. test_teams_channel_adapter_contract.py + test_slack_channel_adapter_contract.py: all GREEN
3. ChannelContext populated correctly per channel (TeamsChannelAdapter populates ChannelKind.TEAMS; SlackChannelAdapter populates ChannelKind.SLACK; both populate AuthClaims via `praxis.kernel.auth.validate_jwt` + `map_claims_to_auth_claims` — Winston #2026-05-27 kernel/auth/ pivot)
4. Webhook signature verification active: `M-T-CHANNEL-teams-WEBHOOK-SIG-01` (Teams HMAC, no_waiver) + `M-T-CHANNEL-slack-WEBHOOK-SIG-01` (Slack X-Slack-Signature HMAC-SHA256, no_waiver) + Slack X-Slack-Request-Timestamp ±5min replay rejection
5. AnalysisResult serialization to channel-specific payload tested (Teams adaptive card + Slack Block Kit)
6. **VCR cassette discipline (Murat #2026-05-27):** `tests/fixtures/vcr_cassettes/{teams,slack}/` populated with recorded MS Teams Bot Framework + Slack Events API interactions; periodic re-record cron documented in `tests/fixtures/vcr_cassettes/README.md`. NOT Pact.
7. E2 surfaces (if any landed during E1's window) committed with path-scoped discipline per §5; E2's `kernel/auth/` workspace member registration in root `pyproject.toml` confirmed (19→20 active members)
8. `F-12-E1-HANDOVER-*` findings ledger: routed or closed
9. Cross-window drift `F-12-E1-E2-DRIFT-*`: zero open
10. mypy strict on `adapters/channels/{teams,slack}/src` clean
11. ruff clean on `adapters/channels/{teams,slack}/`
12. **HARD-constraint grep (Mary #2026-05-27):** zero hits on `\bstrategic analysis\b`, `\bseamless\b`, `\benterprise-grade\b` across any Teams/Slack user-facing surface — adaptive card text, Slack Block Kit text, app manifest descriptions, error envelope strings, README fragments. Variable names with underscores SAFE.
13. **Mary H#7 buyer-language audit (non-negotiable for Teams/Slack-facing surfaces):** budgeted into Phase 3 H#7 demo packaging — surface scope at E1 close for Mary's per-channel audit pass.

Advisor confirms; integration H#7 (Phase D demo packaging — master handover scope) opens after BOTH E1 + E2 complete.

---

## §8 Findings ledger

E1 findings carry `F-12-E1-*` prefix. Subtypes:
- `F-12-E1-PRELOAD-{N}` — preload / entry precondition issues
- `F-12-E1-HANDOVER-{N}` — handover-template drift
- `F-12-E1-SIG-DRIFT-{N}` — GatewayPort/ChannelAdapterPort signature drift post-Stage-11 freeze (would require REFREEZE-03)
- `F-12-E1-E2-DRIFT-{N}` — cross-window drift with E2 (escalate to advisor)
- `F-12-E1-{H#N}-{TOPIC}-{N}` — phase-specific findings

All findings open at surface time → routed at close. Status: CLOSED-IN-CYCLE / ROUTED-FORWARD (target stage) / ROUTED-TO-CLEO (H#8 review surface).

---

## §9 References

- **Parent handover:** `docs/stage-12-implementation-executor-handover.md`
- **Sibling handover:** `docs/stage-12-e2-auth-integration-executor-handover.md` (E2 surfaces; E1 holds commit authority per Stage 11 precedent)
- **Stage 12 advisor handover:** `docs/stage-12-advisor-handover.md`
- **Stage 11 RATIFIED close memo:** `docs/stage-11-ratified-close-memo.md` (commit `e0aade3`)
- **Frozen Stage 11 ports:** `ports/src/praxis/ports/{gateway,gateway_dto,gateway_errors}.py`
- **Stage 11 GatewayPort impl (consumed via composition):** `kernel/gateway/src/praxis/kernel/gateway/service.py`
- **Stage 11 MCP adapter (pattern reference for adapter shape):** `adapters/mcp_server/src/praxis/adapters/mcp_server/`
- **E2's kernel/auth/ public API (consumed by E1 for auth_claims population):** `kernel/auth/src/praxis/kernel/auth/__init__.py` (lands during [E2-H#2]; canonical import `praxis.kernel.auth`)
- **E2's published auth_claims fixtures (E1 codes against these):** `tests/fixtures/auth_claims/{entra,okta,auth0}_*.json` (lands during [E2-H#2-COMPLETE])
- **Verdaca wiki (refreshed 2026-05-26):** `knowledge/wiki/verdaca/{stage-9-state,current-architecture,remaining-work}.md` — Stage 11 RATIFIED + Stage 12 OPEN; 4 MVP ChannelKinds (CLI, TEAMS, SLACK, CLAUDE_DESKTOP per Winston #1)
- **Verdaca knowledge graph (refreshed 2026-05-26):** `graphify-out/GRAPH_REPORT.md` — Stage 11 source-scope (592 .py files / 6,319 nodes / 541 communities); pattern reference community 29 (`MCP Server Adapter`) for adapter shape — Stage 12 E1 will add new communities for Teams + Slack
- **MS Teams bot framework docs:** (verify via context7 MCP at H#1 substrate probe)
- **Slack Events API docs:** (verify via context7 MCP at H#1 substrate probe)
- **VCR.py reference:** vcrpy.readthedocs.io (per Murat #2026-05-27 — NOT Pact)
- **Concurrent executor discipline:** `feedback_concurrent_executor_orchestration` memory
- **Stage 11 commit choreography precedent:** Stage 11 §10.3 + F-9.4.6-B.1-W3-COMMIT-CONTAM-01
- **Project root:** `CLAUDE.md`
- **Memory dir:** `~/.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/memory/`

End of Handover B.E1.
