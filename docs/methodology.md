# PRAXIS BUILD METHODOLOGY — Agent Chain, Elicitation & Model Strategy

**Purpose:** Reusable BMAD methodology for building future projects with Praxis. Documents the agent invocation chain, elicitation framework, and model/thinking strategy that proved effective across 7 stages.

**Related docs:**
- [Pipeline Index](pipeline.md) — links to all split documents
- [Pipeline Stages](pipeline-stages.md) — historical build record with all checkboxes
- [Operations](operations.md) — gate conditions, file paths, handoff protocol
- [Session Log](session-log.md) — chronological session history

---

## SECTION 4: AGENT INVOCATION CHAIN (QUICK REFERENCE)

Per-stage agent sequence varies. Some stages require ELICITATION rounds before Winston can design meaningfully — see Section 4.5 for details.

### Standard 6-Step Pattern (Stages 1 only — pure technical)

```
Step 1: /bmad-agent-architect     (Winston — design)
Step 2: /bmad-tea                 (Murat — test strategy)
Step 3: /bmad-agent-dev           (Amelia — implementation)
Step 4: /bmad-qa-generate-e2e-tests  OR  /bmad-testarch-automate   (Quinn — test execution)
Step 5: /bmad-review-adversarial-general  (alignment review)
Step 6: Manual checkpoint (pre-sales metric capture)
```

### Extended Pattern with Elicitation + Clean Code Review (Stages 2-7)

```
Step E1:  Elicitation Round 1      (domain-specific BMAD skill, before OR after Winston)
Step E2:  Elicitation Round 2      (if stage requires it)
Step E3:  Elicitation Round 3      (Stages 5 and 6 only)
---- (Output: requirements doc at <stage>/requirements.md) ----
Step 1:   /bmad-agent-architect          (Winston — design, now grounded in elicitation output)
Step 2:   /bmad-tea                      (Murat — test strategy)
Step 3:   /bmad-agent-dev                (Amelia — implementation)
Step 3.5: /bmad-agent-clean-code-reviewer (Cleo — clean code review, CRITICAL gate)
Step 4:   Quinn — test execution
Step 5:   Alignment review
Step 6:   Pre-sales checkpoint
```

**Clean code review (Step 3.5) is a hard gate:** Quinn does NOT run tests on code with unresolved CRITICAL violations. Cleo either auto-fixes or the issues return to Amelia before Quinn starts. This prevents "tests pass on bad code" — a class of silent failures where technically working code has architectural smells that break later.

**Rule:** Always complete Step N before starting Step N+1 within a stage. Always complete all steps of Stage N before starting Stage N+1. Elicitation steps are NOT optional — skipping them leads to product-market fit failures that don't surface until launch.

---

## SECTION 4.5: ELICITATION FRAMEWORK PER STAGE

Elicitation transforms UNCERTAIN product/business questions into CERTAIN requirements that Winston can design against. Without it, Winston must invent answers to questions only the market can answer.

### Elicitation Need Matrix

| Stage | Need | Rounds | Position | Why |
|-------|------|--------|----------|-----|
| 1 — Pi-Mono | LOW | 0 | — | Technical requirements are clear |
| 2 — Compression | MODERATE | 1 | AFTER Winston | Validate quality/compression tradeoff philosophy |
| 3 — Memory | HIGH | 2 | BEFORE Winston | Privacy, retention, governance are product decisions |
| 4 — Runtime | HIGH | 1 | BEFORE Winston | Tool library curation needs customer use case input |
| 5 — MAC | **CRITICAL** | 3 | BEFORE Winston | Quality rubric IS the entire business case |
| 6 — Studio | HIGH | 3 | BEFORE Winston | Customer language & output format decide PMF |
| 7 — POV Harness | HIGH | 2 | BEFORE Winston | Pricing, messaging, onboarding are business decisions |

### Stage 2 — Compression (1 round, AFTER Winston)
- **Round:** `/bmad-advanced-elicitation`
- **Focus:** Quality tolerance threshold for compression fall-back
- **Input to the round:** Winston's draft compression architecture
- **Questions:** At what quality loss % do we fall back to uncompressed? How do we measure quality loss? What's the consequence hierarchy (cost vs quality vs latency)?
- **Output:** `_bmad-output/implementation-artifacts/praxis/compression/requirements-validation.md`

### Stage 3 — Memory (2 rounds, BEFORE Winston)
- **Round 1:** `/bmad-advanced-elicitation`
  - Focus: Multi-tenant privacy model
  - Questions: SMB single-tenant? Enterprise strict isolation? Cross-customer learning opt-in? GDPR posture? Data residency?
- **Round 2:** `/bmad-cis-problem-solving` (Dr. Quinn)
  - Focus: Adversarial analysis of retention/governance risks
  - Questions: What happens on customer deletion? Right-to-erasure? Experience library poisoning risk? Multi-tenant leakage attack surface?
- **Output:** `_bmad-output/implementation-artifacts/praxis/memory/requirements.md`

### Stage 4 — Runtime (1 round, BEFORE Winston)
- **Round:** `/bmad-brainstorming` (Carson)
- **Focus:** Tool library curation via customer use case brainstorming
- **Questions:** What external systems do strategic advisory customers already use? Which 20% of integrations create 80% of value? What are "table stakes" tools vs "nice to have"?
- **Output:** `_bmad-output/implementation-artifacts/praxis/runtime/tool-library-requirements.md`

### Stage 5 — MAC (3 rounds, BEFORE Winston) — **CRITICAL**

This is the highest-stakes elicitation in the entire pipeline. The quality rubric defined here becomes the measurement Praxis is built to satisfy. Skipping this means building something technically perfect that fails PMF.

- **Round 1:** `/bmad-brainstorming` (Carson)
  - Focus: Define "strategic analysis quality" via creative brainstorming
  - Questions: What makes analysis GREAT vs mediocre? Comprehensiveness? Dissent preservation? Risk identification? Actionability? Honesty about uncertainty?
  - Output: Draft quality dimensions
- **Round 2:** `/bmad-cis-problem-solving` (Dr. Quinn)
  - Focus: Red team the draft quality rubric
  - Questions: Where do false positives hide (accept bad output)? Where do false negatives hide (reject good output)? What's the failure mode of each proposed gate?
  - Output: Hardened quality dimensions
- **Round 3:** `/bmad-advanced-elicitation`
  - Focus: Finalize benchmark questions + scoring protocol
  - Questions: Which 10 benchmark strategic questions will validate MAC quality? Who scores them? Blind vs open evaluation?
  - Output: `_bmad-output/implementation-artifacts/praxis/mac/quality-rubric.md` + `benchmark-questions.md`

### Stage 6 — Studio (3 rounds, BEFORE Winston)
- **Round 1:** `/bmad-market-research` (Mary)
  - Focus: Customer language discovery for strategic advisory
  - Questions: How do real customers phrase strategic questions? Industry jargon? Budget context? Who is the buyer?
  - Output: Draft customer persona + language patterns
- **Round 2:** `/bmad-cis-design-thinking` (Maya)
  - Focus: Empathy mapping — what customers actually want
  - Questions: Emotional state when asking? Outcome they need to defend to stakeholders? Format they share internally?
  - Output: Empathy map + journey map
- **Round 3:** `/bmad-advanced-elicitation`
  - Focus: Finalize Studio output format contracts
  - Questions: Brief length? Deck format? Dissenting views prominence? Export formats? Shareable links?
  - Output: `_bmad-output/implementation-artifacts/praxis/studio/customer-requirements.md`

### Stage 7 — POV Harness (2 rounds, BEFORE Winston)
- **Round 1:** `/bmad-cis-innovation-strategy` (Victor)
  - Focus: Pricing model + business model validation
  - Questions: Per-session vs subscription vs credit packs? Trial policy? Enterprise upgrade path? Price points? Free tier dynamics?
  - Output: Pricing strategy doc
- **Round 2:** `/bmad-cis-storytelling` (Sophia)
  - Focus: Launch messaging + onboarding narrative
  - Questions: Opening pitch? "Built With Praxis" story? Onboarding copy? First-session walkthrough? Error messages?
  - Output: `_bmad-output/implementation-artifacts/praxis/shell/messaging-and-onboarding.md`

### Quick Reference: Specific Methods Per Round

Instead of picking arbitrary methods from the skill's menu, use these exact selections:

| Stage | Round | Skill | Primary Method | Why This One |
|-------|-------|-------|----------------|--------------|
| 3 | 1 | `/bmad-advanced-elicitation` | **Stakeholder Round Table** | Multi-persona debate for privacy model |
| 3 | 2 | `/bmad-cis-problem-solving` | **Failure Mode Analysis** + **Risk Matrix** | Adversarial analysis of governance failures |
| 4 | 1 | `/bmad-brainstorming` | **Role Playing** + **Six Thinking Hats** | Tool curation from customer personas |
| **5** | **1** | `/bmad-brainstorming` | **First Principles Thinking** + **Values Archaeology** + **Reverse Brainstorming** | Defining quality from fundamentals |
| **5** | **2** | `/bmad-cis-problem-solving` | **Failure Mode Analysis** + **Assumption Busting** + **TRIZ Contradictions** | Red-teaming the rubric |
| **5** | **3** | `/bmad-advanced-elicitation` | **Comparative Analysis Matrix** + **ADRs** + **Thesis Defense Sim** | Selecting benchmark questions |
| 6 | 1 | `/bmad-market-research` | **Voice of Customer protocol** | Verbatim language discovery |
| 6 | 2 | `/bmad-cis-design-thinking` | **Empathy Mapping** + **JTBD** + **Journey Mapping** + **How Might We** | Customer emotional/functional needs |
| 6 | 3 | `/bmad-advanced-elicitation` | **ADRs** + **User Persona Focus Group** + **Critique and Refine** | Format contract finalization |
| 7 | 1 | `/bmad-cis-innovation-strategy` | **Value Proposition Canvas** + **Revenue Model Innovation** + **BMC** + **Lean Startup** | Pricing + business model validation |
| 7 | 2 | `/bmad-cis-storytelling` | **Origin Story** + **Positioning Story** + **Customer Journey** + **Pitch Narrative** | Launch messaging arsenal |

**Why specific methods (not generic skill invocation):** Each BMAD elicitation skill contains 20-60 methods. Without explicit selection, agents pick "whatever feels right" — which produces shallow generic output. The specific methods above are chosen for fit with that stage's actual decision type.

### Elicitation Output Rules

1. **Every elicitation round produces a document.** No verbal-only sessions.
2. **Winston reads elicitation outputs BEFORE designing.** He references them in the architecture doc.
3. **Elicitation outputs are binding during the stage.** If Winston disagrees, he raises it back — does NOT silently override.
4. **Elicitation docs live alongside architecture docs** in `_bmad-output/implementation-artifacts/praxis/<component>/`.
5. **Multi-round elicitation builds on itself.** Round 2 starts by reading Round 1 output; Round 3 reads both.
6. **Elicitation outputs feed Pipeline.md Session Log.** Add a brief summary of key decisions made.

---

## SECTION 4.6: MODEL & THINKING EFFORT STRATEGY

Every step from Stage 2.3 onwards has an assigned model and thinking level. This is an annotation, not a hard override — you can escalate or downgrade if the situation demands it, but defaults are tuned for cost/quality balance.

### Model Cheat Sheet

| Model | Cost (per 1M tokens in/out) | Thinking available | When to use |
|-------|----------------------------|-------------------|-------------|
| **Opus 4.6** | $5 / $25 | Yes (adaptive, no premium) | Architecture, strategy, red team, alignment, complex reasoning, high-risk components |
| **Sonnet 4.6** | $3 / $15 | Yes (adaptive, no premium) | Implementation, standard test design, code review, documentation, routine execution |
| **Haiku 4.5** | $1 / $5 | None | Simple lookups, classification, format conversions (rarely used in Praxis build) |

### Thinking Level Cheat Sheet

| Level | Token budget | When to use |
|-------|-------------|-------------|
| **minimal** | 128 | Simple lookups |
| **low** | 256 | Single-step problems |
| **medium** | 1024 | Multi-step chains, code review, standard test writing |
| **high** | 4096 | Complex reasoning, architecture design, implementation of non-trivial components |
| **max** | 8192+ | Open-ended research, adversarial red team, multi-stakeholder decision capture, highest-risk components (Stage 5 MAC) |

### Role → Default Allocation

| Role | Default Model | Default Thinking | Rationale |
|------|--------------|------------------|-----------|
| Winston (Architect) | Opus 4.6 | high → max (Stage 5) | Architecture is the most costly decision to get wrong |
| Murat (Test Architect) | Opus 4.6 (→ Sonnet for later stages) | high → max (Stage 5) | Risk-based strategy demands deep reasoning; Sonnet OK when risks are well-understood |
| Amelia (Developer) | Sonnet 4.6 (→ Opus for Stage 5) | high | Implementation is multi-step but pattern-following; MAC complex enough to justify Opus |
| Cleo (Clean Code Reviewer) | Sonnet 4.6 | medium | Pattern-matching against standards; deep reasoning not needed except for Stage 5 |
| Quinn (QA Engineer) | Sonnet 4.6 (→ Opus for Stage 5) | medium → high | Test writing is pattern-heavy; MAC tests demand Opus |
| Alignment Review | Opus 4.6 | high → max (Stage 5) | Cross-document consistency analysis is always complex |
| Pre-Sales Checkpoint | Sonnet 4.6 | low → medium | Mostly metric capture + narrative; Opus for launch checkpoint |
| Elicitation rounds | Opus 4.6 | high → max (Stage 5) | Product decisions with long-lasting consequences |

### Stage-Level Intensity Profile

| Stage | Intensity | Rationale |
|-------|-----------|-----------|
| 2 Compression | MEDIUM | Well-understood domain, code porting |
| 3 Memory | HIGH | Privacy/governance stakes |
| 4 Runtime | HIGH | Security model + 16 agents |
| **5 MAC** | **MAX** | **Core differentiation; every step at highest level** |
| 6 Studio | HIGH | PMF decisions |
| 7 POV Harness | HIGH | Customer-facing trust stakes |

### Override Guidance

- **Escalate** (e.g., Sonnet→Opus, medium→high): when a task surprises you with complexity, or when the first attempt produces shallow output
- **Downgrade** (e.g., Opus→Sonnet, high→medium): when a task turns out to be pattern-matching that the LLM handles easily; saves cost
- **Log overrides** in the Session Log (Section 9) so future sessions understand why you deviated

### 1M Context Window Strategy — CRITICAL

**Problem:** Claude's default context is 200k tokens, with compaction triggering around 128k. After compaction, output quality degrades. Steps that require reading:
- Multiple large reference .txt dumps (3-12 MB each = 750k-3M tokens)
- Multiple prior stage architecture docs + test strategies + requirements
- Plus full source directories for review

...will hit 200k quickly and lose fidelity.

**Solution:** Explicitly invoke Claude with 1M context window for the affected steps.

**Model variants to use:**
- **Sonnet 4.6 [1M]** — Sonnet 4.6 with 1M context window enabled
- **Opus 4.6 [1M]** — Opus 4.6 with 1M context window enabled
- Default (no [1M] tag) — 200k context window (cheaper on rate limits)

**When to use [1M]:**
- Amelia implementing against multiple large reference dumps (Stages 2, 3, 4, 5, 7)
- Winston designing against multiple reference dumps + prior stage docs (Stages 3, 4, 5, 6, 7)
- Murat reading Winston arch + reference dumps (Stages 3, 4, 5)
- Cleo reviewing large source trees (Stages 2, 3, 4, 5, 7)
- Alignment Review reading ALL prior architecture docs (Stages 2-7)
- Quinn running adversarial tests on MAC (Stage 5 only)

**When NOT to use [1M]:**
- Elicitation rounds (focused discussion, rarely exceed 50k context)
- Pre-sales checkpoints (metric capture, minimal context)
- Quinn QA in Stages 2-4, 6, 7 (test execution, fits in 200k)
- Stage 6 Studio implementation (mostly YAML + Jinja2, small footprint)

**Rate limit impact (Max $100 plan — Max 5x, ~225 messages per 5hr window):**
- 1M context messages count ~5x against the ITPM/OTPM budget
- Expect to burn through hourly quota faster when using [1M] variants
- Plan sessions accordingly — don't stack multiple 1M context operations back-to-back
- If you hit rate limits, downgrade non-critical steps to standard context or wait for window reset

### UNIVERSAL RULE: Sequential Reference Reading

**Applies to:** ANY step where multiple large reference .txt dumps or prior stage architecture docs must be consulted.

**The rule:** **Read ONE reference at a time. Process it fully. Clear context. Read the next.** Do NOT attempt to load all references simultaneously — even with 1M context, the raw reference material often exceeds the window, and cramming multiple dumps degrades attention quality on each one.

**Why it matters:** Even 1M context is not enough for:
- Stage 2 references: TONL 3MB + Forge 4.8MB + RTK 1.9MB + Caveman 210KB = **2.5M tokens**
- Stage 3 references: Beads + Mem0 **7.8MB** + Atelier 3.3MB = **3M tokens**
- Stage 4 references: Gas Town **12MB** + Atomic Agents 1.7MB + Atelier 3.3MB = **4.5M tokens**
- Stage 5 integration: ALL prior stage architectures + Atelier + Forge patterns = **3M+ tokens**

**How to apply it (Amelia / developer pattern):**
1. Read Winston's architecture doc first (small, defines scope)
2. Pick the FIRST reference you need per architecture
3. Read it fully, extract relevant patterns as notes
4. Implement ONE component
5. Run the component's tests
6. Commit (or mark complete in checklist)
7. Start fresh: read the SECOND reference
8. Repeat

**How to apply it (Winston / architect pattern):**
1. Read the previous stage's architecture doc first (small, defines integration points)
2. Read the highest-priority reference dump
3. Draft the architecture section that uses it
4. Clear context, read the next reference
5. Draft the next architecture section
6. Final pass: integration sections that tie everything together

**How to apply it (Alignment Reviewer pattern):**
1. Read one prior stage's architecture at a time
2. Take notes on invariants: data models, API surfaces, language choices
3. Only after reading all prior architectures, read the CURRENT stage's architecture
4. Compare against accumulated notes, flag inconsistencies

**Steps where this rule is MANDATORY (explicit reminder in checklist):**
- Stage 2: 2.3 Amelia
- Stage 3: 3.1 Winston, 3.3 Amelia
- Stage 4: 4.1 Winston, 4.3 Amelia
- Stage 5: 5.1 Winston, 5.2 Murat, 5.3 Amelia, 5.5 Alignment (reads ALL prior stages)
- Stage 6: 6.1 Winston (reads elicitation + Tokonomics rounds + Stage 5 MAC)
- Stage 7: 7.1 Winston, 7.3 Amelia
