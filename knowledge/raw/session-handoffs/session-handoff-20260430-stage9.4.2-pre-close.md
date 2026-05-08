# Session Handoff — Stage 9.4.2-pre charter close + 9.4.2-pre.1 corrigendum

**Sub-stage:** 9.4.2-pre — environment-foundational bootstrap (carved out of Stage 9.4.2 step 7 after 04-29 morning halt at §9.C runtime check)
**Status:** **CLOSED** — original charter at `439c0b7` + stamp `3fe343f` (2026-04-30); structural-completeness corrigendum 9.4.2-pre.1 at `d9d4cf0` + stamp `1ce354e` (2026-05-01)
**Author:** Executor (Claude Code CLI session, model `claude-opus-4-7[1m]`) under advisor review
**Companion artifact:** `_bmad-output/planning-artifacts/Verdaca/stage9.4.2-pre-bootstrap-memo.md` (close memo + corrigendum addenda)

---

## §1. Scope summary

**Charter close (2026-04-30).** 9.4.2-pre's 8-step bootstrap charter completed: root `pyproject.toml` workspace declaration (10 members), `.python-version` (3.12.12), `uv.lock` regenerated, `.venv/` provisioned via uv 0.11.2, legacy `praxis-compression` editable retired from system Python311, `_bmad-output/.../praxis/compression/` archived to `_bmad-output/_archive/praxis-pre-rename/`, §9.C runtime check PASS (`isinstance(TONLAdapter(), SerializationPort) == True` under the new env), M-T-VS-* reproducibility smoke 10/10 GREEN, bootstrap memo authored. Two commits landed the close: `439c0b7` (substance + memo) + `3fe343f` (§6 stamp follow-up backfilling parent SHA).

**Structural-completeness corrigendum (2026-05-01).** 04-30 EOD pre-docket-draft verification (advisor request) confirmed three workspace-member pyprojects flagged in memo §2 were absent from the close-commit tree; expanded sweep revealed 5 of 10 declared workspace members entirely invisible to git at `439c0b7` due to two `.gitignore` root causes (root `/*` blocking new top-level dirs; `Memory/` pattern catching `kernel/memory/` via Windows case-fold). 9.4.2-pre.1 corrigendum lands the missing 85 files + fixes both root causes + reconciles memo §2 with actual `[build-system]` state across all 10 declared members + fixes a stale memo-path comment in root `pyproject.toml`. Closes are forward-only — `439c0b7` + `3fe343f` stand; corrigendum is a discovery-driven defect fix on top, not a charter reopen. Two commits landed the corrigendum: `d9d4cf0` (substance + memo edits) + `1ce354e` (§6 stamp).

**Outcome.** Repo at `1ce354e` (HEAD on `main`) has the bootstrap state fully reproducible from a clean clone; `praxis` namespace package aggregates 10 paths; all 10 declared workspace members are tracked + buildable; M-T-VS-* contract tests green under the new env. Working tree clean except for pre-existing `docs/pipeline-stage9.md` modification (deferred to a separate session for git-archaeology).

---

## §2. Timeline (commit ledger)

| SHA | Role | Description |
|---|---|---|
| `439c0b7` | Original close (2026-04-30) | Bootstrap charter close — root pyproject + lockfile + 4 member mods + 4 marker deletions + memo |
| `3fe343f` | Stamp (2026-04-30) | Backfilled memo §6 with `439c0b7` |
| `d9d4cf0` | Corrigendum (2026-05-01) | Structural-completeness fix — 85 file adds + 3 mods (memo + 2 .gitignore + root pyproject comment) |
| `1ce354e` | Stamp (2026-05-01) | Backfilled memo §6 with `d9d4cf0`, dropped self-reference row per `3fe343f` precedent |

Branch state on `main`: `934f5ea → 439c0b7 → 3fe343f → d9d4cf0 → 1ce354e`.

---

## §3. F-docket

### §3.0. Status index

| ID | Title | Disposition |
|---|---|---|
| F6 | Charter §9.C location shorthand | Closed via advisor adjudication (a) on 04-30 |
| F7 | §9.C scope clarification: structural conformance, not nominal inheritance | Classified — non-defect scope clarification |
| F8 | Bootstrap commit structural-completeness gap | Closed via corrigendum `d9d4cf0` + stamp `1ce354e` |
| F9 | Windows case-fold `.gitignore` latent landmine | Open-deferred — separate-session audit |
| F10 | `praxis.kernel` package-shape asymmetry | Open-deferred — Stage 9.5 architectural review |

### §3.1. F6 — Charter §9.C location shorthand

**Body.** The 04-29 EOD charter (`session-handoff-20260429eod-stage9.4.2-pre-executor.md` line 52) directed: *"look up §9.C definition in `test-strategy.md` v0.2 at preload. Use whatever test-strategy.md defines, NOT a paraphrase."* 04-30 preload Item-4 surfaced that `test-strategy.md` v0.2 contains no §9.C section — grep for `9\.C` / `isinstance` / `runtime check` / `SerializationPort` returned zero matches; section 9 there is "Hand-offs" (9.1 Amelia, 9.2 Cleo, etc.). Likewise no §9.C in `port-contracts.md`, `ports-architecture.md`, or `docs/pipeline-stage9.md`. Binding §9.C source is the playbook §9 addenda authored at `session-handoff-20260426-stage9.4.1-amelia-preload.md` lines 199–203 (rule, prose form) and most recently restated verbatim at `session-handoff-20260428-stage9.4.2-executor.md` lines 59–66 (TONL/SerializationPort code block).

**Disposition.** Charter-shorthand-vs-actual-location mismatch — same shape as F3 (`where=["api"]` charter shorthand → actual `where=["."]+include=["api*"]`). Advisor disposition (a) on 04-30: adopt the 04-28 code block as canonical operationalization of the 04-26 binding rule; do not auto-substitute, surface the discrepancy at preload. §9.C runtime check then executed verbatim under the new env (`isinstance(TONLAdapter(), SerializationPort) == True`) — PASS.

**Forward action.** Future charters cite `playbook addenda §9.C (04-26 handoff lines 199–203, operationalized at 04-28 lines 59–66)`, not `test-strategy.md §9.C`. Underlying gap: the §9.A/§9.B/§9.C playbook addenda live only in dated session-handoff files, never landed in a binding artifact. Pre-charter authors pin actual file:line cites for the addenda, not the conceptual reference, to avoid this class of shorthand drift across charters.

### §3.2. F7 — §9.C scope clarification: structural conformance, not nominal inheritance

**Body.** §9.C runtime check (`isinstance(TONLAdapter(), SerializationPort) == True`) executed 04-30 step-6 under the new env — PASS. Inspection of `TONLAdapter.__mro__` returned `[TONLAdapter, object]`; `SerializationPort` does not appear in the MRO. The check passes via `runtime_checkable` Protocol structural matching (attribute/method presence verified at the `isinstance` call), not nominal inheritance through the class tree. Side observation surfaced at the step-6 verify report; advisor disposition: gate as F7 docket candidate, not blocking the charter.

**Disposition.** Scope clarification, not a defect. §9.C verifies *Protocol satisfaction* — that the adapter exposes the methods the port declares — which is the correct check given the V4 in-tree-wrap composition pattern adopted at Stage 9.4.1 (`ports-architecture.md` v0.4 + v0.5 corrigenda). All currently-tracked adapters (Beads at 9.4.1, TONL at 9.4.2 step-7 scaffold) use composition, not inheritance, so §9.C covers them correctly.

**Forward action.** Adapter authors and reviewers recognize that §9.C alone does NOT verify class-tree ancestry. If a future adapter ever needs nominal inheritance from an abstract base for shared default implementations (a pattern not yet adopted), `isinstance` will pass even when the ancestry relationship is missing — that scenario requires an additional explicit ancestry check (e.g., `assert SerializationPort in TONLAdapter.__mro__`) beyond §9.C. Underlying gap: V4 composition is the current architectural pattern; if a future architecture review (e.g., Stage 9.5) ever adopts an inheritance-based pattern, the playbook §9.C addenda will need a paired §9.D-shape addition for ancestry verification. No action required at this charter; flag for adapter-pattern review.

### §3.3. F8 — Bootstrap commit structural-completeness gap

**Body.** 2026-05-01 pre-docket-draft verification (advisor request: spot-check that the close commit reproduces the memo's claimed bootstrap state from a clean-clone vantage) ran `git show 439c0b7:<path>` on three workspace-member pyprojects flagged in memo §2 — `adapters/beads/pyproject.toml`, `kernel/memory/pyproject.toml`, `ports/pyproject.toml`. All three returned `fatal: path '...' exists on disk, but not in '439c0b7'`. Expanded sweep across all 10 declared workspace members (per root pyproject `[tool.uv.workspace] members`) revealed 5 of 10 entirely invisible to git at 439c0b7: `ports/`, `adapters/beads/`, `adapters/tonl/`, `tests/`, `kernel/memory/`. Two distinct `.gitignore` root causes:
- **Cause A — root `/*` blocks new top-level dirs.** Repo-root `.gitignore` line 8 (`/*`) excludes everything at the repo root by default; the bootstrap added `!`-re-includes for the 3 new root-level *files* (`!pyproject.toml`, `!.python-version`, `!uv.lock`) but missed the new top-level *directories* `ports/`, `adapters/`, `tests/`. Everything under those directories was silently ignored — including the 10 binding M-T-VS-* contract tests under `tests/` whose 10/10 GREEN run was reported in memo §4 (running, but invisible to git).
- **Cause B — `Memory/` pattern catches `kernel/memory/` via Windows case-fold.** Repo-root `.gitignore` line 29 (`Memory/`, intended for the project-root `Memory/` workspace folder) lacked a leading `/` anchor and matched `Memory/` anywhere in the tree; Windows `core.ignorecase=true` (default) made the match case-insensitive, so `kernel/memory/` was caught.

**Disposition.** Real structural-completeness gap, not a wording fix. F8 was originally framed as "memo §2 vs disk wording reconciliation" during F-docket pre-resolution; verification revealed both the memo claim AND the disk state (commit tree) were wrong. Closes are forward-only — `439c0b7` (charter close) + `3fe343f` (stamp) stand. Corrigendum 9.4.2-pre.1 (commit `d9d4cf0`, stamp `1ce354e`) lands the missing 85 files (workspace substance previously invisible) + fixes both `.gitignore` root causes + reconciles memo §2 with the actual `[build-system]` state across all 10 declared members + fixes a stale memo-path comment in root `pyproject.toml`. 9.4.1 Beads adapter source and its M-T-VS-* tests are tracked retroactively as 9.4.2-pre.1 substance (substance, not charter — 9.4.1 close at `934f5ea` stands; 9.4.1 close memo unedited per forward-only discipline).

**Forward action.** At any future charter-close stamp gate, run a pre-stamp reproducibility check before the stamp commit lands: enumerate all paths claimed in the close-memo's bootstrap state (e.g., declared workspace members for an env charter) and verify each is present in `git show <close-SHA>:<path>` from a clean-clone vantage. Underlying gap: the original 9.4.2-pre charter had no such verification step; memo §2 was authored against on-disk state without cross-checking commit-tree state, and the `.gitignore` gaps masked the divergence. Captured as future memory candidate `feedback_pre_stamp_reproducibility_audit.md`, parked across sessions for the next charter-close work to author. F9 (Windows case-fold `.gitignore` audit) and F10 (`praxis.kernel` package-shape asymmetry) are downstream observations from F8's investigation — both parked for separate sessions.

### §3.4. F9 — Windows case-fold `.gitignore` latent landmine

**Body.** `.gitignore` patterns lacking leading `/` anchors match same-named directories anywhere in the tree, not just at repo root. On Windows with `core.ignorecase=true` (default), the match is also case-insensitive. F8 surfaced the canonical instance: line 29's `Memory/` (intended for the project-root `Memory/` folder grouped under §3 with `_bmad/`, `.claude/`, `Articles/`, etc.) caught `kernel/memory/` despite the lowercase path. Other `.gitignore` patterns without leading `/` may have similar latent collisions with lowercase path components elsewhere in the tree — the pattern's rare-name-protection assumption is broken on Windows.

**Disposition.** Parked for separate-session audit, not blocking. The single known instance (`Memory/` → `kernel/memory/`) was fixed in 9.4.2-pre.1 corrigendum (commit `d9d4cf0`) by anchoring `Memory/` → `/Memory/`. No other instance has been verified yet. Risk class: latent — would manifest only when a future kernel/adapter/test/ directory's name happens to case-fold to one of the unanchored patterns, and the divergence between intended-scope (repo root) and actual-scope (anywhere, case-insensitive) would silently shadow the new substance the same way `kernel/memory/` was shadowed pre-corrigendum.

**Forward action.** Audit pass for any `.gitignore` pattern where comment context implies repo-root scope but the syntax lacks a leading `/` anchor — the §3 "Workspace files — NEVER tracked" block of repo-root `.gitignore` (lines 22–31, where `Memory/` lived) is the highest-risk locus. For each candidate (`_bmad/`, `_bmad-output/`, `.claude/`, `Articles/`, `CLAUDE.md`, `claude-setup-reference.md`), verify whether a same-named directory case-folds to a path elsewhere in the tree (`find . -type d -iname '<pattern>'` on Windows or any case-insensitive filesystem). Anchor any over-broad patterns to repo root via leading `/`. Defer to a session that can land both audit findings and the fix under one corrigendum commit; not a 9.4.2-pre.1 scope expansion.

### §3.5. F10 — `praxis.kernel` package-shape asymmetry

**Body.** Memo §5 obs 2 (pre-corrigendum) characterized `praxis.kernel.__path__` as aggregating `kernel/compression/` only — single-element. This was observable because only `kernel/compression/src/praxis/kernel/__init__.py` was tracked at that point. Post-corrigendum (`d9d4cf0`, closing F8), `kernel/memory/src/praxis/kernel/__init__.py` is also tracked — `kernel/memory` contributes its path to whatever resolution `praxis.kernel` yields. Other kernel members (`mac`, `pi-mono`, `runtime`, `studio`) declare `praxis.<name>.<modules>` at top level (no `.kernel.` infix) per preload Item-3's `praxis.__path__` 10-path aggregation, so they're not in scope for the asymmetry. Open question: does `kernel/compression`'s path still win? Both win (namespace aggregation continues)? One shadow the other (one becomes regular-package resolution)?

**Disposition.** Parked for separate-session investigation, not blocking. Likely Stage 9.5 architectural review scope — answer informs whether any shared `praxis.kernel.<x>` substrate makes architectural sense, or whether `praxis.kernel.memory` is an isolated sub-package by design and the compression contribution is incidental. Whichever way the investigation lands, it's a pattern question, not a defect — both `kernel/compression` and `kernel/memory` work correctly in isolation under the editable installs. The 9.4.2-pre.1 corrigendum (closing F8) made this asymmetry visible to git but did not introduce it; the asymmetry pre-existed silently behind the F8 Cause-B `Memory/` case-fold gap.

**Forward action.** When the next architectural review picks this up: (a) re-run `python -c "import praxis.kernel; print(praxis.kernel.__path__, getattr(praxis.kernel, '__file__', None))"` post-corrigendum to characterize the now-current resolution (memo §5 obs 2's "single-element" claim was an inference, not direct verification — re-verify before proceeding); (b) inventory `__init__.py` markers across all kernel-member `src/praxis/kernel/` paths via `find kernel -path '*/src/praxis/kernel/__init__.py'` to enumerate the contributors; (c) cross-reference with the architectural intent — is `praxis.kernel.<name>` a deliberate sub-package shape, or accidental nesting from `kernel/memory`'s directory layout? (d) reconcile by either renaming `kernel/memory`'s substrate path to `praxis.<name>` (matching its siblings) or by deliberately adopting `praxis.kernel.<name>` everywhere with a paired architectural-decision record. Defer to the session that owns the architectural-pattern disposition.

---

## §4. Self-reference precedent observation

The 9.4.2-pre and 9.4.2-pre.1 close cycles both used a two-commit shape: a substance commit (containing all the load-bearing changes + the memo) followed by a stamp commit (backfilling the close-memo's §6 with the substance commit's SHA). The stamp commit does NOT record its own SHA in the memo — its SHA lives in `git log` of the memo file. Both stamps follow this rule:

- `439c0b7` (substance) → `3fe343f` (stamp records `439c0b7`)
- `d9d4cf0` (substance) → `1ce354e` (stamp records `d9d4cf0`)

This shape resolves the self-reference loop that would otherwise arise if the close-memo tried to record both the substance SHA AND the stamp SHA — the latter is unknowable pre-commit (depends on the tree state which depends on the memo content). Worth pinning for future close-memos: stamp records parent only; stamp's own SHA lives in `git log` of the memo file.

The `1ce354e` stamp explicitly trimmed an over-engineered "9.4.2-pre.1 stamp commit SHA" row that the memo's §10 had pre-staged — the row was dropped per `3fe343f` precedent rather than filled with a self-reference. This trimming is the kind of self-correction that the future-session memory candidate `feedback_pre_stamp_reproducibility_audit.md` would systematize at the discipline level.

---

## §5. Memory writes recap

Two feedback memories written during this session under advisor draft-then-go discipline (per `feedback_memory_authorization.md`):

- **`feedback_provenance_pin.md`** — env-foundational close memos require a §provenance table (surface/model/interpreter/installer/lockfile/SHAs). Bootstrap memo §6 is the proof-of-concept artifact; the discipline is reusable for any future env-foundational close.
- **`feedback_session_surface_audit.md`** — declare session ID/model/JSONL/working-dir as a fixed preload item before any state mutation. Pairs with `feedback_provenance_pin.md` at close-memo time; surfacing at preload avoids late-charter scrambles to backfill provenance fields.

`MEMORY.md` index updated with one-line entries for each (after line 19, in single-line `- [Title](file.md) — hook` form).

**Parked future memory candidate (NOT written this session):**

- **`feedback_pre_stamp_reproducibility_audit.md`** — at any future charter-close stamp gate, run a pre-stamp reproducibility check before the stamp commit lands: enumerate paths claimed in the close-memo's bootstrap state and verify each is present in `git show <close-SHA>:<path>` from a clean-clone vantage. Would have caught the F8 structural-completeness gap at the `3fe343f` stamp gate, before the corrigendum became necessary. Address in the next session that does charter-close work — first-mover authoring discipline applies (don't write speculatively).

---

## §6. Parked items

- **`docs/pipeline-stage9.md`** — pre-existing modification (predates this session; visible in `git status --short` since 04-29). NOT included in any 9.4.2-pre-* commit. Defer to a session that can do git-archaeology to identify the originating change set. Recommend keeping in working tree as-is until then.
- **F9 audit** — Windows case-fold `.gitignore` landmine, full audit pass deferred. See F9 docket entry §3.4 for recipe + candidate-pattern list.
- **F10 architectural review** — `praxis.kernel` package-shape asymmetry, Stage 9.5 architectural review scope. See F10 docket entry §3.5 for verification recipe + reconciliation options.
- **`feedback_pre_stamp_reproducibility_audit.md`** — see §5 above; parked for next charter-close session.

---

## §7. Handoff to 9.4.2-internal step 7 (TONL adapter MAC-T authoring)

**Predicate satisfied.** The env-foundational predicate that blocked §9.C on 04-29 morning (`ModuleNotFoundError: No module named 'praxis.adapters'` under system Python 3.11) is now satisfied. Repo-root `.venv/` is the binding env at HEAD `1ce354e`; Python 3.12.12; uv 0.11.2; lockfile sha256 `a3362cb3cd8d0a5e8fa39f920b3639cb4a2befa7fb2ca12e78ae0b3b28d119cb`.

**Re-engagement scaffold integrity.** TONL adapter scaffold artifacts on disk from 04-28 22:22–22:24 (in `adapters/tonl/src/...`) remain valid; corrigendum `d9d4cf0` did NOT touch their substance, only made them git-tracked for the first time. §9.C runtime PASS at 04-30 confirms scaffold contract holds.

**Preload requirements at re-engagement (per disciplines reinforced this session):**
1. **Surface declaration** (per `feedback_session_surface_audit.md`) — declare session ID + model + JSONL path + working dir + current date at preload, before any state mutation.
2. **Filesystem verify** — confirm HEAD = `1ce354e`, working tree state, lockfile sha256 unchanged.
3. **Interpreter sanity** — `.venv/Scripts/python.exe --version` returns `Python 3.12.12`.
4. **Workspace sanity** — re-run preload Item-3 namespace-package import smoke (`praxis.ports.serialization`, `praxis.adapters.tonl.adapter`); confirm 10-element `praxis.__path__` aggregation.
5. **§9.C re-run** if any env state changed since `1ce354e`. Cite as `playbook addenda §9.C` per F6 forward action — `session-handoff-20260426-stage9.4.1-amelia-preload.md` lines 199–203 (rule prose) + `session-handoff-20260428-stage9.4.2-executor.md` lines 59–66 (TONL/SerializationPort code block). Do NOT cite `test-strategy.md §9.C` (no such section).
6. **Advisor spot-check for env-related rot** (per 04-29 F3 advisor handoff) — standing recommendation at any re-engagement.

**Resumption scope.** TONL adapter MAC-T authoring per `test-strategy.md` v0.2 §2.2.2 (`Serialization Port (ADR-2) — 12 MAC-Ts`) and the playbook §9 addenda for runtime verification. Out-of-scope-for-this-handoff: F9 audit, F10 architectural review, `feedback_pre_stamp_reproducibility_audit.md` authoring — all parked for separate sessions.

---

*Authored 2026-05-01 by Claude Code CLI session (model `claude-opus-4-7[1m]`, JSONL `69f1a342-ab3a-4e66-9df9-df20cff7a15f`); HEAD at write `1ce354e`.*
