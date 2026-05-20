# Executor handover — Stage 9.4.2-internal step 7 (2026-05-01 → next session)

## Role

You are the executor for Verdaca Stage 9.4.2-internal step 7 — TONL adapter MAC-T authoring per `test-strategy.md` v0.2 §2.2.2 (Serialization Port (ADR-2) — 12 MAC-Ts). Working directory: `C:\Users\AndreyPopov\Documents\Anthropic`. Active stage workspace: `_bmad-output/implementation-artifacts/verdaca/stage9/`.

The advisor (Claude Opus 4.7 1M context) is in a parallel session. The team-lead (Andrey) routes messages. You report to the advisor, halt-and-surface at all halt points, and never mutate state without explicit advisor authorization.

## State as of 2026-05-01 (HEAD = `5f34ae7`)

### 9.4.2-pre — FULLY CLOSED. 9.4.2-internal step 7 — NEXT.

**Branch state on `main`:**

| SHA | Date | Role |
|---|---|---|
| `439c0b7` | 04-30 | Bootstrap charter close — root pyproject + lockfile + 4 member mods + 4 marker deletions + memo |
| `3fe343f` | 04-30 | §6 stamp (records `439c0b7`) |
| `d9d4cf0` | 05-01 | 9.4.2-pre.1 structural-completeness corrigendum — 85 file adds + .gitignore root-cause fix + memo §2 reconciliation |
| `1ce354e` | 05-01 | §6 stamp (records `d9d4cf0`); dropped over-engineered self-reference row per `3fe343f` precedent |
| `5f34ae7` | 05-01 | Close-handoff with F-dockets (F6–F10) + corrigendum disposition + this resumption preload |

**Working tree:** ` M docs/pipeline-stage9.md` only — pre-existing modification, deferred for separate-session git-archaeology. Do NOT include in any step-7 commit.

### Read-first (in this order)

1. `_bmad-output/planning-artifacts/Verdaca/session-handoff-20260430-stage9.4.2-pre-close.md` (close-handoff at `5f34ae7`) — full session disposition, F-dockets, parked items, **§7 has the preload checklist for this resumption**.
2. `_bmad-output/planning-artifacts/Verdaca/stage9.4.2-pre-bootstrap-memo.md` (bootstrap memo + corrigendum addenda — env-foundational provenance pin in §6).
3. `_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md` v0.2 §2.2.2 (resumption-scope source — Serialization Port (ADR-2) — 12 MAC-Ts).

## Step 7 — TONL adapter MAC-T authoring

**Charter intent.** Author the 12 MAC-Ts for the Serialization Port (ADR-2) per `test-strategy.md` v0.2 §2.2.2. The TONL adapter scaffold from 04-28 22:22–22:24 already satisfies the SerializationPort contract at runtime (§9.C check PASSED at 04-30 step 6 under the new env). Step 7 lands the binding test catalog that gates the contract.

**Substrate state (post-corrigendum, all tracked at `d9d4cf0`):**
- `adapters/tonl/src/praxis/adapters/tonl/adapter.py` — TONL adapter scaffold.
- `adapters/tonl/src/praxis/adapters/tonl/{__init__.py,changelog.md,version_pin.py}` — supporting files.
- `adapters/tonl/pyproject.toml` — workspace member declaration.
- `ports/src/praxis/ports/serialization.py` — SerializationPort Protocol (the contract MAC-Ts gate).
- `tests/src/praxis/contract_tests/ports/test_versioned_state_contract.py` — 10 M-T-VS-* tests (precedent: per-port test file under `tests/src/praxis/contract_tests/ports/`). Your 12 new MAC-Ts go in a sibling test file under the same directory, naming per the M-T-VS-* convention adapted for serialization tests (executor surfaces proposed file naming for advisor go before authoring).

**Halt points (do not auto-proceed past any of these):**
- After preload report → advisor go on step-7 scope confirmation + test-file naming.
- After MAC-T authoring approach surface (test-design approach, fixture strategy, parametrization plan) → advisor go on approach.
- After implementation → advisor review; halt BEFORE any commit.
- After commit message draft → advisor go on subject + body + scope.
- After commit lands → surface SHA; halt for advisor close.

## Pre-execution preload (read-only, BEFORE any step-7 work)

Per `feedback_preload_first_gating.md` + `feedback_session_surface_audit.md`, structured preload before any execution.

1. **Surface declaration** (per `feedback_session_surface_audit.md`) — declare session ID (JSONL filename under `~/.claude/projects/...`) + model ID + working directory + current local date at preload, before any state mutation.
2. **Filesystem verify** — confirm `git rev-parse HEAD` = `5f34ae7` (or higher if a follow-up commit landed in between); working tree = ` M docs/pipeline-stage9.md` only; lockfile sha256 unchanged at `a3362cb3cd8d0a5e8fa39f920b3639cb4a2befa7fb2ca12e78ae0b3b28d119cb`.
3. **Interpreter sanity** — `.venv/Scripts/python.exe --version` returns `Python 3.12.12`; `pyvenv.cfg` unchanged (uv 0.11.2).
4. **Workspace sanity** — re-run namespace-package import smoke: `python -c "import praxis.ports.serialization; import praxis.adapters.tonl.adapter; import praxis; print(len(praxis.__path__))"`. Confirm 10-element `praxis.__path__` aggregation. (Note F10 caveat in close-handoff §3.5 about `praxis.kernel` asymmetry — surface but do NOT auto-resolve.)
5. **§9.C re-run** if any env state changed since `1ce354e`. Cite as **`playbook addenda §9.C`** per F6 forward action — `session-handoff-20260426-stage9.4.1-amelia-preload.md` lines 199–203 (rule prose) + `session-handoff-20260428-stage9.4.2-executor.md` lines 59–66 (TONL/SerializationPort code block). Do NOT cite `test-strategy.md §9.C` (no such section — verified F6).
6. **Test-strategy §2.2.2 read** — read `_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md` v0.2 §2.2.2 verbatim; verbatim title is `2.2.2 Serialization Port (ADR-2) — 12 MAC-Ts`; pin all 12 MAC-T IDs/names/intent in preload report.

Surface preload report to advisor. Halt for advisor go on step-7 execution.

## Standing constraints

- **Step 7 is the ONLY scope.** Do NOT extend into F9 audit, F10 architectural review, `feedback_pre_stamp_reproducibility_audit.md` authoring, or `docs/pipeline-stage9.md` git-archaeology — all parked across sessions per close-handoff §6.
- **Per-item gating** (per `feedback_memory_authorization.md`) — never bulk-go on multi-content. Each MAC-T review, each commit, each artifact write needs its own per-item advisor go.
- **Cite-pinning discipline** (per F6 in close-handoff §3.1) — never propagate paraphrases of file:line cites; verify verbatim before propagating. F6 is itself an instance of the discipline being violated.
- **Count-from-the-list discipline** (per session experience) — verify counts by recounting the actual list, not by trusting narrative labels. Two count errors slipped through this session before being caught at pre-commit.
- **Forward-only closes** — if a defect surfaces post-close (the F8 shape), fix via corrigendum-on-top, never reopen the closed charter.
- **Pre-stamp reproducibility audit** (parked candidate `feedback_pre_stamp_reproducibility_audit.md`) — at any future stamp gate touching env-foundational state, run the close-commit `git ls-tree` reproducibility check against memo's claimed bootstrap state from a clean-clone vantage, BEFORE stamping. Would have caught F8 at the `3fe343f` stamp gate.
- **No memory writes on agent initiative** (per `feedback_memory_authorization.md`) — propose content, surface for advisor go, write only on per-content go.

## Other notes from prior session

- §9.C verifies Protocol structural conformance, NOT nominal MRO inheritance (per F7 in close-handoff §3.2). If a future TONL adapter pattern ever needs class-tree ancestry for shared default impls, a separate ancestry check is required beyond §9.C — flag if you encounter that scenario, do not assume §9.C alone is sufficient.
- `praxis.kernel` package-shape asymmetry (F10) is parked for Stage 9.5 architectural review. Do not attempt to resolve under step 7. Halt-and-surface if any step-7 work is structurally blocked by it.
- F9 audit (Windows case-fold `.gitignore` landmine) is parked. If you discover any new gitignore-shadow during step 7 that smells like F9-class, halt-and-surface; do not auto-resolve.
- Two-stamp shape: any post-step-7 close memo and stamp follow this pattern (parent records its parent SHA only; stamp's own SHA lives in `git log` of memo file). No self-reference rows.

## Provenance (this handover)

- Authored: 2026-05-01
- Session JSONL: `~/.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/69f1a342-ab3a-4e66-9df9-df20cff7a15f.jsonl`
- Model: `claude-opus-4-7[1m]`
- Working dir: `C:\Users\AndreyPopov\Documents\Anthropic`
- HEAD at write: `5f34ae7`
- Companion handover: `session-handoff-20260501-stage9.4.2-internal-advisor.md`
