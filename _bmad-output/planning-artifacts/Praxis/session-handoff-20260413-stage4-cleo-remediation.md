# Session Handoff — Stage 4.3.5 Cleo MAJOR Remediation (Advisory Mode)

**Created:** 2026-04-13
**Purpose:** Enable a fresh Claude context window to resume advisory partnership with Andrey mid-Stage-4.3.5 Cleo remediation without re-reading the full session history.
**Attach this file to the new session OR paste its contents at session start.**

---

## SECTION 1 — FRESH SESSION BOOTSTRAP (READ FIRST)

You are Claude, acting as **Andrey's advisory partner** on the **Praxis** build — a productized BMAD multi-agent reasoning framework. Andrey is the solo founder and decision authority.

### The advisory pattern (binding for this session)

**You give advice and decisions. You do NOT execute work directly.** Andrey executes in separate target context windows where specialized BMAD agents (Amelia, Cleo, Quinn, etc.) do the actual work. Your job is:

1. **Verify** agent deliverables via targeted file reads and spot-checks when they're reported back
2. **Decide** architectural questions, remediation paths, severity classifications, and gate advancement
3. **Write instruction blocks** in copy-paste format that Andrey pastes into target context windows to brief each agent handoff
4. **Update Pipeline.md and auto-memory** when milestones land (these bookkeeping operations ARE in your authorized scope)

**What you do NOT do in this chat:**
- Run tests, commit code, edit src files, or execute agent skills
- Write full implementations — only advise on them
- Advance stage gates without explicit Andrey confirmation
- Modify `memory/src/`, `pi-mono/src/`, or `compression/src/` (Stages 1–3 frozen surfaces)

### Communication style

- **Decisive, not deliberative.** Andrey values tight specific responses over "on one hand / on the other hand" hedging.
- **Instruction blocks are large and detailed.** When he asks for one, produce a self-contained document the target context can execute without needing the current chat's history.
- **Spot-checks before ratifying.** When an agent reports back with test counts / coverage / commit hashes, verify 2–3 load-bearing claims via targeted Read/Grep/Bash before ratifying. Don't trust blindly.
- **Short updates between tool calls.** One sentence per update is enough. Don't narrate deliberation.

---

## SECTION 2 — PRAXIS PROJECT CONTEXT

### What we're building

**Praxis** is a multi-agent reasoning engine productizing the BMAD framework (16 specialized agents: Mary, Winston, Amelia, Quinn, Murat, Cleo, Carson, Dr. Quinn, Victor, Sophia, Maya, Caravaggio, Paige, John, Sally, Bob). Target customers: strategic advisory, compliance automation, software delivery, sales/content pipelines.

### Billing context (IMPORTANT)

- Currently running via **Claude Max 5x subscription** ($100/mo), CLI mode — NOT the API
- `ANTHROPIC_API_KEY` must NOT be set in environment
- API path reserved for 24/7 autonomous work via Managed Agents later (out of scope now)

### Build plan — 7 stages

| Stage | Name | Status |
|---|---|---|
| 1 | Pi-Mono (cost tracker) | ✅ Complete, ratified |
| 2 | Compression | ✅ Complete, ratified |
| 3 | Memory (Beads + Mem0 + Atelier) | ✅ Complete, ratified. F-5 post-ratification `telemetry.py` added 2026-04-13. |
| **4** | **Agent Runtime** | 🔄 **IN PROGRESS — Stage 4.3.5 Cleo mid-remediation** |
| 5 | MAC (Meta-Agent Controller) | Pending |
| 6 | Benchmarks + Optimization | Pending |
| 7 | POV Delivery Harness | Pending |

### Stage 4 sub-stage progress

- **4.0.1 Carson** (tool library elicitation) — ✅ ratified
- **4.1 Winston** (architecture.md v0.3+) — ✅ ratified
- **4.2 Murat** (test-strategy.md v0.1, 5950 lines, 204 test IDs) — ✅ ratified
- **4.3 Amelia** (Runtime package, ~334 tests green across 3 Checkpoints) — ✅ ratified
- **4.3.5 Cleo** (clean-code review) — 🔄 **CURRENT: RATIFY WITH CONDITIONS, 5 MAJORs being remediated**
- 4.4 Quinn (QA) — **GATED on all 5 MAJORs closing**
- 4.5 Alignment Review — pending
- 4.6 Pre-sales checkpoint — pending
- 4.7 Stage 3 deferred findings closure (F-1, F-3) — pending

---

## SECTION 3 — WHERE WE ARE RIGHT NOW

### Immediate state

Cleo delivered her Stage 4.3.5 review with **RATIFY WITH CONDITIONS** verdict. Zero BLOCKERs, 5 MAJORs, 8 MINORs, 9 NITPICKs. Andrey ratified on substance-over-form grounds and routed the 5 MAJORs to remediation owners.

**4 instruction blocks (A/B/C/D) were planned to execute the remediation:**

| Block | Owner | Scope | Status |
|---|---|---|---|
| **A** | Cleo | M2/M3/M4 pyproject.toml config additions | 🔄 **FIRED, awaiting Cleo's report** |
| **B** | Amelia | M1 mypy --strict error fixes | Scope TBD pending post-M4 mypy count from Block A |
| **C** | Amelia | M5 Memory `AuditEventType` re-export + Runtime drain_loop import update | Pending, can run parallel with B |
| **D** | Cleo | Re-audit + verdict upgrade CONDITIONS → RATIFY | Pending, fires after B+C complete |

### What to expect as the first inbound message

Most likely: **Cleo's Block A report** with the post-M4 mypy error count. This is the critical number that scopes Block B. When it arrives:

1. Verify the commit landed via `git log` spot-check
2. Verify post-M4 mypy error count via targeted rerun
3. If count is reasonable (20–50 range expected): write Block B instruction block for Amelia
4. If count is 0: unexpected — M4 alone closed M1, skip Block B, write Block C directly
5. If count is >50: investigate — M4 path fix wasn't the full cascade source, rescope Block B

### Other possible inbounds

- "Give me Block B" — write the Amelia M1 instruction block using the post-M4 error data
- "Give me Block C" — write the Amelia M5 instruction block (Memory re-export + Runtime import change)
- "Status?" — summarize the 5 MAJORs and remediation progress
- Unexpected failure report from Cleo — diagnose and adjust Block B scope

---

## SECTION 4 — THE 5 MAJORS AND REMEDIATION ROUTING

| # | Finding | Severity | Owner | Scope |
|---|---|---|---|---|
| **M1** | 34 mypy --strict errors in 6 files (type ignore wrong codes, bare dict, missing return types, Result.rowcount, FailureReason not in __all__) | MAJOR | Amelia re-activation | Semantic type annotation fixes — outside Cleo's auto-fix scope |
| **M2** | pytest custom marks not registered (86 warnings/run, --strict-markers would fail) | MAJOR | Cleo extended auth | pyproject.toml `[tool.pytest.ini_options].markers` — config only |
| **M3** | pyproject.toml has no `[project.dependencies]` (fresh install fails) | MAJOR | Cleo extended auth | Add `[project.dependencies]` with unpinned names — versions deferred to Stage 4.5 Alignment Review |
| **M4** | pyproject.toml missing `mypy_path` (106 cascade errors without MYPYPATH) | MAJOR | Cleo extended auth | Add `mypy_path = ["src", "../memory/src", "../pi-mono/src"]` + `namespace_packages = true` + `explicit_package_bases = true` |
| **M5** | `drain_loop.py` imports `memory._internal.audit.AuditEventType` — `_internal` leak from application code | MAJOR | Amelia re-activation | **Option B override** — add `AuditEventType` to `memory/__init__.py` public surface, change Runtime import |

### M5 — Andrey overrode Cleo's Option A recommendation

Cleo recommended **Option A** (accept with documentation comment, no Memory change). Andrey **overrode to Option B** (require minimal Memory public surface extension). Rationale:

1. **Precedent alignment.** F-5 (`memory/telemetry.py` addition) already established the pattern: "minimal additive public surface extension to Memory is permitted when a Stage 4 consumer has a genuine structural need, the addition is purely additive (no existing Memory code references it), and a Pipeline.md F-entry tracks it."
2. **Rule preservation.** The BLOCKER rule for `_internal` leaks from application code stays intact. Accepting Option A would establish "OQ-N made an exception" precedent that future contributors would cite.
3. **Minimal cost.** One line in `memory/__init__.py` (re-export) + one line in `drain_loop.py` (import path change) + Pipeline.md F-6 entry.
4. **Structural correctness.** `AuditEventType` is semantically a public type — it's part of the Memory↔Runtime audit stream contract. Keeping it in `_internal/` was an oversight.

**M5 becomes a new "F-6" Pipeline.md entry** after Amelia's remediation lands, mirroring the F-5 pattern.

---

## SECTION 5 — SESSION-LEVEL BINDING INVARIANTS

These are non-negotiable decisions ratified earlier in the session. Do NOT re-litigate any of them without explicit Andrey request.

### Binding condition #4 — memory/src/ frozen (with two exceptions)

Stage 4 cannot modify `memory/src/` EXCEPT for purely additive public surface extensions with:
- Zero existing Memory code references to the new symbol
- Full Stage 3 test suite 264/264 passing post-addition
- Pipeline.md F-entry tracking the addition

**Existing exceptions:**
- **F-5 (2026-04-13):** `memory/telemetry.py` added with `TelemetryEvent(frozen=True, extra='forbid')` — 7 R53-allowed fields. Commit `6209b50`.
- **F-6 (pending Block C):** `AuditEventType` re-export via `memory/__init__.py`.

**Also frozen:** `pi-mono/src/`, `compression/src/`. No exceptions authorized for these two stages.

### Q3 option (b) — four R53 structural guards

Runtime imports `TelemetryEvent` from `praxis.kernel.memory.telemetry` (public surface, NOT `_internal`). `RuntimeTelemetryEnvelope` is a **wrapper that composes via `to_telemetry_event()`** — NOT a subclass, NOT a parallel type. Four independent guards enforce this:

1. **is-identity:** `runtime.observability.TelemetryEvent is memory.telemetry.TelemetryEvent`
2. **AST scan:** Zero `class TelemetryEvent` or `class RuntimeTelemetryEvent` definitions under `runtime/`
3. **extra='allow' grep:** Zero `extra="allow"` in `observability/` source
4. **Wrapper delegation:** `RuntimeTelemetryEnvelope.to_telemetry_event()` returns Memory's type instance

**Any regression on any guard = BLOCKER.**

### F-13.C1 no_waiver

The xmin-based shared-transaction proof for F-1 Path A atomicity is non-negotiable:

- Test: `tests/runtime/outbox/test_path_a_atomicity.py::test_f13_c1_path_a_shared_transaction_via_xmin`
- Markers: `critical`, `no_waiver`, `f1_absorption`
- Uses real Postgres fixture (not mocked) — SQL: `SELECT j.xmin = e.xmin AS same_transaction FROM jobs_queue j JOIN events_outbox e ...`
- Cannot be skipped, xfailed, quarantined, or removed
- Failure = structural regression of NFR-C-A1 (7-day crypto-shred audit SLA) = BLOCKER

### OQ-N Path (i) committed default

AuditBuffer drain coordination uses position-based shim in `drain_loop.py`:
- Path (i): Position-based `_drained_count` high-water mark, skip-first-N drain, 43 MB at 100K entries (verified stable)
- Path (ii): Minimal `AuditBuffer.drain_atomic()` extension — **escalation path only**, not initial choice
- Path (iii): Sidecar queue — **REJECTED at architecture time**, never an option

Escalation to Path (ii) requires explicit Andrey authorization + test flake evidence on OQ-N.T2/T4/T6 or T3 exceeding 60 MB ceiling.

### Test-first discipline (§13.7)

Git-archaeology audit checks commit ordering via `git log --diff-filter=A`:
- **Rule:** Test file and implementation file CANNOT land in the same commit
- **Rule:** Implementation file CANNOT precede its matching test file
- **One ratified exception:** Checkpoint 2 commit `a6ef167` bundled two coverage-filler test files (`test_claim_and_worker.py`, `test_schema_and_coverage.py`) with their impl — ratified on substance-over-form grounds at Stage 4.3.5. Path α (documentation-only, no history rewrite) applied.
- **Also flagged at Stage 4.3.5:** Commit `c269b90` added coverage filler tests AFTER their implementation commits (separate commit, but post-impl). Same substance-over-form disposition.

### Preload-first gating for BMAD agents

Every BMAD agent handoff uses the same pattern:
1. Agent absorbs preload documents (3–6 files specified in instruction block)
2. Agent returns a structured brief (6–8 items)
3. Andrey verifies alignment before greenlighting work
4. Agent executes with checkpoint halts for review
5. Agent halts at final boundary for ratification

Validated across Carson → Winston → Murat → Amelia → Cleo. The friction is the point — it catches scope drift before expensive rework. Amelia's preload caught the missing `memory/telemetry.py` (F-5).

---

## SECTION 6 — ACTIVE INSTRUCTION BLOCKS

### Block A — Cleo M2/M3/M4 (FIRED)

**Status:** Already written and delivered to Andrey in the prior chat. Andrey pasted it into Cleo's target context. Cleo is executing now.

**What Block A instructs Cleo to do:**
1. Add 12 pytest custom marks to `[tool.pytest.ini_options].markers`
2. Add `[project.dependencies]` with unpinned names inferred from actual imports (grep-derived)
3. Add `mypy_path`, `namespace_packages`, `explicit_package_bases` to `[tool.mypy]`
4. Run verifications: TOML parse, --strict-markers, mypy error count, test suites
5. Single commit with specific message format
6. Report back via structured format

**Key number Block A must report:** post-M4 mypy error count. This scopes Block B.

### Block B — Amelia M1 (SCOPE TBD)

**Status:** Not yet written. Pending Cleo's Block A report for real mypy error count.

**When to write Block B:**
- After Cleo reports post-M4 mypy count
- If count is 20–50: standard Amelia re-activation for mypy error fixes in the 6 identified files
- If count is 0: skip Block B entirely (M4 alone closed M1), proceed directly to Block C
- If count is >50: investigate the extra errors before scoping (may indicate deeper issue)

**Block B scope (standard case):**
- Single Amelia commit fixing all mypy --strict errors
- Categories: wrong `# type: ignore` codes, bare `dict`, missing return types, `Result.rowcount` handling, `FailureReason` not in `__all__`
- Constraint: no behavior changes, no test modifications, no dependency additions
- Verification: pytest 334/334 green post-fix, mypy zero errors post-fix
- Commit message format: `fix(runtime): resolve N mypy --strict errors in M files` with Closes Cleo M1 reference

### Block C — Amelia M5 (PENDING)

**Status:** Not yet written. Can run parallel with Block B or sequentially after.

**Block C scope:**
1. **Memory edit:** Add `from praxis.kernel.memory._internal.audit import AuditEventType` + `"AuditEventType"` in `__all__` in `memory/__init__.py`
2. **Memory verification:** Full Stage 3 test suite must be 264/264 passing post-addition (purely additive, mirrors F-5)
3. **Memory commit:** `feat(memory): re-export AuditEventType for R53 cross-stage consumer` with F-6 tracking note
4. **Runtime edit:** Change `drain_loop.py` import from `memory._internal.audit` to `memory` public
5. **Runtime verification:** 334/334 passing post-change + `_internal` leak grep returns zero hits
6. **Runtime commit:** `fix(outbox): drain_loop import AuditEventType from public memory surface`
7. **Pipeline.md F-6 entry** (Andrey adds after Amelia confirms both commits landed)

### Block D — Cleo re-audit (PENDING)

**Status:** Not yet written. Fires after B+C complete.

**Block D scope:**
1. Re-run all audit steps from the original review: R53 guards, full suite, coverage, `_internal` leak grep, AST scan, extra='allow' grep
2. Verify all 5 MAJORs closed:
   - M1: mypy --strict returns zero errors
   - M2: pytest --strict-markers clean
   - M3: pyproject.toml has dependencies listed
   - M4: mypy runs without external MYPYPATH
   - M5: no `_internal` imports from `runtime/src/` application code
3. Update `cleo-review.md` with "M1-M5 REMEDIATED" section and verdict upgrade
4. Commit: `docs(runtime): cleo-review.md verdict upgrade RATIFY WITH CONDITIONS → RATIFY`
5. Report final verdict + readiness for Stage 4.4 Quinn handoff

---

## SECTION 7 — ADVISORY-ONLY PATTERN (HOW YOU WORK)

### What you do in this chat

1. **Receive agent reports** from Andrey (pasted from target contexts)
2. **Spot-check 2–3 load-bearing claims** via targeted Read/Grep/Bash — never re-read entire large files
3. **Make decisions** on ratification, remediation paths, severity classifications, gate advancement
4. **Write instruction blocks** in copy-paste format for the next agent handoff
5. **Update Pipeline.md** when milestones land (use Edit tool)
6. **Update auto-memory** when session-level state changes (use Edit tool on `~/.claude/projects/C--Users-AndreyPopov-Documents-Anthropic/memory/`)
7. **Keep responses tight** — decisive, specific, with file_path:line_number references

### What you do NOT do in this chat

- Run pytest, mypy, ruff, or any build tool (let Andrey execute in target contexts)
- Edit source code files under `src/`
- Edit test files under `tests/`
- Modify `memory/src/`, `pi-mono/src/`, or `compression/src/` (frozen surfaces)
- Modify architecture.md or test-strategy.md (ratified — edits require stage-gate reopening)
- Advance stage gates without explicit Andrey confirmation
- Write to or simulate target context windows — just produce copy-paste text
- Batch multiple operations into one commit hoping it'll stick

### Spot-check patterns (use sparingly)

When verifying an agent report, pick 2–3 of the most load-bearing claims and verify directly:

- **Test count claims:** `pytest tests/ --collect-only -q | tail` or `pytest tests/ -q --tb=line | tail` for actual results
- **Commit existence:** `git log --oneline -5 <hash>` in the relevant repo
- **File content claims:** `Read` with small offset/limit, or `Grep` for specific patterns
- **Coverage claims:** Read the module file and check line counts match, or re-run pytest-cov for the specific module

Do NOT re-read entire architecture.md (3341 lines) or test-strategy.md (5950 lines). Trust the summaries unless spot-check surfaces a discrepancy.

### When to update Pipeline.md

Immediately at milestones:
- Stage completion (`[x]` marker + summary line)
- Sub-stage start (`[~]` marker)
- Current Stage header update
- Deferred finding closure entries (F-N)

Pipeline.md is at `C:\Users\AndreyPopov\Documents\Anthropic\_bmad-output\planning-artifacts\Praxis\Pipeline.md`. Use Edit tool with anchor strings that won't collide — prefer unique substrings from the exact line you're changing.

### When to update auto-memory

When session-level invariants change:
- New binding condition or exception
- Stage ratification (new project memory entry)
- Feedback memory for validated patterns (e.g., preload-first gating proved effective)

Memory files are at `C:\Users\AndreyPopov\.claude\projects\C--Users-AndreyPopov-Documents-Anthropic\memory\`. Existing entries:
- `MEMORY.md` — index
- `feedback_praxis_stage_gates.md`
- `project_praxis_elicitation_rounds.md`
- `project_praxis_stage4.md` — current Stage 4 state (update this one as Stage 4 progresses)
- `feedback_preload_first_gating.md`

---

## SECTION 8 — KEY FILE PATHS

### Project root
`C:\Users\AndreyPopov\Documents\Anthropic\`

### Pipeline + planning
- `_bmad-output/planning-artifacts/Praxis/Pipeline.md` — master orchestration (always attach to session)
- `_bmad-output/planning-artifacts/Praxis/praxis-build-plan.md` — 7-stage overview
- `_bmad-output/planning-artifacts/Praxis/box-core-architecture.md` — full technical architecture
- `_bmad-output/planning-artifacts/Praxis/stage-4-winston-prompt.md` — Stage 4 launch prompt
- `_bmad-output/planning-artifacts/Praxis/stage-4-deferred-findings-brief.md` — F-1/F-3 architectural inputs
- `_bmad-output/planning-artifacts/Praxis/session-handoff-20260412-stage3-phase3B.md` — prior handoff (Stage 3)
- **THIS FILE:** `_bmad-output/planning-artifacts/Praxis/session-handoff-20260413-stage4-cleo-remediation.md`

### Stage 4 ratified artifacts (TREAT AS FROZEN)
- `_bmad-output/implementation-artifacts/praxis/runtime/architecture.md` — Winston v0.3+
- `_bmad-output/implementation-artifacts/praxis/runtime/test-strategy.md` — Murat v0.1 (5950 lines)
- `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md` — Carson 4.0.1

### Runtime source tree (Amelia's work)
```
_bmad-output/implementation-artifacts/praxis/runtime/
├── src/praxis/kernel/runtime/
│   ├── models.py                    # AgentDefinition + AgentRole
│   ├── proxies/                     # S4.R-01 type-level asymmetry
│   ├── observability/               # Q3 option (b) import + envelope wrapper + 4 guards
│   ├── jobs/                        # F-3 durable jobs infrastructure
│   ├── outbox/                      # F-1 Path A + Path B + drain_loop.py (M5 target)
│   ├── loader/                      # manifest CSV + tool catalog
│   ├── registry/                    # find_agents + embedder + matching
│   ├── mcp_adapter/                 # mcp 1.27.0 SDK wrap + version guard
│   ├── tools/                       # 8 P0 tool concepts / 9 impl files
│   └── spawner/                     # role-based proxy dispatch + budgets + circular_guard
├── tests/runtime/                   # ~334 tests across 3 Checkpoints
├── pyproject.toml                   # Block A target (M2/M3/M4)
├── cleo-review.md                   # Cleo's Stage 4.3.5 report (RATIFY WITH CONDITIONS)
└── cleo-coverage.json               # coverage artifact from Cleo's audit
```

### Memory source tree (FROZEN except F-5/F-6)
```
_bmad-output/implementation-artifacts/praxis/memory/
├── src/praxis/kernel/memory/
│   ├── telemetry.py                 # F-5 Stage 3 post-ratification addition
│   ├── __init__.py                  # F-6 target (AuditEventType re-export for M5)
│   ├── _internal/
│   │   ├── audit.py                 # AuditEventType source (currently _internal)
│   │   └── ...                      # other Memory internals
│   └── ...
├── tests/                           # 264/264 passing (canary baseline)
└── .venv/                           # shared toolchain — Amelia and Cleo both use this venv
```

### Pi-Mono source tree (FROZEN)
```
_bmad-output/implementation-artifacts/praxis/pi-mono/
└── src/praxis/kernel/cost/
    ├── storage/
    │   ├── repository.py            # CostRepository — public, imported by Runtime
    │   └── schema.py                # EventRow — public, imported by Runtime
    └── ...
```

### Auto-memory (persistent across sessions)
`C:\Users\AndreyPopov\.claude\projects\C--Users-AndreyPopov-Documents-Anthropic\memory\`
- `MEMORY.md` (always loaded)
- `project_praxis_stage4.md` (current stage state)
- Other entries as indexed in MEMORY.md

### Claude Code settings (modified this session)
`C:\Users\AndreyPopov\Documents\Anthropic\.claude\settings.local.json`
- `"defaultMode": "bypassPermissions"` set at Andrey's explicit request (auto-approve all tool calls)
- Allow list contains many session-specific bash patterns (preserved intentionally)

---

## SECTION 9 — DECISIONS NOT TO RE-LITIGATE

These are ratified. Do NOT re-open without explicit Andrey request.

| Decision | Ratified at | Context |
|---|---|---|
| Q3 option (b) — import TelemetryEvent from memory.telemetry + wrapper envelope | Stage 4.2 Murat | Four R53 structural guards enforce. No parallel type under runtime/. |
| Q3 option (b) — F-5 creation of `memory/telemetry.py` as Stage 3 post-ratification addition | Amelia Checkpoint 0 | Commit `6209b50`. Pipeline.md line 309. |
| OQ-N Path (i) position-based shim as committed default | Stage 4.1 Winston | Path (ii) is escalation only. Path (iii) rejected. |
| F-13.C1 xmin approach (instead of txid_current) | Amelia Checkpoint 2 | Structurally stronger — xmin is persistent column queryable post-commit. |
| a6ef167 Path α (documentation-only, no history rewrite) | Stage 4.3.5 Cleo | Substance-over-form: critical risk-bearing tests landed test-first in 62047dc. |
| c269b90 same substance-over-form disposition | Stage 4.3.5 Cleo | Coverage fillers on non-risk paths. |
| Class D P2-cap (defer destructive-op approval workflow to Stage 5 MAC or 7 POV) | Winston absorbed from Carson §6.9 | Kubernetes/Terraform write mode P2-capped at launch. |
| Read-only default + per-agent write allowlist for all P0 tools | Winston absorbed from Carson §6.9 | Murat §9 Security Model enforces. |
| Tenant-scoped Postgres per deployment (not shared with RLS) | Winston §4.2.6 | R11 as structural impossibility, not policy. |
| Shared-DB peer tables (jobs_queue + events_outbox same Postgres) | Winston §4.2.1 | Correctness requirement, NOT optimization. F-13.C1 proves this. |
| Q5 metric `runtime.agent.allowlist.stripped.count` | Winston Checkpoint 1 review | Architecture.md §10 amendment deferred to Stage 4.5 Alignment. Documented in test-strategy.md §15. |
| Q8.1 Cleo toolchain — use `../memory/.venv` | Stage 4.3.5 Cleo preload resolution | Session-established interpreter. Python 3.11 vs 3.12 is Quinn's concern. |
| Q8.2 Cleo coverage gates — aggregate module level as written in §11.11 | Stage 4.3.5 Cleo preload resolution | Per-file floor would be scope creep. |
| Q8.3 Cleo Q5 metric — MINOR, track for Stage 4.5 | Stage 4.3.5 Cleo preload resolution | Additive, non-breaking. |
| M5 Option B — require Memory AuditEventType re-export | Stage 4.3.5 remediation routing | Overrides Cleo's Option A recommendation. Precedent alignment with F-5. |
| bypassPermissions mode for Claude Code settings | Session utility decision 2026-04-13 | Session-specific. Allow list preserved with dangerous entries per Andrey's explicit choice (Option A). |

---

## SECTION 10 — WHAT THE NEW SESSION SHOULD DO

### Immediate actions

1. **Read this handoff file if not already absorbed** — all context is here, don't re-read the full session history
2. **Wait for Andrey's inbound** — most likely Cleo's Block A report with post-M4 mypy count
3. **On Block A report arrival:**
   - Spot-check: `git log --oneline -3` in runtime repo to verify commit landed
   - Spot-check: Read the pyproject.toml diff briefly to verify config additions look right
   - Spot-check: Re-run mypy quickly to confirm the reported error count
   - Then: decide Block B scope based on the real error count
4. **Write Block B** when Andrey asks, using the same format as Block A (self-contained, CONTEXT section, REMEDIATION SCOPE, EXECUTION ORDER, HARD RULES, REPORT FORMAT, EXECUTE NOW)

### Sequential work that will fire

1. Block A (fired, awaiting report) — Cleo M2/M3/M4
2. Block B — Amelia M1 (scope depends on Block A output)
3. Block C — Amelia M5 (can run parallel with Block B or after)
4. Block D — Cleo re-audit + verdict upgrade
5. Pipeline.md update: §4.3.5 Cleo → `[x]` COMPLETE, add F-6 entry
6. Memory update: `project_praxis_stage4.md` reflecting Cleo ratification and F-6
7. **Fire Stage 4.4 Quinn** via preload-first gating brief (new instruction block, fresh agent handoff)
8. Quinn's QA execution + Checkpoint cadence
9. Eventually: Stage 4.5 Alignment Review (Winston revisit for §10 Q5 metric amendment, F-1/F-3 closure verification, OQ-N status check)
10. Stage 4.6 Pre-sales checkpoint
11. Stage 4.7 Stage 3 deferred findings formal closure

---

## SECTION 11 — WHAT THE NEW SESSION SHOULD NOT DO

- **Do NOT** re-read architecture.md (3341 lines) or test-strategy.md (5950 lines) front-to-back. Trust this handoff's summaries.
- **Do NOT** execute code, run tests, or do builds yourself — advisory only
- **Do NOT** re-open Q3 option (b), OQ-N Path (i), F-13.C1 xmin approach, M5 Option B, or any Section 9 decision
- **Do NOT** allow Stage 4.4 Quinn to fire before all 5 MAJORs are closed and Cleo's verdict upgrades to RATIFY
- **Do NOT** modify `memory/src/`, `pi-mono/src/`, or `compression/src/` (frozen)
- **Do NOT** modify `architecture.md` or `test-strategy.md` (ratified)
- **Do NOT** write directly to target context windows — produce copy-paste text instead
- **Do NOT** suggest Party Mode, brainstorming, or elicitation activities — we're deep in execution
- **Do NOT** delegate understanding to subagents via Task — the pattern is advisory handoffs in separate context windows, not parallel agent spawns
- **Do NOT** narrate your own deliberation — give decisions directly

---

## SECTION 12 — LIKELY FIRST MESSAGES AND RESPONSE PATTERNS

### Scenario A: Cleo's Block A report arrives (HIGH LIKELIHOOD)

**Inbound shape:**
```
Instruction Block A — M2/M3/M4 Remediation Report
Commit hash: [short hash]
M4 verification:
- Pre-fix mypy errors: 106
- Post-fix mypy errors: [N]  ← key number
...
```

**Your response pattern:**
1. Spot-check commit exists: `git log --oneline -3` in runtime repo
2. Spot-check mypy count: targeted rerun or read captured output file
3. Ratify Block A (Pipeline.md mention, brief acknowledgment)
4. Offer to write Block B based on the scoped mypy output

### Scenario B: "Give me Block B"

**Your response:** Produce full self-contained Block B instruction block in copy-paste format. Same structure as Block A but targeted at Amelia re-activation for M1 fixes. Use the post-M4 mypy error breakdown from Block A to specify exact files and error categories.

### Scenario C: "Give me Block C"

**Your response:** Produce Block C instruction block. Two-commit structure: (1) Memory `__init__.py` re-export, (2) Runtime `drain_loop.py` import change. Include verifications (Stage 3 264/264 green post-memory-edit, Runtime 334/334 green post-runtime-edit, `_internal` leak grep returns zero).

### Scenario D: "Status?"

**Your response:** Brief summary. 5 MAJORs. Block A status. What's next. One paragraph.

### Scenario E: Unexpected failure report

Examples:
- "Cleo's Block A broke pytest"
- "mypy post-M4 error count is 203 (cascade still there)"
- "TOML parse failed"

**Your response pattern:** Don't panic. Diagnose the specific failure. Options: (a) revert Block A and investigate, (b) apply a narrow fix and continue, (c) escalate to deeper investigation. Pick based on the failure specifics.

### Scenario F: "Continue Stage 4.4 Quinn"

**REJECT.** Quinn is gated on all 5 MAJORs closing. Remind Andrey that Block D (Cleo re-audit with verdict upgrade) must complete first. Do NOT fire Quinn prematurely.

### Scenario G: Andrey pastes something unrelated to Cleo remediation

**Diagnose and respond.** Could be a new issue, a question about architecture, a tangent. Address directly but don't lose track of the open Cleo remediation thread.

---

## APPENDIX — GLOSSARY

### BMAD Agents (in this session so far)

- **Andrey** — the user, solo founder, decision authority. You're his advisory partner.
- **Carson** — BMAD Brainstorming Coach. Did Stage 4.0.1 tool library elicitation.
- **Winston** — BMAD Architect. Produced `architecture.md` in Stage 4.1.
- **Murat** — BMAD Test Architect. Produced `test-strategy.md` in Stage 4.2.
- **Amelia** — BMAD Developer. Implemented Runtime package in Stage 4.3 across 3 Checkpoints. Currently stood down; will re-activate for M1 + M5 remediation.
- **Cleo** — BMAD Clean Code Reviewer. Currently active in Stage 4.3.5. Block A fired, awaiting her report.
- **Quinn** — BMAD QA. Pending Stage 4.4, gated on Cleo completion.

### Stage markers

- **C1/C2/C3** — Checkpoint 1/2/3 of Stage 4.3 Amelia implementation
- **§11.11** — architecture.md coverage gates section
- **§13.7** — test-strategy.md git-archaeology test-first audit rule
- **§4.2.1** — architecture.md "shared-DB peer tables correctness requirement" composition paragraph

### Key acronyms

- **F-1** — Memory → Pi-Mono CostEvent wiring (absorbed in Winston §4.2 + §8.1)
- **F-2** — Memory → Compression TONL passthrough (parked to Stage 6)
- **F-3** — Durable jobs table for retention reaper (absorbed in Winston §4.2)
- **F-4** — Connection pool sizing strawman (naturally closed by Stage 3.6)
- **F-5** — Memory `telemetry.py` Stage 3 post-ratification addition (closed 2026-04-13 commit `6209b50`)
- **F-6** — Memory `AuditEventType` re-export (pending Block C, mirrors F-5)
- **F-13.C1** — Shared-transaction atomicity test via xmin (no_waiver capstone)
- **OQ-N** — AuditBuffer drain coordination open question (Path (i) default, Path (ii) escalation, Path (iii) rejected)
- **R53** — Memory privacy requirement for telemetry field allowlist (7 allowed fields, frozen+extra='forbid' enforcement)
- **NFR-C-A1** — 7-day crypto-shred audit SLA
- **NFR-Q6** — 5-minute crash RTO
- **NFR-Q2** — 100K soft / 250K hard entry ceiling per tenant
- **NFR-R1** — Embedder model_id consistency constraint
- **S4.R-01..R-08** — Stage 4 CRITICAL risks (R-01 product-defining asymmetry, R-02 Path A atomicity, R-03 crash recovery, etc.)
- **Q1..Q5** — Andrey's clarifying decisions during Stage 4.1–4.3 (Q3 = TelemetryEvent import pattern, Q5 = allowlist stripped metric)
- **MAC** — Meta-Agent Controller (Stage 5, out of scope now)

### Path shorthand

- **Path A** — F-1 reaper-direct same-transaction CostEvent emission for `memory.retention_action` (atomic via F-13.C1)
- **Path B** — F-1 tick-drain at-least-once CostEvent emission for `memory.record_created` + `memory.retrieval_cache_hit` (bounded window-of-loss)
- **Path (i)** — OQ-N position-based shim default
- **Path (ii)** — OQ-N minimal AuditBuffer extension escalation
- **Path (iii)** — OQ-N sidecar queue rejected
- **Path α** — a6ef167 documentation-only disposition (substance-over-form)
- **Path β** — a6ef167 rebase-split remediation (rejected by Cleo, not triggered)

### Key session-specific files you may need to create

- `cleo-review.md` — exists, at `_bmad-output/implementation-artifacts/praxis/runtime/cleo-review.md`
- Instruction Blocks B, C, D — NOT yet written, produce on request
- Pipeline.md F-6 entry — NOT yet added, add after Block C completes
- `project_praxis_stage4.md` — update after Cleo ratification

---

## BOOTSTRAP CHECKLIST ON SESSION START

When the new session begins:

- [ ] Read this handoff file first (you're doing it now if you're reading this)
- [ ] Read `Pipeline.md` Stage 4 section only (don't re-read the whole file) to confirm current state
- [ ] Check `project_praxis_stage4.md` auto-memory file for any state updates
- [ ] Wait for Andrey's inbound — most likely Cleo's Block A report
- [ ] When Block A report arrives, spot-check 2–3 claims, ratify, then offer Block B

---

**End of handoff. New session is now equipped to resume Stage 4.3.5 Cleo remediation advisory mode with full context.**

**Pipeline.md version at cutover:** ~v1.11 (post-Stage-4.3 ratification, mid-4.3.5 Cleo)
**Session cutover reason:** Context preservation at 43% before Block A report arrives and Blocks B/C/D fire
