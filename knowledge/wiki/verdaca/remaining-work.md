# Verdaca — Remaining Work to POV-Ready

**Compiled:** 2026-05-08 → **Updated:** 2026-05-24 (Stage 10 RATIFIED via merge `8ae4f87`) | **Local main HEAD:** `8ae4f87` | **origin/main HEAD:** `e9c0643` (local 5 commits ahead — push gated) | **Stage:** Stage 9 RATIFIED; **Stage 10 RATIFIED 2026-05-24** (VOC PROVISIONAL via HYPOTHETICAL synthesis; close memo at [[docs/stage-10-ratified-close-memo.md]]; memory entry write pending); Stage 11 (planned) opens after A7 real-VOC re-confirmation per [[docs/stage-10-voc-gate.md]]

---

## Immediate: Stage 10.1 VOC + Ratification Gate

Stage 9 RATIFIED 2026-05-20 (`origin/main` merge `76eea26`, CI close `3e26f48`). Stage 10 implementation already landed at `d2b5670` (#42) on branch `stage-10.0-port-stubs` (pre-roundtable reconcile `50ce68e`). Forge substrate retired at 9.4.6 A.1 in favor of LLMLingua — the historic Forge G-1 BLOCKING GATE is moot.

The next ratification work is **Stage 10 VOC gate + ceremony**:

| Item | Status |
|---|---|
| Mary's VOC | ✅ COMPLETE-PROVISIONAL 2026-05-24 — HYPOTHETICAL synthesis (3 simulated archetypes: reinsurer-ML / consultancy decision-engineering / industrial-AI); 6 files at `voc-stage10/synthesis-run-hypothetical-2026-05-24/`; verdict **GO-with-amendments, LOW confidence**; fragility flag: K1/K2/K3 each triggered once on 1/3 calls (no 2-of-3 trigger, zero margin); buyer-language HARD audit 0 hits |
| VOC kill-switch criteria | K1/K2/K3 each fired on 1/3 (no PIVOT); K4 not flagged |
| Path 1 lock (team-lead 2026-05-24) | Synthesis accepted as provisional; A2/A3/A5 → Stage 11.x scope additions; **A7 = hard Stage 11.1 charter precondition** (real-VOC re-confirmation before Stage 11 locks); A1/A4/A6 forwarded to Stage 11.x ledger |
| Stage 10 RATIFIED ceremony | ✅ COMPLETE 2026-05-24 — Winston/Murat/Cleo audit cycle ALL READY-WITH-AMENDMENTS/WARNINGS; 134 ports tests passed/7 skipped + mypy clean; 2 amendment commits (`3d576a9` VOC gate marker + `da47d67` close memo); merge `8ae4f87` |
| `stage-10.0-port-stubs` FF into main | ✅ DONE via merge `8ae4f87` (origin pull from `85bdea1`→`e9c0643` + merge); local now 5 commits ahead of origin |
| `project_verdaca_stage10_ratified` memory entry | Drafted in close memo §8; **pending team-lead authorization** per `feedback_memory_authorization` |
| Push to origin | **NOT YET DONE** — explicit team-lead consent required per `feedback_memory_authorization` adjacent risk-action discipline |

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

### Stage 10 RATIFIED when
- [x] Mary's VOC complete + synthesized — **PROVISIONAL** via HYPOTHETICAL synthesis 2026-05-24; A7 carries real-VOC obligation forward to Stage 11.1
- [x] VOC readout = GO-with-amendments (no PIVOT; K1/K2/K3 each triggered once — fragility flag noted)
- [x] `stage-10.0-port-stubs` FF into main — DONE via merge `8ae4f87` 2026-05-24; `git pull` to e9c0643 + merge branch with 3 amendments (`d2b5670` + `3d576a9` + `da47d67`)
- [x] Close memo with §provenance table per `feedback_provenance_pin` + synthesis VOC provenance + A7 gate — DONE at [[docs/stage-10-ratified-close-memo.md]] (`da47d67`)
- [ ] Andrey explicit "continue" go to Stage 11 — pending real-VOC re-confirmation per A7
- [ ] `project_verdaca_stage10_ratified` memory entry authorized + written — draft in close memo §8; team-lead gate per `feedback_memory_authorization`

### Before Stage 11 charter opens
- [ ] Stage 10 RATIFIED
- [ ] 4 substrate-API probes PASS (BLOCKING at §4.0 per Stage-11 advisor handover):
      - [ ] FastMCP surface (Python `mcp.server.fastmcp.FastMCP` exists with required API)
      - [ ] JSON-RPC 2.0 golden (request/response shape)
      - [ ] Stateless HTTP invariant (`stateless_http=True` semantics confirmed in FastMCP)
      - [ ] Gateway contract (composition of LLMProxy + Memory + Cost + Compaction + SessionIndex)
- [ ] CAI spike port viable: `spike-mcp-server/src/http.ts` → `adapters/mcp_server/http.py` mirror

### Stage 11 RATIFIED when
- [ ] `adapters/mcp_server/` implements MCPTransportPort + GatewayPort + 1 ChannelAdapterPort (CLI minimum)
- [ ] 5 MCP tools + 5 resources + 1 prompt working end-to-end against Claude Desktop
- [ ] M-T-GATEWAY-* (≥8) + M-T-MCP-* (≥10) + M-T-DIAL-EXEC-* (≥2) + M-T-MCP-API-SURFACE-* (≥2) green
- [ ] No new no_waiver entries beyond +≤5 sublist (target ≤22 Stage-9+10+11 total)
- [ ] Demo packaging: Champion can install + invoke end-to-end via Claude Desktop within X minutes (X TBD per Stage 11 charter)

---

## Stage 10 — SessionIndex / Knowledge / Learning (in-flight; gated on VOC)

Decided at 5-agent roundtable 2026-05-20 (4-1 vote for data-plane / transport split). Hermes Agent self-learning roadmap is preserved; the 2026-05-08 plan was reshaped into the data-plane-first sequence below.

### Implementation status
- Branch: `stage-10.0-port-stubs`
- Implementation COMPLETE at `d2b5670` (#42)
- Pre-roundtable reconcile pass: `50ce68e` (F-10-RECONCILE-PRIOR-PORTS-01)
- Amendment commits on `stage-10.0-port-stubs`: `3d576a9` (VOC gate marker, F-10-TEST-AUDIT-05 resolution) + `da47d67` (close memo §provenance)
- **RATIFIED 2026-05-24** at merge `8ae4f87` into `main` (close memo: [[docs/stage-10-ratified-close-memo.md]]; VOC gate: [[docs/stage-10-voc-gate.md]]); VOC PROVISIONAL via HYPOTHETICAL synthesis — A7 = hard Stage 11.1 precondition for real-VOC re-confirmation

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

## Stage 11 — Channel-Neutral MCP Gateway (planned)

Opens after Stage 10 RATIFIED. Atlas + Mary precedent from CAI spike: populated MCP resources sold the demo, not tool calls — Stage 11 binds to ratified `SessionIndexPort` (NO stubs).

### Ports
| Port | Notes |
|---|---|
| `GatewayPort` | `execute(intent: StartAnalysisRequest, ctx: ChannelContext) → AnalysisResult`; composes LLMProxy + Memory + Cost + Compaction + SessionIndex |
| `MCPTransportPort` | stdio + Streamable HTTP; `stateless_http=True` PINNED as contract invariant |
| `ChannelAdapterPort` | 5 wrappers: Teams, Slack, CLI, UI, Claude-Desktop (Teams/Copilot manifests deferred post-Stage-11) |

### MCP surface (5 tools + 5 resources + 1 prompt)
- Tool language ("buyer-language"): "defensible recommendation with cited tradeoffs"
- Resources: `verdaca://sessions/{id}/result/{summary,transcript,artifacts}` + 2 others
- Mirror CAI spike: `spike-mcp-server/src/http.ts` → `adapters/mcp_server/http.py` (line-for-line port to Python `mcp.server.fastmcp.FastMCP`)

### VOC-10 amendment carry-forward (2026-05-24 Path 1 lock)
- **A2** — Word/PPT export surface (firm-template-friendly); load-bearing for consultancy senior-partner→client path
- **A3** — 3 procurement gates (data-residency / client-data SOP / Microsoft-stack-fit); Stage 10 charter covers via charter-clauses + architecture invariants; Stage 11 inherits and extends to channel-adapter manifests
- **A5** — Forwardable-link surface (stable URL inside channel thread; distinct from Shape A and Shape B)
- **A7** — **HARD CHARTER PRECONDITION** — real-VOC re-confirmation MUST happen before Stage 11.1 locks
- **A1 / A4 / A6** — latency-mode positioning / multi-LLM contract wording / post-mortem-survivability → Stage 11.x ledger

### Post-Stage-11 explicit defers
- Teams/Copilot manifests
- UI rewire to be a gateway client
- OAuth 2.1 auth stage
- Learning/feedback ports beyond SkillTelemetry

---

## Rough Sequence Estimate (Sessions, Not Calendar Days)

| Work block | Sessions estimate |
|---|---|
| ~~9.4.4 → 9.4.6 (Pi-Mono, LiteLLM, Compaction)~~ | ✅ DONE through 2026-05-17 |
| ~~9.4.7 ‖ 9.4.8 Pair 1~~ | ✅ DONE 2026-05-18 (~0.5 session — concurrent) |
| ~~9.5 ‖ 9.9 Pair 2~~ | ✅ DONE 2026-05-19 (~1 session — concurrent) |
| ~~9.6 Cleo supply-chain + Stage 9 RATIFIED~~ | ✅ DONE 2026-05-19 → 2026-05-20 |
| Stage 10 — 3 VOC calls + synthesis + ratification | 1–2 sessions (depends on call cadence) |
| Stage 11 — substrate probes + Gateway + MCP transport + 1 ChannelAdapter | 4–6 sessions |
| Stage 11 — demo packaging + Champion onboarding | 1–2 sessions |
| **Total to POV-ready (post-Stage-11)** | **~6–10 sessions** |
| Post-Stage-11 (Teams/Copilot, UI rewire, OAuth) | deferred |

---

## Quick Reference: What the Next Executor Needs

**For Stage 10 VOC ratification (next ratification work):**
- Local main HEAD = `85bdea1`; origin/main HEAD = `e9c0643` (14 commits ahead; consider `git pull` before VOC ceremony)
- Stage 10 implementation already landed at `d2b5670` on `stage-10.0-port-stubs` branch
- Run 3 Champion VOC calls (Andrey owns) per `voc-stage10-call-script.md`
- Mary synthesizes per `voc-stage10-scoring-rubric.md` (4 kill-switch criteria K1-K4)
- Halt discipline per `feedback_preload_first_gating`, memory writes gated per `feedback_memory_authorization`

**For Stage 11 (after Stage 10 RATIFIED):**
- 4 substrate-API probes BLOCKING before charter (FastMCP, JSON-RPC, stateless HTTP, gateway contract)
- Reference: CAI spike at `spike-mcp-server/src/http.ts` for the Python port pattern
- Stage 11 binds to ratified `SessionIndexPort` — NO stubs allowed

---

## Design Work Remaining (Phase 3+)

- **Factory shell cycle** — next per-surface cycle (S-1..S-4 analogue for Factory product shell); opens at team-lead discretion (after a break per 2026-05-13 disposition)
- **Subsequent shells** — Shield, Pipeline, Ops (per parent brief §4.3)
- **v1.1 substrate amendment cycle** — gates on ≥3 surfaces from 7 P3-* candidates; no schedule yet
- **R3 dark-canonical re-disposition** — required before any production Studio deploy (F-3 thin-slice deviation must not extend to production)
- **v1.1 brand-mark amendments** — 3 candidates from brand-mark cycle: P-BM-1 (master glyph slot spec), P-BM-2 (archive path-of-record corrigendum), P-BM-3 (kickoff-template embedded-repo seam clarification)
