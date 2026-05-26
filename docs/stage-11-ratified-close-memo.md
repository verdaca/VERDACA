# Stage 11 — RATIFIED Close Memo

**Compiled:** 2026-05-26
**Branch:** `stage-11.0-mcp-gateway`
**Stage 11 scope:** Channel-Neutral MCP Gateway (transport/edge)
**Verdict:** **RATIFIED** — full E1 + E2 cycle complete; Cleo H#8 V2 CODE-READY at branch tip `1adbecb`
**Caveat:** A7 closed via team-lead override 2026-05-24 (docs/stage-10-ratified-close-memo.md §9); HYPOTHETICAL VOC substrate inherited per Stage 6.0.1 precedent — see §4 below

---

## §1 — What Was Ratified

Stage 11 ships the **channel-neutral MCP gateway** layer that Stage 12+ will compose into Teams/Copilot/UI surfaces. The architecture lock per master §1: MCP-as-main-channel (`stateless_http=True` PINNED); 4 MVP channel adapters (Teams/Slack/CLI/Claude-Desktop) per Winston #1 ChannelKind corrigendum. Two workspace packages + one Stage 10 additive corrigendum:

| Element | Locator | Provenance |
|---|---|---|
| `GatewayPort` Protocol (read API extended via REFREEZE-01 + 02) | `ports/src/praxis/ports/gateway.py` | H#1.5 `1fc37c2`; REFREEZE-01 `9609c29`; REFREEZE-02 `af5d4f4` |
| `ChannelAdapterPort` Protocol | same | H#1.5 frozen |
| `ChannelContext` + `AuthClaims` + DTOs + `FROZEN_FIELD_ALLOWLIST` | `ports/src/praxis/ports/gateway_dto.py` | H#1.5; ChannelKind corrigendum per Winston #1 at `3cfa121` |
| `VerdacaGatewayService` composing LLMProxy + Memory + Cost + Compaction + Stage 10 SessionIndex | `kernel/gateway/src/praxis/kernel/gateway/service.py` | H#2.3 `b3c7138`; REFREEZE-01/02 read API impl; H#8 hardening at `50fa909` |
| WAL idempotency store + AsyncSessionIndex wrapper | `kernel/gateway/.../wal.py` | H#2.3 + `contextlib.closing` fix at H#8 `50fa909` |
| Policy MVP (bearer token + user-id allow-list + budget cap + safety) | `kernel/gateway/.../policy.py` | H#2.4 `96532f0`; startup health check at H#8 `50fa909` |
| DIAL LiteLLM binding (azure/gpt-4o/api_base_overrides/api_version_overrides) | `kernel/gateway/.../service.py` + LiteLLM adapter | H#3 `0ecc926` |
| Inbound MCP server (FastMCP + 5 tools + 5 resources + 1 prompt + 2 transports) | `adapters/mcp_server/` | E2 surfaces 1-5 (`957faa8` → `1adbecb`) |
| Adapter-local `MCPTransportPort` Protocol | `adapters/mcp_server/.../transport.py` | per Winston #4 — NOT a port-layer Protocol |
| CAI spike snapshot (frozen reference for line-for-line ports) | `tests/reference/spike-mcp-server-snapshot-d93f71a/` | `a11aa67` per Round 2 Item 2 |
| Stage 10 `SessionFilter.source_uri_prefix` additive corrigendum | `kernel/session_index/.../models.py` + `sqlite_store.py` + `schema/001_initial.sql` index | H#8 `50fa909` — backward-compatible (default None) |
| 38 MAC-Ts + exactly 5 no_waiver allow-list (strict-equality meta-test) | `tests/src/praxis/contract_tests/ports/test_*.py` | H#3 v0.2 ratified by Murat; +3 REFREEZE-01 + 1 REFREEZE-02 + 4 surface-4 + Cleo additions |

**5 no_waiver allow-list (Stage 11 delta — exact equality, ratified by Murat at H#3 v0.2):**
- `M-T-GW-JSONRPC-GOLDEN-REPLAY-01`
- `M-T-GW-STDIO-HANDSHAKE-01`
- `M-T-GW-PORT-HANDSHAKE-01`
- `M-T-GW-CHANNELCTX-PII-REDACTION-01`
- `M-T-GW-SESSIONINDEX-BIND-01`

## §2 — Provenance

| Field | Value |
|---|---|
| Branch | `stage-11.0-mcp-gateway` |
| Branch base | `f181a7e` (Stage 10 A7-override close on main) |
| Branch tip | `1adbecb` |
| Commits from `a11aa67` (snapshot-landing first commit) | 19 |
| Stage 11 RATIFIED date | 2026-05-26 |
| Ratification authority | Team-lead (Andrey) — H#8 V2 Cleo CODE-READY 2026-05-26 |
| Phase 1 prerequisites (serial; single executor) | H#A7 (closed via override 2026-05-24) → H#1 substrate probes (`0d01be4`) → H#1.5 Port-freeze (`1fc37c2` + `5dc9c03`) → H#2 charter v0.5 (Winston ratified) + ChannelKind corrigendum (`3cfa121`) → H#3 MAC-T catalog v0.2 (Murat ratified) |
| Phase 2 parallel windows | E1 (commit authority): `kernel/gateway/` composition + WAL + policy + DIAL; E2 (surfaces): `adapters/mcp_server/` 5 tools + 5 resources + 1 prompt + 2 transports |
| Refreeze ceremonies | REFREEZE-01 `9609c29` + `121670a` (read API: get_session_summary/transcript/artifact); REFREEZE-02 `af5d4f4` + `14a31f8` (list_sessions) |
| E2 surface commits landed by E1 | `957faa8` (Phase C skeleton) + `09994f7` (resources/prompts/bearer/JSONRPC) + `850b1dc` (post-REFREEZE-01 resources) + `1501454` (post-REFREEZE-02 tools + Mary H#7 amendments) + `1adbecb` (URI validation) |
| Phase 3 ratifications | H#7 Mary buyer-language RATIFIED-WITH-AMENDMENTS (3 tool descriptions + 2 titles); H#8 Cleo CODE-NOT-READY → micro-halt → H#8 V2 CODE-READY |
| origin/main HEAD at ratification | `f181a7e` (A7-override close pushed 2026-05-24); branch local-only; merge ceremony deferred to team-lead |

## §3 — Audit Cycle Outcomes

| Halt | Agent | Verdict | Outcome |
|---|---|---|---|
| H#2 charter v0.4→v0.5 | 🏗️ Winston (Architect) | RATIFIED-WITH-AMENDMENTS | 8 amendments applied (ChannelKind corrigendum; canonical praxis.ports import path; async SessionIndex via gateway-owned wrapper; MCPTransportPort adapter-local; idempotency authority gateway; §10 buyer-language MAC-T binding; §13 verifiable ratification criteria; §8 future-auth TODO ticket IDs) |
| H#3 MAC-T catalog v0.1→v0.2 | 🧪 Murat (Test Architect) | RATIFIED-WITH-AMENDMENTS | 5 amendments applied (WAL crash-replay binding; JSON-RPC error-frame replay; ChannelContext allowlist-drift runtime; DIAL live-routing nightly; 2 policy MAC-Ts). Composition-ordering amendment DEFERRED to Stage 11.x debt. |
| H#7 demo packaging + buyer-language | 📊 Mary (Business Analyst) | RATIFIED-WITH-AMENDMENTS | 3 tool description amendments (estimate_cost, get_result, get_artifact) + 2 title amendments (Get Recommendation, Get Document) applied. 90-second demo script authored. |
| H#8 V1 across-the-board review | 🧹 Cleo (Clean Code Reviewer) | CODE-NOT-READY | 3 CRITICAL (SQLite leak, cross-tenant fetch, PII redaction test) + 9 WARNINGs (4 fix-now + 4 debt-routed + 1 advisor-disposed) + 6 INFOs |
| H#8 V2 verification pass | 🧹 Cleo (Clean Code Reviewer) | **CODE-READY** | All 8 actionable findings VERIFIED-RESOLVED at `1adbecb`; no regressions; provenance check clean |

### Verified at H#8 V2 close
- Full ports contract suite: **208 passed, 8 skipped** (env-gated DIAL live + others)
- mypy strict clean: ports/src + kernel/gateway/src + kernel/session_index/src + adapters/mcp_server/src
- ruff clean on Stage 11 paths (pre-existing lint in older test files routed to STAGE-11-DEBT-RUFF-CLEANUP-01)
- HARD-constraint `\bstrategic analysis\b` grep: zero hits across `tools.py`, `server.py`, `resources.py`, `prompts.py`
- DIAL secret hygiene: `DIAL_API_KEY` appears only in env-gated test; never logged, never in fixtures, never in commit messages, never in `__repr__`
- Cross-window contamination check: NONE detected; every commit single-window per F-9.4.6-B.1-W3-COMMIT-CONTAM-01 discipline

## §4 — VOC Provenance + Caveat (inherits A7 override)

Stage 11 RATIFIES on the SAME HYPOTHETICAL synthesis substrate that triggered A7 at Stage 10 close (3 simulated Champion archetypes; K1/K2/K3 zero-margin; K4 not flagged). A7 was closed via team-lead override 2026-05-24 (`f181a7e`) per `docs/stage-10-voc-gate.md §"Real VOC Provenance — A7 CLOSED via Explicit Team-Lead Override"` + `docs/stage-10-ratified-close-memo.md §9`.

**Downstream citation discipline (binding per `feedback_go_with_amendments_tracked` + Stage 6.0.1 caveat pattern):** all Stage 11 results that trace back to VOC carry the caveat:

> "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)"

Inherited by: this close memo (above); `project_verdaca_stage11_ratified` memory description (§8); GTM/pitch material citing Stage 11 customer-fit; Stage 12+ work re-encountering K1-K4 risk material; external comms (sales decks, white papers, conference talks).

Stage 11 demo packaging at H#7 honored this constraint — Mary's 90-second demo script uses *qualifying questions* the buyer asks themselves (no "our customers say" testimonials).

## §5 — Forward-Routed Findings Ledger

### Stage 11.5 debt (small follow-ons before Stage 12)
| ID | Severity | Source | Routing |
|---|---|---|---|
| STAGE-11-DEBT-JSONRPC-FIXTURE-REGEN-01 | LOW | E2 H#7 | Regenerate JSON-RPC error frames from live spike build when @modelcontextprotocol/sdk install path is documented |
| STAGE-11-DEBT-RUFF-CLEANUP-01 | LOW | E1 H#1.5 | Resolve pre-existing ruff findings in older `tests/src/praxis/contract_tests/ports/*.py` not touched by Stage 11 |
| STAGE-11-DEBT-DIAL-LIVE-SMOKE-01 | MEDIUM | E1 H#3 | Run `M-T-DIAL-EXEC-LIVE-ROUTING-01` with real DIAL_API_KEY in nightly CI env when creds wire |
| STAGE-11-DEBT-SESSION-ID-WIDTH-01 | LOW | Cleo H#8 F-05 | Use full 64-hex-char digest for session_id (current 16-char = 64-bit collision risk) |
| STAGE-11-DEBT-WAL-CONCURRENCY-01 | MEDIUM | Cleo H#8 edge | No test creates concurrent aiosqlite connections; >1 process pointing at same SQLite file unverified |

### Stage 11.x debt (deferred features; future-stage scope)
| ID | Severity | Source | Routing |
|---|---|---|---|
| STAGE-11-DEBT-AUTH-01 | HIGH | Winston #8 / v0.5 §8 | OAuth/OIDC IdP integration (Entra/Okta/Auth0); `# TODO(STAGE-11-DEBT-AUTH-01)` annotated in policy.py |
| STAGE-11-DEBT-LITELLM-VKEY-01 | HIGH | Winston #8 / v0.5 §8 | LiteLLM virtual keys for budget + model allow-list enforcement; `# TODO(STAGE-11-DEBT-LITELLM-VKEY-01)` annotated |
| STAGE-11-DEBT-GATEWAY-COMPOSE-ORDER-01 | MEDIUM | Murat H#3 amendment 6 (deferred) | If composition ordering surfaces as contentious during Phase A or H#8 review, promote to `M-T-GATEWAY-COMPOSE-ORDER-01` |
| STAGE-11-DEBT-WAL-MID-EXEC-CRASH-01 | HIGH | Cleo H#8 F-08 | Real crash-replay (mid-execute crash with LLM cost burned) NOT covered by current test; current code WILL double-bill; needs WAL row state machine |
| STAGE-11-DEBT-CHANNEL-DETECTION-01 | MEDIUM | Cleo H#8 F-09 | tools.py hardcodes ChannelKind.CLAUDE_DESKTOP; per Winston #1 channel should derive from actual surface |
| STAGE-11-DEBT-CITED-TRADEOFFS-STUB-01 | MEDIUM | Cleo H#8 F-11 | service.py `_build_result` hardcodes cited_tradeoffs as trace markers; real LLM-response parsing deferred |

### Stage 7 debt (operator-disciplined code quality)
- F-11-CLEO-13 through -18 (6 INFO items): cosmetic timestamp ordering, WAL synchronous=NORMAL doc comment, litellm untyped import, ArtifactRef payload vocabulary, adapter standalone lockfile, duplicate API_VERSION constant

### Stage 11.x scope absorbs (forward features)
- Teams / Copilot native MCP manifests (per master §4.6 "do not chase Teams SDK v2 MCP convergence yet")
- Web UI rewire as gateway client
- WebSocket transport (deferred per v0.5 §4.3; ChannelKind enum doesn't carry it post-Winston #1)
- HTTP cold-start race contract (`M-T-GW-HTTP-COLDSTART-01` paranoia margin per Murat Round 2)

## §6 — Cycle-Resolved Findings

| ID | Source | Resolution |
|---|---|---|
| F-11-PRE-H2-OVER-ENG-01 | Pre-dispatch party-mode (party-mode 2026-05-24) | Trim accepted (KEEP frozen ChannelContext + AuthClaims + 3 contract tests; DROP @asynccontextmanager + 14-test ContextVar catalog + structural Option A + import-linter + TRANSPORT-CONTRACT-01); landed at H#1.5 §12.2 final shape |
| F-11-E1-HANDOVER-02 | E1 H#1 (import-linter wildcard syntax) | RESOLVED via master handover §4.0.PRE corrigendum (substituted `tests.reference.*` for wildcard-prefix syntax that import-linter 2.11+ rejects) |
| F-11-E1-RETROFIT-01 | E1 H#2.1 (test imported pre-Winston #2 namespace) | RESOLVED at `f8c638a` — test_gateway_port_contract.py retrofit to canonical `praxis.ports.gateway` source |
| F-11-E1-E2-DRIFT-1 | E2 H#4 (bearer NotImplementedError stub) | RESOLVED at `09994f7` (E2 surface-2 wired bearer to E1 policy) + `50fa909` (E1 policy_health_check landed) |
| F-11-E1-E2-DRIFT-2 | E2 H#5 (shared index hygiene during E1 in-progress edits) | RESOLVED at `957faa8` (E1 path-scoped surface landing) |
| F-11-E1-E2-DRIFT-3 | E2 H#8 micro-halt (stale view of E1 in-progress edits) | RESOLVED — stale-view false positive; advisor verification confirmed working tree clean post-50fa909 |
| F-11-E2-GATEWAY-READ-API-GAP-01 | E2 H#6.5 | RESOLVED via REFREEZE-01 (`9609c29`) + surface-3 (`850b1dc`) |
| F-11-E2-JSONRPC-FIXTURE-GENERATION-01 | E2 H#7 | ACCEPTED-AS-IS (static pinned fixtures sufficient for M-T-MCP-JSONRPC-ERROR-FRAME-01); forward-routed to STAGE-11-DEBT-JSONRPC-FIXTURE-REGEN-01 |
| F-11-PHASE3-TOOLS-IMPL-GAP-01 | Advisor pre-Mary | RESOLVED via REFREEZE-02 (`af5d4f4`) + surface-4 (`1501454`) |
| F-11-CLEO-01 / -02 / -03 (3 CRITICAL) | Cleo H#8 V1 | RESOLVED at `50fa909` — SQLite contextlib.closing wrap; Stage 10 SessionFilter additive corrigendum + SQL pushdown; _ImmutableClaims.__repr__ deliberate redaction + asdict/json PII test |
| F-11-CLEO-04 / -06 / -07 (3 fix-now WARNINGs) | Cleo H#8 V1 | RESOLVED at `50fa909` — bearer policy startup health check; exception class preserved in context_field; single datetime.now capture |
| F-11-CLEO-08 (test rename) | Cleo H#8 V1 | RESOLVED at `50fa909` — WAL test renamed to orphaned-in-progress recovery + binding comment routing mid-execute crash to debt ticket |
| F-11-CLEO-10 (HARD-constraint scope) | Cleo H#8 V1 | RESOLVED via advisor disposition — forbidden TOKEN is `"strategic analysis"` (2-word phrase) per Mary's Stage 10 original audit, NOT `\bstrategic\b` single word. `"strategic decision"` acceptable. No Mary consult needed. |
| F-11-CLEO-12 (URI template validation) | Cleo H#8 V1 | RESOLVED at `1adbecb` (E2 surface-5 — `_validate_id` regex + ToolError) |

## §7 — Stage 12+ Implications

Stage 11 RATIFIED unblocks:
- **Stage 12 channel adapter implementations** — Teams / Slack / CLI / Claude-Desktop adapters can now satisfy `ChannelAdapterPort` against the frozen `GatewayPort` surface
- **Stage 12.x auth integration** — STAGE-11-DEBT-AUTH-01 (OAuth/OIDC) + STAGE-11-DEBT-LITELLM-VKEY-01 (LiteLLM virtual keys) replace policy.py MVP
- **Stage 12.x WebSocket transport** — `MCPTransportPort` adapter-local Protocol can extend to add `serve_websocket()` without touching `praxis.ports`
- **Stage 12.x UI rewire** — Web UI becomes a `ChannelAdapterPort` consumer instead of direct kernel client
- **Stage 11.x debt cycle** — 6 deferred items above; team-lead schedules per priority

Stage 11 does NOT block:
- Stage 10.5 debt cycle (4 items from Stage 10 close memo §5; unrelated to MCP gateway)
- Stage 7 polish (Cleo H#8 INFOs + earlier WARNINGs)
- DIAL VPN-on live smoke (env-gated; runs when DIAL_API_KEY wires)

## §8 — Memory Entry + FF Strategy

### Memory entry (authorized by team-lead 2026-05-26)

Written to `~/.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/memory/project_verdaca_stage11_ratified.md`; MEMORY.md index updated.

### FF / Merge Strategy

**Path A confirmed by team-lead 2026-05-26: Local-only continuation.** `stage-11.0-mcp-gateway` stays local; Stage 12 work cuts a new branch from this tip OR piles on top. Defer push to origin until pre-sales / external demo requires deployable artifact. Aligns with team-lead's 2026-05-20 "local chain stays local indefinitely" directive (only override was A7 close push at `f181a7e` for VOC gate visibility on origin).

---

**Authority:** This memo is binding for Stage 11 ratification. Future modifications require team-lead authorization per `feedback_memory_authorization`.
