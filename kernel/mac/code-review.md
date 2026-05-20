# MAC Clean Code Review (Stage 5.3.5 — Cleo)

**Reviewer:** Cleo (bmad-agent-clean-code-reviewer persona, executed via Opus 4.6 [1M] high thinking — skill support files absent, rubric sourced from `session-handoff-20260415-stage5.3.5-cleo.md` §4 + §6 + §7)
**Target:** `_bmad-output/implementation-artifacts/praxis/mac/src/praxis/kernel/mac/` (62 files, ~5500 LoC prod + fakes)
**Date:** 2026-04-15
**Baseline test suite:** `211 passed, 30 skipped` (1.70s)

---

## 1. Executive summary

| Severity | Count | Status |
|---|---|---|
| CRITICAL | **1** | Pending user ratification — fix proposed, gated on OK |
| WARNING | **7** | 2 proposed for auto-fix; 5 documented-defer with rationale |
| INFO | **3** | Noted; no action |
| Deferred (ratified decisions §4) | 6 | Explicitly NOT re-litigated |

**Files reviewed:** 62 (see Appendix A).
**Auto-fixes applied:** 0 — awaiting ratification per stage-gate rule.
**Ready for Quinn (5.4):** NOT YET — 1 CRITICAL pending.

---

## 2. CRITICAL violations (blocks 5.4)

### CRIT-1 — Production code runtime-imports from `testing.fakes`

**Rule:** Test code MUST NOT leak into production import graph (handoff §10 Scenario 6).

**Locations** (all module-level, all runtime-loaded, not `TYPE_CHECKING`-guarded):

| File | Line | Import |
|---|---|---|
| `src/praxis/kernel/mac/backfill.py` | 30–32 | `from praxis.kernel.mac.testing.fakes.fake_metadata_store import InMemoryMacBootstrapMetadataStore` |
| `src/praxis/kernel/mac/bootstrap.py` | 33–35 | same |
| `src/praxis/kernel/mac/integrations/memory.py` | 32–34 | same |

**Evidence of runtime use (not type-hint only):**
- `bootstrap.py:116` — `self._sidecar = metadata_store` (instance field)
- `bootstrap.py:147` — `if self._sidecar.is_loaded(...)` (method dispatch)
- `bootstrap.py:171` — `self._sidecar.insert(...)` (method dispatch)
- `backfill.py:62` — `self._sidecar = metadata_store`
- `integrations/memory.py:75` — `self._sidecar = sidecar`

**Why CRITICAL:** The handoff’s own Scenario 6 says verbatim: *“Flag as CRITICAL if it's a runtime import, WARNING if the type hint could be moved to a Protocol in production code.”* These are runtime imports with runtime use, not TYPE_CHECKING-guarded.

**Why it matters beyond the rule:** production code now has a structural dependency on a concrete fake. At Stage 7 POV Harness the sidecar will be replaced with a real DB-backed store — but today, any consumer constructing a `BootstrapLoader`/`BackfillJob`/`MacMemoryAdapter` in production is forced to import a class named `InMemoryMacBootstrapMetadataStore`, and downstream stages cannot cleanly swap the implementation without changing production import sites.

**Not a ratified decision:** §4 item 13 ratifies the Option Y *table schema* and its owner (MAC via `migrations/`). It does NOT ratify the step-6 import routing. The concrete `InMemoryMacBootstrapMetadataStore` class lives in `testing.fakes` — its location there is correct (it’s a fake), but production depending on the concrete fake is not.

**Proposed remediation (minimal, no new files, tests unaffected):**

1. Define a `@runtime_checkable` Protocol `BootstrapMetadataStore` in `src/praxis/kernel/mac/migrations/mac_bootstrap_metadata_0001.py` (the file already owns the sidecar schema definition — semantic fit). Protocol surface: `is_loaded`, `mark_loaded`, `insert`.
2. Change the 3 production imports to `from praxis.kernel.mac.migrations.mac_bootstrap_metadata_0001 import BootstrapMetadataStore` and use `BootstrapMetadataStore` as the parameter/field type.
3. `InMemoryMacBootstrapMetadataStore` in `testing.fakes` structurally satisfies the Protocol automatically (no subclass wiring needed).
4. Tests continue to pass concrete `InMemoryMacBootstrapMetadataStore(...)` instances — no test edits.

**Why this fix is safe:**
- No new src/ files (§9 item 8 respected).
- No test edits (tests are frozen by default).
- Widening change: a `Protocol` parameter type accepts any structural match, including the concrete fake today and a real store at Stage 7.
- No runtime behavior change — still the same instance passed in from the caller.

**Gate-on-user:** I’m not applying this before you ratify. Say `apply CRIT-1 fix` (or `defer CRIT-1` if you want the §5.3.5 gate waived for step-6 smoke scope).

---

## 3. WARNING violations

### W-1 — Deprecated `typing.FrozenSet` import

**File:** `observability/telemetry_labels.py:20`
**Rule:** Since PEP 585 / Py 3.9, `frozenset[str]` is preferred over `typing.FrozenSet[str]`.
**Fix:** Remove `FrozenSet` from the `from typing import` line, replace the 3 annotations (`FrozenSet[str]` → `frozenset[str]`).
**Severity:** WARNING — stylistic, but this is the only file in the package using the deprecated form; the rest use `frozenset[...]` directly (see `iteration_controller.py:103`, `gates/guards.py:27`, etc.). Consistency win.
**Proposed action:** auto-fix.

### W-2 — `MacTelemetryEmitter._events` grows unbounded

**File:** `observability/emitter.py:82, 112–119`
**Rule:** No unbounded in-memory growth on a production instance.
**Context:** `self._events: list[TelemetryEvent] = []` accumulates every emitted event for the emitter's lifetime. The list has no cap, no rotation, no evict policy.
**Severity:** WARNING. Today this is exercised by unit tests (short-lived instances), so no actual leak. But the class is production code and a long-lived caller would leak.
**Deferred with rationale:** This is an observable step-6 smoke artifact — `tests/mac/observability/test_emitter.py` reads `emitter.events` as the assertion surface. Capping would require a test-facing change. Legitimate Stage 7 POV Harness cleanup item. **Document in Quinn’s 5.4 review backlog.** No auto-fix.

### W-3 — Broad `except ValueError` in `MetaAgentController._build_deliberation_result`

**File:** `controller.py:184–190`
```python
try:
    composite = composite_score(
        effective_scores=controller_result.final_scores,
        suspended=frozenset(),
    )
except ValueError:
    composite = None
```
**Rule:** Broad exception catches hide bugs; catch only the expected exception or narrow the raising surface.
**Context:** `composite_score()` raises `ValueError` from exactly one site: line 63 `all gates suspended; composite denominator is zero`. The catch correctly handles that, but also silently swallows any *other* `ValueError` that any future change to `composite_score` might introduce.
**Severity:** WARNING — deferrable.
**Deferred with rationale:** The step-6 smoke path passes `suspended=frozenset()` literally, so the “all suspended” branch is never reached today — the whole `try/except` is defensive, not behavioral. Narrowing to a custom exception would require adding one for a path never entered in step-6 smoke. Stage 7 POV Harness is the right time. **No auto-fix.**

### W-4 — Synthesized `raw_score` in step-6 smoke wiring

**File:** `controller.py:175` (inside `_build_deliberation_result`)
```python
raw_score=max(1, score),
```
**Rule:** Field contract honesty — a `GateScore.raw_score` should reflect the actual raw pre-cap score, not a floor synthesized from the effective score.
**Context:** `ControllerResult.final_scores` only carries effective scores (post-cap, post-Forge penalty, post-suspension). The controller has no raw-score view at this layer, so step-6 smoke fabricates `raw=max(1, effective)`. For a suspended gate (`effective=0`), this lies — `raw` becomes 1 but the true raw could be any value in [1..5].
**Severity:** WARNING — documented step-6 smoke behavior.
**Deferred with rationale:** Fixing requires `ControllerResult` to carry `raw_scores` alongside `final_scores`, which touches `iteration_controller.py` plumbing (out of scope for 5.3.5 — this is a Stage 7 wiring gap, not a clean-code violation). **No auto-fix.** **Quinn 5.4 backlog.**

### W-5 — `asymmetry.py:282` hard-codes `manufactured_dissent_detected=False`

**File:** `asymmetry.py:282` (in `AsymmetryRouter.aggregate_critiques`)
```python
# Step 5 does not yet compute this — step 6 will fold in
# the real R5 manufactured-dissent detection from the task
# context. The key is always present so compute_final_scores
# can read it safely.
"manufactured_dissent_detected": False,
```
**Rule:** Code comments that promise future wiring should be discharged, not left dangling.
**Context:** Docstring says “step 6 will fold in” — step 6 is complete, but the field is still hardcoded. Grepping step 6 implementation confirms no update of this field.
**Severity:** WARNING — technical debt documented in the source.
**Deferred with rationale:** Req-C Pair 2 manufactured-dissent detection requires real reviewer critiques with task-context comparison — today the whole reviewer path is a step-6 smoke stub (`controller.py:137` `_build_smoke_scenario` returns constant raw scores 4 with no actual reviewer run). Wiring this field without real reviewers would add nothing. Stage 7 POV Harness owns the actual wire-up. **Log in Quinn 5.4 backlog as pending Stage 7 debt.** No auto-fix.

### W-6 — Duplicate `plan.validate()` call

**File:** `controller.py:108`
```python
plan = self._decomposer.decompose(...)
plan.validate()  # belt + suspenders
```
**Rule:** Don’t re-validate code that already validates (`plan.py:373`, `PlanDecomposer.decompose` calls `dag.validate()` before returning).
**Context:** `PlanDecomposer.decompose` already returns a validated DAG per `plan.py:373`.
**Severity:** WARNING — minor redundancy; the comment `# belt + suspenders` acknowledges it.
**Proposed action:** auto-fix — delete the duplicate call + the now-moot comment. One line. Tests unaffected.

### W-7 — `HybridScoringHarness` callable fields typed as `Any`

**File:** `eval/scoring.py:58–64`
```python
blind_scorer: Any
open_scorer: Any
```
**Rule:** Callable parameters should have a callable type hint (`Protocol` or `Callable[..., R]`).
**Context:** The two fields are invoked at lines 75 and 79 with different keyword-argument shapes (blind: `gate_id, output_id`; open: `gate_id, output_id, task_context`) — a single `Callable[..., int]` wouldn’t capture the asymmetry cleanly.
**Severity:** WARNING — type-hint gap.
**Deferred with rationale:** Proper typing needs two Protocols (`BlindScorerProtocol`, `OpenScorerProtocol`) with kwargs-only signatures. At step 4 both passes use a single `FakeLLMJudge` which satisfies both structurally via `score_by_fixture` (one method, different keyword shapes). Introducing the Protocols today is speculative typing for a stubbed harness. Flag for Quinn 5.4 backlog if the harness gets real implementations. **No auto-fix.**

---

## 4. INFO (noted, no action)

- **I-1** — `task.py:407` — `confidence = best_hits / max(total_hits, 1)`: the `max(..., 1)` is defensive no-op (the branch above already `return`s when `total_hits == 0`). Harmless, readable.
- **I-2** — `observability/emitter.py:80` — string forward-reference `"TelemetrySink | None"` is redundant with `from __future__ import annotations` (line 23). Harmless.
- **I-3** — `iteration_controller.py:549` — `self._clock.advance(int(scenario.wall_seconds_per_cycle))` truncates fractional seconds. Default scenario is 60.0 → 60; any test using non-integer values would lose precision. No current caller depends on it.

---

## 5. Deferred — ratified decisions (§4 of handoff)

These items would trip generic clean-code heuristics but the handoff pre-ratifies them. Explicitly NOT flagged:

| Item | Location | Why deferred |
|---|---|---|
| Gate thin-wrappers `r1.py`..`r12.py` | `gates/r*.py` | §4 item 2 + §7 note 6 — deliberate minimal pattern + grep-lock via `MAC-T-NEG-GATE13-01` |
| Duplicate `ClockProtocol` in `iteration_controller.py:69–80` and `parallel_pool.py:32–41` | both cycle/ files | §7 note 4 — circular-import avoidance (gates→cycle→testing.fakes→fake_llm_judge→gates.base) |
| `testing/fakes/__init__.py` as an aggregator | `testing/fakes/__init__.py` | §7 note 5 — step-5 scope refinement ratified additive-only pattern |
| `LLMJudgeClient.call_live()` excluded from coverage | `judge/llm_judge_client.py:103` | §4 item 20 — `# pragma: no cover` with v0.3 §13.5 citation ✓ |
| `calibration_anchors.py` SHA256 lock + verbatim arch §6.4 block | `gates/calibration_anchors.py` | §4 item 21 — auto-generated, SHA256 locked |
| Fakes living in production modules (`FakeAgentSpawner`, `FakeOutbox` in `integrations/runtime.py`; `FakeCostTracker` in `integrations/pi_mono.py`) | integrations/ | §7 note 5 scope refinement — fakes-near-contract pattern accepted step-5 |

---

## 6. Areas of concern from handoff §7 — findings

| Item | Finding |
|---|---|
| 1. `controller.py` at 85% | Uncovered branches are `final_scores=None` and the `except ValueError → composite=None` path (W-3). Defensive guards, not dead code. **Acceptable.** |
| 2. `plan.py` at 91% | Defensive guards in `_reverse_reach` / `_find_publish_anchor` / `_find_gate_anchor` / `topological_order` post-raise paths are belt-and-suspenders per arch §4.2. **Acceptable, not dead code.** |
| 3. `compute_final_scores()` single source of truth | Verified: `engine.py:78` delegates to `compute_final_scores`; `engine.py` does NOT re-implement SQ-7 ordering; no gate file redefines `CRITICAL_GATES` or `FORGE_PENALTY_SET` (grep-clean). **Invariant holds.** |
| 4. `ClockProtocol` local scope | `iteration_controller.py:69–80` and `parallel_pool.py:32–41` both declare a local Protocol. Identical `advance(int)→None` surface. Minimal collateral — only breaks the circular chain, no sprawl. **Acceptable.** |
| 5. `testing/fakes/__init__.py` additive-only | Verified: 8 import blocks + `__all__` tuple. No function bodies, no class defs, no logic. **Clean.** |
| 6. Gate thin-wrapper pattern | All 12 `r*.py` files are 11-line wrappers with docstring + `gate_id` attr only. Identical structure. **Intentional minimal pattern.** |
| 7. Option Y sidecar migration DDL | `migrations/mac_bootstrap_metadata_0001.py:58–71` — clean PostgreSQL DDL, `IF NOT EXISTS` idempotency, symmetric `DROP` downgrade, FK references `experience_entries.entry_id` by name (not import). Stage 3 Memory schema untouched. **Clean.** |

---

## 7. Test suite state

**Pre-fix baseline:** `211 passed, 30 skipped in 1.70s`
**Post-fix (CRIT-1 + W-1 + W-6 applied):** `211 passed, 30 skipped in 2.98s` ✓

Zero test regression. Three-fix bundle ratified by team lead 2026-04-15 and applied:

| Fix | Files touched | LoC delta |
|---|---|---|
| CRIT-1 — `BootstrapMetadataStore` Protocol extraction | `migrations/mac_bootstrap_metadata_0001.py` (+34 add, +1 export), `backfill.py` (2 edits), `bootstrap.py` (2 edits), `integrations/memory.py` (2 edits) | +34 / −0 net in migrations; 3× `InMemoryMacBootstrapMetadataStore` → `BootstrapMetadataStore` swaps in consumers |
| W-1 — `typing.FrozenSet` → `frozenset` | `observability/telemetry_labels.py` (3 annotation swaps + 1 import removal) | −1 / +0 |
| W-6 — Duplicate `plan.validate()` removal | `controller.py:108` | −1 |

**CRIT-1 resolution verification** — `grep -rn "from praxis.kernel.mac.testing.fakes" src/praxis/kernel/mac/` returns ONLY the testing/fakes/__init__.py internal re-exports (intra-subpackage aggregation, not production leakage). Zero production files import anything from `testing.fakes`. **CRIT-1 fully resolved.**

---

## 8. Ready-for-Quinn statement

**READY.** 0 CRITICAL violations remaining. CRIT-1 resolved via Protocol extraction + 3-file import rewire; post-fix test suite green at `211 passed, 30 skipped`.

Forwarded to Quinn 5.4 backlog (deferred WARNINGs with rationale per §3):
- **W-2** — `MacTelemetryEmitter._events` unbounded list — Stage 7 POV Harness cleanup
- **W-3** — broad `except ValueError` in `MetaAgentController._build_deliberation_result` — narrow when smoke is replaced with real composite path
- **W-4** — synthesized `raw_score=max(1, score)` in step-6 smoke — needs `ControllerResult.raw_scores` plumbing
- **W-5** — hardcoded `manufactured_dissent_detected=False` — needs real reviewer-critique wiring
- **W-7** — `HybridScoringHarness` callable fields typed as `Any` — needs `BlindScorerProtocol` / `OpenScorerProtocol`

3 INFOs (I-1/I-2/I-3) noted, no forwarding required.
6 deferred-ratified-decisions remain untouchable absent v0.4 amendment + re-ratification.

**Gate to 5.4 Quinn: PASSED.** Awaiting team-lead spot-check authorization to mark Pipeline.md §5.3.5 [x].

---

## Appendix A — Files reviewed (62)

Root: `__init__.py`, `task.py`, `state.py`, `results.py`, `plan.py`, `budget.py`, `engine.py`, `asymmetry.py`, `learning.py`, `backfill.py`, `bootstrap.py`, `controller.py` (12)
`cycle/`: `__init__.py`, `iteration_controller.py`, `parallel_pool.py`, `section_router.py` (4)
`gates/`: `__init__.py`, `base.py`, `guards.py`, `calibration_anchors.py`, `registry.py`, `r1.py`..`r12.py` (17)
`eval/`: `__init__.py`, `baselines.py`, `composite.py`, `scoring.py`, `validation.py` (5)
`judge/`: `__init__.py`, `llm_judge_client.py` (2)
`observability/`: `__init__.py`, `telemetry_labels.py`, `emitter.py`, `counters.py` (4)
`integrations/`: `__init__.py`, `pi_mono.py`, `runtime.py`, `compression.py`, `memory.py` (5)
`adversarial/`: `__init__.py`, `persona_3.py`, `rotation.py` (3)
`migrations/`: `__init__.py`, `mac_bootstrap_metadata_0001.py` (2)
`testing/fakes/`: `__init__.py`, `frozen_clock.py`, `fake_llm_judge.py`, `fake_compressor.py`, `fake_benchmark_outputs.py`, `fake_memory_proxies.py`, `fake_memory_facade.py`, `fake_metadata_store.py` (8)

_/__init__.py files for 3 subpackages where empty-or-aggregator-only unverified (`adversarial/__init__.py`, `migrations/__init__.py`, `judge/__init__.py`, `observability/__init__.py`, `integrations/__init__.py`, `eval/__init__.py`, `gates/__init__.py`, `cycle/__init__.py`, `testing/__init__.py` — all read or spot-checked)._
