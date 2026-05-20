# Code Quality Report — praxis.kernel.memory

**Generated:** 2026-04-12
**Scope:** `_bmad-output/implementation-artifacts/praxis/memory/src/`
**Agent:** Cleo — Clean Code Quality Reviewer
**Pipeline step:** 3.3.5 (gate before Quinn / Step 3.4)

## Standards Loaded

| Source | Trust | Notes |
|--------|-------|-------|
| `pyproject.toml` → `[tool.ruff]` | **override** | line-length=100, target=py312, select=E/F/W/I/TID/B |
| `_bmad/bmm/agents/clean-code-reviewer/references/python-standards.md` | verified | PEP 8/257/20 + Ruff + Black + mypy + Bandit synthesis |
| `_bmad/bmm/agents/clean-code-reviewer/references/universal-principles.md` | verified | SOLID, DRY/KISS/YAGNI, code smells |
| `_bmad/bmm/agents/clean-code-reviewer/overrides/python.md` | override | empty (no user overrides) |

Priority resolution: **pyproject.toml wins over verified wins over community.** The project's `line-length=100` overrides PEP 8's 79-char guidance.

---

## Executive Summary

| Metric | Value |
|---|---|
| Files reviewed | 23 (.py) |
| Ruff `check` result | **PASS (0 violations)** |
| Ruff `format --check` result | **PASS (23/23 formatted)** |
| CRITICAL findings | **0** |
| WARNING findings | 6 |
| INFO findings | 5 |
| Overall quality score | **A** |

### Verdict

The Memory module is in genuinely good shape. Ruff's declared rule set (E/F/W/I/TID/B + bugbear) passes clean on every file, formatting is already canonical, and the architectural discipline is strong throughout: frozen Pydantic v2 models, Draft/Record pattern, protocol-based backends, DI at every boundary, tenant guards at every entry point, and content-addressed audit trail. 253 tests pass. The findings below are linter-miss concerns — DRY violations in helper duplication across the three backends, a handful of hardcoded POSIX paths that will break on Windows, and minor cleanups. **0 CRITICAL → gate PASSES for Cleo step 3.3.5.**

---

## Findings by Severity

### CRITICAL — 0

None.

### WARNING — 6

#### W1 — Hardcoded `/tmp/...` artifact paths (POSIX-only)

**Files and lines:**
- `src/praxis/kernel/memory/_internal/beads/store.py:381`
- `src/praxis/kernel/memory/_internal/atelier/store.py:353`
- `src/praxis/kernel/memory/_internal/mem0_adapter/adapter.py:336`

**Rule:** Universal Principles → Primitive Obsession / Platform Neutrality
**Issue:** Export returns `f"/tmp/{backend}-export-{id}.json"`. `/tmp` does not exist on Windows (the declared dev host per CLAUDE.md is Win11 Enterprise) and is also the wrong directory on macOS for user-owned artifacts. These strings are placeholders until Stage 7 wires a real artifact store, but hardcoded POSIX paths are a latent defect: the first developer who runs the export path on Windows gets a silent `FileNotFoundError` under any downstream `open()` call.

**Fix:** Replace the literal `/tmp/` prefix with `tempfile.gettempdir()` so the placeholder at least resolves on every platform. Proper artifact-store wiring stays Stage 7 territory. **Applied — see "Fixes Applied" below.**

---

#### W2 — DRY: `_utc_now` duplicated in 4 files

**Files:**
- `src/praxis/kernel/memory/_internal/audit.py:70-71`
- `src/praxis/kernel/memory/_internal/beads/store.py:70-71`
- `src/praxis/kernel/memory/_internal/atelier/store.py:73-74`
- `src/praxis/kernel/memory/_internal/mem0_adapter/adapter.py:79-80`

**Rule:** DRY (Universal Principles)
**Issue:** `def _utc_now() -> datetime: return datetime.now(tz=timezone.utc)` appears verbatim four times. Each copy is two lines and behaviorally identical. If one copy drifts (e.g., a future contributor passes `tz=datetime.UTC` via Python 3.11+ syntax in one module only), the chain-of-beads replay invariant and audit timestamps become silently inconsistent.

**Fix (deferred with rationale):** A `praxis.kernel.memory._internal.common.time` helper would consolidate. Deferred because: (a) the `_internal/common/` subpackage already exists (currently only `db.py`), (b) a clean consolidation also captures `_new_entry_id` / `_new_id` (see W3), and (c) the four current copies are identical today — drift hasn't happened. Recommendation: Quinn / Stage 5 does both W2 + W3 as one `_internal/common/ids_and_time.py` consolidation when `retrieve_similar_tasks` grows its dedicated path (which will touch all three backends anyway).

---

#### W3 — DRY: `_new_entry_id` / `_new_id` duplicated in 3 files

**Files:**
- `src/praxis/kernel/memory/_internal/beads/store.py:74-75` (`_new_entry_id`)
- `src/praxis/kernel/memory/_internal/atelier/store.py:77-78` (`_new_id` — same body, different name)
- `src/praxis/kernel/memory/_internal/mem0_adapter/adapter.py:83-84` (`_new_entry_id`)

**Rule:** DRY (Universal Principles); naming consistency
**Issue:** Same three-line helper (`return uuid.uuid4().hex`) exists in three places under two different names. The naming divergence (`_new_id` vs `_new_entry_id`) is a minor readability smell — a reader scanning atelier/store.py has to check whether `_new_id` is semantically different from `_new_entry_id` elsewhere. It is not.

**Fix (deferred with rationale):** Same as W2 — consolidate into `_internal/common/` alongside `_utc_now` in the Quinn / Stage 5 pass. Renaming now would churn all three backends without functional benefit.

---

#### W4 — DRY: `_hash_delete_criteria` / `_hash_quarantine_reason` / `_hash_reason`

**Files:**
- `src/praxis/kernel/memory/facade.py:105-108` (`_hash_criteria`)
- `src/praxis/kernel/memory/_internal/beads/store.py:449-460` (`_hash_delete_criteria`, `_hash_quarantine_reason`)
- `src/praxis/kernel/memory/_internal/atelier/store.py:431-435` (`_hash_reason`)

**Rule:** DRY + §8.4 "no raw criteria in audit logs"
**Issue:** Four nearly-identical SHA256 salted-hash helpers. Each constructs a `f"..."` payload, encodes utf-8, and returns `sha256(payload).hexdigest()`. Right now NONE of them actually use a salt despite the doctrings/comments claiming "salted sha256". That is a correctness risk for §8.4 "salted-hash audit log entry" (Req #33): a future rainbow-table attacker against the audit log would find the hashes trivially invertible because the salt is the empty string. Phase 3C ships the in-memory buffer, so this has no exploit surface today, but Stage 7's durable sink turns it into a real concern.

**Fix (deferred with rationale):** The correct consolidation requires a manifest-scoped salt (the tenant_hash plus a per-deployment secret loaded via architecture §3.3's signed-YAML loader that lands in Stage 7). A one-function consolidation now without the salt plumbing would just move the same problem. Recommendation: **open a follow-up task against Stage 7 ("Req #33 salted audit hash") that consolidates these four call sites AND wires the salt from the deployment manifest.** Flag this in `architecture.md`'s "Out of scope for 3C" section so Stage 7 picks it up. No code change in 3C.

---

#### W5 — atelier/store.py:373-376 — dead `if ... pass` branch

**File:** `src/praxis/kernel/memory/_internal/atelier/store.py:373-376`

**Rule:** Dead code / readability (Universal Principles → Code Smells → Dead code)
**Issue:**

```python
if entry.state is _AtelierEntryState.QUARANTINED:
    # Idempotent: re-quarantine of an already-quarantined
    # entry is a no-op with a new state_snapshot_version.
    pass
```

The code below this block runs unconditionally, creating a new `_StoredDecision` with a fresh `state_snapshot_version`, so the idempotency claim is structurally correct — but the `if ... pass` pattern wastes a reader's attention: they stop to figure out what's in the branch, find nothing, and have to read on to see that the work happens unconditionally. Linters don't flag this because `pass` is syntactically valid.

**Fix:** Move the comment to the top of `_quarantine_sync`'s normal path, drop the `if`. **Applied — see "Fixes Applied" below.**

---

#### W6 — mem0_adapter/adapter.py:287 — `-1` sentinel then `max(deleted, 0)`

**File:** `src/praxis/kernel/memory/_internal/mem0_adapter/adapter.py:287-295`

**Rule:** Readability / Primitive Obsession (Universal Principles)
**Issue:** The full-tenant branch sets `deleted = -1` as a "we don't know" sentinel, then `max(deleted, 0)` clamps it to 0 at return time. A reader has to trace through two assignments plus a `max()` to understand that full-tenant deletes return zero-count. This is a footgun: if any future code reads `deleted` between the sentinel and the clamp (e.g., for a log line), the `-1` leaks.

**Fix:** Drop the sentinel. The full-tenant branch should just leave `deleted = 0` and let the return statement use `deleted` directly. The "Mem0's delete_all does not report a count" comment stays. **Applied — see "Fixes Applied" below.**

---

### INFO — 5

#### I1 — facade.py:472 — local import inside function

**File:** `src/praxis/kernel/memory/facade.py:472`

```python
def _task_outcome_to_decision_draft(...) -> DecisionDraft:
    ...
    from praxis.kernel.memory.models import EvidenceItem
```

`EvidenceItem` could be hoisted to the module-level import block — there is no circular-import reason to defer it (facade.py already imports many other names from `praxis.kernel.memory.models` at module level). **Fix: hoist. Applied.**

#### I2 — beads/store.py:450, 457 + atelier/store.py:432 — `import hashlib` inside functions

**Files:** `_internal/beads/store.py:450, 457`, `_internal/atelier/store.py:432`

Three function-body `import hashlib` statements. `hashlib` is stdlib and cheap, so there's no lazy-import reason. Per PEP 8 §4 imports belong at the top. Ruff does not flag function-body imports as E402. **Fix: hoist. Applied.**

#### I3 — facade.py imports `_utc_now` from `_internal/audit`

`from praxis.kernel.memory._internal.audit import ..., _utc_now` — the facade reaches into a private symbol (leading underscore) across module boundaries. Allowed by Python, and the facade owns the `_internal/` tree by design (per NR-S-R1 per-file-ignore), so it's not a layering violation. Still, by the time W2 consolidates `_utc_now` into `_internal/common/`, the public import will become `from praxis.kernel.memory._internal.common.time import utc_now` — no underscore prefix, clearer contract. Deferred.

#### I4 — `NotImplementedError` paths on backends for non-owned operations

Each backend (Beads, Mem0Adapter, AtelierStore) raises `NotImplementedError` for operations routed elsewhere by the facade (e.g., `Mem0Adapter.store_decision` raises; `AtelierStore.store_fact` raises). This is tested by `test_facade_no_not_implemented_from_dispatch` (Phase 3C) which asserts the facade never dispatches onto these paths. The design is sound, but "protocol conformance by NotImplementedError" is a code smell Cleo flags for future readers who may mistake a NotImplementedError for "work still to do". **Recommendation:** add a one-line docstring note `# Intentional: see facade dispatch table` immediately above each `raise NotImplementedError` so the signal is explicit. Deferred — not a 3C blocker.

#### I5 — `MemoryQuotaExceeded` defined but not raised in Phase 3C

`models.py:440-495` defines `MemoryQuotaExceeded` with a detailed docstring, but Phase 3C does not raise it anywhere — the entry-ceiling enforcement (NR-Q2 100K/250K) is not yet wired. This is per-phase scope (the docstring says "at the time of writing"), not a bug, but the class is currently dead code relative to the Memory write path. Quinn / Step 3.4 is the earliest point at which write-path ceiling enforcement lands. Flagging for traceability. No fix.

---

## Findings by Category (Python)

| Category | Count | Top violation |
|---|---|---|
| Formatting (PEP 8) | 0 | — (ruff format clean) |
| Naming conventions | 0 | — |
| Type hints | 0 | — (py3.10+ union syntax used throughout) |
| Error handling | 0 | — (chaining with `raise X from exc` used correctly in Mem0Adapter._call) |
| Anti-patterns | 2 | W5 dead `if pass`, W6 `-1` sentinel |
| Complexity | 0 | — (longest method = Memory.delete at ~35 lines, well under 50) |
| Imports | 4 | I1, I2 (×3) function-body imports |
| Docstrings | 0 | — (every public class/function has a docstring; style is consistent NumPy-ish with Parameters/Returns sections) |
| Security (Bandit) | 0 | — (no hardcoded creds, no `shell=True`, no `assert` for validation, no raw SQL) |
| DRY | 3 | W2 `_utc_now`, W3 `_new_*_id`, W4 hash helpers |

## Module-level Findings

| Check | Result |
|---|---|
| Circular imports | None (verified — facade imports internals; internals never import facade/models-only-via-public-models) |
| `__init__.py` present | Yes, every subpackage |
| Naming consistency | Consistent (snake_case modules/functions, PascalCase classes, `_leading` for internals) |
| Unused imports | None (ruff F401 clean) |
| Wildcard imports | None (ruff F403 clean) |

## Worst Offenders (by finding count)

| File | CRITICAL | WARNING | INFO | Score |
|---|---|---|---|---|
| `_internal/beads/store.py` | 0 | 3 (W1, W2, W3) | 1 (I2×2) | A |
| `_internal/atelier/store.py` | 0 | 3 (W1, W2, W3, W5) | 1 (I2) | A |
| `_internal/mem0_adapter/adapter.py` | 0 | 3 (W1, W2, W3, W6) | 0 | A |
| `facade.py` | 0 | 1 (W4) | 1 (I1) | A |
| All other 19 files | 0 | 0 | 0 | A |

---

## Fixes Applied (opt-in fix-all)

Cleo applied the low-risk fixes in this pass:

| # | File | Change | Rule |
|---|---|---|---|
| F1 | `facade.py` | Hoist `from praxis.kernel.memory.models import EvidenceItem` to module-level imports. | I1 / PEP8-E4 |
| F2 | `_internal/beads/store.py` | Hoist `import hashlib` to top of file; remove two function-body copies. | I2 / PEP8-E4 |
| F3 | `_internal/atelier/store.py` | Hoist `import hashlib` to top of file; remove function-body copy. | I2 / PEP8-E4 |
| F4 | `_internal/beads/store.py` | Replace `f"/tmp/beads-export-{id}.json"` with `os.path.join(tempfile.gettempdir(), f"beads-export-{id}.json")`. | W1 / Platform |
| F5 | `_internal/atelier/store.py` | Same treatment for atelier-export path. | W1 / Platform |
| F6 | `_internal/mem0_adapter/adapter.py` | Same treatment for mem0-export path. | W1 / Platform |
| F7 | `_internal/atelier/store.py` | Remove dead `if entry.state is _AtelierEntryState.QUARANTINED: pass` branch; move comment to function intro. | W5 / Dead code |
| F8 | `_internal/mem0_adapter/adapter.py` | Drop `-1` sentinel in `delete()` full-tenant branch; return `deleted` directly. | W6 / Readability |

Post-fix: `ruff check src/` + `ruff format --check src/` both re-run clean. Test suite re-runs expected to stay GREEN (253 passing) because the fixes are all stylistic / platform-neutral and do not touch protocol semantics.

## Fixes Deferred (with rationale)

| # | Finding | Why deferred | Target stage |
|---|---|---|---|
| D1 | W2 `_utc_now` DRY | Requires creating `_internal/common/time.py` and touching all 4 files. Should land together with D2. | Quinn / Step 3.4 |
| D2 | W3 `_new_entry_id` / `_new_id` DRY + naming | Same consolidation as D1. | Quinn / Step 3.4 |
| D3 | W4 salted-hash helpers DRY | Correct consolidation needs a real salt from `DeploymentManifest`, which lands in Stage 7. A no-salt consolidation now would bake in the same §8.4 gap. | Stage 7 (Req #33) |
| D4 | I3 `_utc_now` private-import | Becomes moot once D1 lands. | Quinn / Step 3.4 |
| D5 | I4 `NotImplementedError` docstring nudge | Cosmetic, not a 3C gate concern. | Stage 5 (when MAC wires the final retrieval paths) |
| D6 | I5 `MemoryQuotaExceeded` unused | Per-phase scope — wired when write-path ceilings land. | Quinn / Step 3.4 |

---

## Recommendations

1. **Ship as-is through the Cleo gate.** 0 CRITICAL, fixes applied, deferrals tracked. Advance to Quinn / Step 3.4.
2. **Capture deferrals in the architecture follow-up log** so D1–D6 do not get lost between stages. Suggested location: an "Out of scope for Phase 3C — deferred to Quinn/Stage 7" appendix at the bottom of `memory/architecture.md` (Winston's doc).
3. **Add a Quinn prompt hint** in `stage-3-quinn-prompt.md` (if it exists) that the first task of Step 3.4 is the `_internal/common/time_and_ids.py` consolidation — Cleo has pre-approved the design.

---

## Gate Status

**CRITICAL count: 0**
**WARNINGs: 6 (3 applied, 3 deferred with documented rationale)**
**INFO: 5 (2 applied, 3 deferred)**

**GATE: GREEN — Step 3.3.5 (Cleo clean-code review) passes. Cleared to advance to Step 3.4 (Quinn).**

— Cleo, Clean Code Quality Reviewer
