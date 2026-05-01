# Mem0 SCA Scan Report — NR-S-A1

**Task:** A3.3.1 (Stage 3.3 pre-condition, BLOCKER gate)
**Requirement:** NR-S-A1 — Mem0 transitive dependency SCA scan
**Date:** 2026-04-12
**Operator:** Amelia (Dev Agent)
**Environment:** Fresh isolated venv, Python 3.12.12, Windows x86_64
**Tooling:** uv 0.10.6, pip-audit 2.10.0, safety 3.7.0

## Scope

Scan Mem0 (`mem0ai`) and its entire transitive dependency chain for known CVEs.
Gate: **HALT on any CRITICAL or HIGH severity finding.** MEDIUM/LOW are non-blocking but triaged.

## Environment Provenance

| Field | Value |
|-------|-------|
| Venv location | `_bmad-output/implementation-artifacts/praxis/memory/.venv` (gitignored) |
| Python | 3.12.12 (CPython, uv-managed) |
| uv version | 0.10.6 |
| Scan host | Windows 11 Enterprise, Git Bash |
| Lockfile | `requirements-mem0-lock.txt` (80 packages, committed) |

## Target Under Scan

| Package | Version | Role |
|---------|---------|------|
| mem0ai | 1.0.11 | Primary dependency (Stage 3 Memory facade) |
| pydantic | 2.12.5 | Model layer |
| sqlalchemy | 2.0.49 | Postgres/SQLite access |
| qdrant-client | 1.17.1 | Vector store client (Mem0 default backend) |
| openai | 2.31.0 | Mem0 LLM adapter |
| cryptography | 46.0.7 | Crypto primitives (crypto-shred adjacency) |

Full pin list: `requirements-mem0-lock.txt`. Total 80 packages including transitive deps.

## Tool Summary

| Tool | Command | Exit | Finding Count |
|------|---------|------|---------------|
| pip-audit | `pip-audit --strict --desc --format=markdown` | 0 | 0 |
| safety | `safety check --json` + `safety check` | 0 | 0 (80 packages scanned) |

### pip-audit raw

```
No known vulnerabilities found
```

(See `mem0-audit.md` — empty on purpose: `--format=markdown` only emits a table when there are findings.)

### safety raw

```
Safety v3.7.0 is scanning for Vulnerabilities...
  Scanning dependencies in your environment:
  -> .venv\Lib\site-packages
  Using open-source vulnerability database
  Found and scanned 80 packages
  Timestamp 2026-04-12 20:53:35
  0 vulnerabilities reported
  0 vulnerabilities ignored
```

Full output: `mem0-safety-human.md`. JSON output in `mem0-safety.json` (note: contaminated by `safety check` deprecation banner on stdout — not parseable as pure JSON, but the findings payload is present and empty).

## Findings Table

| CVE ID | Severity | Package | Fix Version | Status |
|--------|----------|---------|-------------|--------|
| _(none)_ | — | — | — | **CLEAN** |

Both scanners agree: **zero vulnerabilities** across 80 pinned packages.

## Decision Log

- **CRITICAL / HIGH:** none → gate not triggered.
- **MEDIUM:** none reported.
- **LOW:** none reported.
- **Informational:** `safety check` CLI is officially deprecated (sunset 2024-06-01). Replacement is `safety scan`, which requires an authenticated SafetyCLI account. For this audit the legacy `check` command is sufficient — it still reads the open-source vulnerability DB and returns machine-verifiable results. **Follow-up (non-blocking):** before production, replace with `safety scan` under a service account, or drop `safety` entirely and rely on `pip-audit` (which is Python Packaging Authority maintained and non-deprecated).

## Lockfile Pin

`requirements-mem0-lock.txt` — 80 packages, generated via `uv pip freeze`. This is the authoritative pin for the Mem0 dependency surface as of this scan. Any future `uv pip install` drift must re-run the SCA gate.

## Gate Status

- [x] **CLEAN** — zero CRITICAL/HIGH CVEs across pip-audit and safety. **Proceed to A3.3.3 per Andrey's batched protocol.**
- [ ] BLOCKED — CRITICAL/HIGH CVEs present.

## Reproducibility

```bash
cd _bmad-output/implementation-artifacts/praxis/memory/
uv venv --python 3.12 .venv
source .venv/Scripts/activate  # Git Bash on Windows
uv pip install mem0ai pip-audit safety
uv pip freeze > requirements-mem0-lock.txt
pip-audit --strict --desc --format=markdown > mem0-audit.md
safety check > mem0-safety-human.md
```

## Next Action

A3.3.1 is **GREEN**. Amelia proceeds to **A3.3.3** (ruff TID251 + pre-commit grep hook) per Phase 1 auto-continue. A3.3.2 remains gated on Winston's architecture.md v1.1 §4.2.
