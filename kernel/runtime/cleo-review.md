# Stage 4.3.5 Cleo Clean Code Review Report

**Reviewer:** Cleo (BMAD Clean Code Reviewer, Stage 4.3.5)
**Subject:** Stage 4.3 Amelia Runtime Implementation
**Date:** 2026-04-13
**Commit reviewed through:** `c269b90` (before auto-fix) → auto-fix `2d6e2c6`
**Python:** 3.12.12 (memory venv)
**Verdict:** ~~RATIFY WITH CONDITIONS~~ → **RATIFY** *(upgraded 2026-04-13 after M1–M5 closure)*

**Remediation commits:**
- `2d6e2c6` — ruff auto-fix (M2/M3/M4 precursor — style)
- `9ea12e8` — M2/M3/M4: pyproject.toml (markers, dependencies, mypy_path)
- `4bb9f46` — M1/M5: mypy --strict compliance + drain_loop.py OQ-N authorization comment

---

## 1. Executive Summary

Reviewed all 54 source files under `src/praxis/kernel/runtime/` and all 65 test files under
`tests/runtime/` across the three-checkpoint Runtime implementation. All 334 tests pass. All
§13.6 coverage gates are met (96% TOTAL). All four R53 structural guards are green. F-13.C1
`no_waiver` is present, unmarked, and passing against a real Postgres fixture with physical xmin
proof. Stage 3 memory canary is 264/264 zero regression throughout.

**Finding counts (original → resolved):**
| Severity | Count | Status |
|---|---|---|
| BLOCKER | **0** | — |
| MAJOR | **5** | **5/5 CLOSED** (`9ea12e8` + `4bb9f46`) |
| MINOR | **8** | 8 documented, non-blocking |
| NITPICK | **9 residual** (ruff-unfixable) | documented |

**Verdict rationale:** No BLOCKERs. All 5 MAJORs resolved:
- M1 (34 mypy errors) → 0 runtime mypy errors post `4bb9f46`
- M2 (unregistered marks) → 10 markers registered, `--strict-markers` clean post `9ea12e8`
- M3 (missing dependencies) → `[project.dependencies]` + `[project.optional-dependencies]` added post `9ea12e8`
- M4 (missing mypy_path) → `mypy_path` configured, 106→15 errors (15 pi-mono pre-existing, frozen) post `9ea12e8`
- M5 (_internal coupling) → Option A accepted; OQ-N authorization comment added to `drain_loop.py` post `4bb9f46`

All R53 guards, F-13.C1, Checkpoint 3 clean-commit record, and 334/334 test suite hold.

---

## 2. Toolchain Output Summary

### 2.1 ruff

**Before auto-fix (`2d6e2c6`):**
- `ruff check`: 91 violations — 43 `I001` unsorted-imports, 34 `F401` unused-imports,
  10 `E501` line-too-long, 4 `F841` unused-variable. 77 auto-fixable.
- `ruff format`: 43 files would be reformatted.

**After auto-fix:**
- `ruff check`: 9 remaining (5 `E501`, 4 `F841` — all non-auto-fixable, documented in §8)
- `ruff format`: 0 deltas; 125 files clean.

### 2.2 mypy

Invocation: `MYPYPATH="src;../memory/src;../pi-mono/src" mypy src/praxis/kernel/runtime --explicit-package-bases`

**Runtime-source errors: 34** in 6 files (pi-mono pre-existing errors excluded — Stage 1 is frozen).

| File | Error count | Top error |
|---|---|---|
| `proxies/producer.py` | 20 | `[unused-ignore]` + `[attr-defined]` per method (×10 methods) |
| `proxies/reviewer.py` | 4 | Same pattern (×2 methods) |
| `jobs/schema.py` | 2 | `dict` missing type args (lines 80, 101) |
| `jobs/worker.py` | 5 | `dict` type args (×3) + `Result.rowcount` + `FailureReason` not exported |
| `outbox/path_a.py` | 1 | `dict` missing type args (line 63) |
| `mcp_adapter/transport.py` | 2 | Missing return type + wrong `[type: ignore]` code |

See MAJOR finding M1 for full classification and remediation plans.

**Note:** `pyproject.toml`'s `[tool.mypy]` does not set `mypy_path`. Running `mypy .` without the
external `MYPYPATH` env var produces 106 errors (many spurious import-not-found cascades).
See MAJOR finding M4.

### 2.3 pytest

| Run | Result |
|---|---|
| Full runtime suite (pre-fix) | 334/334 passed, 86 warnings |
| Full runtime suite (post-fix) | 334/334 passed, 86 warnings |
| Stage 3 memory canary (post-fix) | 264/264 passed |

No tests failed at any point in the review execution. The 86 warnings are `PytestUnknownMarkWarning`
entries — see MAJOR finding M2.

### 2.4 Coverage (§13.6 gates)

| Module | Gate (§13.6) | Line % | Branch % | Status |
|---|---|---|---|---|
| `proxies/` | ≥95% | **100%** | — | ✅ |
| `spawner/` | ≥95% | **97%** | — | ✅ |
| `jobs/` | ≥95% | **99%** | — | ✅ |
| `outbox/` | ≥95% | **100%** | — | ✅ |
| `observability/` | ≥90% | **99%** | — | ✅ |
| `registry/` | ≥90% | **98%** | — | ✅ |
| `tools/` | ≥85% | **88%** | — | ✅ (individual file gaps → see §8) |
| `loader/` | ≥85% | **94%** | — | ✅ |
| `mcp_adapter/` | ≥85% | **89%** | — | ✅ |
| `models.py` | ≥90% | **98%** | — | ✅ |
| **TOTAL** | — | **96%** | — | ✅ |

Note: architecture.md §11.11 specifies `loader/ ≥95%` and `proxies/ ≥98%` — both stricter than
§13.6. Actual values (94% and 100% respectively) meet §11.11 for proxies but miss §11.11 for
loader (94% vs 95%). §13.6 is the operative DoD gate (explicitly referenced in §13.7 item 4);
§11.11 discrepancy is documented as MINOR finding M-8.

---

## 3. R53 Structural Guards Status

| Guard | Test file | Result | Evidence |
|---|---|---|---|
| **Guard 1: is-identity** | `test_telemetry_event_import_identity.py` | ✅ 2/2 PASSED | `RuntimeTE is MemoryTE` Python `is` assertion holds |
| **Guard 2: AST scan — no parallel type** | `test_no_parallel_telemetry_event_type.py` | ✅ 3/3 PASSED | Zero `class TelemetryEvent` / `class RuntimeTelemetryEvent` under `runtime/` |
| **Guard 3: no extra='allow'** | `test_no_extra_allow_in_observability.py` | ✅ 4/4 PASSED | Zero `extra="allow"` in `observability/` |
| **Guard 4: wrapper delegation** | `test_runtime_telemetry_envelope_wrapper.py` | ✅ 7/7 PASSED | `to_telemetry_event()` returns imported TelemetryEvent type |

**All 16 guard tests green.** Q3 option (b) structural enforcement holds post-Checkpoint-3.

**`_r53_allowlist.txt` field verification:** `TelemetryEvent.model_fields` confirmed at runtime:
`['metric_name', 'metric_type', 'value', 'labels', 'timestamp', 'praxis_version', 'tenant_hash']`
Matches the 7 ALLOWED fields in `observability/_r53_allowlist.txt` exactly. ✅

---

## 4. F-13.C1 no_waiver Proof

**Test:** `tests/runtime/outbox/test_path_a_atomicity.py::test_f13_c1_path_a_shared_transaction_via_xmin`

**Verification checklist:**
- Present: ✅ (line 97)
- Marker `@pytest.mark.critical`: ✅ (line 94)
- Marker `@pytest.mark.no_waiver`: ✅ (line 95)
- Marker `@pytest.mark.f1_absorption`: ✅ (line 96)
- No `@pytest.mark.skip`: ✅
- No `@pytest.mark.xfail`: ✅
- No `@pytest.mark.flaky_quarantine`: ✅
- Uses real Postgres (`@requires_postgres` + `cost_repo_pg` fixture): ✅
- Test result: **PASSED**

**Test output (Step 4 run):**
```
1 passed, 8 warnings in 5.79s
```

The test executes a Postgres `SELECT j.xmin = e.xmin AS same_transaction FROM jobs_queue j JOIN
events_outbox e` and asserts `result[2] is True`. Physical xmin identity proves both the
`UPDATE jobs_queue SET state='completed'` and the `INSERT INTO events_outbox` committed in the
same Postgres transaction — the structural proof for NFR-C-A1.

**F-13.C1 status: PRESENT, NOT SKIPPED, NOT XFAILED, NOT QUARANTINED, PASSING. No waiver.**

---

## 5. Stage 3 Memory Canary

```
264 passed in 5.16s  (pre-fix, Step 3)
264 passed in 4.75s  (post-fix, Step 7 verification)
```

Zero regressions throughout the review. Stage 3 Memory frozen — no `memory/src/` modifications
detected during Stage 4.3. The only Stage 3 addition was the F-5 `telemetry.py` (commit
`6209b50`, ratified during Amelia preload, additive only).

---

## 6. BLOCKER Findings

**None.**

---

## 7. MAJOR Findings

### M1 — mypy --strict non-compliance (34 errors, 6 files)

**Location:** `src/praxis/kernel/runtime/proxies/producer.py` (20 errors),
`proxies/reviewer.py` (4), `jobs/schema.py` (2), `jobs/worker.py` (5),
`outbox/path_a.py` (1), `mcp_adapter/transport.py` (2).

**Finding:** §13.7 item 5 requires mypy --strict clean on each module. 34 runtime-source errors
fail this gate.

**Root causes and remediation plans:**

**M1.a — Proxy `# type: ignore` wrong error codes (24 errors)**
`proxies/producer.py` and `proxies/reviewer.py` use `# type: ignore[union-attr]` on all memory
delegation calls. The actual mypy error is `[attr-defined]` (because `_memory: object` doesn't
have the Memory protocol methods). mypy then issues `[unused-ignore]` for the wrong code AND
`[attr-defined]` for the actual error.

Root cause: `memory: object` was chosen as the least-coupled type annotation for the Memory
facade. This is a defensible design choice (no import coupling to Memory's protocol type), but
the resulting `# type: ignore` suppression is incorrectly typed.

Remediation plan (in order of preference):
1. (Preferred) Add a minimal `MemoryFacadeProtocol` to `proxies/_base.py` with `Protocol`
   type stubs for all 10 Memory methods, and type `_memory` as `MemoryFacadeProtocol`. This
   gives mypy proper type information without importing from `memory/` — the protocol can be
   defined locally using `typing.Protocol`.
2. (Acceptable) Change all `# type: ignore[union-attr]` → `# type: ignore[attr-defined]`
   in `producer.py` and `reviewer.py`. Fast fix, trades type safety for suppression.
3. (Not recommended) Change `_memory: object` → `_memory: Any` and add `from typing import
   Any`. Silences mypy but loses all downstream type checking.

Deadline: Before Stage 4.5 Alignment Review. Does not block Stage 4.4 Quinn.

**M1.b — Bare `dict` type args (6 instances)**
`jobs/schema.py:80,101`, `jobs/worker.py:134,173,189`, `outbox/path_a.py:63` use bare `dict`
instead of `dict[str, Any]` or a typed dict. Standard mypy --strict violation.

Remediation: Add `dict[str, Any]` type argument at each location. Add `from typing import Any`
if not already imported.

**M1.c — `transport.py:make_stdio_params` missing return type**
```python
def make_stdio_params(config: StdioTransportConfig):  # type: ignore[return]
```
mypy reports `[no-untyped-def]` but the comment covers `[return]`. Function is missing a return
type annotation. `StdioServerParameters` is imported inside the function body (lazy import).

Remediation: Add `-> Any` return type (since `StdioServerParameters` is only available if `mcp`
is installed) and fix the `# type: ignore` comment to `# type: ignore[no-untyped-def]`, or
guard with `TYPE_CHECKING` for the proper type.

**M1.d — `worker.py:92` SQLAlchemy `Result.rowcount`**
```python
result = await session.execute(text("UPDATE jobs_queue SET state='claimed'..."))
# worker.py:92
n_reclaimed = result.rowcount
```
mypy reports `"Result[Any]" has no attribute "rowcount"`. SQLAlchemy async `execute()` returns
`Result[Any]` but `.rowcount` is on `CursorResult`. The code is functionally correct (SQLAlchemy
exposes rowcount at runtime) but mypy can't see it through the type stubs.

Remediation: Add `# type: ignore[attr-defined]` at line 92 with an explanatory comment, or cast
to `sqlalchemy.engine.CursorResult`.

**M1.e — `retry.py` not exporting `FailureReason`**
`retry.py.__all__ = ["backoff", "get_final_state", "get_alert_severity"]` — missing
`FailureReason`. `worker.py:191` imports `FailureReason` from `retry.py`. mypy --strict flags
this as unexported.

Remediation: Add `"FailureReason"` to `retry.py`'s `__all__`.

---

### M2 — pytest custom marks not registered (86 warnings per run)

**Location:** `pyproject.toml` `[tool.pytest.ini_options]` — no `markers` section.

**Finding:** The test-strategy §12.1 defines 17+ custom markers (`critical`, `no_waiver`,
`r53_structural`, `f1_absorption`, `f3_absorption`, `integration`, `static`, `property`,
`wall_clock`, `e2e`, `oqn_escalation_canary`, `asyncio_structural`, etc.). None of these are
registered in `pyproject.toml`.

**Impact:**
1. Every `pytest` invocation produces 86 `PytestUnknownMarkWarning` entries — noise that can
   mask real warnings.
2. `pytest --strict-markers` (a CI best practice) would fail at collection.
3. The `no_waiver` meta-check (test-strategy §13.4, OQ-TS-9) uses marker filtering — unreliable
   without registration.
4. The §12.1 formal marker taxonomy investment is functionally inert until registered.

**Remediation plan:** Add `markers` section to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
# ... existing ...
markers = [
    "critical: Risk-bearing test — maps to S4.R-* closure targets",
    "no_waiver: No-waiver test — cannot be skipped or quarantined",
    "r53_structural: R53 field allowlist structural enforcement",
    "f1_absorption: F-1 Path A/B outbox absorption tests",
    "f3_absorption: F-3 Jobs infrastructure tests",
    "integration: Integration test (requires real Postgres)",
    "static: Static/structural test (mypy, grep, AST scan)",
    "property: Property-based test (Hypothesis)",
    "wall_clock: Wall-clock sensitive test (NFR-Q6 timing)",
    "e2e: End-to-end test",
    "oqn_escalation_canary: OQ-N canary tests",
    "asyncio_structural: Asyncio structural tests",
]
filterwarnings = [
    "error::pytest.PytestUnknownMarkWarning",
]
```
Adding `filterwarnings = ["error::PytestUnknownMarkWarning"]` converts unknown marks to errors
so any new unregistered mark is caught at CI time.

Deadline: Before Stage 4.4 Quinn. Quinn's formal QA pass should run with registered markers
so that `pytest -m "critical and no_waiver"` produces reliable selection.

---

### M3 — `pyproject.toml` missing `[project.dependencies]`

**Location:** `pyproject.toml` — no `dependencies` field under `[project]`.

**Finding:** `pyproject.toml` declares `name = "praxis-runtime"` and `requires-python = ">=3.12"`
but has no `dependencies = [...]`. A `pip install .` from this package would not install any
runtime dependencies. The tests require at minimum:

- `mcp>=1.9.0` (MCP SDK — 6 source files import from it; test collection fails without it)
- `sqlalchemy[asyncio]>=2.0` (ORM + async engine)
- `psycopg[binary]` or `asyncpg` (Postgres driver)
- `pydantic>=2.0`
- `hypothesis` (property-based tests)
- `pytest-asyncio`, `pytest-cov`

**Impact:** A fresh environment `pip install praxis-runtime && pytest` would fail at collection
with `ModuleNotFoundError: No module named 'mcp'` — exactly what happened in this review's
Step 2.

**Remediation plan:** Add `[project.dependencies]` with runtime deps, and
`[project.optional-dependencies] dev = [...]` or `[dependency-groups] test = [...]` for test
deps. Minimum required runtime deps: `mcp`, `sqlalchemy[asyncio]`, `pydantic`, `psycopg[binary]`.

Note on `mcp` version: Architecture §C3 notes `mcp 1.27.0` as the targeted version.
`mcp 1.9.0` was used in this review (pip latest). The `version_guard.py` test
(`test_sdk_version_guard.py`) should pin and validate the version contract.

Deadline: Before Stage 4.4 Quinn. Quinn's environment setup requires this.

---

### M4 — `pyproject.toml` missing `mypy_path` for multi-package namespace

**Location:** `pyproject.toml` `[tool.mypy]` section.

**Finding:** The Runtime package imports from `praxis.kernel.memory.*` and
`praxis.kernel.cost.*` (pi-mono) which live in sibling `../memory/src/` and `../pi-mono/src/`
directories. `pyproject.toml` configures `pythonpath = ["src", "../memory/src"]` for pytest
but mypy has no equivalent `mypy_path` configured.

Running `mypy src/praxis/kernel/runtime` without the external `MYPYPATH` env var produces 106
errors (72 spurious `import-not-found` cascades that dwarf the 34 real errors). This review
required manually setting `MYPYPATH="src;../memory/src;../pi-mono/src"` to get the correct 34.

**Impact:**
1. A CI step running `mypy .` would report 106 errors — making the real errors invisible.
2. Anyone running mypy locally without knowing to set `MYPYPATH` gets false cascade errors.
3. Stage 4.5 Alignment Review's mypy gate would be unreliable.

**Remediation plan:** Add to `pyproject.toml`:
```toml
[tool.mypy]
python_version = "3.12"
strict = true
explicit_package_bases = true
mypy_path = ["src", "../memory/src", "../pi-mono/src"]
```
This ensures `mypy .` from the `runtime/` directory finds all cross-package imports without
environment variable workarounds.

Deadline: Before Stage 4.4 Quinn.

---

### M5 — `drain_loop.py` runtime `_internal` coupling (OQ-N Path (i) authorized, undocumented)

**Location:** `src/praxis/kernel/runtime/outbox/drain_loop.py:20`
```python
from praxis.kernel.memory._internal.audit import AuditEvent, AuditEventType
```

**Finding:** Application source code imports from `praxis.kernel.memory._internal.audit` at
runtime. The `_internal` boundary is a standard Python convention for private module internals
not intended for external consumers.

**Context:** This coupling is architecturally authorized. OQ-N Path (i) requires direct access
to `AuditEventType` enum values to filter events in `_PATH_B_EVENT_TYPES`. There is no public
API for `AuditEventType` in the Memory package — the enum lives in `_internal.audit`. The
architecture §16.3 explicitly notes `outbox/path_b.py` as the "OQ-N Path (i) shim test bed"
and requires Amelia to read `memory/_internal/audit.py` directly. This was ratified at
Checkpoint 2 by Andrey.

Note: `path_b.py` uses `if TYPE_CHECKING:` to import `AuditBuffer` and `AuditEvent` — this
is a TYPE_CHECKING-only import (no runtime coupling) and is the correct pattern. Only
`drain_loop.py` has a genuine runtime `_internal` import.

**Gap:** The code comment does not document the OQ-N Path (i) authorization for this `_internal`
coupling. Without documentation, a future reviewer would flag this as an unauthorized internal
import and potentially "clean it up" by breaking the implementation.

**Remediation plan:** Add an explicit comment to `drain_loop.py` lines 19-20:
```python
# OQ-N Path (i) — AuditEventType imported directly from memory._internal.audit
# because no public API exists for event type filtering.  This coupling is
# architecturally authorized per architecture §16.3 + Checkpoint 2 ratification
# (2026-04-13).  If Memory ever exports AuditEventType publicly, migrate this import.
from praxis.kernel.memory._internal.audit import AuditEvent, AuditEventType
```

**Reserve question for Andrey (before Stage 4.5):** The preload brief §6a specified "Zero hits
in application code" as the expected result. This MAJOR finding deviates from that expectation.
Two options:
- Option A: Accept MAJOR disposition (documentation comment sufficient, no architecture change)
- Option B: Elevate to BLOCKER requiring Memory to expose `AuditEventType` publicly before
  Stage 4.5 (adds a Memory §10 amendment and a small Stage 3 additive change similar to F-5)

This review recommends **Option A** — the `_internal` coupling is narrow (one enum import),
well-scoped (only for Path B event filtering), and already ratified. A public API addition for
a single enum adds process overhead with minimal benefit. But Andrey must make this call
explicitly before Stage 4.5 Alignment Review.

---

## 8. MINOR Findings

### Minor-1 — a6ef167 §13.7 letter violation (Path α accepted)

**Finding:** Commit `a6ef167 feat(jobs+outbox): implement Checkpoint 2` bundled 12 implementation
files with two test files (`tests/runtime/jobs/test_claim_and_worker.py` and
`tests/runtime/outbox/test_schema_and_coverage.py`), violating the §13.7 test-first audit rule
at the letter level.

**Substance-over-form analysis:** All F-13.C1/F-1.H*/OQ-N risk-bearing tests landed test-first
in preceding commits (`62047dc`, `4b1e737`, `6a2457b`). The bundled tests are: F-3.H4 concurrent
claim fencing, F-3.H5 NFR-Q6 orphan reclaim, and defensive coverage fillers. F-3.H4/F-3.H5
describe specification-constrained behaviors (`FOR UPDATE SKIP LOCKED`, orphan-to-pending
reclaim) where retrofit bias risk is minimal.

**Disposition:** Path α per preload brief Item 3 — accepted by Andrey at ratification.
No history rewrite. Documentation only.

**Also noted:** Commit `c269b90 test(coverage): add registry find_agents + mcp_adapter error
path coverage fillers` adds two test files after their implementation commits (`36d5e7e` for
mcp_adapter, `31c3ce0` for registry). Structurally different from a6ef167 (separate commit, not
bundled) but still post-implementation testing. Same substance-over-form disposition — both
registry find_agents and mcp_adapter error paths are supplementary coverage fillers, not
risk-bearing specifications. Accepted.

**Pattern note for Amelia:** Both violations occurred in the same window (Checkpoint 2 +
post-Checkpoint-3 cleanup). Checkpoint 3 itself was clean (zero bundled commits). The test-first
discipline improved across checkpoints. Future work: commit coverage fillers in their own
`test(module): add coverage filler for X path` commits BEFORE the feat() implementation commit,
even when the filler tests are low-risk.

---

### Minor-2 — subprocess_mcp.py per-file coverage 70% (Class D enforcement paths uncovered)

**Location:** `src/praxis/kernel/runtime/tools/subprocess_mcp.py`
**Covered:** 14/20 stmts = 70%
**Uncovered lines:** 55-58, 65-68

**Uncovered code:**
- Lines 55-58: `check_binary_allowed()` rejection path — the `raise ToolNotAllowedError(...)`
  when a binary is NOT in `_BINARY_ALLOWLIST`
- Lines 65-68: `check_agent_allowed()` rejection path — the `raise ToolNotAllowedError(...)`
  when an agent is NOT in `SUBPROCESS_AGENT_ALLOWLIST`

**Risk assessment:** These are the **Class D binary/agent allowlist enforcement paths** — the
only code that enforces the "narrow per-binary allowlist" and "tight agent allowlist" per
§6.1.7b. They ARE risk-bearing: if these paths were broken by a refactor, the enforcement would
fail silently. Example: calling `check_binary_allowed("curl")` should raise `ToolNotAllowedError`
but this is never verified by the current test suite.

**Aggregate gate status:** `tools/` aggregate is 88% — passes the §13.6 ≥85% gate. Per Q8.2
resolution, this is MINOR (aggregate passes). But the specific paths are security-adjacent.

**For Quinn (Stage 4.4):** Add tests for the rejection paths:
```python
def test_check_binary_allowed_rejects_disallowed():
    adapter = SubprocessMcpAdapter()
    with pytest.raises(ToolNotAllowedError, match="not in allowlist"):
        adapter.check_binary_allowed("curl")  # curl is not in _BINARY_ALLOWLIST

def test_check_agent_allowed_rejects_disallowed():
    adapter = SubprocessMcpAdapter()
    with pytest.raises(ToolNotAllowedError, match="not in agent allowlist"):
        adapter.check_agent_allowed("bmad-agent-analyst")  # not in SUBPROCESS_AGENT_ALLOWLIST
```

---

### Minor-3 — fs_mcp.py per-file coverage 75% (Class C enforcement path uncovered)

**Location:** `src/praxis/kernel/runtime/tools/fs_mcp.py`
**Covered:** 30/40 stmts = 75%
**Uncovered lines:** 69, 73, 81, 86, 90, 94, 98, 110-113

**Uncovered code:**
- Lines 69, 73: `return True` branches inside the glob loop in `is_path_denied()` — fallback
  path when `fnmatch.fnmatch(normalized, pattern)` or `fnmatch.fnmatch(filename, pattern)`
  matches. These are redundant with the regex check (line 63) and likely never triggered by
  the test suite's denylist test cases (regex catches them first).
- Lines 81, 86, 90, 94, 98: Additional `return True` branches for specific file name checks
  (`credentials.json`, `credentials.yaml`, `.ssh` directory, `.env*`, `credentials.*`) —
  defensive fallbacks that the leading regex likely pre-empts.
- Lines 110-113: **The `pre_invoke_check()` rejection path** — `raise FileSystemAccessDeniedError`
  when `is_path_denied(path)` returns True. This is the primary Class C enforcement entry point
  at the adapter layer (per §9.6) and its rejection branch is uncovered.

**Risk assessment:** The `pre_invoke_check()` rejection path (lines 110-113) is the most
significant — it's the Class C security enforcement entry point. The glob fallback branches
(69, 73) are lower priority since the regex pre-empts them.

**For Quinn:** Add test for the `pre_invoke_check()` rejection path and at least one glob-only
match that bypasses the regex.

---

### Minor-4 — Q5 metric architecture gap

**Location:** `src/praxis/kernel/runtime/spawner/spawner.py` (Q5 metric implementation)
**Finding:** `runtime.agent.allowlist.stripped.count{parent_agent, child_agent, stripped_tool}`
is implemented in `spawner.py` and emitted correctly per test coverage, but `architecture.md §10`
(Observability Hooks) does not enumerate it. Q5 was resolved during Checkpoint 1 planning.

**Disposition:** MINOR. Additive metric, non-breaking, no naming conflict with existing §10 entries.

**Action required at Stage 4.5 Alignment Review:** Winston must add Q5 to architecture.md §10
before Stage 4.7 closes. Alignment Review should include this as a binding checklist item.

Does not block Stage 4.4 Quinn.

---

### Minor-5 — `drain_loop.py` `_internal` AuditEvent TYPE_CHECKING companion

**Location:** `src/praxis/kernel/runtime/outbox/drain_loop.py:20`
**Finding:** See MAJOR finding M5 for the runtime `AuditEventType` import. This MINOR covers
the `AuditEvent` import from the same line — used as a type annotation in the `drain_once()`
function signature. The `AuditEvent` type annotation could be moved under `TYPE_CHECKING` (as
`path_b.py` correctly does) to remove the runtime `_internal` coupling for the type-only usage.
The `AuditEventType` enum value usage is the genuine runtime coupling.

**Disposition:** Acceptable as-is (both imports are on the same line; splitting would be micro-
optimization). Document in the M5 remediation comment. If M5 is resolved via Memory exposing
`AuditEventType` publicly, revisit this import at the same time.

---

### Minor-6 — Sync test functions with `@pytest.mark.asyncio` in test_path_b_drain.py

**Location:** `tests/runtime/outbox/test_path_b_drain.py` — 4 test functions
**Finding:** `pytest-asyncio` warns:
```
PytestWarning: The test <Function test_oqn_t2_concurrent_append_during_snapshot> is marked
with '@pytest.mark.asyncio' but it is not an async function.
```
Affects: `test_oqn_t2_*`, `test_oqn_t3_*`, `test_oqn_t5_*`, and one other. These tests are
synchronous functions that verify AuditBuffer properties (not async operations) but inherited
`@pytest.mark.asyncio` from the module-level `pytestmark`. This is likely due to the test file
using `pytestmark = [pytest.mark.asyncio, ...]` at the module level.

**Impact:** No test failures — pytest runs these as sync functions regardless. Just warning
noise. With MAJOR M2's `filterwarnings = ["error::PytestWarning"]` in place, these would
escalate to errors.

**Remediation:** Remove `asyncio` from the module-level `pytestmark` in `test_path_b_drain.py`
and add it only to the actually-async tests.

---

### Minor-7 — §11.11 vs §13.6 loader/ coverage gate discrepancy

**Location:** Architecture `§11.11` vs test-strategy `§13.6`
**Finding:** Architecture §11.11 specifies `loader/ ≥95% line`. Test-strategy §13.6 specifies
`loader/ ≥85% line`. Actual: 94% (manifest.py 93% — uncovered lines 179-189 are the
`_resolve_schemas()` optional schema-module import path).

**Operative gate:** §13.6 (per §13.7 DoD item 4). Actual 94% passes §13.6's ≥85%. Not a gate
failure.

**For Stage 4.5 Alignment Review:** The §11.11/§13.6 discrepancy on loader/ should be resolved.
Either Winston updates §11.11 to match §13.6's 85% (Murat's calibrated target), or Amelia adds
a test for `_resolve_schemas()` with a real schemas module to reach 95%.

**Uncovered path (lines 179-189):** `_resolve_schemas()` when `_schemas_module is not None` —
the dynamic import path for optional per-agent schema modules. Current tests only exercise the
default `_schemas_module=None` path.

---

### Minor-8 — Residual non-auto-fixable ruff violations (9 total)

**E501 line-too-long (5 instances):**
- `tests/runtime/loader/test_manifest_csv.py:109-110` — CSV test data (162 chars) — inline
  data literal, wrapping would break the CSV format
- `tests/runtime/outbox/test_path_a_atomicity.py:197` — SQL string (106 chars)
- `tests/runtime/outbox/test_tenant_check.py:43` — assertion message (103 chars)
- `tests/runtime/registry/test_registry_find_agents.py:77` — assertion (130 chars)
- `tests/runtime/registry/test_registry_find_agents.py:121` — docstring (104 chars)

All are in test files. The source file E501 (`jobs/schema.py:95`, 101 chars) was resolved by
ruff format.

**F841 unused variables (4 instances — test files only):**
- `tests/runtime/jobs/test_claim_and_worker.py:412` — `results = await asyncio.gather(...)`:
  gather results intentionally discarded (comment says "may raise CancelledError, that's OK")
- `tests/runtime/outbox/test_path_b_drain.py:55` — `errors: list[str] = []`: dead scaffolding
  from test authoring; variable declared but never populated
- `tests/runtime/registry/test_registry_find_agents.py:76` — `names = [r.agent.agent.name
  for r in results]`: computed but assertion uses a different approach; debugging artifact
- `tests/runtime/spawner/test_depth_limit.py:33` — `spawn_ids = [uuid4() for _ in range(9)]`:
  computed but never used in the test body; the test uses a different approach

No source file has F841 violations. None of these are BLOCKERs or security concerns. The
`errors = []` dead scaffolding (test_path_b_drain.py:55) is the most notable — it suggests
the original error-collection design was abandoned mid-authoring without cleanup.

---

## 9. NITPICK Findings

**80 auto-fixed by ruff in commit `2d6e2c6`:**
- 43 unsorted import blocks (I001) — normalized by ruff isort
- 34 unused imports (F401) — removed by ruff check --fix
- 3 additional format violations resolved by ruff format beyond the 43 `ruff format` files

Most significant auto-fixed items for visibility:
- `jobs/schema.py` — `sqlalchemy.dialects.postgresql.UUID as PG_UUID` removed (unused import)
- `jobs/worker.py` — import block reordered
- `outbox/path_b.py` — minor import cleanup
- 52 files reformatted to 100-char line width, consistent string quotes, trailing commas

---

## 10. Auto-fix Commit Reference

**Commit:** `2d6e2c6`
**Message:** `style(runtime): cleo auto-fixes — ruff lint + format + imports`
**Scope:** 52 files changed, 763 insertions(+), 503 deletions(-) — all src/ and tests/
**Content:** ruff check --fix (I001/F401 auto-fixes) + ruff format normalization
**Verification:** 334/334 runtime tests green post-fix; 264/264 memory canary green post-fix
**No semantic changes.** No renames. No test modifications. No `_internal` edits.

---

## 11. Verdict and Gate Decision

**Verdict: RATIFY**

**Stage 4.4 Quinn handoff: UNBLOCKED. All MAJORs closed. 0 runtime mypy errors.**

Zero BLOCKERs. The structural security properties are verified:
- Four R53 guards green — Q3 option (b) holds
- F-13.C1 no_waiver passing — NFR-C-A1 Path A atomicity proven structurally
- 334/334 tests pass including all critical/risk-bearing tests
- §13.6 coverage gates met across all modules
- 264/264 Stage 3 memory canary zero regression

**All MAJORs resolved — no conditions on Stage 4.4 Quinn handoff:**

| ID | Finding | Resolution | Commit |
|---|---|---|---|
| M1 | mypy --strict 34 errors | `type: ignore` codes corrected, dict type args added, return type annotated, `retry.__all__` updated | `4bb9f46` |
| M2 | pytest marks unregistered | 10 markers registered + `filterwarnings` escalation added | `9ea12e8` |
| M3 | Missing pyproject.toml dependencies | `[project.dependencies]` + `[project.optional-dependencies] test` added | `9ea12e8` |
| M4 | Missing mypy_path | `mypy_path` configured in `[tool.mypy]`; errors 106→15 (15 pi-mono frozen) | `9ea12e8` |
| M5 | drain_loop.py _internal coupling | Option A: OQ-N authorization comment added to `drain_loop.py` | `4bb9f46` |

---

## 12. Handoff Notes for Quinn (Stage 4.4)

**High-priority attention items:**

1. **subprocess_mcp.py Class D enforcement paths (Minor-2):** The `check_binary_allowed()` and
   `check_agent_allowed()` rejection paths are not covered by the current test suite. These are
   the primary security enforcement paths for the only admitted Class D tool. Quinn should add
   dedicated rejection tests (`pytest.raises(ToolNotAllowedError)` for non-allowlisted binary
   and non-allowlisted agent) before the Stage 4.5 Alignment Review.

2. **fs_mcp.py pre_invoke_check rejection path (Minor-3):** The `raise FileSystemAccessDeniedError`
   path in `pre_invoke_check()` is uncovered. Add at least one test that passes a denied path
   (e.g., `"../../.env"`) to `pre_invoke_check()` and verifies the exception.

3. **pytest marks registration (M2):** Until Amelia adds the `markers` section, running
   `pytest -m "critical"` or `pytest -m "no_waiver"` will silently select no tests (unknown
   marks don't select by default). Quinn's formal QA pass should wait for M2 to be fixed.

4. **mypy strict compliance (M1):** The 34 mypy errors are all non-blocking (code passes all
   tests) but should be resolved before Quinn runs the alignment review suite with `mypy --strict`
   as a gate.

5. **Q5 metric (`runtime.agent.allowlist.stripped.count`) — Minor-4:** This metric fires on
   spawn-with-stripped-tools events. Quinn should verify the metric is emitted in the right
   spawner scenarios and that the labels (`parent_agent`, `child_agent`, `stripped_tool`)
   are present and correctly populated.

6. **_r53_allowlist.txt and TelemetryEvent field alignment:** Verified in this review (7 fields
   match). The OQ-TS-12 nightly cross-stage drift detector should be set up in CI before Stage
   4.5 so any future Memory TelemetryEvent field change triggers an alert.

7. **`mcp` dependency version (M3):** Architecture targets `mcp 1.27.0`; review used `mcp 1.9.0`.
   Verify the `test_sdk_version_guard.py` tests pass with the final pinned version and that the
   version guard in `version_guard.py` reflects the actual target version.

---

*End of Stage 4.3.5 Cleo Clean Code Review Report*
*Auto-fix commit: `2d6e2c6`*
*Report file: `_bmad-output/implementation-artifacts/praxis/runtime/cleo-review.md`*
