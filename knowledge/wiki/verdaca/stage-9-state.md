# Stage 9 — Ports-and-Adapters State

**Compiled:** 2026-05-08 → **Updated:** 2026-05-29 (Stage 13 RATIFIED + merged to main + Path A CLOSED + Stage 14 G1 RATIFIED) | **Source:** session handoffs + `docs/stage-*-handover.md` 2026-04-12 → 2026-05-28 + in-session VOC synthesis 2026-05-24 + Stage 12 close memo `docs/stage-12-ratified-close-memo.md` 2026-05-27 + Stage 13 close memo `docs/stage-13-ratified-close-memo.md` 2026-05-28 + 6-agent Stage 14 G1 roundtable 2026-05-28 (Winston+Vera+Amelia+Murat+John+Mary, 3 rounds, full alignment)
**Working-branch HEAD (Stage 14 entry):** `stage-14.0-buyer-contact-surface @ 620b4cb` (cut from `main @ 620b4cb`). **Stage 13 RATIFIED 2026-05-28** at `620b4cb` (14 commits from base `5306c8d`) — merged to main + annotated tag `stage-13.0-ratified` → `620b4cb` (pushed to origin). **Path A CLOSED 2026-05-28** via team-lead override of D13: Stages 11+12+13 chain pushed to origin (stage-11.0-mcp-gateway, stage-12.0-channel-adapters, stage-13.0-production-hardening); `local main = origin/main = 620b4cb` (in sync; advanced from `f181a7e` via fast-forward merge of Stage 13 chain).
**Branch:** `stage-12.0-channel-adapters` (Path A local-only; base = Stage-11 close `e0aade3`; never merged to main)

---

## Architecture Binding (Never Re-Litigate)

- **`ports-architecture.md` v0.2 POST-ELICITATION** (5 stacked corrigenda: v0.3/v0.4/v0.5/v0.6/v0.7 — cite as `v0.2 §X ADR-9.2-VX`)
- **`test-strategy.md` v0.2** — 85 MAC-Ts across 8 seams; 25-entry no_waiver allow-list (Stage 9 sublist binding cardinality 9 after 9.9 promotion; MAC list locked at 16)
- **ADR-9.2-V1:** Memory dual-adapter — Mem0 primary + Letta substitute, both built
- **ADR-9.2-V6 v0.7:** CompactionPort substrate re-anchor Forge → LLMLingua (9.4.6 A.1 `127f43c`)
- **ADR-9.1.2-4 v0.2.6:** CompactionPort contract — `StrategyDowngrade` removed; downgrade-as-return via `CompactionResult.strategy_applied`; `compute_determinism_hash()` content-derived shared constructor
- **Path convention:** `adapters/{name}/src/praxis/adapters/{name}/` (NOT `src/verdaca/adapters/`)
- **uv workspace:** 13 active members at 9.4.6 close + 9.6 registration audit — ports, tests, kernel/{compression,mac,memory,pi-mono/src,runtime,studio}, adapters/{beads,tonl,mem0,letta,pi_mono_native,litellm,in_tree_compaction_stub,llmlingua}; `shell/` deferred (pytest-asyncio conflict). 9.6 audit closed `F-9.9-CONTRACT-COLLECTION-UNRUNNABLE-01` via `tests/pyproject.toml` `[tool.uv.sources]` fixes for the 6 adapter members previously unregistered. **Stage 12 extended to 22 members** (19→22): adds `adapters/channels/teams/`, `adapters/channels/slack/`, `kernel/auth/`.
- **`_bmad-output/` and `docs/` are gitignored** (`.gitignore:29`; `effa9ad` 2026-05-15 chore commit untracked `docs/`) — commit bodies + close-commit messages are canonical authority, not local sandbox files
- **`praxis.__path__`:** expanded namespace package (pi_mono_native + litellm at 9.4.4/9.4.5; in_tree_compaction_stub + llmlingua at 9.4.6); all `praxis/__init__.py` markers deleted at C.2 `3fe343f`, residual 12 namespace markers cleaned at 9.4.7 `c466049`; legacy `_bmad-output/praxis/` tree archived to `_bmad-output/planning-artifacts/Verdaca/_archive/`
- **`ports/` now includes:** `memory.py`, `serialization.py`, `versioned_state.py`, `cost_meter.py`, `llm_proxy.py`, `compaction.py` (9.4.6 A.2 `72b7beb` + v0.2.6 corrigendum at B.1-W1 `e98a25b`), `common.py` (Message sibling-add at 9.4.5 A.2), `gateway.py` + `gateway_dto.py` + `gateway_errors.py` (Stage 11 — H#1.5 + REFREEZE-01 `9609c29`/`121670a` + REFREEZE-02 `af5d4f4`/`14a31f8`; FROZEN_FIELD_ALLOWLIST invariant preserved across both ceremonies) + `virtual_key.py` (Stage 12 — `VirtualKeySpec`, `VirtualKeyInfo`, `BudgetExhaustedError`; VirtualKeyPort)
- **Stage 12 additions (RATIFIED 2026-05-27 at `43f57ba`):** new kernel module `kernel/auth/` (claims.py, oidc.py — `JwksCache`, jwt.py — `JwtVerifier` + alg-pin, idp.py — `discover`, nonce.py — `NonceStore`); new adapters `adapters/channels/teams/` (HMAC-SHA256, replay window) + `adapters/channels/slack/` (X-Slack-Signature v0); `adapters/litellm/virtual_keys.py` (HTTP-client vkeys, no Python LiteLLM SDK); `kernel/gateway/policy.py` refactored to thin orchestrator consuming `kernel.auth` + VirtualKeyPort. AST gate: M-T-AUTH-KERNEL-NO-ADAPTER-IMPORT-01 — `kernel/auth/` must have NO adapter import.
- **Stage 11 additions (RATIFIED 2026-05-26 at `e0aade3`):** new kernel module `kernel/gateway/` (port.py, models.py, service.py = `VerdacaGatewayService`, execution.py, policy.py MVP — bearer-token + user-allow-list + per-user-budget + safety); new adapter `adapters/mcp_server/` (FastMCP-backed inbound — server.py, http.py, stdio.py, tools.py, resources.py, prompts.py, transport.py); adapter-local Protocol `MCPTransportPort` (NOT in `praxis.ports` layer); new infrastructure: WAL idempotency store + AsyncSessionIndex wrapper. **Canonical import path:** `praxis.ports.gateway` ONLY (Winston #2 corrigendum) — no re-exports through `kernel.gateway`.
- **Stage 10 additions (carried forward):** `kernel/session_index/` module (port.py = SessionIndexPort + SkillTelemetryPort Protocols co-located with their kernel module; models.py; sqlite_store.py; schema/) — note: Stage 10 broke Stage-9 convention of consolidating Protocol definitions in `ports/`; SessionIndexPort lives in `kernel/session_index/`, NOT in `ports/`.
- **HARD constraint extended (Stage 11):** `\bstrategic analysis\b` (2-word phrase, word-boundary grep) — zero hits across tools/server/resources/prompts (advisor-disposed at F-11-CLEO-10; "strategic decision" remains acceptable per dual-context citation discipline). **HARD constraint further extended (Stage 12 — Mary amendments):** `\bseamless\b` + `\benterprise-grade\b` (word-boundary, case-sensitive grep) — zero hits across source + tests at Stage 12 close. All three forbidden tokens carry forward to Stage 13.
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
| **Stage 12** | ✅ **RATIFIED 2026-05-27** | close at `43f57ba` on `stage-12.0-channel-adapters` (binding ratification anchor preserved); 29 commits from base `e0aade3`; H#8.V2 chain; Mary H#7 `4608a52`; **Path A status CLOSED 2026-05-28** — 3 hygiene tail commits `dc97e7a` + `9fe3057` + `5306c8d` post-RATIFIED for wiki sync + close memo tracking; branch pushed to origin 2026-05-28 | Teams + Slack `ChannelAdapterPort` (E1); `kernel/auth/` OIDC+JWKS+JWT+claims+nonce + VirtualKeyPort + LiteLLM HTTP-client vkeys (E2); `kernel/gateway/policy.py` thin-orchestrator refactor; uv 19→22; 281 tests / 9 no_waiver / 6 AST gates; Mary PASS-WITH-AMENDMENTS + Cleo FAIL→PASS post-V2; 5 findings → Stage 13; DIAL-LIVE-SMOKE RESOLVED; HYPOTHETICAL-VOC inherited |
| **Stage 13** | ✅ **RATIFIED 2026-05-28** | close at `620b4cb` on `stage-13.0-production-hardening` (14 commits from base `5306c8d`); E2 SHAs `4d45100`+`f1aa572`+`2e1d134`; E1 SHAs `2802754`+`8be62e0`+`54f9235`+`a354283`+`a3c589a`; V2 chain CRITICAL `e2ece6f` → HIGH `f91aad0` → MEDIUM `2776be0` → LOW `3fc11c7`; V3.A `1ce9539` (V1 C-1 binding criterion fully closed via unconditional enforce_budget); close memo `620b4cb` MERGED TO MAIN + tag `stage-13.0-ratified` → `620b4cb` pushed origin 2026-05-28 | Production hardening Option A; auth quartet invoked-in-execute (V2.A + V3.A) + composition root `kernel/gateway/composition.py` 11-param `build_gateway()` + OidcPolicy NEW class + extract_claims relocation + NonceStore SQLite separate file + BEGIN IMMEDIATE atomic + Teams/Slack post_result async + WebhookSigningKeyResolver hybrid dataclass + gateway session-id W-1 (32-hex/128-bit) + 6 AST gates A-F (Gate F close-memo tracking symmetry); **321 tests / 13 runtime no_waiver / 6 Stage 13 AST gates A-F / 19 total enforced markers**; 5/5 V1 Cleo CLOSED + 2/12 V3 CLOSED at V3.A + 10 V3 carry-forward Stage 14; Mary H#7 PASS (zero HARD-constraint hits); Stage 9-12 invariants ALL preserved; HYPOTHETICAL-VOC inherited (now compounds on merged main) |
| **Stage 14** | 🔲 **OPEN** (G1 RATIFIED 2026-05-28) | branch cut: `stage-14.0-buyer-contact-surface @ 620b4cb` (from main); 6-agent roundtable Winston+Vera+Amelia+Murat+John+Mary (3 rounds, full alignment) | Cycle = "Buyer Contact Surface via auditor gate" (NOT Option-A hardening); Phase 0 dual-track Week 1 (Track A engineering CVE close: JWKS-NOT-INTEGRATED + AUDIENCE bundled + R15-c TTL race + R15-d pin + vkey REQUIRED fail-closed + policy_health_check ‖ Track B GTM+auditor floor B-1..B-7 Mary-coordinated split with Cleo+Murat); two end-of-Week-1 hard gates (CVE PASS ∧ B-6 auditor floor attestation); Phase 1 Week 2-3 first Champion VOC + demo runbook + onboarding pipeline + Charter v0.2 11-param ratification; Phase 2 Week 4+ polish burndown; **canonical pin target 14/9/20** (+1 no_waiver `M-T-AUTH-JWKS-ROTATION-INVARIANT-01`, +3 AST gates A-S14/B-S14/C-S14); PROVISIONAL-SINGLE-SAMPLE caveat replaces HYPOTHETICAL-VOC after N=1 (full retire N≥3 per Murat); K1/K2/K3 pre-registration MANDATORY in close memo; auditor voice split Mary+Cleo+Murat; PARSE-ACTIVITY → Stage 14.5 event-gated named debt (Winston Round 3 yield); HARD-constraint adds `\brobust\b` + `\bproduction-ready\b` + `\bcomprehensive\b`; OUT: 4 WARNING + 3 LOW Cleo cosmetic + handover-template drift (3) + Mary docstring polish (3) + F-10-ARCH-AUDIT-02 |

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

### Stage 12 sublist — 9 entries (strict equality)

Stage 12 sublist binding cardinality at Stage-12 RATIFIED is **9 entries** (strict equality meta-test at `tests/src/praxis/contract_tests/test_stage12_no_waiver_count.py`).

| # | MAC-T ID | Reason |
|---|---|---|
| 31 | M-T-TEAMS-WEBHOOK-HMAC-TAMPERED-01 | Teams HMAC-SHA256 webhook signature tamper rejection (E1) |
| 32 | M-T-SLACK-WEBHOOK-SIGNING-TAMPERED-01 | Slack X-Slack-Signature v0 tamper rejection (E1) |
| 33 | M-T-TEAMS-CHANNEL-ADAPTER-PORT-CONTRACT-01 | Teams adapter ChannelAdapterPort contract (E1) |
| 34 | M-T-SLACK-CHANNEL-ADAPTER-PORT-CONTRACT-01 | Slack adapter ChannelAdapterPort contract (E1) |
| 35 | M-T-AUTH-JWT-ALG-PIN-01 | JWT algorithm pinning — rejects unexpected alg header (E2) |
| 36 | M-T-AUTH-NONCE-REPLAY-BLOCK-01 | Nonce replay blocked (E2) |
| 37 | M-T-AUTH-CLAIMS-SCHEMA-01 | AuthClaims schema validation (E2) |
| 38 | M-T-VKEY-BUDGET-EXHAUSTED-01 | VirtualKeyPort BudgetExhaustedError path (E2) |
| 39 | M-T-AUTH-KERNEL-NO-ADAPTER-IMPORT-01 | AST gate: kernel/auth has NO adapter import (E2) |

**Cross-stage totals (post-Stage-12):** Stage 9 (9) + Stage 10 (4; verify) + Stage 11 (5) + Stage 12 (9) = **~27 across stages**. Stage 12 sublist cardinality strict equality = 9.

### Stage 13 sublist — 4 entries (BINDING at Stage 13 RATIFIED 2026-05-28)

Stage 13 RATIFIED 2026-05-28 at `620b4cb` — 4 NEW no_waiver entries added (Stage 12 9 → Stage 13 13 strict-equality total at `tests/src/praxis/contract_tests/test_stage13_no_waiver_count.py`). Marker IDs:
- `M-T-GATEWAY-EXECUTE-AUTH-FIRST-01` (V2.A rename of original `M-T-AUTH-VERIFIER-WIRED-AT-COMPOSITION-01`; renamed at V2.D `3fc11c7` for V2.A rename regression closure)
- `M-T-AUTH-NONCE-PERSISTENCE-RESTART-01`
- `M-T-SESSION-ID-ENTROPY-FLOOR-01`
- `M-T-NO-BARE-EXCEPT-AUTH-CRYPTO-01`

### Stage 14 planned additions — 1 entry (PLANNED; not yet binding)

Stage 14 G1 ratified 2026-05-28 plans to add **1 new no_waiver entry** (Stage 13 13 → Stage 14 14 strict-equality total). Marker ID:
- `M-T-AUTH-JWKS-ROTATION-INVARIANT-01` (Murat lock: bundled commit ≠ bundled discipline; AUDIENCE-DOUBLE-DECODE bundled with JWKS in B1 but does NOT get a no_waiver marker — risk 5/10 < no_waiver floor 7)

Not binding until Stage 14 RATIFIED.

| # (planned) | MAC-T ID (planned) | Reason |
|---|---|---|
| 40 | M-T-AUTH-VERIFIER-WIRED-AT-COMPOSITION-01 | JwtVerifier injected at composition root (no None default) |
| 41 | M-T-AUTH-NONCE-PERSISTENCE-RESTART-01 | NonceStore persists across restarts (SQLite) |
| 42 | M-T-SESSION-ID-ENTROPY-FLOOR-01 | Session ID entropy floor ≥128 bits |
| 43 | M-T-NO-BARE-EXCEPT-AUTH-CRYPTO-01 | No bare-except in auth/crypto code paths |

---

## Open Findings Carried Forward (to Stage 10 / 11 / 12 / 13 / debt)

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

### Stage 11.5 debt — dispositions at Stage 12 close

| Finding | Severity | Stage 12 disposition |
|---|---|---|
| JSONRPC-FIXTURE-REGEN | Low–Medium | Carries to Stage 13 IN SCOPE |
| RUFF-CLEANUP | Low | Folded to CI baseline (Stage 12 close); scope OUT of Stage 13 |
| DIAL-LIVE-SMOKE | Medium | **RESOLVED** — Azure-style gpt-4o probe completed in Stage 12 |
| SESSION-ID-WIDTH | Low | Carries to Stage 13 IN SCOPE (entropy floor ≥128 bits per Cleo ranking) |
| WAL-CONCURRENCY | Medium | DEFERRED per Stage 13 R6 — separate SQLite file, no shared writers confirmed |

### Stage 11.x debt (6 HIGH–MEDIUM deferred features; 2 closed at Stage 12)

| Finding | Severity | Status |
|---|---|---|
| STAGE-11-DEBT-AUTH-01 | High | **CLOSED at Stage 12** — `kernel/auth/` (OIDC+JWKS+JWT+claims+nonce) shipped at Stage 12 E2; F-12-CLEO-C2 composition root wiring carries to Stage 13 |
| STAGE-11-DEBT-LITELLM-VKEY-01 | High | **CLOSED at Stage 12** — VirtualKeyPort + `adapters/litellm/virtual_keys.py` HTTP-client shipped at Stage 12 E2 |
| COMPOSE-ORDER | Medium | Stage 11.x |
| WAL-MID-EXEC-CRASH | Medium | Stage 11.x |
| CHANNEL-DETECTION | Medium | Stage 11.x |
| CITED-TRADEOFFS-STUB | Medium | Stage 11.x |

### Stage 12 carry-forward to Stage 13 (5 findings)

| Finding | Severity | Stage 13 disposition |
|---|---|---|
| F-12-CLEO-C2-COMPOSITION-PENDING-01 | CRITICAL | IN SCOPE Stage 13 — JwtVerifier injection at gateway startup (composition root wiring) |
| F-12-CLEO-M3-NONCE-RESTART-DEFER-01 | MEDIUM | IN SCOPE Stage 13 — NonceStore SQLite persistence + TTL; Redis re-evaluation gated to multi-host |
| F-12-CLEO-W2-SYNC-HTTPX-01 | LOW | IN SCOPE Stage 13 — TeamsAdapter + SlackAdapter `post_result` async migration |
| F-12-OIDC-LIVE-DEFERRED-01 | Champion-gated | OUT OF SCOPE Stage 13 — live IdP smoke deferred until Champion available |
| F-12-CLEO-M5-FALSE-POSITIVE-01 | Informational | OUT OF SCOPE Stage 13 — `GatewayPort.execute` is sync; Cleo finding acknowledged as false positive |

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

## Stage 12 — Channel Adapters + Auth Kernel (RATIFIED 2026-05-27)

**Branch tip (ratification authority):** `43f57ba` on `stage-12.0-channel-adapters` (Path A local-only; never pushed to origin). 29 commits from base `e0aade3` (Stage-11 close). Branch is LOCAL-ONLY.

**Ratification chain:** Phase 0 open (`015240d` + `4bc4cba`); H#1 substrate probes (`57fd348`); H#1.5 auth_claims surface freeze (`3257304` + `43036f4`); E2-H#2 VirtualKeyPort + `kernel/auth/` (`2c68f12`); E1 Teams/Slack adapters (`0a060dd` → `7a8e5ff`); E2 kernel/auth modules (`a398c91` → `bfd94c6`); E2-H#4 LiteLLM vkeys (`01654ff`); E2-H#5 policy.py orchestrator (`58fe467`); E1-H#4 D2 cross-window + meta-test (`355f516` + `0457944`); H#7 Mary amendments (`4608a52`); H#8.V2 Cleo CRITICAL (`c48d3ce`) → HIGH (`06bcb8a`) → MEDIUM (`16a147a`) → WARNING close (`43f57ba`).

**Scope shipped:**
- **E1:** Teams `ChannelAdapterPort` impl under `adapters/channels/teams/` (HMAC-SHA256 webhook signature, replay window) + Slack impl under `adapters/channels/slack/` (X-Slack-Signature v0). Teams + Slack now **LIVE** (was deferred in Stage 11). Claude-Desktop remains LIVE. CLI deferred to Stage 13 or later.
- **E2:** `kernel/auth/` — claims.py, oidc.py (`JwksCache`), jwt.py (`JwtVerifier` + alg-pin RS256/ES256/PS256), idp.py (`discover`), nonce.py (`NonceStore` in-memory); `ports/virtual_key.py` (`VirtualKeySpec`, `VirtualKeyInfo`, `BudgetExhaustedError`); `adapters/litellm/virtual_keys.py` (HTTP-client vkeys, no Python LiteLLM SDK). `kernel/gateway/policy.py` refactored to thin orchestrator consuming `kernel.auth` + VirtualKeyPort.
- **uv workspace:** 19 → 22 members (adds `adapters/channels/teams/`, `adapters/channels/slack/`, `kernel/auth/`).

**Ports added:**
- `virtual_key.py` — `VirtualKeyPort`, `VirtualKeySpec`, `VirtualKeyInfo`, `BudgetExhaustedError`

**No-waiver additions:** 9 entries (Stage 12 sublist, strict equality) — see allow-list section above.

**Contract tests:** 47 MAC-Ts delta (12 Teams + 12 Slack + 10 kernel/auth + 5 LiteLLM + 7 AST gates + 1 D2 cross-window); **281 tests PASS / 8 skipped / 0 failed**; 6 AST gates green; 12 VCR cassettes; 3 IdP fixtures (entra/okta/auth0). *(uncertain: memo says "47 MAC-Ts delta" using 7 AST gates in the breakdown but also "6 AST gates green" — verify against close artifacts)*

**HARD constraint extension (Mary H#7):** `\bseamless\b` + `\benterprise-grade\b` added (word-boundary, case-sensitive); `\bstrategic analysis\b` carried forward. Zero hits across source + tests.

**REFREEZE-03:** No GatewayPort / ChannelAdapterPort / ChannelContext surface changes landed in Stage 12 (policy.py refactor is internal; no REFREEZE-03 ceremony was needed). REFREEZE-03 ceremony remains required for any future surface changes.

**Carry-forward to Stage 13:** 5 findings — F-12-CLEO-C2 (CRITICAL), F-12-CLEO-M3 (MEDIUM), F-12-CLEO-W2 (LOW), F-12-OIDC-LIVE-DEFERRED-01 (Champion-gated; OUT of Stage 13), F-12-CLEO-M5-FALSE-POSITIVE-01 (informational; OUT of Stage 13).

**Inherited caveat:** HYPOTHETICAL-VOC (Stage 6.0.1 / A7 team-lead override 2026-05-24 at `f181a7e`) — every Stage 12 customer-fit claim carries: "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)".

**Stage 11.5 debt closures:** DIAL-LIVE-SMOKE RESOLVED; STAGE-11-DEBT-AUTH-01 CLOSED; STAGE-11-DEBT-LITELLM-VKEY-01 CLOSED. Carries to Stage 13: JSONRPC-FIXTURE-REGEN, SESSION-ID-WIDTH. WAL-CONCURRENCY DEFERRED per R6.

---

## Stage 13 — Production Hardening — RATIFIED 2026-05-28

**Status:** RATIFIED 2026-05-28 at `620b4cb` on `stage-13.0-production-hardening` (14 commits from base `5306c8d`); merged to main via fast-forward + tag `stage-13.0-ratified` → `620b4cb` pushed to origin 2026-05-28. Stage 12 binding RATIFIED anchor `43f57ba` preserved.

**Cycle:** Production hardening Option A — no new feature surface. R1–R14 advisor-reconciled + R15-V2 7-amendment patch folded pre-dispatch via Path α (Cleo C-1/C-2/C-3 + Amelia B1/B2 + Vera R13-A-1/R13-A-3).

**Scope IN (6 active items + 1 deferred):**
1. F-12-CLEO-C2 composition root — `OidcPolicy.__init__(verifier: JwtVerifier)` REQUIRED; no `None` default; no synthetic-fallback in production
2. F-12-CLEO-M3 NonceStore SQLite persistence + TTL — separate SQLite file from `session_index`; lazy TTL on read + startup sweep; WAL mode; Redis re-evaluation gated to multi-host
3. F-12-CLEO-W2 async `post_result` migration — TeamsAdapter + SlackAdapter
4. D4/Q1 hybrid `WebhookSigningKeyResolver` — dataclass per channel (NOT a port; promotable to port at 3rd channel); fail-fast on missing env-var; manual restart-rotation
5. JSONRPC-FIXTURE-REGEN
6. SESSION-ID-WIDTH — entropy floor ≥128 bits (Cleo entropy ranking: MEDIUM)
7. WAL-CONCURRENCY — DEFERRED per R6 (separate SQLite file confirmed; no shared writers)

**Scope OUT:** F-10-ARCH-AUDIT-02 (→ Stage 14), F-12-OIDC-LIVE-DEFERRED-01 (Champion-gated), F-12-CLEO-M5-FALSE-POSITIVE-01 (informational), RUFF-CLEANUP (folded to CI baseline), Cleo Q3 pre-existing sweep (→ Stage 14 candidates).

**MAC-T floor:** 25 binding (distribution per Murat; exact breakdown uncertain — verify at H#3).

**No-waiver planned:** 9 (Stage 12) → **13** total at Stage 13 close (strict equality). 4 additions: M-T-AUTH-VERIFIER-WIRED-AT-COMPOSITION-01, M-T-AUTH-NONCE-PERSISTENCE-RESTART-01, M-T-SESSION-ID-ENTROPY-FLOOR-01, M-T-NO-BARE-EXCEPT-AUTH-CRYPTO-01.

**5 AST gates (Cleo A–E):**
- A: `extract_claims(verifier=None)` ban outside `tests/`
- B: NonceStore `persistent: ClassVar[bool]` required
- C: sync httpx ban in async adapter bodies
- D: session-id entropy floor 128 bits
- E: bare-except ban in auth/crypto code paths

**Executor split:** E1 (auth/channel hardening) ‖ E2 (hygiene/data-plane); 2-window concurrent pattern. Sequencing: E2 commits land first (no behavioral delta), E1 second.

**Pre-charter gate (HARD):** `/verdaca-wiki-update` + `graphify update .` MUST run BEFORE H#1 (Vera load-bearing).

**7 gates:**

| Gate | Description | Status |
|---|---|---|
| G1 | Stage 13 scope confirmation roundtable | ✅ RATIFIED 2026-05-27 |
| G2 | VOC — HYPOTHETICAL caveat inherited; no new VOC gate for Stage 13 hardening cycle | RESOLVED per finish-then-demo sequencing lock |
| G3 | Cut `stage-13.0-production-hardening` from `stage-12.0-channel-adapters @ 5306c8d` (post-hygiene tail) | ✅ CLOSED 2026-05-28 |
| G4 | Executor dispatch — E1 ‖ E2; E2 commits land first | CLOSED via R11 |
| G5 | Stage 11.5 debt scheduling — JSONRPC-FIXTURE-REGEN + SESSION-ID-WIDTH in scope; WAL/RUFF deferred | CLOSED at G1 |
| G6 | Dispatch master executor | ✅ CLOSED 2026-05-28 (Codex/GPT-5 master + Claude Code executor served Stages 13 H#1-H#9; V1+V2+V3.A) |
| G7 | Merge Stages 11+12+13 → main | ✅ CLOSED 2026-05-28 (team-lead override of D13; fast-forward merge of Stage 13 chain; main `f181a7e` → `620b4cb`; tag `stage-13.0-ratified` pushed) |

**Inherited caveat:** HYPOTHETICAL-VOC (A7 team-lead override 2026-05-24 at `f181a7e`) — every Stage 13 customer-fit claim must carry: "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)".

---

## Stage 14 — Buyer Contact Surface via auditor gate (OPEN — G1 RATIFIED 2026-05-28)

**Status:** OPEN — G1 scope confirmation ratified 2026-05-28 via 6-agent roundtable (Winston + Vera + Amelia + Murat + John + Mary, 3 rounds, 16 total responses, full alignment). Branch `stage-14.0-buyer-contact-surface @ 620b4cb` cut from main 2026-05-29.

**Cycle framing:** NOT another pure Option-A hardening. Stage 13 substrate is internally-defensible; Stage 14 makes it externally-defensible by clearing the **auditor gate FIRST**, then exposing to first real Champion. HYPOTHETICAL-VOC retire runway longer than originally implied: first Champion call downgrades caveat to PROVISIONAL-SINGLE-SAMPLE (N=1); full retire needs N≥3 for population/magnitude/pricing claims per Murat lock.

### Phase 0 (Week 1) — Dual-track, two hard gates

**Track A — Engineering CVE close (Amelia + Cleo + Murat):**
- F-13-V3-JWKS-NOT-INTEGRATED-01 (CVE-class, Murat risk 9/10) — `JwksCache.get_or_fetch()` wired into `OidcPolicy.authenticate` before `JwtVerifier.decode`; `UnknownKeyError` → `invalidate()` + retry once; typed `AuthenticationError` on second failure
- F-13-V3-AUDIENCE-DOUBLE-DECODE-01 — bundled into B1; +2 MAC-Ts + 1 AST gate but **NO `@pytest.mark.no_waiver`** (risk 5 < 7 floor)
- vkey REQUIRED at production deploy — `policy_health_check()` fail-closed at production profile
- R15-c TTL race test + R15-d no_waiver constant pin (Murat backlog)
- Charter v0.2 11-param ratification — doc-only; M2 buyer-language audit before commit

**Track B — GTM + Auditor floor (Mary-coordinated split ownership):**
- B-1 Target prospect list (8-12 enterprise contacts, Teams/Slack profile)
- B-2 First-call script (K1/K2/K3 hypothesis-test structure)
- B-3 HYPOTHETICAL-VOC disclosure language
- B-4 SOC2-style pre-flight checklist (Mary draft; Cleo + Murat grading slots reserved)
- B-5 "First auditor meeting" worksheet (12-18 prepared Q&A pairs)
- B-6 End-of-Phase-0 reconciliation → "auditor floor satisfied" attestation OR gap ledger
- B-7 First-call scheduling Week 2-3, CONTINGENT on B-6 attestation

**Two end-of-Week-1 hard gates (BOTH must pass to release Phase 1):**
1. CVE PASS (Track A)
2. B-6 auditor floor attestation (Track B)

### Phase 1 (Week 2-3) — Champion-facing surface
- First Champion VOC call against clean substrate
- Demo runbook (M3 buyer-language audit at draft-close)
- Onboarding pipeline scripts
- K1/K2/K3 pre-registration table authored BEFORE Champion call
- Post-call hypothesis-class log + HYPOTHETICAL-VOC → PROVISIONAL-SINGLE-SAMPLE downgrade

### Phase 2 (Week 4+) — Polish burndown + Stage 14.5 named debt closure

### Canonical pin target
**Stage 14 close target: Runtime no_waiver = 14 / Stage 14 AST gates = 3 NEW / Total enforced markers = 23**
- +1 marker: `M-T-AUTH-JWKS-ROTATION-INVARIANT-01`
- +3 AST gates: Gate A-S14 + Gate B-S14 + Gate C-S14

### PROVISIONAL-SINGLE-SAMPLE caveat string (locked per Murat Round 3)

> *"(PROVISIONAL-SINGLE-SAMPLE: ratified by N=1 Champion call on YYYY-MM-DD; binding for existence + disqualification claims only; population/magnitude/pricing claims remain HYPOTHETICAL pending N≥3 triangulation)"*

### Auditor floor — split ownership (Mary coordinator)

| Owner | Artifact |
|---|---|
| Mary | SOC2-style pre-flight checklist + "First auditor meeting" worksheet + post-CVE-close reconciliation attestation |
| Cleo | Code-evidence grading against Mary's checklist |
| Murat | Test-discipline-evidence grading (no_waiver MAC-Ts + AST gates → control mapping) |

### HARD-constraint additions for Stage 14 (Mary M2 + M3)

Added to Stage 11+12 inheritance: `\brobust\b`, `\bproduction-ready\b` (+ hyphen variant), `\bcomprehensive\b`.

### Stage 14.5 named debt ledger
- F-13-V3-PARSE-ACTIVITY-CLAIMS-DICT-BYPASS-01 (Winston Round 3 yield; Teams-channel-coupled, demo-event-gated)
- R15-b semantic-drift probe (Murat backlog; if budget)

### OUT of scope
- 4 V3 WARNING + 3 V3 LOW Cleo cosmetic
- 3 handover-template drift candidates → Vera Stage 14.1 corrigendum
- 3 Mary H#7 cosmetic polish
- F-10-ARCH-AUDIT-02 (shell workspace)
- External SOC2 consultant (Stage 15+; needs VOC signal)

### Stage 14 gates
| Gate | Description | Status |
|---|---|---|
| G1 | 6-agent scope roundtable | ✅ RATIFIED 2026-05-28 |
| G2 | First real Champion VOC call | OPEN (Phase 1; contingent on B-6) |
| G3 | Cut `stage-14.0-buyer-contact-surface` from main `@620b4cb` | ✅ CLOSED 2026-05-29 |
| G4 | Phase 0 dispatch (Track A executor ‖ Track B Mary session) | OPEN |
| G5 | Memory `project_verdaca_stage14_scope` saved | ✅ CLOSED 2026-05-28 |
| G6 | Phase 0 end-of-Week-1 hard gates (CVE PASS ∧ B-6 attestation) | OPEN |
| G7 | Phase 1 release post-gates | OPEN |

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
- `feedback_hard_constraint_word_boundary` — UPDATED 2026-05-13: dual-context citation discipline (R8-binding docs cite by clause-ordinal; R8-non-binding cite by token-name). **UPDATED 2026-05-27 (Stage 12):** active forbidden tokens = `\bseamless\b` + `\benterprise-grade\b` + `\bstrategic analysis\b` (all word-boundary, case-sensitive grep; zero hits at Stage 12 close; carry forward to Stage 13).
- `feedback_go_with_amendments_tracked` — UPDATED 2026-05-13: executor surfaces compositional extensions BEFORE applying, even when substrate-conformant
- `feedback_concurrent_executor_orchestration` — load-bearing through Pair-1 (9.4.7‖9.4.8) and Pair-2 (9.5‖9.9); 2-window hard cap; halt-class disjointness verification at dispatch; path-scoped `git commit <pathspec>` at H#4; per-executor git worktree isolation (post F-9.4.6-B.1-W3-COMMIT-CONTAM-01 lesson)
- `feedback_preload_tracking_status_verification` — re-confirmed at 9.4.6, 9.4.7/9.4.8, 9.6 — verify cited SHAs / paths / tracking status at preload (gitignored docs/, sessions.db, etc.)
- `feedback_handover_template_discipline` — verify paths / §-refs / SHAs at H#1; surface drift as F-{stage}-HANDOVER-*
- `feedback_preload_api_surface_verification` — substrate-truth probes (9.4.6 LLMLingua PASS-DEGRADED precedent); Stage-11 FastMCP probes BLOCKING before charter
- **REFREEZE ceremony discipline (Stage 11 precedent, binding through Stage 12):** Any change to a FROZEN Port surface (GatewayPort, ChannelAdapterPort, ChannelContext, FROZEN_FIELD_ALLOWLIST) requires a REFREEZE-{N} ceremony (substantive commit + freeze SHA stamp commit, FROZEN_FIELD_ALLOWLIST invariant preserved). Stage 11 set this precedent with REFREEZE-01 (read API `9609c29`/`121670a`) and REFREEZE-02 (list_sessions `af5d4f4`/`14a31f8`). Stage 12 inherits: REFREEZE-03 required for any Port surface changes.
- **HYPOTHETICAL-VOC caveat inheritance (binding through Stage 13+):** Every customer-fit claim in Stage 11/12/13 close memos AND all downstream work must carry the inherited caveat string: "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)" — inherited from A7 team-lead override on Stage 10 close `f181a7e`. Caveat carries forward until a real-Champion VOC pass replaces the HYPOTHETICAL synthesis substrate. Per `project_verdaca_strategic_sequencing` memory: VOC re-do gate fires post-impl+test only; advisor MUST NOT propose VOC as a stage-close blocker until then.
