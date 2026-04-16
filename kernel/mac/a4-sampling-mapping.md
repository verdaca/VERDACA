# A4 Sampling — Operator-Side Label Mapping (DO NOT SHARE WITH ANDREY IN ANY CONVERSATION)

**SENSITIVITY NOTE (2026-04-15 recovery):** An earlier Greek-letter version of this mapping was exposed in the coordinator conversation (team-lead session Read the previous mapping file, compromising A4 blinding under that label set). This file is the RECOVERY regeneration under a new label set (colors: Azure–Kelp) and a different random permutation. This file MUST NOT be Read, pasted, summarized, or otherwise exposed in any conversation Andrey will see — including this one — before Andrey submits his 27 scores.

**Purpose:** Reproducible label → (question, baseline) mapping for the Stage 5.6 A4 blind scoring package (recovery version). This file is operator-only; Andrey scores `mac/a4-sampling-blinded.md` without ever seeing this file.

**Written:** 2026-04-15 (recovery regeneration after protocol breach in coordinator session)
**Scope:** 3 pre-selected questions (Q1 Pricing, Q5 Moat, Q10 Diagnostic) × 3 baselines (B1 vanilla / B2 enhanced / B3 MAC) = 9 outputs under 9 color-name labels
**Supersedes:** the Greek-letter mapping (Alpha–Iota) which is considered CONTAMINATED and must not be reused for any future A4 round on this content.

---

## Randomization method (recovery regeneration)

**Explicit hand-assigned permutation** designed to satisfy FOUR constraints:

1. Each question (Q1 / Q5 / Q10) appears at 3 positions with consecutive gaps ≥ 2 in the alphabetical label order.
2. Each baseline (B1 / B2 / B3) appears at 3 positions with consecutive gaps ≥ 2.
3. All 9 (Q, baseline) pairs are uniquely assigned.
4. **DERANGEMENT:** No position's new (Q, baseline) mapping equals the old Greek-letter version's positional mapping at the same position.

### Constraint check

- Q1 positions: 1, 4, 8 — gaps 3, 4 — non-adjacent ✓
- Q5 positions: 2, 5, 7 — gaps 3, 2 — non-adjacent ✓
- Q10 positions: 3, 6, 9 — gaps 3, 3 — non-adjacent ✓
- B1 positions: 2, 4, 6 — gaps 2, 2 — non-adjacent ✓
- B2 positions: 3, 5, 8 — gaps 2, 3 — non-adjacent ✓
- B3 positions: 1, 7, 9 — gaps 6, 2 — non-adjacent ✓
- Uniqueness: 9 distinct (Q, B) pairs ✓
- Derangement: all 9 positional mappings differ from the Greek-letter version ✓

**Derangement detail (old → new at each position):**

| Position | Old Greek label | Old (Q, B) | New color label | New (Q, B) | Differs? |
|---|---|---|---|---|---|
| 1 | Alpha | (Q5, B2) | Azure | (Q1, B3) | ✓ |
| 2 | Beta | (Q1, B3) | Coral | (Q5, B1) | ✓ |
| 3 | Gamma | (Q10, B1) | Ember | (Q10, B2) | ✓ |
| 4 | Delta | (Q1, B2) | Flint | (Q1, B1) | ✓ |
| 5 | Epsilon | (Q5, B3) | Garnet | (Q5, B2) | ✓ |
| 6 | Zeta | (Q10, B2) | Hazel | (Q10, B1) | ✓ |
| 7 | Eta | (Q1, B1) | Indigo | (Q5, B3) | ✓ |
| 8 | Theta | (Q10, B3) | Jade | (Q1, B2) | ✓ |
| 9 | Iota | (Q5, B1) | Kelp | (Q10, B3) | ✓ |

No positional mapping is a trivial renaming. The Q identity differs at positions 1, 2, 7, 8, 9 (5 positions); the Q identity is preserved at positions 3, 4, 5, 6 (4 positions) but the B identity differs at all four of those — so the (Q, B) pair differs everywhere.

---

## The recovery mapping (color labels)

| Label | Position | Question | Baseline | Automated composite (from §4) |
|---|---|---|---|---|
| Azure | 1 | Q1 Pricing | **B3** MAC | 77.6 |
| Coral | 2 | Q5 Moat | **B1** Vanilla | 55.3 |
| Ember | 3 | Q10 Diagnostic | **B2** Enhanced | 65.9 |
| Flint | 4 | Q1 Pricing | **B1** Vanilla | 52.9 |
| Garnet | 5 | Q5 Moat | **B2** Enhanced | 63.5 |
| Hazel | 6 | Q10 Diagnostic | **B1** Vanilla | 54.1 |
| Indigo | 7 | Q5 Moat | **B3** MAC | 80.0 |
| Jade | 8 | Q1 Pricing | **B2** Enhanced | 68.2 |
| Kelp | 9 | Q10 Diagnostic | **B3** MAC | 80.0 |

**Automated rank order (highest to lowest composite):** Indigo (80.0) = Kelp (80.0) > Azure (77.6) > Jade (68.2) > Ember (65.9) > Garnet (63.5) > Coral (55.3) > Hazel (54.1) > Flint (52.9).

(Note the Indigo/Kelp tie at 80.0 — both are B3 outputs with all-4 gate scores. Spearman with ties uses the mean rank = 1.5.)

---

## Spearman ρ computation template (recovery version)

Once Andrey returns 27 scores keyed by the new color labels, fill in:

| Label | Andrey G1 | Andrey G2 | Andrey G3 | Andrey mean | Andrey composite (×20) | Automated composite | Andrey rank | Automated rank |
|---|---|---|---|---|---|---|---|---|
| Azure | | | | | | 77.6 | | 3 |
| Coral | | | | | | 55.3 | | 7 |
| Ember | | | | | | 65.9 | | 5 |
| Flint | | | | | | 52.9 | | 9 |
| Garnet | | | | | | 63.5 | | 6 |
| Hazel | | | | | | 54.1 | | 8 |
| Indigo | | | | | | 80.0 | | 1.5 |
| Jade | | | | | | 68.2 | | 4 |
| Kelp | | | | | | 80.0 | | 1.5 |

Then compute Spearman ρ = 1 − (6 × Σ d²) / (n × (n²−1)), where n=9, d = Andrey_rank − Automated_rank.

---

## Gate mapping reminder (unchanged from Greek-letter version)

| Andrey gate | Intent | Approximate automated proxy |
|---|---|---|
| G1 "Would I act on this?" | Actionability | R8 Actionability Calibration |
| G2 "Obviously wrong?" (reverse-coded: 5=nothing obviously wrong, 1=obvious errors) | Calibration / epistemic soundness | R1 Epistemic Calibration |
| G3 "Does this tell me something non-obvious?" | Novelty / insight | R10 Epistemic Scope Honesty + R4 Steelman quality |

---

## Post-scoring workflow

After Andrey submits 27 scores keyed by color labels:
1. Operator fills in the template above.
2. Operator computes Spearman ρ.
3. If ρ ≥ 0.6: A4 validation PASSED (with contamination caveat per §10 Limitation 9 of pre-sales-report.md). Operator updates `pre-sales-report.md` §8 with the computed ρ + pass statement, updates §1 executive summary headline, and sends the updated report for team-lead spot-check before marking Pipeline §5.6 `[x]`.
4. If ρ < 0.6: A4 validation FAILED. Operator updates `pre-sales-report.md` §8 with the computed ρ + fail statement, flags "automated scoring has drifted from human judgment" in §1, and escalates to team-lead for strategic decision (retune scoring? re-run with different judge? accept with credibility concern?). Pipeline §5.6 stays `[ ]` pending resolution.

**Contamination-aware interpretation:** Per pre-sales-report.md §10 Limitation 9, Andrey has residual knowledge of the automated rank structure (3 top-tier 78-80, 3 middle-tier 62-68, 3 bottom-tier 52-56) from the earlier contaminated mapping, but does NOT know which specific outputs map to which tier under the new color labels. A high Spearman ρ (e.g., ρ > 0.85) should be read with caution as it may be slightly inflated by this residual pattern knowledge; a moderate ρ (0.6-0.8) is a more credible validation signal; ρ < 0.6 is a genuine failure regardless of contamination.

---

**End of operator-side mapping (recovery version). This file MUST NOT be shown to Andrey in any conversation before he submits the 27 scores via `mac/a4-sampling-blinded.md`. The Greek-letter version is considered CONTAMINATED and must not be reused.**
