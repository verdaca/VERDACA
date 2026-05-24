# Stage 9 — Ports-and-Adapters State

**Compiled:** 2026-05-08 → **Updated:** 2026-05-24 (VOC synthesis + Path 1 lock) | **Source:** session handoffs 2026-04-12 → 2026-05-13 + `docs/stage-*-handover.md` 2026-05-16 → 2026-05-22 + in-session VOC synthesis 2026-05-24
**HEAD at last local-main close:** `8ae4f87` (Stage 10 RATIFIED merge — joins `da47d67` close memo + `3d576a9` VOC gate + `d2b5670` Stage 10 impl with `e9c0643` origin/main) | **origin/main HEAD:** `e9c0643` (local now 5 commits ahead via Stage 10 RATIFIED merge — push gated per `feedback_memory_authorization` adjacent risk-action discipline)
**Branch:** main (local ahead of origin)

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
- **`ports/` now includes:** `memory.py`, `serialization.py`, `versioned_state.py`, `cost_meter.py`, `llm_proxy.py`, `compaction.py` (9.4.6 A.2 `72b7beb` + v0.2.6 corrigendum at B.1-W1 `e98a25b`), `common.py` (Message sibling-add at 9.4.5 A.2)

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

⚠ Memory entry `[[project_verdaca_stage9_ratified]]` cites SHA `45e1fd8 #41`. That commit exists only on feature branches (`stage-9.4.7-namespace-cleanup`, `stage-9.6-cleo-supply-chain`, `stage-10.0-port-stubs`) and is a 9.6 corrigendum that did not merge into `origin/main`. The Stage-9 close on `origin/main` is `3e26f48` (#40 CI close) + `76eea26` (Stage 9 ratification merge). Memory SHA correction pending team-lead authorization.

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

## Stage 11 (planned) — Channel-Neutral MCP Gateway

**Opens only after Stage 10 RATIFIED.** Atlas + Mary precedent: populated MCP resources sold the CAI demo, not tool calls — Stage 11 binds to ratified SessionIndexPort (NO stubs).

- 4 substrate-API probes BLOCKING before charter (FastMCP surface, JSON-RPC golden, stateless HTTP invariant, gateway contract)
- `GatewayPort` — `execute(intent, ctx) → AnalysisResult`; composes LLMProxy + Memory + Cost + Compaction + SessionIndex
- `MCPTransportPort` — stdio + Streamable HTTP; `stateless_http=True` PINNED as contract invariant
- `ChannelAdapterPort` — 5 wrappers: Teams, Slack, CLI, UI, Claude-Desktop (Teams/Copilot manifests deferred post-Stage-11)
- MCP surface: 5 tools + 5 resources (`verdaca://sessions/{id}/result/{summary,transcript,artifacts}`) + 1 prompt
- Mirror CAI spike: `spike-mcp-server/src/http.ts` → `adapters/mcp_server/http.py` (Python `mcp.server.fastmcp.FastMCP`)
- +≤5 no_waiver entries (target ≤22 total Stage-9+10+11); MAC-T floor ≥22 (M-T-GATEWAY-* 8 + M-T-MCP-* 10 + M-T-DIAL-EXEC-* 2 + M-T-MCP-API-SURFACE-* 2)

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
