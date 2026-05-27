# Verdaca — Remaining Work to POV-Ready

**Compiled:** 2026-05-08 → **Updated:** 2026-05-26 (Stage 11 RATIFIED) | **Working branch HEAD:** `stage-11.0-mcp-gateway @ e0aade3` (Path A local-only; NOT pushed to origin) | **local main = origin/main = `f181a7e`** (Stage 10 RATIFIED in sync via A7 override push 2026-05-24) | **Stage:** Stage 9 RATIFIED 2026-05-20; **Stage 10 RATIFIED 2026-05-24** (VOC PROVISIONAL via HYPOTHETICAL synthesis; A7 closed via team-lead override; close memo at [[docs/stage-10-ratified-close-memo.md]]); **Stage 11 RATIFIED 2026-05-26** (Channel-Neutral MCP Gateway; Path A local-only on `stage-11.0-mcp-gateway`); **Stage 12 OPEN** — 7 gates G1-G7 in-flight (TENTATIVE scope; not yet ratified). A7 HYPOTHETICAL-VOC caveat inherited indefinitely: every customer-fit claim must say "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)".

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

### Before Stage 12 charter opens — IN FLIGHT (TENTATIVE)
- [ ] **G1** Stage 12 scope confirmation roundtable (Winston + Mary + Murat + Vera + advisor) — IN-FLIGHT
- [ ] **G2** VOC decision — three options: (a) inherit HYPOTHETICAL caveat indefinitely; (b) abbreviated VOC for Stage 12 questions (Teams vs Slack adoption, Entra/Okta/Auth0 distribution); (c) full re-do
- [ ] **G3** Cut `stage-12.0-channel-adapters` branch from `stage-11.0-mcp-gateway @ e0aade3` (Path A continuation recommended)
- [ ] **G4** Executor split confirmation (E1 = channels + E2 = auth recommended)
- [ ] **G5** Stage 11.5 debt scheduling (5 items; pre-Stage-12 or parallel)
- [ ] **G6** Dispatch fresh executor — BLOCKED on G1+G3+G4
- [ ] **G7** Merge Stage 11 to main — recommend keep local-only through Stage 12

### Stage 12 RATIFIED when — TENTATIVE (gated on G1 roundtable outcome)
- [ ] E1 = Teams + Slack `ChannelAdapterPort` impls landed under `adapters/channels/{teams,slack}/`; CLI hardening optional (TENTATIVE per G1)
- [ ] E2 = OAuth 2.1 + OIDC (Entra/Okta/Auth0) replacing `policy.py` bearer MVP (TENTATIVE per G1)
- [ ] E2 = LiteLLM virtual keys replacing budget-cap MVP (TENTATIVE per G1)
- [ ] Cross-window dep honored: E1 BLOCKS on `[E2-H#2-COMPLETE]` for auth_claims wiring
- [ ] Frozen Port surfaces (GatewayPort + ChannelAdapterPort) — NO Stage 12 changes without REFREEZE-03 ceremony
- [ ] STAGE-11-DEBT-AUTH-01 + STAGE-11-DEBT-LITELLM-VKEY-01 close as Stage 12 E2 lands
- [ ] (uncertain — verify) MAC-T floor + no_waiver count for Stage 12 — TBD at G1

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

## Stage 12 — OPEN (TENTATIVE; 7 gates G1-G7 in flight)

Stage 12 is **OPEN — not yet ratified**. Scope is TENTATIVE pending G1 roundtable confirmation. All claims below carry TENTATIVE flag until G1 closes.

### Gates G1-G7

| Gate | Description | Status |
|---|---|---|
| **G1** | Stage 12 scope confirmation roundtable (Winston + Mary + Murat + Vera + advisor) | IN-FLIGHT |
| **G2** | VOC decision — (a) inherit HYPOTHETICAL caveat indefinitely; (b) abbreviated VOC for Stage 12 questions (Teams vs Slack adoption, Entra/Okta/Auth0 distribution); (c) full re-do | OPEN |
| **G3** | Cut `stage-12.0-channel-adapters` from `stage-11.0-mcp-gateway @ e0aade3` (Path A continuation recommended; branch does NOT yet exist) | OPEN |
| **G4** | Executor split confirmation — E1 = channels + E2 = auth recommended | OPEN |
| **G5** | Stage 11.5 debt scheduling (5 items; pre-Stage-12 or parallel) | OPEN |
| **G6** | Dispatch fresh executor — BLOCKED on G1+G3+G4 | BLOCKED |
| **G7** | Merge Stage 11 to main — recommend keep local-only through Stage 12 | OPEN |

### TENTATIVE scope (gated on G1)

- **E1 (channels):** Teams + Slack `ChannelAdapterPort` impls under `adapters/channels/{teams,slack}/`; CLI hardening optional
- **E2 (auth):** OAuth 2.1 + OIDC (Entra/Okta/Auth0) replacing `policy.py` bearer MVP + LiteLLM virtual keys replacing budget-cap MVP
- **Cross-window dep:** E1 BLOCKS on `[E2-H#2-COMPLETE]` for auth_claims wiring
- **Frozen Port surfaces:** GatewayPort + ChannelAdapterPort — NO Stage 12 changes without REFREEZE-03 ceremony
- **4 handover files drafted** (gitignored): `docs/stage-12-*.md`

### Stage 11 RATIFIED inheritance

- HYPOTHETICAL-VOC caveat inherited indefinitely (A7 closed via override 2026-05-24)
- STAGE-11-DEBT-AUTH-01 + STAGE-11-DEBT-LITELLM-VKEY-01 are Stage 12 E2 candidate scope — they'd close as Stage 12 E2 lands

---

## Debt Tiers Post-Stage-11

### Stage 11.5 — pre-Stage-12 or parallel (5 items)
- JSONRPC-FIXTURE-REGEN
- RUFF-CLEANUP
- DIAL-LIVE-SMOKE
- SESSION-ID-WIDTH
- WAL-CONCURRENCY

### Stage 11.x — deferred features (6 items)
- **STAGE-11-DEBT-AUTH-01** — OAuth 2.1 + OIDC (candidate Stage 12 E2 scope)
- **STAGE-11-DEBT-LITELLM-VKEY-01** — LiteLLM virtual keys (candidate Stage 12 E2 scope)
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
| Stage 11.5 debt (5 items) | ~0.5–1 session (pre-Stage-12 or parallel) |
| Stage 12 — G1 roundtable + scope lock | TBD (unknown until G1 closes) |
| Stage 12 — E1 channels (Teams + Slack) + E2 auth (OAuth/OIDC + LiteLLM vkeys) | (uncertain — verify; TENTATIVE per G1) |
| Stage 12 — demo packaging + Champion onboarding | TBD per G1 |
| **Total to POV-ready (post-Stage-12)** | unknown until G1 |
| Post-Stage-12 (UI rewire, learning ports) | deferred |

---

## Quick Reference: What the Next Executor Needs

**For Stage 12 entry (next ratification work; G1 in flight):**
- Working branch: `stage-11.0-mcp-gateway @ e0aade3` (Path A local-only; NOT pushed to origin)
- `local main = origin/main = f181a7e` (Stage 10 RATIFIED; in sync via A7 override push 2026-05-24)
- Stage 11 RATIFIED 2026-05-26 — close memo at branch tip `e0aade3`
- **G1 roundtable IN-FLIGHT** — Winston + Mary + Murat + Vera + advisor confirming Stage 12 scope (TENTATIVE: E1 channels + E2 auth)
- **G2 VOC decision OPEN** — 3 options: (a) inherit HYPOTHETICAL caveat; (b) abbreviated VOC; (c) full re-do
- **G3 OPEN** — cut `stage-12.0-channel-adapters` from `e0aade3` once G1+G4 close
- 4 Stage 12 handover files drafted (gitignored): `docs/stage-12-*.md`
- HYPOTHETICAL-VOC caveat inherited indefinitely: append "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)" to every customer-fit claim
- Frozen Port surfaces (GatewayPort + ChannelAdapterPort) — NO Stage 12 changes without REFREEZE-03 ceremony
- Halt discipline per `feedback_preload_first_gating`; memory writes gated per `feedback_memory_authorization`

---

## Design Work Remaining (Phase 3+)

- **Factory shell cycle** — next per-surface cycle (S-1..S-4 analogue for Factory product shell); opens at team-lead discretion (after a break per 2026-05-13 disposition)
- **Subsequent shells** — Shield, Pipeline, Ops (per parent brief §4.3)
- **v1.1 substrate amendment cycle** — gates on ≥3 surfaces from 7 P3-* candidates; no schedule yet
- **R3 dark-canonical re-disposition** — required before any production Studio deploy (F-3 thin-slice deviation must not extend to production)
- **v1.1 brand-mark amendments** — 3 candidates from brand-mark cycle: P-BM-1 (master glyph slot spec), P-BM-2 (archive path-of-record corrigendum), P-BM-3 (kickoff-template embedded-repo seam clarification)
