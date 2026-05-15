# Stage 9.4.6 Phase A.1 — LLMLingua Substrate Re-anchor Executor Handover

**Persona:** Amelia (executor)
**Predecessor:** TBD at H#1 — predecessor SHA is whichever lands LAST between this Phase A.1 cycle and the Stage 9.1.2-2 serialization §3 corrigendum cycle (independent stream; either may land first). Verify at H#1 preload via `git log --oneline -<N>` where N counts SHAs from current HEAD back to `5b7019f` (Stage 9.4.5 RATIFIED close).
**Chain at HEAD:** TBD (24-SHA + 1-2 since Stage 9.4.5 close depending on whether Stage 9.1.2-2 corrigendum landed first); target +1 SHA at Phase A.1 landing.
**Authorized model:** Sonnet 4.6 medium (substance-heavy doc corrigendum + commit-body-of-record)
**Scope class:** Stage 9.4.6 Phase A.1 ONLY (docs corrigendum); forward-pointers to A.2/B.1/B.2/C are NOT authorized in this sub-charter.

---

## §1 Authorization scope

This sub-charter authorizes ONE Phase A.1 cycle: land the ADR-9.2-V6 corrigendum re-anchoring CompactionPort substrate from Forge → LLMLingua, plus any required ADR-9.1.2-4 §3 DTO PINNING updates.

**Decision basis** (locked at advisor seat 2026-05-13):
- F-9.4.6-FORGE-SEMANTIC-MISFIT DECLARED (root finding) + F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE DECLARED + F-9.4.6-FORGE-IDENTITY-DRIFT-1 DECLARED — all retained as RETIRED-FALSIFIED in close memo
- Decision 2 = Option C / LLMLingua primary; D pure-Python stub as CI-fragility fallback
- G-1 license: PASSED at advisor mini-scout (MIT + OSI-permissive transitive deps)

**Substance source:** `_bmad-output/planning-artifacts/Verdaca/adr-9.2-v6-corrigendum-draft.md` (~5KB advisor-authored corrigendum substance). Read verbatim at H#1; this is your H#2 substance-design template.

**Out of scope this cycle:**
- Phase A.2 `ports/compaction.py` Protocol authoring (next sub-charter)
- Phase B.1 `adapters/llmlingua/` implementation (next sub-charter after A.2)
- Phase B.2 contract tests
- Phase C close-handoff with pipeline flip
- Stage 9.1.2-2 serialization §3 corrigendum (independent parallel cycle; do NOT touch)
- Allow-list mutations (NO entries added or removed this cycle; LLMLingua adapter allow-list scope determined at Phase A.2)

---

## §2 Predecessor + chain

Verify at H#1 preload:

- **Predecessor SHA:** `git rev-parse HEAD` — note value at H#1
- **Chain length:** `git log --oneline 5b7019f..HEAD | wc -l` — expected 0 (if 9.1.2-2 hasn't landed) or 1 (if 9.1.2-2 landed first); target +1 at this cycle's close
- **Working-tree baseline at start:** verify via `git status --short`; expected `??` files:
  - 4 baseline carry-forward (`docs/epam-security-clearance-email-draft.md`, `docs/openclaw-setup-guide.md`, `docs/stage-9.4.6-handover-advisor.md`, `docs/stage-9.4.6-handover-executor.md`)
  - 3 Stage 9.4.6 gate-clearance deliverables (`docs/stage-9.4.6-a.1-john-1-audit-report.md`, `docs/stage-9.4.6-g1-license-audit.md`, `docs/stage-9.4.6-docker-readiness.md`)
  - 2 new handover docs from advisor seat (`docs/stage-9.1.2-2-corrigendum-executor-handover.md`, `docs/stage-9.4.6-phase-a.1-executor-handover.md`)
  - Possibly 1 audit-report from Stage 9.1.2-2 if that cycle landed first (depends on inter-cycle ordering)
  - Total: 8-10 `??` files (verify exact count + composition at H#1)

Surface drift per Q-9.4.5-19 + `feedback_concurrent_executor_orchestration`.

---

## §3 Substance scope — the corrigendum

### §3.1 Substance source authority (gitignore-caveat)

Per `feedback_preload_tracking_status_verification` + `feedback_handover_template_discipline`:

- **Local files (best-available substance):**
  - `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md` (gitignored)
  - `_bmad-output/implementation-artifacts/verdaca/stage9/port-contracts.md` (gitignored)
  - `_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md` (gitignored)
- **Authoritative on divergence:** corrigendum-of-record commit-message body per `de365ff` precedent
- **Substance template:** `_bmad-output/planning-artifacts/Verdaca/adr-9.2-v6-corrigendum-draft.md` (advisor-authored, 2026-05-13)

The corrigendum substance MUST be captured in the commit-message body of THIS cycle's commit. Local files updated as best-available substance (your edits land there for team-lead working file currency).

### §3.2 Substance — ADR-9.2-V6 v0.6 → v0.7 corrigendum

Update `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md`:

1. **Doc-version bump:** v0.6 → v0.7 in the corrigendum-banner stack (preserve previous banner lines; add new v0.7 banner at top per Q-9.4.5-18 stacked-corrigenda discipline)
2. **G-1 BLOCKING GATE section:** update substrate identity + PASS/FAIL paths per ADR-V6 corrigendum draft §4 + §5. Verbatim substance from `_bmad-output/planning-artifacts/Verdaca/adr-9.2-v6-corrigendum-draft.md` §4 + §5.
3. **F-class history note:** add inline reference to F-9.4.6-FORGE-SEMANTIC-MISFIT (RETIRED-FALSIFIED) as the falsification basis, citing the H2-falsification precedent at ADR-9.2-V5 v0.6 in 9.4.5.

### §3.3 Substance — ADR-9.1.2-4 §3 DTO PINNING (conditional)

Verify at H#1 / H#2 substance design:
- Does ADR-9.1.2-4 §3 currently list Forge-specific DTO names? If yes, replace with LLMLingua-mapped DTOs at §3 base + §3.6 corrigendum-DTO additions if scope expands.
- If ADR-9.1.2-4 §3 is stub-only (in_tree_compaction_stub fallback DTOs), this section may be UNCHANGED at A.1; LLMLingua-specific DTOs land at Phase A.2 alongside `ports/compaction.py` Protocol authoring.

**Disposition options at H#2 (advisor disposes):**
- **3.3.A** — ADR-9.1.2-4 §3 needs CompactionRequest + CompactionResponse base DTOs added now (Phase A.1 scope expanded)
- **3.3.B** — ADR-9.1.2-4 §3 stays at stub fallback; PASS-path DTOs land at Phase A.2 (Phase A.1 scope unchanged from §3.2)

### §3.4 Paired sweep (per `feedback_corrigendum_paired_sweep`)

Three paired artifacts to update at A.1 landing:

1. **`docs/pipeline-stage9.md`** (TRACKED — edit + commit alongside corrigendum)
   - Locate 9.4.6 pipeline lines (284-287 per advisor handover §1)
   - Add corrigendum cite row for ADR-9.2-V6 v0.7 (per Q-9.4.5-20 line-text discipline: citation-chain context acceptable, status-declaration NOT acceptable)
   - Update compaction adapter substrate header from "Forge — Rust sidecar via Docker" → "LLMLingua PyPI library single-adapter"
2. **`_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md`** (GITIGNORED — commit-body-of-record)
   - Update CompactionPort MAC-T scope if any tests reference Forge-specific adapter testing
   - Allow-list entries scope determined at Phase A.2 (not A.1)
3. **`_bmad-output/implementation-artifacts/verdaca/stage9/port-contracts.md`** (GITIGNORED — commit-body-of-record)
   - Per §3.3 disposition
   - Doc-level version bump (verify ordering vs Stage 9.1.2-2 corrigendum; if 9.1.2-2 already landed and bumped to v0.2.4, this cycle bumps v0.2.4 → v0.2.5)

---

## §4 5-halt cycle

| Halt | You produce | Advisor disposes |
|---|---|---|
| **H#1 Preload** | Session surface (ID/model/JSONL/cwd) + `git rev-parse HEAD` + chain-length verification (expected 0 or 1 SHAs from `5b7019f`) + `git status --short` (8-10 `??` files; verify composition + drift per Q-9.4.5-19) + tracking-status verification of 3 paired artifacts (ports-architecture.md / port-contracts.md / test-strategy.md / pipeline-stage9.md) per `feedback_preload_tracking_status_verification` + Read `_bmad-output/planning-artifacts/Verdaca/adr-9.2-v6-corrigendum-draft.md` (substance template) + Read ports-architecture.md current v0.6 substance + Read port-contracts.md §4 ADR-9.1.2-4 current substance for §3.3 disposition input + halt-class echo + cosmetic-immutable lineage echo + subject-line proposal | GO / amendments / HALT |
| **H#2 Substance design** | Full edit proposals for: (a) ports-architecture.md v0.6 → v0.7 corrigendum banner + G-1 substrate update; (b) port-contracts.md §3.3 disposition (3.3.A or 3.3.B); (c) pipeline-stage9.md cite-bump + substrate header update; (d) test-strategy.md determinations + commit subject (~85-95 char band) + ~180-220 LOC commit body draft (larger than 9.1.2-2 since this is stage-level substrate re-anchor) + F-token strip self-audit on commit subject + body section index | GO / amendments |
| **H#3 Write + verify** | Apply Edits to all targeted files; `git diff --stat` verifies exact scope (gitignored files: no tracked-surface diff; tracked surface diff = pipeline-stage9.md only); F-token grep on commit subject (zero matches); `git status --short` | GO to H#4 |
| **H#4 Commit draft** | Write commit body to `.git/STAGE-9-4-6-PHASE-A-1_COMMIT_MSG.txt` (contains verbatim ADR-9.2-V6 v0.7 corrigendum substance + ADR-9.1.2-4 §3 disposition + paired-sweep evidence); body section index; pre-authorized commit sequence (7 steps) | GO to execute |
| **H#5 Close** | C-SHA + `git log -1 --format=%B <C-SHA>` verification + chain count = +1 from H#1 baseline + `git diff <predecessor>..HEAD --stat` + working-tree state + Phase A.1 → CLOSED (ADR-9.2-V6 v0.7 corrigendum CLOSED; F-9.4.6-FORGE-SEMANTIC-MISFIT close-via-rescope; substrate re-anchored to LLMLingua) + hand-back to advisor with Phase A.2 forward-pointer | Hand-back |

Per `feedback_preload_first_gating`: NO substance design at preload; NO writes at design halt; NO commits before commit-draft halt GO.

---

## §5 Halt-class boundaries

| Category | Disposition |
|---|---|
| `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md` | READ + EDIT v0.6 → v0.7 (substance-of-record will live in commit body per gitignore-caveat) |
| `_bmad-output/implementation-artifacts/verdaca/stage9/port-contracts.md` | READ + conditional EDIT per §3.3 disposition |
| `_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md` | READ + conditional EDIT per §3.4.2 determinations |
| `docs/pipeline-stage9.md` | READ + EDIT + COMMIT (tracked surface) |
| `_bmad-output/planning-artifacts/Verdaca/adr-9.2-v6-corrigendum-draft.md` | READ ONLY (substance template; don't edit the planning artifact) |
| `_bmad-output/planning-artifacts/Verdaca/decision-2-substrate-frame.md` | READ ONLY (Mary's substrate frame; reference for substance context) |
| All port files (`ports/src/praxis/ports/*.py`) | READ-ONLY (Phase A.2 territory) |
| `ports/src/praxis/ports/compaction.py` | DOES NOT EXIST YET; do NOT create this cycle (Phase A.2 territory) |
| Adapter source files (`adapters/**/*.py`) | READ-ONLY (Phase B.1 territory) |
| Contract tests (`tests/**/*.py`) | READ-ONLY (Phase B.2 territory) |
| Substrate (`kernel/**`, `praxis.kernel.*`) | READ-ONLY |
| Repo-root `pyproject.toml` + `tests/pyproject.toml` + `uv.lock` | READ-ONLY (Cleo 9.6 territory) |
| `conftest.py` / meta-test / marker-registration / enforcer | READ-ONLY |
| 22-entry no_waiver allow-list | UNTOUCHED (LLMLingua allow-list scope determined at Phase A.2; this cycle makes ZERO allow-list mutations) |
| Memory files | ADVISOR-ONLY — ZERO writes (per `feedback_memory_authorization`) |
| Stage 9.4.6 gate-clearance deliverables (3 reports in working tree) | PRESERVE VERBATIM |
| Stage 9.1.2-2 corrigendum cycle artifacts (if landed first) | PRESERVE VERBATIM; do NOT touch |
| 4 baseline `??` files | PRESERVED VERBATIM |
| Historical commits | IMMUTABLE (no --amend, no --no-verify, no --no-gpg-sign) |
| Chain at predecessor SHA | APPEND-ONLY → +1 SHA at your H#5 hand-back |
| Stage 9.4.7 territory (repo restructure) | OUT OF SCOPE — DO NOT MENTION |

---

## §6 Discipline carry-forward (load at H#1)

| Memory | Purpose |
|---|---|
| `feedback_preload_first_gating` | Five halt-point structure; no shortcut to any subsequent halt before advisor GO |
| `feedback_memory_authorization` | ZERO memory writes this cycle |
| `feedback_session_surface_audit` | Declare session ID/model/JSONL/cwd at H#1 |
| `feedback_preload_tracking_status_verification` | Verify tracking status of paired artifacts at H#1; gitignored substance authority is commit body per `de365ff` precedent (re-confirmed at 9.4.6 gate-clearance E1-H1) |
| `feedback_handover_template_discipline` | Path-of-record + section-role + SHA-resolvability verification at H#1 (NEW memory, captures handover-template lineage class from 9.4.6 gate-clearance) |
| `feedback_no_waiver_discipline` | 22-entry allow-list untouched |
| `feedback_corrigendum_paired_sweep` | Paired sweep across pipeline + port-contracts + ports-architecture + test-strategy; corrigendum body holds substance-of-record for gitignored artifacts |
| `feedback_concurrent_executor_orchestration` | If Stage 9.1.2-2 cycle is concurrent, halt-class boundaries are disjoint; surface working-tree drift per Q-9.4.5-19 (NEW memory, 9.4.6 precedent) |
| `feedback_advisor_executor_model_effort` | Model + effort set by advisor; do not change |
| `feedback_go_with_amendments_tracked` | All advisor amendments come with verbatim ledger; apply exactly as instructed |
| `feedback_provenance_pin` | §provenance table in commit body |
| `project_verdaca_stage9_2` | Original ports-architecture.md v0.2 binding (pre-falsification baseline) |
| `project_verdaca_stage9_4_3` | Mem0 §3.6 corrigendum precedent (f843d44 commit-body-as-authority pattern) |
| `project_verdaca_stage9_4_5` | LLM-Proxy §3.7 + H2-falsification precedent at ADR-9.2-V5 v0.6 (closest substrate-fit-falsification sibling) |

---

## §7 F-token discipline

### Forbidden in pipeline line text
- F-class status declarations as bare claims (e.g., `[x] CompactionPort substrate — F-9.4.6-FORGE-SEMANTIC-MISFIT RETIRED-FALSIFIED`)

### Acceptable in pipeline line text
- F-tokens in citation-chain context (e.g., `corrigendum closing F-9.4.6-FORGE-SEMANTIC-MISFIT at <SHA>` per Q-9.4.5-20 refined interpretation; sibling-precedent at eccc307 line 276 + 5b7019f line 281)

### Acceptable in commit body
- F-tokens unrestricted in commit body §F-docket + §3 F-class lifecycle + §provenance + anywhere else (de365ff / b0c333c / f843d44 / 2043563 / 5b7019f precedent)

### F-class lifecycle table required in commit body
Capture verbatim:

| F-class ID | Pre-A.1 status | Post-A.1 status | Notes |
|---|---|---|---|
| F-9.4.6-FORGE-IDENTITY-DRIFT-1 | DECLARED | DECLARED-RETIRED-FALSIFIED | Substrate no longer Forge; preserved for audit trail |
| F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE | DECLARED | DECLARED-RETIRED-FALSIFIED | Downstream surface of semantic misfit; preserved |
| F-9.4.6-FORGE-SEMANTIC-MISFIT | DECLARED (root) | DECLARED-CLOSED-VIA-RESCOPE | Substrate re-anchored; close-via-rescope per 9.4.5 RTK precedent |
| F-9.4.6-FORGE-LOCAL-DUMP-SHA-NOT-GIT-REF | DECLARED (cosmetic) | DECLARED-CARRY-FORWARD-COSMETIC | Doc-tooling cosmetic, surfaces in close memo §F-docket |
| F-9.4.6-HANDOVER-PATH-DRIFT-1 | CANDIDATE | CANDIDATE-CARRY-FORWARD | Carry to close memo |
| F-9.4.6-HANDOVER-§3.6-FRAMING-DRIFT-1 | CANDIDATE | CANDIDATE-CARRY-FORWARD | Sibling to PATH-DRIFT-1 |
| F-9.4.6-A1J1-COMMON-MSG-XREF-COSMETIC-01 | CANDIDATE | CANDIDATE-CARRY-FORWARD | Cosmetic; common-port docstring §0.5 vs §3.7 |
| F-9.4.6-LLMLINGUA-MAINTENANCE-STALENESS-1 | CANDIDATE (NEW) | CANDIDATE-MONITORING | Threshold: >12 mo without commit/release |

### Self-audit at H#2 substance design
- Grep proposed pipeline-stage9.md line text for F-tokens; classify each hit as status-declaration (REMOVE) or citation-chain (ACCEPT + surface as AM candidate)
- Zero matches in commit-subject expected

---

## §8 Commit-body substance-of-record discipline

Because `_bmad-output/...` is gitignored, corrigendum substance is captured in the commit-message body. This is the Option D-refined pattern from `de365ff` precedent + re-confirmed across 9.4.3/9.4.4/9.4.5.

**Commit body structure expected (~180-220 LOC):**

1. **Subject** (~85-95 char band, F-token-stripped): `docs: 9.4.6 Phase A.1 — ADR-9.2-V6 v0.7 substrate re-anchor (Forge → LLMLingua)`
2. **§1 Scope** — what closes (4 F-class transitions; substrate re-anchor)
3. **§2 Predecessor + chain** — predecessor SHA, chain count, target chain count
4. **§3 ADR-9.2-V6 v0.7 corrigendum substance (verbatim)** — full §1-§9 from `_bmad-output/planning-artifacts/Verdaca/adr-9.2-v6-corrigendum-draft.md`
5. **§4 ADR-9.1.2-4 §3 disposition (3.3.A or 3.3.B per H#2)** — verbatim substance if 3.3.A
6. **§5 Paired sweep** — pipeline-stage9.md cite-bump + test-strategy.md + port-contracts.md determinations
7. **§6 F-class lifecycle** — table from §7 above
8. **§7 Halt-class hold** — verify carry-forward
9. **§provenance** — predecessor SHA, advisor disposition trail, decision lineage, source artifacts
10. **§8 Next phase** — Phase A.2 forward-pointer (`ports/compaction.py` Protocol authoring); NOT this cycle

---

## §9 Memory writes: ZERO

Per `feedback_memory_authorization`: executor performs ZERO memory writes during halt-cycle. If memory-worthy state surfaces, surface at H#5 hand-back; advisor handles post-cycle under explicit team-lead authorization.

---

## §10 Reference paths

- **Substance template (advisor-authored):** `_bmad-output/planning-artifacts/Verdaca/adr-9.2-v6-corrigendum-draft.md`
- **Substrate decision rationale:** `_bmad-output/planning-artifacts/Verdaca/decision-2-substrate-frame.md` (Mary survey)
- **Predecessor commit body:** `git log -1 --format=%B 5b7019f`
- **Closest sibling precedents:**
  - `git log -1 --format=%B 2043563` — Stage 9.4.5 Phase A.3 (ADR-9.2-V5 v0.6 H2-falsification — RTK retired-falsified; closest substrate-fit-falsification sibling)
  - `git log -1 --format=%B de365ff` — Stage 9.4.5 Phase A.1 (gitignore-caveat substance-of-record pattern)
- **Gate-clearance source reports:**
  - `docs/stage-9.4.6-a.1-john-1-audit-report.md` (E1 audit — serialization gap, but informational only)
  - `docs/stage-9.4.6-g1-license-audit.md` (E2 scout — Forge license + 3 F-class surfacing)
  - `docs/stage-9.4.6-docker-readiness.md` (E2 scout — Docker probe + F-9.4.6-FORGE-NO-UPSTREAM-DOCKER-IMAGE evidence)
- **Substance source (gitignored):** `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md` + `port-contracts.md` + `test-strategy.md`
- **Tracked surface:** `docs/pipeline-stage9.md`
- **Project CLAUDE.md:** project root
- **Memory dir:** `~/.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/memory/`

---

## §11 Dispatch confirmation

Upon receiving this handover:
1. Self-launch H#1 preload immediately (handover IS the dispatch per `feedback_preload_first_gating`)
2. Surface H#1 preload report to user/team-lead, who relays to advisor (main chat window)
3. Wait for explicit advisor GO before H#2 substance design
4. Apply preload-first gating at every halt point — no shortcuts
5. ZERO `--no-verify` / `--no-gpg-sign` / `--amend` (per `feedback_advisor_executor_model_effort` + halt-class boundaries)
6. If Stage 9.1.2-2 corrigendum cycle is concurrent in another executor window: per `feedback_concurrent_executor_orchestration`, halt-class boundaries are disjoint (Stage 9.1.2-2 owns SerializationPort substance; you own CompactionPort substrate substance); surface cross-stream artifacts in working tree at every halt per Q-9.4.5-19

End of Stage 9.4.6 Phase A.1 Executor handover. Standing by for self-launched H#1 preload.
