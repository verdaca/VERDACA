# Stage 9 — Ports-and-Adapters State

**Compiled:** 2026-05-08 | **Source:** 52 session handoffs 2026-04-12 → 2026-05-07
**HEAD at last close:** `1a42896` | **Branch:** main

---

## Architecture Binding (Never Re-Litigate)

- **`ports-architecture.md` v0.2 POST-ELICITATION** (3 stacked corrigenda: v0.3/v0.4/v0.5 — cite as `v0.2 §X ADR-9.2-VX`)
- **`test-strategy.md` v0.2** — 85 MAC-Ts across 8 seams; 22-entry no_waiver allow-list
- **ADR-9.2-V1:** Memory dual-adapter — Mem0 primary + Letta substitute, both built
- **Path convention:** `adapters/{name}/src/praxis/adapters/{name}/` (NOT `src/verdaca/adapters/`)
- **uv workspace:** 10 members — ports, adapters/beads, adapters/tonl, adapters/mem0, adapters/letta, tests, kernel/{compression,mac,memory,pi-mono/src,runtime,studio}; `shell/` deferred (pytest-asyncio conflict)
- **`_bmad-output/` is gitignored** (`.gitignore:29`) — `f843d44` commit body is canonical authority, not local sandbox files
- **`praxis.__path__`:** 11-entry namespace package (no `praxis/__init__.py` markers — all 5 deleted at C.2, commit `3fe343f`)

---

## Sub-Stage Ratification Log

| Sub-stage | Status | Close commit | Key artifact |
|---|---|---|---|
| 9.1 | ✅ CLOSED | — | Base architecture |
| 9.2 | ✅ RATIFIED 2026-04-18 | — | `ports-architecture.md` v0.2; Forge G-1 gate locked |
| 9.3 | ✅ RATIFIED 2026-04-18 | — | `test-strategy.md` v0.2; 85 MAC-Ts; 22-entry allow-list |
| 9.4.1 Beads | ✅ CLOSED 2026-04-28 | — | `adapters/beads/` greenfield in-tree; 264 LOC; 10/10 M-T-VS-* GREEN |
| 9.4.2 TONL | ⏸ DEFERRED-WORK | `5f34ae7` bootstrap; `1ea7ac6` MAC-Ts | 12 M-T-SER-* catalog; F9/F10/F11/F12/F13 open-deferred |
| 9.4.3 Memory | ✅ RATIFIED 2026-05-07 | `1a42896` | Mem0 + Letta adapters; 18 MAC-Ts; F-9.4.3-MEM-DTO-01 cleared; 7 probes → 9.4.5/9.6; 2 gaps → 9.9 |
| 9.4.4 Pi-Mono | 🔄 IN PROGRESS | A.1 done (`?`) | Phase A.2 + B + C pending |

---

## Active No-Waiver Allow-List Entries (Stage 9 additions, #17–#22)

Entries #1–#16 inherited from Stage 5.2 (see `test-strategy.md v0.2 §6.1`).

| # | MAC-T ID | Reason |
|---|---|---|
| 17 | M-T-MEM-PROMO-01 | Live-server promotion semantic |
| 18 | M-T-MEM-PROMO-02 | Live-server promotion semantic |
| 19 | M-T-MEM-PROMO-03 | Live-server promotion semantic |
| 20 | M-T-MEM-PROMO-04 | Live-server promotion semantic |
| 21 | M-T-SER-EVO-01 | TONL evolution spec (skeleton, pytest.skip) |
| 22 | M-T-SER-FUZZ-01 | TONL fuzz spec (skeleton, pytest.skip) |

**Rule:** No `@pytest.mark.no_waiver` added outside this list on agent initiative.

---

## Open Findings Carried Forward

| Finding | Severity | Routed to |
|---|---|---|
| F9 — Windows case-fold .gitignore audit | Low | 9.4.7 housekeeping |
| F10 — `praxis.kernel` package-shape asymmetry | Medium | 9.5 architectural review |
| F11 — `tests/pyproject.toml` no `no_waiver` marker registration | Low | Coupled F11+F12+F13 landing |
| F12 — 22-entry enforcer doesn't span Stage 9 §6.1 entries #21/#22 | Low | Coupled F11+F12+F13 landing |
| F13 — `tests/static/verdaca/` paper-only (no directory) | Low | Coupled F11+F12+F13 landing |

---

## Binding Constraints Active

- `feedback_no_waiver_discipline` — no allow-list additions on agent initiative
- `feedback_memory_authorization` — no memory writes without explicit team-lead go
- `feedback_corrigendum_paired_sweep` — corrigendum sweeps ports + test-strategy + pipeline
- `feedback_preload_first_gating` — structured preload report required before any implementation
- `feedback_provenance_pin` — close memos require §provenance table
- `feedback_session_surface_audit` — declare session ID/model/JSONL/working-dir at preload
- `feedback_advisor_executor_model_effort` — advisor = Opus 4.7 1M max; executor effort advisor-set
