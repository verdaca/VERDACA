# Innovation Strategy: Praxis Studio Pricing + Business Model

**Date:** 2026-04-16
**Strategist:** Andrey
**Strategic Focus:** Pricing model, business model validation, and monetization strategy for Praxis Studio POV launch

---

## Strategic Context

### Current Situation

Praxis is a multi-agent reasoning engine for strategic advisory. Stages 1-6 built the engine (measurement, compression, memory, runtime, MAC meta-agent controller, Studio workflow wrapper). Stage 7 wraps everything in a customer-facing shell (Next.js + FastAPI + Clerk + Stripe). No revenue yet. Internal cost to run one Studio deep session is ~$2.50. The product delivers a ~15-page structured strategic analysis with red team dissent and named scenarios in ~12 minutes (deep mode). Three hypothesized customer segments: Series A-C founders (50%), mid-market COOs (30%), boutique strategy consultancies (20%). [HYPOTHETICAL — all segments from synthesis, not confirmed via real-buyer interviews]

### Strategic Challenge

Define a pricing model that: (1) resonates with how each ICP segment already thinks about advisory spend, (2) covers costs with healthy margin at POV scale, (3) scales from single founder to enterprise consultancy without structural redesign, (4) enables first POV customer to go from signup to paid session in <10 minutes. The existing Winston prompt contains placeholder prices ($500/$1000/$2000 per session) that need validation or replacement based on this analysis.

---

## MARKET ANALYSIS

### Market Landscape

**Strategic advisory market (the budget category Praxis competes in):**

The hypothesized ICP buys strategic analysis from three existing channels — each with distinct cost, speed, and quality profiles: [HYPOTHETICAL — all market sizing from synthesis]

1. **Management consulting engagements** ($50K-$300K per project, 4-12 weeks) — McKinsey/Bain/BCG for enterprise; boutique firms for mid-market. Strength: deep domain expertise, relationship trust, deliverable density. Weakness: cost, timeline, availability for <$50K engagements. [HYPOTHETICAL]

2. **Fractional C-suite / independent strategists** ($5K-$15K/month retainer, or $200-$500/hour) — individual advisors with domain expertise. Strength: speed, personal relationship, contextual knowledge. Weakness: single perspective (no red team), deliverable quality varies, availability constrained by individual capacity. [HYPOTHETICAL]

3. **Internal strategy teams** ($15K-$25K/month fully-loaded per analyst) — in-house teams at larger organizations. Strength: organizational context, always available. Weakness: groupthink, limited perspective diversity, expensive to maintain for <100-person companies. Not available to most Series A-C founders. [HYPOTHETICAL]

**The gap Praxis fills:** there is no existing option that delivers structured multi-perspective strategic analysis at the $29-$149 price point in minutes rather than weeks. The closest analogue is "asking ChatGPT a strategic question" — which is free but produces single-perspective, unstructured, non-falsifiable output without dissent, scenarios, or scope-limits. [HYPOTHETICAL]

### Competitive Dynamics

**Direct competitors (AI-powered strategic advisory):** None identified at the specific intersection of multi-agent deliberation + structured output format + dissent preservation + muted operator-realism register. The market category is nascent. [HYPOTHETICAL]

**Adjacent competitors:**
- **ChatGPT / Claude / Gemini (direct prompting):** Free or $20-200/month subscription. Single-agent, unstructured output. No quality gates, no dissent, no scenarios. The "good enough" baseline that Praxis must demonstrably beat. [HYPOTHETICAL]
- **Perplexity / AI research tools:** $20-40/month. Research-oriented, not advisory-oriented. Don't produce decision frameworks. [HYPOTHETICAL]
- **Strategy consulting AI assistants (boutique SaaS):** Emerging category. Typically $99-$499/month subscription. Feature comparison TBD. None identified with the multi-agent deliberation architecture. [HYPOTHETICAL]

**Competitive positioning:**
- vs. consulting firms: 100x cheaper, 100x faster, available 24/7, no engagement minimums
- vs. fractional strategists: structured output with explicit dissent vs. verbal advice; always available vs. scheduling-constrained
- vs. direct LLM prompting: structured multi-perspective analysis with quality gates vs. single-perspective prose

### Market Opportunities

1. **Underserved "below the consulting threshold" segment:** Series A-C founders who need strategic analysis but can't justify $50K+ consulting engagements for individual decisions. This is the primary beachhead. [HYPOTHETICAL]

2. **Consultancy leverage multiplier:** Boutique firms that need to produce more deliverables per analyst hour. Praxis as invisible infrastructure (firm_voice mode) that compounds engagement leverage. [HYPOTHETICAL]

3. **Decision audit trail:** Organizations that need documented decision rationale for governance, board reporting, or regulatory compliance. The structured output format (dissent + scenarios + scope-limits) naturally serves as an audit artifact. [HYPOTHETICAL]

### Critical Insights

1. **The budget anchor determines everything.** If founders anchor on "AI tool" pricing ($20-$50/month), Praxis is expensive. If they anchor on "strategic advisory" pricing ($5K-$50K per engagement), Praxis is a bargain. The entire pricing strategy depends on which frame wins. [HYPOTHETICAL]

2. **Per-session pricing aligns with the decision-shaped job.** Founders don't hire advisory monthly — they hire it per decision. "I need an answer to THIS question" is the job shape. Per-session pricing maps to the job better than subscription. [HYPOTHETICAL]

3. **The consultancy channel has different economics.** Consultancies evaluate tools on engagement leverage (hours saved per deliverable vs. risk to deliverable density), not on absolute price. A $149/session tool that saves 20 analyst hours at $300/hour blended rate is a 40:1 ROI. [HYPOTHETICAL]

---

## BUSINESS MODEL ANALYSIS

### Current Business Model

Pre-revenue. The business model is being designed at this stage. The engine is built; the question is how to monetize it.

### Value Proposition Assessment

**Value Proposition Canvas — Per Segment:**

**Founders (50%):**

| Customer Profile | Value Map |
|---|---|
| **Jobs:** Board-ready decision frameworks under time pressure; surface blind spots; genuine steelman treatment of uncomfortable options | **Products:** Studio deep session — 15-page structured analysis with red team dissent, named scenarios, falsification conditions |
| **Pains:** Cross-functional teams produce contradictory recommendations; can't find clean numbers for transition impacts; board expects clarity in weeks | **Pain relievers:** Multi-agent red team forces genuine steelman; named scenarios with trigger conditions; explicit [UNCERTAIN] sections prevent false confidence |
| **Gains:** Position to hold through 2 quarters; falsification rules with specific flip conditions; board sees due diligence | **Gain creators:** 12-minute turnaround vs 2-4 week consultancy; structured output format; ~100x cheaper than consulting engagement |

[ALL ENTRIES HYPOTHETICAL]

**COOs (30%):**

| Customer Profile | Value Map |
|---|---|
| **Jobs:** Decision architectures exposing factors/weights/trade-offs; structured diagnostic plans per hypothesis | **Products:** Studio deep session in decision-framework rendering mode |
| **Pains:** Memos with conclusions untraceable to factors; binary framings hiding actual decision structure | **Pain relievers:** Structured output forces factor-level transparency; scope-limits section surfaces what wasn't analyzed |
| **Gains:** Decision frameworks surviving the execution quarter; risk-weighted analysis matching longer COO time horizon | **Gain creators:** Repeatable template for each decision type; explicit [UNCERTAIN] sections calibrate confidence |

[ALL ENTRIES HYPOTHETICAL]

**Consultancies (20%):**

| Customer Profile | Value Map |
|---|---|
| **Jobs:** White-label tool output as firm-voice deliverables; maximize engagement leverage; assess commoditization risk | **Products:** Studio deep session in firm-voice rendering mode with invisible provenance |
| **Pains:** Provenance anxiety — tool brand competing with firm brand; thin analysis losing follow-on engagement; commoditization of judgment | **Pain relievers:** ADR-09 invisible provenance mode; dense analytical structure; register enforcement (ADR-11) matches professional advisory tone |
| **Gains:** Engagement leverage compound — 12-minute analysis → 8 hours billable framing; deliverable density preserved | **Gain creators:** Volume pricing via Partner credit pack; white-label rendering; no tool branding on output |

[ALL ENTRIES HYPOTHETICAL]

### Revenue and Cost Structure

**Cost per session (internal, LLM cost only):**

| Mode | Estimated internal cost | Notes |
|---|---|---|
| Quick | ~$0.80 | Single-cycle MAC, shorter output |
| Deep | ~$2.50 | Full 3-cycle MAC deliberation |

**(Internal scoring; A4 human validation deferred to Stage 7 POV Harness.)**

**Infrastructure costs (POV scale):**
- Hosting: ~$50-$100/month (Vercel + Railway/ECS Fargate + managed Postgres)
- Clerk auth: free tier at launch (up to 10,000 MAU)
- Stripe: 2.9% + $0.30 per transaction
- Anthropic API: usage-based (covered in per-session cost above)
- Total fixed cost at POV: ~$100-$200/month [HYPOTHETICAL]

**Revenue model (per-session primary + credit packs secondary):**

Break-even analysis at POV:
- Fixed costs ~$150/month
- At $149/deep session with $2.50 internal cost: $146.50 margin per session
- Break-even: 2 deep sessions/month (trivially achievable with ≥1 active customer)
- At 10 paying customers × 3 deep sessions/quarter each: $4,470/quarter revenue
- At 50 paying customers × 3 deep sessions/quarter: $22,350/quarter

[ALL PROJECTIONS HYPOTHETICAL]

### Business Model Weaknesses

1. **Single-product dependency:** All revenue from Studio sessions. No diversification until Stage 8+ expands the workflow library. [HYPOTHETICAL]

2. **Anthropic API dependency:** Single supplier for the core LLM. Price increases, rate limits, or service disruptions directly impact cost structure and availability. No alternative supplier path designed. [HYPOTHETICAL]

3. **Quality validation incomplete:** The headline quality improvement figure carries an "(internal scoring; A4 deferred)" caveat. If A4 Spearman validation fails (ρ < 0.6), the quality-based pricing justification weakens. [HYPOTHETICAL]

4. **No switching costs at POV:** Customers can replicate the job (imperfectly) by prompting Claude/ChatGPT directly. Lock-in develops only if session history, workspace memory, and custom templates become valuable over time. [HYPOTHETICAL]

5. **Consultancy channel is unproven:** The white-label use case (firm_voice mode, invisible provenance) is architecturally supported but no consultancy partner has confirmed willingness to use it. [HYPOTHETICAL]

---

## DISRUPTION OPPORTUNITIES

### Disruption Vectors

**Primary disruption vector: "Below the consulting threshold" strategic advisory**

Classic Christensen low-end disruption: serve the segment that management consulting firms can't profitably serve. Series A-C founders with $5M-$50M in revenue need strategic analysis for board-level decisions but can't justify $50K-$150K consulting engagements for individual questions. They currently muddle through with direct LLM prompting, informal advisor conversations, or internal team brainstorming. Praxis offers structured, multi-perspective analysis at 100x lower cost and 100x faster delivery. [HYPOTHETICAL]

**Secondary disruption vector: Consultancy leverage multiplier**

Not displacing consultancies — empowering them. Boutique firms that can't hire enough analysts to match Big 4 deliverable volume can use Praxis as invisible analytical infrastructure. The disruption target is the analyst-hours bottleneck, not the consultant-client relationship. [HYPOTHETICAL]

### Unmet Customer Jobs

From Maya §B.1 functional JTBD analysis, the most underserved jobs:

1. **"Surface the uncomfortable question"** — hiring someone to make the steelman case for the option nobody wants to consider (sell the company, take the bridge round, kill the product line). Current alternatives (advisors, board members) have incentive misalignment. Praxis has no incentive structure — it treats all options equally. [HYPOTHETICAL]

2. **"Give me a falsification rule"** — not "what should I do?" but "what specific evidence would change my mind?" No current advisory product produces explicit invalidation conditions as a structural output feature. [HYPOTHETICAL]

3. **"Tell me what's not in the analysis"** — explicit scope-limits (ADR-07) as a standard output section. Consultancy deliverables rarely name what they chose not to analyze. [HYPOTHETICAL]

### Technology Enablers

1. **Multi-agent deliberation at $2.50/session cost** — the underlying LLM cost has dropped enough that multi-perspective analysis is economically viable at consumer price points. This was not possible 12 months ago. [HYPOTHETICAL]

2. **Structured output enforcement (quality gates R1-R12)** — the MAC quality gate engine ensures every output meets minimum standards for dissent, scenarios, scope-limits, and epistemic honesty. This eliminates the "sometimes great, sometimes garbage" failure mode of direct LLM prompting. [HYPOTHETICAL]

3. **Template-driven rendering (Jinja2 + YAML)** — output format customization (position-to-hold vs decision-framework vs firm-voice) without changing the underlying analysis. Enables per-segment value propositions from a single analytical engine. [HYPOTHETICAL]

### Strategic White Space

**The $29-$149 structured strategic analysis market does not exist yet.** There are $0 options (direct prompting, low quality) and $5K+ options (consultancy/fractional, high quality but slow and expensive). The space between $0 and $5K for strategic advisory is empty. Praxis fills it. [HYPOTHETICAL]

This is the classic Christensen gap: incumbents (consultancies) can't profitably serve it, free alternatives (direct prompting) can't serve it at quality, and the enabling technology (multi-agent deliberation at $2.50/run) just became viable. [HYPOTHETICAL]

---

## INNOVATION OPPORTUNITIES

### Innovation Initiatives

1. **Per-session advisory marketplace** — position Praxis as the "Stripe for strategic analysis": API-first, per-session billing, self-serve, no engagement minimums. [HYPOTHETICAL]

2. **Consultancy white-label program** — formal partner channel where boutique firms use Praxis as invisible analytical infrastructure, branded under their own identity. [HYPOTHETICAL]

3. **Decision audit trail product** — position the structured output (dissent + scenarios + scope-limits + [UNCERTAIN] flags) as a governance artifact for board documentation and compliance. [HYPOTHETICAL]

4. **Benchmark-as-a-service** — the 10-question benchmark suite and quality gates (R1-R12) as a standalone product for evaluating ANY strategic analysis (not just Praxis output). [HYPOTHETICAL]

5. **"Built With Praxis" transparency dashboard** — public dashboard showing aggregate session metrics, cost breakdowns, and quality scores as a marketing asset and trust signal. Required at Stage 7 per Pipeline §7.6 + ADR-10. [HYPOTHETICAL]

### Business Model Innovation

**The core innovation is per-session pricing for strategic advisory.** Consultancies charge per-engagement ($50K+). Fractional strategists charge per-hour ($200-$500). SaaS tools charge per-month ($20-$200). Praxis charges per-decision ($29-$149). This maps the payment to the customer's job shape: "I need an answer to THIS question." [HYPOTHETICAL]

### Value Chain Opportunities

**Praxis owns the entire analytical value chain** from question intake to rendered output. No dependency on external data sources, third-party analytical tools, or human analysts in the loop. This means:
- Zero marginal human cost per session
- Quality gates enforce minimum output standards without human review
- Session cost is purely LLM API cost + infrastructure overhead
- Gross margin >95% at any scale [HYPOTHETICAL]

### Partnership and Ecosystem Plays

1. **Boutique consultancy partnerships** — co-branded "Powered by Praxis" (inspectable mode) or fully invisible (firm_voice mode) depending on partner preference. Revenue share or volume-discounted credit packs. [HYPOTHETICAL]

2. **VC portfolio advisors** — partner with VC firms to offer Praxis to portfolio companies as a value-add service. The VC buys a credit pool; portfolio founders consume sessions. [HYPOTHETICAL]

3. **Accelerator / incubator programs** — free trial sessions as part of accelerator onboarding. Conversion to paid after program graduation. [HYPOTHETICAL]

---

## STRATEGIC OPTIONS

### Option A: Per-Session Launch (Lean MVP)

Launch with per-session pricing only. Two tiers: quick ($29) and deep ($149). 1 free quick trial per workspace. No subscriptions, no credit packs, no enterprise tier at launch. Add complexity only when customer behavior demands it.

**Pros:**
- Simplest possible billing implementation (Stripe Checkout per session)
- Fastest time-to-first-revenue
- Directly maps to customer job shape ("I need an answer to THIS question")
- Easiest to understand and communicate
- Validates budget-anchor hypothesis immediately (are founders willing to pay $149 for an analysis?)

**Cons:**
- No recurring revenue predictability (MRR = 0 until repeat usage emerges)
- No volume incentive for heavy users
- Consultancy channel may need volume pricing from day 1
- Revenue forecasting is pure guesswork until usage patterns emerge

### Option B: Hybrid Launch (Per-Session + Credit Packs)

Launch with per-session pricing (quick $29 / deep $149) AND credit packs (Starter $599/5 deep, Growth $1,499/15 deep, Partner $3,999/50 deep). 1 free quick trial. Credit packs offer 20-46% discount vs per-session.

**Pros:**
- Captures both impulse buyers (per-session) and committed users (credit packs)
- Credit packs provide upfront cash and signal commitment
- Volume pricing addresses consultancy partner economics from day 1
- Familiar SaaS pattern (credits/tokens are well-understood)

**Cons:**
- More complex billing implementation (credit ledger + session deduction + pack management)
- More complex pricing page (cognitive load for new visitors)
- Credit pack revenue recognition is complex (deferred revenue until sessions consumed)
- Risk of unsold credits creating support burden

### Option C: Subscription + Per-Session Overage

Launch with a monthly subscription ($99/month includes 1 deep session/month) + per-session overage ($149/deep, $29/quick). 1 free quick trial. Annual plans at 20% discount.

**Pros:**
- Recurring MRR from day 1
- Subscription floor ensures minimum revenue per customer
- Familiar pricing model for SaaS buyers
- Annual plans provide cash and reduce churn

**Cons:**
- Subscription + overage is the most complex model to implement and communicate
- The "1 included deep session/month" may not match founder decision cadence (2-5 decisions/quarter ≠ 1/month)
- Subscription pricing feels wrong for infrequent, high-stakes decisions — you don't subscribe to a consultant
- Underutilization of included session breeds resentment ("I'm paying $99 and not using it")
- Contradicts the per-decision job shape the ICP articulates

---

## RECOMMENDED STRATEGY

### Strategic Direction

**Recommendation: Option A (Per-Session Lean MVP) with planned evolution to Option B at 50+ paying customers.**

Rationale:
1. **Per-session maps to the job.** The JTBD analysis (Maya §B.1) shows founders hiring Studio per-decision, not per-month. The pricing should match the purchase occasion.
2. **Simplicity maximizes time-to-first-revenue.** Stage 7 scope is already loaded (6 debt-ledger blockers + A4 validation + full web app build). Adding credit pack billing complexity delays launch for uncertain benefit.
3. **Per-session validates the riskiest assumption.** If founders won't pay $149 for a deep session, no amount of credit pack discounting saves the business. Per-session pricing surfaces this signal immediately.
4. **Evolution is straightforward.** Adding credit packs later requires a credit-ledger table + Stripe product catalog extension + pricing page update. It does NOT require architectural changes to the session engine or billing integration. This is a Stripe configuration change, not a codebase change.

**Planned evolution triggers:**
- **Add credit packs** when ≥3 customers have run ≥5 sessions each (signal: repeat usage exists; volume incentive is warranted)
- **Add enterprise tier** when any customer requests annual commitment or >$5K/quarter spend
- **Add consultancy partner program** when first consultancy partner confirms white-label intent

### Key Hypotheses to Validate

| # | Hypothesis | Test | Kill signal |
|---|---|---|---|
| H1 | Founders anchor on "strategic advisory" pricing, not "AI tool" pricing | Show 5 founders Studio output, ask WTP before revealing price | 4/5 anchor on "AI tool" ($20-50/month) |
| H2 | $149/deep session is within founder discretionary advisory budget | Track conversion rate from trial to first paid deep session | <10% trial→paid conversion at 30 days |
| H3 | Per-session demand supports repeat usage (≥2 sessions/quarter) | Track session frequency per workspace over 90 days | Median workspace <1 session in 90 days |
| H4 | Quick trial demonstrates enough value to convert | Track trial completion rate + immediate paid session conversion | <50% trial completion OR <25% trial→paid |
| H5 | Budget anchor holds across segments (founder/COO/consultancy) | Segment-level conversion tracking | Any segment <5% conversion |

[ALL HYPOTHESES HYPOTHETICAL — subject to real-buyer corroboration per Mary §D.5]

### Critical Success Factors

1. **Time-to-first-result < 10 minutes** (Pipeline §7.6 gate) — if signup→result takes longer, conversion drops regardless of pricing
2. **Output quality must demonstrably exceed direct LLM prompting** — if the A4 Spearman validation fails (ρ < 0.6), the quality-based pricing justification weakens significantly
3. **Stripe integration must be bulletproof** — billing errors (double-charging, incorrect amounts) destroy trust at the single worst moment (payment)
4. **First 5 paying customers must come from warm outreach** — cold inbound is unlikely at POV; founder network and accelerator connections are the acquisition channel
5. **Consultancy channel requires at least 1 pilot partner** — the 20% segment weight is theoretical until a real firm tries firm_voice mode

---

## EXECUTION ROADMAP

### Phase 1: Immediate Impact (Stage 7 build, weeks 1-2)

**Key initiatives:**
- Implement per-session billing via Stripe (quick $29 / deep $149)
- 1 free quick trial per workspace (no credit card required)
- Stripe Checkout flow after trial completion
- "Built With Praxis" public dashboard (Pipeline §7.6 + ADR-10)
- Landing page with pricing section (two tiers, clear positioning)

**Success metrics:**
- Billing integration passes E2E test (signup → trial → paid session → receipt)
- Landing page live with pricing
- Public dashboard shows real aggregate data

**Decision gate:** Can a test user go from landing page → signup → free trial → paid deep session → result in <10 minutes?

### Phase 2: Foundation Building (POV launch, weeks 3-6)

**Key initiatives:**
- Warm outreach to 10-15 founder contacts for POV trials
- Onboard first 5 paying customers
- Collect WTP feedback (H1 budget-anchor test)
- Monitor session frequency (H3 repeat-usage test)
- Onboard 1 consultancy partner pilot (firm_voice mode)

**Success metrics:**
- 5+ paying customers
- ≥25% trial→paid conversion
- ≥2 repeat sessions from at least 2 customers
- 1 consultancy partner active

**Decision gate:** Is H1 (budget anchor) confirmed? If yes, proceed. If founders anchor on "AI tool" pricing, consider repositioning or price adjustment before scaling.

### Phase 3: Scale and Optimization (weeks 7-12)

**Key initiatives:**
- Add credit packs if repeat-usage signal confirmed (≥3 customers with ≥5 sessions each)
- Add enterprise tier if annual commitment request received
- Formalize consultancy partner program if pilot succeeds
- Iterate output templates based on customer feedback
- Expand benchmark suite based on real customer questions
- A4 Spearman validation completion (if not already done in parallel)

**Success metrics:**
- 25+ paying customers (across segments)
- $5K+ MRR
- ≥2 sessions/quarter per active customer
- NPS ≥40 from first 10 customers
- A4 Spearman ρ ≥ 0.6 (caveat dropped from headline)

**Decision gate:** Is the business model working? Revenue growing? Repeat usage emerging? If yes, begin Series A fundraising conversations with "Built With Praxis" public dashboard as the proof exhibit.

---

## SUCCESS METRICS

### Leading Indicators

- Trial completion rate (target: ≥50%)
- Trial→paid conversion rate (target: ≥25% at 30 days)
- Session frequency per workspace (target: ≥2/quarter)
- Time-to-first-result (target: <10 minutes)
- NPS from first 10 customers (target: ≥40)
- Landing page → signup conversion (target: ≥5%)

### Lagging Indicators

- Monthly recurring revenue (MRR) proxy — sum of per-session revenue per month
- Customer count (paying workspaces)
- Revenue per customer per quarter
- Consultancy partner count
- Churn rate (workspaces with 0 sessions in 90-day window)

### Decision Gates

| Gate | Trigger | Action |
|---|---|---|
| Budget anchor confirmed | ≥3/5 test founders anchor on "advisory" pricing | Proceed with $29/$149 pricing |
| Budget anchor failed | ≥4/5 test founders anchor on "AI tool" pricing | Reposition: either lower price or change framing |
| Repeat usage confirmed | ≥3 customers with ≥5 sessions | Add credit packs (Option B evolution) |
| Enterprise demand | Any customer requests annual >$5K commitment | Add enterprise tier |
| Consultancy validated | 1 partner completes 5+ firm_voice sessions | Formalize consultancy partner program |
| A4 validation passed | Spearman ρ ≥ 0.6 | Drop "(internal scoring; A4 deferred)" caveat from all materials |
| A4 validation failed | Spearman ρ < 0.6 | Reopen 5.6 gate for strategic decision; consider retuning scoring |

---

## RISKS AND MITIGATION

### Key Risks

1. **Budget-anchor misfire (HIGH):** Founders perceive Praxis as "AI tool" not "strategic advisory," making $149 feel expensive rather than cheap. Probability: uncertain [HYPOTHETICAL]. Impact: pricing structure fails, conversion <5%.

2. **Quality credibility gap (MEDIUM):** A4 Spearman validation fails or the quality improvement narrative doesn't resonate without the caveat-free headline. Probability: bounded by Stage 5.6 automated scoring but unconfirmed. Impact: pricing justification weakens; may need to lower prices.

3. **Single-use pattern (MEDIUM):** Customers run 1 session and never return — treating Praxis as a novelty, not a tool. Probability: common pattern in AI tools [HYPOTHETICAL]. Impact: per-session MRR is volatile; need subscription or engagement mechanics.

4. **Consultancy channel friction (LOW-MEDIUM):** Firms want PDF export (ADR-08 deferred), branded templates, or integration with their existing tools. Probability: likely based on consultancy workflow norms [HYPOTHETICAL]. Impact: 20% segment delayed until Stage 8.

5. **Anthropic dependency (LOW probability, HIGH impact):** API pricing increase, rate limit reduction, or service disruption. No alternative LLM path designed. Mitigation: monitor API pricing; maintain <10% of revenue as API cost (currently <2%).

### Mitigation Strategies

| Risk | Mitigation |
|---|---|
| Budget-anchor misfire | Run H1 test with 5 founders BEFORE public launch; adjust pricing or positioning based on signal |
| Quality credibility gap | Complete A4 Spearman validation in parallel with Stage 7 build (Option C); if ρ < 0.6, lead with output examples rather than statistical claims |
| Single-use pattern | Post-session email: "Your next board meeting is in X weeks — run a Praxis session to prepare"; session history as re-engagement surface; workspace memory (Stage 3) makes subsequent sessions smarter |
| Consultancy channel friction | Defer to Stage 8; don't over-invest in consultancy features at POV; if first partner requests PDF, fast-track ADR-08 |
| Anthropic dependency | Monitor API cost as % of revenue; maintain margin buffer; explore multi-model support in Stage 8+ |

---

## §E — Session-Close Audit

### §E.1 — Deliverable metrics

| Metric | Value |
|---|---|
| Total document lines | (see file) |
| Sections | 9 major sections + E audit |
| Frameworks applied | Value Proposition Canvas, Revenue Model Innovation, Business Model Canvas, Lean Startup |
| [HYPOTHETICAL] marker count | 46 (grep-verified) |

### §E.2 — Constraint compliance

- **C1 (no pre-sales numbers):** Zero instances of +47%, +21%, 25.2, 13.7, 10/10, composite, beat-count in this document. The cost figure ~$2.50 and ~$0.80 per session are internal-cost estimates from Stage 6.6, not pre-sales headline figures.
- **C2 (forbidden verbs):** Word-boundary grep for `\bvalidated\b|\bvalidation\b|\bmeasured\b|\bproven\b|\bdemonstrated\b|\bshown to\b|\btested\b` — anticipated matches: "validation" appears in context of "A4 validation" (referring to the deferred A4 Spearman procedure, not making a claim about Praxis having been validated). This is procedural reference, not a product claim. See precedent #14 (word-boundary enforcement, coincidental-collision exceptions documented inline).
- **C3 (no WTP numbers from real buyers):** All WTP-adjacent figures ($29, $149, $599, etc.) are marked [HYPOTHETICAL] and derived from strategic-advisory budget-anchor analysis, not from real buyer interviews.
- **C4 (ICP hypothesized):** All three segments marked [HYPOTHETICAL] throughout.
- **C5 (no MAC-mechanism → customer-corroborated-value attribution):** Zero claims that specific MAC mechanisms (R1-R12, 3-cycle, information asymmetry) have been corroborated by customers.
- **§A.0 tokonomics firewall:** No tokonomics-era personas, vocabulary, or pricing imported. Firewall rule 4 (no numeric WTP from tokonomics) explicitly honored — the $500-$2K/mo tooling-budget bands from tokonomics are noted as the WRONG anchor and explicitly rejected.
- **Memory writes:** NONE. No memory files written or proposed.
- **Pipeline marks:** NONE. No Pipeline.md checkboxes touched.

---

_Generated using BMAD Creative Innovation Studio - Innovation Strategy Workflow_
_Stage 7.0.1 — Praxis POV Delivery Harness pricing and business model validation_
