# Praxis Stage 7.5 — Alignment Review Report

**Stage:** 7.5 — Shell Alignment Review
**Reviewer:** Team Lead (Opus 4.6 [1M])
**Date:** 2026-04-16
**Scope:** Cross-stage verification of Shell (Stage 7) against Studio (Stage 6), MAC (Stage 5), Pi-Mono (Stage 1), and Memory (Stage 3)

---

## Executive Summary

| Gate | Requirement | Status |
|---|---|---|
| Shell correctly consumes Studio + MAC | Verified | **PASS** |
| Billing reconciled against Pi-Mono | Verified | **PASS** |
| Public dashboard shows real data | Verified | **PASS** |

**Verdict: GO to 7.6 Pre-Sales Checkpoint.**

1 LOW finding (arch-text drift, no behavioral impact). 0 MEDIUM. 0 HIGH.

---

## §1 — Shell → Studio Consumption (PASS)

### §1.1 Studio Invocation Surface

**Architecture §10.1 contract:**
```python
result = await studio.invoke(
    template_path="strategic_session.yaml",
    question=user_question,
    context=user_context,
    rendering_mode=RenderingMode(req.rendering_mode),
)
```

**Implementation (`routes/sessions.py:155-166`):**
```python
template = (
    "strategic_session_quick.yaml"
    if session_data["depth"] == "quick"
    else "strategic_session.yaml"
)
result = await self._studio.invoke(
    template_path=template,
    question=session_data["question"],
    context=session_data["context"],
    rendering_mode=session_data["rendering_mode"],
)
```

**Alignment:** MATCH.
- Depth-based template selection (quick vs deep) present in both arch §7.3 and impl
- DL-15 rendering_mode passthrough from user input to Studio — correctly wired
- Studio `invoke()` kwargs match arch §10.1 contract
- `FakeStudioSession` in tests returns canned `SessionResult` with matching interface

### §1.2 C-4 Promotion Hook (Shell → Memory)

**Architecture §10.3 contract:**
```python
await memory_adapter.promote_entries(
    workspace_id=workspace.id,
    session_id=session_id,
    task_signature=result.task_signature,
)
```

**Implementation (`routes/sessions.py:173-178`):**
```python
if self._memory_adapter and result.status == "completed":
    await self._memory_adapter.promote_entries(
        workspace_id=session_data["workspace_id"],
        session_id=session_id,
        task_signature=result.task_signature,
    )
```

**Alignment:** MATCH.
- Promotion fires only on `status == "completed"` (arch §7.3 step 5)
- Method chain: `ShellMemoryAdapter.promote_entries()` → `MemoryFacadeProtocol.promote_task_entries()`
- `confirmation_source=f"session:{session_id}"` format matches arch §10.3
- C-4 debt blocker resolved per §16.1

### §1.3 MAC Consumption (Indirect via Studio)

Shell does NOT import from `praxis.kernel.*` directly — verified via grep (0 matches). All MAC interaction is mediated through Studio per DQ-4 chain: **Shell → Studio → MAC**. This is the correct DQ-1 isolation boundary.

---

## §2 — Billing Reconciliation Against Pi-Mono (PASS)

### §2.1 C-2 ULID Adapter

**Architecture §5.3:** ShellCostAdapter mints ULID for Pi-Mono, stashes MAC's `mac:{cycle_id}:{phase}:{seq}` in `tags["mac_request_id"]`.

**Implementation (`cost_adapter.py:117-127`):** `pi_mono_request_id = str(ulid.ULID())` + `tags={"mac_request_id": mac_request_id}`.

**Alignment:** MATCH. Tests: SHELL-T-ADAPT-CONTRACT-01 (ULID format) + SHELL-T-ADAPT-CONTRACT-02 (tags stash).

### §2.2 C-3 Shape Enforcement

**Architecture §5.3:** LLMResponse sent to Pi-Mono has NO `usd_cost` field — token counts only.

**Implementation:** `PiMonoLLMResponse` dataclass has fields: `request_id`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `finished_at`, `stop_reason`. No `usd_cost` — structural enforcement at class definition level.

**Alignment:** MATCH. Tests: SHELL-T-ADAPT-CONTRACT-03 (no usd_cost) + SHELL-T-ADAPT-CONTRACT-04 (integer tokens) + structural test `test_response_fields_exclude_usd_cost`.

### §2.3 Customer Price vs Internal Cost

**Architecture §5.4:** Customer price ($29/$149) is Stripe-side. Internal cost is Pi-Mono-side. Separate concerns.

**Implementation:**
- `billing.py:42-43`: `PRICE_QUICK_CENTS = 2900`, `PRICE_DEEP_CENTS = 14900` (Stripe charges)
- `cost_adapter.py:143-161`: `track_session()` aggregates Pi-Mono cost records (internal cost)
- No cross-contamination between billing and cost tracking modules

**Alignment:** MATCH.

### §2.4 Protocol Isolation

Shell uses `CostTrackerProtocol` (not direct `CostTracker` import) — DQ-1 isolation preserved. Pi-Mono is consumed only through the adapter's Protocol interface.

---

## §3 — Public Dashboard Real Data (PASS)

### §3.1 Data Sources

**Architecture §8.1:** Metrics from sessions table (real-time counts and averages).

**Implementation (`routes/public.py:29-69`):** `compute_stats()` computes:
- `total_sessions` — count of completed sessions
- `avg_cost_usd` — mean of cost_usd field
- `avg_duration_seconds` — mean of duration_seconds field
- `sessions_today` — date-filtered count

All derived from the `sessions` list parameter (DB-backed in production). No hardcoded values. The `insufficient_data` threshold (min 10 sessions) matches arch §8.3.

### §3.2 Privacy Safeguards

**Architecture §8.3:** No customer names, workspace names, question content. Aggregate only. Min 10 sessions.

**Implementation:** `PublicStatsResponse` model contains only: `total_sessions`, `avg_cost_usd`, `avg_duration_seconds`, `sessions_today`, `insufficient_data`. No PII fields. Tests SHELL-T-DASH-UNIT-03 and SHELL-T-TENANT-INT-03 verify.

**Alignment:** MATCH.

---

## §4 — Cross-Stage Contradiction Scan

### §4.1 C-1 through C-5 Disposition (from Stage 5.5)

| Contradiction | Stage 5.5 Status | Stage 7 Resolution |
|---|---|---|
| C-1 Compression class name drift | Advisory (Stage 8) | Shell doesn't touch Compression (DQ-4). No action needed. |
| C-2 Pi-Mono ULID mismatch | Blocker | **RESOLVED** — ShellCostAdapter mints ULID (§5.3) |
| C-3 LLMResponse shape drift | Blocker | **RESOLVED** — PiMonoLLMResponse has no usd_cost (§5.3) |
| C-4 Memory promotion mismatch | LATENT Stage-7 blocker | **RESOLVED** — ShellMemoryAdapter.promote_entries() (§10.3) |
| C-5 Runtime spawner method drift | Advisory (Stage 8) | Shell doesn't touch Runtime (DQ-4). No action needed. |

All 3 blockers (C-2, C-3, C-4) resolved. C-1/C-5 remain advisory for Stage 8. No new contradictions introduced by Shell.

### §4.2 Stage 6 Debt Items Carried Forward

| Item | Status in Stage 7 |
|---|---|
| DL-14 CostTrackerProtocol rename | Shell uses its own `CostTrackerProtocol` — naming is local. No conflict. |
| DL-15 Rendering-mode routing | **RESOLVED** — `CreateSessionRequest.rendering_mode` + 3-mode enum + Studio passthrough |
| MAC W-2/W-3/W-4/W-5/W-7 (5 items) | MAC frozen — shell wraps as-is. Deferred to Stage 8. |
| Studio W-1/W-2/W-3/W-4 (4 items) | Studio frozen — shell wraps as-is. Deferred to Stage 8. |
| ADR-08 PDF/pptx export | Deferred to Stage 8 per DQ-3. |

### §4.3 New Findings

**S7-A1 (LOW): Architecture §5.3 ULID API text drift**

Architecture shows `ulid.new()` but implementation uses `ulid.ULID()`. The `python-ulid` v3.x package uses `ULID()` as the constructor. Both produce valid ULIDs. The implementation uses the correct library API; the architecture pseudocode used an older API style.

**Impact:** None. Text-only drift. No behavioral difference.
**Action:** No action required. The code is correct.

---

## §5 — Frozen Artifact Verification

| Stage | Artifact | Touched by Stage 7? | Status |
|---|---|---|---|
| Stage 1 | pi-mono/ | No | FROZEN |
| Stage 2 | compression/ | No | FROZEN |
| Stage 3 | memory/ | No | FROZEN |
| Stage 4/5 | mac/ | No | FROZEN |
| Stage 6 | studio/ | No | FROZEN |
| Stage 7 | shell/architecture.md | Read-only | FROZEN |
| Stage 7 | shell/test-strategy.md | Read-only | FROZEN |

All prior-stage artifacts untouched. Shell implementation is self-contained in `shell/api/` and `shell/tests/`.

---

## §6 — Stage 7 Debt Ledger Update

**Entering Stage 7.5:** 19 items (from Stage 6.5)
**Stage 7.3.5 Cleo added:** 7 WARNINGs (W-1..W-7) — all ACCEPT AS-IS per Quinn 7.4
**Stage 7.4 Quinn disposition:** 0 items forwarded (all 7 accepted)
**New from 7.5:** 1 LOW (S7-A1 ULID text drift — no action)

**Exiting Stage 7.5:** 19 items (unchanged from entry — Shell-specific items resolved or accepted within stage; S7-A1 is informational only)

The 19-item debt ledger from Stage 6 remains the canonical set for Stage 8:
- 5 MAC Cleo WARNINGs (W-2/W-3/W-4/W-5/W-7)
- 4 Studio Cleo WARNINGs (W-1/W-2/W-3/W-4)
- C-1 Compression class name drift
- C-5 Runtime spawner method drift
- DL-14 CostTrackerProtocol rename
- ADR-08 PDF/pptx export
- A4 Spearman validation (parallel, deferred)
- 5 Stage 5.5 Cleo WARNINGs deferred to Stage 7 → now Stage 8

---

## §7 — Verdict

**GO to 7.6 Pre-Sales Checkpoint (LAUNCH).**

All 3 alignment gates pass:
1. Shell→Studio→MAC chain correctly wired via Protocol isolation (DQ-1/DQ-4)
2. Billing (Stripe) and cost tracking (Pi-Mono) are correctly separated; C-2/C-3 adapters structurally enforced
3. Public dashboard uses real aggregate data with privacy safeguards matching arch §8.3

No blocking contradictions. C-4 (the LATENT Stage-7 blocker from 5.5) is resolved. The 19-item debt ledger passes through unchanged to Stage 8.
