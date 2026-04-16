# Strategic Analysis Quality Dimensions — Draft Rubric

**Stage:** Praxis 5.0.1 — Elicitation Round 1  
**Produced by:** Carson (brainstorming specialist)  
**Methods used:** First Principles Thinking → Values Archaeology → Reverse Brainstorming  
**Date:** 2026-04-14  
**Status:** DRAFT — input to Stage 5.0.2 (Dr. Quinn red-team) and Stage 5.1 (Winston MAC architect)

---

## Q1/Q3 Scoping Constraints (Applied)

- **Q1 resolved**: Dimensions are **universal across task types** (code review, market research, strategy). Tier 1 gates are universal. Per-workflow specialization happens via gate weights, not new dimensions. MAC differentiation claim is task-agnostic.
- **Q3 resolved**: 14 dimensions produced. D14 flagged as collapse candidate. Winston collapses to 12 gates; this document ranks and flags which to collapse.
- **Q2 deferred**: Scorer identity (human vs. LLM-judge vs. blind third party) is a Stage 5.6 protocol question. Not reflected in these dimensions.

---

## Section 1: Quality Dimensions Catalog

### D1 — Epistemic Calibration

**Definition:** Claims are labeled by their evidential basis (observed fact / inference / assumption / speculation); confidence language is proportional to evidence quality — not prose quality.

**First Principles Basis:** Analysis exists to update belief under uncertainty. Without distinguishing fact from inference from assumption, the recipient cannot calibrate trust. Presenting all claims with equal confidence is epistemically fraudulent regardless of how correct the conclusions turn out to be.

**Value It Serves (Values Archaeology):** Elena (COO, $50M bet) specifically valued "every assumption had a label." Marco (founder, bad advice) felt the report "didn't earn its confidence." Unstated value: people want to know WHERE they should trust more and WHERE they should probe.

**Inverse Failure Mode (Reverse Brainstorming):** **Confidence washing** — inferences stated in the same authoritative voice as facts; assumptions buried in prose rather than labeled. The reader finishes the analysis believing it is more certain than it is.

**Single-Agent Gap:** Single-agent systems routinely confidence-wash — the model generates inferences fluently, and fluency creates false certainty. Without a reviewer who did not see the producer's reasoning, this goes unchallenged.

**How to Measure:**
- Count labeled vs. unlabeled major claims
- Check whether confidence language ("will," "likely will," "may," "could under conditions X") tracks evidential strength
- Proxy: presence/absence of an explicit Assumptions section

**Tension with other dimensions:** T3 — Epistemic Calibration in tension with Actionability Calibration. Rigorous uncertainty labeling can paralyze; a decision-maker sometimes needs a confident recommendation even when the evidence is ambiguous. The dimension measures calibration, not maximum confidence.

**Gate tier assignment:** Tier 1 (rule-based partial: check for assumption section presence); Tier 3 (LLM-judge: assess whether confidence language tracks evidence quality)

---

### D2 — Question Fidelity

**Definition:** Analysis answers the actual question posed — including flagging when the question itself may be the wrong question to ask.

**First Principles Basis:** The MAP must match the TERRITORY. An analysis that answers a proxy question — even brilliantly — fails the decision-maker. This is the most common single-agent failure: the model answers the question it can answer most fluently, not the question posed.

**Value It Serves (Values Archaeology):** David (consultant, fired) said "the client asked for competitive analysis. They needed market intelligence. I gave them what they asked for." The full version of Question Fidelity includes the obligation to surface when the stated question is not the right question.

**Inverse Failure Mode (Reverse Brainstorming):** **Easiest question bias** — the analysis answers a question similar to but easier than the one posed, without signaling the substitution. Or: the analysis frames the question as a pretext rather than a target.

**Single-Agent Gap:** A single agent anchors to its training distribution. "Should we expand to Europe?" becomes "here is what I know about European expansion" — the specific decision (should THIS company expand NOW given THESE constraints) becomes the frame, not the target.

**How to Measure:**
- Alignment check: does the stated question appear in the conclusion section with a direct answer?
- Scope audit: does the analysis address the specific entity/context or a generic version of the question?
- Best-practice: does the analysis flag if the stated question may be incomplete or misframed?

**Tension with other dimensions:** Low — Question Fidelity is orthogonal to most other dimensions. Minor tension with Actionability Calibration: faithfully answering "should we?" sometimes requires saying "that's not the right question" which feels un-actionable.

**Gate tier assignment:** Tier 1 (rule-based: does the conclusion section contain a direct answer to the stated question?); Tier 2 (retrieval: compare to similar past tasks — is the question mapping consistent?)

---

### D3 — Falsifiability / Invalidation Clarity

**Definition:** Conclusions specify what evidence would overturn them; the analysis is testable, not merely assertable.

**First Principles Basis:** Any analysis that cannot specify what evidence would overturn its conclusions is not analysis — it is advocacy wearing analysis clothes. Falsifiability is the line between opinion and reasoning. This is not a philosophical nicety; it is practically necessary because conditions change, and the decision-maker needs to know when to revisit the conclusion.

**Value It Serves (Values Archaeology):** Marco said "they recommended Europe but never told me what would make them change their mind." The implicit need: a conclusion with invalidation conditions is an *ongoing* analytical tool, not a one-time deliverable. The decision-maker can monitor whether invalidation conditions are being triggered.

**Inverse Failure Mode (Reverse Brainstorming):** **Assertion masquerading as analysis** — the conclusion is stated confidently, and no conditions under which it would be revisited are given. The analysis becomes unfalsifiable, and therefore untrustworthy when conditions shift.

**Single-Agent Gap:** Single agents almost never include invalidation conditions unless explicitly prompted. The conclusion is stated; what would falsify it is not. There is no reviewer to demand "what would change your mind?"

**How to Measure:**
- Presence check: does each major conclusion have at least one stated invalidation condition?
- Quality check: are invalidation conditions specific and testable, or vague ("if market conditions change")?

**Tension with other dimensions:** T3 — Falsifiability in tension with Actionability Calibration. Extensive invalidation conditions can make a recommendation feel hedged and uncommitted. The dimension measures presence and quality of invalidation conditions, not how many are listed.

**Gate tier assignment:** Tier 1 (rule-based: presence of invalidation conditions per conclusion); Tier 2 (retrieval: compare to past high-quality analyses — do their invalidation conditions have this level of specificity?)

---

### D4 — Steelman Completeness

**Definition:** The strongest counterarguments to the main conclusions are included at full fidelity — not as straw men to dismiss.

**First Principles Basis:** A decision-maker needs the best case against the conclusion, not a weakened version easily knocked down. Without this, the analysis is advocacy. The steelman requirement is the structural guarantee that opposition receives proportional representation.

**Value It Serves (Values Archaeology):** Elena's best-ever analysis included a formal minority view section with the dissenting team members' best argument. She valued this because it told her where the analysis was vulnerable and what she would need to watch. The steelman is a form of epistemic respect — it signals confidence through engagement, not dismissal.

**Inverse Failure Mode (Reverse Brainstorming):** **The straw man counter** — counterarguments are present but are weakened versions: "Some might argue X, but this ignores Y." The "X" is not the strongest version of the argument. A knowledgeable reader who holds the opposing view would recognize the misrepresentation.

**Single-Agent Gap:** Single agents generate arguments and counterarguments from the same mind with the same priors. The counterarguments section is weaker than the argument section by construction — the model's prior pulls toward the conclusion it already generated. Information asymmetry (reviewer who didn't see the producer's reasoning) is the structural fix. This dimension is where MAC adds the most value over single-agent.

**How to Measure:**
- Steel test: would a knowledgeable person who holds the opposing view recognize their best argument in the counterargument section?
- Weight parity: is the counterargument given proportional space and rigor to the argument?
- Proxy: does the analysis explicitly label the "strongest objection" or equivalent?

**Tension with other dimensions:** T2 — Steelman Completeness in tension with Dissent Preservation. Steelman is about argument quality (best version of opposing view); Dissent is about perspective completeness (all significant views represented). A 5/5 on both is achievable; a 1/5 on one often implies weakness in the other.

**Gate tier assignment:** Tier 3 (LLM-judge only — requires understanding whether an argument is the strongest version of a position; not rule-checkable)

---

### D5 — Dissent Preservation

**Definition:** Minority views are represented accurately and with proportional weight; the analysis does not collapse to the majority position.

**First Principles Basis:** Multi-agent deliberation adds value precisely when it preserves genuine disagreement. If the final output converges to consensus, the multi-agent process produced the same result a single agent would. Dissent Preservation is the anti-conformity dimension — it is the mechanism that makes the MAC's deliberation meaningful.

**Value It Serves (Values Archaeology):** Elena valued the explicit minority view section: "Two team members thought we were wrong. The report included their best case, not a dismissal." Unstated value: the decision-maker wants to know who disagreed and why — because those people may be right, or may surface something useful in post-decision monitoring.

**Inverse Failure Mode (Reverse Brainstorming):** **Perspective selection bias** — only the views of people who agree with the conclusion are reported. Or: minority views are represented so briefly that they appear marginal when they are substantive.

**Single-Agent Gap:** A single agent has no genuine internal disagreement — it generates one perspective from its single prior. Any "alternative views" it produces are manufactured, not preserved from a separate reasoning process. Multi-agent dissent is structurally generated, not manufactured.

**How to Measure:**
- Presence check: is there an explicit section or labeled paragraph representing minority/dissenting views?
- Attribution check: are dissenting views attributed to specific reasoning (even if anonymous) rather than "some believe"?
- Weight check: do dissenting views receive proportional space relative to how significant the disagreement is?

**Tension with other dimensions:** T2 — Dissent Preservation in tension with Decision Clarity (not listed as a separate dimension but relevant to Actionability Calibration). Vigorous dissent preserved in the output can make the recommendation feel ambiguous. Resolution: dissent is preserved in a clearly labeled section; the recommendation section is still decisive.

**Gate tier assignment:** Tier 1 (rule-based: presence of dissent/minority section); Tier 3 (LLM-judge: assess whether minority views are faithfully represented or strawmanned)

---

### D6 — Decision Relevance Density

**Definition:** Content is ranked by decision relevance; padding is minimized; key findings are explicitly prioritized so the signal is not buried.

**First Principles Basis:** Not all true information is decision-relevant. An analysis padded with context that doesn't bear on the decision wastes cognitive budget and buries signal. The measure is: what proportion of the content directly affects the decision at hand?

**Value It Serves (Values Archaeology):** Elena could explain the 40-page analysis in 5 minutes — because the key findings were clearly prioritized, not buried. Marco felt the analysis was "comprehensive" but the decision-relevant content was hard to locate.

**Inverse Failure Mode (Reverse Brainstorming):** **Research theater** — the analysis demonstrates extensive research effort through volume. Competitor lists, market statistics, historical context — all accurate, all largely irrelevant to the specific decision. The reader finishes feeling informed but not helped.

**Single-Agent Gap:** Single agents pad — they fill context with evidence of effort rather than signal. A separate reviewer who must evaluate the output faces research theater without a producer's explanation of what matters most.

**How to Measure:**
- Priority marking: are the top 3-5 findings explicitly flagged as key?
- Proportion test: what percentage of the total word count directly bears on the decision? (proxy: ratio of findings/recommendations to background/context)
- Executive summary quality: if an executive summary is present, does it contain the decision-critical content?

**Tension with other dimensions:** T1 — Decision Relevance Density in tension with Comprehensive scope requirements. More coverage means more content, which dilutes density. Resolution: density is measured relative to the scope, not as an absolute word count.

**Gate tier assignment:** Tier 1 (rule-based: presence of explicit priority markers for key findings); Tier 3 (LLM-judge: assess whether background content is proportional to decision-relevance)

---

### D7 — Risk Specificity

**Definition:** Risks identified are specific to this entity/situation; not generic category risks the reader already knows.

**First Principles Basis:** Risk identification is a core function of analysis — but generic risks ("regulatory compliance," "market competition") are already known to any competent decision-maker. The value-add is identifying risks specific to this company, this timing, this move. Generic risks confirm the analysis was done; specific risks add information.

**Value It Serves (Values Archaeology):** Marco said the risks listed were generic — every European expansion faces "regulatory compliance." The risks specific to HIS company (EU VAT incompatibility with SaaS pricing, thin Berlin hiring market for his tech stack) were never mentioned. The risk section added zero information.

**Inverse Failure Mode (Reverse Brainstorming):** **Category-generic risk listing** — risks that any competent reader would list from memory. If a risk section could be copy-pasted into a competitor's analysis without change, it failed Risk Specificity.

**Single-Agent Gap:** Single agents retrieve risks from training data — their risks are heavily weighted toward common, well-documented, high-frequency risks. Entity-specific risks require specific context retrieval and reasoning that single agents underweight. Multi-agent with retrieval from Memory (Stage 3) specifically addresses this.

**How to Measure:**
- Specificity test: could each risk be copy-pasted into a generic report in this category? If yes, it fails.
- Entity-specific test: does each major risk reference specific attributes of this entity (their pricing model, their team, their current customer base)?

**Tension with other dimensions:** Low. Risk Specificity is a specialized flavor of Decision Relevance Density — specific risks are more decision-relevant. Minor tension with Scenario Coverage: broad scenario analysis may surface generic risks across futures that are category-level.

**Gate tier assignment:** Tier 3 (LLM-judge — requires evaluating whether a risk is generic or specific; not rule-checkable; requires understanding of the entity)

---

### D8 — Reasoning Traceability

**Definition:** The logic chain from evidence to conclusion is followable step-by-step; no black-box conclusions; each major inference is explicit.

**First Principles Basis:** If a reviewer cannot follow the reasoning, they cannot (a) catch errors, (b) extend the logic to new situations, or (c) update selectively when new evidence arrives. An untraced conclusion is a black box that fails completely when assumptions change.

**Value It Serves (Values Archaeology):** Elena's analysis was traceable — it made the $50M bet communicable to her board. Reasoning Traceability is what enables Extractable Logic (D14) — the chain must exist before it can be extracted.

**Inverse Failure Mode (Reverse Brainstorming):** **Black-box conclusion** — "Therefore, you should expand to Europe" stated without a followable reasoning chain. The reader must trust the conclusion without understanding it.

**Single-Agent Gap:** Single agents compress reasoning under context pressure. Long reasoning chains get summarized, premises get elided, inferential steps get skipped in favor of conclusions. MAC's Cycle 3 verification requires the chain to be intact for the reviewer to evaluate. The Forge compression layer in Stage 2 specifically preserves reasoning chains — this dimension is what that engineering decision was optimizing for.

**How to Measure:**
- Trace test: can a reviewer reconstruct the argument from evidence to conclusion without filling in gaps?
- Explicit inference markers: presence of "therefore," "because," "given that," "which implies" connecting evidence to conclusions
- Step-count proxy: number of explicit reasoning steps between a piece of evidence and the conclusion that depends on it

**Tension with other dimensions:** T4 — Reasoning Traceability in tension with Decision Relevance Density. Full chain tracing increases length; density optimization reduces it. Resolution: the chain is traced at the level required for verification, not at maximum verbosity.

**Gate tier assignment:** Tier 2 (retrieval: compare against high-traceability past analyses); Tier 3 (LLM-judge: assess whether the chain is complete)

---

### D9 — Actionability Calibration

**Definition:** Recommendations are specific enough to guide the next concrete action; avoid epistemic cowardice ("recommend further analysis"); avoid over-prescription that removes decision-maker agency.

**First Principles Basis:** Analysis must close the gap between "situation understood" and "next concrete action." Two failure modes: too vague (epistemic cowardice — hedge with "further research needed" to avoid being wrong) and too prescriptive (over-specification — prescribes implementation details the decision-maker is better positioned to determine).

**Value It Serves (Values Archaeology):** Marco needed to know what to do on Monday. Elena needed recommendations she could present to her board. Both valued a specific enough recommendation to act on, not instructions that assumed her board knew nothing.

**Inverse Failure Mode (Reverse Brainstorming):** **Epistemic cowardice** — "We recommend further analysis before committing." This is the most recognized failure of strategic analysis; it protects the analyst from being wrong while protecting no one who needed a decision.

**Single-Agent Gap:** Single agents over-hedge under uncertainty — they recognize their epistemic limits and respond with excessive caution. A second agent in reviewer mode, seeing only the output and not the producer's uncertainty trail, can push back on hedging that doesn't serve the decision.

**How to Measure:**
- Concreteness test: does each major recommendation specify a next action (not just a direction)?
- Epistemic cowardice check: does the analysis defer to "further research" where a recommendation was possible?
- Over-prescription check: do recommendations leave decision-maker agency on implementation intact?

**Tension with other dimensions:** T3 — Actionability Calibration in tension with Epistemic Calibration. Rigorous uncertainty labeling can make recommendations feel hedged. T3 is real: resolution requires a section structure where uncertainty is labeled in findings and recommendations are still decisive in conclusions.

**Gate tier assignment:** Tier 1 (rule-based: presence of actionable recommendations section; absence of "recommend further analysis" without accompanying action); Tier 3 (LLM-judge: assess whether recommendations are appropriately specific)

---

### D10 — Structural Impartiality

**Definition:** The analysis does not narratively favor one outcome; evidence selection, framing, and sequencing are neutral with respect to the conclusion.

**First Principles Basis:** Analysis is trusted when the conclusion is reached via evidence, not selected to support a predetermined conclusion. Structural Impartiality means the analysis would be indistinguishable from one a genuine skeptic produced — no thumb on the scale.

**Value It Serves (Values Archaeology):** Marco felt the analysis was "written FOR European expansion." The vocabulary, the evidence sequence, the framing of counterarguments — all signaled a predetermined conclusion. The unstated value: decision-makers want analysis they can trust even when the analyst disagrees with them.

**Inverse Failure Mode (Reverse Brainstorming):** **Confirmation-bias-as-analysis** — tell the client what they want to hear. Weight evidence selection, argument structure, and framing toward the conclusion the audience is predisposed to accept.

**Single-Agent Gap:** A single agent, given a prompt that implies a preferred answer, will often generate analysis that supports it. There is no reviewer with a different prior to push back on the framing. Structural impartiality requires a separate reviewer who evaluates the analysis independent of the producer's framing.

**How to Measure:**
- Frame audit: does the introduction/framing section imply a preferred conclusion before evidence is presented?
- Evidence balance: is supporting evidence given proportionally more space/prominence than opposing evidence?
- Language audit: does evaluative language ("unfortunately," "encouragingly," "despite") tilt in one direction?

**Tension with other dimensions:** Mild tension with Actionability Calibration — a decisive recommendation can appear to favor one outcome. Resolution: the recommendation section is allowed to be decisive; the analysis sections preceding it must be impartial.

**Gate tier assignment:** Tier 3 (LLM-judge — requires detecting subtle framing bias; not rule-checkable)

---

### D11 — Scope Transparency

**Definition:** Explicitly states what was examined AND what was not; search boundaries are visible to the reader.

**First Principles Basis:** An analysis can only be trusted to the extent its coverage is visible. "There are three main competitors" does not tell the reader how many competitors were considered, what search method was used, what time horizon was covered, what geographies were included. The recipient is making decisions based on findings, but the reliability of findings depends on search scope.

**Value It Serves (Values Archaeology):** David's failure: "I was comprehensive within my boundaries. I never questioned whether my boundaries were right." The repair is not just to widen scope — it is to make scope explicit so the reader can assess whether the boundaries were appropriate.

**Inverse Failure Mode (Reverse Brainstorming):** **Invisible scope** — the analysis reports findings without reporting coverage. A reader who assumes comprehensive coverage but receives partial coverage will make decisions based on systematically incomplete information.

**Single-Agent Gap:** Single agents report findings; they do not report coverage. They have no introspective mechanism to surface "I searched for X but not for Y, which may be relevant." A reviewer evaluating the output cannot assess coverage reliability without this information.

**How to Measure:**
- Scope declaration: presence of explicit section stating what was and was not covered
- Search method transparency: are information sources and methods identified?
- Boundary justification: are scope boundaries explicitly justified ("we focused on North America because...")?

**Tension with other dimensions:** Low. Scope Transparency is independent of most quality dimensions — it's a metadata property of the analysis, not a quality property of the reasoning.

**Gate tier assignment:** Tier 1 (rule-based: presence of explicit scope/methodology section)

---

### D12 — Unknown Unknown Acknowledgment

**Definition:** The analysis actively identifies what it might be missing even within its stated scope; explicitly acknowledges where expertise or search methodology may create blind spots.

**First Principles Basis:** Known unknowns ("we don't know X") are relatively easy to surface. Unknown unknowns ("we don't know what we don't know") require active epistemic effort — deliberately searching for the shape of the gap, not just the content of what was found.

**Value It Serves (Values Archaeology):** David's failure was epistemic: "I knew the space well. That's why I missed it. I was mapping the world I knew." Expertise creates coverage blind spots. Quality analysis names this explicitly: "our deep familiarity with established competitors may have led us to underweight emerging ones."

**Inverse Failure Mode (Reverse Brainstorming):** **Closed-world assumption** — the analysis presents what was found as if it represents everything that exists. No acknowledgment that the search might have missed something systematically. The reader mistakes "we found nothing" for "nothing exists."

**Single-Agent Gap:** A single agent has no mechanism to step outside its own search process and ask "what am I systematically missing?" A reviewer with a different background, reading the output, can surface "there's a whole category of risk you haven't mentioned." This requires information asymmetry.

**How to Measure:**
- Acknowledgment presence: does the analysis explicitly name categories of information it may have missed?
- Bias naming: does it identify where the analyst's perspective or method may create systematic gaps?
- "What would change this" test: does it name what kind of additional information would most improve confidence?

**Tension with other dimensions:** Adjacent to D11 (Scope Transparency). Scope Transparency reports what was examined; Unknown Unknown Acknowledgment extends further to what might exist beyond the examination. Collapse candidate for Winston: could merge into a single "Epistemic Scope Honesty" dimension.

**Gate tier assignment:** Tier 2 (retrieval: compare to past analyses — does this one acknowledge blind spots that similar analyses have needed to flag?); Tier 3 (LLM-judge: assess quality of blind spot identification)

---

### D13 — Scenario Coverage

**Definition:** Analysis covers multiple plausible futures with differentiated implications; includes trigger conditions under which the recommendation changes.

**First Principles Basis:** Strategic decisions are made under irreducible uncertainty about which future obtains. An analysis that provides one expected-case scenario is treating an uncertain future as if it were deterministic. The decision-maker needs to know: what changes if the key assumptions are wrong?

**Value It Serves (Values Archaeology):** Marco never received information about what would make the Europe recommendation wrong. Elena's analysis included monitoring indicators — effectively, implicit scenario coverage. The Decision Trigger Clarity need from Values Archaeology is captured here: scenarios come with conditions under which the recommendation changes.

**Inverse Failure Mode (Reverse Brainstorming):** **Single-scenario confidence** — "The market will grow 15%." No range, no alternative scenario, no trigger conditions. The decision-maker has no frame for what to do when the expected case doesn't materialize.

**Single-Agent Gap:** Single agents default to expected-case analysis. Generating genuinely differentiated alternative scenarios requires reasoning that is adversarial to the primary thesis — which a single agent with one prior generates weakly. Multi-agent with dedicated scenario generation adds structural diversity.

**How to Measure:**
- Scenario count: at least base + one alternative (optimistic or pessimistic); best practice is base + upside + downside
- Differentiation test: do the scenarios have meaningfully different implications, or are they variations of the same outcome?
- Trigger condition presence: for each scenario, is there a specified condition under which this scenario becomes more likely?

**Tension with other dimensions:** T5 — Scenario Coverage in tension with Decision Relevance Density. Multiple scenarios increase length. Resolution: scenarios add decision-relevant content (not padding) by definition; the tension is real but resolvable by limiting scenario count.

**Gate tier assignment:** Tier 1 (rule-based: presence of multiple scenarios with labeled triggers); Tier 2 (retrieval: compare scenario differentiation quality against past examples)

---

### D14 — Extractable Logic *(COLLAPSE CANDIDATE)*

**Definition:** The core reasoning chain can be extracted and communicated to a non-specialist by the decision-maker, without losing the essential logic.

**First Principles Basis:** An analysis that cannot be communicated onward by the recipient has limited leverage. Strategic decisions require stakeholder alignment — the decision-maker must be able to say "here's why" in a board meeting, a budget review, a team briefing. If the reasoning lives only in the analysis document and cannot be compressed into a communicable form, the analysis produced a conclusion without transferring understanding.

**Value It Serves (Values Archaeology):** Elena's standout analysis: "I could explain it to my board in 5 minutes even though it was 40 pages. The structure made the logic portable." This is distinct from length or simplicity — a complex analysis can have extractable logic; a simple analysis can fail this.

**Inverse Failure Mode (Reverse Brainstorming):** **Reasoning that requires reading the full document to understand.** The board meeting version collapses to "trust us, the analysis showed." No logic transferred.

**Single-Agent Gap:** Partially. Single agents produce analysis primarily for the direct reader; communicability downstream is rarely optimized. However, this dimension may be more a property of deliverable format than of reasoning quality per se.

**Winston's Decision:** Should this be:
- A Stage 5 MAC quality gate (reasoning quality dimension)?
- A Stage 6 Studio format requirement (deliverable format spec)?

**Recommendation:** If the MAC's Cycle 3 evaluates reasoning quality independent of format, this dimension belongs in Stage 6. If the reasoning chain itself must be structured to enable extraction, this dimension belongs in Stage 5. **Flag for Winston to decide.**

**Gate tier assignment (if kept):** Tier 3 (LLM-judge: can a non-specialist follow the core logic?)

---

## Section 2: Dimension Prioritization

**Top 5 most critical for MAC's 12 gates:**

| Rank | Dimension | Why Most Critical |
|---|---|---|
| **#1** | D4 — Steelman Completeness | WHERE multi-agent adds most value over single-agent; the information asymmetry reviewer exists specifically to catch what the producer's reasoning missed; if this gate doesn't fire, the MAC's architectural advantage is unrealized |
| **#2** | D1 — Epistemic Calibration | Universal across all task types; foundational to all other quality assessments; if calibration fails, no other dimension's score is meaningful; cheap to partially evaluate at Tier 1 |
| **#3** | D5 — Dissent Preservation | Directly addresses the MAC's anti-conformity failure mode; the most likely failure mode of a well-functioning multi-agent system is that it converges to consensus and produces a confident answer that is structurally identical to a single-agent answer |
| **#4** | D2 — Question Fidelity | Highest signal-to-noise at Tier 1 (cheapest to check: does the conclusion section answer the stated question?); if the MAC answers the wrong question, no amount of quality on the remaining dimensions matters |
| **#5** | D8 — Reasoning Traceability | Required for MAC's Cycle 3 verification and experience library write-back; if the reasoning chain is not traceable, the reviewer cannot verify it, and the learning loop cannot extract what worked; directly supports the Forge compression integration |

**Collapse candidates (flagged for Winston):**

- **D11 + D12** → potential collapse into **"Epistemic Scope Honesty"** (one gate: what did we cover and what might we be missing?) — saves one of the 12 gate slots
- **D14** → potential move to Stage 6 Studio format spec (not a MAC gate at all)

**Remaining 8 dimensions (D3, D6, D7, D9, D10, D13 + collapsed D11/12 + one of the top 5)** form the balance of the 12-gate catalog. Priority ordering for gate slots 6-12: D9 > D3 > D13 > D10 > D6 > D7 > D11/D12 combined.

---

## Section 3: Measurement Protocol — Top 5 Dimensions

### D4 — Steelman Completeness (1–5)

| Score | Criteria |
|---|---|
| **1** | No counterarguments present; only supporting evidence. The analysis reads as advocacy. |
| **2** | Counterarguments present but weakened versions (straw men). A knowledgeable opponent would not recognize their best argument. |
| **3** | Some real counterarguments included; the strongest argument for the opposing view is partially represented but not at full fidelity. |
| **4** | The strongest counterargument is included with full representation. The analysis engages with it substantively rather than dismissing it. |
| **5** | Multiple steelman counterarguments; each is the genuine best case for the opposing view; the analysis explicitly responds to the strongest version of each; shows what evidence would change the conclusion. |

**What distinguishes 4 from 5:** At 4, the analysis includes the counterargument and addresses it. At 5, the analysis credits the counterargument's full strength even where it isn't resolved — "this remains a legitimate concern even if we conclude X."

---

### D1 — Epistemic Calibration (1–5)

| Score | Criteria |
|---|---|
| **1** | All claims stated with uniform confidence; no distinction between facts and assumptions; confident language throughout regardless of evidence quality. |
| **2** | Some hedging present but inconsistent; major inferences stated as facts in key sections; confidence language doesn't track evidence quality. |
| **3** | Most major claims labeled; some assumptions implicit in prose; hedging present but not systematically applied to all inferential leaps. |
| **4** | All major claims labeled with evidential basis; confidence language proportional to evidence; explicit assumptions section or equivalent. |
| **5** | Every claim labeled; uncertainty quantified where possible (ranges, confidence intervals, or explicit probability language); the reader can distinguish at a glance between fact, inference, and assumption throughout. |

**What distinguishes 4 from 5:** At 4, labeling is present and proportional. At 5, it is systematic and quantified where applicable.

---

### D5 — Dissent Preservation (1–5)

| Score | Criteria |
|---|---|
| **1** | Single viewpoint presented as if universal; no acknowledgment that other perspectives exist. |
| **2** | Acknowledges other views exist but doesn't represent them ("some disagree," without content); dissent is a footnote. |
| **3** | Minority views summarized accurately but briefly; not straw-manned but given minimal weight relative to their actual significance. |
| **4** | Minority views presented with the same rigor as majority views; attribution clear (even if anonymous); reader can evaluate the dissenting case independently. |
| **5** | Explicit dissent section with the dissenting position's best argument; dissent given proportional representation relative to how significant the disagreement is; reader can form their own judgment; the analysis does not tell the reader what to think about the dissent. |

**What distinguishes 4 from 5:** At 4, the dissent is present and accurate. At 5, it is structurally equal — the reader is not steered toward dismissing it.

---

### D2 — Question Fidelity (1–5)

| Score | Criteria |
|---|---|
| **1** | Analysis answers a different question than posed; the stated question appears as a pretext or frame; conclusion doesn't address the decision. |
| **2** | Analysis partially addresses the question; significant scope drift; related but not identical question answered with confidence. |
| **3** | Analysis addresses the main question; some off-target content present; conclusion provides a direct answer but with gaps on sub-questions. |
| **4** | Analysis directly answers the stated question; all major sub-questions addressed; conclusion is unambiguously responsive to the decision posed. |
| **5** | Analysis answers the stated question AND assesses whether the stated question was the right question; flags if the question was incomplete, misframed, or answering it would be insufficient for the actual decision. |

**What distinguishes 4 from 5:** At 4, the analysis answers the question. At 5, it meta-evaluates the question.

---

### D8 — Reasoning Traceability (1–5)

| Score | Criteria |
|---|---|
| **1** | Conclusions stated without reasoning; the path from evidence to conclusion is entirely absent; black-box output. |
| **2** | Some reasoning present; major inferential gaps between evidence and conclusion; key steps missing. |
| **3** | Main reasoning chain present; some inferential leaps compressed; a careful reader can reconstruct most of the logic but must fill in some gaps. |
| **4** | Complete reasoning chain present; every major conclusion traced to premises; inferential steps explicit; a reviewer can verify each step independently. |
| **5** | Numbered or explicitly labeled reasoning steps; each premise is independently checkable; the chain from evidence → inference → conclusion is formally complete; a separate reviewer with no access to the producer's notes can fully evaluate the logic. |

**What distinguishes 4 from 5:** At 4, the chain is complete but integrated into narrative. At 5, the chain is explicit enough to evaluate step by step without re-reading the surrounding context.

---

## Section 4: Open Questions for Winston

**OQ-1 — Collapse decision for D11 + D12:**
Should Scope Transparency (D11) and Unknown Unknown Acknowledgment (D12) merge into a single "Epistemic Scope Honesty" gate? They are conceptually adjacent (what was examined vs. what might be missing despite examination). Merging saves one of the 12 gate slots. Risk: merging loses the measurement precision — scope reporting (rule-checkable at Tier 1) and blind spot identification (LLM-judge at Tier 3) are evaluated very differently.

**OQ-2 — D14 placement:**
Should Extractable Logic belong in Stage 5 MAC quality gates or Stage 6 Studio format specifications? Recommendation in this document: Stage 6. But if Winston determines that the MAC's reasoning structure must be designed for extractability from the start, this becomes a Stage 5 constraint.

**OQ-3 — Tier assignment for D10 (Structural Impartiality):**
D10 is Tier 3 only (LLM-judge) — it requires detecting subtle framing bias. Is this too expensive for inclusion in every cycle's Cycle 3 verification? Should it be sampled (periodic evaluation) rather than applied to every output?

**OQ-4 — Scenario count floor:**
D13 (Scenario Coverage) requires "at least base + one alternative." Is this floor appropriate for all task types (e.g., code review), or should it be per-workflow-template configuration (strategic analysis: base+upside+downside; code review: pass/fail)?

**OQ-5 — Gate weighting model:**
The 12 gates need weights for the overall quality score calculation. Should all gates have equal weight, or should the Top 5 (D1, D2, D4, D5, D8) have higher weights? This affects the +15-25% improvement claim measurement and should be decided before the benchmark evaluation harness is built.

**OQ-6 — Bootstrapping the quality rubric:**
The MAC uses Memory to retrieve "similar past high-quality analyses" for Tier 2 gates. But initially, there are no past analyses in Memory. How does the rubric bootstrap? Does the 5.6 benchmark set (10 questions + gold standard answers) seed the initial experience library?

---

## Section 5: Tension Summary (for Winston's Gate Design)

| Tension | Dimensions | Implication for Gate Design |
|---|---|---|
| T1 | D6 (Density) vs. Comprehensiveness (implicit) | Set density threshold relative to scope, not absolute word count; don't penalize comprehensive scope |
| T2 | D4 (Steelman) vs. D5 (Dissent) | Different gates; D4 = quality of counterargument, D5 = presence of minority views; both can fire independently |
| T3 | D1 (Calibration) vs. D9 (Actionability) | Separate sections in output structure: calibrated findings + decisive recommendations; gate each section type differently |
| T4 | D8 (Traceability) vs. D6 (Density) | Traceability threshold set at "verifiable chain," not maximum verbosity; summarized chain counts if checkable |
| T5 | D13 (Scenarios) vs. D6 (Density) | Scenarios are decision-relevant by definition; density gate should not fire on scenario content |
| T6 | D8 (Traceability) vs. D12 (Unknown unknowns) | Both require explicit meta-reasoning about reasoning; could be co-located in a "reasoning quality" section |

---

*Document produced by: Carson (bmad-brainstorming specialist)*
*Next: Stage 5.0.2 — Dr. Quinn red-teams this rubric via Failure Mode Analysis + Assumption Busting + TRIZ*
*Then: Stage 5.0.3 — Advanced elicitation finalizes benchmark question set*
*Then: Stage 5.1 — Winston anchors MAC's 12 quality gates on this rubric*
