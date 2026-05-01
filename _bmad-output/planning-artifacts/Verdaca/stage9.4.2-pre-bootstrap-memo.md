# Stage 9.4.2-pre Bootstrap Memo — repo-root uv workspace

**Sub-stage:** 9.4.2-pre — environment-foundational bootstrap (carved out of Stage 9.4.2 step 7 after the 04-29 morning halt at §9.C runtime check)
**Status:** **CHARTER COMPLETE** (steps 1–8, including this memo) — pending advisor close
**Author:** Executor (Claude Code CLI session, model `claude-opus-4-7[1m]`) under advisor review
**Scope cap:** environment-foundational only. Does NOT extend into 9.4.2-internal step 7 (TONL adapter MAC-T authoring) — that resumes under the original 9.4.2 charter on a separate go.
**Outcome:** §9.C runtime check `isinstance(TONLAdapter(), SerializationPort) == True` passes under the new env; M-T-VS-* reproducibility smoke 10/10 GREEN; consolidated `praxis` namespace package aggregates 10 paths.

---

## §1. Charter recap

8-step bootstrap, all complete:

| # | Step | Disposition |
|---|------|-------------|
| 1 | Root `pyproject.toml` workspace decl + 9 member `[build-system]` blocks (B1.a) | ✅ |
| 2 | Root `.python-version` → 3.12.12 | ✅ |
| 3 | `uv sync` to produce `.venv/` + `uv.lock` | ✅ (87 pkgs, 10 workspace members) |
| 4 | Retire legacy `praxis-compression 0.1.0` editable from system Python311 | ✅ |
| 5 | Archive `_bmad-output/.../praxis/compression/` → `_bmad-output/_archive/praxis-pre-rename/compression/` | ✅ (265 files via PowerShell `Move-Item`) |
| 6 | Re-run §9.C runtime check under new env | ✅ PASS |
| 7 | M-T-VS-* reproducibility smoke (recommended) | ✅ 10/10 GREEN |
| 8 | Bootstrap memo writeup | ✅ (this document) |

R3 noted: `shell/` carries `[build-system]` on disk per S1 but is **not** workspace-installed (pytest-asyncio constraint conflict with `kernel/runtime/[test]`). Workspace member count = 10, not 11.

---

## §2. What was bootstrapped (filesystem additions)

**Repo root:**
- `pyproject.toml` (635 B) — workspace declaration, 10 members
- `.python-version` (8 B) — `3.12.12`
- `uv.lock` (352 587 B) — `version=1`, `revision=3`, `requires-python=">=3.12"`, sha256 `a3362cb3cd8d0a5e8fa39f920b3639cb4a2befa7fb2ca12e78ae0b3b28d119cb`
- `.venv/` — Python 3.12.12 from `%APPDATA%\Roaming\uv\python\cpython-3.12.12-windows-x86_64-none\python.exe`, installer `uv 0.11.2`, `include-system-site-packages = false`, prompt `Anthropic`
- `.gitignore` — 3 `!` re-includes appended after line 15 (`!pyproject.toml`, `!.python-version`, `!uv.lock`)

**Workspace members — 10 declared, `[build-system]` state at 9.4.2-pre.1 corrigendum close:**

| Member (per root `[tool.uv.workspace] members`) | `[build-system]` source | First tracked at | Notes |
|---|---|---|---|
| `ports` | pre-existing | 9.4.2-pre.1 | Newly visible to git (Cause-A `.gitignore` gap; see §3). |
| `adapters/beads` | pre-existing | 9.4.2-pre.1 | Newly visible. 9.4.1 Beads adapter substance retroactively tracked (substance, not charter; see §10). |
| `adapters/tonl` | pre-existing | 9.4.2-pre.1 | Newly visible. 9.4.2 step-7 (04-28) TONL scaffold retroactively tracked. |
| `tests` | pre-existing | 9.4.2-pre.1 | Newly visible. 10 binding M-T-VS-* contract tests retroactively tracked. |
| `kernel/compression` | pre-existing (before bootstrap) | pre-bootstrap | `[build-system]` precedent for the 4 mods below. |
| `kernel/mac` | added in 439c0b7 | 439c0b7 | `[build-system]` block added. |
| `kernel/memory` | pre-existing | 9.4.2-pre.1 | Newly visible (Cause-B `Memory/` case-fold; see §3). 67 files added; 6 cruft excluded per kernel-local `.gitignore`. |
| `kernel/pi-mono/src` | pre-existing (before bootstrap) | pre-bootstrap | **Nested-src pyproject layout** — pyproject lives at `kernel/pi-mono/src/pyproject.toml`, one directory deeper than its siblings. Drives the importlib-finder editable-install behavior pinned in §5 obs. 4. |
| `kernel/runtime` | added in 439c0b7 | 439c0b7 | `[build-system]` block added. |
| `kernel/studio` | added in 439c0b7 | 439c0b7 | `[build-system]` block added. |

Plus `shell/pyproject.toml` — `[build-system]` added in 439c0b7 per S1 (`where=["."]+include=["api*"]`); shell deferred from workspace install per R3 (pytest-asyncio constraint conflict with `kernel/runtime/[test]`). Workspace member count = 10, not 11.

3 members carry `[tool.uv.sources]` workspace-internal dep markers (unchanged from 439c0b7).

**Editable install asymmetry observed:** `pi-mono` resolves through an importlib-finder hook (`__editable__.praxis_pi_mono-0.1.0.finder.__path_hook__`) due to its `where=["."]` setuptools config + nested-src pyproject layout (above); the other 9 use `.pth`-based editables. Both work, asymmetric — pinned in §5.

---

## §3. What was retired / moved

**Legacy editable uninstalled:**
- `praxis-compression 0.1.0` removed from system Python311 site-packages. Pre-bootstrap, this editable was the only Python-side path to `praxis.*` modules and was the precipitating cause of the 04-29 morning `ModuleNotFoundError: No module named 'praxis.adapters'` at §9.C — system Python311 had `praxis.compression` but not `praxis.adapters` / `praxis.ports`.

**Archive move:**
- Source: `_bmad-output/implementation-artifacts/praxis/compression/` (265 files)
- Target: `_bmad-output/_archive/praxis-pre-rename/compression/` (11 top-level entries: `src/`, `tests/`, plus 9 .md/cfg files)
- Mechanism: bash `mv` failed with "Permission denied" across gitignored-tree parents on Windows; PowerShell `Move-Item` succeeded. Pinned for §5.

**Out of step-5 scope (deliberately untouched):**
- 5 sibling legacy trees at `_bmad-output/implementation-artifacts/praxis/{mac,memory,runtime,shell,studio}/` — docket'd, not addressed in 9.4.2-pre.
- 13 historical doc references in `docs/` to the pre-archive path — accepted historical class.

**Untouched binding artifacts:** `ports-architecture.md`, `port-contracts.md`, `test-strategy.md`, `requirements.md`, `pipeline-stage9.md` — zero edits in 9.4.2-pre.

**`.gitignore` root-cause finding (surfaced 2026-05-01 during F8 verification):** 5 of the 10 declared workspace members were invisible to git at 439c0b7 close — `ports/`, `adapters/beads/`, `adapters/tonl/`, `tests/`, `kernel/memory/`. Two distinct mechanisms:

- **Cause A — root `/*` blocks new top-level dirs.** Repo-root `.gitignore` line 8 (`/*`) excludes everything at the repo root by default; lines 11–18 re-include named entries (`.gitignore`, `README.md`, `kernel/`, `shell/`, `docs/`, `pyproject.toml`, `.python-version`, `uv.lock`). The bootstrap added `!`-re-includes for the 3 new root-level *files* but missed the new top-level *directories* `ports/`, `adapters/`, `tests/`. Everything under those directories was silently ignored — including `tests/src/praxis/contract_tests/ports/test_versioned_state_contract.py` whose 10/10 GREEN run is reported in §4.
- **Cause B — `Memory/` pattern catches `kernel/memory/` via Windows case-fold.** Repo-root `.gitignore` line 29 (`Memory/`, intended for the project-root `Memory/` workspace folder grouped under §3 with `_bmad/`, `.claude/`, `Articles/`, etc.) lacked a leading `/` anchor and matched `Memory/` anywhere in the tree; Windows `core.ignorecase=true` (default) made the match case-insensitive, so `kernel/memory/` was caught.

Both causes were resolved in the 9.4.2-pre.1 corrigendum (see §10). The original 439c0b7 close memo lacked these findings because the verification gate that surfaced them (clean-clone-reproducibility check on the bootstrap commit's tree) wasn't part of the original 9.4.2-pre charter — captured as a future memory candidate (`feedback_pre_stamp_reproducibility_audit.md`) per advisor disposition.

---

## §4. Verification

### §9.C runtime check (step 6) — PASS

Executed verbatim per 04-28 executor handover lines 59–66 (advisor disposition (a) on the test-strategy.md/charter-shorthand discrepancy: 04-28 block adopted as canonical; faithful operationalization of binding 04-26 rule lines 199–203):

```python
from praxis.adapters.tonl.adapter import TONLAdapter
from praxis.ports.serialization import SerializationPort
adapter = TONLAdapter()
assert isinstance(adapter, SerializationPort), "§9.C check failed"
```

Result: `True`, exit 0. `TONLAdapter` resolved from `adapters/tonl/src/praxis/adapters/tonl/adapter.py`; `SerializationPort` resolved from `ports/src/praxis/ports/serialization.py`. Both reached through 10-element `praxis.__path__`.

### M-T-VS-* reproducibility smoke (step 7) — 10/10 GREEN

Command: `.venv/Scripts/python.exe -m pytest tests/src/praxis/contract_tests/ports/test_versioned_state_contract.py -v` → `10 passed in 0.26s`, exit 0.

All 10 binding `M-T-VS-*` MAC-Ts (SNAPSHOT-01, LATEST-01, AT-VERSION-01, LIST-01, MIGRATE-01, MIGRATE-02, MIGRATE-SIG-01, CONFLICT-01, GAP-01, SERIAL-COUPLING-01) green. M-T-VS-MIGRATE-02 (Cleo grep — adapter authors no Migrator) confirms no overnight drift in adapter-vs-port boundary.

---

## §5. Observations (roll into bootstrap-state record)

1. **`praxis` is now a 10-path namespace package.** `praxis.__path__` aggregates `adapters/{beads,tonl}/src/praxis`, `kernel/{compression,mac,memory,pi-mono,runtime,studio}/src/praxis`, `ports/src/praxis`, `tests/src/praxis`, plus the pi-mono importlib-finder hook entry. PEP-420 namespace resolution working post-Finding-C.2 marker deletions.

2. **Kernel substrate paths are asymmetric, not uniform.** `praxis.kernel.__path__` aggregates kernel/compression/ only (single-element); other kernel members place packages at different `praxis.*` paths (e.g., `praxis.adapters.tonl` lives under `adapters/`, not under `praxis.kernel.*`). Worth pinning — assumptions like "everything under `praxis.kernel`" will not hold.

3. **§9.C verifies Protocol structural conformance, not nominal inheritance.** `type(TONLAdapter).__mro__` = `['TONLAdapter', 'object']` — `SerializationPort` does not appear in the MRO. The check passes via `runtime_checkable` Protocol matching. Consistent with V4 in-tree-wrap composition pattern; gated as candidate F7 docket text per advisor discipline.

4. **Editable install pattern asymmetry.** `pi-mono` uses an importlib-finder editable; siblings use `.pth`-based editables. Both work but the asymmetry is a real difference — driven by `where=["."]` in pi-mono setuptools config.

5. **Windows-on-bash filesystem operation gotcha.** `mv` for cross-parent gitignored-tree moves fails "Permission denied"; PowerShell `Move-Item` is the reliable fallback. Step 5 evidence.

6. **uv-managed venvs ship without pip.** Use `uv pip show` from repo root, not in-venv pip-style introspection.

7. **stdout encoding artifact.** Windows cp1252 mangles `§` to `�` in console output; logic unaffected. Cosmetic only — declined for docket per advisor disposition on side observation #2.

---

## §6. Provenance pin

For the discipline-ledger `feedback_provenance_pin.md` candidate (Andrey may authorize after this memo lands):

| Field | Value |
|---|---|
| Surface | Claude Code CLI |
| Model | `claude-opus-4-7[1m]` |
| Working dir | `C:\Users\AndreyPopov\Documents\Anthropic` |
| Session JSONL | `~/.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/69f1a342-ab3a-4e66-9df9-df20cff7a15f.jsonl` |
| Interpreter | Python 3.12.12 (`%APPDATA%\Roaming\uv\python\cpython-3.12.12-windows-x86_64-none\python.exe`) |
| Installer | uv 0.11.2 (delta vs 04-28 run: uv 0.10.6) |
| Lockfile size | 352 587 B |
| Lockfile sha256 | `a3362cb3cd8d0a5e8fa39f920b3639cb4a2befa7fb2ca12e78ae0b3b28d119cb` |
| Pre-bootstrap commit SHA | `934f5eae5c05d3c77c1b8d1643b813158d9569bf` (HEAD on `main` at memo write; bootstrap deltas live as uncommitted working-tree changes — listed in §2/§3 + visible in `git status --short`) |
| Bootstrap close commit SHA | `439c0b71b12a94b06fe32b1d338684ba9168464c` |
| 9.4.2-pre.1 corrigendum commit SHA | `d9d4cf092692c795220cc239ce1d85af03b8e6f5` |
| Memo timestamp | 2026-04-30 |

---

## §7. Findings dispositioned + docket items

**Closed in 9.4.2-pre:**
- F1, F2, F3 — closed at 04-29 EOD (advisor adjudication; F3 closed at (d) effective; F5 disposed Medium with caveats).

**Gated, awaiting advisor go:**
- **F6** — proposal text not yet drafted; remains gated on separate go.
- **F7 (candidate)** — §9.C scope clarification: §9.C verifies Protocol structural satisfaction, not MRO ancestry. Future adapters needing shared default impls via class-tree ancestry will not be caught by §9.C alone — that scenario requires a separate explicit ancestry check. Consistent with V4 in-tree-wrap composition pattern; not a defect.

**Memorialization candidates (draft-only; gated per `feedback_memory_authorization.md`):**
- `feedback_provenance_pin.md` — see §6 provenance fields as proof-of-concept.
- `feedback_session_surface_audit.md` — pending draft.

**Side observations declined for docket per advisor disposition (this session):**
- cp1252 stdout `§` mangling — cosmetic, terminal-encoding-local.
- Namespace-package end-to-end resolution — positive confirmation, no docket; pinned in §5.

---

## §8. Out of scope (explicit) + handoff to 9.4.2-internal

**Not done in 9.4.2-pre (and not in scope):**
- TONL adapter MAC-T authoring (the original 9.4.2 step 7 substance).
- 5 sibling legacy `praxis/{mac,memory,runtime,shell,studio}/` tree dispositions.
- 13 historical `docs/` references to pre-archive compression path.
- `shell/` workspace install (deferred per R3; pytest-asyncio constraint conflict).
- F6 + F7 docket landings.
- Memory writes (`feedback_provenance_pin.md` and any other) — gated.

**Handoff note for 9.4.2-internal step 7 resumption:** the env-foundational predicate that blocked §9.C on 04-29 morning is now satisfied. Next session can re-engage from the original 9.4.2 charter step 7 (TONL adapter MAC-T authoring) without re-doing bootstrap. Scaffold artifacts on disk from 04-28 22:22–22:24 should remain valid; advisor spot-check for env-related rot at re-engagement is the standing recommendation per the 04-29 F3 advisor handoff.

---

## §9. Charter close request

Charter steps 1–8 complete. M-T-VS-* smoke 10/10 GREEN; §9.C PASS; no binding-artifact edits; no memory writes; F6+F7 gated; provenance fully pinned. Awaiting advisor close + post-close commit SHA assignment for §6 final field.

---

## §10. 9.4.2-pre.1 corrigendum (2026-05-01)

**Trigger.** F8 verification (2026-05-01, pre-docket-draft check at advisor request) confirmed three workspace-member pyprojects (`adapters/beads/pyproject.toml`, `kernel/memory/pyproject.toml`, `ports/pyproject.toml`) were not present at 439c0b7. Investigation surfaced that 5 of 10 declared workspace members were entirely invisible to git pre-corrigendum, due to the two `.gitignore` root causes documented in §3.

**Disposition.** Closes are forward-only — 9.4.2-pre charter close at 3fe343f stands. The corrigendum is a discovery-driven defect fix that lands the missing substance under a new commit suffixed `9.4.2-pre.1`. Not a charter reopen. Precedent: defects found post-stamp-follow-up are dispositioned via corrigendum commit, not charter reopen.

**Scope (single corrigendum commit, fix mechanism γ — root-cause `.gitignore` fix + named-file enumeration):**
- **`.gitignore` (repo-root):** 3 re-includes (`!ports/`, `!adapters/`, `!tests/`); anchor `Memory/` → `/Memory/`.
- **`kernel/memory/.gitignore` (kernel-local):** add `pre_sales_demo_result.json` (the other 5 cruft patterns were already covered).
- **File adds:** 85 files across `ports/` (6), `adapters/beads/` (5), `adapters/tonl/` (5), `tests/` (2), `kernel/memory/` (67). 6 cruft files in `kernel/memory/` excluded per kernel-local `.gitignore`.
- **Root `pyproject.toml`:** memo-path comment fix (`_bmad-output/implementation-artifacts/verdaca/stage9/9.4.2-pre-bootstrap-memo.md` → `_bmad-output/planning-artifacts/Verdaca/stage9.4.2-pre-bootstrap-memo.md`).
- **This memo:** §2 full rewrite (per-member `[build-system]` state table + nested-src pi-mono note); §3 addition for `.gitignore` root-cause; this §10; §6 row addition for corrigendum SHA.

**9.4.1 substance retroactive tracking note.** The Beads adapter source (`adapters/beads/src/praxis/adapters/beads/...`) and its 10 M-T-VS-* contract tests (`tests/src/praxis/contract_tests/ports/test_versioned_state_contract.py`) were authored as Stage 9.4.1 substance but were never tracked because `adapters/` and `tests/` were both blocked by the same Cause-A `.gitignore` gap. They become tracked under this 9.4.2-pre.1 corrigendum because the workspace declaration at 439c0b7 depends on them — substance, not charter scope. **9.4.1 close at 934f5ea stands; 9.4.1 close memo (`stage9.4.1-close-memo.md`) is not edited.** Future sessions may issue a 9.4.1 retrospective annotation pointing to this corrigendum; deferred.

**F10 candidate (parked, not blocking).** After this corrigendum lands, `kernel/memory/src/praxis/kernel/__init__.py` is tracked, making `praxis.kernel` a regular package rooted only at `kernel/memory`'s path. Other kernel members (compression, mac, pi-mono, runtime, studio) declare `praxis.<name>.<modules>` (top-level, no `.kernel.` infix) per preload Item-3's `praxis.__path__` aggregation. Whether this asymmetry is intentional (memory's sub-package isolation has a reason) or accidental shape divergence is deferred to a separate session — likely a Stage 9.5 architectural review.

**F9 candidate (parked, not blocking).** Windows case-fold `.gitignore` latent landmine — patterns lacking leading `/` anchors will match same-named directories anywhere in the tree, and Windows `core.ignorecase=true` (default) makes them case-insensitive. The `Memory/` → `kernel/memory/` collision is the instance fixed here; other lowercase path components could silently collide. Audit pass (enumerate all `.gitignore` patterns without leading `/`, cross-reference against actual lowercase directory names) deferred to a separate session.

**Future memory candidate (parked).** `feedback_pre_stamp_reproducibility_audit.md` — at charter-close stamp time, before stamping, verify the close commit's tree reproduces the memo's claimed bootstrap state from a clean-clone vantage. Would have caught this at the 3fe343f stamp gate. Address in the next session that does charter-close work.
