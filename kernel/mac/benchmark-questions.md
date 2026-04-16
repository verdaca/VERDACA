# MAC Benchmark Question Set + Scoring Protocol

**Stage:** Praxis 5.0.3 — Elicitation Round 3  
**Methods:** Comparative Analysis Matrix → Architecture Decision Records → Thesis Defense Simulation  
**Date:** 2026-04-14  
**Status:** FINAL — input to Stage 5.1 (Winston MAC architect) and Stage 5.6 (pre-sales checkpoint)

---

## Section 1: Comparative Analysis Matrix — Question Selection

### Candidate Pool (18 questions scored)

| # | Question Summary | CR | GC | MD | AS | TD | Total | Selected |
|---|---|---|---|---|---|---|---|---|
| C1 | Europe expansion timing and risks | 3 | 3 | 2 | 3 | 3 | **14** | ✓ |
| C2 | Per-seat → usage-based pricing transition | 3 | 3 | 3 | 3 | 3 | **15** | ✓ |
| C3 | Competitive response to aggressive pricing | 3 | 3 | 3 | 3 | 2 | **14** | ✓ |
| C4 | Raise now vs. extend runway to wait | 3 | 3 | 3 | 3 | 3 | **15** | ✓ |
| C5 | Customer concentration / custom integration | 3 | 2 | 2 | 3 | 1 | **11** | — |
| C6 | Acquire competitor vs. build capability | 3 | 3 | 3 | 3 | 3 | **15** | ✓ |
| C7 | NPS high but annual retention declining | 3 | 2 | 2 | 3 | 3 | **13** | ✓ |
| C8 | Strategic partnership with exclusivity constraint | 3 | 3 | 3 | 3 | 3 | **15** | ✓ |
| C9 | Open-source core engine strategy | 2 | 3 | 3 | 2 | 3 | **13** | — |
| C10 | Build defensibility around cost-savings capability | 3 | 3 | 3 | 3 | 3 | **15** | ✓ |
| C11 | Co-founder strategic disagreement | 2 | 2 | 2 | 2 | 2 | **10** | — |
| C12 | Enterprise vs. SMB GTM pivot | 3 | 3 | 3 | 3 | 2 | **14** | ✓ |
| C13 | Core product commoditized by platform | 3 | 3 | 3 | 3 | 3 | **15** | ✓ |
| C14 | Investor metric vs. north star metric | 2 | 2 | 2 | 2 | 2 | **10** | — |
| C15 | Senior hire with culture fit risk | 2 | 2 | 1 | 2 | 1 | **8** | — |
| C16 | Headcount reduction 18% | 2 | 2 | 1 | 2 | 2 | **9** | — |
| C17 | AI infrastructure moat vs. cloud giants | 3 | 3 | 3 | 3 | 1 | **13** | — |
| C18 | Vertical expansion timing | 3 | 3 | 3 | 3 | 3 | **15** | — |

**Criteria:** CR = Customer Realism, GC = Gate Coverage, MD = MAC Differentiability, AS = Answer Scorability, TD = Type Diversity (1–3 each)

**Selection rationale for final 10:** C2, C4, C6, C8, C10, C13 scored 15 each. C1, C3, C12 scored 14. C7 scored 13 (selected for unique diagnostic question type — NPS/retention divergence has no analog in the other 9). C17 excluded despite 13 (C13 already covers platform commoditization; C17 would duplicate type diversity with C13 for AI-specific context). C18 excluded (scores 15 but C1 already covers market expansion; C18 is too similar in question structure to justify the type-diversity slot given C7's unique diagnostic value). C9 excluded — answer scorability is lower without tech industry context assumptions.

**10 question types covered:** Pricing architecture, Capital strategy, Make-vs-buy, Strategic alliance with constraints, Market expansion, Competitive response, Moat building, Platform threat response, GTM model, Diagnostic (diverging metrics).

---

## Section 2: The 10 Benchmark Questions

### Q1 — Pricing Strategy Transition

**Customer context:** SaaS founder, Series B, 200 customers, currently on per-seat pricing. Usage has grown faster than seat count. CFO is modelling the impact of switching. Board wants decision in 6 weeks.

**Question:** Our SaaS product is priced per seat and we're growing users-per-seat much faster than new seats. Usage-based pricing is becoming the market norm in our category. Should we transition, and if so, how do we manage the MRR impact during the transition?

**Why in set:** Exercises R11 (multiple scenarios with very different revenue trajectories), R4 (strong steelman for staying per-seat), R1 (revenue projections are inferences, not facts), R8 (requires a specific staged transition plan, not just "yes switch"). MAC differentiability: the financial modeling perspective, the customer success perspective, and the sales perspective will meaningfully disagree — information asymmetry produces genuine dissent.

**Gold Standard Required Elements:**
- `[FINDINGS]`: Current revenue at risk under both models (quantified ranges, not assertions); customer segmentation by usage intensity; competitive pricing benchmarks; transition risk categories specific to this company's stage and customer base
- `[STEELMAN]`: The case for staying per-seat — predictable revenue, current customers signed at per-seat, risk of cannibalizing high-value seats
- `[DISSENT]`: CFO / finance perspective likely differs from product / growth perspective; both must be represented
- `[SCENARIOS]`: At minimum: (a) immediate full switch, (b) hybrid period + migration, (c) stay per-seat with usage tier overlay — differentiated revenue implications per scenario
- `[RECOMMENDATIONS]`: Specific transition path with timeline milestones, not just "consider hybrid approach"

**Gate-specific indicators:**
- R11 (4/5): Scenarios have genuinely different revenue implications; trigger conditions specified (e.g., "switch to hybrid if usage/seat ratio exceeds 3.5× within next 2 quarters")
- R4 (4/5): Steelman for per-seat includes the strongest revenue certainty argument, not just "some customers prefer predictability"
- R7 (4/5): Revenue model claims trace to stated assumptions about cohort behavior, not just stated as facts

**What single-agent typically misses:** The transition sequencing risk — new vs. existing customers on different models creates sales complexity and legal risk with existing contracts. Single agents jump to "switch" or "don't switch" without modeling the migration period.

---

### Q2 — Capital Strategy Under Uncertainty

**Customer context:** Series B founder, 16 months runway, SaaS metrics are strong but growth has slowed. VCs are offering a flat round at current valuation. Team wants to wait for better market conditions.

**Question:** We have 16 months of runway with slowing growth. We can raise a bridge now at a flat round, or cut burn by 15% to extend to 24 months and wait for Series C market conditions to improve. What's the right decision and what factors should drive it?

**Why in set:** Exercises R3 (invalidation conditions — what market signals would change the recommendation), R13's concerns (external data about market conditions requires labeled inference), R11 (scenario analysis is the core of the answer), R4 (waiting has a strong steelman). MAC differentiability: finance, ops, and growth perspectives will meaningfully disagree on risk tolerance.

**Gold Standard Required Elements:**
- `[FINDINGS]`: Bridge vs. extend analysis with explicit assumptions about market recovery timing; current burn rate and cut feasibility; runway sensitivity table; what "Series C market conditions improving" means operationally (what signal, what timeline)
- `[STEELMAN]`: The case for raising now — dilution is known vs. unknown; keeping growth team intact; optionality preserved
- `[DISSENT]`: Growth team vs. finance team perspectives on burn cut impact
- `[SCENARIOS]`: (a) raise bridge now, (b) cut burn 15% + wait 8 months, (c) cut burn 20% + wait 12+ months — with differentiated outcome probabilities
- `[RECOMMENDATIONS]`: Specific decision rule: "Take bridge if [condition X]; cut burn if [condition Y]" — not "it depends"

**Gate-specific indicators:**
- R3 (4/5): At least two specific, monitorable invalidation conditions for the recommendation (e.g., "recommendation changes if Series C market shows >3 closings at pre-flat valuations in the next 90 days")
- R1 (4/5): Revenue trajectory claims labeled as inferences; market recovery timeline explicitly flagged as assumption
- R8 (4/5): Recommendation includes a conditional: if forced to decide today with current information, specific path named

**What single-agent typically misses:** The team retention risk during an extended lean period — single agents model financial runway without modeling the probability that key hires leave if growth slowdowns extend.

---

### Q3 — Acquire vs. Build Decision

**Customer context:** Mid-market SaaS COO, technology company, Series C. Identified a smaller competitor with complementary technology ($4M ARR, asking $12M). Alternative: build the capability in-house in 9–12 months.

**Question:** We can acquire a competitor with the capability we need for $12M, or build it ourselves over 9–12 months. How do we structure this decision and what factors matter most?

**Why in set:** Classic strategic decision with multiple legitimate competing perspectives. Exercises R4 (strong arguments exist on both sides), R11 (scenarios including acquisition success, acquisition failure, build success, build delay), R7 (M&A decisions require traceable financial logic). MAC differentiability: finance, engineering, product, and customer success will all assess this differently.

**Gold Standard Required Elements:**
- `[FINDINGS]`: Build cost (9–12 months of engineering time at loaded cost) vs. acquisition cost including integration; capability gap specificity (what exactly does the acquired company have that we don't?); time-to-market differential; integration risk assessment specific to this company's architecture
- `[STEELMAN]`: The case against acquisition — integration typically takes 12–18 months, destroying the time-to-market advantage; acquired team may leave; technology debt may be worse than starting fresh
- `[DISSENT]`: Engineering team's perspective (build) vs. product/commercial team's perspective (buy) vs. finance team's perspective (NPV)
- `[SCENARIOS]`: (a) acquire + fast integration, (b) acquire + slow integration, (c) build on time, (d) build delayed — differentiated timelines and cost projections
- `[RECOMMENDATIONS]`: Specific recommendation with stated conditions, not "run a detailed due diligence"

**Gate-specific indicators:**
- R4 (4/5): The steelman against acquisition addresses the strongest real objection (integration failure rate), not just "culture fit risk"
- R12 (4/5): No internal contradictions — if findings establish integration takes 12–18 months, recommendations should not claim "time-to-market advantage"

**What single-agent typically misses:** The "acqui-hire" scenario — the primary value may be the team, not the technology, and that changes the entire acquisition rationale and risk profile.

---

### Q4 — Strategic Partnership With Exclusivity

**Customer context:** Series B founder, B2B SaaS, strong product but limited distribution. Large tech company (50k business customers) offers distribution partnership with a 3-year exclusivity clause in their vertical.

**Question:** A large tech company wants to distribute our product to their 50,000 business customers. The constraint: 3-year exclusivity in their vertical, preventing us from selling to their competitors. Should we take this deal, and what are the real strategic risks?

**Why in set:** High-stakes irreversible decision with a 3-year commitment horizon. Exercises all core gates: R11 (what if the distribution partner underperforms, pivots, or is acquired?), R3 (what would make us regret this?), R4 (the steelman for declining is very strong — optionality destroyed), R10 (analysis must explicitly state what was NOT analyzed — e.g., partner's M&A risk). MAC differentiability: commercial, legal, and product strategy perspectives will produce genuinely different risk assessments.

**Gold Standard Required Elements:**
- `[FINDINGS]`: Exclusivity scope analysis — how many potential customers are locked out? Revenue ceiling estimate for locked-out market. Partner's vertical penetration track record. Optionality destroyed vs. TAM unlocked. Specific risks: partner gets acquired, deprioritizes our product, pivots vertical
- `[STEELMAN]`: The case for declining — 3-year lock-in at growth stage destroys Series C optionality; if partner underperforms, we've both ceded market and failed to build own distribution muscle
- `[DISSENT]`: Sales team (desperate for distribution) vs. strategy (concerned about optionality) must both be represented
- `[SCENARIOS]`: (a) partnership exceeds expectations, (b) partnership underperforms but locked in, (c) partner acquired by competitor during exclusivity window
- `[RECOMMENDATIONS]`: Specific negotiation position — if we recommend accepting, what terms must change? If declining, what alternative distribution paths?

**Gate-specific indicators:**
- R10 (4/5): Explicitly names what was not analyzed — partner's acquisition risk, partner's financial stability, specific exclusivity clause legal interpretation
- R3 (4/5): Clear invalidation conditions — "recommendation changes if partner cannot demonstrate >30% vertical penetration within first 12 months"
- R5 (4/5): Sales team vs. strategy team dissent given equal representation, not just acknowledged

**What single-agent typically misses:** The negotiation angle — single agents analyze the deal as binary (accept/decline) rather than as a negotiation where exclusivity terms, performance guarantees, and exit clauses can be modified.

---

### Q5 — Moat Building Before Commoditization

**Customer context:** AI infrastructure startup, seed to Series A transition. Core capability: 30–65% token cost reduction across LLM workloads. Token pricing is deflating industry-wide.

**Question:** Our core value proposition is 30–65% cost savings on LLM tokens. Token prices are dropping industry-wide by ~30% per year. How do we build a defensible business before our cost savings become irrelevant?

**Why in set:** Directly relevant to Praxis's own strategic context (from Tokonomics). Exercises R11 (scenarios depend heavily on token deflation rate assumptions), R1 (cost savings percentages are measurements, not projections — what do future projections assume?), R4 (steelman that this business is undefendable). MAC differentiability: product, commercial, and technical strategy will each see a very different moat-building path.

**Gold Standard Required Elements:**
- `[FINDINGS]`: Token deflation rate historical trend (labeled as inference from public pricing data); current defensibility of core compression algorithms; moat-building options ranked by switching costs (workflow integration > algorithm optimization > data flywheel > brand); time horizon for each
- `[STEELMAN]`: The case that no moat is buildable in this space before commoditization — compression algorithms are open-source, cloud giants have scale advantages, token price deflation will outrun any technical efficiency gains
- `[DISSENT]`: Engineering perspective (technical moat) vs. commercial perspective (workflow lock-in) vs. investor perspective (urgency vs. defensibility trade-off)
- `[SCENARIOS]`: (a) deflation accelerates (>40%/yr) — what's viable?, (b) deflation stabilizes (10–20%/yr) — what's viable?, (c) token prices rebound — which moat investments look different?
- `[RECOMMENDATIONS]`: Specific moat-building sequence with explicit prioritization — not "pursue multiple moats"

**Gate-specific indicators:**
- R1 (4/5): Deflation rate projections explicitly labeled as inference from limited public data; moat timeline estimates labeled as assumptions
- R11 (4/5): Three scenarios have meaningfully different strategic implications — not just different growth rates

**What single-agent typically misses:** The second-order question — if the cost-savings value proposition is commoditized, what customer PROBLEM remains unsolved? The pivot is not from compression to more compression, but from cost savings to a new value delivery.

---

### Q6 — Competitive Response to Aggressive Pricing

**Customer context:** Series B SaaS, 18-month market leader. New well-funded competitor entered at 40% lower price point. Two enterprise customers have asked for re-negotiation.

**Question:** A well-funded competitor entered our market at 40% lower pricing. Two of our enterprise accounts have asked for pricing discussions. How do we respond strategically without triggering a race to the bottom?

**Why in set:** High urgency, multiple legitimate strategic options with strong disagreements between commercial and product teams. Exercises R11 (scenarios: price match, ignore, differentiate), R4 (steelman for price matching — not matching accelerates churn), R5 (sales vs. product vs. finance will have very different positions). MAC differentiability: information asymmetry between these functional perspectives is the core of the strategic question.

**Gold Standard Required Elements:**
- `[FINDINGS]`: Competitive pricing differential analysis (40% lower — is this sustainable? What's their unit economics?); retention risk assessment for at-risk accounts (2 asking, how many at risk silently?); differentiation clarity — what do customers actually value that justifies the premium?
- `[STEELMAN]`: The case for selective price matching for at-risk accounts — losing a reference customer sends a worse signal than a 20% price concession
- `[DISSENT]`: Sales team (match price to retain) vs. product team (defend differentiation) vs. finance team (margin protection)
- `[SCENARIOS]`: (a) defend premium + risk churn, (b) selective matching for existing at-risk only, (c) broad 20% reduction to reset category expectations
- `[RECOMMENDATIONS]`: Immediate action (what to say to the 2 customers asking NOW) + medium-term positioning (within 90 days)

**Gate-specific indicators:**
- R8 (4/5): Recommendation includes both an immediate response (this week) and a strategic positioning response (next quarter) — not just general strategic direction
- R7 (4/5): The logic chain from "competitor is unsustainably priced" to "therefore don't match" is explicitly traced

**What single-agent typically misses:** The signaling value of the response — how the response to the 2 accounts will be perceived by the other 50% of the account base who are watching but not asking yet.

---

### Q7 — Market Expansion Timing

**Customer context:** US-first SaaS company, $8M ARR, strong Series A, investor board pushing European expansion. Product-market fit strong in North America. 2 EU inbound leads in the last 6 months.

**Question:** We have strong US market fit and investors are pushing us to expand to Europe. We have 2 EU inbound leads but no European presence. When is the right time and what are the real risks we're not seeing?

**Why in set:** Classic expansion timing question with strong legitimate arguments on both sides and significant risk specificity requirements (EU risks are entity-specific, not generic). Exercises R7 (what is the actual argument for European readiness?), R10 (what risks are we not seeing — scope acknowledgment), R1 (the 2 EU inbound leads are weak evidence labeled as strong), R4 (steelman for waiting). MAC differentiability: investor board, commercial team, and engineering team will have dramatically different risk tolerances.

**Gold Standard Required Elements:**
- `[FINDINGS]`: Entity-specific EU risks (not "regulatory compliance" — specific GDPR data residency requirements for THIS product's data model; EU VAT for THIS company's billing structure; hiring market for THIS tech stack in EU markets); readiness checklist against known expansion failure modes; what the 2 inbound leads actually signal (demand pull vs. noise)
- `[STEELMAN]`: The case for waiting — US market still has 10× the TAM being captured; EU expansion before US dominance creates organizational split focus that slows both
- `[DISSENT]`: Investor board (expansion signals growth) vs. operator (execution risk is real, team is stretched)
- `[SCENARIOS]`: (a) expand now with dedicated EU team, (b) expand in 12 months after US consolidation, (c) service EU inbound remotely without local presence
- `[RECOMMENDATIONS]`: Decision criteria — what specific US metrics and organizational conditions must be met before EU expansion is the right move?

**Gate-specific indicators:**
- R1 (4/5): EU risks are entity-specific (named with reference to actual product/team attributes), not category-generic "European expansion risks"
- R10 (4/5): Explicitly names what was NOT analyzed — local labor law in specific target markets, specific EU VAT treatment for this billing model, specific GDPR implications for this data architecture

**What single-agent typically misses:** The organizational readiness dimension — whether the current management team has the bandwidth and experience to run a dual-geography operation, and what the cost of split attention is.

---

### Q8 — Platform Threat Response

**Customer context:** AI middleware/tooling startup, $5M ARR, growing 120% YoY. Foundation model providers (OpenAI, Anthropic, Google) are adding features that overlap with core capabilities.

**Question:** Our core product is being gradually replicated by foundation model providers moving up the stack. How do we identify what defensible layer to build next before we're commoditized?

**Why in set:** Existential strategic question that requires genuine multi-perspective analysis. Exercises R4 (steelman that no defensible layer exists — some businesses just get commoditized), R11 (scenarios depend on platform providers' roadmap — which is unknowable), R3 (what would confirm we're choosing the right layer?). MAC differentiability: technical, commercial, and competitive strategy perspectives will identify completely different "next layers."

**Gold Standard Required Elements:**
- `[FINDINGS]`: Platform provider capability expansion timeline (labeled as inference from public signals, not forecast); current product's "last-mile" advantages that platforms won't replicate (workflow specificity, customer data, integration depth); customer switching cost analysis — what would customers need to rebuild if they switched to platform-native?
- `[STEELMAN]`: The case that there is no defensible next layer — once a foundation model provider decides to compete directly, resource asymmetry makes resistance futile; the right answer is to sell the company before commoditization completes
- `[DISSENT]`: Engineering team (technical moat is possible) vs. commercial team (relationship moat is more durable) vs. investor (exit optimization)
- `[SCENARIOS]`: (a) platforms commoditize core in 12 months — what's viable?, (b) commoditization takes 3+ years — what's the right investment?, (c) platforms decide not to compete in this specific niche
- `[RECOMMENDATIONS]`: Specific next-layer candidates ranked by defensive durability and time-to-build, not just "build more integrations"

**Gate-specific indicators:**
- R4 (4/5): The "sell now" steelman receives genuine treatment — it is the strongest opposing position, not a dismissable option
- R11 (4/5): Each scenario has meaningfully different implications for the next layer recommendation

**What single-agent typically misses:** The "stay small on purpose" option — deliberately limiting growth to stay below the threshold that makes direct competition worth the platform provider's effort.

---

### Q9 — GTM Model Selection

**Customer context:** B2B SaaS, 7-9 month enterprise sales cycle, $50K ACV, 14 months runway. Current bookings are 2× slower than needed to hit Series B metrics.

**Question:** Our enterprise sales cycle is 7–9 months and we're burning cash. Should we pivot to an SMB self-serve model to accelerate bookings, or stay focused on enterprise and cut costs elsewhere?

**Why in set:** GTM architecture decision with irreversible elements and strong competing perspectives. Exercises R11 (SMB pivot takes 6-12 months to validate — scenarios must span both fast and slow validation timelines), R5 (commercial team vs. engineering team vs. current customers will have strong disagreements), R3 (what would falsify the SMB hypothesis before 12 months of burn?). MAC differentiability: the product, sales, and finance perspectives will generate genuine conflict.

**Gold Standard Required Elements:**
- `[FINDINGS]`: Current sales pipeline analysis — is 7-9 months deal-specific or market-structural? SMB pivot cost and timeline (product changes, pricing model, self-serve infrastructure); what existing enterprise customers are at risk if product focus shifts; runway math under both scenarios
- `[STEELMAN]`: The case against SMB pivot — existing enterprise customers will feel abandoned; SMB product requires 6-12 months of engineering before generating meaningful revenue; the company will burn through cash building a new GTM muscle while the existing one atrophies
- `[DISSENT]`: Enterprise sales team (we just need more time and pipeline) vs. product team (SMB pivot requires different product architecture) vs. finance (survival math is non-negotiable)
- `[SCENARIOS]`: (a) full SMB pivot in 3 months, (b) hybrid with SMB self-serve for new segment + maintain enterprise for existing, (c) enterprise acceleration (more sales hires, more pipeline)
- `[RECOMMENDATIONS]`: Decision criteria with specific runway math — what SMB ramp rate within what timeline justifies the pivot investment?

**Gate-specific indicators:**
- R3 (4/5): Clear falsification criteria for the SMB hypothesis — "if self-serve sign-up rate doesn't reach X within Y months, return to enterprise focus"
- R8 (4/5): Immediate action specified — what to do this week (which option to pursue) vs. what to plan for next 90 days

**What single-agent typically misses:** The "hybrid disaster" trap — companies that try to serve both enterprise and SMB simultaneously often do neither well; the analysis should explicitly address whether hybrid is a real option or a wishful-thinking compromise.

---

### Q10 — Diagnostic (Diverging Metrics)

**Customer context:** B2B SaaS, 4 years old, strong NPS (67), enterprise segment. Annual retention dropped from 91% to 84% over 12 months. No obvious cause — support tickets flat, NPS rising, product engagement stable.

**Question:** Our NPS is 67 and rising, but annual retention dropped from 91% to 84% over 12 months. We don't know why these signals are diverging. How do we diagnose what's actually happening and what do we do about it?

**Why in set:** Diagnostic question — structurally different from all other 9 questions. Requires genuine analytical rigor: generating hypotheses, designing investigation protocol, epistemic calibration (must label hypotheses as hypotheses). Exercises R12 (an analysis that accepts the NPS data at face value and contradicts it with retention data has an internal consistency challenge), R3 (each hypothesis has falsification criteria), R7 (diagnostic reasoning chain is testable). MAC differentiability: customer success, product, and finance will each generate very different hypotheses.

**Gold Standard Required Elements:**
- `[FINDINGS]`: Taxonomy of possible hypotheses (labeled as hypotheses, not conclusions): cohort effects, product-market fit drift, competitive displacement, champion turnover, pricing sensitivity, expansion vs. contraction customers. Data collection protocol for each hypothesis — what specific analysis would confirm or rule it out
- `[STEELMAN]`: The case that NPS is the lagging indicator and retention is the leading indicator of a fundamental product-market fit problem, not a tactical retention issue
- `[DISSENT]`: Customer success team (it's execution/relationship issues) vs. product team (it's product-market fit drift) must both be represented with evidence requirements for each
- `[SCENARIOS]`: The scenarios ARE the hypotheses — each one implies a different intervention; the analysis must distinguish "if H1 is true, do X" from "if H2 is true, do Y"
- `[RECOMMENDATIONS]`: Investigation protocol with timeline and decision points — not "do more analysis" but "run these 3 specific analyses by [date] and make a decision based on results"

**Gate-specific indicators:**
- R1 (4/5): All hypotheses explicitly labeled as hypotheses; no hypothesis stated as a conclusion; confidence levels assigned
- R12 (4/5): Internal consistency check — the analysis acknowledges the NPS/retention divergence directly and does not accept both metrics at face value without reconciling them
- R7 (4/5): The logic chain "NPS is high AND retention fell → the most likely explanation is X" is traceable and challenged by the steelman

**What single-agent typically misses:** The composition effect — aggregate retention may be falling because the distribution of customer types is shifting (more high-churn SMB added recently), not because existing customers are churning more.

---

## Section 3: Architecture Decision Records

### ADR-1: Blind vs. Open Scoring

**Context:** The LLM-judge scoring outputs needs to assign scores on R1–R12. If the judge knows which output is MAC vs. single-agent, it may assign higher scores to MAC outputs based on expectation rather than quality. Blind scoring prevents this. However, Req-C's R5 co-evaluation requires knowing whether dissent corresponds to positions in the task context — which requires task context awareness.

**Options:**
- A: Fully blind (judge sees only the output, no system identification)
- B: Fully open (judge knows which system produced each output)
- C: Hybrid — blind for R1–R4, R6–R12; R5 co-evaluation runs as a second pass with task context

**Decision: Option C — Hybrid blind/open**

**Rationale:** Fully blind scoring is the scientific ideal; fully open scoring introduces confirmation bias. The R5 co-evaluation exception is narrow and necessary — without knowing the task context, the judge cannot detect manufactured dissent. Option C provides scientific validity for 11 gates while preserving R5 integrity.

**Consequences:** Scoring protocol requires two passes. Pass 1 (blind): assign random IDs to outputs; score R1–R4, R6–R12 without system identification. Pass 2 (R5 only): provide task context to judge; apply Req-C manufactured-dissent co-evaluation. Final R5 score is from Pass 2 only.

---

### ADR-2: Gold Standard Answer Format

**Context:** Gold standard answers serve two purposes: (1) anchor LLM-judge calibration (Req-D requires score-2 and score-4 examples per gate); (2) seed the initial Memory corpus (OQ-6). The format choice affects both purposes.

**Options:**
- A: Full model answer (complete analysis document in correct output structure)
- B: Scoring rubric checklist (list of required structural elements, no example content)
- C: Hybrid — required elements checklist (structural) + brief reference examples (2–3 sentences) for the 3 most gate-relevant elements

**Decision: Option C — Hybrid**

**Rationale:** Full model answers (Option A) are costly to produce and risk over-anchoring LLM-judges to one specific formulation — judges may score outputs low if they don't match the specific phrasing of the gold standard, regardless of quality. Pure checklists (Option B) are too abstract for calibration — without examples, judges don't know what "differentiated scenario implications" looks like. Option C provides structural guidance with just enough reference content to anchor the scale without over-specifying it.

**Consequences:** Each gold standard is ~500–800 words: checklist (structural requirements) + 3 reference examples (illustrating what score-4 looks like on the 3 gates most relevant to that question). This document (Sections 2 and 5 combined) constitutes the gold standard corpus.

---

### ADR-3: A4 Validation Loop Design

**Context:** Dr. Quinn's A4 assumption busting produced a REVISE verdict: rubric scores must be validated against human-judged decision quality, not just assumed to correlate. The benchmark evaluation must include this validation. But human expert evaluation for all 10 questions at every MAC version is impractical.

**Options:**
- A: Expert panel evaluates all 10 questions independently — high validity, high cost
- B: Single evaluator (Andrey) reviews 3 randomly selected questions with a simplified 5-question decision-quality checklist — practical, limited statistical power
- C: Retrospective validation using historical decisions from Tokonomics rounds — compares rubric scores on existing analyzed outputs against known decision-quality outcomes
- D: Defer entirely to Stage 6 or 7

**Decision: Option B for Stage 5.6; Option C as a supplementary validation over time**

**Rationale:** Option A is too expensive for the pre-sales checkpoint. Option D makes the +15–25% claim unvalidated. Option B is the minimum viable validation — it produces a correlation coefficient between automated rubric scores and one human evaluator's quality judgment for 3 questions. This is not a rigorous statistical test, but it is sufficient to (a) catch systematic rubric failures and (b) provide an honest characterization of the benchmark's validation status. Option C is valuable long-term but requires historical decisions with known outcomes — a resource that doesn't yet exist.

**Simplified decision-quality checklist for Andrey (5 questions, rated 1–5):**
1. Would you, as the decision-maker, trust this analysis enough to act on it?
2. Does this analysis surface risks or perspectives you hadn't considered?
3. Does this analysis give you a clear sense of what to do next?
4. Does this analysis feel intellectually honest — neither over-confident nor evasively hedged?
5. Would you share this analysis with your board or investors to support this decision?

**Correlation protocol:** Run automated scoring and Andrey's 5-question assessment on the same 3 outputs (one MAC, one single-agent baseline, one single-agent enhanced). Compute Spearman correlation between composite rubric scores and Andrey's assessment total. A correlation ≥ 0.6 provides provisional validation that rubric scores track human-judged quality.

**Consequences:** The +15–25% claim at Stage 5.6 must be characterized as: "Praxis MAC scored X% higher on the automated 12-gate rubric, with provisional human validation on 3 of 10 questions showing Y correlation between rubric scores and human quality judgment."

---

## Section 4: Thesis Defense Responses

### Persona 1 — The Statistician

*"N=10 is too small to prove +15–25% at any meaningful confidence interval. What's your power analysis? How do you avoid the claim being statistical noise?"*

**Response:** The Statistician is right that N=10 cannot establish statistical significance for a +15–25% improvement claim at p<0.05. We accept this and change the claim framing. The 5.6 benchmark is not a hypothesis test — it is a **directional demonstration**. The claim is: "In our benchmark evaluation of 10 diverse strategic questions, MAC scored an average of X% higher than single-agent baseline on the 12-gate quality rubric." No p-value. No confidence interval. This is sales evidence, not academic publication.

**Design change:** The 5.6 pre-sales report must include a "Benchmark Limitations" section that explicitly states: (1) N=10 is insufficient for statistical hypothesis testing; (2) the improvement claim is directional and based on a specific benchmark set; (3) expansion to a larger question set is planned. This honest framing is more defensible than overclaiming statistical validity.

**What would invalidate the claim:** If MAC scores higher than single-agent on fewer than 7 of 10 questions, or if the average improvement is below 10%, the differentiation claim requires revision. These are stated as explicit invalidation conditions per R3.

---

### Persona 2 — The Practitioner

*"These questions are too abstract. A real COO would never ask these. Your benchmark is cherry-picked to make multi-agent look good."*

**Response:** The 10 questions were selected using a 5-criteria matrix before knowing which questions would favor MAC or single-agent. The selection criteria explicitly included "Customer Realism" (scored 3/3 for all 10 selected questions) — each question is drawn from real strategic advisory contexts, including Tokonomics multi-agent sessions where these exact question types were deliberated. The cherry-picking accusation requires showing that excluded questions would have shown no MAC advantage; we address this by publishing the full 18-candidate matrix including scoring and exclusion rationale.

**Design change:** Full result disclosure is required. If MAC scores lower than single-agent on any of the 10 questions, those results are published. We do not cherry-pick the 8 where MAC wins and hide the 2 where it doesn't. The 5.6 report shows all 10 individual question scores, not just the aggregate. This preempts cherry-picking accusations.

---

### Persona 3 — The Adversary

*"I can game your benchmark. I'll prompt a single agent to steelman its own output and score just as high as MAC. Your gates don't distinguish MAC from single-agent-with-chain-of-thought."*

**Response:** Partially valid and worth testing directly. The benchmark includes **two baseline conditions**, not one:
1. **Vanilla single-agent:** Standard analytical prompt with the question
2. **Enhanced single-agent:** Same prompt with explicit chain-of-thought + steelman instruction + dissent instruction ("argue the strongest opposing case; present minority views explicitly")

If MAC beats vanilla but not enhanced single-agent, the claim becomes "MAC is equivalent to an expertly prompted single-agent, without requiring expert prompting." This is still a useful product claim (democratizing expert prompt engineering).

If MAC beats enhanced single-agent, the claim is stronger: "Even when single-agent is explicitly prompted to steelman and present dissent, MAC produces higher-quality outputs — because information asymmetry generates genuinely different perspectives, not just simulated ones."

**Design change:** The 5.6 evaluation runs THREE output sets per question (vanilla baseline, enhanced baseline, MAC) and reports all three comparative scores. The headline is framed for whichever result is most honest.

**Unresolvable objection acknowledgment:** The Adversary is correct that R4 (Steelman Completeness) and R5 (Dissent Preservation) are the gates most susceptible to gaming by enhanced single-agent prompting. We acknowledge this explicitly: these two gates measure PRESENCE and QUALITY of steelmans and dissent, which a well-prompted single agent can generate. The MAC's structural advantage on these gates comes from information asymmetry generating genuinely independent analysis — something that can't be fully measured by presence/quality scoring alone. This is a known limitation of the rubric.

---

## Section 5: Gate Calibration Anchors (R1–R12)

For each gate: one score-2 example and one score-4 example, drawn from the benchmark question contexts. These are the calibration anchors for the LLM-judge prompt per Req-D.

**R1 — Epistemic Calibration**
- Score 2: "European expansion is the right move for your company given your strong product-market fit and the growing EU AI services market projected to reach €40B by 2030." (inference stated as fact; market projection stated without basis; "right move" asserted without labeling as conclusion)
- Score 4: "Based on the two EU inbound leads (weak demand signal — inference, not validation) and the EU AI services market projections (third-party projection with ±30% uncertainty range), our assessment — which we treat as a reasoned recommendation, not a forecast — is that expansion readiness is not yet confirmed."

**R2 — Question Fidelity**
- Score 2: "Regarding your question about Europe expansion, here is a comprehensive analysis of European market dynamics, GDPR considerations, and competitive landscape..." (answers a general European expansion question, not THIS company's timing decision)
- Score 4: "You asked when to expand to Europe. The more precise question is: what conditions define readiness for this company? We've reframed accordingly and will answer both."

**R3 — Falsifiability**
- Score 2: "This recommendation should be revisited if market conditions change significantly." (vague; unmonitorable; no specific signal identified)
- Score 4: "This recommendation to delay EU expansion changes if: (a) EU inbound leads exceed 5 qualified enterprise conversations within 60 days (demand pull validated), OR (b) a direct competitor announces EU presence with >3 customer wins in this category."

**R4 — Steelman Completeness**
- Score 2: "Some might argue that staying per-seat is more predictable, but usage-based pricing is the clear market direction and predictability concerns are outweighed by growth opportunity." (the steelman is dismissed in the same sentence it's raised)
- Score 4: "The strongest case for staying per-seat: existing customers signed under per-seat contracts have a legitimate expectation of pricing model stability; switching mid-contract risks triggering renegotiation across the entire base; the revenue predictability of per-seat enables better headcount planning and investor communication. This is a real constraint that must be addressed in any transition plan, not dismissed."

**R5 — Dissent Preservation**
- Score 2: "Some stakeholders may prefer the acquisition option due to speed-to-market concerns." (no argument given; no attribution; one sentence)
- Score 4: "The engineering team's position — stated in the product review — is that the acquisition target's codebase carries significant technical debt that will require 6–12 months of refactoring before integration, eliminating the time-to-market advantage entirely. This is a substantive constraint: the acquisition thesis assumes 3-month integration, and engineering believes this is structurally impossible given what they've seen in due diligence."

**R6 — Decision Relevance Density**
- Score 2: "The European SaaS market represents a significant opportunity. Key players include [list of 12 companies]. Historical European expansion data shows [3 paragraphs of market statistics]. [The actual recommendation appears in paragraph 11.]"
- Score 4: "Key Decision: Delay EU expansion until the US conversion rate from inbound exceeds 25% (currently 14%). This is the leading indicator of product-market fit strength sufficient to support parallel expansion. Three supporting factors follow."

**R7 — Reasoning Traceability**
- Score 2: "Given the market dynamics, the hybrid GTM approach is clearly the best path forward." (no reasoning chain; conclusion asserted)
- Score 4: "The hybrid GTM approach is recommended because: (1) existing enterprise customers generate 87% of ARR and cannot be abandoned without triggering immediate churn risk; (2) SMB self-serve requires minimum 6 months of product changes before generating meaningful ARR; (3) therefore, a phase transition is structurally required — pure pivot would create a 6-month revenue gap that current runway cannot absorb."

**R8 — Actionability Calibration**
- Score 2: "We recommend further analysis of the SMB market before committing to a pivot." (no conditional recommendation; pure epistemic cowardice)
- Score 4: "Given current information, pursue the hybrid approach: (a) this week — freeze new enterprise AE hiring; (b) within 30 days — complete SMB product requirements document; (c) within 90 days — launch SMB beta to 20 inbound prospects. Revisit if SMB conversion rate is below 15% at 90-day checkpoint."

**R9 — Evidence Impartiality**
- Score 2 (findings section): "Encouragingly, the EU market is showing strong demand signals, and our product's differentiation makes it ideally suited for European buyers. The competitive landscape, while present, is manageable..." (evaluative language tilts positive; evidence selection skews toward supporting the recommendation before it's made)
- Score 4 (findings section): "EU inbound leads: 2 qualified conversations in 6 months (base rate for this stage: unknown; insufficient to conclude demand pull). Competitive presence: 3 direct competitors with EU offices. GDPR compliance gap: 4 identified items requiring engineering work before launch (estimated 8–12 weeks). Expansion readiness: mixed evidence."

**R10 — Epistemic Scope Honesty**
- Score 2: "This analysis may not capture all relevant factors. We recommend ongoing monitoring of market conditions." (boilerplate; no specific exclusion; no specific blind spot)
- Score 4: "This analysis did not examine: (a) post-2023 EU regulatory precedents on AI data processing (relevant but beyond our regulatory expertise); (b) the specific VAT treatment for this company's billing structure in Germany and France (requires tax counsel). Our assessment of EU readiness is therefore conditional on these two factors receiving independent review."

**R11 — Scenario Coverage**
- Score 2: "Scenario A: market grows quickly — revenue reaches $5M. Scenario B: market grows slowly — revenue reaches $3M." (same recommendation implied; no differentiated decision implications; scenarios differ only in magnitude)
- Score 4: "Scenario A (token deflation >40%/yr): the cost-savings value proposition becomes irrelevant within 18 months; pivot to workflow integration moat immediately. Scenario B (deflation stabilizes 10–20%/yr): 36-month window to build data flywheel; invest in algorithm improvement AND integration depth. These scenarios imply different investment priorities and are monitored by tracking quarterly token pricing across major providers."

**R12 — Internal Consistency**
- Score 2: "[FINDINGS]: The acquisition target's technology will require 12–18 months of integration work. [RECOMMENDATIONS]: The acquisition provides a 6-month time-to-market advantage over the build option." (direct internal contradiction)
- Score 4: "[FINDINGS]: Integration timeline estimated at 12–18 months based on due diligence findings (codebase complexity, API architecture mismatch). [RECOMMENDATIONS]: The acquisition is recommended NOT for time-to-market advantage — findings show this is negligible — but for the team acquisition and IP rights to specific algorithms. The time-to-market framing should be removed from investor communications."

---

## Section 6: Scoring Protocol

### Step 1: Preparation (per question)

1. Load the benchmark question text and customer context
2. Prepare three prompts:
   - **Vanilla baseline prompt:** "You are a strategic advisor. A client asks: [question]. Provide your analysis."
   - **Enhanced baseline prompt:** "You are a strategic advisor. A client asks: [question]. In your analysis: (a) explicitly steelman the strongest opposing recommendation; (b) present any significant minority views from different stakeholder perspectives; (c) show your reasoning chain explicitly."
   - **MAC prompt:** Standard MAC task intake via Task Interpreter; no special instructions
3. Generate all three outputs independently (no cross-contamination)

### Step 2: Output Structuring

For all three outputs: if the output doesn't use the required section labels (`[FINDINGS]`, `[RECOMMENDATIONS]`, `[STEELMAN]`, `[DISSENT]`, `[SCENARIOS]`), apply a post-processing step to identify and label the closest structural analog. A structurally unlabeled output is not automatically scored low — the absence of labels is scored in R1 (lack of structured format signals calibration gap) but other gates evaluate the content in the most generous structural interpretation.

### Step 3: Pass 1 — Blind Scoring (R1–R4, R6–R12)

1. Assign random IDs to the three outputs (e.g., Output-Kappa, Output-Lambda, Output-Mu)
2. For each gate R1–R4 and R6–R12, run the LLM-judge with:
   - Gate definition from quality-rubric.md Section 6
   - Calibration anchors from Section 5 of this document (score-2 and score-4 examples)
   - Output section(s) specified per Req-B gate routing
3. Record scores on 1–5 scale for each (gate, output) pair
4. For R4: run two-step protocol per Req-F — judge generates independent steelman first, then compares

### Step 4: Pass 2 — R5 Scoring with Context

1. Provide judge with: (a) task context (customer situation and question), (b) all three outputs with their random IDs
2. Evaluate R5 for each output: is dissent present with content depth? Does it correspond to positions plausible given the task context?
3. Apply Req-C R5/R4 co-evaluation: if R5 ≥ 4 but dissent doesn't correspond to any plausible stakeholder position in the task context, cap R5 at 2

### Step 5: Composite Score Calculation

**Gate weights (OQ-5 recommendation — top-5 weighted):**

| Gate | Weight | Rationale |
|---|---|---|
| R1 Epistemic Calibration | 2× | Universal; MAC structural advantage |
| R2 Question Fidelity | 2× | Universal; MAC structural advantage |
| R4 Steelman Completeness | 2× | Primary MAC differentiation gate |
| R5 Dissent Preservation | 2× | Anti-conformity gate; MAC structural advantage |
| R7 Reasoning Traceability | 2× | Required for Cycle 3 verification |
| R3, R6, R8, R9, R10, R11, R12 | 1× each | Standard weight |

Total weight units: 5 gates × 2 + 7 gates × 1 = **17 weight units**

Composite score = Σ(gate_score × gate_weight) / (17 × 5) × 100 (expressed as 0–100%)

### Step 6: A4 Validation (3 selected questions)

1. Randomly select 3 questions from the 10
2. Andrey evaluates all three outputs (MAC, vanilla, enhanced baseline) for each selected question using the 5-question simplified checklist from ADR-3 (each rated 1–5; max 25 per output)
3. Compute Spearman correlation between automated composite scores and Andrey's simplified assessment totals across the 9 output × 3 question evaluations
4. Report correlation coefficient in the 5.6 pre-sales report alongside the primary quality scores

### Step 7: Reporting

Report all results in a standard table:

| Question | Vanilla Score | Enhanced Baseline Score | MAC Score | MAC vs. Vanilla % | MAC vs. Enhanced % |
|---|---|---|---|---|---|
| Q1–Q10 | | | | | |
| **Average** | | | | | |

Publish all 10 question scores. Identify any questions where MAC underperforms. Characterize improvement claim as directional, not statistically significant (Thesis Defense Persona 1 response).

---

## Section 7: OQ-5 — Gate Weighting Recommendation

**Decision: Top-5 weighted for Stage 5.6 first run; empirically validated after**

**Rationale:** The 5 critical gates (R1, R2, R4, R5, R7) are the MAC's structural advantage gates — the places where multi-agent deliberation with information asymmetry is designed to produce the largest improvement over single-agent. Equal weighting (1/12 per gate) would give equal importance to R6 (Decision Relevance Density) and R4 (Steelman Completeness) — but R4 is WHERE the MAC adds value, while R6 measures a structural property that both MAC and single-agent can satisfy with good prompting.

**Bootstrap paradox acknowledgment:** Using the first benchmark run to derive empirical weights is circular — the weights depend on the benchmark data, which depends on the weights. The top-5 weighted model uses external justification (architectural reasoning about where MAC adds value) rather than empirical derivation, which makes it more defensible for the first run.

**Update protocol:** After Stage 5.6 runs with top-5 weights, observe which gates show the largest variance between MAC and both baselines. If R4 and R5 show the largest differential (expected), the top-5 weighting is validated. If unexpected gates show the largest differential, revise weights for subsequent evaluations.

---

## Section 8: OQ-6 — Memory Bootstrap Plan

**How the 10 gold-standard answers seed the initial Memory corpus:**

For each benchmark question, the gold-standard required elements checklist (Section 2) plus the gate-specific indicators constitute a task outcome record. These 10 records are pre-loaded into Praxis Memory before the first real user task, structured as:

```
Task Signature: [question type] + [domain] + [key decision variables]
Approach: [analytical framework implied by gold standard structure]
Outcome: Gold-standard analysis (checklist + gate indicators)
Quality Score: Preset to 4.2/5.0 (representative of score-4 performance)
Reasoning Trace: Gate-specific indicators in this document
```

**10 task signatures for Memory pre-load:**

| # | Question | Task Signature | Domain |
|---|---|---|---|
| Q1 | Pricing transition | pricing-model-change + SaaS + revenue-model-migration | Revenue strategy |
| Q2 | Capital strategy | capital-allocation + runway + raise-vs-extend | Financing |
| Q3 | Build vs. buy | make-vs-buy + capability-gap + integration-risk | Strategic decision |
| Q4 | Partnership decision | strategic-alliance + exclusivity + optionality-cost | Partnership |
| Q5 | Moat building | defensibility + commoditization-threat + moat-building | Competitive strategy |
| Q6 | Competitive response | competitive-pricing + race-to-bottom + differentiation | Competitive response |
| Q7 | Market expansion | geographic-expansion + readiness + entity-specific-risk | Growth strategy |
| Q8 | Platform threat | platform-commoditization + next-layer + existential | Strategic repositioning |
| Q9 | GTM pivot | gtm-model + enterprise-vs-smb + runway-constraint | Go-to-market |
| Q10 | Diagnostic | diverging-metrics + hypothesis-generation + root-cause | Operational diagnosis |

**Bootstrap protocol:** Before MAC Cycle 1's first retrieval call, these 10 records are inserted into Memory with a metadata flag `source: benchmark_gold_standard` and `bootstrap: true`. The Cycle 1 retrieval ("retrieve similar past tasks") will return the most similar gold standard as a seed for candidate generation. The `bootstrap: true` flag allows the learning loop to distinguish pre-loaded seeds from organically generated experience, enabling a future quality audit of bootstrap vs. organic entries.

---

*Document produced by: Advanced Elicitation Specialist (Praxis Stage 5.0.3)*  
*Next: Stage 5.1 — Winston anchors MAC architecture on quality-rubric.md + benchmark-questions.md*  
*Winston must read BOTH documents before drafting the architecture*
