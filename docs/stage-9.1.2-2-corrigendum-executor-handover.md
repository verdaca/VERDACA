# Stage 9.1.2-2 — Serialization §3 Corrigendum Executor Handover

**Persona:** Amelia (executor)
**Predecessor:** `5b7019f` (Stage 9.4.5 RATIFIED close-handoff; 2026-05-12)
**Chain at HEAD:** 24-SHA; target 25+-SHA at corrigendum landing
**Authorized model:** Sonnet 4.6 medium (substance-heavy single-phase cycle)
**Scope class:** Dedicated Stage 9.1.2-2 corrigendum cycle (NOT 9.4.6 Phase A.1; insulated per advisor [E1-H5 → CLOSED] Decision 1 disposition)

---

## §1 Authorization scope

This handover authorizes ONE corrigendum cycle: land Stage 9.1.2-2 serialization §3 DTO PINNING corrigendum, closing two DECLARED F-class IDs from the A.1-JOHN-1 audit:

- **F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01** — RoundtripFuzzReport class body absent from port-contracts.md §2 §3 Decision (referenced as return type at line 334; 4 fields introduced in `ports/src/praxis/ports/serialization.py` without ADR pinning)
- **F-9.4.6-A1J1-SER-JSONVALUE-PINNING-01** — JsonValue PEP 695 type alias absent from §3 as typed declaration (inline comment only at port-contracts.md line 337; port code line 50 introduces novel recursive type)

**Out of scope this cycle:** Forge CompactionPort (9.4.6 Phase A.1) — BLOCKED on independent ADR-9.2-V6 re-anchor decision; advisor authoring; NOT touched by this cycle.

---

## §2 Predecessor + chain

- **Predecessor SHA:** `5b7019f` (Stage 9.4.5 RATIFIED close-handoff; 2026-05-12)
- **Chain at HEAD:** 24-SHA
- **Target at hand-back:** 25+-SHA (this cycle commits at least 1 corrigendum SHA)
- **Working-tree baseline at start:** likely 7 `??` carried from Stage 9.4.6 gate-clearance:
  - `docs/epam-security-clearance-email-draft.md` (baseline)
  - `docs/openclaw-setup-guide.md` (baseline)
  - `docs/stage-9.4.6-handover-advisor.md` (baseline)
  - `docs/stage-9.4.6-handover-executor.md` (baseline)
  - `docs/stage-9.4.6-a.1-john-1-audit-report.md` (E1 deliverable)
  - `docs/stage-9.4.6-g1-license-audit.md` (E2 deliverable)
  - `docs/stage-9.4.6-docker-readiness.md` (E2 deliverable)
  - + this handover at `docs/stage-9.1.2-2-corrigendum-executor-handover.md` (NEW)

Verify exact count at H#1; surface drift per Q-9.4.5-19.

---

## §3 Substance scope — the corrigendum

### §3.1 Substance source authority

Per `feedback_preload_tracking_status_verification` + `feedback_handover_template_discipline`:

- **Local file (best-available substance):** `_bmad-output/implementation-artifacts/verdaca/stage9/port-contracts.md` (gitignored at `.gitignore:30` via `_bmad-output/`)
- **Authoritative on divergence:** corrigendum-of-record commit-message body per `de365ff` precedent

Because `port-contracts.md` is gitignored, the corrigendum substance MUST be captured in the commit-message body of THIS cycle's commit. The local file is updated as best-available substance (your edits land there for team-lead's working file), but the **commit body is the authoritative version-controlled snapshot**.

### §3.2 Substance — F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01 close

Add `RoundtripFuzzReport` class body to port-contracts.md §2 (ADR-9.1.2-2) §3 Decision section. Source the 4 fields from `ports/src/praxis/ports/serialization.py` verbatim:

- `sample_count: int`
- `seed: int`
- `samples_passed: int`
- `encoding_format: str`

(Verify exact field types + ordering by reading the port file at H#2 substance design.)

Format mirroring the existing §3 DTO bodies in §2 (e.g., SerializablePayload, EncodedBytes) for stylistic consistency.

### §3.3 Substance — F-9.4.6-A1J1-SER-JSONVALUE-PINNING-01 close

Pin the JsonValue PEP 695 type alias as an explicit declaration in port-contracts.md §2 §3:

```python
type JsonValue = bool | int | float | str | None | list[JsonValue] | dict[str, JsonValue]
```

(Verify exact syntax by reading `ports/src/praxis/ports/serialization.py` line 50 at H#2.)

Replace the existing inline comment (line 337 of port-contracts.md: `# JsonValue = recursive primitive type`) with the typed declaration.

### §3.4 Doc-version bumps

- **§2 ADR-9.1.2-2 status header:** v0.2 → v0.2.1 with corrigendum lineage cite (e.g., "v0.2.1 corrigendum (2026-05-13): §3 expanded with RoundtripFuzzReport + JsonValue PINNING — F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01 + F-9.4.6-A1J1-SER-JSONVALUE-PINNING-01 close")
- **Doc-level version (port-contracts.md line 4):** v0.2.3 → v0.2.4 reflecting accumulated corrigenda

### §3.5 Paired sweep (per `feedback_corrigendum_paired_sweep`)

Identify cite locations in the 3 paired artifacts and bump as needed:

1. **`docs/pipeline-stage9.md`** (TRACKED — edit + commit)
   - Locate Stage 9.1.2-2 line(s); add corrigendum cite if pipeline tracks ADR corrigendum lineage
   - Add 9.4.6-prerequisite line if not present (gate-clearance precedent)
2. **`_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md`** (likely GITIGNORED — verify at H#1; if gitignored, capture cite-bump in commit body)
   - Locate any MAC-T entries referencing serialization DTOs (e.g., M-T-SER-* IDs)
   - Update if RoundtripFuzzReport / JsonValue PINNING introduces new test surface; if no new test surface needed, document the determination explicitly
3. **`_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md`** (GITIGNORED — same handling)
   - Locate §-references to SerializationPort DTO surface
   - Update if §3.1 + §3.2 surface changes; document determination

Surface tracking status of each paired artifact at H#1; per `feedback_preload_tracking_status_verification`, gitignored substance lives in commit body.

---

## §4 5-halt cycle

| Halt | You produce | Advisor disposes |
|---|---|---|
| **H#1 Preload** | Session surface (ID/model/JSONL/cwd) + `git rev-parse HEAD` matches `5b7019f` + `git log --oneline -24` confirms chain + `git status --short` (expected 8 `??` per §2 above; verify) + tracking-status verification for port-contracts.md / test-strategy.md / ports-architecture.md / pipeline-stage9.md + read §2 ADR-9.1.2-2 verbatim at port-contracts.md lines 313-358 + read serialization.py for DTO + JsonValue surface + halt-class echo + cosmetic-immutable lineage echo + subject-line proposal | GO / amendments / HALT |
| **H#2 Substance design** | Full edit proposals for: (a) port-contracts.md §2 §3 RoundtripFuzzReport addition; (b) §2 §3 JsonValue typed declaration; (c) §2 status header v0.2 → v0.2.1; (d) doc-level v0.2.3 → v0.2.4; (e) pipeline-stage9.md cite-bump; (f) test-strategy.md + ports-architecture.md cite-bump determinations + commit subject (~85-95 char band) + ~140-LOC commit body draft mirroring sibling skeleton (de365ff / f843d44 for gitignored-substance pattern) + F-token strip self-audit on commit subject + body section index | GO / amendments |
| **H#3 Write + verify** | Apply Edits to all targeted files; `git diff --stat` verifies exact scope (port-contracts.md gitignored — no diff in tracked surface for that file; tracked surface diff = pipeline-stage9.md + commit body holding ADR substance); F-token grep on commit subject (zero matches); `git status --short` | GO to H#4 |
| **H#4 Commit draft** | Write commit body to `.git/STAGE-9-1-2-2-CORRIGENDUM_COMMIT_MSG.txt` (contains the §3.2 RoundtripFuzzReport body + §3.3 JsonValue declaration + paired-sweep cite captures); body section index; pre-authorized commit sequence (7 steps: stage paired-tracked files → commit with `--file=...` → verify SHA + status) | GO to execute |
| **H#5 Close** | C-SHA + `git log -1 --format=%B <C-SHA>` verification + chain count = 25-SHA + `git diff <predecessor>..HEAD --stat` + working-tree state + Phase → CLOSED (Stage 9.1.2-2 corrigendum CLOSED; F-FUZZREPORT-01 CLEARED; F-JSONVALUE-01 CLEARED) + hand-back to advisor | Hand-back |

Per `feedback_preload_first_gating`: NO substance design at preload; NO writes at design halt; NO commits before commit-draft halt GO. Each halt is its own boundary.

---

## §5 Halt-class boundaries

| Category | Disposition |
|---|---|
| `ports/src/praxis/ports/serialization.py` | READ for substance (DTO + type alias verification at H#1/H#2) |
| `ports/src/praxis/ports/{memory,cost_meter,common}.py` | READ-ONLY (NOT this cycle's scope) |
| `_bmad-output/implementation-artifacts/verdaca/stage9/port-contracts.md` | READ for substance + EDIT §2 §3 + status header + doc-level version (substance-of-record will live in commit body per gitignore-caveat) |
| `_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md` | READ for paired-sweep substance + possible EDIT (if gitignored, cite-bump determination captured in commit body) |
| `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md` | READ for paired-sweep substance + possible EDIT (same handling) |
| `docs/pipeline-stage9.md` | READ for paired-sweep substance + EDIT + COMMIT (tracked surface) |
| `docs/adr-*.md` (other ADRs) | OUT OF SCOPE (do not touch) |
| Adapter source files (`adapters/**/*.py`) | READ-ONLY |
| Contract tests (`tests/**/*.py`) | READ-ONLY (no test additions this cycle; new MAC-Ts deferred to Phase B.2 of 9.4.6 OR future Stage 9.6 cleanup, advisor scope) |
| Substrate (`kernel/**`, `praxis.kernel.*`) | READ-ONLY |
| Repo-root `pyproject.toml` + `tests/pyproject.toml` + `uv.lock` | READ-ONLY (Cleo 9.6 territory) |
| `conftest.py` / meta-test / marker-registration / enforcer | READ-ONLY |
| 22-entry no_waiver allow-list | UNTOUCHED (NO mutations this cycle; allow-list discipline per `feedback_no_waiver_discipline`) |
| Memory files | ADVISOR-ONLY — ZERO writes (per `feedback_memory_authorization`) |
| Stage 9.4.6 deliverables in working tree (audit report + license + docker readiness) | PRESERVE VERBATIM (do not touch; cross-cycle artifacts from CLOSED gate-clearance cycles) |
| 4 baseline `??` files | PRESERVED VERBATIM |
| Historical commits | IMMUTABLE (no --amend, no --no-verify, no --no-gpg-sign) |
| 24-SHA chain | APPEND-ONLY → 25-SHA at your H#5 hand-back |
| Stage 9.4.7 territory | OUT OF SCOPE — DO NOT MENTION |

---

## §6 Discipline carry-forward (load at H#1)

| Memory | Purpose |
|---|---|
| `feedback_preload_first_gating` | Five halt-point structure; NO shortcut to any subsequent halt before advisor GO |
| `feedback_memory_authorization` | ZERO memory writes this cycle |
| `feedback_session_surface_audit` | Declare session ID/model/JSONL/cwd at H#1 |
| `feedback_preload_tracking_status_verification` | Verify tracking status of port-contracts.md + test-strategy.md + ports-architecture.md + pipeline-stage9.md at H#1; gitignored substance authority is commit body per `de365ff` precedent |
| `feedback_handover_template_discipline` | Path-of-record + section-role + SHA-resolvability verification at H#1 |
| `feedback_no_waiver_discipline` | 22-entry allow-list untouched |
| `feedback_corrigendum_paired_sweep` | Paired sweep across test-strategy + port-contracts + ports-architecture + pipeline; corrigendum body holds substance-of-record for gitignored artifacts |
| `feedback_advisor_executor_model_effort` | Model + effort set by advisor; do not change |
| `feedback_go_with_amendments_tracked` | All advisor amendments come with verbatim ledger; apply exactly as instructed |
| `feedback_provenance_pin` | §provenance table in commit body |
| `project_verdaca_stage9_4_3` | Mem0 §3.6 corrigendum precedent (f843d44 commit-body-as-authority pattern) |
| `project_verdaca_stage9_4_4` | cost_meter §3.6 corrigendum precedent (b0c333c OPENS-and-CLOSES single-commit pattern; closest sibling to this cycle's substance pattern) |
| `project_verdaca_stage9_4_5` | LLM-Proxy §3.7 + Message DTO sibling-add precedent (de365ff) |
| `project_verdaca_stage9_2` | ports-architecture.md v0.2 binding (baseline DTO surface reference) |

---

## §7 F-token discipline

### Forbidden in pipeline line text
- F-class status declarations as bare claims (e.g., `[x] serialization §3 corrigendum — F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01 CLOSED`)

### Acceptable in pipeline line text
- F-tokens in citation-chain context (e.g., `corrigendum closing F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01 at <SHA>` per Q-9.4.5-20 refined interpretation)

### Acceptable in commit body
- F-tokens unrestricted in commit body §F-docket + §3 F-class lifecycle + §provenance + anywhere else (de365ff / b0c333c / f843d44 precedent)

### Self-audit at H#2 substance design
- Grep proposed pipeline-stage9.md line text for F-tokens; classify each hit as status-declaration (REMOVE) or citation-chain (ACCEPT + surface as AM-X-N candidate for advisor disposition)
- Zero matches in commit-subject expected after self-audit

---

## §8 Commit-body substance-of-record discipline

Because port-contracts.md is gitignored, the corrigendum substance is captured in the commit-message body. This is the Option D-refined pattern from `de365ff` precedent.

**Commit body structure expected:**

1. **Subject** (~85-95 char band, F-token-stripped): `docs: 9.1.2-2 serialization §3 corrigendum — RoundtripFuzzReport + JsonValue PINNING`
2. **§1 Scope** — what closes (2 F-class IDs)
3. **§2 Predecessor + chain** — predecessor SHA, chain count, target chain count
4. **§3 Substance — RoundtripFuzzReport class body** — verbatim
5. **§3a Substance — JsonValue typed declaration** — verbatim
6. **§4 Doc-version bumps** — §2 v0.2 → v0.2.1; doc-level v0.2.3 → v0.2.4
7. **§5 Paired sweep** — pipeline-stage9.md cite-bump (tracked); test-strategy.md + ports-architecture.md determinations
8. **§6 F-class lifecycle** — F-9.4.6-A1J1-SER-FUZZREPORT-PINNING-01 OPENED-and-CLOSED; F-9.4.6-A1J1-SER-JSONVALUE-PINNING-01 OPENED-and-CLOSED (mirror b0c333c single-commit OPEN-and-CLOSE pattern)
9. **§7 Halt-class hold** — verify carry-forward
10. **§provenance** — predecessor SHA, advisor disposition trail, cycle effort
11. **§8 Next stage** — 9.4.6 Phase A.1 launch eligibility pending ADR-9.2-V6 re-anchor (advisor scope; not this cycle)

Total body target: ~140-180 LOC (mirrors b0c333c sibling).

---

## §9 Memory writes: ZERO

Per `feedback_memory_authorization`: executor performs ZERO memory writes during halt-cycle. If memory-worthy state surfaces, surface at H#5 hand-back; advisor handles post-cycle.

---

## §10 Reference paths

- **Predecessor commit body**: `git log -1 --format=%B 5b7019f`
- **Sibling close-handoff templates** (commit-body-as-substance-of-record pattern):
  - `git log -1 --format=%B f843d44` — Stage 9.4.3 Phase A.1 (Memory port §3.6 corrigendum — first gitignore-caveat precedent)
  - `git log -1 --format=%B b0c333c` — Stage 9.4.4 (cost_meter §3.6 corrigendum — closest sibling, single-commit OPEN-and-CLOSE pattern)
  - `git log -1 --format=%B de365ff` — Stage 9.4.5 Phase A.1 (LLM-Proxy §3.7 + Message DTO sibling-add — most recent precedent)
- **Audit source**: `docs/stage-9.4.6-a.1-john-1-audit-report.md` (E1 deliverable at working tree; SerializationPort findings at §2.3 + §3 disposition + §5 recommendations)
- **Substance source (gitignored)**: `_bmad-output/implementation-artifacts/verdaca/stage9/port-contracts.md`
- **Paired artifacts**:
  - `_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md`
  - `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md`
  - `docs/pipeline-stage9.md` (tracked)
- **Port code**: `ports/src/praxis/ports/serialization.py`
- **Project CLAUDE.md**: project root
- **Memory dir**: `~/.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/memory/`

---

## §11 Dispatch confirmation

Upon receiving this handover:
1. Self-launch H#1 preload immediately (handover IS the dispatch per `feedback_preload_first_gating`)
2. Surface H#1 preload report to user/team-lead, who relays to advisor (main chat window)
3. Wait for explicit advisor GO before H#2 substance design
4. Apply preload-first gating at every halt point — no shortcuts
5. ZERO `--no-verify` / `--no-gpg-sign` / `--amend` (per `feedback_advisor_executor_model_effort` + halt-class boundaries)

End of Stage 9.1.2-2 Corrigendum Executor handover. Standing by for self-launched H#1 preload.
