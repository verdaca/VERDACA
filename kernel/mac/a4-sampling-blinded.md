# Stage 5.6 A4 Sampling — Blind Human Evaluation Package (Recovery Version)

**For:** Andrey (solo evaluator)
**Purpose:** Validate the Stage 5.6 automated composite scoring against human judgment via Spearman rank correlation. This is the credibility anchor for the entire Stage 5.6 benchmark.
**Expected time to complete:** 15-30 minutes.
**What to do:** Score each of the 9 outputs on the 3-gate rubric below. Submit the 27 scores back to the operator keyed by the color labels used in this file.

**Recovery note:** An earlier blinded package under Greek-letter labels (Alpha–Iota) had its mapping exposed to the team-lead coordinator session, compromising blinding under that label set. This file is the regenerated package under a new color-name label set (Azure through Kelp) with a fresh random permutation. Only the new labels in this file should be used for scoring.

---

## Instructions

You are looking at 9 outputs to 3 different strategic questions, each answered by 3 different approaches. The question each output answers (Q1 / Q5 / Q10) is visible so you can evaluate whether the answer addresses the question. The approach that produced each output is **not** visible — outputs are labeled Azure through Kelp in scrambled order to prevent baseline identification from biasing your scoring.

**Important:** Do NOT try to identify which output came from which approach. The structural features (prose vs. bracketed sections vs. deeper structure) are part of the output and should be scored as you see them, not reverse-engineered as baseline signals. Score against the 3-gate rubric as-if each output stood alone.

**Residual contamination disclosure:** From the earlier (contaminated) mapping you have seen the coarse automated rank structure — roughly 3 top-tier outputs near 78-80, 3 middle-tier outputs 62-68, and 3 bottom-tier outputs 52-56. You do NOT know which specific outputs under the new color labels map to which tier. Try to score each output on its merits against the rubric rather than pattern-matching to the tier structure. The operator's post-hoc analysis will interpret Spearman ρ with this caveat noted.

### The 3-gate rubric

For each output, assign three scores on a 1-5 scale. Total: 9 outputs × 3 gates = **27 scores**.

**G1 — "Would I act on this?"**
- 5 = I would act on this recommendation today, with high confidence
- 4 = I would act on this with minor additional verification
- 3 = Directionally right but I'd need meaningful follow-up before acting
- 2 = Partially useful but too vague or generic to drive action
- 1 = I would not act on this — either wrong, too abstract, or incomplete

**G2 — "Is this obviously wrong in any way I'd catch immediately?"** (REVERSE-CODED)
- 5 = Nothing obviously wrong; the reasoning and claims hold up on a first read
- 4 = Minor quibbles but no errors a knowledgeable reader would flag
- 3 = One or two places I'd push back on but not fatal
- 2 = Noticeable errors or misjudgments that weaken the credibility
- 1 = Obvious errors that make me distrust the whole output

**G3 — "Does this tell me something non-obvious?"**
- 5 = Contains a genuine insight I wouldn't have gotten from common knowledge
- 4 = Meaningfully non-obvious; pushed my thinking beyond the default frame
- 3 = Useful framing but mostly familiar ground
- 2 = Obvious points only; little beyond what I'd already know
- 1 = Nothing non-obvious; reads like a generic answer

### Scoring discipline

- **Score blind to your own identification guesses.** If you catch yourself thinking "this looks like [baseline]," ignore that and score the output on its merits.
- **Score against the rubric, not against an ideal answer.** A 4 on G1 does not require perfection — it requires that you'd act on it with minor verification.
- **Be consistent across outputs.** Pick an anchor example for each gate at score 3 from the first output you read, then calibrate the other 8 against it.
- **Don't over-weight length.** Longer ≠ better. A terse output that nails the core insight can score 5 on G3 while a long output that covers ground you already knew scores 2.

### Submission format

At the bottom of this file there's a scoring template. Fill in 27 numbers (9 outputs × 3 gates) and send back. The operator will compute the Spearman ρ against the automated composite scores across the 9 rows and record pass/fail at threshold ρ ≥ 0.6.

---

## The 9 outputs

---

### Azure

**Question:** Q1 — Pricing Strategy Transition

**Prompt:** Our SaaS product is priced per seat and we're growing users-per-seat much faster than new seats. Usage-based pricing is becoming the market norm in our category. Should we transition, and if so, how do we manage the MRR impact during the transition? (Customer context: SaaS founder, Series B, 200 customers, currently on per-seat pricing. Usage has grown faster than seat count. CFO is modelling the impact of switching. Board wants decision in 6 weeks.)

**Output:**

**[L1 SUMMARY]** Commit to the transition, but through a staged hybrid: new customers onboard to usage-based immediately; existing customers stay on per-seat through contract renewal, then choose at renewal. This sequencing trades short-term MRR optimization for long-term revenue alignment and limits the legal/relational risk of mid-contract price changes. The decision criterion: pull actual usage distribution and run the MRR impact model before committing — the right answer depends on whether your distribution is long-tailed (net upside) or normal (flat net, still strategically correct). Revisit if fewer than 40% of existing customers choose usage-based at first renewal cohort.

**[FINDINGS]**
- **Revenue at risk per model (quantified ranges, labeled as inferences):** Under per-seat: current MRR trajectory based on seat growth (slow) — inference from your stated "users-per-seat growing faster than seats"; under usage-based with median-neutral pricing: MRR tracks usage growth — inference assuming usage elasticity of ~1.0. Actual ranges require your usage distribution data which was not provided in the task.
- **Customer segmentation by usage intensity:** Unknown from task context. Gold-standard analysis requires this data. Inference: typical SaaS distributions are long-tailed (Pareto-like), suggesting net upside, but this must be validated, not assumed.
- **Competitive pricing benchmarks:** Inference — "usage-based becoming market norm in your category" signals a 50%+ share of new-customer acquisitions now choosing usage-based vendors. This creates sales-cycle disadvantage for per-seat vendors at new logo acquisition, independent of the MRR math on existing customers.
- **Transition risk categories (entity-specific to Series B, 200 customers):** (1) existing contracts typically have 12-month terms with ~8-month average remaining life; (2) enterprise segment (if >50% of ARR) creates concentrated renegotiation risk; (3) CS team of typical Series B size (~5-10 people) has limited bandwidth for 200 structured migration conversations in a single quarter.

**[STEELMAN for staying per-seat]** The strongest case: existing customers signed under per-seat have a legitimate expectation of pricing-model stability, not just pricing-level stability. Switching mid-contract — even with good intentions — breaks an implicit contract and exposes you to renegotiation across the entire base, not just the ones you target. The predictability of per-seat enables better headcount planning, cleaner investor communication, and simpler sales motions. Usage-based pricing at your stage introduces MRR volatility that makes your next Series C harder to price. This is not "finance being conservative" — it's a real constraint. Per-seat pricing is ALSO the model your CFO built her operating model around; disrupting it disrupts forecasting, which is load-bearing at Series B. Any transition plan that ignores this is incomplete.

**[DISSENT]** Three stakeholder positions, all legitimate:
- **CFO / finance:** Preserve per-seat for predictability; the MRR optimization is not worth the forecasting noise. Correct concern: usage-based forecasting error at your stage can be ±20%, which breaks investor communication.
- **Commercial / growth:** Transition immediately to capture expansion revenue. Correct concern: every quarter on per-seat is a quarter of delivered-but-uncaptured value; the compound loss is material.
- **Product / CS:** Worry about customer trust during the transition; heavy users will feel punished. Correct concern: customers don't distinguish "price change" from "value extraction"; the communication burden falls on CS and the rollout can damage relationships regardless of how fair the new pricing is in theory.

**[SCENARIOS]**
- **(a) Immediate full switch** (all customers moved at announcement): Fastest MRR alignment, highest legal/relational risk. Estimated 12-18% of customers trigger renegotiation or churn; enterprise segment overweighted in risk. Revisit trigger: if legal counsel identifies contract clauses that make the switch legally risky, this scenario is off the table.
- **(b) 12-month hybrid with migration at renewal** (recommended): Moderate pace, lowest risk. Existing customers grandfather through one contract cycle; new customers start fresh. Estimated MRR flat-to-+5% over 6 months, +15-25% by month 18 assuming long-tailed usage distribution.
- **(c) Stay per-seat with usage-tier overlay** (preserve base, capture expansion): Lowest risk, smallest upside. Add usage-tier overages for heavy users without changing per-seat base. Captures ~40% of the usage-based upside at ~10% of the execution risk. Revisit trigger: if the overlay complexity confuses customers more than it monetizes, retire the overlay.

**[RECOMMENDATIONS]**
1. **Week 1 (before board):** Pull actual usage distribution from billing data. Compute neutral-rate MRR impact under scenario (b). Identify the 10-20 enterprise customers whose migration requires individual planning.
2. **Week 2-3:** Conduct 10-15 customer conversations across the usage distribution. Ask consumption-budgeting questions, not preference questions.
3. **Week 4:** Present board with three scenarios, data, and a recommendation. Scenario (b) is the recommendation if usage distribution is long-tailed; scenario (c) if distribution is roughly normal; scenario (a) is not recommended at this stage.
4. **Post-decision (month 2+):** Migrate new customers to usage-based immediately. Design renewal playbook for existing customers. Train sales + CS on the new pitch. Budget 1 FTE-quarter for billing-system engineering work.
5. **Invalidation criterion:** Revisit decision if fewer than 40% of existing customers choose usage-based at their first renewal — signals the pricing structure is mispriced and the hybrid is generating a two-tier customer base rather than a migration.

**[UNCERTAIN]**
- Usage elasticity at your customer base (assumed ~1.0; actual may be 0.6-1.4)
- Legal exposure from mid-contract model change in your specific contract language
- Whether your billing system can handle usage metering at required accuracy (engineering assessment needed)

**[NONOBVIOUS]**
- The transition sequencing risk — running two pricing models for 12 months creates sales complexity (which pitch for which prospect?), support complexity (two billing flows), and reporting complexity (MRR definition becomes ambiguous). The hidden cost is not the engineering work — it's the operational fragmentation.
- The "stay per-seat" scenario is stronger than it sounds at first. If your ACV is growing through natural seat expansion, you may not NEED usage-based to capture value; you may just need better expansion-motion execution.

---

### Coral

**Question:** Q5 — Moat Building Before Commoditization

**Prompt:** Our core value proposition is 30–65% cost savings on LLM tokens. Token prices are dropping industry-wide by ~30% per year. How do we build a defensible business before our cost savings become irrelevant?

**Output:**

Cost-savings value props are notoriously hard to defend because someone with more scale or more capital can always underbid you. 30% annual deflation means your value delivery erodes passively even if you do nothing wrong. The question is whether "cost savings" is your actual value prop or whether it's just your marketing message, and whether a more durable value prop is hiding underneath.

My read: pivot from cost savings to workflow lock-in before the arithmetic catches up. Customers who adopted you for cost savings have integrated your product into their workflows — that integration is the moat, not the compression algorithm. You have maybe 18-24 months before the cost savings argument stops landing, so the strategic priority is to make yourself load-bearing in customer workflows during that window. Features that create switching costs: data integration, shared history, custom fine-tuning, tenant-specific optimizations, team usage analytics. Each one adds a reason to stay even when the raw cost math changes.

What to avoid: doubling down on algorithm improvements. The cost savings floor will keep dropping; you'll end up in a technical arms race you can't win against frontier model providers who have scale economics you don't. Build workflow moats, not technical moats.

---

### Ember

**Question:** Q10 — Diagnostic (Diverging Metrics)

**Prompt:** Our NPS is 67 and rising, but annual retention dropped from 91% to 84% over 12 months. We don't know why these signals are diverging. How do we diagnose what's actually happening and what do we do about it? (Customer context: B2B SaaS, 4 years old, strong NPS, enterprise segment. Support tickets flat, NPS rising, product engagement stable.)

**Output:**

**[FINDINGS]**
- NPS ≠ retention for a reason: NPS measures survey respondents (biased toward engaged users), retention measures all customers. Divergence signals selection bias in NPS, not contradiction.
- 7-point retention drop (91→84) in 12 months = ~$X million revenue impact depending on ARR.
- Possible root causes without evidence to distinguish: cohort drift, segment shift, champion turnover, product drift, competitive displacement, pricing sensitivity, over/under-served segments.
- Actionable without diagnosis: nothing. Treating symptoms without diagnosis risks wrong interventions.

**[RECOMMENDATIONS]**
1. **Diagnostic protocol (30 days):**
   - Segment churn by cohort, segment, ACV, tenure, acquisition channel
   - Qualitative exit interviews with 10-15 churned customers
   - Cross-reference NPS respondents vs. churned customers (overlap expected to be near-zero)
   - Identify champion turnover rate among churned accounts
2. **Diagnosis-driven interventions** (not yet actionable — wait for data):
   - If segment shift: product-market fit drift, requires roadmap repositioning
   - If champion turnover: customer success playbook for champion transitions
   - If competitive displacement: competitive intelligence + product response
   - If pricing: retention pricing review
3. **Decision timeline:** Diagnose in 30 days, intervene in month 2.

**[DISSENT]**
- **Customer success:** It's execution — we need more CSMs and better playbooks. Counter: more CS without diagnosis is throwing people at a problem.
- **Product:** It's product-market fit drift. Counter: we don't know yet; could be PMF or execution.
- **Sales:** It's pricing sensitivity at renewal. Counter: could be, but testable only after diagnosis.

**Self-critique:** My protocol assumes you have customer data granular enough to segment. If your data infrastructure is weak, the diagnosis itself takes 90 days, not 30.

---

### Flint

**Question:** Q1 — Pricing Strategy Transition

**Prompt:** Our SaaS product is priced per seat and we're growing users-per-seat much faster than new seats. Usage-based pricing is becoming the market norm in our category. Should we transition, and if so, how do we manage the MRR impact during the transition? (Customer context: SaaS founder, Series B, 200 customers, currently on per-seat pricing. Usage has grown faster than seat count. CFO is modelling the impact of switching. Board wants decision in 6 weeks.)

**Output:**

Usage-based pricing is becoming the dominant model in SaaS for a reason — it aligns what you charge with the value customers get, and when usage is growing faster than seats, per-seat pricing is literally leaving money on the table. So yes, you should probably transition, but the how matters more than the whether.

The core problem with per-seat pricing in your situation is that customers are getting more value than they're paying for. That sounds like a customer win, but it's actually a risk: you're training your base to expect that usage is free, and when you try to charge for it later, they'll experience it as a price hike rather than a natural consequence of value delivered. The longer you wait, the worse this gets.

On the transition itself, a full flash-cut is almost always a mistake. You'll spook existing customers, trigger a wave of renegotiations you don't have capacity for, and your CFO will lose her mind trying to model the MRR impact with that much uncertainty. A better approach is a hybrid period: new customers onboard to usage-based, existing customers stay on per-seat through their current contract renewal, and at renewal you offer them the choice between staying per-seat (at a modest increase to reflect growth) or moving to usage-based (which will probably be cheaper for light users and more expensive for heavy ones, but aligns incentives).

During the transition you should expect some MRR volatility. Heavy-usage customers will initially pay more on usage-based, which is good for revenue but bad for relationships if you don't communicate it clearly in advance. Light-usage customers will pay less, which is bad for short-term MRR but good for expansion potential. Net, you should see flat to slightly positive MRR in the first 6 months, and meaningful upside in year 2 as usage continues to grow.

A few practical things to watch. First, make sure your billing system can actually handle usage-based before you promise it — usage metering, overage handling, and mid-period upgrades are surprisingly hard engineering problems. Second, your sales team will need a new pitch — per-seat is easier to sell because buyers can predict the cost, and usage-based requires more customer education up front. Budget for sales enablement. Third, your CS team needs to proactively reach out to heavy-usage customers before they see a surprise bill; nothing burns trust faster than a 40% price increase that arrives in an email.

On timing: 6 weeks is tight for a decision, but reasonable. I'd spend the first 2 weeks modeling the MRR impact under three scenarios (hybrid, full switch, stay put), the next 2 weeks talking to 10-15 customers across the usage distribution to understand their reaction, and the final 2 weeks making the call and designing the rollout. Don't let the board rush you into committing to a specific transition design before you've validated the customer reaction — a decision to transition is reversible; a botched rollout isn't.

My recommendation: commit to the transition, but execute as a 12-month hybrid with new customers on usage-based immediately and existing customers migrated at renewal. Expect MRR to look flat for 6 months and then accelerate. The bigger risk is waiting — every quarter you stay on per-seat while usage grows is a quarter of value you're delivering for free.

---

### Garnet

**Question:** Q5 — Moat Building Before Commoditization

**Prompt:** Our core value proposition is 30–65% cost savings on LLM tokens. Token prices are dropping industry-wide by ~30% per year. How do we build a defensible business before our cost savings become irrelevant?

**Output:**

**[FINDINGS]**
- Token prices dropping ~30%/year industry-wide — your cost-savings value prop erodes passively; inference from public pricing data.
- Compression algorithms are not defensible as IP — most core techniques are public or reimplementable.
- Workflow integration IS defensible: data, history, custom prompts, team usage patterns create real switching costs.
- Cloud giants' scale advantages make cost-only competition unwinnable long-term.
- Customer relationship depth + switching costs > technical algorithm edge for durability.

**[RECOMMENDATIONS]**
1. Pivot narrative from "30-65% savings" to "workflow intelligence" within 6 months. Savings become a feature, not the value prop.
2. Ship switching-cost features in priority order: tenant-specific history/state > team analytics > integration depth > fine-tuning.
3. Price on outcomes (productivity, time saved) not on savings, to decouple pricing from deflating token cost.
4. Avoid investment in pure algorithm R&D beyond maintenance; divert to integration depth.

**[DISSENT]**
- Engineering: technical moat is real; algorithm improvements compound. Counter: not against infinite-capital competitors.
- Commercial: customers buy savings, not workflow. Counter: they buy workflows from vendors they trust — savings are the entry point, not the relationship.
- Investor: urgency vs. defensibility trade-off; spend fast on growth or slow on moats? Counter: both are needed, but the growth path without moats is a slow death.

**Self-critique:** My framing assumes workflow integration features are buildable in 18-24 months with current eng capacity. If the eng team is already consumed with keeping cost savings working, the pivot requires hiring, which costs time the deflation clock doesn't give you.

---

### Hazel

**Question:** Q10 — Diagnostic (Diverging Metrics)

**Prompt:** Our NPS is 67 and rising, but annual retention dropped from 91% to 84% over 12 months. We don't know why these signals are diverging. How do we diagnose what's actually happening and what do we do about it? (Customer context: B2B SaaS, 4 years old, strong NPS, enterprise segment. Support tickets flat, NPS rising, product engagement stable.)

**Output:**

Rising NPS with falling retention is a classic sign that the respondents aren't representative. The customers who fill out NPS surveys are not the customers who are churning — the churners are quiet, and the enthusiasts are loud. So the divergence isn't actually a divergence; it's selection bias.

The diagnosis should start with WHO is churning. Break retention down by cohort, segment, ACV, tenure, acquisition channel. Usually the answer emerges quickly: a specific segment is churning (maybe SMB while enterprise is stable), or a specific cohort (customers who signed in a specific quarter), or a specific use case. Once you find the who, the why usually follows.

Common patterns: (1) competitive displacement in a specific segment; (2) champion turnover where the original buyer left and the new buyer didn't adopt; (3) product drift where the product evolved away from a segment's needs; (4) pricing sensitivity from renewals hitting budget constraints; (5) over-served and under-served customer segments both churning for different reasons. The interventions are completely different for each root cause, so diagnosis must precede action.

---

### Indigo

**Question:** Q5 — Moat Building Before Commoditization

**Prompt:** Our core value proposition is 30–65% cost savings on LLM tokens. Token prices are dropping industry-wide by ~30% per year. How do we build a defensible business before our cost savings become irrelevant?

**Output:**

**[L1 SUMMARY]** Pivot the value proposition from cost savings to workflow intelligence within the next 6 months, while the cost-savings narrative still generates customer acquisition. Prioritize switching-cost features in this order: tenant-specific history/state (highest switching cost, fastest to build) → team analytics (high customer stickiness) → integration depth (slower but durable) → custom fine-tuning (slow and expensive, lowest priority). Avoid algorithm R&D beyond maintenance — you cannot win a cost race against frontier providers with infinite capital. Revisit at 12 months if workflow feature adoption is below 40% of active customers.

**[FINDINGS]**
- **Deflation rate:** Inference — ~30%/year industry-wide from public pricing data, likely accelerating in second half of 2026 as frontier providers continue scaling. 18-24 month timeline before cost savings value proposition becomes negligible is reasonable but not certain.
- **Defensibility options ranked by switching cost:**
  1. **Workflow integration** — customer's internal tools integrated with product's APIs (highest switching cost; takes 6-18 months for customers to build; they will not rebuild for marginal savings)
  2. **Data / history lock-in** — shared optimization history, learned patterns specific to tenant (high switching cost; invisible to customer until they try to leave)
  3. **Brand / relationship depth** — customer success + training + documentation (medium switching cost; erodes with vendor changes)
  4. **Algorithm IP** — compression techniques (low switching cost; open-source alternatives exist)
- **Commodification threshold:** When frontier providers' native token prices drop below ~50% of your current customer cost, the savings argument stops working. Current deflation trajectory suggests this threshold hits in 18-24 months.
- **Critical asymmetry:** Frontier providers (OpenAI, Anthropic, Google) have infinite capital for native cost reduction but NO incentive to build workflow features for third-party use cases. This is your real defensibility window.

**[STEELMAN — no moat is buildable]** The strongest case: cost-savings businesses in commoditizing markets rarely build durable moats. The history of "optimization" businesses (CDN providers, caching layers, compression tools) shows that they either become commodity infrastructure (low margin, high volume) or get absorbed by the platform they were optimizing. Building workflow features is a tempting pivot but adds complexity without changing the fundamental value equation — you're still a tool layer on top of platforms that will eventually absorb your function. The defensible move may be to exit early — sell the company to a platform provider before commoditization completes, rather than trying to build a new moat during the decay window. This is not defeatism; it's acknowledging that some business models have a half-life.

**[DISSENT]**
- **Engineering:** Technical moat is possible via novel optimization techniques; skilled team can stay ahead. Core concern: pivoting to features abandons the technical strength that got you here.
- **Commercial:** Workflow lock-in is the only durable moat; pivot immediately and aggressively. Core concern: the savings argument already feels weaker in sales calls than 12 months ago.
- **Investor:** Exit optimization — the defensible play may be acquisition before commoditization. Core concern: every quarter of delay reduces exit value as commoditization progresses.
- **CEO:** Identity question — is the company "a compression tool" or "a workflow platform"? The pivot requires rebranding, re-pricing, and repositioning, which is its own execution risk.

**[SCENARIOS]**
- **(a) Deflation accelerates (>40%/yr):** Cost savings become irrelevant in 12 months. Pivot is urgent; some workflow features ship too late; exit-before-commoditization becomes attractive. Probability ~30%.
- **(b) Deflation stabilizes (10-20%/yr):** 36+ month window to build workflow moats. Pivot is meaningful; features become the business. Probability ~40%.
- **(c) Deflation flattens or reverses (<10%/yr):** Rare but possible if frontier provider pricing power stabilizes. Cost savings retain value; workflow pivot is additive, not urgent. Probability ~15%.
- **(d) Frontier providers launch competing feature set:** Tail risk. Frontier providers decide to build workflow tools natively. Your entire defensibility window closes. Probability ~15-20%.

**[RECOMMENDATIONS]**
1. **Month 1-3:** Ship 1-2 tenant-specific history/state features. Measure adoption + retention impact.
2. **Month 1:** Rebrand narrative from "cost savings" to "workflow intelligence" in new sales collateral while old narrative is still working for existing pipeline.
3. **Month 2:** Cost-savings feature goes into "maintenance-only" mode; no new algorithm investment.
4. **Month 3-6:** Team analytics + integration depth features.
5. **Month 6:** Checkpoint review. Measure workflow feature adoption. If <30%, re-think feature priorities. If >50%, accelerate investment.
6. **Month 12:** Strategic review. Update pivot speed based on actual deflation trajectory. Consider exit conversation if scenario (d) unfolds.
7. **Invalidation triggers:** (i) frontier providers announce native workflow features → reconsider defensibility entirely; (ii) deflation accelerates past 40%/yr → compress timeline; (iii) workflow feature adoption <30% at 6 months → pivot priorities.

**[UNCERTAIN]** Precise deflation trajectory (30%/yr is current rate, not a projection); frontier providers' roadmap for workflow-layer features; customer elasticity between savings-based and feature-based pricing; eng team capacity for the pivot without hiring.

**[NONOBVIOUS]** The "pivot" framing may be wrong. The real question is whether the customer PROBLEM (LLM cost + workflow complexity) changes as tokens get cheaper. Cheaper tokens mean more LLM usage per workflow, which means MORE workflow complexity — and workflow tools become MORE valuable, not less. If this is right, your customers will increase spend on workflow-layer products even as they reduce spend on compression. The pivot isn't away from a dying market — it's toward an expanding one that your customers don't yet realize they need.

---

### Jade

**Question:** Q1 — Pricing Strategy Transition

**Prompt:** Our SaaS product is priced per seat and we're growing users-per-seat much faster than new seats. Usage-based pricing is becoming the market norm in our category. Should we transition, and if so, how do we manage the MRR impact during the transition? (Customer context: SaaS founder, Series B, 200 customers, currently on per-seat pricing. Usage has grown faster than seat count. CFO is modelling the impact of switching. Board wants decision in 6 weeks.)

**Output:**

**[FINDINGS]**

Per-seat to usage-based migration is a structural GTM change, not a pricing tweak. Three facts frame the decision:

1. **Usage growing faster than seats** means the product is doing its job — customers are getting more value per user — but your revenue is not capturing that value. This is the definition of a pricing model misaligned with value delivery.
2. **Market norm shifting to usage-based** in your category is a signal, not a mandate. The relevant question is whether your BUYERS are moving, not whether your competitors are. If buyers still budget by seat count (common in CFO-driven procurement), usage-based adds friction.
3. **MRR impact is bimodal.** Heavy-usage customers will pay more on usage-based; light-usage customers will pay less. Net MRR depends on the shape of your usage distribution. If it's long-tailed (a few very heavy users, many light), net MRR goes up. If it's normally distributed, it roughly stays flat. You need the actual distribution before committing.

Transition risk categories specific to your Series B stage: (a) existing contracts — most per-seat contracts have language that makes mid-term pricing changes hard; (b) sales cycle impact — usage-based lengthens enterprise sales cycles because buyers need to forecast consumption; (c) customer success bandwidth — usage alerts and overage conversations are a new CS workload.

**[RECOMMENDATIONS]**

1. **This week:** Pull the usage distribution data. Calculate MRR impact under usage-based pricing using your current cohort for three rate structures (aggressive / neutral / conservative). This is a 2-day CFO exercise and must happen before any strategic commitment.
2. **Weeks 2-3:** Talk to 10-15 customers across the usage distribution. Don't ask "would you prefer usage-based?" — ask "how do you currently budget for this product and how would you react if your bill was 20% higher in months you used it more?" The answers will tell you whether the MRR upside is real or illusory.
3. **Weeks 4-5:** Design a hybrid: new customers to usage-based immediately; existing customers stay per-seat through current contract, migrate at renewal with a choice. Price the usage-based tier so the median existing customer pays roughly what they pay today (± 10%), heavy users pay more, light users pay less.
4. **Week 6:** Present to the board with the data, not a recommendation. Let the board make the commit/don't-commit call armed with actual numbers.

**[DISSENT]**

The CFO / finance perspective will push for preserving per-seat predictability — MRR forecasting is dramatically harder under usage-based, and board / investor communication becomes more variable quarter-to-quarter. This is a real constraint, not just risk aversion. Counter: the predictability comes at the cost of systematic undercharging, and "predictable revenue that undervalues the product" is not a sustainable position.

The commercial team will push for the transition aggressively because it unlocks expansion revenue without new logo acquisition. Counter: the transition adds new failure modes (customers hitting unexpected bills, churning on sticker shock) that are easy to underweight when the upside math looks good.

The product team will push to align with market norms because it makes competitive positioning easier. Counter: market norms lag product reality; being the exception can be a differentiator if executed intentionally.

**Self-critique:** My framing assumes usage is actually creating value customers would pay for incrementally. If usage is growing because of inefficiency (customers using more because the product is clunky, not because they're getting more value), usage-based pricing monetizes the inefficiency and accelerates churn. Validate this before committing — if usage growth doesn't correlate with retention and expansion, the transition is the wrong move regardless of market norms.

---

### Kelp

**Question:** Q10 — Diagnostic (Diverging Metrics)

**Prompt:** Our NPS is 67 and rising, but annual retention dropped from 91% to 84% over 12 months. We don't know why these signals are diverging. How do we diagnose what's actually happening and what do we do about it? (Customer context: B2B SaaS, 4 years old, strong NPS, enterprise segment. Support tickets flat, NPS rising, product engagement stable.)

**Output:**

**[L1 SUMMARY]** Do not intervene until diagnosis is complete. The NPS/retention divergence is almost certainly selection bias — NPS respondents are not the churned customers. Run a 30-day diagnostic protocol: segment churn across 5 axes (cohort, segment, ACV, tenure, channel) + 10-15 qualitative exit interviews. The diagnosis determines the intervention; intervening without diagnosis risks expensive wrong fixes. Invalidation trigger: if diagnosis surfaces multiple co-occurring root causes, shift to portfolio-of-interventions framing rather than single-root-cause fix.

**[FINDINGS]** — Framed as hypothesis taxonomy for diagnostic rigor.

**Hypotheses (labeled as hypotheses, NOT conclusions):**
- **H1 — Selection bias in NPS:** Engaged users respond to NPS; churning users are disengaged and don't respond. NPS is a measure of the engaged subset, retention is a measure of all customers. Divergence is expected, not paradoxical. Falsification test: cross-reference NPS respondent list against churned customer list; <10% overlap confirms bias.
- **H2 — Cohort effect:** Customer distribution is shifting — recent signups are in a higher-churn segment (e.g., SMB acquired via different channel). Aggregate retention falls even if existing customers stay. Falsification test: compute retention by cohort of acquisition; if older cohorts are stable and newer are churning faster, H2 confirmed.
- **H3 — Champion turnover:** Original buying champions have departed customer organizations; new champions haven't bought in. Product becomes shelfware regardless of NPS. Falsification test: exit interviews — ask about champion stability; track champion tenure in customer DB if available.
- **H4 — Product-market fit drift:** Product has evolved away from original use case; engaged users still value it (high NPS) but new cohorts don't find it. Falsification test: compare product usage depth between high-retention and low-retention cohorts.
- **H5 — Pricing sensitivity at renewal:** Customers are churning at renewal due to pricing, not product. Falsification test: correlate renewal timing with churn; if churn clusters at renewal dates, H5 likely.
- **H6 — Competitive displacement:** Specific competitor winning in a specific segment. Falsification test: exit interviews — name specific next vendors; segment analysis by lost-to-competitor.
- **H7 — Over-served vs. under-served segments both churning:** Different segments churning for different reasons, aggregating into one number. Falsification test: ACV segmentation of churn reveals bimodal pattern.

**Data collection protocol per hypothesis:** Each hypothesis has a specific data query (customer DB analysis) + qualitative signal (exit interview) that can confirm or refute it.

**Internal consistency check:** Accepting NPS at face value while accepting retention at face value is inconsistent — one measures engagement, the other measures all customers. The analysis must start from the premise that NPS and retention can both be "true" while measuring different things.

**[STEELMAN — it's a PMF crisis]** Strongest case: NPS from engaged users is high; retention is falling; this is product-market fit drift where the product-market is contracting. The engaged users genuinely love the product but the TAM is shrinking or segmenting out from under you. The data will show this via cohort decay — each subsequent cohort retains worse than the prior. This is a structural business issue, not a tactical retention issue, and CSM playbooks won't save you. The honest answer may be that you need a product pivot, not a retention fix.

**[DISSENT]**
- **Customer success:** It's execution — we need more CSM capacity and better renewal playbooks.
- **Product:** It's PMF drift — cohort data will show structural issue.
- **Sales:** It's pricing — renewals are hitting budget ceilings.
- **Finance:** It's composition — customer mix shift toward higher-churn segments.
- **CEO:** It's multiple things at once — no single root cause.

**[SCENARIOS]** — presented as "interventions conditional on hypothesis":
- **(IF H1 confirmed):** No action needed; "divergence" is measurement artifact. Reframe metrics to measure "engaged retention" separately.
- **(IF H2 confirmed):** Filter cohort data for intervention targeting; adjust acquisition channels.
- **(IF H3 confirmed):** Customer success playbook for champion turnover; track champion health in CRM.
- **(IF H4 confirmed):** Strategic — product roadmap repositioning or PMF pivot. Largest action required.
- **(IF H5 confirmed):** Pricing review; retention pricing for at-risk renewals.
- **(IF H6 confirmed):** Competitive intelligence + product/feature response.
- **(IF H7 confirmed):** Segment-specific strategies, potentially discontinuing or repricing sub-segments.

**[RECOMMENDATIONS]**
1. **Week 1:** Pull churn data by cohort × segment × ACV × tenure × acquisition channel. This is a 1-2 day data exercise if your CS team has proper instrumentation.
2. **Week 1-2:** Cross-reference NPS respondent list against churned customer list. Quantify overlap. <10% overlap confirms H1 selection bias.
3. **Week 2-4:** 10-15 qualitative exit interviews. Ask about champion tenure, competitive alternatives, pricing reactions, product fit.
4. **Week 4:** Hypothesis triage. Which 1-2 hypotheses does the data support? Which are refuted?
5. **Month 2:** Intervention implementation based on diagnosis.
6. **Invalidation:** If multiple hypotheses co-occur (common in practice), shift to portfolio of interventions rather than single-root-cause fix.

**[UNCERTAIN]** Customer data granularity; exit interview willingness; actual churn distribution across segments; CSM capacity for diagnostic workload.

**[NONOBVIOUS]** The "diverging metrics" framing conceals a deeper issue — the question is not "why is retention falling while NPS rises" but "what does retention actually measure that NPS doesn't." The honest answer is usually: retention measures all customers (including the quiet departers) while NPS measures a self-selected subset (the engaged respondents). These are measuring DIFFERENT populations. The divergence is not paradoxical — it's informative. Treating them as comparable was the error.

---

## Scoring template

Fill in the 27 blanks below (9 outputs × 3 gates), then submit back to the operator. The operator will compute Spearman ρ against the automated composite and record A4 validation pass/fail at threshold ρ ≥ 0.6.

| Label | Question | G1 "Would I act?" | G2 "Obviously wrong?" (reverse) | G3 "Non-obvious?" |
|---|---|---|---|---|
| Azure | Q1 | ___ | ___ | ___ |
| Coral | Q5 | ___ | ___ | ___ |
| Ember | Q10 | ___ | ___ | ___ |
| Flint | Q1 | ___ | ___ | ___ |
| Garnet | Q5 | ___ | ___ | ___ |
| Hazel | Q10 | ___ | ___ | ___ |
| Indigo | Q5 | ___ | ___ | ___ |
| Jade | Q1 | ___ | ___ | ___ |
| Kelp | Q10 | ___ | ___ | ___ |

**Total scores required: 27.** Each score on 1-5 scale. G2 is reverse-coded (higher = fewer errors).

---

**End of blinded sampling package (recovery version). Submit scores back to operator for Spearman computation.**
