# Advisor handover — Stage 9.4.2-internal step 7 (2026-05-01 → next session)

## Role

You are the advisor for Verdaca Stage 9.4.2-internal step 7 (TONL adapter MAC-T authoring). Working directory: `C:\Users\AndreyPopov\Documents\Anthropic`. Active stage workspace: `_bmad-output/implementation-artifacts/verdaca/stage9/`.

The executor runs in a parallel context window — you review, spot-check, and authorize their work but do NOT write code, binding artifacts, or memory directly. The team-lead (Andrey) routes messages between you and the executor.

## State as of 2026-05-01 (HEAD = `5f34ae7`)

### 9.4.2-pre — FULLY CLOSED. 9.4.2-internal step 7 — NEXT.

5-commit close arc on `main`: `439c0b7 → 3fe343f → d9d4cf0 → 1ce354e → 5f34ae7`. Full disposition + F-dockets in `session-handoff-20260430-stage9.4.2-pre-close.md`.

### Read-first (in this order)

1. `_bmad-output/planning-artifacts/Verdaca/session-handoff-20260430-stage9.4.2-pre-close.md` (close-handoff at `5f34ae7`) — F-dockets (F6–F10), parked items, §7 preload checklist that the executor will run.
2. `_bmad-output/planning-artifacts/Verdaca/stage9.4.2-pre-bootstrap-memo.md` (bootstrap memo + corrigendum addenda).
3. `_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md` v0.2 §2.2.2 (Serialization Port (ADR-2) — 12 MAC-Ts) — resumption scope; verify before adjudicating step-7 approach.
4. Memory files just landed in this session: `feedback_provenance_pin.md`, `feedback_session_surface_audit.md`.
5. Companion executor handover: `session-handoff-20260501-stage9.4.2-internal-executor.md`.

## Step 7 — what to expect from the executor

Executor will surface:
1. **Preload report** (6 items per close-handoff §7 + this handoff's checklist). You review env state + verify §2.2.2 cite + confirm 12 MAC-T IDs pinned. Halt for your go.
2. **MAC-T authoring approach** (test-file naming, test-design strategy, fixture/parametrization plan). You adjudicate approach. Halt for your go.
3. **Implementation** (test code + any adapter scaffold tweaks). You review for contract correctness, idiom, no §9.C-shape regressions. Halt before commit.
4. **Commit draft** (subject + body + scope). You review subject ≤ 70 chars envelope, body accuracy, scope correctness. Halt for your go.
5. **SHA after commit.** You close.

Authorize each phase explicitly. Do not bulk-go.

## Adjudication priorities

- **Per-item gating** (per `feedback_memory_authorization.md`): NEVER bulk-go on multi-content. Each MAC-T review, each commit, each artifact write needs its own per-item go. The executor will halt at every step; respect the cadence.
- **Cite-pinning discipline** (F6 lesson): when reviewing the executor's preload + drafts, watch for paraphrases of file:line cites. Propagated unverified inference is a recurring failure mode. Verify verbatim cites before approving — even ones that "look right." F6 itself was the canonical example of this failure shape; this session's close-handoff §7 cite verification (`(ADR-2)` paraphrase) was the second-order recurrence within the same artifact authoring it. The discipline is fragile under fatigue.
- **Count-from-the-list** (session experience): when reviewing tallies, recount from the actual list, not from narrative labels. Even short lists produced count errors this session. Two count slips (24 not 23 tests; 23 not 22 source files) cascaded through R-set adjudications before being caught at pre-commit.
- **Forward-only closes**: if a post-close defect surfaces (F8 shape), authorize corrigendum-on-top, NOT charter reopen. The 9.4.2-pre.1 corrigendum at `d9d4cf0` is the precedent.
- **Pre-stamp reproducibility audit** (parked memory candidate `feedback_pre_stamp_reproducibility_audit.md`): at any stamp gate touching env-foundational state, request a `git show <close-SHA>:<path>` enumeration from clean-clone vantage BEFORE stamping. F8 would have been caught at the `3fe343f` stamp gate. Apply the discipline informally until the memory is written.

## Standing precedents from prior session

- **Two-stamp shape:** parent (substance) → stamp (records parent SHA only). Stamp's own SHA lives in `git log` of memo file. Don't recommend self-reference rows in close-memo §provenance — `1ce354e` explicitly trimmed an over-engineered one this session.
- **Corrigendum-on-closed-charter pattern:** structural-completeness defects landed via corrigendum commit + dedicated stamp; closed charter's commit and memo stay unedited. 9.4.1 close at `934f5ea` precedent: substance retroactively tracked under 9.4.2-pre.1, but 9.4.1 close memo NOT edited.
- **F-docket landing in dated session-handoff close artifacts:** matches F1–F5 precedent; not a separate standing docket file. Default to (1)(a) framing when this surfaces.
- **MEMORY.md index discipline:** entry is one-line `- [Title](file.md) — hook` form, under ~150 chars. Two entries landed this session (lines 20–21).
- **Three-section F-docket shape:** Body / Disposition / Forward action, with optional subordinated "Underlying gap:" sentence inside Forward action. Template robust to absence — F9 and F10 used it without the subordinated observation.

## Watch-fors at step 7 close

- **F8-shape gap recurrence.** Step 7 will track new test files. Verify they're in the post-corrigendum visible directories (`tests/src/praxis/contract_tests/ports/`) and that the close commit reproduces the claimed test state from clean-clone vantage. The pre-stamp reproducibility audit applies here.
- **Cite-pinning discipline at executor's preload time.** The §9.C cite is the canonical example — should always be `playbook addenda §9.C (04-26 handoff lines 199–203, operationalized at 04-28 lines 59–66)`, never `test-strategy.md §9.C`. Reject the latter on sight.
- **New gitignore-shadow during step-7 substance authoring.** If any F9-shape collision surfaces (a path silently invisible to git despite being on disk), halt the executor and adjudicate before they auto-resolve.
- **F10 architectural surfacing.** If step-7's MAC-T authoring touches `praxis.kernel.*` namespace shape, halt — F10 is parked for Stage 9.5 review, not for step-7 in-passing remediation.

## Parked items requiring review-then-go on revisit

- **`feedback_pre_stamp_reproducibility_audit.md` candidate** — first-mover authoring discipline; address in the next charter-close session that would benefit from the discipline being formalized. Prior session left a draft sketch in close-handoff §5 (contextual, not durable).
- **F9 audit** — Windows case-fold `.gitignore` landmine; separate audit session; F9 docket entry §3.4 has the recipe (audit `_bmad/`, `_bmad-output/`, `.claude/`, `Articles/`, `CLAUDE.md`, `claude-setup-reference.md` for case-fold collisions via `find . -type d -iname '<pattern>'`).
- **F10 architectural review** — `praxis.kernel` package-shape asymmetry; Stage 9.5 architectural review session; F10 docket entry §3.5 has the verification recipe + reconciliation options.
- **`docs/pipeline-stage9.md` modification** — pre-existing M, deferred; git-archaeology session.

## Disciplines learned this session (apply forward)

- **"Physician heal thyself."** When issuing N-style notes about discipline, immediately apply them to your own reasoning. (This session: N2 cite-discipline issued in same turn that propagated a count error; F6 cite-pinning forward action issued in artifact that elided `(ADR-2)`.) Discipline notes are not exemptions from the discipline.
- **Halt-on-discrepancy beats apply-then-fix.** Executor's halt on count discrepancy in the corrigendum draft saved a permanent record-error. Reward the halt; don't pressure past it.
- **Authoring vs adjudication.** When you're reviewing in-thread drafts, don't author content yourself — that crosses the role boundary and you lose review independence. (This session: I authored draft memory content as "advisor", which was caught and rolled back. Pattern not to repeat.)
- **`(ADR-2)` lesson.** Twelve characters of literal accuracy is worth a round-trip when the artifact is the discipline's own home. Apply it forward.

## Out of scope for step 7

- F9 audit, F10 architectural review, `feedback_pre_stamp_reproducibility_audit.md` authoring, `docs/pipeline-stage9.md` git-archaeology — all parked.
- Step 7 is TONL adapter MAC-T authoring per §2.2.2 only. No scope expansion.
- The 04-29 EOD F3/F5 disposition stack — closed; do not re-litigate.

## Provenance (this handover)

- Authored: 2026-05-01
- Session JSONL: `~/.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/69f1a342-ab3a-4e66-9df9-df20cff7a15f.jsonl`
- Model: `claude-opus-4-7[1m]`
- Working dir: `C:\Users\AndreyPopov\Documents\Anthropic`
- HEAD at write: `5f34ae7`
- Companion handover: `session-handoff-20260501-stage9.4.2-internal-executor.md`
