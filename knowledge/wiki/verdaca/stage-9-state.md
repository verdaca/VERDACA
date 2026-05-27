# Stage 9 — Ports-and-Adapters State

**Compiled:** 2026-05-08 → **Updated:** 2026-05-26 (Stage 11 RATIFIED + Stage 12 OPEN) | **Source:** session handoffs 2026-04-12 → 2026-05-13 + `docs/stage-*-handover.md` 2026-05-16 → 2026-05-22 + in-session VOC synthesis 2026-05-24 + Stage 11 handoffs 2026-05-25 → 2026-05-26
**Working-branch HEAD (Stage 11 ratification authority):** `e0aade3` on `stage-11.0-mcp-gateway` (close memo commit); substantive H#8 V2 close at `1adbecb`; 20 commits total from `a11aa67` base (19 substantive + 1 close memo). **Branch is LOCAL-ONLY (Path A — never pushed to origin).** | **origin/main HEAD:** `f181a7e` (Stage 10 A7 team-lead override close 2026-05-24); local now diverged via Path A — push gated through Stage 12 close per `feedback_memory_authorization` adjacent risk-action discipline.
**Branch:** `stage-11.0-mcp-gateway` (Path A local-only; base = Stage-10 close `f181a7e` on origin/main; never merged to main pending Stage 12 close)

---

## Architecture Binding (Never Re-Litigate)

- **`ports-architecture.md` v0.2 POST-ELICITATION** (5 stacked corrigenda: v0.3/v0.4/v0.5/v0.6/v0.7 — cite as `v0.2 §X ADR-9.2-VX`)
- **`test-strategy.md` v0.2** — 85 MAC-Ts across 8 seams; 25-entry no_waiver allow-list (Stage 9 sublist binding cardinality 9 after 9.9 promotion; MAC list locked at 16)
- **ADR-9.2-V1:** Memory dual-adapter — Mem0 primary + Letta substitute, both built
- **ADR-9.2-V6 v0.7:** CompactionPort substrate re-anchor Forge → LLMLingua (9.4.6 A.1 `127f43c`)
- **ADR-9.1.2-4 v0.2.6:** CompactionPort contract — `StrategyDowngrade` removed; downgrade-as-return via `CompactionResult.strategy_applied`; `compute_determinism_hash()` content-derived shared constructor
- **Path convention:** `adapters/{name}/src/praxis/adapters/{name}/` (NOT `src/verdaca/adapters/`)
- **uv workspace:** 13 active members at 9.4.6 close + 9.6 registration audit — ports, tests, kernel/{compression,mac,memory,pi-mono/src,runtime,studio}, adapters/{beads,tonl,mem0,letta,pi_mono_native,litellm,in_tree_compaction_stub,llmlingua}; `shell/` deferred (pytest-asyncio conflict). 9.6 audit closed `F-9.9-CONTRACT-COLLECTION-UNRUNNABLE-01` via `tests/pyproject.toml` `[tool.uv.sources]` fixes for the 6 adapter members previously unregistered.
- **`_bmad-output/` and `docs/` are gitignored** (`.gitignore:29`; `effa9ad` 2026-05-15 chore commit untracked `docs/`) — commit bodies + close-commit messages are canonical authority, not local sandbox files
- **`praxis.__path__`:** expanded namespace package (pi_mono_native + litellm at 9.4.4/9.4.5; in_tree_compaction_stub + llmlingua at 9.4.6); all `praxis/__init__.py` markers deleted at C.2 `3fe343f`, residual 12 namespace markers cleaned at 9.4.7 `c466049`; legacy `_bmad-output/praxis/` tree archived to `_bmad-output/planning-artifacts/Verdaca/_archive/`
- **`ports/` now includes:** `memory.py`, `serialization.py`, `versioned_state.py`, `cost_meter.py`, `llm_proxy.py`, `compaction.py` (9.4.6 A.2 `72b7beb` + v0.2.6 corrigendum at B.1-W1 `e98a25b`), `common.py` (Message sibling-add at 9.4.5 A.2), `gateway.py` + `gateway_dto.py` + `gateway_errors.py` (Stage 11 — H#1.5 + REFREEZE-01 `9609c29`/`121670a` + REFREEZE-02 `af5d4f4`/`14a31f8`; FROZEN_FIELD_ALLOWLIST invariant preserved across both ceremonies)
- **Stage 11 additions (RATIFIED 2026-05-26 at `e0aade3`):** new kernel module `kernel/gateway/` (port.py, models.py, service.py = `VerdacaGatewayService`, execution.py, policy.py MVP — bearer-token + user-allow-list + per-user-budget + safety); new adapter `adapters/mcp_server/` (FastMCP-backed inbound — server.py, http.py, stdio.py, tools.py, resources.py, prompts.py, transport.py); adapter-local Protocol `MCPTransportPort` (NOT in `praxis.ports` layer); new infrastructure: WAL idempotency store + AsyncSessionIndex wrapper. **Canonical import path:** `praxis.ports.gateway` ONLY (Winston #2 corrigendum) — no re-exports through `kernel.gateway`.
- **Stage 10 additions (carried forward):** `kernel/session_index/` module (port.py = SessionIndexPort + SkillTelemetryPort Protocols co-located with their kernel module; models.py; sqlite_store.py; schema/) — note: Stage 10 broke Stage-9 convention of consolidating Protocol definitions in `ports/`; SessionIndexPort lives in `kernel/session_index/`, NOT in `ports/`.
- **HARD constraint extended (Stage 11):** `\bstrategic analysis\b` (2-word phrase, word-boundary grep) — zero hits across tools/server/resources/prompts (advisor-disposed at F-11-CLEO-10; "strategic decision" remains acceptable per dual-context citation discipline).
- **Stateless HTTP pinned (Stage 11):** `stateless_http=True` PINNED at contract level for `MCPTransportPort`.
- **Stage 10 additive corrigendum:** `SessionFilter.source_uri_prefix` added at `50fa909` (backward-compatible, default `None`) — landed during Stage 11 H#8 V2 to support gateway tenant-scoping.

---

## Sub-Stage Ratification Log

| Sub-stage | Status | Close commit | Key artifact |
|---|---|---|---|
| 9.1 | ✅ CLOSED | — | Base architecture |
| 9.2 | ✅ RATIFIED 2026-04-18 | — | `ports-architecture.md` v0.2; Forge G-1 gate (later retired at 9.4.6 A.1) |
| 9.3 | ✅ RATIFIED 2026-04-18 | — | `test-strategy.md` v0.2; 85 MAC-Ts; allow-list baseline |
| 9.4.1 Beads | ✅ CLOSED 2026-04-28 | — | `adapters/beads/` greenfield in-tree; 264 LOC; 10/10 M-T-VS-* GREEN |
| 9.4.2 TONL | ⏸ DEFERRED-WORK | `5f34ae7` bootstrap; `1ea7ac6` MAC-Ts | 12 M-T-SER-* catalog; remained out of Stage-9-close scope |
| 9.4.3 Memory | ✅ RATIFIED 2026-05-07 | `1a42896` | Mem0 + Letta adapters; 18 MAC-Ts; F-9.4.3-MEM-DTO-01 cleared |
| 9.4.4 Pi-Mono | ✅ RATIFIED 2026-05-08 | `eccc307` (close); B.2 `3cd6c86` | `ports/cost_meter.py` (7 DTOs); `adapters/pi_mono_native/`; 8 M-T-COST-*; ADR-9.2-V4 |
| 9.4.5 LLM Proxy | ✅ RATIFIED 2026-05-12 | `5b7019f` (close); B.2 `e9ea948` | `ports/llm_proxy.py` (4 DTOs + Message sibling + 2 errors); `adapters/litellm/`; 7 M-T-LLM-*; ADR-9.2-V5 v0.6; H2-falsification — Docker sidecar retired; LiteLLM sole substrate |
| 9.4.6 Compaction | ✅ RATIFIED 2026-05-17 | `85bdea1` (#35 close); A.1 `127f43c`; A.2 `72b7beb`; B.1-W1 `e98a25b`; B.1-W2 `15d5a57`; B.1-W3 `2f46f57`; B.2 `9a5b1dc` | `ports/compaction.py` (3 DTOs + 3 errors); `adapters/in_tree_compaction_stub/` + `adapters/llmlingua/` (llmlingua==0.2.2, MIT, 5 files each); 14 M-T-COMP-*; substrate-truth probe PASS-DEGRADED; Phase 0 P0.1–P0.3 (`0fef796`, `f75ab7b`, `40dc556`) closed in parallel — Caveman + LLMJudge + LiteLLM all route through LLMProxyPort |
| 9.4.7 Namespace | ✅ CLOSED 2026-05-18 | `c466049` | Delete 12 residual `praxis` namespace markers; archive `_bmad-output/praxis/` → `_archive/`; Windows case-fold `.gitignore` audit (F9 closed); branch `stage-9.4.7-namespace-cleanup` |
| 9.4.8 FTS5 Index | ✅ CLOSED 2026-05-18 | `2b7cbf3` | `scripts/index-sessions.py` (~50 LOC, stdlib-only SQLite FTS5 indexer); `knowledge/sessions.db` (gitignored build artifact); `/verdaca-wiki-update --index` flag |
| 9.5 Arch Review | ✅ CLOSED 2026-05-19 | `e7bd77d` | F10 `praxis.kernel` package-shape asymmetry document-and-defer; F-9.4.7-RUNTIME-PATHWALK-01 fixed in 3 `kernel/runtime/` files (repo-root via `git rev-parse --show-toplevel` + assert sentinels) |
| 9.9 Test-Strategy | ✅ CLOSED 2026-05-19 | `ef401a2` | Stage-9 enforcer `tests/src/praxis/contract_tests/ports/test_no_waiver_inventory.py` (NEW); `STAGE9_NO_WAIVER_ALLOWLIST` frozenset 9 entries; sublist 6→9 (compaction bearers added); F11/F12/F13 coupled landing CLOSED; enforcer SKIPPED pending 9.6 workspace fix |
| 9.6 Supply-Chain | ✅ CLOSED 2026-05-19 | `3e26f48` (#40 CI close); merge into main `76eea26` | `uv.lock` SHA-pinned (mem0ai==1.0.11, letta-client==1.10.3, litellm==1.83.14, llmlingua==0.2.2); 4 adapter `version_pin.py` with hashes; `.github/{renovate.json, workflows/contract-tests.yml, workflows/audit.yml}`; `tests/pyproject.toml` registers 6 adapter members; runtime fixture `kernel/runtime/tests/runtime/fixtures/agent-manifest.csv`; 9.9 enforcer un-skipped + green; F-9.9-CONTRACT-COLLECTION-UNRUNNABLE-01 CLOSED; 22 CVE deferrals + 2 carry-forward |
| **Stage 9** | ✅ **RATIFIED 2026-05-20** | merge `76eea26` on origin/main; CI close `3e26f48` | Full Stage 9 ports-and-adapters production-grade rebuild complete; 9.4.2 TONL remains deferred-work (authorized separate launch) |
| **Stage 11** | ✅ **RATIFIED 2026-05-26** | close memo `e0aade3` on `stage-11.0-mcp-gateway` (Path A local-only); H#8 V2 substantive close `1adbecb`; H#7 buyer-language `1501454`; H#1.5 list_sessions freeze `14a31f8`; REFREEZE-02 substantive `af5d4f4`; REFREEZE-01 substantive `9609c29` (read API stamp `121670a`); base `a11aa67` (off Stage-10 close `f181a7e`) | Channel-Neutral MCP Gateway; GatewayPort + ChannelAdapterPort + ChannelContext (FROZEN_FIELD_ALLOWLIST); `kernel/gateway/` + `adapters/mcp_server/` (FastMCP); 5 tools + 5 resources + 1 prompt + 2 transports (stdio + Streamable HTTP); 38 MAC-Ts delta; 208 contract tests GREEN + 8 skipped (env-gated DIAL live + others); 8 Cleo findings closed at H#8 V2; 4 MVP ChannelKinds (CLI, TEAMS, SLACK, CLAUDE_DESKTOP — UI/WEB deferred); only Claude-Desktop ChannelAdapter ships LIVE; HYPOTHETICAL-VOC caveat inherited from A7 override |

⚠ Memory entry `[[project_verdaca_stage9_ratified]]` cites SHA `45e1fd8 #41`. That commit exists only on feature branches (`stage-9.4.7-namespace-cleanup`, `stage-9.6-cleo-supply-chain`, `stage-10.0-port-stubs`) and is a 9.6 corrigendum that did not merge into `origin/main`. The Stage-9 close on `origin/main` is `3e26f48` (#40 CI close) + `76eea26` (Stage 9 ratification merge). Memory SHA correction pending team-lead authorization.

⚠ **Stage 11 branch is LOCAL-ONLY (Path A).** Branch `stage-11.0-mcp-gateway` has never been pushed to `origin`; `origin/main` remains at `f181a7e`. Merge to main is gated as Stage 12 G7 and is recommended to remain local-only through Stage 12 close. The 20-commit Stage 11 chain (`a11aa67` → `e0aade3`) is the sole ratification authority.

---

## Active No-Waiver Allow-List Entries (Stage 9 sublist, #17–#25)

Entries #1–#16 inherited from Stage 5.2 (see `test-strategy.md v0.2 §6.1`). Stage 9 sublist binding cardinality at Stage-9 RATIFIED is **9 entries**.

| # | MAC-T ID | Reason |
|---|---|---|
| 17 | M-T-MEM-PROMO-01 | Live-server promotion semantic |
| 18 | M-T-MEM-PROMO-02 | Live-server promotion semantic |
| 19 | M-T-MEM-PROMO-03 | Live-server promotion semantic |
| 20 | M-T-MEM-PROMO-04 | Live-server promotion semantic |
| 21 | M-T-SER-EVO-01 | TONL evolution spec (skeleton, pytest.skip) |
| 22 | M-T-SER-FUZZ-01 | TONL fuzz spec (skeleton, pytest.skip) |
| 23 | M-T-COMP-_lossless_overflow | Compaction `TokenBudgetUnreachable` bearer |
| 24 | M-T-COMP-_preserved_span_invariant | Compaction `PreservedSpanEvicted` bearer |
| 25 | M-T-COMP-_caller_raised_shape | Compaction `DeterminismViolation` bearer |

**Enforcer authority:** `tests/src/praxis/contract_tests/ports/test_no_waiver_inventory.py` (added 9.9 `ef401a2`, un-skipped at 9.6 `3e26f48`). `STAGE9_NO_WAIVER_ALLOWLIST` frozenset is character-identical to the table above; cardinality test asserts == 9.

**Rule:** No `@pytest.mark.no_waiver` added outside this list on agent initiative.

### Stage 11 sublist — 5 entries (strict equality)

Stage 11 sublist binding cardinality at Stage-11 RATIFIED is **5 entries** (strict equality meta-test).

| # | MAC-T ID | Reason |
|---|---|---|
| 26 | M-T-GW-JSONRPC-GOLDEN-REPLAY-01 | Wire-format conformance (JSON-RPC golden replay) |
| 27 | M-T-GW-STDIO-HANDSHAKE-01 | stdio `initialize`/`initialized` round-trip |
| 28 | M-T-GW-PORT-HANDSHAKE-01 | E2-imports-E1 compile-time check |
| 29 | M-T-GW-CHANNELCTX-PII-REDACTION-01 | PII never serializes to logs/envelopes |
| 30 | M-T-GW-SESSIONINDEX-BIND-01 | Gateway binds ratified Stage 10 `SessionIndexPort`, NOT a stub |

**Cross-stage totals:** Stage 9 sublist (9) + Stage 10 sublist (4 entries; indices uncertain — verify against Stage 10 close artifacts) + Stage 11 sublist (5) = **~18 across stages**; Stage 11 sublist cardinality is **strict equality at exactly 5** per Murat's MAC-T v0.2 ratification.

---

## Open Findings Carried Forward (to Stage 10 / 11 / debt)

| Finding | Severity | Status / Routed to |
|---|---|---|
| F-9.6-FINALIZE-CLEO-* (minor ledger) | Low | Stage 10 debt; non-blocking |
| F-10-EDGE-03 | Medium | Stage 10 §7 debt — SQLite WAL/pooling for async SessionIndex |
| F-10-EDGE-04 | Medium | Stage 10 §7 debt — max payload guard |
| F-10-COMPRESSION-MOCKER-DEP-01 | Low | Stage 10 §7 debt |
| F-10-MAC-CRLF-SNAPSHOT-01 | Low | Stage 10 §7 debt |
| F-9.4.6-LLMLINGUA-MAINTENANCE-STALENESS-1 | Low | 9.6 CVE-deferrals (originally mis-routed to 9.4.8; corrected 2026-05-18) |

**Stage 9 ratification-cycle findings CLOSED:** F9, **F10 (RESOLVED at d2b5670 — uniform `praxis.kernel` PEP-420; 6 marker `__init__.py` deleted; team-lead authorized 2026-05-21; supersedes the 9.5 "document-and-defer" disposition)**, F11, F12, F13, F-9.4.7-RUNTIME-PATHWALK-01, F-9.9-CONTRACT-COLLECTION-UNRUNNABLE-01, F-9.5-RUNTIME-MANIFEST-FIXTURE-01, F-9.9-MYPY-PORTS-PEP695-01, F-9.5-MYPY-SCORING-PREEXISTING-01, F-9.5-RUNTIME-LINT-DEBT-01.

**Stage 11 ratification-cycle findings CLOSED (8 at H#8 V2):**
- F-11-CLEO-01 (CRITICAL — SQLite leak) → resolved `50fa909`
- F-11-CLEO-02 (CRITICAL — cross-tenant fetch) → resolved `50fa909`
- F-11-CLEO-03 (CRITICAL — PII redaction test) → resolved `50fa909`
- F-11-CLEO-04 (fix-now WARNING) → resolved `50fa909`
- F-11-CLEO-06 (fix-now WARNING) → resolved `50fa909`
- F-11-CLEO-07 (fix-now WARNING) → resolved `50fa909`
- F-11-CLEO-08 (test rename) → resolved `50fa909`
- F-11-CLEO-12 (URI template parameter validation) → resolved `1adbecb`

### Stage 11.5 debt (5 LOW–MEDIUM items, pre-Stage-12)

| Finding | Severity | Status |
|---|---|---|
| JSONRPC-FIXTURE-REGEN | Low–Medium | Stage 11.5 debt |
| RUFF-CLEANUP | Low | Stage 11.5 debt |
| DIAL-LIVE-SMOKE | Medium | Stage 11.5 debt — env-gated live smoke |
| SESSION-ID-WIDTH | Low | Stage 11.5 debt |
| WAL-CONCURRENCY | Medium | Stage 11.5 debt — schedule pre-Stage-12 if DIAL/WAL surfaces blocking |

### Stage 11.x debt (6 HIGH–MEDIUM deferred features)

| Finding | Severity | Status |
|---|---|---|
| STAGE-11-DEBT-AUTH-01 | High | Stage 11.x — OAuth/OIDC replaces policy.py bearer-token MVP; candidate Stage 12 E2 scope (TENTATIVE) |
| STAGE-11-DEBT-LITELLM-VKEY-01 | High | Stage 11.x — LiteLLM virtual keys replace per-user-budget MVP; candidate Stage 12 E2 scope (TENTATIVE) |
| COMPOSE-ORDER | Medium | Stage 11.x |
| WAL-MID-EXEC-CRASH | Medium | Stage 11.x |
| CHANNEL-DETECTION | Medium | Stage 11.x |
| CITED-TRADEOFFS-STUB | Medium | Stage 11.x |

### Stage 7 cosmetic debt (Stage 11 — 6 INFO items)

F-11-CLEO-13, F-11-CLEO-14, F-11-CLEO-15, F-11-CLEO-16, F-11-CLEO-17, F-11-CLEO-18 — all INFO-severity cosmetic findings deferred to Stage 7 polish cycle.

---

## Stage 10 (started) — SessionIndex / Knowledge / Learning

**Decision:** 5-agent roundtable 2026-05-20 split post-9 work 4–1 for Stage 10 (data-plane) + Stage 11 (transport/edge). Strict serial: 9.6 → 10 → 11.

- Implementation COMPLETE at `d2b5670` #42 on branch `stage-10.0-port-stubs` (pre-roundtable reconcile at `50ce68e` F-10-RECONCILE-PRIOR-PORTS-01)
- **Stage 10 RATIFIED 2026-05-24** at merge `8ae4f87` (amendment chain: `3d576a9` VOC gate marker + `da47d67` close memo + Winston/Murat/Cleo audit cycle READY-WITH-AMENDMENTS/WARNINGS) — VOC PROVISIONAL via HYPOTHETICAL synthesis (GO-with-amendments LOW confidence; K1/K2/K3 each triggered once — zero margin); Path 1 lock by team-lead; 7-amendment ledger (VOC-10-A1..A7) with **A7 = hard Stage 11.1 charter precondition** (real-VOC re-confirmation per [[docs/stage-10-voc-gate.md]]); close memo at [[docs/stage-10-ratified-close-memo.md]]; memory entry write pending team-lead authorization per `feedback_memory_authorization`
- `SessionIndexPort` (`API_VERSION 1.0.0`) — index/search/list/get/artifact/telemetry; SQLite + FTS5 backing; semantic mode = no-op stub
- `SkillTelemetryPort` (renamed from SkillObserverPort) — `record_invocation` + `query(window)`; writes through index
- 10 DTOs (SessionExcerpt, SessionRecord, SessionFilter, ArtifactRef, TelemetryEvent, SkillOutcome, SkillUsage, SkillInvocationRecord, TimeWindow)
- CLI: `verdaca session list` + `verdaca session show <id>` (replay + cost surfaces)
- +4 no_waiver entries planned (9 → 13); MAC-T floor ≥18 (`M-T-SESSIONIDX-*` 11 + `M-T-SKILLTEL-*` 6 + `M-T-TELEMETRY-*` 1)
- VOC artifacts at `_bmad-output/planning-artifacts/Verdaca/voc-stage10/` (6 docs: ICP+target-list, call-script, scoring-rubric, synthesis-template, readout-template, README)
- **Stage 11-era additive corrigendum:** `SessionFilter.source_uri_prefix` added at `50fa909` during Stage 11 H#8 V2 (backward-compatible, default `None`) — supports gateway tenant-scoping; no SessionIndexPort surface re-freeze needed (additive-only).

## Stage 11 — Channel-Neutral MCP Gateway (RATIFIED 2026-05-26)

**Branch tip (ratification authority):** `e0aade3` on `stage-11.0-mcp-gateway` (Path A local-only; never pushed to origin). 20 commits total from base `a11aa67` (off Stage-10 close `f181a7e`). H#8 V2 substantive close at `1adbecb`.

**Ratification chain:** H#2 charter v0.5 (Winston 8 amendments) + H#3 MAC-T v0.2 (Murat 5 amendments) + H#7 buyer-language (Mary 3-tool + 2-title amendments) + H#8 V2 CODE-READY (Cleo all 8 findings resolved).

**2 REFREEZE ceremonies (FROZEN_FIELD_ALLOWLIST invariant preserved both times):**
- **REFREEZE-01** `9609c29` + read API stamp `121670a` — read API: get_session_summary / transcript / artifact
- **REFREEZE-02** `af5d4f4` + freeze SHA stamp `14a31f8` — list_sessions

**Ports added (FROZEN; no Stage 12 changes without REFREEZE-03):**
- `GatewayPort` — channel-neutral execution surface; composes LLMProxy + Memory + Cost + Compaction + SessionIndex
- `ChannelAdapterPort` — adapter-layer Protocol for channel wrappers
- **NOT in `praxis.ports` layer:** `MCPTransportPort` (adapter-local Protocol under `adapters/mcp_server/transport.py`)

**DTOs added:**
- `ChannelContext` (frozen dataclass with FROZEN_FIELD_ALLOWLIST), `AuthClaims`, `CallerKind`
- `ChannelKind` — **4 MVP values per Winston #1 corrigendum: CLI, TEAMS, SLACK, CLAUDE_DESKTOP** (UI / WEB deferred — corrects pre-Stage-11 wiki claim of "5 wrappers")
- `StartAnalysisRequest`, `AnalysisResult`, `SessionHandle`, `ArtifactRef`

**Errors added:** `GatewayCtxError`, `AuthClaimsAccessError`

**Kernel module added:** `kernel/gateway/` — port.py, models.py, service.py (`VerdacaGatewayService`), execution.py, policy.py MVP (bearer-token + user-allow-list + per-user-budget + safety)

**Adapter added:** `adapters/mcp_server/` — FastMCP-backed inbound (server.py, http.py, stdio.py, tools.py, resources.py, prompts.py, transport.py)

**Infrastructure added:** WAL idempotency store + AsyncSessionIndex wrapper

**MCP surface live (2026-05-26):** 5 tools (`verdaca_start_analysis`, `verdaca_estimate_cost`, `verdaca_get_result`, `verdaca_list_sessions`, `verdaca_get_artifact`) + 5 resources (`verdaca://methodology`, `verdaca://templates`, `verdaca://sessions/{id}/result/summary` + `/transcript` + `/artifacts/{id}`) + 1 prompt + 2 transports (stdio + Streamable HTTP, `stateless_http=True` PINNED)

**Channel live status:** Only **Claude-Desktop ChannelAdapter** ships LIVE in Stage 11. Teams + Slack + CLI deferred to Stage 12 (E1 candidate scope — TENTATIVE).

**Contract tests:** 38 MAC-Ts delta (Stage 11); 208 contract tests GREEN + 8 skipped (env-gated DIAL live + others).

**Canonical import path (Winston #2 corrigendum):** `praxis.ports.gateway` ONLY — no re-exports through `kernel.gateway`.

**HARD constraint extended:** `\bstrategic analysis\b` (2-word phrase, word-boundary grep) — zero hits across tools / server / resources / prompts (advisor-disposed at F-11-CLEO-10; "strategic decision" acceptable per dual-context citation discipline).

**Inherited caveat:** HYPOTHETICAL-VOC (Stage 6.0.1 / A7 team-lead override 2026-05-24 at `f181a7e`) — every Stage 11 customer-fit claim carries: "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)".

**Reference snapshot:** `tests/reference/spike-mcp-server-snapshot-d93f71a/` — CAI spike, frozen reference, non-importable.

## Stage 12 OPEN — TENTATIVE charter pending roundtable ratification

**Status:** OPEN — Stage 12 scope is **TENTATIVE** and **NOT yet ratified**. Charter pending roundtable confirmation (G1). Do not cite Stage 12 scope as binding.

**7 gates (G1–G7):**

| Gate | Description | Status |
|---|---|---|
| G1 | Stage 12 scope confirmation roundtable (Winston + Mary + Murat + Vera + advisor) | OPEN — in-flight via `/bmad-party-mode` |
| G2 | VOC question — HYPOTHETICAL caveat inheritance vs abbreviated VOC vs full re-do | OPEN |
| G3 | Cut `stage-12.0-channel-adapters` from `stage-11.0-mcp-gateway @ e0aade3` (Path A continuation recommended) | OPEN |
| G4 | Executor split (E1 = channels + E2 = auth recommended; concurrent 2-window pattern per `feedback_concurrent_executor_orchestration`) | OPEN |
| G5 | Stage 11.5 debt scheduling (5 items; recommend post-Stage-12 unless DIAL/WAL surfaces blocking) | OPEN |
| G6 | Dispatch fresh executor — blocked on G1 + G3 + G4 | OPEN (blocked) |
| G7 | Merge Stage 11 → main — recommend keep local-only through Stage 12 close | OPEN |

**TENTATIVE scope (NOT binding until G1 ratifies):**
- **E1 (TENTATIVE):** Teams + Slack `ChannelAdapterPort` impls under `adapters/channels/{teams,slack}/` (CLI hardening optional). Closes the 3 deferred ChannelKinds (TEAMS, SLACK, CLI) from Stage 11 Winston #1 corrigendum.
- **E2 (TENTATIVE):** OAuth 2.1 + OIDC (Entra / Okta / Auth0) replacing `policy.py` bearer-token MVP + LiteLLM virtual keys replacing per-user budget-cap MVP. Closes STAGE-11-DEBT-AUTH-01 + STAGE-11-DEBT-LITELLM-VKEY-01.
- **Cross-window dependency (TENTATIVE):** E1 BLOCKS on `[E2-H#2-COMPLETE]` for `auth_claims` wiring.

**Inherited caveat:** HYPOTHETICAL-VOC (Stage 6.0.1 / A7 team-lead override 2026-05-24 at `f181a7e`) — every Stage 12 customer-fit claim must carry: "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)".

**REFREEZE-03 ceremony required:** Any Stage 12 change to GatewayPort / ChannelAdapterPort / ChannelContext / FROZEN_FIELD_ALLOWLIST requires a REFREEZE-03 ceremony (mirroring REFREEZE-01 / REFREEZE-02 from Stage 11).

---

## Design Work — Phase 3 Studio Shell UI

**Status:** Phase 3 / S-1 thin-slice CLOSED 2026-05-13.

- **Cycle:** 4 HTML/CSS mocks (S-1 launcher, S-2 deliberation, S-3 output, S-4 audit trail) against substrate v1.0
- **Mode:** light-canonical (F-3 bounded thin-slice deviation; R3 dark-canonical preserved as substrate rule; production-deploy must re-disposition)
- **Deploy:** PD-S1-DEPLOY = C — local mocks only; no production deploy in Phase 3
- **Artifacts:** workshop-binding at `_bmad-output/implementation-artifacts/verdaca/phase3-studio-shell-ui/` (gitignored per `effa9ad`)
- **Sophia commission:** 20 strings authored + applied; R5/R8 PASS; independent-seam-verification
- **G-1..G-5 gates:** all GREEN at HP-S1-5 close
- **7 v1.1 substrate amendment candidates** (P3-1..P3-7): all DEFERRED to v1.1 cycle
- **Production:** verdaca.com LIVE since 2026-05-11 (Phase 2 landing + docs; Cloudflare Pages + Spaceship + Formspree)
- **Next:** Factory shell cycle — opens at team-lead discretion

## Design Work — Brand-Mark Cycle (closed 2026-05-16)

- **Deliverables:** master glyph (a) Baseline-iter + auxiliary (c) Verdict-dial; wordmark Path A (text-element) + Path B (outlined-paths, JetBrains Mono dependency eliminated); horizontal lockup 360×80
- **Favicon refresh:** `9d145ca` deployed to inner `_deploy/verdaca-prod/`; F-H1-3 color drift `#7C2229` → `#6B1F25` resolved
- **3 v1.1 candidates carried forward:** P-BM-1 (master brand-glyph slot spec), P-BM-2 (substrate path-of-record corrigendum), P-BM-3 (kickoff-template embedded-repo seam clarification)
- **Workshop-binding:** `.venv/`, `render-pngs.py`, `outline-wordmark.py`, direction-sketches/ — all gitignored

---

## Binding Constraints Active

- `feedback_no_waiver_discipline` — no allow-list additions on agent initiative
- `feedback_memory_authorization` — no memory writes without explicit team-lead go
- `feedback_corrigendum_paired_sweep` — corrigendum sweeps ports + test-strategy + pipeline
- `feedback_preload_first_gating` — structured preload report required before any implementation
- `feedback_provenance_pin` — close memos require §provenance table
- `feedback_session_surface_audit` — declare session ID/model/JSONL/working-dir at preload
- `feedback_advisor_executor_model_effort` — advisor = Opus 4.7 1M max; executor effort advisor-set
- `feedback_hard_constraint_word_boundary` — UPDATED 2026-05-13: dual-context citation discipline (R8-binding docs cite by clause-ordinal; R8-non-binding cite by token-name)
- `feedback_go_with_amendments_tracked` — UPDATED 2026-05-13: executor surfaces compositional extensions BEFORE applying, even when substrate-conformant
- `feedback_concurrent_executor_orchestration` — load-bearing through Pair-1 (9.4.7‖9.4.8) and Pair-2 (9.5‖9.9); 2-window hard cap; halt-class disjointness verification at dispatch; path-scoped `git commit <pathspec>` at H#4; per-executor git worktree isolation (post F-9.4.6-B.1-W3-COMMIT-CONTAM-01 lesson)
- `feedback_preload_tracking_status_verification` — re-confirmed at 9.4.6, 9.4.7/9.4.8, 9.6 — verify cited SHAs / paths / tracking status at preload (gitignored docs/, sessions.db, etc.)
- `feedback_handover_template_discipline` — verify paths / §-refs / SHAs at H#1; surface drift as F-{stage}-HANDOVER-*
- `feedback_preload_api_surface_verification` — substrate-truth probes (9.4.6 LLMLingua PASS-DEGRADED precedent); Stage-11 FastMCP probes BLOCKING before charter
- **REFREEZE ceremony discipline (Stage 11 precedent, binding through Stage 12):** Any change to a FROZEN Port surface (GatewayPort, ChannelAdapterPort, ChannelContext, FROZEN_FIELD_ALLOWLIST) requires a REFREEZE-{N} ceremony (substantive commit + freeze SHA stamp commit, FROZEN_FIELD_ALLOWLIST invariant preserved). Stage 11 set this precedent with REFREEZE-01 (read API `9609c29`/`121670a`) and REFREEZE-02 (list_sessions `af5d4f4`/`14a31f8`). Stage 12 inherits: REFREEZE-03 required for any Port surface changes.
- **HYPOTHETICAL-VOC caveat inheritance (binding through Stage 12):** Every customer-fit claim in Stage 11 close memos AND Stage 12 work must carry the inherited caveat string: "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)" — inherited from A7 team-lead override on Stage 10 close `f181a7e`. Caveat carries forward until a real-Champion VOC pass replaces the HYPOTHETICAL synthesis substrate.
