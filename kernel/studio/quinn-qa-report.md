# Studio Python Glue — Quinn QA Report

**Stage:** 6.4 Quinn (QA)
**Date:** 2026-04-16
**Model:** claude-sonnet-4-6 (Sonnet 4.6 standard 200k)
**Environment:** Python 3.12.12, pytest 9.0.3, hypothesis 6.151.12, venv: `praxis/memory/.venv`
**Binding:** Pipeline.md §6.4; studio/test-strategy.md v0.1; `feedback_preload_first_gating.md`

---

## §1 — Gate Results

| Gate | Requirement | Actual | Status |
|---|---|---|---|
| G-1 Coverage | ≥ 80% | **95.79%** (branch+line) | **PASS** |
| G-2 PR-gate tests | 0 failures | **97 passed, 0 failed** | **PASS** |
| G-3 Benchmark regression | 5 Tier-1 scoring tests pass | **5/5 pass** | **PASS** |
| G-4 Dissent preservation | Backbone "Dissent" section verified in all outputs | **All 4 backbone tests pass (tpl_backbone_01–04)** | **PASS** |

**Overall gate decision: PASS — 4/4 gates met.**

19 tests deselected by marker filter (`nightly_only`, `release_gate`) per pyproject.toml default. These are Tier-3/4 tests; their exclusion from the PR gate is by design per test-strategy.md §1.3.

---

## §2 — Pre-fix Triage (37 failures found, all resolved)

Quinn found 37 failures on first run. Root causes spanned three categories: test bugs, production code bugs, and template bugs. All resolved before final gate run. No failures deferred — each was deterministic, reproducible, and locally fixable without architecture changes.

### 2.1 Test bugs (fixes in test files only)

| ID | File | Issue | Fix |
|---|---|---|---|
| TB-1 | `test_schema_validation.py:26` | `_STUDIO_ROOT` computed with 5 `.parent` traversals instead of 4 — resolves to `praxis/` not `studio/`, causing `FileNotFoundError` for all YAML-loading tests (13 failures) | Changed to 4 `.parent` traversals |
| TB-2 | `test_cost_budget.py` | 3 `session.invoke()` calls missing required `"rendering_mode"` in `user_inputs` | Added `"rendering_mode": "position_to_hold"` to all 3 calls |
| TB-3 | `test_observability.py` | `_invoke_session()` helper missing `"rendering_mode"` in `user_inputs` — caused all 7 integration obs tests to fail | Added `"rendering_mode": "position_to_hold"` to helper |
| TB-4 | `test_integration.py` | 5 `session.invoke()` calls missing `"rendering_mode"`; `test_int_01` asserts `task_input.strategic_question` (non-existent attribute — correct attribute is `raw_prompt`); `test_int_07` accesses `deep_template.default_rendering_mode` (non-existent — correct attribute is `rendering_mode`) | Fixed all 5 user_inputs; corrected attribute names in test_int_01 and test_int_07 |

### 2.2 Production code bugs (fixes in src/)

| ID | File | Issue | Fix |
|---|---|---|---|
| PC-1 | `harness.py:run_studio():101` | `user_inputs` passed to `session.invoke()` omitted required `"rendering_mode"` — all `ABHarness`-driven tests failed | Added `"rendering_mode": template.rendering_mode.value` |
| PC-2 | `invoker.py:190-192` | `gate_scores` dict comprehension assumes `gs.effective_score` attribute (real MAC's `GateScore` object), but `FakeMAC.deliberate()` returns `ReasoningTrace.gate_scores: dict[str, int]` — plain ints have no `.effective_score` | Added `hasattr(gs, "effective_score")` guard: `gs.effective_score if hasattr(...) else int(gs)` |
| PC-3 | `register_check.py:46` | `_EXCLAMATION_PATTERN = re.compile(r"(?<![a-zA-Z0-9/_])!")` is inverted — the negative lookbehind excludes `word!` patterns (the most common case), matching only `!` preceded by non-alphanumeric chars. Test corpus `bad_exclamation_marks.md` contains `opportunity!`, `forward!`, etc. — all excluded by the broken pattern | Changed to `re.compile(r"(?<![/])!")` — excludes only URL-path `!` (preceded by `/`), correctly detects analytical text exclamation marks |

### 2.3 Template backbone bugs (fixes in templates/)

All four ADR-01 backbone sections (`"Structured Trade-offs"`, `"Dissent"`, `"Named Scenarios"`, `"What This Analysis Did Not Cover"`) must appear verbatim in every output template. `brief.md.j2` (position_to_hold) was the only correct template; the others deviated:

| File | Missing/Wrong sections | Fix applied |
|---|---|---|
| `position_to_hold/deck.html.j2` | H2 "Trade-offs: factors, weights, and the reasoning" → "Structured Trade-offs"; "Named scenarios: …" → "Named Scenarios"; "What this analysis did not cover" → "What This Analysis Did Not Cover" | Changed H2 headings to canonical names |
| `position_to_hold/executive_summary.md.j2` | "Key Trade-offs", "Scenarios", "Scope Limits" instead of canonical names | Renamed 3 section headings to canonical names |
| `decision_framework/brief.md.j2` | "What This Framework Did Not Cover" instead of "What This Analysis Did Not Cover" | Renamed section heading |
| `firm_voice/brief.md.j2` | "Trade-off Analysis", "Scenarios and Trigger Conditions", "Scope Limits" instead of canonical names | Renamed 3 section headings to canonical names |

---

## §3 — Final Test Run Summary

```
97 passed, 19 deselected in 4.31s
```

**Coverage by file:**

| File | Stmts | Miss | Branch | BrPart | Cover |
|---|---|---|---|---|---|
| `__init__.py` | 7 | 0 | 0 | 0 | 100% |
| `harness.py` | 87 | 3 | 10 | 2 | 95% |
| `invoker.py` | 82 | 4 | 14 | 3 | 93% |
| `models.py` | 126 | 1 | 0 | 0 | 99% |
| `register_check.py` | 64 | 1 | 12 | 1 | 97% |
| `renderer.py` | 41 | 1 | 6 | 1 | 96% |
| `schema.py` | 176 | 5 | 40 | 6 | 95% |
| **TOTAL** | **583** | **15** | **82** | **13** | **95.79%** |

**Coverage misses (non-blocking):**

- `harness.py:107-109` — `RenderedOutput` empty-fallback branch (W-4 deferred WARNING — should never occur per code comment; live MAC path only)
- `harness.py:243→246` — `generate_report` dissent analysis branch when `per_gate_rows` is empty
- `invoker.py:115` — required-param validation raise branch (tested indirectly; direct coverage requires omitting a required param, which was excluded after TB-1–TB-4 fixes)
- `invoker.py:186` — budget-string exception catch branch (W-1 deferred WARNING — broad except with fragile string match)
- `invoker.py:269-270` — `_extract_trace` error-path branch
- `register_check.py:151` — empty text fast-exit
- `register_check.py:194→192` — critical-in-risk-context lookbehind branch
- `renderer.py:124` — invisible provenance clean-verify error branch
- `schema.py:274,310,312,314,319→318,321` — negative validation paths covered by Pydantic `ValidationError` tests (collected via `pytest.raises`, not line-hit)

All misses are in error paths, live-MAC paths, or Pydantic internal validation paths. None indicate coverage gaps in the happy path or core Studio logic.

---

## §4 — Benchmark Regression

All 5 Tier-1 benchmark scoring unit tests pass:

| Test ID | Description | Result |
|---|---|---|
| STUDIO-T-BENCH-SCORE-01 | Composite formula correct for known fixture | PASS |
| STUDIO-T-BENCH-SCORE-02 | R4/R5 weight multiplier (2×) applied correctly | PASS |
| STUDIO-T-BENCH-SCORE-03 | Floor assertion fires below 60 | PASS |
| STUDIO-T-BENCH-SCORE-04 | Ceiling assertion fires above 95 | PASS |
| STUDIO-T-BENCH-SCORE-05 | Score fixture matches expected composite | PASS |

9 Tier-3 nightly benchmark tests and 1 Tier-4 A4 release test are deselected per marker filter (requires live LLM + Pi-Mono; Stage 7 scope).

---

## §5 — Dissent Preservation Verification

Dissent preservation was verified through the backbone assertion tests:

| Test | Scope | Result |
|---|---|---|
| STUDIO-T-TPL-BACKBONE-01 | `position_to_hold/brief.md.j2` — "Dissent" section present | PASS |
| STUDIO-T-TPL-BACKBONE-02 | `position_to_hold/deck.html.j2` — "Dissent" section present | PASS |
| STUDIO-T-TPL-BACKBONE-03 | `position_to_hold/executive_summary.md.j2` — "Dissent" section present | PASS |
| STUDIO-T-TPL-BACKBONE-04 | All 3 rendering modes (`position_to_hold`, `decision_framework`, `firm_voice`) — "Dissent" section present in all `brief.md.j2` variants | PASS |
| STUDIO-T-INT-03 | Full pipeline end-to-end — dissent section present in rendered output | PASS |

`"Dissent"` (exact string) is verified in all template families. `FakeSingleAgent` in `test_ab_harness.py` returns structural prompts that also include `"## Dissent"` — verified by blind evaluation integrity tests.

---

## §6 — Stage 7 Debt Ledger Additions

No new debt items from Stage 6.4 QA. The 4 WARNINGs from Cleo 6.3.5 (W-1..W-4) remain on the Stage 7 ledger. The template backbone mismatches (§2.3) were resolved, not deferred.

**Stage 7 debt ledger: 17 items** (unchanged from 6.3.5 close).

---

## §7 — Gate Decision

**PASS**

All 4 gates met:
1. Coverage 95.79% ≥ 80% ✓
2. 97 PR-gate tests green, 0 failures ✓
3. 5/5 benchmark regression tests pass ✓
4. Dissent preservation verified in all template families ✓

Stage 6.5 Alignment Review may proceed.

Quinn held — no autonomous Pipeline.md marks. Team-lead applies `[x]` ratification.
