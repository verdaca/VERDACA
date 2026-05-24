# Stage 10 VOC Gate

**Compiled:** 2026-05-24
**Stage:** Stage 10 — SessionIndexPort + SkillTelemetryPort data-plane
**Status:** RATIFIED-WITH-PROVISIONAL-VOC

---

## Machine-Readable Marker

```
provisional_voc=True
real_voc_required_before_stage_11_charter=True
```

## What This Means

Stage 10 was RATIFIED 2026-05-24 on the basis of a **HYPOTHETICAL VOC synthesis**, not real Champion calls. The synthesis returned `GO-with-amendments` at **LOW confidence**, with a fragility flag (K1/K2/K3 each triggered once across 3 simulated archetypes — no 2-of-3 PIVOT, zero safety margin).

The **A7 amendment** (VOC-10-A7) makes real-VOC re-confirmation a **HARD Stage 11.1 charter precondition.** Stage 11.1 charter authoring is BLOCKED until real Champion VOC calls have been completed and synthesized, returning a non-PIVOT verdict.

## Why a Marker File and Not Only a Memory Entry

Per `feedback_no_waiver_discipline` + Murat's 9.3 / 9.4.5 / 9.4.6 PENDING-AUDIT precedent: commit-body prose has the lowest discoverability in our stack. A git-trackable marker gives:

- A grep-able anchor (`grep -r "provisional_voc=True" docs/`)
- A canonical reference for future agents loading state
- A pre-flight check Stage 11.1 charter dispatch can run
- An artifact CI could enforce later (parallels 9.4.4 cost-meter Decimal-formula-parity gate pattern)

## Provenance

| Field | Value |
|---|---|
| Synthesis verdict | GO-with-amendments, **LOW confidence** |
| Synthesis date | 2026-05-24 |
| Synthesis kind | **HYPOTHETICAL** (3 simulated Champion archetypes; no real calls) |
| Archetypes simulated | reinsurer-ML / consultancy decision-engineering / industrial-AI |
| Synthesis output | `_bmad-output/planning-artifacts/Verdaca/voc-stage10/synthesis-run-hypothetical-2026-05-24/` (6 files) |
| Kill-switch criteria | K1 UI-only VP / K2 VP-readout blocker / K3 vendor-objection / K4 JTBD missing — any 2 triggers PIVOT |
| Kill-switch outcome | K1, K2, K3 each fired on exactly 1 of 3 calls; K4 not flagged; **no 2-of-3 trigger**, zero margin |
| Buyer-language HARD audit | 0 hits |
| Path 1 decision | 2026-05-24 — team-lead accepted synthesis as provisional |
| Stage 10 implementation SHA | `d2b5670` ("feat: Stage 10 — SessionIndexPort + SkillTelemetryPort") |
| Stage 10 ratification ceremony SHA | TBD (this commit + close memo) |
| A7 routing | HARD Stage 11.1 charter precondition |
| Stage 11.1 dispatch gate | Real Champion VOC calls + synthesis returning non-PIVOT verdict before Stage 11.1 charter drafting may proceed |

## Other VOC-10 Amendments (Routed to Stage 11.x Scope)

| ID | Description | Routing |
|---|---|---|
| VOC-10-A1 | Latency-mode positioning | Stage 11.x ledger |
| VOC-10-A2 | Word/PPT export surface (firm-template-friendly) | Stage 11.x scope addition |
| VOC-10-A3 | 3 procurement gates (data-residency / client-data SOP / Microsoft-stack-fit) | Stage 10 charter covers via clauses + invariants; Stage 11 inherits to channel-adapter manifests |
| VOC-10-A4 | Multi-LLM contract wording | Stage 11.x ledger |
| VOC-10-A5 | Forwardable-link surface (stable URL in channel thread) | Stage 11.x scope addition |
| VOC-10-A6 | Post-mortem-survivability | Stage 11.x ledger |
| VOC-10-A7 | **Real-VOC re-confirmation** | **HARD Stage 11.1 charter precondition (this file)** |

## Stage 11.1 Charter Dispatch Pre-Flight

Before drafting Stage 11.1 charter, the dispatch agent MUST verify:

1. Real Champion VOC calls have been run (Andrey owns; per `voc-stage10-call-script.md`)
2. Mary has synthesized against `voc-stage10-scoring-rubric.md`
3. Synthesis returned non-PIVOT verdict (GO or GO-with-amendments)
4. Synthesis output captured at `_bmad-output/planning-artifacts/Verdaca/voc-stage10/` with non-HYPOTHETICAL provenance
5. **This file updated:** `provisional_voc=False` + new §"Real VOC Provenance" section appended; `Status` line flipped to `RATIFIED`

If any of (1)–(4) is unmet at Stage 11.1 dispatch, the charter MUST NOT be drafted; the dispatch is BLOCKED.

---

**Authority:** This file is binding. Modifications require team-lead authorization per `feedback_memory_authorization`.
