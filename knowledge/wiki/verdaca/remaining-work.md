# Verdaca — Remaining Work to POV-Ready

**Compiled:** 2026-05-08 → **Updated:** 2026-05-29 (Stage 13 RATIFIED + merged to main + Path A CLOSED + Stage 14 G1 OPEN) | **Working branch HEAD:** `stage-14.0-buyer-contact-surface @ 620b4cb` (cut from main 2026-05-29) | **local main = origin/main = `620b4cb`** (Stage 13 RATIFIED close memo; tag `stage-13.0-ratified` → `620b4cb` pushed origin 2026-05-28; Path A CLOSED via team-lead override of D13) | **Stage:** Stage 9 RATIFIED 2026-05-20; Stage 10 RATIFIED 2026-05-24; Stage 11 RATIFIED 2026-05-26; Stage 12 RATIFIED 2026-05-27; **Stage 13 RATIFIED 2026-05-28** at `620b4cb` (14-commit chain from base `5306c8d`; auth quartet invoked-in-execute + composition root build_gateway() 11-param + OidcPolicy + NonceStore SQLite + Teams/Slack async post_result + WebhookSigningKeyResolver + session-id W-1 + 6 AST gates A-F; 321 tests / 13 runtime no_waiver / 6 AST gates / 19 total enforced markers; 5/5 V1 Cleo CLOSED + 2/12 V3 CLOSED at V3.A + 10 V3 carry-forward Stage 14; close memo `docs/stage-13-ratified-close-memo.md` TRACKED on main); **Stage 14 OPEN** — G1 RATIFIED 2026-05-28 via 6-agent roundtable Winston+Vera+Amelia+Murat+John+Mary (3 rounds, 16 responses, full alignment); cycle = "Buyer Contact Surface via auditor gate"; Phase 0 dual-track Week 1 + two end-of-Week-1 hard gates (CVE PASS ∧ B-6 auditor floor attestation). A7 HYPOTHETICAL-VOC caveat compounds on merged main; **PROVISIONAL-SINGLE-SAMPLE replaces HYPOTHETICAL-VOC after N=1 first Champion call (full retire needs N≥3 per Murat lock)**: every population/magnitude/pricing claim still carries HYPOTHETICAL-VOC tail until N≥3; existence/disqualification claims downgrade at N=1.

---

## Stage 10 — CLOSED RATIFIED 2026-05-24 (Historical)

Stage 9 RATIFIED 2026-05-20 (`origin/main` merge `76eea26`, CI close `3e26f48`). Stage 10 implementation landed at `d2b5670` (#42); merged via `8ae4f87` 2026-05-24; A7 override push to origin completed at `f181a7e` 2026-05-24.

| Item | Status |
|---|---|
| Mary's VOC | COMPLETE-PROVISIONAL 2026-05-24 — HYPOTHETICAL synthesis (3 simulated archetypes); verdict GO-with-amendments, LOW confidence; K1/K2/K3 each fired 1/3 (zero margin); buyer-language HARD audit 0 hits |
| Path 1 lock (team-lead 2026-05-24) | Synthesis accepted as provisional; A2/A3/A5 → Stage 11.x scope; A1/A4/A6 → Stage 11.x ledger |
| Stage 10 RATIFIED ceremony | COMPLETE 2026-05-24 — Winston/Murat/Cleo READY-WITH-AMENDMENTS; merge `8ae4f87` |
| `stage-10.0-port-stubs` FF into main | DONE via merge `8ae4f87` 2026-05-24 |
| A7 (real-VOC re-confirmation) | CLOSED via team-lead override 2026-05-24 at `f181a7e`; HYPOTHETICAL-VOC caveat inherited indefinitely to all downstream stages |
| `project_verdaca_stage10_ratified` memory entry | WRITTEN 2026-05-24 (team-lead authorized save) |
| Push to origin | DONE 2026-05-24 — `local main = origin/main = f181a7e` (in sync) |

---

## Stage 9 Sequence — COMPLETE 2026-05-20

```
9.4.4 Pi-Mono    ✅ RATIFIED 2026-05-08 (close `eccc307`)
  ↓
9.4.5 LLM Proxy  ✅ RATIFIED 2026-05-12 (close `5b7019f`; H2-falsification — Docker sidecar retired; LiteLLM sole substrate)
  ↓
9.4.6 Compaction ✅ RATIFIED 2026-05-17 (close `85bdea1`; ADR-9.2-V6 substrate Forge→LLMLingua; CompactionPort + 2 adapters + 14 M-T-COMP-*; Phase 0 P0.1-P0.3 closed in parallel)
  ↓
Pair 1 [concurrent]
  9.4.7 Namespace ✅ CLOSED 2026-05-18 (`c466049`) — 12 markers deleted, _archive/ created
  9.4.8 FTS5      ✅ CLOSED 2026-05-18 (`2b7cbf3`) — scripts/index-sessions.py + knowledge/sessions.db
  ↓
Pair 2 [concurrent]
  9.5 Arch review ✅ CLOSED 2026-05-19 (`e7bd77d`) — F10 document-and-defer; PATHWALK fix
  9.9 Test-strat  ✅ CLOSED 2026-05-19 (`ef401a2`) — Stage-9 enforcer + sublist 6→9 + F11/F12/F13 close
  ↓
9.6 Cleo supply-chain ✅ CLOSED 2026-05-19 (`3e26f48` #40; merge `76eea26`)
  ↓
Stage 9 RATIFIED 2026-05-20 — full ports-and-adapters production rebuild
  ↓
9.4.2 TONL — deferred-work (authorized separate launch; not blocking forward sequence)
```

⚠ Memory entry `[[project_verdaca_stage9_ratified]]` cites SHA `45e1fd8 #41`; that commit exists only on feature branches (`stage-9.4.7-namespace-cleanup`, `stage-9.6-cleo-supply-chain`, `stage-10.0-port-stubs`) and is a 9.6 corrigendum not merged into `origin/main`. The actual Stage-9 close on `origin/main` is `3e26f48` (#40 CI close) + `76eea26` (Stage 9 ratification merge). Memory SHA correction pending team-lead authorization.

---

## Stage 7 Debt Items That Gate Future Milestones

| Item | Blocks | Priority |
|---|---|---|
| **C-4** — Memory `mac.reuse_successful` promotion path | Production launch headline | HIGH — resolve before external demos |
| **A4** — Spearman ρ ≥ 0.6 human validation | Headline caveat removal | HIGH |
| **C-1..C-3, C-5** — arch contradictions | POV delivery quality | MEDIUM |
| W-1..W-7 Cleo WARNINGs | Code quality | MEDIUM |
| PDF + pptx export | Stage 7 completeness | LOW |
| "Built With Verdaca" dashboard badge | Pre-sales asset | LOW |

---

## Per-Stage Gate Criteria (current)

### Stage 10 RATIFIED — COMPLETE (Historical)
- [x] Mary's VOC complete + synthesized — PROVISIONAL via HYPOTHETICAL synthesis 2026-05-24
- [x] VOC readout = GO-with-amendments (K1/K2/K3 each triggered once — fragility flag noted)
- [x] `stage-10.0-port-stubs` FF into main — DONE via merge `8ae4f87` 2026-05-24
- [x] Close memo with §provenance table + A7 gate — DONE at [[docs/stage-10-ratified-close-memo.md]] (`da47d67`)
- [x] Andrey explicit "continue" go to Stage 11 — DONE (A7 closed via team-lead override 2026-05-24 at `f181a7e`)
- [x] `project_verdaca_stage10_ratified` memory entry authorized + written — DONE 2026-05-24

### Before Stage 11 charter opens — COMPLETE (Historical)
- [x] Stage 10 RATIFIED (2026-05-24)
- [x] 4 substrate-API probes PASS — FastMCP / JSON-RPC 2.0 / stateless HTTP / Gateway contract
- [x] CAI spike port viable: `spike-mcp-server/src/http.ts` → `adapters/mcp_server/http.py` mirror

### Stage 11 RATIFIED — COMPLETE (Historical) 2026-05-26
- [x] `adapters/mcp_server/` implements GatewayPort + ChannelAdapterPort (Claude-Desktop LIVE; Teams/Slack/CLI deferred to Stage 12)
- [x] 5 MCP tools + 5 resources + 1 prompt working end-to-end against Claude Desktop
- [x] 38 MAC-Ts (Stage 11 delta) + 5 no_waiver entries strict-equality meta-test
- [x] 208 contract tests GREEN + 8 skipped (env-gated DIAL live)
- [x] 4 BMAD ratifications closed with amendments (Winston/Murat/Mary/Cleo); Cleo H#8 V2 substantive close at `1adbecb`
- [x] Branch tip `e0aade3` (close memo); 20 commits from `a11aa67` to `e0aade3`; Path A local-only (NOT merged to main)

### Before Stage 12 charter opens — COMPLETE (Historical) 2026-05-27
- [x] **G1** Stage 12 scope confirmation roundtable (Winston + Mary + Murat + Vera + advisor) — CLOSED 2026-05-27 (14 amendments D1–D11; E1=channels + E2=auth + uv 19→22)
- [x] **G2** VOC decision — CLOSED: option (a) inherit HYPOTHETICAL caveat indefinitely
- [x] **G3** Cut `stage-12.0-channel-adapters` from `stage-11.0-mcp-gateway @ e0aade3` — DONE (Path A continuation)
- [x] **G4** Executor split confirmed — E1 = channels, E2 = auth
- [x] **G5** Stage 11.5 debt scheduled — DIAL-LIVE-SMOKE resolved in-cycle; AUTH-01 + LITELLM-VKEY-01 closed by E2; JSONRPC-FIXTURE-REGEN + RUFF-CLEANUP + SESSION-ID-WIDTH + WAL-CONCURRENCY carry to Stage 13
- [x] **G6** Executor dispatched + closed (E1 + E2 + 1 E2 redispatch after DIAL_API_KEY env export fix)
- [x] **G7** Local-only maintained — Stages 11+12 still NOT merged to main (Path A; D13)

### Stage 12 RATIFIED — COMPLETE (Historical) 2026-05-27
- [x] E1 = Teams + Slack `ChannelAdapterPort` impls landed under `adapters/channels/{teams,slack}/` — DONE (HMAC-SHA256; X-Slack-Signature v0)
- [x] E2 = OAuth 2.1 + OIDC via `kernel/auth/` (claims.py, oidc.py, jwt.py, idp.py, nonce.py) — DONE; `policy.py` refactored to thin orchestrator
- [x] E2 = LiteLLM virtual keys via `adapters/litellm/virtual_keys.py` (HTTP-client; no Python SDK) + `ports/virtual_key.py` — DONE; STAGE-11-DEBT-AUTH-01 + STAGE-11-DEBT-LITELLM-VKEY-01 CLOSED
- [x] Cross-window dep honored — DONE
- [x] Frozen Port surfaces respected — no REFREEZE-03 triggered
- [x] 281 tests pass / 8 skipped / 0 failed; 47 MAC-Ts; 9 no_waiver strict-equality; 6 AST gates green
- [x] Mary buyer-language audit PASS-WITH-AMENDMENTS (H#7); Cleo adversarial FAIL→PASS post-V2 (H#8)
- [x] Close memo: `docs/stage-12-ratified-close-memo.md` at `43f57ba`; 5 findings → Stage 13

### Before Stage 13 charter opens — COMPLETE (Historical) 2026-05-27
- [x] **G1** Stage 13 scope confirmation roundtable (Winston + Murat + Cleo + Vera + Amelia) — RATIFIED 2026-05-27 (R1–R14 + R15-V2 + R16-V3 + V3.1 corrigenda)
- [x] **G2** VOC — CLOSED: inherits HYPOTHETICAL caveat
- [x] **G3** Cut `stage-13.0-production-hardening` from `9fe3057` (post-Stage-12-hygiene-tip) — CLOSED 2026-05-28 (later FF'd to `5306c8d`)
- [x] **G4** Executor split E1 (auth/channel) ‖ E2 (hygiene/data-plane); E2 commits first
- [x] **G5** Debt scheduling — 7 scope IN; WAL-CONCURRENCY DEFERRED per R6
- [x] **G6** Dispatch master executor + V2 (CRITICAL→HIGH→MEDIUM→LOW) + V3.A — CLOSED 2026-05-28
- [x] **G7** Path A — CLOSED 2026-05-28 via team-lead override; Stages 11+12+13 merged to main + tag `stage-13.0-ratified` pushed

### Stage 13 RATIFIED — COMPLETE (Historical) 2026-05-28
- [x] All 7 scope IN items closed via E1 + E2 + V2 + V3.A (auth quartet invoked-in-execute; composition root build_gateway 11-param; NonceStore SQLite BEGIN IMMEDIATE; Teams/Slack async post_result; WebhookSigningKeyResolver; gateway session-id W-1 128-bit; JSONRPC-FIXTURE-REGEN no-delta; WAL-CONCURRENCY DEFERRED documented)
- [x] 47 MAC-Ts (Stage 13 delta) + 13-entry no_waiver strict-equality at `test_stage13_no_waiver_count.py` (9 Stage 12 preserved + 4 new: `M-T-GATEWAY-EXECUTE-AUTH-FIRST-01` V2.A rename, `M-T-AUTH-NONCE-PERSISTENCE-RESTART-01`, `M-T-SESSION-ID-ENTROPY-FLOOR-01`, `M-T-NO-BARE-EXCEPT-AUTH-CRYPTO-01`) + 6 AST gates A-F (added Gate F close-memo tracking symmetry per Murat R16-a V3)
- [x] 321 tests pass / 8 skipped / 1 warning at close
- [x] H#7 Mary buyer-language audit PASS — zero HARD-constraint hits across Stage 13 source
- [x] H#8 Cleo V1 FAIL → V2 (CRITICAL `e2ece6f` + HIGH `f91aad0` + MEDIUM `2776be0` + LOW `3fc11c7`) → V3 FAIL → V3.A (HIGH `1ce9539` V1 C-1 binding criterion fully closed; V3 PASS-WITH-AMENDMENTS 10 carry-forward Stage 14)
- [x] Close memo: `docs/stage-13-ratified-close-memo.md` TRACKED on main `@620b4cb` (per `.gitignore:61` negation); merged to main 2026-05-28; tag `stage-13.0-ratified` pushed to origin

### Before Stage 14 charter opens — IN FLIGHT
- [x] **G1** Stage 14 scope confirmation 6-agent roundtable (Winston + Vera + Amelia + Murat + John + Mary) — RATIFIED 2026-05-28 (3 rounds, 16 responses, full alignment; cycle = "Buyer Contact Surface via auditor gate")
- [x] **G2** VOC — OPEN (Phase 1; first Champion call scheduled contingent on B-6 attestation)
- [x] **G3** Cut `stage-14.0-buyer-contact-surface` from main `@620b4cb` — CLOSED 2026-05-29
- [x] **G4** Executor split — Phase 0 Track A (engineering CVE close) ‖ Track B (Mary-coordinated GTM + auditor floor split with Cleo + Murat)
- [x] **G5** Memory `project_verdaca_stage14_scope` saved — CLOSED 2026-05-28
- [ ] **G6** Phase 0 end-of-Week-1 hard gates (CVE PASS ∧ B-6 auditor floor attestation) — OPEN
- [ ] **G7** Phase 1 release (Champion VOC + demo runbook + onboarding + Charter ratification) — OPEN, contingent on G6

### Stage 14 RATIFIED when — TENTATIVE
- [ ] Phase 0 Track A: B1 bundle JWKS-NOT-INTEGRATED + AUDIENCE-DOUBLE-DECODE + R15-c TTL race + R15-d no_waiver constant pin; vkey REQUIRED fail-closed at production profile; policy_health_check; Charter v0.2 11-param ratification (M2 buyer-language audit zero hits)
- [ ] Phase 0 Track B: B-1 through B-7 (target list + first-call script + HYPOTHETICAL-VOC disclosure + SOC2 pre-flight checklist + auditor meeting worksheet + reconciliation attestation + scheduling contingent on B-6)
- [ ] Phase 1: First Champion VOC call against clean substrate; demo runbook + onboarding pipeline (M3 buyer-language audit); K1/K2/K3 pre-registration table authored BEFORE call; post-call hypothesis-class log + HYPOTHETICAL-VOC → PROVISIONAL-SINGLE-SAMPLE caveat downgrade
- [ ] Phase 2: Stage 14.5 named debt closure (PARSE-ACTIVITY event-gated)
- [ ] Canonical pin: 13/6/19 → **14/9/23** (+1 no_waiver `M-T-AUTH-JWKS-ROTATION-INVARIANT-01`; +3 AST gates A-S14/B-S14/C-S14; AUDIENCE bundled in B1 with +2 MAC-Ts + 1 AST gate but NO no_waiver per Murat lock "bundled commit ≠ bundled discipline" risk 5 < 7)
- [ ] H#7 Mary buyer-language audit PASS — 6 forbidden tokens zero hits (`\bstrategic analysis\b` + `\bseamless\b` + `\benterprise-grade\b` + `\brobust\b` + `\bproduction-ready\b` (+ hyphen) + `\bcomprehensive\b`)
- [ ] H#8 Cleo adversarial review = PASS or PASS-WITH-AMENDMENTS
- [ ] B-6 auditor floor attestation language: "Stage 14 Phase 0 auditor floor satisfied at SHA [X]. ... HYPOTHETICAL-VOC caveat inherited; auditor floor does NOT supersede VOC requirement."

---

## Stage 10 — CLOSED RATIFIED 2026-05-24 (Historical)

Decided at 5-agent roundtable 2026-05-20 (4-1 vote for data-plane / transport split). Hermes Agent self-learning roadmap is preserved; the 2026-05-08 plan was reshaped into the data-plane-first sequence below.

### Implementation status — CLOSED
- Branch: `stage-10.0-port-stubs` — FF'd into `main` at `8ae4f87` 2026-05-24
- Implementation: `d2b5670` (#42); amendment commits `3d576a9` + `da47d67`
- **RATIFIED 2026-05-24** at merge `8ae4f87`; A7 CLOSED via team-lead override 2026-05-24 at `f181a7e` (pushed to origin); HYPOTHETICAL-VOC caveat inherited indefinitely

### Ports (landed)
| Port | Methods | Key DTOs |
|---|---|---|
| `SessionIndexPort` (API_VERSION 1.0.0) | index_session, search(mode=keyword\|semantic), list_sessions, get_session, get_artifact, get_telemetry | SessionExcerpt, SessionRecord, SessionFilter, ArtifactRef, TelemetryEvent, TimeWindow |
| `SkillTelemetryPort` (renamed from SkillObserverPort) | record_invocation, query(window) | SkillOutcome, SkillUsage, SkillInvocationRecord |

Semantic search is a no-op stub at Stage 10 (keyword/FTS5 only); semantic promotion is a Stage-10.1+ enhancement.

### CLI surface
`verdaca session list` + `verdaca session show <id>` — replay + cost surfaces.

### MAC-T + allow-list deltas
- +4 no_waiver entries (9 → 13)
- MAC-T floor ≥18: `M-T-SESSIONIDX-*` (11) + `M-T-SKILLTEL-*` (6) + `M-T-TELEMETRY-*` (1)

### Stage 10 §7 debt items routed forward
- F-10-EDGE-03 (SQLite WAL/pooling for async)
- F-10-EDGE-04 (max payload guard)
- F-10-COMPRESSION-MOCKER-DEP-01
- F-10-MAC-CRLF-SNAPSHOT-01
- F-9.4.6-LLMLINGUA-MAINTENANCE-STALENESS-1 (carried from 9.6 CVE-deferrals)

### VOC artifacts (`_bmad-output/planning-artifacts/Verdaca/voc-stage10/`)
- `voc-stage10-icp-and-target-list.md` — Champion cohort definition
- `voc-stage10-call-script.md` — interview script (governance preference, VP readout, vendor onboarding, JTBD)
- `voc-stage10-scoring-rubric.md` — GO / GO-with-amendments / PIVOT decision; 4 kill-switch criteria K1-K4
- `voc-stage10-synthesis-template.md`, `voc-stage10-readout-template.md`, `README.md`

### Carry-forward: SkillPort + curator/honcho adapters
The original Stage 10 Phase 2/3 design (`SkillPort` with apply_patch authorization gate, `adapters/skill_curator/`, `adapters/honcho/`) is **deferred to Stage-10.1+ or Stage-12**. Stage 10 ships only SessionIndex + SkillTelemetry as the data-plane substrate; curator/state-machine work happens after the VOC tells us users actually need it.

---

## Stage 11 — Channel-Neutral MCP Gateway — RATIFIED 2026-05-26

RATIFIED 2026-05-26 on `stage-11.0-mcp-gateway @ e0aade3` (Path A local-only; NOT merged to main). 20 commits from `a11aa67` to `e0aade3`; H#8 V2 substantive close at `1adbecb`. Atlas + Mary precedent from CAI spike: populated MCP resources sold the demo, not tool calls — Stage 11 binds to ratified `SessionIndexPort` (NO stubs).

### What shipped
- **Branch tip:** `stage-11.0-mcp-gateway @ e0aade3` (close memo); H#8 V2 substantive close `1adbecb`; 20 commits from base `a11aa67` (base `f181a7e`)
- **New kernel module:** `kernel/gateway/` — `VerdacaGatewayService` composes all 5 data-plane ports (LLMProxy + Memory + Cost + Compaction + SessionIndex)
- **New adapter:** `adapters/mcp_server/` — FastMCP-backed; 5 tools + 5 resources + 1 prompt + 2 transports (stdio + Streamable HTTP)
- **2 REFREEZE ceremonies:** read API freeze `9609c29` + list_sessions freeze `af5d4f4`
- **Stage 10 SessionFilter additive corrigendum** applied at `50fa909`
- **38 MAC-Ts** (Stage 11 delta) + **5 no_waiver** entries strict-equality meta-test
- **208 contract tests GREEN** + 8 skipped (env-gated DIAL live)
- **4 BMAD ratifications** closed with amendments (Winston/Murat/Mary/Cleo)

### Ports (landed)
| Port | Notes |
|---|---|
| `GatewayPort` | `execute(intent: StartAnalysisRequest, ctx: ChannelContext) → AnalysisResult`; composes LLMProxy + Memory + Cost + Compaction + SessionIndex; frozen at H#1.5 + REFREEZE-01 + REFREEZE-02 |
| `ChannelAdapterPort` | 4 MVP adapters per Winston #1; **only Claude-Desktop is LIVE at Stage 11**; Teams/Slack/CLI deferred to Stage 12; frozen at H#1.5 + REFREEZE-01 + REFREEZE-02 |
| `MCPTransportPort` | adapter-local Protocol under `adapters/mcp_server/transport.py` (NOT in `praxis.ports` layer); stdio + Streamable HTTP; `stateless_http=True` PINNED |

**Frozen Port surfaces** — NO Stage 12 changes to GatewayPort or ChannelAdapterPort without REFREEZE-03 ceremony.

### MCP surface (5 tools + 5 resources + 1 prompt)
- Tool language ("buyer-language"): "defensible recommendation with cited tradeoffs"
- 5 tools: `verdaca_start_analysis`, `verdaca_estimate_cost`, `verdaca_get_result`, `verdaca_list_sessions`, `verdaca_get_artifact`
- Resources: `verdaca://methodology`, `verdaca://templates`, `verdaca://sessions/{id}/result/{summary,transcript,artifacts}`
- Mirror CAI spike: `spike-mcp-server/src/http.ts` → `adapters/mcp_server/http.py` (Python `mcp.server.fastmcp.FastMCP`); reference snapshot frozen at `tests/reference/spike-mcp-server-snapshot-d93f71a/`

### VOC-10 amendment carry-forward (Stage 11 inherited)
- **A2** — Word/PPT export surface — carried into Stage 11.x debt
- **A3** — 3 procurement gates — Stage 11 channel-adapter manifests partially address; full closure in Stage 12 channel work
- **A5** — Forwardable-link surface — carried into Stage 11.x debt
- **A7** — CLOSED via team-lead override 2026-05-24 at `f181a7e`; HYPOTHETICAL-VOC caveat inherited indefinitely
- **A1 / A4 / A6** — carried into Stage 11.x ledger

### Post-Stage-11 explicit defers (routed to Stage 12 or 11.x)
- Teams + Slack ChannelAdapter impls — Stage 12 E1 TENTATIVE
- CLI hardening — Stage 12 E1 optional TENTATIVE
- UI rewire to be a gateway client — Stage 11.x or later
- OAuth 2.1 + OIDC (Entra/Okta/Auth0) — Stage 12 E2 TENTATIVE (STAGE-11-DEBT-AUTH-01)
- LiteLLM virtual keys — Stage 12 E2 TENTATIVE (STAGE-11-DEBT-LITELLM-VKEY-01)
- Learning/feedback ports beyond SkillTelemetry — Stage 12+ or later
- Teams/Copilot manifests — Stage 12 E1 surface

---

## Stage 12 — Channel Adapters + Auth — RATIFIED 2026-05-27

RATIFIED 2026-05-27 at `43f57ba` on `stage-12.0-channel-adapters` (29 commits from base `e0aade3`). Path A local-only; NOT merged to main. Close memo: `docs/stage-12-ratified-close-memo.md`.

### Gates G1-G7 — ALL CLOSED

| Gate | Description | Status |
|---|---|---|
| **G1** | Scope roundtable (Winston + Mary + Murat + Vera + advisor) — E1=channels + E2=auth + uv 19→22; 14 amendments D1–D11 | CLOSED 2026-05-27 |
| **G2** | VOC — option (a): inherit HYPOTHETICAL caveat indefinitely | CLOSED |
| **G3** | Branch `stage-12.0-channel-adapters` cut from `e0aade3` | CLOSED |
| **G4** | Executor split — E1 (channels) ‖ E2 (auth) | CLOSED |
| **G5** | Debt scheduling — DIAL-LIVE-SMOKE resolved in-cycle; AUTH-01 + LITELLM-VKEY-01 closed by E2; 4 items carry to Stage 13 | CLOSED |
| **G6** | Executors dispatched + closed (E1 + E2 + 1 E2 redispatch) | CLOSED |
| **G7** | Path A maintained — Stages 11+12 local-only NOT merged to main (D13) | CLOSED |

### What shipped

- **Branch tip:** `stage-12.0-channel-adapters @ 43f57ba`; 29 commits from `e0aade3`; 4 cycle commits H#7→H#8.V2.D
- **kernel/auth/** (workspace member #22): `claims.py`, `oidc.py`, `jwt.py`, `idp.py`, `nonce.py`
- **adapters/channels/teams/** + **adapters/channels/slack/** — HMAC-SHA256; X-Slack-Signature v0
- **adapters/litellm/virtual_keys.py** — HTTP-client; no Python LiteLLM SDK
- **ports/virtual_key.py** — `VirtualKeyPort` + `VirtualKeySpec` + `VirtualKeyInfo` + `BudgetExhaustedError`
- **kernel/gateway/policy.py** — refactored to thin orchestrator
- **DIAL-LIVE-SMOKE RESOLVED** via Azure-style gpt-4o probe (in-cycle)
- **281 tests pass** / 8 skipped / 0 failed; 47 MAC-Ts; 9 no_waiver strict-equality; 6 AST gates green
- Mary buyer-language audit PASS-WITH-AMENDMENTS (H#7); Cleo adversarial FAIL→PASS post-V2 (H#8)

### Channel adapter live status (post-Stage-12)

| Channel | Status |
|---|---|
| Claude-Desktop | LIVE (Stage 11) |
| Teams | LIVE NEW (Stage 12) — HMAC-SHA256 |
| Slack | LIVE NEW (Stage 12) — X-Slack-Signature v0 |
| CLI hardening | Deferred |

### Stage 12 carry-forward findings → Stage 13

| Finding | Severity | Route |
|---|---|---|
| F-12-CLEO-C2-COMPOSITION-PENDING-01 — JwtVerifier wiring at composition root | CRITICAL | Stage 13 E1 |
| F-12-CLEO-M3-NONCE-RESTART-DEFER-01 — NonceStore SQLite persistence + TTL | MEDIUM | Stage 13 E1 |
| F-12-CLEO-W2-SYNC-HTTPX-01 — TeamsAdapter + SlackAdapter post_result → AsyncClient | LOW | Stage 13 E1 |
| F-12-OIDC-LIVE-DEFERRED-01 — Champion-gated live IdP smoke | DEFERRED | Champion-gated |
| F-12-CLEO-M5-FALSE-POSITIVE-01 — informational | INFO | informational |

### Inheritance
- HYPOTHETICAL-VOC caveat inherited indefinitely (A7 closed via override 2026-05-24)
- STAGE-11-DEBT-AUTH-01 + STAGE-11-DEBT-LITELLM-VKEY-01 CLOSED in-cycle by E2

---

## Stage 13 — Production Hardening — OPEN (G1 RATIFIED 2026-05-27)

Stage 13 is **OPEN**. G1 RATIFIED 2026-05-27 (R1–R14 advisor-reconciled + R15-V2 7-amendment patch folded pre-dispatch via Path α). Cycle = production hardening Option A — NO new feature surface. Continues local-only Path A from `43f57ba`. Branch `stage-13.0-production-hardening` not yet cut (G3 OPEN).

### Gates G1-G7

| Gate | Description | Status |
|---|---|---|
| **G1** | Scope roundtable (Winston + Murat + Cleo + Vera + Amelia, advisor-reconciled) — R1–R14 + R15-V2 7-amendment pre-dispatch patch (Path α) | RATIFIED 2026-05-27 |
| **G2** | VOC — inherits HYPOTHETICAL caveat per project_verdaca_strategic_sequencing | CLOSED |
| **G3** | Cut `stage-13.0-production-hardening` from `43f57ba` | OPEN (master executor Phase 0) |
| **G4** | Executor split — E1 (auth/channel hardening) ‖ E2 (hygiene/data-plane); E2 commits land first (no behavioral delta) | CLOSED via R11 |
| **G5** | Debt scheduling — 7 scope IN; WAL-CONCURRENCY DEFERRED per R6 | CLOSED via R1+R2 |
| **G6** | Dispatch master executor | OPEN |
| **G7** | Path A local-only — Stages 11+12+13 all local-only | CLOSED via D13 |

### Scope IN (7 items)

| # | Item | Executor | Severity |
|---|---|---|---|
| 1 | F-12-CLEO-C2 — JwtVerifier wiring at composition root; `OidcPolicy.__init__(verifier: JwtVerifier)` REQUIRED, no None default | E1 | CRITICAL |
| 2 | F-12-CLEO-M3 — NonceStore SQLite separate file + lazy TTL + startup sweep + WAL mode | E1 | MEDIUM |
| 3 | F-12-CLEO-W2 — async `post_result` via `httpx.AsyncClient` (Teams + Slack) | E1 | LOW |
| 4 | D4/Q1 — WebhookSigningKeyResolver dataclass per channel; fail-fast on missing env-var; manual restart-rotation (HYBRID, not port; promotable at 3rd channel) | E1 | CRITICAL-class |
| 5 | JSONRPC-FIXTURE-REGEN — regenerate Stage 11 golden fixtures | E2 | LOW |
| 6 | SESSION-ID-WIDTH — entropy floor ≥128 bits | E2 | MEDIUM |
| 7 | WAL-CONCURRENCY — DEFERRED per R6 (NonceStore on separate SQLite file; no shared writers) | — | DEFERRED |

### Scope OUT (5 items)
- F-10-ARCH-AUDIT-02 (shell workspace) → Stage 14
- F-12-OIDC-LIVE-DEFERRED-01 (Champion-gated)
- F-12-CLEO-M5-FALSE-POSITIVE-01 (informational)
- RUFF-CLEANUP → fold to CI baseline (not stage item)
- Cleo Q3 pre-existing sweep → Stage 14 candidates

### Test discipline
- MAC-T floor: 25 binding (distribution per Murat; exact breakdown uncertain — verify at H#3)
- no_waiver: 9 → **13** strict-equality (additions: `M-T-AUTH-VERIFIER-WIRED-AT-COMPOSITION-01`, `M-T-AUTH-NONCE-PERSISTENCE-RESTART-01`, `M-T-SESSION-ID-ENTROPY-FLOOR-01`, `M-T-NO-BARE-EXCEPT-AUTH-CRYPTO-01`)
- 5 AST gates A–E: claims-extraction ban + NonceStore persistent ClassVar + sync httpx in async ban + session-id entropy floor 128 bits + bare-except auth/crypto ban
- R10 mitigation: composition-root test must import + invoke canonical `shell/.../build_gateway()` factory via canonical-module-path reference
- 281+ tests still passing (Stage 12 baseline + Stage 13 additions)

### Pre-charter requirement
`/verdaca-wiki-update` + `graphify update .` BEFORE H#1 — kernel/auth/ not yet in wiki/graph (Vera load-bearing).

---

## Debt Tiers Post-Stage-11

### Stage 11.5 — post-Stage-12 status (5 items → 2 closed in-cycle; 3 routed)
- ~~DIAL-LIVE-SMOKE~~ — CLOSED IN-CYCLE (Stage 12; Azure-style gpt-4o probe)
- JSONRPC-FIXTURE-REGEN — → Stage 13 E2 scope IN
- SESSION-ID-WIDTH — → Stage 13 E2 scope IN
- WAL-CONCURRENCY — → Stage 13 DEFERRED per R6 (separate SQLite file; no shared writers)
- ~~RUFF-CLEANUP~~ — folded to CI baseline (not a stage item per Stage 13 R14)

### Stage 11.x — deferred features (6 items; 2 closed)
- ~~**STAGE-11-DEBT-AUTH-01**~~ — CLOSED IN-CYCLE (Stage 12 E2; kernel/auth/ landed)
- ~~**STAGE-11-DEBT-LITELLM-VKEY-01**~~ — CLOSED IN-CYCLE (Stage 12 E2; adapters/litellm/virtual_keys.py landed)
- Compose order
- WAL mid-exec crash
- Channel detection
- Cited tradeoffs stub

### Stage 10.5 — carried from Stage 10 (4 items)
- F-10-ARCH-AUDIT-02 — shell workspace pytest conflict
- F-10-EDGE-04 — max payload
- F-10-ARCH-AUDIT-04 + W-10-Cleo-6 — DRY `_DEFAULT_DB_PATH`
- F-10-TEST-AUDIT-02 — tighten allow-list bounds

### Stage 7 cosmetic (6 INFO)
- F-11-CLEO-13 through F-11-CLEO-18

---

## Rough Sequence Estimate (Sessions, Not Calendar Days)

| Work block | Sessions estimate |
|---|---|
| ~~9.4.4 → 9.4.6 (Pi-Mono, LiteLLM, Compaction)~~ | DONE through 2026-05-17 |
| ~~9.4.7 ‖ 9.4.8 Pair 1~~ | DONE 2026-05-18 (~0.5 session — concurrent) |
| ~~9.5 ‖ 9.9 Pair 2~~ | DONE 2026-05-19 (~1 session — concurrent) |
| ~~9.6 Cleo supply-chain + Stage 9 RATIFIED~~ | DONE 2026-05-19 → 2026-05-20 |
| ~~Stage 10 — VOC + ratification~~ | DONE 2026-05-24 (HYPOTHETICAL synthesis; A7 override push at `f181a7e`) |
| ~~Stage 11 — Gateway + MCP transport + Claude-Desktop ChannelAdapter~~ | DONE 2026-05-26 (`stage-11.0-mcp-gateway @ e0aade3`; Path A local-only) |
| ~~Stage 12 — E1 channels (Teams + Slack) + E2 auth (kernel/auth/ + VirtualKeyPort)~~ | DONE 2026-05-27 (`stage-12.0-channel-adapters @ 43f57ba`; 281 tests; Path A local-only) |
| Stage 13 — G1 RATIFIED; production hardening (7 scope IN, E1‖E2) | IN-FLIGHT (~1–2 sessions; branch cut + dispatch OPEN) |
| Stage 13 — demo packaging + Champion onboarding | TBD post-Stage-13 |
| **Total to POV-ready (post-Stage-13)** | unknown until Stage 13 closes |
| Post-Stage-13 (UI rewire, Stage 14 shell workspace, learning ports) | deferred |

---

## Quick Reference: What the Next Executor Needs

**For Stage 13 entry (next ratification work; G1 RATIFIED; G3+G6 OPEN):**
- Working branch: `stage-12.0-channel-adapters @ 43f57ba` (Path A local-only; NOT pushed to origin) — Stage 13 branch NOT yet cut
- `local main = origin/main = f181a7e` (Stage 10 RATIFIED; in sync via A7 override push 2026-05-24; Stages 11+12+13 local-only per D13)
- Stage 12 RATIFIED 2026-05-27 — close memo at `docs/stage-12-ratified-close-memo.md` (`43f57ba`)
- **G3 OPEN** — cut `stage-13.0-production-hardening` from `43f57ba` (master executor Phase 0)
- **G6 OPEN** — dispatch master executor (blocked on G3)
- **Pre-charter requirement:** run `/verdaca-wiki-update` + `graphify update .` BEFORE H#1 (Vera load-bearing; kernel/auth/ not yet in wiki/graph)
- 5 carry-forward findings from Stage 12 → Stage 13 scope IN (`docs/stage-12-ratified-close-memo.md` §findings)
- no_waiver strict-equality gate: **13** (was 9; +4 new markers; R10 composition-root test required)
- HYPOTHETICAL-VOC caveat inherited indefinitely: append "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)" to every customer-fit claim
- Frozen Port surfaces (GatewayPort + ChannelAdapterPort) — NO Stage 13 changes without REFREEZE-03 ceremony
- Halt discipline per `feedback_preload_first_gating`; memory writes gated per `feedback_memory_authorization`

---

## Design Work Remaining (Phase 3+)

- **Factory shell cycle** — next per-surface cycle (S-1..S-4 analogue for Factory product shell); opens at team-lead discretion (after a break per 2026-05-13 disposition)
- **Subsequent shells** — Shield, Pipeline, Ops (per parent brief §4.3)
- **v1.1 substrate amendment cycle** — gates on ≥3 surfaces from 7 P3-* candidates; no schedule yet
- **R3 dark-canonical re-disposition** — required before any production Studio deploy (F-3 thin-slice deviation must not extend to production)
- **v1.1 brand-mark amendments** — 3 candidates from brand-mark cycle: P-BM-1 (master glyph slot spec), P-BM-2 (archive path-of-record corrigendum), P-BM-3 (kickoff-template embedded-repo seam clarification)
