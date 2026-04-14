# MAC Quality Gate Rubric — Hardened

**Stage:** Praxis 5.0.2 — Elicitation Round 2  
**Produced by:** Dr. Quinn (systematic problem-solving specialist)  
**Methods used:** Failure Mode Analysis → Assumption Busting → TRIZ Contradiction Matrix  
**Input:** Carson's quality-dimensions-draft.md (14 dimensions)  
**Date:** 2026-04-14  
**Status:** HARDENED — input to Stage 5.0.3 (benchmark question set) and Stage 5.1 (Winston MAC architect)

---

## Executive Summary of Changes

| Category | Count | Summary |
|---|---|---|
| BLOCKER failure modes resolved | 4 | D2 Tier-1 redesign; D4 two-step judge; D10 reformulation; D12 specificity floor |
| CONCERN failure modes noted | 10 | Refinements to D1, D3, D5, D6, D7, D8, D9, D11, D13 — all buildable |
| Assumptions busted | 7 | 0 HOLD / 5 REVISE / 2 REPLACE |
| TRIZ tensions resolved | 3 | T3, T1/T4/T5 compound, T7 new |
| Dimensions removed | 2 | D14 (→ Stage 6); D7 (merged into R1) |
| Dimensions collapsed | 2→1 | D11 + D12 → R10 Epistemic Scope Honesty |
| Dimensions added | 2 | R12 Internal Consistency (confirmed); R13 Evidence Sourcing (conditional) |
| **Final gate count** | **12 confirmed + 1 conditional** | R1–R12 confirmed; R13 Winston's decision |
| Carson open questions resolved | 4/6 | OQ-1, OQ-2, OQ-3, OQ-4 partially; OQ-5, OQ-6 remain |
| New open questions | 3 | OQ-7, OQ-8, OQ-9 |

---

## Section 1: BLOCKER List — Must Resolve Before Winston Designs Gates

### BLOCKER-1: D2 (Question Fidelity) — Tier 1 gate contradicts 5/5 definition

**Problem:** The 5/5 definition says the analysis should answer the stated question AND flag when the question itself is wrong. But the Tier 1 check asks "does the conclusion answer the stated question?" — an analysis that correctly redirects to a better question FAILS Tier 1 on a 5/5 performance.

**Resolution:** Reformulate Tier 1: "Does the conclusion contain a direct answer to either (a) the stated question, OR (b) a reformulation of the question explicitly named in the analysis?" Both paths pass Tier 1. The BEST performance on this dimension (recognizing the question is wrong) passes, not fails.

**Winston action:** Gate prompt for D2/R2 must implement the OR logic at Tier 1.

---

### BLOCKER-2: D4 (Steelman Completeness) — LLM-judge false negative is systematic in novel domains

**Problem:** The LLM-judge evaluating steelman quality shares the producer's training prior. For niche positions not well-represented in training data, both the producer and the judge will miss the best counterargument simultaneously. The judge cannot evaluate what it doesn't know. This failure is worst in exactly the cases where D4 adds the most value.

**Resolution:** Mandatory two-step Tier 3 evaluation protocol:
1. Judge independently generates what it considers the BEST counterargument to the main conclusion (before reading the analysis's counterargument section)
2. Judge compares its independently-generated steelman to what the analysis included, assessing the gap

Without step 1, the evaluation is pattern-recognition of counterargument structure — not assessment of whether the actual best argument was captured.

**Winston action:** D4/R4 gate prompt must implement two-step evaluation. The comparison step explicitly asks: "What did the independent steelman include that the analysis's counterargument section missed?"

---

### BLOCKER-3: D10 (Structural Impartiality) — Gate fires systematically on well-reasoned analyses

**Problem:** Any analysis that reaches a well-supported conclusion organizes evidence toward that conclusion — because that is what evidence-based reasoning does. The current gate question ("does the analysis narratively favor one outcome?") cannot distinguish motivated reasoning (BAD) from coherent argumentation (GOOD). False positive rate on genuinely well-reasoned analyses is potentially very high.

**Additional problem (T7 tension):** A thorough steelman (D4) gives strong representation to the opposing view — which triggers the impartiality gate because the analysis "favors" that view. The gate penalizes the highest-quality D4 performance.

**Resolution:** Two changes:
1. **Reformulate the gate question**: From "is the analysis narratively neutral?" to "is the strength of the conclusion proportional to the strength of the evidence?" This targets motivated reasoning (conclusion exceeds evidence) without penalizing coherent argumentation.
2. **Restrict gate scope**: D10/R9 evaluates evidence and findings sections ONLY. Dedicated steelman sections (R4) and dissent sections (R5) are **explicitly exempt** from the impartiality gate — giving the opposing view full force in those sections IS the purpose, not a failure of impartiality.

**Winston action:** R9 (Evidence Impartiality) gate prompt must: (a) ask "does the conclusion strength exceed what the evidence in the findings sections supports?" not "is the analysis neutral?"; (b) receive only the findings/evidence subsections of the output, not the full document including steelman/dissent.

---

### BLOCKER-4: D12 (Unknown Unknown Acknowledgment) — Completely gameable with boilerplate

**Problem:** "We acknowledge that there may be factors outside our analysis that could affect the outcome. We recommend ongoing monitoring." This is 100% content-free. It satisfies every presence check, matches every LLM-judge pattern for this dimension, and delivers zero epistemic value. The gate is entirely defeatable by boilerplate. Starting at Tier 2 (retrieval) means no gate fires at all until Memory is seeded.

**Resolution (via merge with D11 into R10 Epistemic Scope Honesty):**
New Tier 1 check with a specificity floor: to pass Tier 1, the scope/blind-spot section must:
- Name at least one specific category of information NOT covered (scope declaration component — from D11)
- Name at least one specific reason WHY it might be missing something — method, expertise, time horizon, or perspective explicitly not available (blind spot component — from D12)

Boilerplate ("we may have missed things") fails. Specific ("we did not analyze regulatory precedents post-2023; our analysis team has no direct EU market operating experience") passes.

**Winston action:** R10 Tier 1 check requires presence of BOTH specific scope exclusion AND specific blind spot attribution. One generic acknowledgment sentence does not pass.

---

## Section 2: Failure Mode Analysis — Full Table

| Gate | False Positive Mode | False Negative Mode | Gaming Mode | Tier Verdict | Severity |
|---|---|---|---|---|---|
| **R1** Epistemic Calibration + Risk Specificity | Expert-audience communication; universal risks in regulated industries | Assumptions section masks body confidence-washing | Boilerplate assumptions section + cosmetic risk specificity details | Add body-level keyword density scan to Tier 1; reformulate risk specificity sub-check | CONCERN |
| **R2** Question Fidelity | Best performance (question redirection) fails Tier 1 — BLOCKER resolved by OR logic | Verbatim answer to proxy question | Question words copy-pasted into conclusion | Tier 1 OR logic fix; Tier 2 appropriate | BLOCKER → RESOLVED |
| **R3** Falsifiability | Deterministic/factual questions | Vague invalidation conditions | One sentence: "revised if [unmonitorable event] occurs" | Add specificity floor: invalidation conditions must name observable, monitorable events | CONCERN |
| **R4** Steelman Completeness | Settled questions; false balance forced | Systematic judge miss in thin-domain positions | Domain-vocabulary steelman structure without content fidelity | Two-step judge protocol mandatory — BLOCKER resolved | BLOCKER → RESOLVED |
| **R5** Dissent Preservation | Expert consensus domains | Slightly-off representation; patronizing framing | One-sentence dissent per view; manufactured dissent | Tier 1 must require content depth; manufactured dissent detection needed | CONCERN |
| **R6** Decision Relevance Density | Legitimate context-heavy analyses | Priority-marked executive summary + padding body | Strong exec summary; irrelevant appendices | Scope to primary deliverable layer (L1) only; acceptable gaming at appendix level | ACCEPTABLE |
| **R7** Reasoning Traceability | Expert-level inference compression for expert audiences | Inference markers present; logical connection still missing | Syntactic markers without logical validity | Add Tier 1 marker density; Tier 3 must assess logical validity not just markers | CONCERN |
| **R8** Actionability Calibration | Genuine uncertainty where gathering info IS the right action | Specific but unsupported recommendations | "Next Steps" section disconnected from analysis | Tier 1 fix: "further analysis" only fails if no conditional recommendation; co-evaluate with R7 | CONCERN |
| **R9** Evidence Impartiality (reformulated D10) | Well-reasoned conclusions look "biased" — BLOCKER; steelman sections trigger gate — BLOCKER resolved by scope restriction | Surface balance masks systematic source selection | Linguistic equalization | Restrict to findings sections; reformulate question to "conclusion proportional to evidence?" | BLOCKER → RESOLVED |
| **R10** Epistemic Scope Honesty (D11+D12 merged) | Internal memos with established scope context | Boilerplate acknowledgment — BLOCKER for D12 component | Boilerplate scope declaration | Both components required (specific exclusion + specific blind spot); no boilerplate pass | BLOCKER → RESOLVED (via specificity floor) |
| **R11** Scenario Coverage | Deterministic/technical questions | Same-magnitude scenarios ("10%" vs "15%") | Same recommendation at different confidence levels | Tier 1 must verify differentiated decision implications, not just scenario count | CONCERN |
| **R12** Internal Consistency (NEW) | Very low — internal contradiction is a real failure, not a debatable quality | Implicit contradictions (accepted premises that undermine later conclusions) | N/A — gaming internal consistency requires genuine consistency | Tier 1: direct contradiction detection; Tier 3: implicit contradiction assessment | HIGH — required addition |
| **R13** Evidence Sourcing (CONDITIONAL) | Agents operating from training knowledge shouldn't be penalized for not citing sources | Fabricated statistics pass all other gates | Cite plausible-sounding but unverifiable sources | Conditional on MAC retrieval architecture — Winston's decision | CONDITIONAL |
| **D14** Extractable Logic | Systematic false positive on expert-to-expert analyses | — | — | **REMOVED — defer to Stage 6** | MOOT |

---

## Section 3: Assumption Busting Results

### A1 — LLM-judge can reliably detect steelman quality
**REVISE:** Judge can assess steelman quality for well-represented positions. For all evaluations, the judge must first generate an independent steelman, then compare to what the analysis included. This two-step protocol is a hard engineering requirement for R4, not an optional enhancement.

### A2 — Dimensions are stable across task types without per-dimension calibration
**REVISE:** Universal dimensions require per-gate guard conditions. Before applying R5 (Dissent) and R11 (Scenarios), the MAC classifies whether the task is in a consensus/deterministic domain. In consensus domains: R5 passes if analysis explicitly notes consensus; R11 requirement is suspended with a note. Guard conditions are Winston's design responsibility in the Quality Gate Engine (architecture §4).

### A3 — Multi-agent information asymmetry produces genuinely different counterarguments
**REVISE:** Information asymmetry removes anchoring bias; it does not create perspectival diversity from same-model agents. The MAC's R4 differentiation claim requires that reviewer agents be explicitly prompted to argue the opposing case before evaluating the producer's steelman. Information hiding alone is insufficient. This is a constraint on Winston's Information Asymmetry Router design (architecture §5).

### A4 — Dimension scores correlate with decision outcomes
**REVISE:** The rubric measures epistemic quality properties hypothesized to correlate with better decisions. Stage 5.6 benchmark evaluation MUST include a validation component: do higher-scoring outputs produce better-rated decisions per human evaluators? The benchmark design (5.0.3) must include this validation loop explicitly. Without it, the +15-25% claim measures quality theater, not decision quality improvement.

### A5 — 1-5 scoring scale produces consistent scores without calibration corpus
**REPLACE:** The measurement protocol must include calibration anchors: at minimum 2 examples per dimension (one scoring 2, one scoring 4) embedded in the LLM-judge prompt as reference. The 5.0.3 benchmark questions and gold-standard answers should provide the initial calibration corpus. Until calibration examples exist, quality scores are relative across analyses, not absolute — the 5.6 comparison must control for judge variance.

### A6 — The 14 dimensions are independent enough to gate separately
**REVISE:** Structurally co-dependent dimension pairs must be evaluated jointly:
- **(R8, R7) co-evaluation:** If R8 actionability score is ≥4 but R7 traceability score is ≤2, both scores are capped at 3. Actionable recommendations not traceable to evidence fail both dimensions.
- **(R4, R5) co-evaluation:** If R5 dissent score is ≥4 but dissenting positions don't correspond to positions identified in the task context, R5 score is capped at 2. Manufactured dissent is penalized even when it appears thorough.

### A7 — The 14 dimensions cover all important quality failure modes
**REPLACE:** The rubric is incomplete without Internal Consistency (R12). An internally contradictory analysis passes all 14 existing gates. R12 is a confirmed required addition. Evidence Sourcing (R13) is a conditional required addition depending on whether MAC agents use retrieval-augmented generation. Both must be addressed before Winston finalizes the gate set.

---

## Section 4: TRIZ Contradiction Resolutions

### TRIZ-1: T3 — Epistemic Calibration (R1) vs. Actionability Calibration (R8)

**Contradiction:** Increasing R1 (more uncertainty labeling, explicit hedges, confidence ranges) → decreases R8 (recommendations become hedged, non-decisive). These dimensions pull in opposite directions on the same output sections.

**TRIZ principle applied:** Principle #1 — Segmentation

**Resolution:** Separate gate application by document section. R1 evaluates **findings/evidence sections only**. R8 evaluates **recommendations/conclusions sections only**. An analysis where findings are rigorously calibrated ("regulatory risk: HIGH, based on three analogous cases; confidence: inference, not direct legal review") AND recommendations are decisive ("Delay European expansion until Q3 2027") receives 5/5 on both gates — because they fire on different sections.

**Winston action item:** The MAC output structure contract (Task Interpreter design, §3) must require two labeled sections in all analysis outputs:
- `[FINDINGS]` section — evaluated by R1, R7, R9, R10 (epistemic quality gates)
- `[RECOMMENDATIONS]` section — evaluated by R8, R2 (actionability gates)

The Cycle 3 gate evaluation subsystem must be section-aware: different gates are applied to different labeled sections.

---

### TRIZ-2: T1/T4/T5 compound — Completeness dimensions (R4, R5, R7, R11) vs. R6 Decision Relevance Density

**Contradiction:** Steelmans, dissent sections, reasoning chains, and scenarios all require MORE content → R6 penalizes content bulk and rewards signal density.

**TRIZ principle applied:** Principle #7 — Nesting

**Resolution:** Required quality content is nested at different document levels. R6 evaluates the **primary deliverable layer (L1)** only — executive summary and key recommendations. All required completeness content (R4, R5, R7, R11) is gated on the **full document** including secondary and supporting layers. The tension dissolves: completeness dimensions are present at L2/L3 while L1 remains dense.

**Winston action item:** Output structure contracts must define three labeled content levels:
- **L1** (Executive Summary + Decisions) — evaluated by R6 density gate; must be dense
- **L2** (Main Analysis Body) — evaluated by R4, R5, R7, R8, R9, R11 content quality gates
- **L3** (Supporting Detail / Appendices) — not gated for quality; only R10 scope transparency applies

Gate evaluation subsystem applies **different gate subsets to different content levels**. R6 receives only L1; completeness gates receive L1+L2. This resolves T1, T4, and T5 simultaneously — all variants of the same compound tension, all resolved by the same structural principle.

---

### TRIZ-3: T7 (new) — D4 Steelman Completeness vs. D10 Structural Impartiality

**Contradiction:** Giving the opposing view full force (R4 improvement) → makes the analysis appear to favor that view, triggering the impartiality gate; maintaining strict evidence balance (R9 improvement) → constrains how much force the steelman can receive.

**TRIZ principle applied:** Principle #1 — Segmentation + Principle #23 — Feedback

**Resolution:** The tension exists because R4 and R9 were evaluated on the same document sections. Resolution:
1. **R9 scope restriction:** Evidence Impartiality applies ONLY to findings/evidence sections. Dedicated steelman and dissent sections are explicitly gate-exempt.
2. **R9 question reformulation:** Gate question changes from "is the analysis narratively neutral?" to "is the strength of the conclusion proportional to the strength of the evidence in the findings sections?"

These two changes structurally decouple R4 and R9: R4 evaluates the quality of the steelman section; R9 evaluates whether the findings section's conclusions are proportional to its evidence. They now operate on different sections with different questions.

**Winston action item:** R9 gate prompt receives only the findings/evidence subsections (not the full document). The output structure contract must label steelman and dissent sections as `[STEELMAN]` and `[DISSENT]` — explicitly marking them as R9-exempt. R9 gate instruction: "Evaluate whether the conclusion stated in the [RECOMMENDATIONS] section is proportional in strength and confidence to the evidence presented in the [FINDINGS] section. Do not evaluate [STEELMAN] or [DISSENT] sections."

---

## Section 5: Dimension Changes — Before/After

| # | Before (Carson) | After (Quinn hardened) | Change type | Reason |
|---|---|---|---|---|
| R1 | D1 Epistemic Calibration (Tier 1+3) | Epistemic Calibration + Risk Specificity absorbed (Tier 1+3, body scan added) | MERGED + STRENGTHENED | D7 is a specialized application of D1; saves one gate slot; Tier 1 body scan added for gaming resistance |
| R2 | D2 Question Fidelity (Tier 1+2) | Question Fidelity (Tier 1 OR-logic + Tier 2) | TIER 1 REDESIGNED | Blocker: best performance failed Tier 1 |
| R3 | D3 Falsifiability (Tier 1+2) | Falsifiability — specificity floor added (Tier 1+2) | MEASUREMENT REFINED | Vagueness gaming blocked by specificity requirement |
| R4 | D4 Steelman Completeness (Tier 3) | Steelman Completeness — 2-step judge protocol (Tier 3 two-step) | EVALUATION PROTOCOL UPGRADED | Blocker: false negative systematic in thin-domain positions |
| R5 | D5 Dissent Preservation (Tier 1+3) | Dissent Preservation — content depth floor + manufactured dissent detection (Tier 1+3) | TIER 1 STRENGTHENED | Concern: one-sentence gaming blocked; manufactured dissent detection added |
| R6 | D6 Decision Relevance Density (Tier 1+3) | Decision Relevance Density — scoped to L1 layer (Tier 1+3) | SCOPE CLARIFIED | TRIZ-2: scope restriction resolves compound tension |
| R7 | D8 Reasoning Traceability (Tier 2+3) | Reasoning Traceability — Tier 1 added + logical validity prompt (Tier 1+2+3) | TIER ADDED | Concern: no Tier 1 check was a gap; logical validity must be explicit in judge prompt |
| R8 | D9 Actionability Calibration (Tier 1+3) | Actionability Calibration — conditional recommendation fix + R7 co-eval (Tier 1+3) | TIER 1 REFINED + CO-EVAL ADDED | Concern: "further analysis" false positive; unsupported specificity gaming blocked |
| R9 | D10 Structural Impartiality (Tier 3) | **Evidence Impartiality** — reformulated question + scope restricted to findings sections (Tier 3, findings only) | RENAMED + REFORMULATED + SCOPE RESTRICTED | Blocker: systematic false positive on well-reasoned analyses; T7 tension resolved |
| R10 | D11 Scope Transparency + D12 Unknown Unknown (separate) | **Epistemic Scope Honesty** — merged, both components required, specificity floor (Tier 1+3) | MERGED + SPECIFICITY FLOOR | Blocker (D12): boilerplate gaming eliminated; saves one gate slot |
| R11 | D13 Scenario Coverage (Tier 1+2) | Scenario Coverage — differentiated implications required (Tier 1+2) | TIER 1 STRENGTHENED | Concern: same-magnitude scenario gaming blocked |
| R12 | *(missing)* | **Internal Consistency** — new gate (Tier 1+3) | ADDED | A7: internally contradictory analyses pass all existing gates; critical omission |
| R13 | *(missing)* | **Evidence Sourcing** — new gate, conditional (Tier 1+2) | CONDITIONALLY ADDED | A7: fabricated statistics pass all existing gates; include if agents use retrieval |
| *(removed)* | D7 Risk Specificity | Merged into R1 | REMOVED | Specialized case of D1 calibration; gate slot saved for R12 |
| *(removed)* | D14 Extractable Logic | Moved to Stage 6 | REMOVED | False positive systematic on expert analyses; format concern, not reasoning quality |

---

## Section 6: Hardened Rubric — Final Gate Set

### Confirmed Gates (12)

| Gate # | Name | Definition | Tier | Priority | Section Applied |
|---|---|---|---|---|---|
| **R1** | Epistemic Calibration | Claims labeled by evidential basis; confidence language proportional to evidence; risks referenced to entity-specific attributes | 1 (section presence + body keyword density scan) + 3 (LLM-judge: calibration quality + risk specificity) | **Critical** | Full document |
| **R2** | Question Fidelity | Analysis answers stated question OR explicitly-named reformulation; 5/5 includes meta-evaluation of whether the question was right | 1 (OR-logic: stated question OR named reformulation answered) + 2 (retrieval: question mapping consistency) | **Critical** | [RECOMMENDATIONS] section |
| **R3** | Falsifiability | Conclusions specify monitorable, observable invalidation conditions — not vague contingencies | 1 (presence of per-conclusion invalidation conditions) + 2 (retrieval: specificity comparison) | High | Full document |
| **R4** | Steelman Completeness | Strongest counterarguments included at full fidelity; evaluated via two-step judge (independent steelman generated first, then compared) | 3 two-step (independent generation then comparison; consensus-domain guard condition applies) | **Critical** | [STEELMAN] section |
| **R5** | Dissent Preservation | Minority views represented with content depth and proportional weight; manufactured dissent detected and penalized | 1 (presence + minimum content depth: reason for dissent required) + 3 (LLM-judge: faithful representation; consensus-domain guard condition applies) | **Critical** | [DISSENT] section |
| **R6** | Decision Relevance Density | L1 layer (executive summary + key recommendations) is dense with decision-relevant signal; key findings explicitly prioritized | 1 (priority markers for key findings in L1) + 3 (LLM-judge: L1 density assessment only) | Medium | L1 layer only |
| **R7** | Reasoning Traceability | Logic chain is followable step-by-step; inference markers present; logical validity of chain (not just syntactic markers) assessed | 1 (inference marker density ≥ threshold) + 2 (retrieval comparison) + 3 (LLM-judge: logical validity of chain) | **Critical** | L2 main analysis |
| **R8** | Actionability Calibration | Recommendations specific enough to guide next concrete action; "further analysis" without conditional recommendation fails; co-evaluated with R7 | 1 (actionable recommendations present; "further analysis without conditional recommendation" detection) + 3 (LLM-judge: specificity and groundedness; R7 co-eval: cap at 3 if R7 ≤ 2) | High | [RECOMMENDATIONS] section |
| **R9** | Evidence Impartiality | Conclusion strength in recommendations is proportional to evidence strength in findings; findings sections not narratively biased; steelman/dissent sections exempt | 3 (LLM-judge: applied to [FINDINGS] sections only; question: "is conclusion proportional to evidence?" not "is analysis neutral?") | Medium | [FINDINGS] sections only |
| **R10** | Epistemic Scope Honesty | Specific scope declaration (what examined AND what not); specific blind spot acknowledgment (named method/expertise/perspective gap) — both components required, boilerplate fails | 1 (presence of BOTH specific exclusion AND specific blind spot attribution) + 3 (LLM-judge: quality of blind spot identification) | High | Full document |
| **R11** | Scenario Coverage | Multiple plausible futures with differentiated decision implications and trigger conditions; guard condition for deterministic domains | 1 (scenario presence + differential implications verification; deterministic-domain guard condition) + 2 (retrieval: scenario differentiation quality) | High | L2 main analysis |
| **R12** | Internal Consistency | Analysis does not contradict itself; premises accepted in findings are not denied in conclusions | 1 (direct contradiction detection: flag specific text contradictions) + 3 (LLM-judge: implicit contradiction assessment across sections) | High | Full document |

### Conditional Gate (Winston's Decision)

| Gate # | Name | Definition | Tier | Condition |
|---|---|---|---|---|
| **R13** | Evidence Sourcing | External factual claims are attributable to sources (or explicitly labeled as agent knowledge/inference); fabricated statistics prevented | 1 (source attribution for external factual claims) + 2 (retrieval: factual consistency check) | **Include if** MAC agents use retrieval-augmented generation with source access. **Defer to Stage 6** if agents operate from training knowledge only. |

---

## Section 7: Structural Architecture Requirements for Winston

These are not just gate design notes — they are **mandatory architectural requirements** derived from the TRIZ resolutions and dimension co-evaluations.

### Req-A: Section-Labeled Output Structure Contract

All MAC analysis outputs must use labeled sections. Minimum required labels:

| Label | Purpose | Gates that apply |
|---|---|---|
| `[FINDINGS]` | Evidence and findings sections | R1, R7, R9 (findings), R10, R12 |
| `[RECOMMENDATIONS]` | Decision and action sections | R2, R8, R9 (conclusion proportionality check) |
| `[STEELMAN]` | Dedicated counterargument sections — R9 exempt | R4 |
| `[DISSENT]` | Dedicated minority view sections — R9 exempt | R5 |
| `[SCENARIOS]` | Alternative futures section | R11 |

The Task Interpreter (§3) must require these labels in output format contracts. The Quality Gate Engine (§4) must be section-aware.

### Req-B: Section-Aware Gate Evaluation Subsystem

The Cycle 3 gate evaluation pass must not apply all gates to the full document. It must:
1. Parse section labels from the output
2. Route each gate to the appropriate section(s) per the table above
3. Evaluate R6 only on L1 content (executive summary + key recommendations)
4. Evaluate completeness gates (R4, R5, R7, R11) on L2 content + their dedicated sections
5. Exempt `[STEELMAN]` and `[DISSENT]` sections from R9 evaluation

### Req-C: Co-Evaluation Pairs

The Quality Gate Engine must implement co-evaluation logic for dependent dimension pairs:

- **(R8, R7):** If R8 specificity score ≥4 AND R7 traceability score ≤2 → both scores capped at 3. Unsupported actionability is a compound failure.
- **(R5, R4):** If R5 dissent score ≥4 AND dissenting positions do not correspond to positions referenced in the task context → R5 capped at 2. Manufactured dissent is penalized.

### Req-D: LLM-Judge Calibration Corpus

Before the first MAC deployment, the LLM-judge prompt for each gate must include:
- One calibration example scoring 2/5 (with explanation of why)
- One calibration example scoring 4/5 (with explanation of why)

These anchor examples prevent scale drift across judge instances. The 5.0.3 benchmark question set and gold-standard answers should provide these anchors. The 5.6 pre-sales evaluation requires anchor-calibrated judges to produce meaningful comparative scores.

### Req-E: Domain Guard Conditions

The Quality Gate Engine must implement a task-type classification check before applying:
- R5 Dissent Preservation: if task classified as consensus/settled-fact domain → R5 passes if analysis explicitly notes the consensus; absence of dissent section is not penalized
- R11 Scenario Coverage: if task classified as deterministic/binary domain → R11 gate is suspended; a note is added that scenarios don't apply

Winston's architecture §4 (Quality Gate Engine) must document the classification mechanism and domain taxonomy.

### Req-F: Reviewer Agent Prompt Requirement for R4

The Information Asymmetry Router (§5) must ensure that reviewer agents assigned to evaluate steelman completeness are explicitly prompted to:
1. First construct what they independently consider the best counterargument
2. Then read the analysis's steelman section
3. Then assess the gap

Information hiding alone is insufficient for R4 improvement — the reviewer prompt must actively elicit independent counterargument construction.

---

## Section 8: Measurement Protocol Refinements — Top 5 Gates

The following refinements REPLACE the corresponding sections in Carson's quality-dimensions-draft.md Section 3.

### R4 — Steelman Completeness (1–5) — REVISED

| Score | Criteria |
|---|---|
| **1** | No counterarguments present; analysis reads as advocacy. |
| **2** | Counterarguments present but weakened (straw men); a knowledgeable holder of the opposing view would not recognize their best argument. |
| **3** | Some real counterarguments included; the strongest opposing argument partially represented but not at full fidelity. |
| **4** | The strongest counterargument included with full representation; analysis engages substantively; gap between independently-generated steelman and included steelman is small. |
| **5** | Multiple steelman counterarguments at full fidelity; gap between independently-generated steelman and included steelman is negligible; analysis explicitly credits remaining strength of counterarguments even where not resolved. |

**Key change from Carson:** Score is now defined relative to the gap between the judge's independently-generated steelman and the analysis's counterargument section. Without this anchor, 3 and 4 are subjective.

---

### R1 — Epistemic Calibration (1–5) — REFINED

| Score | Criteria |
|---|---|
| **1** | All claims stated with uniform confidence; no distinction between facts and assumptions; confident language throughout; no assumptions section. |
| **2** | Some hedging present but inconsistent; major inferences stated as facts; confidence language doesn't track evidence quality; assumptions section absent or empty. |
| **3** | Most major claims labeled; some assumptions implicit in prose; hedging present but not systematically applied; assumptions section present but not comprehensive. |
| **4** | All major claims labeled with evidential basis; confidence language proportional to evidence; explicit assumptions section; entity-specific risks distinguished from category-generic risks. |
| **5** | Every claim labeled; uncertainty quantified where possible; assumptions section comprehensive; risks are entity-specific with explicit entity-attribute references; body keyword density scan: ≤30% strong-certainty language ("will," "is/are certain," "proves") on inferential claims. |

**Key change from Carson:** Added entity-specific risk requirement (absorbing D7) and body keyword density scan criterion.

---

### R2 — Question Fidelity (1–5) — REDESIGNED

| Score | Criteria |
|---|---|
| **1** | Analysis answers a different question than posed; stated question appears as pretext; conclusion doesn't address the decision. |
| **2** | Analysis partially addresses the question; significant scope drift; related but not identical question answered with confidence. |
| **3** | Analysis addresses the main question; some off-target content; conclusion provides a direct answer but with sub-question gaps. |
| **4** | Analysis directly answers the stated question (or explicitly-named reformulation) with all major sub-questions addressed. |
| **5** | Analysis answers the stated question AND explicitly evaluates whether the stated question was the right question to ask; flags if incomplete, misframed, or answering it would be insufficient for the actual decision. |

**Key change from Carson:** Score 4 now explicitly includes the "explicitly-named reformulation" path — a D2/R2 score-5 performance no longer fails the gate.

---

### R5 — Dissent Preservation (1–5) — REFINED

| Score | Criteria |
|---|---|
| **1** | Single viewpoint presented as if universal; no acknowledgment that other perspectives exist. |
| **2** | Acknowledges other views exist but doesn't represent them with content ("some disagree"); dissent is a sentence, not a position. |
| **3** | Minority views summarized accurately with stated reason for the dissent; not straw-manned but given minimal space. |
| **4** | Minority views presented with the same rigor as majority views; reason for dissent clearly stated; attribution clear; views correspond to positions referenced in task context (not manufactured). |
| **5** | Explicit dissent section with the dissenting position's full argument; dissent proportionally represented; analysis does not steer the reader toward dismissal; corresponds to actual positions in the task context. |

**Key change from Carson:** Score 4 and 5 now require that dissenting views correspond to actual positions in the task context — manufactured dissent is capped at score 2.

---

### R8 — Actionability Calibration (1–5) — REFINED

| Score | Criteria |
|---|---|
| **1** | No recommendations; analysis ends with conclusions only; "further analysis recommended" without any conditional recommendation. |
| **2** | Direction stated but no specific actions; or: epistemic cowardice ("more information needed") without a conditional recommendation for the current information state. |
| **3** | Recommendations present and specific enough to guide next action; some hedging that doesn't eliminate decisiveness; "further analysis" paired with a conditional recommendation for now. |
| **4** | Recommendations specific, decisive, and traceable to the analysis body via R7 reasoning chain; over-prescription absent (decision-maker agency preserved). |
| **5** | Recommendations at score 4 PLUS: explicitly distinguishes between actions within decision-maker's control and those requiring further information; staged recommendation where uncertainty warrants ("proceed with X; revisit Y when Z is known"). |

**Key change from Carson:** Score 1 is now more precisely defined — "further analysis" only fails if unaccompanied by conditional recommendation. Score 4 now requires traceability to R7 reasoning chain.

---

## Section 9: Open Questions Resolved and Remaining

### Resolved (from Carson's OQ-1 through OQ-6)

**OQ-1 RESOLVED:** D11 + D12 collapsed into R10 Epistemic Scope Honesty. Both components required; specificity floor eliminates D12 boilerplate gaming.

**OQ-2 RESOLVED:** D14 removed from Stage 5 gate set. Systematic false positive on expert-to-expert analyses confirms it is a Stage 6 format concern, not a Stage 5 reasoning quality gate.

**OQ-3 RESOLVED:** D10 reformulated as R9 Evidence Impartiality, applied to findings sections only. Tier 3 now evaluates a specific document subsection (not full document), making it less expensive than full-document evaluation. Sampling may still be warranted as an optimization — Winston's call.

**OQ-4 PARTIALLY RESOLVED:** R11 Tier 1 now requires differentiated decision implications (not just scenario count), which is a stricter and more universally applicable check. Task-type guard conditions (deterministic domains exempt) address the floor variation question. Remaining question: should guard condition logic be per-workflow-template or per-task-classification at runtime? Deferred to Winston.

### Resolved (OQ-5, OQ-6) — by Stage 5.0.3

**OQ-5 RESOLVED:** Top-5 weighted model for Stage 5.6 first run; empirically validated after. Gates R1, R2, R4, R5, R7 each weighted 2×; all others 1×. Total weight units: 17. Composite score = Σ(gate_score × gate_weight) / (17 × 5) × 100. Empirical update protocol: after first 5.6 run, revise weights based on observed variance between MAC and baselines. See `benchmark-questions.md` §7 for full rationale.

**OQ-6 RESOLVED:** 10 gold-standard task records (one per benchmark question) pre-loaded into Memory before first real user task. Each record carries task signature, approach, preset quality score (4.2/5.0), and gate-specific indicators as reasoning trace. Records flagged `bootstrap: true` to distinguish from organic experience. Winston must design explicit bootstrap protocol in Learning Loop architecture (§6), including: (a) pre-load mechanism, (b) `bootstrap: true` flag handling in retrieval scoring, (c) future quality audit of bootstrap vs. organic entries. See `benchmark-questions.md` §8 for full bootstrap plan.

### New Open Questions for Winston (OQ-7 through OQ-9)

**OQ-7:** Should R13 (Evidence Sourcing) be included? Depends on whether MAC agents use retrieval-augmented generation with source access. If agents generate analysis from training knowledge only, R13 creates false positives. Winston must decide during architecture §3 (Task Interpreter) design whether agent retrieval is in scope for Stage 5.

**OQ-8:** How should the scoring model handle R7+R8 co-evaluation cap (cap at 3 when R7 ≤ 2 despite R8 ≥ 4)? Three options: (a) hard cap at 3 on both; (b) R8 score = min(R8 raw, R7 raw + 1); (c) co-failure flag rather than score modification. Architecture §4 Quality Gate Engine must decide.

**OQ-9:** Req-E domain guard conditions require a task-type classification mechanism. How does the MAC classify task type? Options: (a) Task Interpreter extracts domain classification as part of structured Task object; (b) dedicated classification gate before Cycle 1; (c) per-workflow-template guard condition flags in the workflow YAML. This is a design decision for architecture §3 + §4.

---

## Section 10: Handoff to Stage 5.0.3

**What 5.0.3 must accomplish:**
1. Finalize the 10 benchmark strategic questions (from Tokonomics rounds or equivalent)
2. Produce gold-standard answers for each — these become the initial Memory corpus AND the calibration anchors for LLM-judge prompts (Req-D)
3. Design the scoring protocol for the 5.6 benchmark evaluation — including the validation loop (A4 assumption: do higher-scoring outputs correlate with better-rated decisions?)
4. Address OQ-5 (gate weighting): benchmark data should guide weighting rather than a priori assignment
5. Address OQ-6 (bootstrapping): benchmark question answers seed initial Memory corpus

**What 5.0.3 does NOT need to address:**
- Gate count or composition — resolved here (R1–R12 confirmed, R13 conditional)
- Dimension definitions — hardened here; Winston builds from this document
- Tier assignments — established here; Winston validates during architecture
- OQ-7, OQ-8, OQ-9 — Winston's design decisions during architecture §3/§4

**Input documents for Stage 5.1 Winston (required preload):**
1. This document (`quality-rubric.md`) — 12 confirmed gates with tier assignments, measurement protocols, structural architecture requirements
2. Carson's `quality-dimensions-draft.md` — for the 1-5 scoring protocols of R2, R3, R10, R11 (not revised here)
3. Stage 5.0.3 output (`benchmark-questions.md`) — for calibration anchors and OQ-5 weighting guidance

---

*Document produced by: Dr. Quinn (bmad-cis-problem-solving specialist)*  
*Next: Stage 5.0.3 — Advanced elicitation finalizes benchmark question set + scoring protocol*  
*Then: Stage 5.1 — Winston anchors MAC architecture on this hardened rubric*  
*Winston reads this document first — all 4 BLOCKERs are resolved here; all 3 TRIZ architectural requirements are binding design constraints*
