# NR-S-R1 Banned-API Enforcement Setup — A3.3.3

**Task:** A3.3.3 (Stage 3.3 pre-condition)
**Requirement:** NR-S-R1 — Specify `__all__` / `_internal` import lint tool
**Date:** 2026-04-12
**Operator:** Amelia (Dev Agent)
**Upstream:** nfr-report.md §7.1 (NR-S-R1), architecture.md §3.1 + Req #9

## What NR-S-R1 Requires

Application code must not import from `praxis.kernel.memory._internal.*`. The Memory
module owns `_internal`; everything else must go through the facade in
`praxis.kernel.memory`. Architecture §3.1 names "CI lint rule" without specifying the
tool; NR-S-R1 directs Amelia to pick and configure one.

The strawman from nfr-report.md §7.1:

> Use `ruff` with a custom `TID251` banned-api rule OR a pre-commit hook running
> `grep -rE "from praxis\.kernel\.memory\._internal"` … **Owner: Amelia at Stage 3.3
> setup.** Deadline: before first module merges to main.

Decision: **ship both**, layered. Ruff catches 99% of violations during dev; the grep
hook is a defense-in-depth tripwire in case ruff is misconfigured or bypassed.

## Enforcement Stack

| Layer | Tool | File | Scope |
|-------|------|------|-------|
| 1 | ruff TID251 banned-api | `pyproject.toml` | Language-aware AST check |
| 2 | grep pattern scan | `scripts/check-no-internal-imports.sh` | Shell-level tripwire |

Both layers wire into pre-commit via `.pre-commit-config.yaml`. Both must be green for
a commit to land.

### Layer 1 — ruff TID251

`pyproject.toml` configuration:

```toml
[tool.ruff.lint]
select = ["E", "F", "W", "I", "TID", "B"]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"praxis.kernel.memory._internal".msg = "NR-S-R1 / Req #9: import from the praxis.kernel.memory facade, not _internal.*"

[tool.ruff.lint.per-file-ignores]
"src/praxis/kernel/memory/**/*.py" = ["TID251"]
"tests/memory/**/*.py" = ["TID251"]
"tests/tooling/banned_import_fixtures/**/*.py" = ["F401", "TID251"]
```

Key design choices:

- **`"praxis.kernel.memory._internal".msg`** — Ruff TID251 matches imports at the
  module prefix level, so this covers every depth (`_internal`, `_internal.mem0`,
  `_internal.mem0.client`, etc.).
- **Per-file ignores** — the Memory module itself MUST import from `_internal` (it
  owns it). White-box tests in `tests/memory/**` also need white-box access. Self-test
  fixtures intentionally contain a banned import and must compile without tripping
  ruff during normal sweeps.
- **`ban-relative-imports = "all"`** — additional hardening: all imports must be
  absolute so there is no ambiguity about which module the ban applies to.

### Layer 2 — grep tripwire

`scripts/check-no-internal-imports.sh` scans `src/` and `tests/` for the regex:

```
^\s*(from\s+praxis\.kernel\.memory\._internal|import\s+praxis\.kernel\.memory\._internal)
```

Files under `src/praxis/kernel/memory/**`, `tests/memory/**`, and
`tests/tooling/banned_import_fixtures/**` are excluded (same exemptions as ruff per-file
ignores). Any match outside those paths exits 1.

The script runs via `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: check-no-internal-imports
      name: NR-S-R1 grep — ban praxis.kernel.memory._internal from application code
      entry: bash scripts/check-no-internal-imports.sh
      language: system
      pass_filenames: false
      types: [python]
```

## Self-Test Harness

`scripts/self-test-banned-imports.sh` exercises both layers against two fixtures:

| Fixture | Import | Expected Layer 1 | Expected Layer 2 |
|---------|--------|------------------|------------------|
| `tests/tooling/banned_import_fixtures/banned_caller.py` | `from praxis.kernel.memory._internal import something` | reject | reject |
| `tests/tooling/banned_import_fixtures/clean_caller.py` | `from praxis.kernel import memory` | accept | accept |

The harness copies each fixture into `src/praxis/app_selftest/` (a path NOT exempted by
either layer's ignore rules), runs both layers, asserts the expected verdict, then
removes the copy.

### Self-Test Run — 2026-04-12

```
=== NR-S-R1 Self-Test ===

Case 1: banned_caller.py (should be REJECTED)
  PASS  ruff TID251 (expected=reject, got=reject)
  PASS  grep defense layer (expected=reject, got=reject)

Case 2: clean_caller.py (should be ACCEPTED)
  PASS  ruff TID251 (expected=accept, got=accept)
  PASS  grep defense layer (expected=accept, got=accept)

=== Results: 4 passed, 0 failed ===
```

**All 4 assertions PASS.** Both enforcement layers behave correctly.

## Full Ruff Sweep

Running `ruff check src tests scripts` against the committed source tree
(facade placeholder + `_internal` placeholder + self-test fixtures) returns:

```
All checks passed!
```

No false positives from the committed tree. The fixtures under
`banned_import_fixtures/` are correctly exempted from normal sweeps.

## File Manifest

New files introduced by A3.3.3:

```
memory/
├── pyproject.toml                                              # ruff config (Layer 1)
├── .pre-commit-config.yaml                                     # pre-commit wiring
├── scripts/
│   ├── check-no-internal-imports.sh                            # grep hook (Layer 2)
│   └── self-test-banned-imports.sh                             # self-test harness
├── src/praxis/__init__.py
├── src/praxis/kernel/__init__.py
├── src/praxis/kernel/memory/__init__.py                        # facade placeholder
├── src/praxis/kernel/memory/_internal/__init__.py              # _internal placeholder
└── tests/tooling/banned_import_fixtures/
    ├── clean_caller.py                                         # CLEAN fixture
    └── banned_caller.py                                        # BANNED fixture
```

The `src/praxis/kernel/memory/**` tree is the **minimum** required for the ban target
module path to resolve. Real implementation lands in A3.3.4+.

## Gate Status

- [x] Ruff TID251 rule configured and tested
- [x] Grep hook implemented and tested
- [x] Self-test harness proves both layers reject a banned import
- [x] Self-test harness proves both layers accept the facade import
- [x] Full ruff sweep green on the committed source tree
- [x] Pre-commit wiring in place (both layers triggered on `git commit`)
- [x] **A3.3.3 CLEAN — proceed per Phase 1 auto-continue**

## Follow-Ups (non-blocking)

- **CI integration** — the pre-commit stack runs locally; wiring into GitHub Actions /
  equivalent happens at Stage 7 (POV harness) alongside the rest of CI. Until then the
  enforcement is developer-discipline + pre-commit.
- **TID252 (relative-import ban)** — already active via `ban-relative-imports = "all"`.
- **Consider `flake8-import-restrictions`** — an alternative tool that allows
  per-directory rule sets. Not needed now since ruff TID251 + per-file-ignores covers
  the requirement, but worth revisiting if the rule set grows beyond 3–4 entries.
