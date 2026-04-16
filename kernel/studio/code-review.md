# Studio Python Glue — Clean Code Review Report

**Stage:** 6.3.5 Cleo (Clean Code Review)
**Reviewer:** Cleo (automated Cleo persona — no external `bmad-agent-clean-code-reviewer` skill registered; conducted inline per Stage 5.3.5 precedent)
**Date:** 2026-04-16
**Model:** claude-sonnet-4-6 (Sonnet 4.6 standard 200k)
**Target:** `_bmad-output/implementation-artifacts/praxis/studio/src/praxis/kernel/studio/` — Python glue only (YAML + Jinja2 templates reviewed separately)
**Binding:** Pipeline.md §6.3.5 checklist; stage-handoff §3 model map; `feedback_preload_first_gating.md`

---

## §1 — Scope & Files Reviewed

| File | Lines | Role |
|---|---|---|
| `schema.py` | 345 | Pydantic models — `WorkflowTemplate`, 2 enums, 5 validators |
| `models.py` | 268 | Frozen dataclasses — `ReasoningTrace`, `RenderedOutput`, `SessionResult`, A/B containers |
| `invoker.py` | 367 | `StudioSession` + `template_to_task_input`; MAC protocol stubs |
| `register_check.py` | 222 | `RegisterChecker` — 4 drift-marker regex categories (ADR-11) |
| `renderer.py` | 138 | `TemplateRenderer` — Jinja2 rendering + invisible-mode provenance strip |
| `harness.py` | 311 | `ABHarness` — 3-path A/B comparison + `ComparisonReport` |
| `__init__.py` | 82 | Public surface re-export |

**Explicitly out of scope:** `strategic_session.yaml`, `strategic_session_quick.yaml`, all `templates/` Jinja2 files, `register_guide.md`, `pyproject.toml`.

---

## §2 — Summary

| Severity | Count | Post-fix count |
|---|---|---|
| CRITICAL | 2 (same block — 1 fix) | **0** ✓ |
| WARNING | 4 (auto-fix applied) + 4 (deferred) | 0 closed + 4 forwarded to Stage 7 |

**Gate:** 0 CRITICAL violations remaining. **Advancement to Quinn (6.4) unblocked.**

---

## §3 — CRITICAL Violations (resolved)

### C-1 · `harness.py:287-293` — Wrong key access + malformed f-string format spec in `generate_report()`

**Status:** RESOLVED (auto-fix applied)

**File/lines:** `harness.py:287-293`

**Description:** Two bugs in the same block — both cause runtime exceptions whenever R5 gate data is present in a comparison run.

**Bug 1 — KeyError (wrong dict key):**

`per_gate_rows` items are built at lines 252-262 with keys `gate_id`, `studio_avg`, `baseline_avg`, `delta`. The dissent-analysis block at lines 287-288 accessed `r["studio_score"]` and `r["baseline_score"]` — neither key exists. This raises `KeyError("studio_score")` whenever any question has R5 gate scores (i.e., in any real benchmark run).

**Bug 2 — Malformed f-string format spec:**

```python
# BEFORE (raises IndexError when empty, ValueError when non-empty)
f"{r5_studio[0]:.2f if r5_studio else 'n/a'}"
```

Python f-string parsing splits at the first `:` not inside brackets: expression = `r5_studio[0]`, format spec = `.2f if r5_studio else 'n/a'`. The ternary lives in the format spec, not the expression. Python evaluates `r5_studio[0]` unconditionally (→ `IndexError` when list is empty), then passes the literal string `.2f if r5_studio else 'n/a'` to `float.__format__` (→ `ValueError: Invalid format specifier`). Neither branch produces a valid result.

**Fix applied:**

```python
# AFTER — harness.py:287-294
r5_studio = [r["studio_avg"] for r in per_gate_rows if r.get("gate_id") == "R5"]
r5_baseline = [r["baseline_avg"] for r in per_gate_rows if r.get("gate_id") == "R5"]
r5_s = f"{r5_studio[0]:.2f}" if r5_studio else "n/a"
r5_b = f"{r5_baseline[0]:.2f}" if r5_baseline else "n/a"
dissent_analysis = (
    f"R5 Dissent Preservation — Studio avg: {r5_s}, "
    f"Baseline avg: {r5_b}."
)
```

Keys corrected (`studio_avg`, `baseline_avg`). Ternary moved to the expression position; format spec is unconditionally `.2f` and applied only when the list is non-empty.

---

## §4 — Auto-fixes Applied

### AF-1 · `schema.py:192-194` — Dead code: `_VALID_GATE_IDS` frozenset

**Status:** REMOVED

`_VALID_GATE_IDS = frozenset(f"R{n}" for n in range(1, 13))` was defined at module level but never referenced anywhere. Gate-ID validation is already enforced by the `Literal["R1", ..., "R12"]` type in `QualityGateSpec.gate_id`. Deleted 4 lines.

---

### AF-2 · `__init__.py:77` — Duplicate `"RenderedOutput"` in `__all__`

**Status:** REMOVED

`RenderedOutput` appeared twice in `__all__`: once in the models section (correct, imported from `models`) and once in the utilities section (erroneous, re-listed alongside harness exports). Duplicate removed from the utilities section. The canonical listing in the models section is preserved.

---

### AF-3 · `register_check.py:119` — `re.Match` missing `[str]` type parameter

**Status:** FIXED

```python
# BEFORE
def _extract_context(text: str, match: re.Match) -> str:  # type: ignore[type-arg]

# AFTER
def _extract_context(text: str, match: re.Match[str]) -> str:
```

`re.Match[str]` is valid in Python 3.8+ (`from __future__ import annotations` is present). The `# type: ignore[type-arg]` suppressor is no longer needed and has been removed.

---

## §5 — WARNING Violations (deferred to Stage 7 debt ledger)

The following four WARNINGs are non-blocking for Quinn (6.4) and are deferred per the established Stage 7 debt-ledger pattern. None affect correctness within the current test suite scope.

### W-1 · `invoker.py:183-186` — Broad `except Exception` with fragile string-matching

```python
except Exception as exc:
    if "budget" in str(exc).lower():
        return self._degraded_result(...)
    raise
```

Catches all `Exception` subclasses including programming errors and third-party library exceptions. The budget-detection heuristic (`"budget" in str(exc).lower()`) is fragile — any exception whose message happens to contain "budget" silently triggers degraded mode instead of propagating. Pattern parallels MAC W-3 (deferred at Stage 5.3.5). **Deferred to Stage 7 — W-1.**

---

### W-2 · `invoker.py:159` — `renderer: Any` loses type safety

```python
def __init__(self, mac: MACProtocol, cost_tracker: CostTrackerProtocol, renderer: Any) -> None:
```

The comment says "avoid circular import" but `TemplateRenderer` is already imported in `renderer.py` with no circular chain. The `Any` annotation means all `self._renderer.render(...)` calls are unchecked by mypy. Pattern parallels MAC W-7 (deferred at Stage 5.3.5). Correct fix: `from __future__ import annotations` guard + `TYPE_CHECKING` conditional import of `TemplateRenderer`. **Deferred to Stage 7 — W-2.**

---

### W-3 · `invoker.py:200,256,330` + `harness.py:107-108` — Deferred imports inside methods (4 occurrences)

`from praxis.kernel.studio.models import ReasoningTrace` (and others) are deferred inside `invoke()`, `_extract_trace()`, `_degraded_result()`, and `run_studio()`. Deferred imports avoid circular import issues but: (1) slow the first call through cache-miss overhead, (2) obscure dependencies, (3) are asymmetric with the top-level imports already present in the same files. Root cause is the same circular import concern as W-2 — addressable together via `TYPE_CHECKING` guards. **Deferred to Stage 7 — W-3.**

---

### W-4 · `harness.py:104-116` — Silent fallback returns empty `RenderedOutput` with no logging

```python
if result.outputs:
    return result.outputs[0]
# Fallback — should not occur in practice
...
return RenderedOutput(text="", ...)
```

The comment says "should not occur in practice" but provides no logging, no metric emission, and no exception. An empty `RenderedOutput` silently corrupts A/B comparison results — a Studio run with zero outputs would score as composite=0 without surfacing the failure. Should raise `RuntimeError` or at minimum emit a Pi-Mono label. **Deferred to Stage 7 — W-4.**

---

## §6 — Observations (informational, no action required)

- **`models.py`** — Clean. All dataclasses are `frozen=True`. No mutability violations. `ReasoningTrace` contract matches test-strategy §14.3 fixture spec exactly.
- **`schema.py`** — Validators are comprehensive (budget_pct sum, depends_on DAG, circular reference DFS). `model_config = ConfigDict(frozen=True)` on all submodels is correct.
- **`renderer.py`** — `_apply_provenance_strip` invisible-mode implementation matches ADR-09 §D fold-back checklist. `verify_invisible_clean` public method correctly scoped for STUDIO-T-PROV-LEAK-04.
- **`register_check.py`** — Drift marker catalogs are well-organized. The `_RISK_DOMAIN_BEFORE` pattern for contextual "critical" exemption (`\b(risk|failure|error|...)\b\s+\w+\s*$`) uses a trailing `$` anchored to the preceding substring (lines 91-94), which correctly limits the lookbehind window. The feedback_hard_constraint_word_boundary feedback (word-boundary `\b` on all markers) is satisfied.
- **`harness.py:144-197`** — `run_full_comparison` correctly sequences three independent timing blocks. Blind-evaluation `anonymize()` satisfies STUDIO-T-AB-BLIND-01/02/03 (label strip + shuffle).

---

## §7 — Stage 7 Debt Ledger additions

Items forwarded from this review (appended to the 13-item ledger from Stage 5 + 6.0.3):

| ID | Location | Description |
|---|---|---|
| W-1 | `invoker.py:183` | Broad `except Exception` with fragile budget string-match |
| W-2 | `invoker.py:159` | `renderer: Any` — should be `TemplateRenderer` under `TYPE_CHECKING` |
| W-3 | `invoker.py:200,256,330`; `harness.py:107` | Deferred imports inside methods (4 occurrences) |
| W-4 | `harness.py:104-116` | Silent empty-`RenderedOutput` fallback — should raise or log |

Stage 7 debt ledger is now **17 items** (13 prior + 4 from Stage 6.3.5).

---

## §8 — Files modified by this review

| File | Change |
|---|---|
| `src/praxis/kernel/studio/harness.py` | CRITICAL fix: lines 287-294 — wrong keys + malformed f-string |
| `src/praxis/kernel/studio/schema.py` | AF-1: removed `_VALID_GATE_IDS` dead code |
| `src/praxis/kernel/studio/__init__.py` | AF-2: removed duplicate `"RenderedOutput"` from `__all__` |
| `src/praxis/kernel/studio/register_check.py` | AF-3: `re.Match` → `re.Match[str]`, removed `# type: ignore` |

---

## §9 — Gate Decision

**PASS — 0 CRITICAL violations remaining.**

Stage 6.4 Quinn (QA) may proceed.

Quinn reads:
- `studio/test-strategy.md` — 116 test IDs (§3–§12)
- `studio/code-review.md` (this document) — 4 Stage-7 WARNINGs for awareness
- Runs `pytest studio/tests/` — gate: coverage ≥ 80%, benchmark regression pass, dissent preservation verified

Quinn must **not** open the 4 deferred WARNINGs as blocking items; they are Stage 7 debt.
