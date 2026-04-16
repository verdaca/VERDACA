# Praxis Compression Layer — Requirements Validation (Elicitation Round 1)

**Stage:** Praxis Stage 2, Step 2.1.5 (Elicitation Round 1 — AFTER Winston)
**Input:** `compression/architecture.md` draft v0.1 (Winston, 2026-04-12)
**Facilitator:** `/bmad-advanced-elicitation` skill
**Methods applied:** Method 2 (Failure Mode Analysis) + Method 5 (Comparative Analysis Matrix)
**Date:** 2026-04-12
**Status:** Complete — 16 architecture edits applied; draft advanced to v0.2
**Next step:** Step 2.2 (Murat / Test Architect) — `/bmad-tea`

---

## 0. SCOPE AND CONTRACT

Elicitation Round 1 exists to interrogate Winston's compression architecture draft on three specific dimensions before Murat writes the test strategy:

1. **Quality tolerance threshold for compression fall-back** — what fall-back percentage is acceptable before a component is considered failed?
2. **Quality measurement methodology** — how do we know compression is "safe"? What validators are in the pipeline and how do they fail?
3. **Consequence hierarchy** — if multiple components can fail, which failure is worst? This drives test-effort allocation and circuit-breaker hardening priorities.

Two methods were applied in sequence:
- **Method 2 — Failure Mode Analysis.** Systematic walk of each component's failure space. Produced 40+ failure modes across 5 component tables + orchestrator; surfaced 5 top-RPN gaps in the draft; produced 12 specific architecture edits.
- **Method 5 — Comparative Analysis Matrix.** Seven weighted-scoring matrices converting the FMEA's qualitative findings into explicit threshold numbers. Produced 4 additional architecture edits (3 threshold tightenings + 1 canonical severity ranking).

**Net output:** 16 architecture edits applied to `compression/architecture.md`; the draft is now stable and ready for Murat's test strategy (Step 2.2).

---

## 1. ELICITATION TARGET #1 — QUALITY TOLERANCE THRESHOLD FOR COMPRESSION FALL-BACK

### 1.1 The question restated

Every component in the compression layer has a circuit breaker that falls back to its uncompressed input on validation failure. At what percentage of requests is this fall-back acceptable before the component is considered failed and should be disabled for the workload?

### 1.2 What the draft said before elicitation

**§10.2 (original):** "5% combined fallback rate (structural + semantic) over any 24-hour window triggers an alert. 10% disables Caveman for the workload until investigated."

No scoring. No rationale beyond intuition. The number was a placeholder for the elicitation.

### 1.3 What the elicitation produced

**Comparative Analysis Matrix 1 — Caveman fallback warn/disable thresholds**

Criteria and weights:
- User impact — 0.25 (how badly does silent-corruption or false-disable hurt users?)
- Production tolerance — 0.20 (how much fallback is acceptable before it's a quality regression?)
- Investigation cost — 0.15 (engineering time spent investigating alerts)
- Dashboard signal clarity — 0.15 (can ops tell good fallback from bad fallback?)
- Harness sensitivity — 0.15 (how quickly can A/B harness detect regressions?)
- Implementation complexity — 0.10

| Option | User | Prod | Invest | Dash | Harness | Impl | **Weighted** |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A. 2% / 5% | 5 | 3 | 2 | 4 | 5 | 3 | 3.75 |
| **B. 3% / 7%** | 5 | 4 | 3 | 4 | 5 | 3 | **4.15** ⭐ |
| C. 5% / 10% (prior default) | 4 | 5 | 4 | 4 | 4 | 3 | 4.10 |
| D. 7% / 15% | 3 | 5 | 4 | 3 | 3 | 3 | 3.60 |
| E. 10% / 20% | 2 | 4 | 5 | 2 | 2 | 3 | 2.95 |

**Winner:** Option B — **3% warn / 7% disable**, by 0.05 margin over prior default.

### 1.4 Answer

**Quality tolerance threshold (post-elicitation):**
- **3% combined fallback rate** (structural + semantic, over 24-hour window) triggers a warning alert.
- **7% disables** Caveman for the workload until investigated.
- Thresholds MAY loosen to 5% / 10% after the first 30 days of production if observed fallback rate is stable and no silent degradation is detected.

**Rationale:** Praxis's pre-launch pitch is *"measured savings with quality preservation."* Quality is the sell. Starting tighter (3% / 7%) and loosening on evidence is the conservative play; the 0.05 margin over 5% / 10% is small on paper but large in marketing consequence — a single "10% of outputs silently degraded" incident erases the credibility of any headline savings number.

**Architecture edit applied:** §10.2 rewritten to document matrix-backed thresholds with explicit review commitment at 30 days.

### 1.5 Component-by-component fall-back rate tolerances

Matrix 1 scored Caveman specifically. The other components have different failure profiles and need their own bars:

| Component | Tolerance (warn / disable) | Rationale |
|-----------|----------------------------|-----------|
| **Caveman** | **3% / 7%** | Matrix 1. Silent semantic drift is load-bearing product risk. |
| **TONL** | **0.1% / 1%** | Round-trip must be near-perfect; >0.1% indicates real data corruption in the encoder. No matrix needed — this is a correctness floor, not a tolerance bar. |
| **Forge** | **1% / 5%** | Compaction fallback is "bigger request, works anyway" — lower user impact. Reasoning-chain drift (FMEA F.2) is the real concern, but that's a binary alert (either the schema is known or it isn't), not a percentage. |
| **RTK** | **5% / 15%** | Binary missing / crash is visible; subprocess failures are expected for unsupported platforms. Higher tolerance reflects lower severity (Matrix 6 ranks RTK severity at 1.85, the lowest). |

All four component-specific thresholds are written into `compression:` YAML config per §4.4; operators override per-deployment if needed.

---

## 2. ELICITATION TARGET #2 — QUALITY MEASUREMENT METHODOLOGY

### 2.1 The question restated

How does Praxis know that a compressed output preserves the meaning of its uncompressed input? Structural checks catch code-block corruption, URL loss, heading count mismatch — but do not catch semantic drift. What's the right layering of validators?

### 2.2 What the draft said before elicitation

**§3.4.4 structural validator:**
- H1 heading count match
- H2 code block byte-exact match
- H3 URL set match
- H4 file-path set match
- H5 bullet count within 15% tolerance (placeholder)

**§3.4.5 semantic validator (Stage 2 addition):**
- S1 negation token count preservation
- S2 numeric literal preservation

Embedding-based semantic similarity was deferred to Stage 3 (§10.3 in original draft).

### 2.3 What the FMEA surfaced

Two critical blind spots in the draft's semantic validator:

**FMEA V.2 — Negation-count check is fooled by simultaneous add-and-drop.** "Not recommended" compressed to "recommended" has the same negation count *if the compression adds another "not" somewhere else*. S1 passes; meaning flips. Concrete adversarial example: input "do NOT use X, and do NOT enable Y" compressed to "do use X, and do NOT enable Y" preserves negation count (1 in original, 1 in compressed) but inverts the imperative.

**FMEA V.3 — Antonym swap escapes S1 entirely.** "Safe" → "unsafe" involves zero negation tokens. The check is blind to antonym flips that don't go through the `not/no/never` lexicon.

### 2.4 What the Comparative Matrix scored

**Matrix 7 — Quality measurement methodology**

Criteria: coverage of known drift types (0.30), impl cost (0.15), runtime latency (0.15), false positive rate (0.20), maintainability (0.20).

| Option | Coverage | Impl | Latency | FP | Maint. | **Weighted** |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|
| 1. Structural only | 1 | 5 | 5 | 5 | 5 | 3.30 |
| 2. + S1 (negation) | 2 | 5 | 5 | 4 | 5 | 3.45 |
| 3. + S1 + S2 (numbers) | 3 | 4 | 5 | 4 | 5 | 4.05 |
| **4. + S1–S4** (polarity + imperative) | 4 | 4 | 5 | 4 | 4 | **4.15** ⭐ |
| 5. + embedding cosine | 5 | 3 | 3 | 3 | 3 | 3.75 |
| 6. + LLM-as-judge | 5 | 2 | 1 | 3 | 2 | 2.85 |

**Winner:** Option 4 — Structural + S1–S4. Embedding cosine is advanced from Stage 3 to Stage 2 P1 (deferred after S1–S4 ships, not rejected outright). LLM-judge is rejected.

### 2.5 Answer

**Quality measurement methodology (post-elicitation):**

The Caveman compression layer uses a **4-tier validation stack**:

```
┌─────────────────────────────────────────────────┐
│ Tier 1 (Structural, H1–H5):                    │
│   heading / code / URL / path / bullet         │
│   Fast, deterministic, catches corruption      │
├─────────────────────────────────────────────────┤
│ Tier 2 (Semantic baseline, S1–S2):             │
│   negation token count + numeric literals      │
│   Fast, catches bulk semantic loss             │
├─────────────────────────────────────────────────┤
│ Tier 3 (Semantic defense-in-depth, S3–S4):     │
│   polarity pair preservation (antonym flips)   │
│   + imperative inversion detection             │
│   New in Stage 2 P0, closes FMEA V.2 / V.3     │
├─────────────────────────────────────────────────┤
│ Tier 4 (Embedding cosine — Stage 2 P1):         │
│   Reserved for post-deployment tuning          │
│   Advanced from Stage 3 in response to         │
│   remaining blind spot on synonym-based drift  │
└─────────────────────────────────────────────────┘
```

**S3 — Polarity pair preservation (new).** Maintains a small, conservative antonym lexicon (15 pairs: `safe/unsafe`, `recommended/discouraged`, `allow/deny`, `enable/disable`, etc.). For each pair, compression may change absolute counts but MUST NOT flip the sign of the positive-minus-negative bias. Catches FMEA V.2 / V.3.

**S4 — Imperative inversion (new).** Counts positive vs negative imperative verbs (`do/use/run/call/include/set/enable/apply/add` vs `don't/avoid/skip/exclude/disable/never/remove/omit`). Delta between original and compressed must be ≤ 1. Catches "do X" → "don't X" transformations that escape S1.

**S3 and S4 are intentionally false-positive-biased.** A wrongly-flagged compression triggers a cheap retry; a false negative on semantic drift corrupts meaning silently. At Stage 2 P0, false positives are the acceptable cost.

**Architecture edits applied:**
- §3.4.5 rewritten with S3 and S4 definitions + POLARITY_PAIRS and IMPERATIVE sets inline
- §9.2 added property tests P_V3 (polarity flip) and P_V4 (imperative inversion)
- §10.3 updated: embedding cosine advanced from Stage 3 to Stage 2 P1

### 2.6 Additional measurement infrastructure surfaced by FMEA + Matrix

The elicitation also surfaced that quality measurement requires **infrastructure beyond the validators themselves**:

1. **Calibration staleness guard (FMEA V.4, architecture §3.4.3):** the Caveman net-positive gate denies compression if the A/B harness's calibration is older than `max_calibration_age_seconds` (7 days default). A stale calibration is worse than no compression.

2. **Ground-truth feedback loop (FMEA V.5, architecture §3.4.3):** the caller's `expected_downstream_reads` is a prediction. The compression layer records `(request_id, expected, actual_observed_in_7d)` tuples; nightly harness computes `prediction_error_pct`; if median error > 30%, `break_even_reads` auto-raises by 1. Over-prediction is systematically penalized until predictions stabilize.

3. **Reconciliation round-trip test (FMEA P.4, architecture §9.4 #6):** CI test produces 100 compression-tagged requests, queries Pi-Mono via `get_cost_summary`, sums the tag aggregates, compares against the A/B harness's reported savings. Drift > 0.5% fails the test (Matrix 5 tightened from 1% → 0.5%).

All three are now canonical parts of the measurement methodology — not optional add-ons.

---

## 3. ELICITATION TARGET #3 — CONSEQUENCE HIERARCHY

### 3.1 The question restated

If multiple components can fail, which failure is worst? This drives:
- Test-effort allocation (Murat's Step 2.2)
- Implementation priority (Amelia's Step 2.3)
- Circuit-breaker hardening depth
- Pre-sales messaging emphasis

### 3.2 What the draft said before elicitation

**§5.2 fail-safe ordering (original):** A 4-item ordered list:
1. Return structurally valid output
2. Preserve billing accuracy
3. Attribute the failure
4. Don't cascade

No component ranking. No explicit cascade enumeration. "Don't cascade" was stated but untestable — there was no list of what-must-run-when-X-fails.

### 3.3 What the FMEA surfaced

**FMEA P.1 — Cascade isolation is underspecified.** The architecture asserted isolation as a principle but didn't enumerate paths. A test engineer reading §5.2 would not know which cascades to test.

**Fix applied:** §5.2 now contains a 6-row cascade table (TONL encode fail, TONL decode fail, Forge fail, Caveman fail, RTK fail, Pi-Mono fail). Each row names what still runs and what does NOT happen. §9.4 test #5 iterates the table as an integration test.

### 3.4 What the Comparative Matrix scored

**Matrix 6 — Component severity ranking**

This is the canonical consequence hierarchy. Criteria: user-visible impact (0.30), billing correctness (0.25), recovery cost (0.15), detection lag (0.15), cascade risk (0.15). Scale 1–5 where **5 = MOST severe**.

| Rank | Component | User | Billing | Recovery | Detect lag | Cascade | **Severity** |
|:---:|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 🔴 | Orchestrator | 5 | 4 | 3 | 3 | 5 | **4.15** |
| 2 🟠 | Caveman | 4 | 3 | 4 | 5 | 2 | **3.60** |
| 3 🟡 | Forge | 3 | 2 | 3 | 4 | 3 | **2.90** |
| 4 🟡 | TONL | 4 | 3 | 2 | 2 | 2 | **2.85** |
| 5 🟢 | RTK | 2 | 2 | 2 | 2 | 1 | **1.85** |

### 3.5 Answer

**Consequence hierarchy (post-elicitation), in descending severity:**

1. **Orchestrator (severity 4.15).** A cascade leak disables multiple components in a single request. Silent test gap was that §5.2 asserted isolation without enumerating paths. **Highest priority for test effort.** The 6-row cascade enumeration (§5.2) + the chaos test (§9.4 #5) are the two highest-value gates in the whole Stage 2 test strategy.

2. **Caveman (severity 3.60).** Silent semantic drift corrupts user-visible content. Detection lag is the highest of any component (5/5) because semantic corruption looks plausible. Highest leverage for correctness investment → S3/S4 validators are non-negotiable P0.

3. **Forge (severity 2.90).** Broken reasoning chains mislead downstream agent turns. Not user-visible directly, but cascades into the next agent's behavior. Reasoning-schema drift (FMEA F.2) and non-overwrite (FMEA F.6) closed as hard gates.

4. **TONL (severity 2.85).** Round-trip loss is well-contained by Hypothesis property tests. Tied with Forge in the middle.

5. **RTK (severity 1.85).** Binary crashes are loud; attribution errors are isolated. Lowest severity — RTK ships with minimum viable wrapper; don't over-invest in its tests.

### 3.6 Implications propagated to architecture

The severity ranking is now **§11.4 in the architecture document** as a canonical reference. It drives three downstream commitments:

- **Murat's test strategy (Step 2.2):** test-effort allocation mirrors the ranking. Orchestrator cascade tests come first; Caveman semantic validator property tests come second; Forge + TONL share third; RTK is last.
- **Amelia's implementation priorities (Step 2.3):** orchestrator fail-safe ordering and `try/except` boundaries are P0 non-negotiable; Caveman S3/S4 are P0; RTK minimum viable wrapper is acceptable.
- **Pre-sales messaging (Step 2.6):** lead with Caveman quality preservation, NOT RTK compression rate. A single silent semantic drift incident erases the credibility of any savings headline.

**Architecture edits applied:**
- §5.2 cascade enumeration table (6 rows)
- §9.4 test #5 iterates the table as chaos test
- §11.4 new section: Matrix 6 severity ranking as canonical reference with implications for Murat, Amelia, and pre-sales

---

## 4. FULL LOG OF ARCHITECTURE EDITS APPLIED

Sixteen edits were applied to `compression/architecture.md` during Elicitation Round 1. Grouped by source:

### 4.1 From FMEA (Method 2) — 12 edits

| # | Section | Edit | FMEA driver |
|:---:|---------|------|:-----------:|
| 1 | §3.4.5 | S3 polarity pair validator added | V.2 |
| 2 | §3.4.5 | S4 imperative inversion validator added | V.3 |
| 3 | §3.4.3 | Calibration staleness guard (`max_calibration_age_seconds`) | V.4 |
| 4 | §3.4.3 | Ground-truth feedback loop (prediction_error → auto-raise) | V.5 |
| 5 | §3.2.3 | Forge reasoning schema version detection + alert | F.2 |
| 6 | §3.2.3 | Forge reasoning non-overwrite guard (strengthened) | F.6 |
| 7 | §6.3 | A/B harness seed pinning | P.3 |
| 8 | §6.3, §8.2 | A/B harness config_hash fairness assertion | P.5 |
| 9 | §4.1 | Tag budget ceiling (28) + priority drop order | P.2 |
| 10 | §2.4, §10.4 | RTK orphan timeout (60s) + bucket attribution | R.8 |
| 11 | §5.2, §9.4 | Cascade isolation 6-row enumeration + chaos test | P.1 |
| 12 | §3.4.4, §10.11 | Bullet drift threshold marked placeholder + new §10.11 for calibration | V.10 |

### 4.2 From Comparative Matrix (Method 5) — 4 edits

| # | Section | Edit | Matrix driver |
|:---:|---------|------|:-------------:|
| 13 | §10.2 | Caveman fallback threshold 5/10 → **3% warn / 7% disable** | Matrix 1 |
| 14 | §2.4, §10.4 | RTK orphan rate investigation 10% → **5% sustained 24h** | Matrix 4 |
| 15 | §9.4 #6 | Reconciliation round-trip drift tolerance 1% → **0.5%** | Matrix 5 |
| 16 | §11.4 (new) | Component severity ranking as canonical reference | Matrix 6 |

### 4.3 Matrix-recommendations NOT adopted (with rationale)

One matrix-winner was not applied:

**Matrix 2 — `max_calibration_age_seconds`: recommended 3 days, kept 7 days.**

- Matrix result: 3 days wins by 0.10 margin
- Reason for override: operational predictability matters more when the team is bootstrapping Stage 2. A 3-day window gives no slack for holiday weekends or on-call rotations. The 0.10 margin is small enough that operational friction dominates mathematical optimum.
- **Commitment:** Review `max_calibration_age_seconds` at first 30-day production review. Tighten to 3 days if observed harness run rate is reliable and staleness drift is causing issues.

---

## 5. OPEN QUESTIONS ESCALATED TO ANDREY

After elicitation, two questions from §10 remain open for Andrey's direct decision. These are escalated deliberately — the elicitation could not decide them and Murat cannot proceed without Andrey's input:

### 5.1 Caveman scope for Stage 2 P0 (§10.1)

**Question:** Caveman is LLM-driven (not zero-cost). The architecture now has a net-positive gate, calibration staleness guard, prediction feedback loop, and 4-tier validation stack to make it safe. But all of that infrastructure is justified ONLY if Caveman is actually in Stage 2 P0. Should it slip to Stage 3?

**What the FMEA + Matrix work revealed:**
- Caveman is the second-highest severity component (Matrix 6)
- Its failure mode (silent semantic drift) is the single most expensive product risk in the architecture
- The net-positive gate is self-correcting only if the A/B harness is actually running nightly (operational dependency)
- 2 of the 16 edits exist solely to make Caveman safer (V.4 staleness + V.5 feedback loop)

**Options:**

| Option | Pros | Cons |
|--------|------|------|
| **A. Keep in Stage 2 P0** (current plan) | Delivers the full "3 compression layers" narrative; produces first Caveman production data for Stage 3 calibration | Complex infrastructure must be operational from day 1; silent-drift risk if any gate misconfigures |
| **B. Slip to Stage 3** | Reduces Stage 2 surface area by ~15%; Caveman arrives with Stage 3's memory/retrieval context (natural fit) | "Two compression layers combined deliver X%" is a softer pre-sales headline than "three"; loses the pay-forward savings argument |
| **C. Ship Caveman as opt-in behind a feature flag** | Best of both: production validates gate infrastructure without exposing user-visible risk | Feature-flag proliferation; ambiguous savings claim |

**Recommendation (from elicitation, not from Andrey):** Option C — ship Caveman behind a `compression.caveman.enabled` flag defaulted OFF at first deploy, flip ON once the A/B harness confirms break-even N is stable. This matches the "measured savings with quality preservation" pitch without risking the first production incident.

**Who decides:** Andrey. **This question is a precondition for Amelia's implementation scoping (Step 2.3).**

### 5.2 Real-time semantic validation (§10.3, advanced)

**Question:** The elicitation advanced embedding-based semantic similarity from Stage 3 → Stage 2 P1 (ship first with S1–S4; add embeddings after initial production calibration). But is Stage 2 P1 the right window, or should embeddings arrive in Stage 2 P0 alongside S3/S4?

**Options:**
- **P0:** Ship embeddings with S1–S4. Higher infrastructure cost, lower false-negative rate.
- **P1 (current recommendation):** Ship S1–S4 first, add embeddings after ~30 days of production calibration against observed false-positive / false-negative rates.

**Recommendation:** P1. Embedding cosine without calibration is a knob without a number — better to calibrate against real drift data than to guess.

**Who decides:** Winston + Murat, with Andrey informed. Non-blocking for Stage 2.2 Murat.

---

## 6. DOWNSTREAM HANDOFF

### 6.1 Next step — Step 2.2 (Murat / Test Architect)

The architecture document v0.2 (post-elicitation) is stable and ready for Murat's test strategy. Key inputs for Murat:

- **§9 Testability Notes** — 11 property tests (P_T1–P_T3, P_F1–P_F6, P_V1–P_V7, P_R1–P_R2), 11 integration tests, 4 coverage targets, 1 perf benchmark per component
- **§11.4 Component severity ranking** — drives test-effort allocation in rank order (Orchestrator → Caveman → Forge/TONL → RTK)
- **§5.2 cascade isolation table** — 6-row enumeration that becomes the chaos test matrix
- **Caveman fallback thresholds** (§10.2) — 3% / 7% from Matrix 1; test fixtures need to generate controlled false-positive and false-negative rates to calibrate
- **Reconciliation drift** (§9.4 #6) — tightened to 0.5%, requires integration test with real Pi-Mono tracker
- **New property tests** from FMEA: P_F5b (non-overwrite), P_F6 (schema drift), P_V3 (polarity), P_V4 (imperative), P_V6 (calibration staleness), P_V7 (prediction feedback)

Murat's test strategy should concentrate on:
1. **Orchestrator cascade chaos suite** (Priority 1 per Matrix 6)
2. **Caveman semantic validator adversarial corpus** (Priority 2 per Matrix 6, plus P_V3 / P_V4 from FMEA)
3. **Forge reasoning preservation** (P_F5, P_F5b, P_F6)
4. **TONL round-trip property tests** (P_T1–P_T3)
5. **RTK integration smoke tests** (Priority 5 — minimum viable)

### 6.2 Precondition on Andrey

**Before Murat begins Step 2.2:** Andrey must decide §5.1 (Caveman scope for P0). Murat's test strategy depth for Caveman depends on whether it's a P0 component or a feature-flagged P0 component.

If Andrey chooses Option A or C, Murat's test strategy covers Caveman at full depth.
If Andrey chooses Option B, Caveman moves to Stage 3 and the test strategy drops ~30% of its Caveman content.

**Recommendation to Andrey:** Choose Option C (feature-flagged) so the architecture surfaces are exercised in production without user-visible exposure.

### 6.3 No re-draft of architecture required

Elicitation Round 1 applied 16 edits inline; no structural rewrite is needed. Winston's architecture v0.2 is the final document for Step 2.1.5. Step 2.1 checkbox stands at `[x]`; Step 2.1.5 checkbox can advance to `[x]` once this document is merged.

If Stage 2 discovers new constraints later (during Amelia's implementation or Quinn's QA), they become Elicitation Round 2 inputs, not amendments to this doc.

---

## 7. METHOD-LEVEL RETROSPECTIVE

### 7.1 What Method 2 (FMEA) contributed

Systematic failure-space walk. Produced 40+ failure modes across 5 components, ranked by RPN (severity × frequency × detection), surfaced 5 top gaps that drove the 12 structural architecture edits. Most valuable finding: **Caveman is LLM-driven and costs tokens** — this single insight reshaped the pipeline composition, added the net-positive gate, and drove Matrix 1 and Matrix 3 in the subsequent round.

### 7.2 What Method 5 (Comparative Matrix) contributed

Converted the FMEA's qualitative findings into explicit, defensible numbers. Produced the canonical severity ranking (Matrix 6) that downstream agents (Murat, Amelia, Andrey) use as an authoritative reference. Most valuable output: **the tightened thresholds (3%/7% Caveman, 5% RTK orphan, 0.5% reconciliation drift)** — each a single decimal change with meaningful operational consequences.

### 7.3 Why two methods were enough

The third elicitation pass was recommended but not executed (user selected `x` to proceed). Pre-mortem and Red Team were considered — both would have produced narrative-based failure scenarios, but the FMEA's systematic coverage already captured the high-RPN failures. Running a third pass would risk circular findings rather than new signal. The architecture is stable.

If Stage 2 discovers a blind spot Murat, Amelia, or Quinn surface — it becomes Elicitation Round 2. That's the correct pattern: elicitation rounds are episodic, not continuous.

---

## 8. STATUS

- **Architecture document v0.2** (`compression/architecture.md`) — stable, 16 edits applied
- **This document** (`requirements-validation.md`) — captures FMEA findings, matrix results, open questions, and downstream handoff
- **Step 2.1.5 Pipeline.md checkbox** — ready to advance to `[x]`
- **Step 2.2 Murat** — ready to start, preconditioned on Andrey's §5.1 decision

**Elicitation Round 1 complete.**

— Winston + `/bmad-advanced-elicitation`, 2026-04-12
