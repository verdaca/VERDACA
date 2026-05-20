"""Studio domain objects — intermediate and output representations.

These dataclasses carry structured data between the MAC output parser,
the Jinja2 template renderer, and the A/B comparison harness.

Binding anchors:
  - studio/architecture.md §4 Output Template Contracts
  - studio/test-strategy.md §14.3 Reasoning Trace Fixture Contract
  - ADR-01: four-feature backbone (trade_offs, dissent_frames, scenarios, scope_limits)
  - ADR-03: brief length band
  - ADR-04: deck format
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from praxis.kernel.studio.schema import ProvenanceMode, RenderingMode


# ---------------------------------------------------------------------------
# ADR-01 four-feature backbone components
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TradeOff:
    """One trade-off factor (arch §4.1, ADR-01 Structured Trade-offs)."""

    factor: str
    """Name of the trade-off factor."""

    weight: float
    """Relative importance weight (normalized 0–1 or absolute score)."""

    alternatives: tuple[str, ...]
    """Alternative options compared on this factor."""

    recommendation: str
    """Which alternative is recommended on this factor, and why."""


@dataclass(frozen=True)
class DissentFrame:
    """One competing frame (arch §4.5, ADR-05 Dissent Rendering).

    Must contain all four required sub-fields per STUDIO-T-TPL-DISSENT-02.
    """

    frame_name: str
    steelman: str
    """Strongest version of the competing position — from the reviewer agent."""

    evidence: str
    """Specific evidence supporting this frame from the reasoning trace."""

    conditions: str
    """Conditions under which this frame becomes the recommendation."""

    confidence: str
    """Rubric score comparison vs. recommended frame (ADR-05 §D fold-back)."""


@dataclass(frozen=True)
class Scenario:
    """One named scenario (arch §4.6, ADR-06 Scenario Rendering).

    Must contain all three required sub-fields per STUDIO-T-TPL-SCENARIO-02.
    """

    name: str
    trigger: str
    """What makes this scenario live."""

    invalidation: str
    """What falsifies this scenario."""

    decision_rule: str
    """What to do if the trigger fires — includes owner + date (COO fold-back)."""


@dataclass(frozen=True)
class ScopeLimits:
    """Three-category scope-limits structure (arch §4.7, ADR-07).

    Each category must have ≥ 1 entry per STUDIO-T-TPL-SCOPE-02.
    """

    data_gaps: tuple[str, ...]
    """Specific data the analysis did not have access to."""

    adjacent_questions: tuple[str, ...]
    """Specific follow-on analyses out of scope (one per item, not open-ended)."""

    invalidating_assumptions: tuple[str, ...]
    """Specific assumptions — if wrong, the recommendation changes."""


@dataclass(frozen=True)
class Recommendation:
    """One top-level recommendation."""

    text: str
    confidence: str
    """Confidence signal per ADR-05 §D."""


# ---------------------------------------------------------------------------
# Composite reasoning trace — test-strategy §14.3
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReasoningTrace:
    """Studio-internal structured representation of MAC deliberation output.

    Carries the parsed sections from the [FINDINGS]/[DISSENT]/[SCENARIOS]
    labeled text, ready for Jinja2 template rendering. In Tier 1 tests this
    is constructed directly from fixture data without a real MAC call.
    """

    trade_offs: tuple[TradeOff, ...]
    """≥ 1 entry (R1 comprehensiveness)."""

    dissent_frames: tuple[DissentFrame, ...]
    """≥ 1 entry with all 4 sub-fields (R5 dissent, ADR-05)."""

    scenarios: tuple[Scenario, ...]
    """≥ 2 entries with 3 sub-fields each (R6 scenario coverage, ADR-06)."""

    scope_limits: ScopeLimits
    """3 sub-categories, each ≥ 1 entry (R9 scope-awareness, ADR-07)."""

    recommendations: tuple[Recommendation, ...]
    """Final recommendations."""

    rendering_mode: RenderingMode
    provenance_mode: ProvenanceMode

    composite_score: float = 0.0
    """0–100 composite score from MAC gate evaluation."""

    gate_scores: dict[str, int] = field(default_factory=dict)
    """gate_id → effective_score (1–5). Populated after MAC evaluation."""

    backtrack_count: int = 0
    cost_usd: float = 0.0


# ---------------------------------------------------------------------------
# Output and session containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateScores:
    """Per-gate scores for one output (used by A/B harness scoring)."""

    scores: dict[str, int]
    """gate_id → score (1–5)."""

    composite: float
    """0–100 weighted composite."""

    backbone_completeness: dict[str, bool]
    """section_name → present. Four keys: trade_offs, dissent, scenarios, scope_limits."""

    register_compliant: bool
    """Whether the register-check passed."""


@dataclass(frozen=True)
class RenderedOutput:
    """Result of one TemplateRenderer.render() call.

    Binding: studio/architecture.md §4 (all template contracts).
    """

    text: str
    """Fully rendered content after provenance-mode strip."""

    format: Literal["markdown", "html"]
    rendering_mode: RenderingMode
    provenance_mode: ProvenanceMode

    word_count: int
    """Approximate word count of the rendered text."""

    register_violations: tuple[str, ...]
    """Drift markers found. Empty tuple = register PASS."""

    @property
    def register_pass(self) -> bool:
        return len(self.register_violations) == 0


@dataclass(frozen=True)
class SessionResult:
    """Result of a full StudioSession.invoke() call."""

    outputs: tuple[RenderedOutput, ...]
    """One RenderedOutput per OutputSpec in the WorkflowTemplate."""

    composite_score: float
    gate_scores: dict[str, int]
    backtrack_count: int
    cost_usd: float
    duration_seconds: float
    rendering_mode: RenderingMode
    mode: Literal["deep", "quick"]

    @property
    def degraded(self) -> bool:
        """True when the session hit the budget ceiling before completing."""
        return any("DEGRADED" in o.text for o in self.outputs)


# ---------------------------------------------------------------------------
# A/B harness containers — arch §6
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunResult:
    """Scores and metrics for one path in the A/B comparison (arch §6.2)."""

    path: Literal["single_agent", "enhanced_single_agent", "studio"]
    question_id: str
    output_text: str
    gate_scores: GateScores
    cost_usd: float
    duration_seconds: float
    word_count: int


@dataclass(frozen=True)
class ComparisonReport:
    """Full A/B comparison report (arch §6.4 format)."""

    headline: str
    per_question_rows: tuple[dict, ...]
    """Each row: question_id, studio_score, baseline_score, enhanced_score, cost_ratio, time_ratio."""

    per_gate_rows: tuple[dict, ...]
    """Each row: gate_id, studio_avg, baseline_avg, delta."""

    dissent_analysis: str
    """R5-specific analysis — whether Studio's red team produces stronger dissent."""

    cost_quality_data: tuple[dict, ...]
    """Scatter-plot data: cost vs composite score per question per path."""


__all__: tuple[str, ...] = (
    "ComparisonReport",
    "DissentFrame",
    "GateScores",
    "ReasoningTrace",
    "Recommendation",
    "RenderedOutput",
    "RunResult",
    "Scenario",
    "ScopeLimits",
    "SessionResult",
    "TradeOff",
)
