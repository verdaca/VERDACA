"""Calibration anchors — GENERATED from benchmark-questions.md §5.

**DO NOT EDIT BY HAND.** Regenerate via
``scripts/parse_calibration_anchors.py`` whenever benchmark-questions.md
§5 changes. The SHA256 hash of the canonical structure is recorded in
:data:`CALIBRATION_ANCHORS_SHA256` — any mismatch fails the build at
PR-gate time via :func:`verify_calibration_anchors_sha256`.

Per arch §6.4, every Tier 3 LLM-judge gate prompt embeds the score-2
and score-4 anchors defined here. Each anchor is sourced verbatim from
benchmark-questions.md §5.

Binding anchors:
  - mac/architecture.md §6.4 Calibration Corpus (Req-D)
  - mac/benchmark-questions.md §5 Gate Calibration Anchors (R1–R12)
  - mac/test-strategy.md v0.3 §7.7 CALIBRATION-01..02
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Mapping


@dataclass(frozen=True)
class CalibrationAnchor:
    """One gate's pair of score-2 and score-4 calibration anchors.

    Sourced verbatim from benchmark-questions.md §5. The rationale text
    ("why score 2" / "why score 4") is captured so the judge prompt
    template can surface it to the LLM at Tier 3 evaluation time.
    """

    gate_id: str
    score_2_example: str
    score_2_explanation: str
    score_4_example: str
    score_4_explanation: str


# =============================================================================
# Verbatim from benchmark-questions.md §5 — DO NOT EDIT BY HAND
# =============================================================================


CALIBRATION_ANCHORS: Mapping[str, CalibrationAnchor] = {
    "R1": CalibrationAnchor(
        gate_id="R1",
        score_2_example=(
            "European expansion is the right move for your company given your "
            "strong product-market fit and the growing EU AI services market "
            "projected to reach 40B by 2030."
        ),
        score_2_explanation=(
            "inference stated as fact; market projection stated without basis; "
            "'right move' asserted without labeling as conclusion"
        ),
        score_4_example=(
            "Based on the two EU inbound leads (weak demand signal -- inference, "
            "not validation) and the EU AI services market projections (third-party "
            "projection with 30 percent uncertainty range), our assessment -- which we "
            "treat as a reasoned recommendation, not a forecast -- is that expansion "
            "readiness is not yet confirmed."
        ),
        score_4_explanation=(
            "claims labeled by evidential basis; uncertainty quantified; "
            "conclusion proportional to evidence"
        ),
    ),
    "R2": CalibrationAnchor(
        gate_id="R2",
        score_2_example=(
            "Regarding your question about Europe expansion, here is a "
            "comprehensive analysis of European market dynamics, GDPR "
            "considerations, and competitive landscape..."
        ),
        score_2_explanation=(
            "answers a general European expansion question, not THIS company's "
            "timing decision"
        ),
        score_4_example=(
            "You asked when to expand to Europe. The more precise question is: "
            "what conditions define readiness for this company? We have reframed "
            "accordingly and will answer both."
        ),
        score_4_explanation=(
            "stated question + explicit reformulation both answered (5/5 meta-eval branch)"
        ),
    ),
    "R3": CalibrationAnchor(
        gate_id="R3",
        score_2_example=(
            "This recommendation should be revisited if market conditions change "
            "significantly."
        ),
        score_2_explanation="vague; unmonitorable; no specific signal identified",
        score_4_example=(
            "This recommendation to delay EU expansion changes if: (a) EU inbound "
            "leads exceed 5 qualified enterprise conversations within 60 days "
            "(demand pull validated), OR (b) a direct competitor announces EU "
            "presence with more than 3 customer wins in this category."
        ),
        score_4_explanation=(
            "specific, monitorable, observable invalidation conditions per conclusion"
        ),
    ),
    "R4": CalibrationAnchor(
        gate_id="R4",
        score_2_example=(
            "Some might argue that staying per-seat is more predictable, but "
            "usage-based pricing is the clear market direction and predictability "
            "concerns are outweighed by growth opportunity."
        ),
        score_2_explanation=(
            "the steelman is dismissed in the same sentence it is raised"
        ),
        score_4_example=(
            "The strongest case for staying per-seat: existing customers signed "
            "under per-seat contracts have a legitimate expectation of pricing "
            "model stability; switching mid-contract risks triggering "
            "renegotiation across the entire base; the revenue predictability "
            "of per-seat enables better headcount planning and investor "
            "communication. This is a real constraint that must be addressed "
            "in any transition plan, not dismissed."
        ),
        score_4_explanation=(
            "strongest counterargument included at full fidelity; analysis "
            "engages substantively"
        ),
    ),
    "R5": CalibrationAnchor(
        gate_id="R5",
        score_2_example=(
            "Some stakeholders may prefer the acquisition option due to "
            "speed-to-market concerns."
        ),
        score_2_explanation=(
            "no argument given; no attribution; one sentence"
        ),
        score_4_example=(
            "The engineering team's position -- stated in the product review -- "
            "is that the acquisition target's codebase carries significant "
            "technical debt that will require 6-12 months of refactoring before "
            "integration, eliminating the time-to-market advantage entirely."
        ),
        score_4_explanation=(
            "minority view presented with rigor; reason for dissent stated; "
            "attribution clear; corresponds to positions referenced in task context"
        ),
    ),
    "R6": CalibrationAnchor(
        gate_id="R6",
        score_2_example=(
            "The European SaaS market represents a significant opportunity. "
            "Key players include [list of 12 companies]. Historical European "
            "expansion data shows [3 paragraphs of market statistics]."
        ),
        score_2_explanation=(
            "the actual recommendation appears in paragraph 11; L1 is not dense"
        ),
        score_4_example=(
            "Key Decision: Delay EU expansion until the US conversion rate from "
            "inbound exceeds 25 percent (currently 14 percent). This is the "
            "leading indicator of product-market fit strength sufficient to "
            "support parallel expansion. Three supporting factors follow."
        ),
        score_4_explanation=(
            "L1 dense with decision-relevant signal; key findings prioritized"
        ),
    ),
    "R7": CalibrationAnchor(
        gate_id="R7",
        score_2_example=(
            "Given the market dynamics, the hybrid GTM approach is clearly the "
            "best path forward."
        ),
        score_2_explanation="no reasoning chain; conclusion asserted",
        score_4_example=(
            "The hybrid GTM approach is recommended because: (1) existing "
            "enterprise customers generate 87 percent of ARR and cannot be "
            "abandoned without triggering immediate churn risk; (2) SMB "
            "self-serve requires minimum 6 months of product changes before "
            "generating meaningful ARR; (3) therefore, a phase transition is "
            "structurally required -- pure pivot would create a 6-month revenue "
            "gap that current runway cannot absorb."
        ),
        score_4_explanation=(
            "logic chain followable step-by-step; inference markers present; "
            "logical validity assessable"
        ),
    ),
    "R8": CalibrationAnchor(
        gate_id="R8",
        score_2_example=(
            "We recommend further analysis of the SMB market before committing "
            "to a pivot."
        ),
        score_2_explanation=(
            "no conditional recommendation; pure epistemic cowardice"
        ),
        score_4_example=(
            "Given current information, pursue the hybrid approach: (a) this "
            "week -- freeze new enterprise AE hiring; (b) within 30 days -- "
            "complete SMB product requirements document; (c) within 90 days -- "
            "launch SMB beta to 20 inbound prospects. Revisit if SMB conversion "
            "rate is below 15 percent at 90-day checkpoint."
        ),
        score_4_explanation=(
            "recommendations specific, decisive, traceable to analysis body; "
            "conditional revisit clause present"
        ),
    ),
    "R9": CalibrationAnchor(
        gate_id="R9",
        score_2_example=(
            "Encouragingly, the EU market is showing strong demand signals, and "
            "our product's differentiation makes it ideally suited for European "
            "buyers. The competitive landscape, while present, is manageable..."
        ),
        score_2_explanation=(
            "evaluative language tilts positive; evidence selection skews toward "
            "supporting the recommendation before it is made"
        ),
        score_4_example=(
            "EU inbound leads: 2 qualified conversations in 6 months (base rate "
            "for this stage: unknown; insufficient to conclude demand pull). "
            "Competitive presence: 3 direct competitors with EU offices. GDPR "
            "compliance gap: 4 identified items requiring engineering work "
            "before launch (estimated 8-12 weeks). Expansion readiness: mixed "
            "evidence."
        ),
        score_4_explanation=(
            "conclusion strength proportional to evidence; findings sections "
            "neither narratively biased nor hedged away"
        ),
    ),
    "R10": CalibrationAnchor(
        gate_id="R10",
        score_2_example=(
            "This analysis may not capture all relevant factors. We recommend "
            "ongoing monitoring of market conditions."
        ),
        score_2_explanation="boilerplate; no specific exclusion; no specific blind spot",
        score_4_example=(
            "This analysis did not examine: (a) post-2023 EU regulatory "
            "precedents on AI data processing (relevant but beyond our "
            "regulatory expertise); (b) the specific VAT treatment for this "
            "company's billing structure in Germany and France (requires tax "
            "counsel). Our assessment of EU readiness is therefore conditional "
            "on these two factors receiving independent review."
        ),
        score_4_explanation=(
            "specific scope declaration + specific blind spot attribution; "
            "entity-specific, not boilerplate"
        ),
    ),
    "R11": CalibrationAnchor(
        gate_id="R11",
        score_2_example=(
            "Scenario A: market grows quickly -- revenue reaches 5M. "
            "Scenario B: market grows slowly -- revenue reaches 3M."
        ),
        score_2_explanation=(
            "same recommendation implied; no differentiated decision implications; "
            "scenarios differ only in magnitude"
        ),
        score_4_example=(
            "Scenario A (token deflation over 40 percent/yr): the cost-savings "
            "value proposition becomes irrelevant within 18 months; pivot to "
            "workflow integration moat immediately. Scenario B (deflation "
            "stabilizes 10-20 percent/yr): 36-month window to build data "
            "flywheel; invest in algorithm improvement AND integration depth. "
            "These scenarios imply different investment priorities and are "
            "monitored by tracking quarterly token pricing across major "
            "providers."
        ),
        score_4_explanation=(
            "multiple plausible futures with differentiated decision "
            "implications and observable trigger conditions"
        ),
    ),
    "R12": CalibrationAnchor(
        gate_id="R12",
        score_2_example=(
            "[FINDINGS]: The acquisition target's technology will require 12-18 "
            "months of integration work. [RECOMMENDATIONS]: The acquisition "
            "provides a 6-month time-to-market advantage over the build option."
        ),
        score_2_explanation="direct internal contradiction",
        score_4_example=(
            "[FINDINGS]: Integration timeline estimated at 12-18 months based "
            "on due diligence findings (codebase complexity, API architecture "
            "mismatch). [RECOMMENDATIONS]: The acquisition is recommended NOT "
            "for time-to-market advantage -- findings show this is negligible -- "
            "but for the team acquisition and IP rights to specific algorithms."
        ),
        score_4_explanation=(
            "premises in findings not denied in conclusions; internal "
            "inconsistencies explicitly addressed and resolved"
        ),
    ),
}


# =============================================================================
# SHA256 lock per arch §6.4
# =============================================================================


def compute_calibration_anchors_sha256() -> str:
    """Compute a canonical SHA256 over :data:`CALIBRATION_ANCHORS`.

    Canonicalization: JSON-serialize the dict with sorted keys and no
    whitespace. The result is the byte-stable hash that arch §6.4
    requires be recorded and verified at build time.
    """
    canonical = json.dumps(
        {k: asdict(v) for k, v in sorted(CALIBRATION_ANCHORS.items())},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


CALIBRATION_ANCHORS_SHA256: str = compute_calibration_anchors_sha256()
"""The SHA256 of the canonical anchor structure at build time. When
benchmark-questions.md §5 is regenerated, this value must be updated
via ``scripts/parse_calibration_anchors.py``; any mismatch at runtime
(vs a caller-supplied expected hash) indicates drift."""


def verify_calibration_anchors_sha256(expected: str) -> None:
    """Raise :class:`ValueError` if the current anchor hash doesn't match ``expected``.

    Used by ``tests/mac/benchmark/test_calibration_anchors.py`` at PR-gate
    time to lock the anchors against drift.
    """
    actual = compute_calibration_anchors_sha256()
    if actual != expected:
        raise ValueError(
            f"calibration anchors SHA256 drift: expected {expected!r}, got {actual!r} "
            f"(benchmark-questions.md §5 changed? regenerate via "
            f"scripts/parse_calibration_anchors.py)"
        )


__all__ = (
    "CALIBRATION_ANCHORS",
    "CALIBRATION_ANCHORS_SHA256",
    "CalibrationAnchor",
    "compute_calibration_anchors_sha256",
    "verify_calibration_anchors_sha256",
)
