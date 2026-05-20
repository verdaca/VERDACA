# Register Guide — ADR-11 Muted Operator-Realism Register

**Binding:** studio/architecture.md §4.10, Mary §A.1 customer-language-research.md  
**Enforced by:** `RegisterChecker` in `src/praxis/kernel/studio/register_check.py`  
**Validates:** All Studio customer-facing copy — briefs, decks, executive summaries,
error messages, progress indicators.

---

## The Register Contract (Mary §A.1 verbatim)

> wry, specific, hedged, risk-aware, uninterested in performing. No founder-Twitter
> caricature, no dramatic-stakes language, no urgency performance.

This is the production register for all Studio customer-facing output. It is not
aspirational — it is a contract enforced programmatically by `RegisterChecker` and
validated by the register-check tests (test-strategy §10).

---

## What the Muted Register Sounds Like

**Acceptable (muted, specific, hedged):**

- "The data available suggests a modest advantage in this direction, contingent on Q3 pricing decisions."
- "We did not have access to competitor cost data, which limits the precision of the cost comparison."
- "This scenario becomes live if the partnership terms shift materially within 60 days."
- "The analysis supports this position for the next two quarters, given current market assumptions."

**Not acceptable (founder-Twitter caricature):**

- "This will revolutionize how your team operates."  ← dramatic verb
- "Immediately implement this before competitors catch on."  ← urgency adverb
- "Obviously the right answer is to expand now."  ← condescending pattern
- "This is an incredible opportunity."  ← dramatic adjective

---

## Drift Marker Categories

### Category 1: Exclamation marks in analytical text

Any `!` in analytical copy is a drift marker. Analytical findings, trade-off
assessments, scenario descriptions, and scope-limits text should not contain
exclamation marks.

*Exception:* Quoted text from primary sources (clearly marked as quotes).

### Category 2: Dramatic-stakes verbs

Words that perform urgency, scale, or disruption that the content does not
warrant. Curated list (see `register_check.py` for authoritative list):

> revolutionize, disrupt, transform (as hyperbole), unprecedented,
> game-changing, game changer, paradigm shift, breakthrough, explosive,
> skyrocket, rocket, dominate, crush, obliterate, destroy, massive,
> incredible, amazing, phenomenal, spectacular, unstoppable

**Context matters:** "The strategy aims to disrupt incumbents" is borderline;
"This will disrupt the entire market" is a drift marker. When in doubt, flag it
and let the author decide.

### Category 3: Urgency-performing adverbs

Words that perform urgency where the content doesn't require it:

> urgently, immediately, asap, right away, as soon as possible

**"critical" in non-risk contexts:** The word "critical" is acceptable when
describing a risk, failure mode, or technical severity (e.g., "critical
infrastructure risk"). It is a drift marker when used as an adjective meaning
"very important" in a non-risk context (e.g., "critical opportunity").

### Category 4: Condescending patterns

Phrases that talk down to the reader:

> obviously, clearly you, as anyone knows, it goes without saying,
> needless to say, of course you, simply put, just do, just implement, just use

---

## What the Register Tolerates

- **Hedging language:** "suggests," "may," "appears to," "based on available data"
- **Risk-domain directness:** "This assumption is likely wrong if X happens."
- **Wry distance:** "The strong version of the opposing position is worth holding."
- **Specificity:** Named scenarios with specific trigger dates, named owners, measurable conditions.

---

## Enforcement

`RegisterChecker.check(text: str) → tuple[RegisterViolation, ...]`

Empty tuple = PASS. Any violation = FAIL. Quinn (6.4) validates the curated
drift-marker list against nightly benchmark outputs (STUDIO-T-REG-06).

The curated list in `register_check.py` is Amelia's initial draft (OQ-TS-S3).
Quinn 6.4 may extend or prune based on false-positive and false-negative rates
observed on the 10-question benchmark set.

---

## Stage 7 Extension

The register contract applies to all Studio-facing surfaces. Stage 7 Shell
adds customer-visible error messages, progress indicators, and onboarding copy —
all of which fall under this register contract.
