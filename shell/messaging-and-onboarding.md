# Praxis Studio — Launch Messaging + Onboarding Narrative Arsenal

**Date:** 2026-04-16
**Storyteller:** Sophia (Master Storyteller) — Stage 7.0.2 Elicitation Round 2
**Strategist:** Andrey
**Methodology:** Per Pipeline.md §7.0.2 + §4.5 Quick Reference — (1) Origin Story, (2) Positioning Story, (3) Customer Journey, (4) Pitch Narrative
**Status:** DRAFT v0.1 — all customer reactions, emotional arcs, and behavioral claims are HYPOTHETICAL until real-buyer corroboration per Mary §D.5
**Binding upstream inputs:** `shell/pricing-strategy.md` (7.0.1 Victor, ratified), `studio/customer-language-research.md` (Mary 6.0.1), `studio/empathy-map.md` (Maya 6.0.2), `studio/customer-requirements.md` (6.0.3 ADRs)

---

## ⚠️ §A.0 — INHERITANCE + CONSTRAINTS BLOCK (load-bearing)

**All Stage 6 elicitation firewalls, anti-glossaries, and flag disciplines apply verbatim:**

1. **§A.0 tokonomics firewall** — inherited from Mary 6.0.1. No tokonomics-era personas (VP-Eng / agent-builder CTO / RAG Dir-of-Eng) or vocabulary (compression / token / gateway / proxy / SDK / callback / per-call cost / LLM spend / pip install) in any narrative. Studio's ICP speaks strategic-decision dialect, not cost-engineering dialect.

2. **Producer-vocabulary exclusion** — inherited from Mary §B.7 + §C.4. No multi-agent deliberation, information asymmetry, quality gates R1-R12, 3-cycle iteration, MAC, meta-agent controller, Pi-Mono, Forge, or any internal architecture component name in customer-facing copy. Customers don't say these words.

3. **`[HYPOTHETICAL]` flag discipline** — every customer reaction, emotional state, behavioral claim, and conversion assumption carries a flag.

4. **Stage 5.6 caveat artifact-level elimination** — zero numbers from `mac/pre-sales-report.md` (+47%, +21%, 25.2, 13.7, 10/10, composite, beat-count) appear anywhere in this document. The caveat-drop prevention strategy from Mary/Maya/6.0.3 is preserved: the numbers are absent, not caveated.

5. **C2 forbidden verbs** — word-boundary grep clean for: validated, validation, measured, proven, demonstrated, shown to, tested (in relation to Praxis product claims).

6. **Muted operator-realism register** — inherited from Mary §A.1. All customer-facing copy uses the same register: wry, specific, hedged, risk-aware, uninterested in performing. No hyperbolic marketing language. No "revolutionary" / "game-changing" / "disruptive" / "10x" claims.

7. **Memory writes:** NONE on agent initiative. Pipeline marks: NONE.

---

## §B — Story Type 1: Origin Story ("Built With Praxis")

**Framework:** Origin Story (strategic category)
**Key questions addressed:** What was the spark? What early struggles? What breakthrough? How did it evolve? What's the current mission?

### §B.1 — The Narrative

**The spark:**

Praxis started as a question about questions. We were watching founders make board-level strategic decisions — pricing transitions, capital strategy, competitive responses, market expansion timing — and we noticed the same pattern repeating: the founder asks a single AI model for analysis, gets a confident-sounding answer, and has no way to know what the answer left out. [HYPOTHETICAL — framing anchored on MAC benchmark questions Q1-Q9 customer contexts]

No dissent. No alternative scenarios. No explicit scope-limits on what wasn't analyzed. No falsification conditions that would tell you when to change course. Just a single perspective presented as comprehensive.

**The early struggle:**

We tried to fix this with better prompting. Longer system prompts. Chain-of-thought instructions. "Consider multiple perspectives" appended to every query. The output got longer but not deeper. The fundamental problem isn't the prompt — it's the architecture. A single model asked to steelman both sides of an argument is still one model pretending to disagree with itself. [HYPOTHETICAL — architectural hypothesis, not empirically confirmed with user testing]

**The breakthrough:**

We built it differently. Multiple independent analytical perspectives, each with different information access, forced to engage with each other's conclusions before producing a final output. The dissent isn't manufactured — it emerges from structural disagreement between perspectives that genuinely see different parts of the problem. [HYPOTHETICAL — product description, not empirical claim]

**The self-demonstrating proof:**

Here's the part we're most transparent about: Praxis was built using Praxis. Every architectural decision, every test strategy, every product requirement in the build pipeline was run through the same multi-perspective analysis that the product now delivers to customers. The "Built With Praxis" dashboard shows the aggregate data from that 7-stage build — not cherry-picked highlights, but the full picture, including the decisions where the analysis surfaced uncomfortable conclusions we'd rather not have heard. [HYPOTHETICAL — dashboard design per ADR-10 / Pipeline §7.6; "full picture" claim subject to privacy-safe aggregation constraints]

**The current mission:**

Structured strategic analysis — with genuine dissent, named scenarios, explicit scope-limits, and falsification conditions — at a price point and speed that makes it accessible to any founder making a consequential decision. Not replacing advisors. Making the quality of structured analysis available where it wasn't before. [HYPOTHETICAL — mission statement, not empirically confirmed market response]

### §B.2 — Emotional Arc

| Beat | Emotion | Copy register |
|---|---|---|
| Spark | Recognition — "I've seen this problem" | Specific, observational, no drama |
| Struggle | Honest frustration — "we tried the obvious thing and it didn't work" | Admission of failure, not performance |
| Breakthrough | Quiet confidence — "so we built it differently" | Understated, no "eureka moment" theatrics |
| Proof | Transparency — "we used it on ourselves, here's what happened" | Numbers-available-but-not-flashy, dashboard as proof |
| Mission | Purposeful — "this is what we're doing and who it's for" | Direct, bounded, no world-changing rhetoric |

### §B.3 — Usage Locations

- **Landing page "Our story" section** — medium version (§D.2)
- **"Built With Praxis" public dashboard header** — short version (§D.1)
- **Onboarding email #2 (day 3 post-signup)** — extended version (§D.3)
- **Investor/partner conversations** — extended version with dashboard walkthrough

---

## §C — Story Type 2: Positioning Story (Market Position)

**Framework:** Positioning Story (strategic category)
**Key questions addressed:** What market gap? How uniquely qualified? What makes approach different? Why should audience care? What future enabled?

### §C.1 — The Narrative

**The market gap:**

Right now, if you're a Series A-C founder making a $50K+ decision — pricing transition, capital strategy, market expansion, competitive response — your options look like this: [HYPOTHETICAL — competitive landscape from Victor 7.0.1 §Market Analysis]

You can ask an AI model directly. It's fast and free, and you get a single perspective that sounds authoritative but has no internal quality checks, no dissent, no explicit scope-limits, and no way to know what it didn't consider.

You can hire a consulting firm. You'll get structured analysis with multiple perspectives, but it costs $50K-$150K, takes 4-12 weeks, and has a minimum engagement size that prices out most individual decisions. [HYPOTHETICAL]

You can talk to your advisors. Good advice if you have good advisors, but it's verbal, unstructured, and limited to whoever happens to be in your network.

There's nothing in between. Nothing that delivers the STRUCTURE of consulting-quality analysis (explicit trade-offs, dissent, scenarios, scope-limits) at the SPEED and PRICE of an AI tool. That gap is where Praxis sits. [HYPOTHETICAL — market gap hypothesis, not confirmed]

**What makes the approach different:**

We don't ask one model to "think about multiple perspectives." We run multiple independent analytical perspectives with different information access, then surface where they disagree. The dissent you see in the output isn't a prompt trick — it's a structural feature of how the analysis was produced. When two perspectives with different information reach different conclusions, that disagreement IS the insight. [HYPOTHETICAL — product architecture description]

**Why it matters to each segment:**

For the founder: you get a position you can hold through two quarters without flinching — with the dissent visible so your board sees due diligence, and falsification conditions so you know when to change course. [HYPOTHETICAL — anchored on Mary §A.1 Q6 "a position I can hold"]

For the COO: you get a decision architecture, not a conclusion — factors, weights, trade-offs stated explicitly instead of hidden in the final recommendation. [HYPOTHETICAL — anchored on Mary §A.2 Q3 "trade-offs stated explicitly"]

For the consultancy partner: you get engagement leverage — 12-minute structured analysis that your team frames into firm-voice deliverables, compounding analyst hours instead of replacing them. [HYPOTHETICAL — anchored on Mary §A.3.a + §C.3 "engagement leverage"]

### §C.2 — Positioning Statement (internal reference, not customer-facing copy)

**For** Series A-C founders, mid-market COOs, and boutique strategy consultancies [HYPOTHETICAL segments]
**Who** need structured strategic analysis for consequential decisions
**Praxis Studio is** an analytical service
**That** delivers multi-perspective strategic analysis with explicit dissent, named scenarios, and scope-limits
**Unlike** direct LLM prompting (single-perspective, unstructured) or management consulting ($50K+, weeks-long)
**Praxis** delivers consulting-structure analysis at $29-$149 per session in ~12 minutes [HYPOTHETICAL pricing per Victor 7.0.1]

---

## §D — Story Type 3: Customer Journey (Before/After Onboarding Arc)

**Framework:** Customer Journey (transformation category)
**Key questions addressed:** Before-state struggle? Discovery moment? Implementation? Transformation? New reality?

### §D.1 — Founder Journey (primary, 50% weight)

**Before (the struggle):**

The board meeting is in six weeks. The pricing transition decision is sitting on your desk. Your CFO says one thing, your product team says another, and you've been cycling between two options for a month without new information to break the tie. You tried asking ChatGPT — it gave you a confident answer, but you can't tell if it considered what happens to your existing 200 customers during the migration window. You don't know what it left out. [HYPOTHETICAL — anchored on Mary §A.1 Q1 quotes + Maya §A.1 Thinks]

**Discovery (the moment):**

You open Praxis. There's no signup form to fill out, no sales call to book, no "request a demo" button. OAuth with Google, name your workspace, and you're looking at an intake form. You paste the question that's been on your desk for a month — the real version, with the context your board gave you. [HYPOTHETICAL — onboarding flow per Pipeline §7 requirements 14-15]

**Implementation (the session):**

Twelve minutes. You watch the progress indicator tick through the analysis. The cost counter shows $2.41. When it finishes, you're looking at a brief that starts with a structured summary of what you should do, followed by: the strongest case AGAINST your preferred option (steelmanned, not strawmanned), three named scenarios with specific conditions that would trigger each, a section titled "What this analysis did NOT consider," and an explicit falsification rule — "revisit this decision if X happens." [HYPOTHETICAL — output structure per ADR-01/05/06/07, cost per Stage 6.6 estimates]

**Transformation (what changed):**

The decision didn't change. You were leaning toward the hybrid migration, and the analysis confirms that direction. But now you have something you didn't have before: the dissent is visible, so when a board member asks "did you consider staying on per-seat?" you can show them the steelman. The scenarios are named, so when your CFO says "what if the conversion rate is lower than expected?" you have a pre-analyzed answer. The falsification conditions are explicit, so three months from now, you'll know whether to stay the course or revisit. [HYPOTHETICAL — anchored on Mary §A.1 Q1 context + Maya §B.1 functional job #1]

**New reality:**

You're not making better decisions. You're making the SAME decisions with better supporting structure — decisions that survive scrutiny, that anticipate the follow-up questions, and that have built-in checkpoints for when to change course. The next time a consequential question lands on your desk, you know where to start. [HYPOTHETICAL]

### §D.2 — COO Journey (secondary, 30% weight)

**Before:** A draft decision memo arrives for your approval. The conclusion is "we should acquire." But the memo doesn't distinguish between acquiring the technology, acquiring the team, or acquiring time-to-market — three different deals pointing at different diligence processes. The trade-offs are hidden in the conclusion. [HYPOTHETICAL — anchored on Mary §A.2 Q3]

**After:** You run the acquire-vs-build question through Praxis in decision-framework mode. The output restructures the binary into three conditional tracks, names the five factors that matter most weighted against your specific architecture and team, and flags the thing nobody puts in the model — integration reality, team retention during change, hidden second-order costs. You send the framework back to the team with: "structure the diligence around these three tracks." [HYPOTHETICAL — anchored on Mary §A.2 Q3 + Maya §A.2 Does]

### §D.3 — Consultancy Partner Journey (tertiary, 20% weight)

**Before:** Your analysts spend 20-40 hours producing a 15-page strategic analysis for a client engagement. The engagement economics work, but barely — analyst hours are the constraint on how many engagements the firm can run per quarter. [HYPOTHETICAL — anchored on Mary §C.3 engagement leverage + Victor §Value Chain]

**After:** You run the client's question through Praxis in firm-voice mode with invisible provenance. Twelve minutes, $2.50 internal cost. The output is a structured analysis in your firm's register — muted, professional, no tool branding visible. Your senior analyst spends 3 hours framing and contextualizing, not 20 hours building from scratch. The deliverable density is the same or higher. The engagement economics shift from "we can run 4 engagements per quarter" to "we can run 12." The follow-on engagement closes because the deliverable depth is what the client pays for. [HYPOTHETICAL — anchored on Mary §A.3.a + ADR-09 invisible provenance + ADR-11 register contract]

---

## §E — Story Type 4: Pitch Narrative (Landing Page Hero)

**Framework:** Pitch Narrative (persuasive category)
**Key questions addressed:** Problem landscape? Vision for solution? Proof? Action?

### §E.1 — Hero Section Copy

**Headline:**

> **Strategic analysis with genuine dissent. In minutes, not weeks.**

**Subheadline:**

> Praxis delivers structured multi-perspective strategic analysis — explicit trade-offs, red team dissent, named scenarios, and scope-limits — for $29-$149 per session. Paste your question, get your analysis. [HYPOTHETICAL pricing per Victor 7.0.1]

**CTA:**

> **Run your first analysis free** — no credit card, no demo call, no signup form beyond OAuth.

### §E.2 — "How It Works" Section (5 steps)

1. **Paste your question.** The real version — with the business context, the constraints, the stakeholders involved. The more specific, the more useful the analysis.

2. **Choose your depth.** Quick (~4 minutes, $29) for a first-pass structured alternatives view. Deep (~12 minutes, $149) for full analysis with dissent, scenarios, and falsification conditions. [HYPOTHETICAL pricing]

3. **Watch it work.** Real-time progress indicator. Live cost counter. No black box.

4. **Read the dissent first.** The strongest case against your preferred option, steelmanned by a perspective that had access to the same evidence you did. If the dissent is weak, your direction is strong. If it's strong, you've found what you'd otherwise discover three months into execution.

5. **Act with checkpoints.** Every analysis includes explicit conditions under which the recommendation should be revisited. Decisions don't just have answers — they have expiration conditions.

### §E.3 — Value Proposition Blocks (per segment)

**For founders:**

> You're 6 weeks from a board meeting and the pricing transition decision is sitting on your desk. Your CFO says one thing, your product team says another. You need a structured position you can defend — with the dissent visible so the board sees due diligence, and explicit conditions that tell you when to revisit. [HYPOTHETICAL — anchored on Mary §A.1 Q1]

**For operations leaders:**

> The decision memo on your desk has a conclusion but no visible architecture. You need the five factors that actually matter, weighted against your specific situation, with the trade-offs stated explicitly instead of hidden in the recommendation. [HYPOTHETICAL — anchored on Mary §A.2 Q3]

**For advisory firms:**

> Your analysts spend 20 hours building what Praxis produces in 12 minutes. Run the analysis in your firm's voice with invisible provenance, then spend your analysts' time on framing and judgment — the part clients actually pay for. [HYPOTHETICAL — anchored on Mary §A.3.a + ADR-09]

### §E.4 — Pricing Section Copy

> **Simple pricing. Pay per analysis.**
>
> | | Quick | Deep |
> |---|---|---|
> | **What you get** | Structured alternatives view | Full analysis: dissent, scenarios, falsification conditions |
> | **Time** | ~4 minutes | ~12 minutes |
> | **Price** | $29 | $149 |
>
> **First analysis free.** No credit card required.
>
> Running 5+ analyses per month? [Credit packs save 20-46%.](link) [HYPOTHETICAL — credit packs per Victor 7.0.1 planned evolution, not available at MVP launch]

### §E.5 — "Built With Praxis" Dashboard Section Copy

> **We built Praxis using Praxis.**
>
> Every architectural decision in the 7-stage build pipeline was run through the same analytical process you can buy today. The dashboard below shows the aggregate data — not cherry-picked highlights, but the full picture. [HYPOTHETICAL — dashboard per ADR-10 / Pipeline §7.6]

### §E.6 — Error Messages + Edge Cases (onboarding copy)

**Session failed mid-analysis:**

> Something went wrong during your analysis. We've logged the issue and your session will not be charged. You can retry the same question or start a new one. If this happens again, contact support@praxis.app. [HYPOTHETICAL — error handling per Pipeline §7 risk context item 2]

**Session completed but quality gate flagged:**

> Your analysis is ready, but our quality checks flagged areas where the output may be less structured than usual. The flagged sections are marked. You can read the analysis as-is or re-run at no additional cost. [HYPOTHETICAL — quality gate surface behavior TBD by Winston 7.1]

**Free trial consumed:**

> You've used your free analysis. Your next session costs $29 (quick) or $149 (deep). Connect billing to continue. [HYPOTHETICAL pricing]

**Workspace invitation:**

> [Name] invited you to the [Workspace] workspace on Praxis. Join to view shared analyses and run your own sessions. [HYPOTHETICAL — workspace model per Pipeline §7 requirement 8]

---

## §F — Story Variations (cross-channel adaptations)

### §F.1 — Short Versions (1-2 sentences, social/email subjects)

**Origin:**
> We built Praxis using Praxis. Every decision in the 7-stage build was run through the same multi-perspective analysis you can buy today. [HYPOTHETICAL]

**Positioning:**
> Consulting-structure strategic analysis — explicit dissent, named scenarios, scope-limits — at $29-$149 per session in ~12 minutes. [HYPOTHETICAL pricing]

**Customer journey:**
> Paste a strategic question. Get structured analysis with genuine dissent in 12 minutes. The part that matters most: it tells you when to change course. [HYPOTHETICAL]

**Pitch:**
> Strategic analysis with genuine dissent. In minutes, not weeks. First analysis free. [HYPOTHETICAL]

### §F.2 — Medium Versions (1-2 paragraphs, email body/blog intro)

**Origin:**
> Praxis started as a question about questions. We watched founders make board-level decisions using single-perspective AI output and noticed the same gap every time: no dissent, no alternative scenarios, no explicit scope-limits, no falsification conditions. We tried fixing it with better prompts. It didn't work — the problem isn't the prompt, it's the architecture. So we built multiple independent analytical perspectives that are forced to engage with each other before producing a final output. Then we used the system to build itself — every architectural decision in the 7-stage pipeline was run through the same analysis. The "Built With Praxis" dashboard shows the full picture. [HYPOTHETICAL]

**Positioning:**
> If you're a founder making a $50K+ decision, your options today are: ask an AI model (free, fast, single-perspective, no quality checks), hire a consulting firm ($50K-$150K, 4-12 weeks, structured but expensive), or talk to advisors (good if you have them, verbal and unstructured). There's nothing in between — nothing that delivers consulting-structure analysis at AI-tool speed and price. Praxis fills that gap: structured trade-offs, red team dissent, named scenarios, and explicit scope-limits at $29-$149 per session in ~12 minutes. [HYPOTHETICAL]

### §F.3 — Extended Versions

See §B.1 (Origin), §C.1 (Positioning), §D.1/D.2/D.3 (Customer Journeys), §E.1-E.6 (Pitch) above — each is the extended version for its respective story type.

---

## §G — Onboarding Flow Copy (per Pipeline §7 requirements 14-16)

### §G.1 — Signup Flow (<3 minutes)

**Step 1 — OAuth:**
> Sign in with Google, GitHub, or Microsoft. One click.

**Step 2 — Workspace:**
> Name your workspace. This is where your analyses live.
> `[Text field: "My workspace name"]`
> Skip team invites for now — you can add people later.

**Step 3 — First session prompt:**
> Run your first analysis. It's free and takes about 4 minutes.
>
> **Paste a strategic question you're actually working on.** The more specific the context (your company stage, the decision timeline, who the stakeholders are), the more useful the output.
>
> Or try one of these:
>
> - "We're evaluating a 3-year exclusivity partnership with a distribution partner who has 50K customers. What scenarios should we plan for?" [adapted from MAC benchmark Q4]
> - "Our core value proposition is under pricing pressure from a competitor offering 40% lower. Two enterprise accounts are asking to renegotiate. What position can we hold?" [adapted from MAC benchmark Q6]
> - "The board wants European expansion based on 2 inbound leads. What entity-specific risks are we not seeing?" [adapted from MAC benchmark Q7]

### §G.2 — First Session Experience

**During analysis:**
> Your analysis is running. You'll see the progress and cost in real time.
> Estimated time: ~4 minutes (quick mode).

**After completion:**
> Your analysis is ready.
>
> **Read the dissent section first** — it contains the strongest case against your preferred direction. If the dissent is weak, your direction is strong.
>
> [View Full Analysis] [Download Markdown] [Share Link]

**Post-result prompt:**
> That was your free analysis. Want to go deeper?
>
> A **deep analysis** ($149) adds: full red team dissent, 3+ named scenarios with trigger conditions, explicit scope-limits, and falsification rules that tell you when to revisit.
>
> [Run Deep Analysis — $149] [Maybe Later]

### §G.3 — Second Session (Billing Upsell)

**Trigger:** User clicks "Run Deep Analysis" or starts a new session after trial consumed.

> **Connect billing to continue.**
>
> Praxis charges per analysis — $29 for quick, $149 for deep. No subscription, no commitment. Pay for what you use.
>
> [Connect with Stripe]
>
> Running 5+ analyses per month? Credit packs save 20-46%. [View options] [HYPOTHETICAL — credit packs are planned evolution, may not be available at MVP launch per Victor 7.0.1 Option A recommendation]

---

## §H — Tone + Voice Guidelines

### §H.1 — Register Definition

**Praxis customer-facing copy uses a muted operator-realism register** — inherited from Mary §A.1, enforced by ADR-11 register contract, verified by Studio register-check enforcement.

| Do | Don't |
|---|---|
| Specific, concrete, verifiable claims | Vague superlatives ("revolutionary," "game-changing") |
| Hedged where appropriate ("typically ~12 minutes") | False precision ("exactly 11 minutes 47 seconds") |
| Honest about limitations ("this analysis did NOT consider...") | Overconfident ("the definitive answer") |
| Understated confidence ("it works — here's the data") | Performative confidence ("we're disrupting the industry") |
| Direct, short sentences | Long explanatory chains |
| Customer's vocabulary (see Mary §A/§B/§C glossary) | Producer vocabulary (see §A.0 exclusion list) |

### §H.2 — Register Violations to Watch For

Per ADR-11 drift-marker categories + Studio register-check enforcement:

- **Exclamation marks** in customer-facing copy (except error acknowledgments)
- **Dramatic verbs:** revolutionize, transform, disrupt, unleash, unlock, supercharge
- **Urgency adverbs:** immediately, urgently, critically, absolutely, definitely
- **Superlative claims:** best, fastest, most powerful, only, first-ever
- **Marketing filler:** leverage, synergy, paradigm, scalable solution, cutting-edge

### §H.3 — Per-Channel Tone Adjustments

| Channel | Adjustment |
|---|---|
| Landing page | Slightly warmer than internal docs; still no hyperbole |
| Onboarding flow | Helpful, brief, action-oriented |
| Error messages | Honest, specific, no blame ("something went wrong" not "you broke it") |
| Email notifications | Informational, no urgency language |
| Dashboard copy | Data-forward, minimal prose |
| Investor/partner materials | Same register; let the numbers speak |

---

## §I — Session-Close Audit

### §I.1 — Deliverable Metrics

| Metric | Value |
|---|---|
| Total document lines | (see wc -l) |
| Sections | 9 major sections (A.0 through H) + I audit |
| Story types applied | 4/4 (Origin, Positioning, Customer Journey, Pitch Narrative) |
| [HYPOTHETICAL] marker count | (grep-verified, see spot-check) |
| Channel adaptations | Short (4), medium (2), extended (6), onboarding flow (3 steps), error messages (4) |

### §I.2 — Constraint Compliance

- **C1 (no pre-sales numbers):** Zero instances of +47%, +21%, 25.2, 13.7, 10/10, composite, beat-count. Cost figures ($2.50, $0.80) are internal-cost estimates from Stage 6.6 live demo, not pre-sales headline figures.
- **C2 (forbidden verbs):** Word-boundary grep anticipated clean. "Validation" does not appear in this document in product-claim context.
- **C3 (no real WTP):** All pricing ($29/$149, credit packs) sourced from Victor 7.0.1 and marked [HYPOTHETICAL].
- **C4 (ICP hypothesized):** All three segments flagged [HYPOTHETICAL] throughout.
- **C5 (no MAC-mechanism → customer-corroborated-value attribution):** Product descriptions reference "multiple independent analytical perspectives" and "structural disagreement" — customer-language descriptions of what the product does, not internal mechanism names.
- **§A.0 tokonomics firewall:** No tokonomics-era personas, vocabulary, or pricing imported.
- **ADR-11 register contract:** All customer-facing copy uses muted operator-realism register. Zero exclamation marks in customer-facing sections. Zero dramatic verbs. Zero superlative claims.
- **Memory writes:** NONE.
- **Pipeline marks:** NONE.

### §I.3 — Downstream Binding Outputs for Winston 7.1

Winston 7.1 MUST read this file before designing the shell architecture. The following are binding inputs:

1. **Landing page structure:** Hero (§E.1) → How It Works (§E.2) → Segment value props (§E.3) → Pricing (§E.4) → Built With Praxis (§E.5) → CTA
2. **Onboarding flow:** 3-step signup (§G.1) → first session prompt with sample questions → post-result upsell (§G.2-G.3)
3. **Error message patterns:** §E.6 — session failure, quality gate flag, trial consumed, workspace invite
4. **Tone enforcement:** §H register definition — muted operator-realism, no hyperbole, specific hedged claims
5. **Pricing copy:** $29 quick / $149 deep / 1 free quick trial / credit packs as planned evolution (§E.4)

---

_Story crafted using the BMAD CIS storytelling framework — Stage 7.0.2 Praxis POV Delivery Harness launch messaging and onboarding narrative_
