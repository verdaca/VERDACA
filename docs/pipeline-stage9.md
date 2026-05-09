# VERDACA STAGE 9: LEGO Seam Rebuild — Port+Adapter+Contract-Test Triad

**Date:** 2026-04-18
**Supplements:** `docs/pipeline.md` (master orchestration, Stages 1–7), `docs/pipeline-stage8.md` (production hardening), `docs/18.04.2026.md` (roundtable decisions that produced this stage)
**Purpose:** Rebuild the Verdaca kernel around a stable seam architecture. Each of the six vendored upstream components (Mem0, TONL, Beads, Forge, Pi-Mono, RTK) moves behind a Verdaca-owned **port** (stable Protocol) with a thin replaceable **adapter**. Upstream versions become feature-branch bumps, not rewrites. The quality system grows accordingly: +82 MAC-T bindings, 16→22 no_waiver allow-list, 2 new test tiers — all under **fresh ratification**.

**Strategic rationale (from `docs/18.04.2026.md` Round 1/2):** Verdaca is the assembler, not the parts vendor. Clients buy the assembled, warranted, reproducible box. Supplier transparency is a trust signal, not a weakness. Rebuild makes "replaceable by design, not by accident" operationally true, not rhetorical.

---

## FRESH SESSION BOOTSTRAP

If you are a new Claude session seeing this file for the first time:

1. **Read `docs/pipeline.md` Section 3** — confirm ALL Stages 1–7 are `[x]` and Stage 8 status is understood.
2. **Read `docs/18.04.2026.md` in full** — the two-round roundtable is the design input for this stage. Not reading it means you will re-litigate decisions.
3. **Read this file's Status Tracker (Section 3)** — find last completed item, identify NEXT incomplete item.
4. **Verify repo structure** — `kernel/` has 6 packages, `shell/` has Next.js + FastAPI.
5. **Verify billing mode** — `echo $ANTHROPIC_API_KEY` must be empty (Max billing).
6. **Verify prior ratifications still bind** — `MEMORY.md` index points to Stage 5.2 v0.3 (215 MAC-T, 16-entry no_waiver). Stage 9 supersedes on the supply-chain axis ONLY; kernel-semantics ratifications still stand.
7. **Do not skip sub-stages.** Elicitation rounds (9.1) are NOT optional. Skipping them produces an adapter layer that ships but can't be warrantied.

---

## SECTION 1: DESIGN PRINCIPLES (Inherited From Roundtable)

These are binding for every sub-stage. Deviations require explicit Andrey sign-off.

1. **Ports are sacred.** Pure Python `Protocol` + Pydantic DTOs + explicit error taxonomy. No upstream imports. `src/verdaca/ports/<name>.py`.
2. **Adapters are disposable.** Thin translators. `src/verdaca/adapters/<upstream>/`. Expected to be rewritten on every upstream bump.
3. **Vendored upstream stays upstream.** `vendor/<upstream>/` as git submodule pinned to commit SHA + artifact sha256 in lockfile. No in-tree patches — fix by PR to upstream + submodule bump.
4. **Contract tests are the stud-and-hole.** One shared pytest suite per port at `tests/ports/test_<port>_contract.py`. Any adapter that passes it is swap-equivalent.
5. **Supplier transparency is a product feature.** `UPSTREAM.md` at repo root: name, version pin, license, maintainer, one-line "why chosen." Shipped to every POV prospect.
6. **Replacement claim = "2–4 weeks with contract proof,"** NOT "hot-swappable." Honest and defensible.
7. **Color = ownership** (Caravaggio's visual rule, codified): the brand is Verdaca; the suppliers are line-art. Every piece of external comms must respect this.
8. **Upgrade discipline: PIN → TEST → RE-RATIFY → SHIP.** No silent bumps, no skipped gates, no "it's just a patch version."

---

## SECTION 2: DEPENDENCY FLOW

```
                    ┌──────────────────────────────────┐
                    │ 9.1 Elicitation (3 rounds)       │
                    │ BEFORE Winston                   │
                    └──────────┬───────────────────────┘
                               │
                               ▼
                    ┌──────────────────────────────────┐
                    │ 9.2 Winston — Port Design        │
                    │ (6 ports, error taxonomy, DTOs)  │
                    │ Output: ports-architecture.md    │
                    └──────────┬───────────────────────┘
                               │
                               ▼
                    ┌──────────────────────────────────┐
                    │ 9.3 Murat — Test Strategy        │
                    │ +82 MAC-Ts, 2 new tiers,         │
                    │ 16→22 allow-list ratification    │
                    └──────────┬───────────────────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
    ┌──────────────────────┐   ┌──────────────────────────┐
    │ 9.4 Amelia — Impl    │   │ 9.5 Contract Test Author │
    │ Beads → TONL → Mem0  │   │ (parallel with 9.4)      │
    │ → Pi-Mono → RTK      │   │ 6 port suites + 2 tiers  │
    │ → Forge (sidecar)    │   │                          │
    │ 10 pw                │   │ 2 pw                     │
    └──────────┬───────────┘   └──────────┬───────────────┘
               │                           │
               └─────────────┬─────────────┘
                             ▼
                ┌──────────────────────────────┐
                │ 9.6 Cleo — Clean Code Review │
                │ CRITICAL gate                │
                │ + supply-chain hygiene rules │
                └──────────┬───────────────────┘
                           │
                           ▼
                ┌──────────────────────────────┐
                │ 9.7 Quinn — Test Execution   │
                │ Matrix green across seams    │
                │ + E2E smoke + drift monitor  │
                └──────────┬───────────────────┘
                           │
                           ▼
                ┌──────────────────────────────┐
                │ 9.8 Alignment Review         │
                │ Cross-stage consistency,     │
                │ C-4 closure verification     │
                └──────────┬───────────────────┘
                           │
                           ▼
                ┌──────────────────────────────┐
                │ 9.9 Fresh Ratification       │
                │ Supply-chain axis,           │
                │ 22-entry allow-list,         │
                │ 297 MAC-T catalog            │
                └──────────┬───────────────────┘
                           │
                           ▼
                ┌──────────────────────────────┐
                │ 9.10 Transparency Manifest + │
                │ Pitch Deck Handoff           │
                │ UPSTREAM.md, Caravaggio deck │
                │ Sophia narrative             │
                └──────────────────────────────┘
```

**Parallelization notes:**
- 9.4 (Amelia impl) and 9.5 (contract test authoring) run in parallel — tests are the contract, writing them alongside the adapter is the only way to keep both honest.
- 9.10 (deck + UPSTREAM.md) can start as soon as 9.2 delivers port names and pin candidates; does NOT block on 9.4 completion.
- Elicitation 9.1 rounds 1 and 2 are sequential; round 3 depends on both.

**Total estimate:** 12 pw (10 adapters + 2 tests) + 1 pw ratification ceremony + 0.5 pw deck/manifest = **~13.5 pw**. Single-engineer: ~7 weeks. Two engineers: ~3.5 weeks.

---

## SECTION 3: STATUS TRACKER

**Legend:** `[ ]` not started  |  `[~]` in progress  |  `[x]` complete  |  `[!]` blocked

### Pre-Flight Checks

- [x] `docs/18.04.2026.md` read in full
- [x] Stages 1–7 all `[x]` in `docs/pipeline-stages.md` (Stage 7 LAUNCH 2026-04-16)
- [x] Stage 8 status documented — kickoff handoff written (`docs/session-handoff-stage8-kickoff.md`), execution explicitly deferred; Stage 9 does not require 8 done
- [x] `ANTHROPIC_API_KEY` unset (Max billing)
- [x] 16-entry no_waiver allow-list + 215 MAC-T catalog readable (Stage 5.2 v0.3 binding; artifacts in praxis/{shell,studio}/test-strategy.md)
- [x] C-4 ticket — Stage 7.5 confirmed shell-adapter structural resolution; Stage 9 scope = kernel/Mem0-port closure (the real fix)
- [x] Andrey signed off on **fresh ratification** scope (supply-chain axis, orthogonal to 5.2 v0.3) — 2026-04-18

**Deferred (defaults apply — see Section 4):**
- 9a/9b split, pricing model, promise wording, deck commissioning timing are **not pre-flight blockers**. Each has a late-stage decision point and a default that runs if silent.

---

### 9.1 — Elicitation (3 rounds, BEFORE Winston)

**Why:** The port contracts are product decisions, not technical ones. A wrong port design locks in bad assumptions under 82 tests. Elicitation catches the assumption before it petrifies.

**Model:** Opus 4.7 for all rounds (product-decision weight).

#### 9.1.1 — Round 1: Supplier Strategy (`/bmad-cis-innovation-strategy` — Victor)

- [x] **Focus:** Which upstreams stay, which are candidates for replacement now, which are dark-horse substitutes we should shadow-test
- [x] **Method:** *Blue Ocean Strategy* + *Value Proposition Canvas* (supplier-side)
- [x] **Questions:**
  - [x] For each of 6 upstreams: activity signal (last-commit date, open CVE count, maintainer response latency)?
  - [x] Which upstream has a credible competing project we should treat as a hot-swap candidate? (e.g., Mem0 vs Letta vs Zep)
  - [x] Where is the "one-throat-to-choke" risk highest if an upstream pivots?
  - [x] Which upstream's MIT license is at risk of relicensing (SSPL, BSL drift)?
- [x] **Output:** `_bmad-output/implementation-artifacts/verdaca/stage9/supplier-strategy.md`

#### 9.1.2 — Round 2: Port Contract Shape (`/bmad-advanced-elicitation` — Mary)

- [x] **Focus:** What MUST each port expose, what MUST it hide
- [x] **Method:** *Stakeholder Round Table* + *ADRs*
- [x] **Questions per port (Memory, Serialization, State, Compaction, Cost, LLM Proxy):**
  - [x] What does the kernel strictly need from this port? (the minimum viable surface)
  - [x] What upstream-specific behavior must NOT leak through the port? (leakage = lock-in)
  - [x] What is the explicit error taxonomy? (TransientError / ContractViolation / UpstreamUnavailable / BudgetExceeded...)
  - [x] Are there async/streaming/idempotency semantics that must be pinned?
- [x] **C-4 specific:** For Memory port, what are the exact promotion-semantic assertions that close C-4 at the seam (not inside the adapter)?
- [x] **Output:** `_bmad-output/implementation-artifacts/verdaca/stage9/port-contracts.md` — one ADR per port (v0.2 post-9.1.4, 6 ADRs with F-002 §3.5 + F-003 §3.4 PS-3 closures)

#### 9.1.3 — Round 3: Replacement Rehearsal (`/bmad-cis-problem-solving` — Dr. Quinn)

- [x] **Focus:** Adversarial — what happens when we have to actually swap
- [x] **Method:** *Failure Mode Analysis* + *Red Team Simulation*
- [x] **Questions:**
  - [x] Pick ONE upstream (Mem0 is the obvious candidate given C-4). Simulate full replacement with a plausible substitute. What breaks?
  - [x] What data migration is required? (vector re-embedding? state re-serialization?)
  - [x] What is the client-visible downtime or degradation?
  - [x] What does the 2–4 week claim look like on the wall-clock — honest Gantt?
  - [x] What abuses of the port contract does the current implementation expose that would make replacement painful?
- [x] **Output:** `_bmad-output/implementation-artifacts/verdaca/stage9/replacement-rehearsal.md` — used to calibrate the warranty language and the SLA (warranty verdict "2–4 weeks with contract proof" validated)

#### 9.1.4 — Elicitation Requirements Roll-up

- [x] **Assemble:** `_bmad-output/implementation-artifacts/verdaca/stage9/requirements.md` consolidating all three rounds
- [x] **Include:** supplier scorecard, 6 port ADRs, 1 replacement-rehearsal gantt, explicit C-4 closure spec
- [x] **Gate 9.1 complete:** three round outputs exist, requirements roll-up exists, Andrey has explicitly signed off on port contract shapes before Winston starts — **RATIFIED 2026-04-18**

---

### 9.2 — Winston: Port & Vendor Architecture

**Goal:** Design `ports-architecture.md` that binds every subsequent step. Grounded in 9.1 output; not a green-field design.

**Model:** Opus 4.7 [1M]

- [x] **Winston: Ports layer specification** (INHERITED from port-contracts.md v0.2 per team-lead preload binding; cited, not re-authored at 9.2 — see ports-architecture.md §1 pointer index)
  - [x] 6 Protocol definitions with full type signatures
  - [x] Pydantic DTO contracts (in + out)
  - [x] Error taxonomy class hierarchy
  - [x] Deprecation policy (how do we version a port if we ever must) — mechanics surfaced at ports-architecture.md §6 (API_VERSION / schema_version coupling)
- [x] **Winston: Adapter pattern specification** — ports-architecture.md §2
  - [x] File layout: `src/verdaca/adapters/<upstream>/`
  - [x] One `adapter.py` + one `version_pin.py` + one `changelog.md` per upstream
  - [x] Adapter lifecycle: on-init contract validation, on-shutdown cleanup
- [x] **Winston: Vendor strategy per upstream** (per Amelia's round-1 table) — ports-architecture.md §3, ADR-9.2-V1..V6
  - [x] Beads → git submodule (ADR-9.2-V3)
  - [x] TONL → git submodule + thin Python wrapper (ADR-9.2-V2)
  - [x] Mem0 → PyPI pin (ADR-9.2-V1 — dual-adapter Mem0 primary + Letta substitute, both PyPI-pinned)
  - [x] Pi-Mono → reimplement 200 LOC pricing math in-tree (TS/Python bridge rejected) (ADR-9.2-V4)
  - [x] RTK → Docker sidecar (ADR-9.2-V5 — + LiteLLM substitute-conformance at matrix tier)
  - [x] Forge → Docker sidecar (ADR-9.2-V6 — with G-1 BLOCKING GATE pre-audit; in-tree-stub fallback pre-staged)
  - [x] ADR per choice with decision rationale
- [x] **Winston: Repository restructure plan** — ports-architecture.md §4
  - [x] `src/verdaca/ports/`, `src/verdaca/adapters/`, `vendor/` layout (Q(b) resolved: repo-root `vendor/`, 3-0 three-axis matrix)
  - [x] Atomic-PR migration plan with file-move inventory (method specified; grep-driven inventory runs at Amelia 9.4.7)
  - [x] CI config updates needed
- [x] **Winston: Upgrade workflow** — ports-architecture.md §5 (skeleton YAMLs with Murat/Cleo/Amelia extension points)
  - [x] Monthly GitHub Action that bumps every submodule to upstream `main`
  - [x] Contract suite as pass/fail gate
  - [x] Auto-label PRs PASS/FAIL; green ones merge after human nod
- [x] **Output:** `_bmad-output/implementation-artifacts/verdaca/stage9/ports-architecture.md` v0.1 (draft) — delivered 2026-04-18
- [x] **Advanced elicitation on Winston's draft:** run `/bmad-advanced-elicitation` (per Stage 2.1.5 pattern in memory) — step 9.2.5 — executed 2026-04-18; 3 methods (Stakeholder Round Table + Comparative Analysis Matrix + Red Team vs Blue Team); 5 amendments applied + A-4 disposition recorded
- [x] **Output:** ports-architecture.md v0.2 post-elicitation — delivered 2026-04-18 with §8.6 Version Delta log
- [x] **Gate 9.2 complete:** ports-architecture.md v0.2 ratified by Andrey, no open issues on Protocol signatures or error taxonomy — **RATIFIED 2026-04-18**

---

### 9.3 — Murat: Test Strategy + Fresh Ratification Scope

**Goal:** Formalize the quality expansion. Supply-chain is a new risk axis — fresh ratification, not corrigendum.

**Model:** Opus 4.7 [1M]

- [x] **Murat: MAC-T catalog expansion** (Gate 9.3 ratified 2026-04-18; count minted at 85 within 82–86 band per ruling A — 82 base per port-contracts.md v0.2 §8.2 + 3 substitute-conformance at matrix tier per Victor §9.1 amendment #2; ceiling slot retired per 9.3.5 Matrix outcome)
  - [x] Detailed IDs per seam: Mem0 (18), TONL (12), Beads (10), Forge (14), Pi-Mono (8), RTK (10), version matrix (6+3 substitute-conformance), drift monitor (4) = **85 new bindings at 9.3**
  - [x] Each new MAC-T has: ID, seam, tier, trigger, assertion, no_waiver flag — see test-strategy.md v0.2 §2.2
- [x] **Murat: no_waiver allow-list expansion 16 → 22** (byte-preservation discipline held; 16 existing entries from Stage 5.2 v0.3 verbatim + 6 new minted at 9.3)
  - [x] 6 new entries per ruling B selection (4 Memory PROMO + 2 Serialization — `M-T-MEM-PROMO-01..04` + `M-T-SER-EVO-01` + `M-T-SER-FUZZ-01`); deferred Compaction/LLM-Proxy IDs routed to Stage 9.9 promotion cycle
  - [x] Each with canonical ID matching the 5.2 v0.3 pattern (see test-strategy.md v0.2 §6.1)
  - [x] Explicitly separate from kernel-semantics allow-list (different failure class)
- [x] **Murat: Two new test tiers formally introduced** (per pipeline §9.7 labels; Stage 5.2 crosswalk published at test-strategy.md v0.2 §3.2)
  - [x] **Tier 2: Adapter Conformance Matrix** — PR gate, parametrized over `{current, current-1, next-candidate}` + substitute-conformance cells (17 cells total, matrix fill at test-strategy.md v0.2 §5.2)
  - [x] **Tier 4: Drift Monitor** — weekly cron, non-blocking, alerts-only, emits dashboard (thresholds at test-strategy.md v0.2 §5.3)
  - [x] Tier definitions added to `test-strategy.md` with explicit gate semantics
- [x] **Murat: C-4 closure spec at Mem0 port** — 4 of the 18 Mem0 MAC-Ts are promotion-semantic assertions (`M-T-MEM-PROMO-01..04`); all 4 warranty-load-bearing and in 22-entry allow-list (see test-strategy.md v0.2 §7.1)
- [x] **Output:** `_bmad-output/implementation-artifacts/verdaca/stage9/test-strategy.md` v0.1 (draft, 2026-04-18 single-shot)
- [x] **Advanced elicitation on Murat's draft:** `/bmad-advanced-elicitation` 9.3.5 round complete 2026-04-18 — 3 methods executed (Stakeholder Round Table + Comparative Analysis Matrix + Red Team vs Blue Team); zero residual DIV classes; 5/5 softening attacks defended
- [x] **Output:** test-strategy.md v0.2 post-elicitation (6 amendments A-1..A-6 applied; A-N disposition traceable; no silent renumbering per 9.2.5 precedent)
- [x] **Gate 9.3 complete:** test-strategy.md v0.2 RATIFIED 2026-04-18; 85 MAC-T IDs minted within 82–86 freeze-block band; 22-entry allow-list frozen (16 preserved verbatim + 6 new); Andrey explicitly confirmed fresh ratification scope (test-strategy axis, orthogonal to Stage 9.9 supply-chain axis)

---

### 9.4 — Amelia: Adapter Implementation

**Goal:** Six adapters, six vendor integrations. Sequence chosen for risk-ramp (low-risk first, build muscle, high-risk last).

**Model:** Sonnet 4.6 for implementation, Opus 4.7 for any design-escalation question.

**Sequence (binding per Round 1 Amelia table):**

- [x] **9.4.1 — Beads adapter** — CLOSED 2026-04-28; see `_bmad-output/planning-artifacts/Verdaca/stage9.4.1-close-memo.md`
  - [x] `ports/src/praxis/ports/versioned_state.py` Protocol (path corrected per v0.3 §4.1 corrigendum)
  - [x] `adapters/beads/src/praxis/adapters/beads/` — `adapter.py` + `version_pin.py` + `changelog.md` (in-tree greenfield per ADR-9.2-V3 v0.5 corrigendum, not submodule pointer)
  - [x] ~~`vendor/beads/` as git submodule pinned~~ — RETIRED per ADR-9.2-V3 v0.4 corrigendum (in_tree, no submodule)
  - [x] ~~Call-site migration~~ — N/A per ADR-9.2-V3 v0.5 corrigendum (kernel `_internal/beads/` is audit-trail substrate, stays put; not a Versioned-State consumer)
- [ ] **9.4.2 — TONL adapter** (~1.0 pw, LOW risk)
  - [ ] `ports/serialization.py` Protocol
  - [ ] In-tree adapter wrapping `praxis.kernel.compression.tonl` (per ADR-9.2-V2 v0.2 corrigendum)
  - [ ] Roundtrip fuzz harness wired
- [x] **9.4.3 — Memory port + Mem0/Letta dual-adapter + C-4 closure** (~2.0 pw combined — revised from original ~1.5 pw to reflect dual-adapter scope per ADR-9.2-V1 v0.1; revision is corrigendum-class transparency, not a ratified re-estimate)
  - [x] **Step 1** — `ports/src/praxis/ports/memory.py` Protocol (landed 2026-05-02 at commit `685ecb0`; per ADR-1 §3 + v0.2.1 corrigendum closing F-9.4.3-MEM-DTO-01)
  - [x] **Step 2** — `adapters/mem0/src/praxis/adapters/mem0/` Mem0 primary adapter (landed 2026-05-03 at commit `34a4eca`; `adapter.py` + `version_pin.py` + `__init__.py`; in-tree PyPI-pinned per ADR-9.2-V1 v0.1 + ports-architecture.md v0.3 corrigendum §4.1; sha256 in `uv.lock`)
  - [x] **Step 3** — `adapters/letta/src/praxis/adapters/letta/` Letta substitute adapter (landed 2026-05-04 at commit `b14285b`; same in-tree PyPI-pinned shape per ADR-9.2-V1 v0.1; substitute-conformance H1 hedge per port-contracts.md v0.2 ADR-1:241–243)
  - [x] **Step 4** — `tests/src/praxis/contract_tests/ports/test_memory_contract.py` (landed 2026-05-04 at commit `ae1c806`; 18 MAC-Ts per `test-strategy.md` v0.2 §2.2.1; 28P/2S/0F under Option α runner; `@pytest.mark.no_waiver` on PROMO-01..04 per §6.1 allow-list entries #17–#20; structural mirror of step-7 `test_serialization_contract.py`)
  - [x] **Step 5** — Matrix-tier conformance (verified at B.2 #3 cross-adapter `inspect.signature` parity probe at commit `b14285b`; B.3 cross-adapter QUERY-03 set-equality + QUERY-04 cardinality-drift PASSED at commit `ae1c806`; per ADR-9.2-V1 v0.1 substitute-readiness + Victor §9.1 amendment #2)
  - [x] **C-4 closure** — Explicit promotion-semantic assertions (PS-1..PS-4 per port-contracts.md v0.2 ADR-1 §3.4) ratified via Step 4 contract test substance + Step 5 matrix-tier conformance (4 PROMO no_waiver markers per allow-list #17–#20 at commit `ae1c806`)
- [x] **9.4.4 — Pi-Mono reimplement** (~0.5 pw, MEDIUM risk: TS/Python boundary)
  - [x] `ports/cost_meter.py` Protocol (landed 2026-05-08 at commit `68db50d`; 7 DTOs PINNED — BudgetScope, CostEvent, CostBreakdown, CostLedgerEntry, BudgetStatus, CostQuery, CostReport — + 2 error specializations PricingTableMismatch/ParityDrift + `CostMeterPort` Protocol with `API_VERSION="1.0.0"` + `@runtime_checkable`; per ADR-9.1.2-5 §3 + v0.2.2 §3.6 corrigendum closing F-9.4.4-COST-DTO-01 at `b0c333c`)
  - [x] Reimplement 200 LOC pricing math in `adapters/pi_mono_native/` (landed 2026-05-08 at commit `325820a`; ~285 LOC `adapter.py` + `version_pin.py` + `__init__.py` + `pyproject.toml` + `changelog.md`; `PRICING_TABLE` 8 models keyed `tuple(provider, model)` → Decimal prices; `PRICING_TABLE_VERSION=0b4251681ed9` via `sha256(canonical-JSON)[:12]`; FIRST in-tree-native adapter in repo per ADR-9.2-V4 in-tree-native disposition; sibling precedent Beads with distinguishing axis (Python rewrite of TS source vs greenfield))
  - [x] Snapshot test against original TS output for parity (landed 2026-05-08 at commit `3cd6c86`; 8 M-T-COST-* MAC-Ts in `tests/src/praxis/contract_tests/ports/test_cost_meter_contract.py` + 7-vector fixture in `tests/fixtures/pi_mono_parity_vectors.json` per `test-strategy.md` v0.2 §2.2.5; 8/8 PASSED · 0 FAILED · 0 SKIPPED · 0.25s wall-clock under Option α `uv run --project tests` runner per Q-9.4.4-6; Q-9.4.4-5 AMENDED to Decimal-formula-parity (NOT byte-parity vs IEEE 754 float TS-output per S2 disposition); zero `@pytest.mark.no_waiver` per 22-entry allow-list zero-Cost-meter lock)
  - [x] ADR documenting choice NOT to bridge TS (Q-9.4.4-3 (β) disposition — adapter-side rationale inline in `adapter.py` module docstring + `changelog.md` v0.1.0 entry at `325820a`; no separate ADR file per advisor §3.1; 3 reasons captured: 200 LOC small enough to rewrite, TS/Python boundary cost > maintenance cost, in-tree posture aligns with ADR-9.2-V4 substrate-API-surface verification)
- [ ] **9.4.5 — RTK adapter** (~2.0 pw, HIGH WATCH — metering overlap with Pi-Mono)
  - [ ] `ports/llm_proxy.py` Protocol
  - [ ] Docker sidecar wiring
  - [ ] Explicit cost-meter ownership ADR: RTK emits raw; Pi-Mono is the source of truth
- [ ] **9.4.6 — Forge adapter** (~1.5 pw, MEDIUM risk — Rust sidecar, license recheck)
  - [ ] `ports/compaction.py` Protocol
  - [ ] Docker sidecar
  - [ ] License audit: confirm MIT (not GPL, not SSPL)
- [ ] **9.4.7 — Repository atomic restructure PR**
  - [ ] Move vendored code into `vendor/`
  - [ ] Update all imports
  - [ ] Update CI config
  - [ ] One PR, bisect-friendly
- [ ] **9.4.8 — Upstream-bump workflow**
  - [ ] `.github/workflows/upstream-bump.yml` — monthly, per submodule
  - [ ] Auto-PR with contract-test gate
  - [ ] PASS/FAIL label automation
- [ ] **Gate 9.4 complete:** all 6 adapters implemented, all direct upstream imports from kernel code eliminated (grep-verified), atomic restructure PR merged, monthly bump workflow tested on one seam

---

### 9.5 — Contract Test Authoring (Parallel With 9.4)

**Goal:** One pytest contract suite per port + version-matrix harness + drift monitor. Tests are written BEFORE or ALONGSIDE adapter, never after.

**Model:** Sonnet 4.6

- [ ] **9.5.1 — Port contract suites** (~1.0 pw total)
  - [ ] `tests/ports/test_versioned_state_contract.py` (Beads port)
  - [ ] `tests/ports/test_serialization_contract.py` (TONL port)
  - [ ] `tests/ports/test_memory_contract.py` (Mem0 port — includes 4 C-4 promotion-semantic assertions)
  - [ ] `tests/ports/test_cost_meter_contract.py` (Pi-Mono port)
  - [ ] `tests/ports/test_llm_proxy_contract.py` (RTK port)
  - [ ] `tests/ports/test_compaction_contract.py` (Forge port)
  - [ ] Each suite covers the MAC-T IDs minted in 9.3
- [ ] **9.5.2 — Adapter conformance matrix harness** (~0.5 pw)
  - [ ] `.github/workflows/adapter-matrix.yml`
  - [ ] Parametrization: `{upstream × [current, current-1, next-candidate]}`
  - [ ] Emits `SUPPORTED_VERSIONS.md` nightly
- [ ] **9.5.3 — Drift monitor cron** (~0.5 pw)
  - [ ] `.github/workflows/drift-monitor.yml` — weekly
  - [ ] Checks: last upstream commit date, open CVE severity, semver delta vs pinned
  - [ ] Alerts at 90 / 180 days silence + HIGH CVE
  - [ ] Dashboard-only (not PR gate)
- [ ] **Gate 9.5 complete:** 6 port contract suites green, matrix harness emits SUPPORTED_VERSIONS.md, drift monitor runs weekly, all 82 new MAC-T IDs have at least one covering test

---

### 9.6 — Cleo: Clean Code Review + Supply-Chain Hygiene

**Goal:** Hard gate before Quinn runs the full suite. Extend Cleo's standard rules with the 3 CRITICAL + 4 WARNING supply-chain rules from Round 1.

**Model:** Opus 4.7 [1M]

- [ ] **Cleo: Standard code review** (CRITICAL + WARNING per `shell/code-review.md` pattern)
- [ ] **Cleo: Supply-chain review** (new rules from Round 1)
  - [ ] **C-1 (hash-pinned vendoring)** — verify per-language lockfiles have SHA + hash
  - [ ] **C-2 (adapter contract tests, version-parameterized)** — confirm 9.5 suites are wired to matrix
  - [ ] **C-3 (SBOM generated + diffed)** — CycloneDX or SPDX at `/sbom/verdaca-<sha>.json`
  - [ ] **W-1 (CVE monitoring)** — Dependabot + osv-scanner + cargo-audit + pip-audit + govulncheck + npm audit
  - [ ] **W-2 (license audit gate)** — `/vendored/<name>/LICENSE-INVENTORY.md`, SPDX allow-list
  - [ ] **W-3 (abandonment detector)** — implemented per 9.5.3
  - [ ] **W-4 (upstream-compat matrix)** — green square per (seam × supported version)
- [ ] **Output:** `_bmad-output/implementation-artifacts/verdaca/stage9/code-review.md`
- [ ] **Gate 9.6 complete:** 0 CRITICAL violations (blocking); WARNINGs either auto-fixed or explicitly deferred with ADR

---

### 9.7 — Quinn: Test Execution

**Goal:** All four tiers green on the rebuilt kernel.

**Model:** Sonnet 4.6

- [ ] **Tier 1: Port contract tests** — PR gate, <30s, all 6 suites
- [ ] **Tier 2: Adapter conformance matrix** — PR gate, <2min, all 6 seams against current/current-1/next-candidate
- [ ] **Tier 3: E2E smoke (bump-PR trigger)** — 8–12 happy-path tests, box boots + deliberation completes
- [ ] **Tier 4: Drift monitor** — weekly cron runs clean
- [ ] **Coverage gate:** no package drops below ratified floor (per `docs/pipeline-stage8.md` floors — Pi-Mono 79%, Compression 94%, Memory 98%, Runtime 97%, MAC 94%, Studio 96%, Shell 92%)
- [ ] **New coverage floor for adapters layer:** ≥90%
- [ ] **Full nightly run clean** (includes `--run-nightly` tests + cross-stage drift canaries)
- [ ] **Output:** `_bmad-output/implementation-artifacts/verdaca/stage9/quinn-qa-report.md`
- [ ] **Gate 9.7 complete:** all 4 tiers green, coverage floors held, 297 MAC-T binding tests passing

---

### 9.8 — Alignment Review

**Goal:** Cross-stage consistency. Make sure Stage 9 doesn't silently contradict Stages 1–7 or break carried debt.

**Model:** Opus 4.7 [1M]

- [ ] **Reviewer: `/bmad-review-adversarial-general`** (not the author of any Stage 9 artifact)
- [ ] **Check: Stage 5.2 v0.3 kernel-semantics allow-list still binding, unchanged**
- [ ] **Check: Stage 5.5 OTEL ratifications still honored in new adapter layer**
- [ ] **Check: C-4 closure verified** (Mem0 port tests pass, promotion semantics match 9.1 Round 2 ADR)
- [ ] **Check: Other 4 cross-stage contradictions (C-1, C-2, C-3, C-5 from Stage 5.5) — still non-blocking? any regressed?**
- [ ] **Check: Stage 6 headline (+47% vs vanilla / +21% vs enhanced) re-measurable on new kernel** — smoke test, not full re-benchmark
- [ ] **Output:** `_bmad-output/implementation-artifacts/verdaca/stage9/alignment-review.md`
- [ ] **Gate 9.8 complete:** 0 CRITICAL contradictions, all WARNINGs either resolved or forwarded to a Stage 10 debt ledger

---

### 9.9 — Fresh Ratification (Supply-Chain Axis)

**Goal:** Formally ratify the 22-entry allow-list, 297-MAC-T catalog, 2 new test tiers. This is a **fresh ratification**, not a corrigendum — scope is the supply-chain axis, orthogonal to 5.2 v0.3 kernel-semantics scope.

- [ ] **Authority:** Andrey as team lead + Murat as test architect + Winston as architect
- [ ] **Artifact:** `_bmad-output/implementation-artifacts/verdaca/stage9/ratification-v0.1.md`
  - [ ] Explicit scope statement: "supply-chain + adapter-seam test axis"
  - [ ] Does NOT supersede 5.2 v0.3 (orthogonal scope)
  - [ ] 22-entry no_waiver allow-list verbatim
  - [ ] 297 MAC-T catalog (215 prior + 82 new, all IDs listed)
  - [ ] 2 new tier definitions (Adapter Conformance, Drift Monitor)
  - [ ] Replacement-warranty language: "replaceable in 2–4 weeks with contract proof"
- [ ] **Ceremony:** Andrey explicit "ratified" statement logged in `MEMORY.md` index as `project_verdaca_stage9.md`
- [ ] **Gate 9.9 complete:** ratification-v0.1.md signed off; memory updated; 5.2 v0.3 still binding on its axis

---

### 9.10 — Transparency Manifest + Pitch Deck Handoff

**Goal:** Turn the architecture into sales assets. This is where the roundtable narrative (Sophia) and visual (Caravaggio) become shippable.

- [ ] **9.10.1 — `UPSTREAM.md` at repo root**
  - [ ] Per upstream: name, URL, commit pin, version tag, license, maintainer team, one-line "why we chose it"
  - [ ] Rendered as a single page, client-shareable
  - [ ] Linked from README and pitch deck
- [ ] **9.10.2 — Pitch deck v0.1 (3 slides per Caravaggio spec)**
  - [ ] Hero: exploded-view "Assembled Car" (oxblood chassis, line-art suppliers)
  - [ ] BOM: monospaced supplier list with version pin + license
  - [ ] Upgrade Path: PIN → TEST → RE-RATIFY → SHIP
  - [ ] Industrial-editorial visual system (charcoal + oxblood, no hexagons, no SaaS gradients)
  - [ ] File location: `_bmad-output/implementation-artifacts/verdaca/stage9/pitch-deck/`
- [ ] **9.10.3 — Narrative copy (Sophia lock)**
  - [ ] Elevator story (74 words, verbatim from Round 2)
  - [ ] 3 messaging pillars
  - [ ] Procurement-diffuser line
  - [ ] File: `_bmad-output/implementation-artifacts/verdaca/stage9/messaging.md`
- [ ] **9.10.4 — Sales team briefing doc**
  - [ ] "How to talk about suppliers" — curator pride, not apology
  - [ ] "What the warranty actually covers"
  - [ ] "When a client asks 'so you didn't build any of this' — the scripted response"
- [ ] **Gate 9.10 complete:** UPSTREAM.md published, deck rendered, messaging locked, one client demo conducted with the new materials to validate reception

---

## SECTION 4: DEFERRED DECISIONS (Defaults Apply Until Resolved)

These four questions came out of Round 2 (2026-04-18). **None block Stage 9 start.** Each has a natural decision point later in the stage and a safe default that runs if Andrey stays silent. Revisit during Stage 9 implementation — do not hold up 9.1 elicitation on them.

| # | Question | Latest safe decision point | Default if silent |
|---|---|---|---|
| 1 | **9a / 9b split or single Stage 9?** | Start of 9.8 (alignment review) | Single Stage 9, straight through |
| 2 | **Pricing model** — per-outcome POV vs warranty-SLA subscription (Victor) | Before 9.10.3 (messaging lock) | Warranty-SLA framing in copy; pricing execution deferred to Stage 8/10 |
| 3 | **Promise wording final** | Before 9.10.3 (messaging lock) | "Replaceable in 2–4 weeks with contract proof" (Winston's softer frame) |
| 4 | **Deck commissioning timing** — external designer now or after 9.7 green | Start of 9.10.2 | Caravaggio spec renders in-house first; external designer only if demo reception warrants |

**Rule:** if a sub-stage reaches the "latest safe decision point" and Andrey has not closed the question, the default applies and the stage continues. The decision can still be overridden later, but not retroactively.

---

## SECTION 5: AGENT CHAIN SUMMARY (For Reference)

```
9.1.1 Victor        (supplier strategy)        — Opus 4.7
9.1.2 Mary          (port contract shape)      — Opus 4.7
9.1.3 Dr. Quinn     (replacement rehearsal)    — Opus 4.7
9.2   Winston       (port & vendor arch)       — Opus 4.7 [1M]
9.2.5 Mary          (advanced elicitation)     — Opus 4.7
9.3   Murat         (test strategy + ratif.)   — Opus 4.7 [1M]
9.4   Amelia        (6 adapters)               — Sonnet 4.6
9.5   Amelia/Quinn  (contract tests)           — Sonnet 4.6
9.6   Cleo          (code + supply chain)      — Opus 4.7 [1M]
9.7   Quinn         (test execution)           — Sonnet 4.6
9.8   Alignment     (adversarial review)       — Opus 4.7 [1M]
9.9   Ratification  (Andrey + Murat + Winston) — human
9.10  Sophia + Caravaggio (manifest + deck)    — Opus 4.7
```

**Rule (inherited from methodology.md):** Complete Step N before Step N+1 within a stage. Elicitation rounds 9.1.1 → 9.1.2 → 9.1.3 are sequential. Step 9.4 and 9.5 run in parallel (explicitly).

---

## SECTION 6: GATE CONDITIONS SUMMARY

| Gate | Blocker |
|---|---|
| 9.1 → 9.2 | All 3 elicitation rounds done; requirements roll-up signed off by Andrey |
| 9.2 → 9.3 | ports-architecture.md v0.2 post-elicitation, ratified |
| 9.3 → 9.4/9.5 | test-strategy.md v0.2, 82 MAC-T IDs minted, 22-entry allow-list frozen, fresh-ratification scope signed off |
| 9.4/9.5 → 9.6 | All direct upstream imports removed from kernel (grep-verified); 6 port contract suites + matrix harness + drift monitor in place |
| 9.6 → 9.7 | 0 CRITICAL code-review violations |
| 9.7 → 9.8 | All 4 test tiers green; coverage floors held; 297 MAC-T bindings passing |
| 9.8 → 9.9 | 0 CRITICAL alignment contradictions; C-4 closure verified |
| 9.9 → 9.10 | Fresh ratification artifact signed off, memory updated |
| Stage 9 DONE | UPSTREAM.md published, deck rendered, messaging locked, one client demo conducted |

---

## SECTION 7: SUCCESS CRITERIA (What "Done" Means)

Stage 9 is complete when:

1. **No kernel module imports upstream symbols directly.** Grep for `from mem0 import`, `from beads import`, etc. in `src/verdaca/` returns zero results outside `adapters/`.
2. **Monthly upstream bump workflow ran at least once on the real schedule**, gating on contract tests, and merged a green bump PR.
3. **Replacement rehearsal executed end-to-end** on one upstream (Mem0 recommended, aligns with C-4 closure), wall-clock within 2–4 weeks, no production incident.
4. **UPSTREAM.md is the single source of truth** for client-facing supplier disclosure. Sales deck, pitch, onboarding all link to it.
5. **C-4 (Memory promotion semantic mismatch) is CLOSED** in the debt ledger, with proof being the 4 Mem0 port promotion-semantic MAC-Ts passing.
6. **Ratification v0.1 is binding** — 297 MAC-Ts, 22-entry allow-list, 2 new tiers — and the 5.2 v0.3 kernel-semantics ratification still binds on its own axis.
7. **At least one client has heard the Toyota pitch and bought the Toyota pitch** — procurement-diffuser line validated in the wild.

---

## SECTION 8: OUT OF SCOPE (Explicit)

To protect scope against drift:

- **NOT in this stage:** adding new upstream components beyond the existing 6.
- **NOT in this stage:** building a self-assembly / dynamic-supplier registry. Fixed topology.
- **NOT in this stage:** re-running the Stage 6 benchmark (+47% vs vanilla). Smoke-verification only in 9.8.
- **NOT in this stage:** billing / pricing implementation. Decision lives here (9.10 messaging), execution in Stage 8 or later.
- **NOT in this stage:** A4 human validation of reasoning quality. Still deferred per Stage 5.6 conditional pass.

---

**Status:** Stage 9 document drafted 2026-04-18. Not yet started. Awaits Andrey sign-off on pre-flight checks (Section 3) only. Section 4 deferred decisions have defaults and do NOT block start.

**Next action:** Andrey confirms pre-flight checks in Section 3, then 9.1.1 (Victor supplier strategy elicitation) kicks off.
