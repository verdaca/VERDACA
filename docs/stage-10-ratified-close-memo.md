# Stage 10 — RATIFIED Close Memo

**Compiled:** 2026-05-24
**Branch:** `stage-10.0-port-stubs`
**Stage 10 scope:** SessionIndexPort + SkillTelemetryPort data-plane
**Verdict:** **RATIFIED-WITH-PROVISIONAL-VOC** — provisional pending real-VOC re-confirmation against Stage 11.1 (per [[docs/stage-10-voc-gate.md]] A7 gate) **→ A7 CLOSED 2026-05-24 via team-lead override; see §9 amendment**

---

## §1 — What Was Ratified

Stage 10 ships the **data-plane substrate** that Stage 11 will compose into a channel-neutral MCP gateway. Two new ports + one workspace package + one CLI surface land at this ratification:

| Element | Locator |
|---|---|
| `SessionIndexPort` Protocol (API_VERSION 1.0.0) | `kernel/session_index/src/praxis/kernel/session_index/port.py` |
| `SkillTelemetryPort` Protocol (API_VERSION 1.0.0) | same file |
| 9 DTOs (`SessionExcerpt`, `SessionRecord`, `SessionFilter`, `ArtifactRef`, `TelemetryEvent`, `TimeWindow`, `SkillOutcome`, `SkillUsage`, `SkillInvocationRecord`) | `kernel/session_index/.../models.py` |
| 5 closed `Literal` aliases (`SessionStatus`, `ArtifactKind`, `TelemetryEventKind`, `SkillProvenance`, `SkillState`) | same file |
| `SqliteSessionIndex` reference adapter | `kernel/session_index/.../sqlite_store.py` |
| `SqliteSkillTelemetry` reference adapter | `kernel/session_index/.../skill_telemetry.py` |
| `001_initial.sql` migration + `schema_migrations` ledger | `kernel/session_index/.../schema/001_initial.sql` |
| `verdaca session list / show <id>` CLI | `shell/src/praxis/shell/cli.py` |
| 27 MAC-T contract surfaces / 38 test items / +4 no_waiver delta (9 → 13) | `tests/src/praxis/contract_tests/ports/test_session_index_port_contract.py`, `test_skill_telemetry_port_contract.py`, `test_no_waiver_inventory.py` |
| F10 (Stage 9.5 #38) PEP-420 resolution | 6 marker `__init__.py` deletions across kernel packages |

**Default dev DB path** is package-owned (`tempfile.gettempdir() / "verdaca-session-index" / "session-index-dev.sqlite3"`), explicitly NOT `knowledge/sessions.db` (Stage 9.4.8 FTS5 session-handoff indexer).

## §2 — Provenance

| Field | Value |
|---|---|
| Branch | `stage-10.0-port-stubs` |
| Base SHA (Stage 10 implementation) | `d2b5670` — "feat: Stage 10 — SessionIndexPort + SkillTelemetryPort" (Fri 2026-05-22 by Andrey + Codex GPT-5) |
| Parent chain base | `45e1fd8` (9.6 corrigendum, NOT on origin/main) → `3e26f48` (origin/main 9.6 close) → ... → `85bdea1` (local main HEAD; 9.4.6 close) |
| Pre-roundtable reconcile | `50ce68e` (F-10-RECONCILE-PRIOR-PORTS-01) |
| Amendment SHA #1 (VOC gate marker) | `3d576a9` — "docs: Stage 10 — VOC gate marker (F-10-TEST-AUDIT-05 resolution)" (this session, 2026-05-24) |
| Amendment SHA #2 (close memo) | `da47d67` — "docs: Stage 10 RATIFIED close memo (§provenance + audit ledger)" (this session, 2026-05-24) |
| Amendment SHA #3 (A7 override close) | This commit — single commit lands [[docs/stage-10-voc-gate.md]] flip + this memo §9 amendment. Derive via `git log --oneline -1 -- docs/stage-10-voc-gate.md docs/stage-10-ratified-close-memo.md` |
| Stage 10 RATIFIED date | 2026-05-24 |
| Ratification authority | Team-lead (Andrey) — Path 1 lock 2026-05-24 |
| origin/main HEAD at ratification | `e9c0643` (14 commits ahead of local main; FF requires `git pull` reconcile) |

## §3 — Audit Cycle Outcomes

Three-agent BMAD audit on `d2b5670`, all returning ready verdicts:

| Agent | Verdict | Findings → Stage 7 debt | Blockers / Amendments |
|---|---|---|---|
| 🏗️ Winston (Architect) | ARCH-READY-WITH-AMENDMENTS | F-10-ARCH-AUDIT-01/03/04/05 (4 LOW/TRIVIAL) | F-10-ARCH-AUDIT-02 (shell/ workspace registration) — **reclassified Stage 10.5 debt** due to pre-existing pytest-asyncio<1 + pytest>=9 conflict in shell `[dev]` deps; 9.6 deferral stands |
| 🧪 Murat (Test Architect) | TEST-READY-WITH-AMENDMENTS | F-10-TEST-AUDIT-01/02/03/04 (4 cosmetic/forward-route) | F-10-TEST-AUDIT-05 (VOC provisionality not git-trackable) — **RESOLVED** by [[docs/stage-10-voc-gate.md]] at amendment SHA `3d576a9` |
| 🔍 Cleo (Clean Code Reviewer) | CODE-READY-WITH-WARNINGS | 7 WARNINGs as `W-10-Cleo-1..7` | **Zero blockers** |

### Verified by (replay of d2b5670 baseline at amendment SHA `3d576a9`)
- Full ports contract suite: **134 passed, 7 skipped** ✓
- Stage 10 contract subset: 38 passed (incl. `M-T-SESSIONIDX-REPLAY-01` falsification probe + `M-T-SESSIONIDX-COMPOSITION-01` cross-port-delegation forbid) ✓
- No-waiver inventory: 6 passed (`test_stage9_no_waiver_inventory_matches_allowlist` + `test_stage10_no_waiver_inventory_matches_allowlist` GREEN) ✓
- mypy strict on `kernel/session_index/src`: clean (6 source files) ✓
- mypy on `shell/src`: clean (2 source files) ✓

## §4 — VOC Provenance + A7 Gate

**Synthesis verdict:** GO-with-amendments, **LOW confidence**, **provisional**.

**Synthesis kind:** HYPOTHETICAL — 3 simulated Champion archetypes (reinsurer-ML / consultancy decision-engineering / industrial-AI). NO real Champion calls.

**Fragility flag:** K1/K2/K3 each triggered on exactly 1 of 3 calls — no 2-of-3 PIVOT, **zero safety margin**. K4 not flagged. Buyer-language HARD audit: 0 hits.

**Artifacts:** `_bmad-output/planning-artifacts/Verdaca/voc-stage10/synthesis-run-hypothetical-2026-05-24/` (6 files).

**Path 1 lock decision:** Synthesis accepted as provisional. A7 (real-VOC re-confirmation) becomes a HARD Stage 11.1 charter precondition. Stage 11.1 charter authoring is BLOCKED until real Champion VOC calls complete and synthesize to non-PIVOT.

**Machine-readable gate:** [[docs/stage-10-voc-gate.md]] — `provisional_voc=True`, `real_voc_required_before_stage_11_charter=True`. Stage 11.1 dispatch pre-flight enforces.

**Update 2026-05-24 (amendment SHA #3 — see §9 below):** A7 CLOSED via explicit team-lead override. Marker flipped to `provisional_voc=False` + `real_voc_required_before_stage_11_charter=False` + `a7_close_kind=team_lead_override`. Closure substrate UNCHANGED (no real Champion calls; HYPOTHETICAL synthesis inherited). Downstream citation discipline per Stage 6.0.1 caveat pattern (see §9 for full text + acknowledged risks).

### Other VOC-10 Amendments

| ID | Routing |
|---|---|
| VOC-10-A1 (latency-mode positioning) | Stage 11.x ledger |
| VOC-10-A2 (Word/PPT export surface) | Stage 11.x scope addition |
| VOC-10-A3 (3 procurement gates) | Stage 10 charter covers; Stage 11 channel-adapter manifests inherit |
| VOC-10-A4 (multi-LLM contract wording) | Stage 11.x ledger |
| VOC-10-A5 (forwardable-link surface) | Stage 11.x scope addition |
| VOC-10-A6 (post-mortem-survivability) | Stage 11.x ledger |
| **VOC-10-A7 (real-VOC re-confirmation)** | **HARD Stage 11.1 charter precondition (this memo, [[docs/stage-10-voc-gate.md]])** |

## §5 — Forward-Routed Findings Ledger

### Stage 10.5 debt (new — small follow-ons before Stage 11)
| ID | Severity | Source | Routing |
|---|---|---|---|
| F-10-ARCH-AUDIT-02 | MEDIUM | Winston | shell/ workspace registration — blocked by pytest-asyncio<1 ∧ pytest>=9 conflict in shell `[dev]`. Resolve via shell pytest-asyncio bump OR CLI extraction OR explicit operational install doc |
| F-10-EDGE-04 | MEDIUM | Original d2b5670 | Max payload guard for SessionIndex / SkillTelemetry write paths |
| F-10-ARCH-AUDIT-04 | TRIVIAL | Winston | DRY `_DEFAULT_DB_PATH` between `sqlite_store.py` + `skill_telemetry.py` (also Cleo W-10-Cleo-6) |
| F-10-TEST-AUDIT-02 | LOW | Murat | Tighten allow-list bounds from `<= 13`/`<= 4` to `== 13`/`== 4` |

### Stage 11.x debt
| ID | Severity | Source | Routing |
|---|---|---|---|
| F-10-EDGE-03 | MEDIUM | Original d2b5670 | SQLite WAL/pooling policy for Stage 11 async gateway (subsumes F-10-ARCH-AUDIT-03 "two ports sharing DB file") |
| F-10-COMPRESSION-MOCKER-DEP-01 | LOW | Original d2b5670 | Pre-existing compression test dependency gap |
| F-10-MAC-CRLF-SNAPSHOT-01 | LOW | Original d2b5670 | Pre-existing Windows CRLF/LF snapshot mismatch (visible in this branch's git-diff stat-cache noise on `pyproject.toml`) |
| F-9.4.6-LLMLINGUA-MAINTENANCE-STALENESS-1 | LOW | 9.6 CVE-deferrals carry-forward | Pinned for later |
| F-10-ARCH-AUDIT-01 | LOW | Winston | `index_session(content: str)` JSON-parse-failure synthesis — document explicitly OR split `index_record(SessionRecord)` typed-caller path |
| F-10-TEST-AUDIT-01 | COSMETIC | Murat | 3 MAC-T ID collisions (`LIST_02`, `GET_03`, `QUERY_02`); pytest discrimination saves correctness, auditability wants renumber |
| F-10-TEST-AUDIT-03 | MEDIUM | Murat | Schema-migration explicit contract tests missing (migration runs implicitly via fixture construction) |

### Stage 9.9-debt
| ID | Severity | Source | Routing |
|---|---|---|---|
| F-10-TEST-AUDIT-04 | LOW | Murat | No nightly Tier 3 schedule for full ports contract suite |

### Stage 7 debt (operator-disciplined code quality)
| ID | Title | Severity |
|---|---|---|
| W-10-Cleo-1 | Enable `[S, DTZ, RUF]` in `kernel/session_index/pyproject.toml [tool.ruff.lint] select` (consolidates 5.3.5 W1) | WARNING |
| W-10-Cleo-2 | `shell/cli.py:64` "session not found" → `sys.stderr` per POSIX.1-2017 §3 (F-10-CLEO-AUDIT-01) | WARNING |
| W-10-Cleo-3 | `list_sessions` dynamic-WHERE builder needs defensive comment / parameterized-query catalog (F-10-CLEO-AUDIT-02) | WARNING |
| W-10-Cleo-4 | `_record_from_content` silent JSON-fabrication branch — make explicit via separate API or OTEL warning span (F-10-CLEO-AUDIT-03) | WARNING |
| W-10-Cleo-5 | `_fts_query` empty-tokenization → OTEL attribute or `ContractViolation` (F-10-CLEO-AUDIT-04) | WARNING |
| W-10-Cleo-6 | DRY `_DEFAULT_DB_PATH` between sqlite_store + skill_telemetry (F-10-CLEO-AUDIT-05; also Winston F-10-ARCH-AUDIT-04) | WARNING |
| W-10-Cleo-7 | `json_group_array` ordering is undefined behavior — sort `SkillUsage.sessions` in Python (F-10-CLEO-AUDIT-06) | WARNING (LATENT) |

## §6 — Closed at d2b5670 (carry-forward CLOSED, not routed)
- F-10-CLEO-01 (Cleo H#5: query indexes for SessionIndex + SkillTelemetry) ✓
- F-10-CLEO-02 (Cleo H#5: SQLite foreign keys + busy_timeout per connection) ✓
- F-10-EDGE-01 (reject reversed `TimeWindow(start > end)` with `ContractViolation`) ✓
- F-10-EDGE-02 (reject naive datetime in `index_session()`) ✓
- **F10 (Stage 9.5 #38)** — RESOLVED at d2b5670 via uniform `praxis.kernel` PEP-420 (6 marker `__init__.py` deleted, team-lead authorized 2026-05-21). **Wiki F10 status correction needed at FF.**
- F-10-RECONCILE-PRIOR-PORTS-01 — CLOSED at `50ce68e` (pre-roundtable reconcile)

## §7 — Stage 11.1 Implications

**Stage 11.1 charter MUST verify before dispatch** (per [[docs/stage-10-voc-gate.md]] §"Stage 11.1 Charter Dispatch Pre-Flight"):
1. Real Champion VOC calls run (Andrey owns; per `voc-stage10-call-script.md`)
2. Mary synthesized against `voc-stage10-scoring-rubric.md`
3. Synthesis returned non-PIVOT (GO or GO-with-amendments)
4. Synthesis output captured at `_bmad-output/planning-artifacts/Verdaca/voc-stage10/` with non-HYPOTHETICAL provenance
5. `docs/stage-10-voc-gate.md` updated: `provisional_voc=False` + new §"Real VOC Provenance" appended; `Status` line flipped to `RATIFIED`

If any of (1)–(4) is unmet, Stage 11.1 charter MUST NOT be drafted.

**Status 2026-05-24 (amendment SHA #3 — see §9):** Items (1)-(4) **explicitly bypassed** via team-lead override. Item (5) executed by amendment SHA #3 commit. Stage 11.1 charter dispatch **UNBLOCKED** for serial Phase 1 (H#1 substrate probes → H#1.5 Port-freeze → H#2 charter → H#3 MAC-T catalog) per master handover §7. Downstream Stage 11 work inherits the citation caveat from §9.

**Stage 11.x scope absorbs:** VOC-10-A2 (Word/PPT export), A5 (forwardable-link), F-10-EDGE-03 (WAL/pooling), F-10-EDGE-04 (payload guard), all 7 Cleo WARNINGs (W-10-Cleo-1..7 polish in Stage 7), F-10-ARCH-AUDIT-01/03 (port-API hardening + DB-substrate concerns), F-10-TEST-AUDIT-03 (schema-migration explicit tests). **Plus added 2026-05-24:** `VOC-10-A7-DEFERRED` (real Champion outreach — RECOMMENDED-NOT-REQUIRED per §9 amendment).

## §8 — FF Strategy + Memory Entry Gate

### FF strategy (recommended sequence step 4)
1. `git checkout main` (return to main worktree)
2. `git pull origin main` to catch up 14 commits (origin/main `e9c0643`)
3. Resolve merge: `stage-10.0-port-stubs` (this branch + amendments) into main. **Merge commit** preferred over rebase per `feedback_advisor_executor_model_effort` non-destructive default (45e1fd8 is non-trivial; rebase would rewrite SHAs).
4. Address `.gitignore` drift between local main mod (removes `!docs/`) and branch state (keeps `!docs/`) — likely keep the branch's `!docs/` if `docs/` is now the canonical close-memo + VOC-gate location.
5. Do NOT `git push` without explicit team-lead consent per `feedback_memory_authorization`'s adjacent risk-action discipline.

### Memory entry gate (recommended sequence step 6)
**Pending team-lead authorization.** Draft for `project_verdaca_stage10_ratified`:

```markdown
---
name: project-verdaca-stage10-ratified
description: Stage 10 RATIFIED — SessionIndex / SkillTelemetry data-plane; PROVISIONAL VOC via HYPOTHETICAL synthesis; A7 hard precondition for Stage 11.1
metadata:
  type: project
---

Stage 10 RATIFIED 2026-05-24 (this close-memo SHA + amendment chain
3d576a9 → d2b5670 → 45e1fd8 → 3e26f48). [[docs/stage-10-voc-gate.md]]
carries the provisional-VOC marker; A7 real-VOC re-confirmation gates
Stage 11.1 charter. 27 MAC-Ts / 13-entry no_waiver allow-list / 134 ports
GREEN / mypy clean. F-10-ARCH-AUDIT-02 (shell/ workspace) reclassified
to Stage 10.5 debt due to pre-existing pytest-asyncio<1 ∧ pytest>=9
conflict in shell [dev] (9.6 deferral stands). 7 Cleo WARNINGs +
4 cosmetic/medium amendments routed to Stage 7 / 10.5 / 11.x / 9.9-debt
ledgers per [[docs/stage-10-ratified-close-memo.md]] §5.

Why: closes the data-plane substrate Stage 11 binds against; A7 gate
preserves Verdaca's correctness>speed discipline through Stage 11 against
a fragility-flagged provisional VOC.

How to apply: when authoring Stage 11.1 charter, run pre-flight check
per [[docs/stage-10-voc-gate.md]] §"Stage 11.1 Charter Dispatch Pre-Flight"
before any draft work. Real VOC obligation is non-negotiable.
```

Team-lead must explicitly authorize before this memory entry is written per `feedback_memory_authorization`.

---

## §9 — Amendment 2026-05-24: A7 CLOSED via Explicit Team-Lead Override

**Amendment commit:** This commit — single commit covers both this memo §§ above and [[docs/stage-10-voc-gate.md]] flip. Derive SHA via `git log --oneline -1 -- docs/stage-10-voc-gate.md docs/stage-10-ratified-close-memo.md`.
**Amendment authority:** Team-lead (Andrey) directive 2026-05-24 ("close A7") in Stage 11 advisor party-mode session.
**Closure kind:** Explicit override — NO real Champion calls were run before closure.

**Closure substrate (unchanged from §4):**
- Original HYPOTHETICAL synthesis (3 simulated archetypes: reinsurer-ML / consultancy decision-engineering / industrial-AI)
- K1/K2/K3 each fired on 1 of 3 calls (zero margin; no 2-of-3 PIVOT); K4 not flagged
- Buyer-language HARD audit: 0 hits
- Artifacts at `_bmad-output/planning-artifacts/Verdaca/voc-stage10/synthesis-run-hypothetical-2026-05-24/`

**Closure effect:**
- [[docs/stage-10-voc-gate.md]] Status flipped: `RATIFIED-WITH-PROVISIONAL-VOC` → `RATIFIED (A7 closed 2026-05-24 via explicit team-lead override)`
- Machine-readable marker: `provisional_voc=False`, `real_voc_required_before_stage_11_charter=False`, `a7_close_kind=team_lead_override`, `a7_close_date=2026-05-24`, `a7_close_authority=team-lead Andrey`
- Stage 11.1 charter dispatch **UNBLOCKED** for serial Phase 1 (per master handover §7)
- VOC-10-A7 reclassified: HARD precondition → `VOC-10-A7-DEFERRED` (Stage 11.x debt ledger; RECOMMENDED-NOT-REQUIRED; re-activated if/when team-lead schedules Champion outreach)

**Downstream citation discipline (binding per `feedback_go_with_amendments_tracked` + Stage 6.0.1 caveat pattern):** All Stage 11 results that trace back to A7 carry the caveat:

> "(A7 closed via team-lead override 2026-05-24; underlying VOC substrate is HYPOTHETICAL synthesis, not real Champion calls)"

**Caveat inherited by (forward-propagation):**
- Stage 11 RATIFIED close memo (`project_verdaca_stage11_ratified` close ceremony)
- `project_verdaca_stage11_ratified` memory description
- Any GTM / pitch material citing Stage 11 customer-fit
- Any Stage 12+ work re-encountering K1-K4 risk material
- Any external comms (sales decks, white papers, conference talks) citing Stage 11 buyer validation

**Risk acknowledgment:** Stage 11 charter authors on the same fragile (zero-margin K1/K2/K3) substrate that triggered A7 in the first place. Treat A7 gate as **not load-bearing** for customer-fit claims. The HYPOTHETICAL synthesis remains the only VOC substrate at Stage 11 dispatch time.

**Rollback path:** This amendment is supersession-compatible. If real Champion calls later contradict the HYPOTHETICAL synthesis, a §10 "Amendment YYYY-MM-DD: A7 supersession on real-VOC" may be authored — restoring or correcting the substrate without losing the override history.

**Memory entry update:** The `project_verdaca_stage10_ratified` memory description (per §8 above, written 2026-05-24 with team-lead "save") will be updated separately to reflect A7 closure via override — **pending separate team-lead "save" authorization** per `feedback_memory_authorization`. Proposed description delta:

> "Stage 10 RATIFIED 2026-05-24 at merge `8ae4f87` — SessionIndex / SkillTelemetry data-plane; PROVISIONAL VOC via HYPOTHETICAL synthesis; **A7 CLOSED 2026-05-24 via explicit team-lead override (no real Champion calls; downstream Stage 11 results carry HYPOTHETICAL-substrate caveat); Stage 11.1 charter dispatch UNBLOCKED**."

---

**Authority:** This memo is binding for Stage 10 ratification. Future modifications require team-lead authorization.
