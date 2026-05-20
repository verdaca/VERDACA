"""FakeMAC — deterministic MAC double for Studio Tier 1/2 tests.

Returns pre-built ReasoningTrace fixtures keyed by raw_prompt.
No real LLM calls; no praxis-mac dependency.

Binding: studio/test-strategy.md §14.1.
"""

from __future__ import annotations

from praxis.kernel.studio.invoker import TaskInput
from praxis.kernel.studio.models import (
    DissentFrame,
    ReasoningTrace,
    Recommendation,
    Scenario,
    ScopeLimits,
    TradeOff,
)
from praxis.kernel.studio.schema import ProvenanceMode, RenderingMode


def _make_minimal_trace(
    rendering_mode: RenderingMode = RenderingMode.POSITION_TO_HOLD,
    provenance_mode: ProvenanceMode = ProvenanceMode.FLEXIBLE,
) -> ReasoningTrace:
    """Minimal fixture: 1 dissent frame, 2 scenarios, 1 entry per scope-limits category."""
    return ReasoningTrace(
        trade_offs=(
            TradeOff(
                factor="Cost vs. speed",
                weight=0.6,
                alternatives=("Invest now", "Wait and observe"),
                recommendation="Invest now given the data window is closing.",
            ),
        ),
        dissent_frames=(
            DissentFrame(
                frame_name="Wait and observe",
                steelman=(
                    "The market may correct within 90 days, making the investment premature. "
                    "Early movers in analogous markets have often ceded advantage to fast followers."
                ),
                evidence=(
                    "Three comparable market entries in 2022–2023 saw first-movers "
                    "outspent on positioning while fast followers captured margin."
                ),
                conditions=(
                    "This frame prevails if: competitive pricing drops more than 15% in Q2, "
                    "or if two or more incumbents announce equivalent solutions before Q3."
                ),
                confidence=(
                    "Moderate — the wait-and-observe position has a plausible 30–35% chance "
                    "of being correct based on the market analogy evidence."
                ),
            ),
        ),
        scenarios=(
            Scenario(
                name="Base case",
                trigger="Market conditions remain within current range through Q3.",
                invalidation=(
                    "Invalidation conditions: competitor announces direct substitute, "
                    "or customer NPS drops more than 8 points in 60 days."
                ),
                decision_rule=(
                    "Proceed with primary recommendation. "
                    "Owner: CEO. Review: Q3 board meeting."
                ),
            ),
            Scenario(
                name="Downside case",
                trigger="Competitive pricing drops more than 20% within 60 days.",
                invalidation=(
                    "Invalidation conditions: pricing stabilizes within 5% of current level "
                    "for two consecutive months."
                ),
                decision_rule=(
                    "Pause investment, revisit at next board meeting. "
                    "Owner: COO. Review: within 30 days of trigger."
                ),
            ),
        ),
        scope_limits=ScopeLimits(
            data_gaps=(
                "Proprietary competitor cost structure data was not available.",
            ),
            adjacent_questions=(
                "Operational scaling requirements for rapid expansion are not covered here.",
            ),
            invalidating_assumptions=(
                "Market growth assumptions are based on industry consensus projections "
                "that may not reflect company-specific dynamics.",
            ),
        ),
        recommendations=(
            Recommendation(
                text=(
                    "Proceed with the primary initiative within the current quarter, "
                    "subject to the named scenario trigger conditions."
                ),
                confidence=(
                    "High confidence given available data, contingent on Q3 market assumptions."
                ),
            ),
        ),
        rendering_mode=rendering_mode,
        provenance_mode=provenance_mode,
        composite_score=78.5,
        gate_scores={f"R{i}": 4 for i in range(1, 13)},
        backtrack_count=0,
        cost_usd=3.50,
    )


def _make_rich_trace(
    rendering_mode: RenderingMode = RenderingMode.POSITION_TO_HOLD,
    provenance_mode: ProvenanceMode = ProvenanceMode.FLEXIBLE,
) -> ReasoningTrace:
    """Rich fixture: 4 dissent frames, 5 scenarios, multiple entries per scope-limits category."""
    minimal = _make_minimal_trace(rendering_mode, provenance_mode)
    extra_frames = (
        DissentFrame(
            frame_name="Radical consolidation",
            steelman=(
                "Consolidating existing lines rather than expanding increases margin "
                "without the execution risk of new market entry."
            ),
            evidence=(
                "Internal data shows top 3 product lines account for 78% of gross margin. "
                "Industry consolidation patterns show 2–3× margin improvement within 18 months."
            ),
            conditions=(
                "This frame prevails if: current product margin falls below 30% for two quarters, "
                "or if expansion cost exceeds $5M in first year."
            ),
            confidence=(
                "Low confidence — expansion-vs-consolidation trade-off is well-studied "
                "but outcome depends heavily on execution quality."
            ),
        ),
        DissentFrame(
            frame_name="Partnership first",
            steelman=(
                "Entering through a partnership reduces capital risk while maintaining "
                "market positioning. The equity cost of a JV is lower than solo entry."
            ),
            evidence=(
                "Comparable JV entries in adjacent markets captured 60–70% of the "
                "market share benefit at 40% of the capital outlay."
            ),
            conditions=(
                "This frame prevails if: a Tier 1 partner is available within 90 days "
                "at acceptable equity terms."
            ),
            confidence=(
                "Moderate — dependent on partner availability, which is unverified."
            ),
        ),
        DissentFrame(
            frame_name="Defer entirely",
            steelman=(
                "The question assumes the current window is time-constrained. "
                "If the window is 18 months rather than 6, deferral preserves optionality."
            ),
            evidence=(
                "Window-constraint assumption is based on one analyst estimate "
                "with no proprietary data backing."
            ),
            conditions=(
                "This frame prevails if: independent market research confirms a window "
                "of 18+ months."
            ),
            confidence=(
                "Low — the deferral frame is the weakest of the alternatives given "
                "current market signals."
            ),
        ),
    )
    return ReasoningTrace(
        trade_offs=minimal.trade_offs + (
            TradeOff(
                factor="Partnership vs. solo entry",
                weight=0.4,
                alternatives=("JV with Tier-1 partner", "Solo entry", "Defer"),
                recommendation="Solo entry given partner availability constraints.",
            ),
        ),
        dissent_frames=minimal.dissent_frames + extra_frames,
        scenarios=minimal.scenarios + (
            Scenario(
                name="Partnership scenario",
                trigger="Tier-1 partner signals availability within 60 days.",
                invalidation=(
                    "Invalidation conditions: partner terms exceed 30% equity stake, "
                    "or partner timeline exceeds 120 days."
                ),
                decision_rule=(
                    "Re-evaluate partnership path. Owner: BD Lead. Review: within 14 days of signal."
                ),
            ),
            Scenario(
                name="Consolidation scenario",
                trigger="Gross margin on top 3 lines drops below 28% for two consecutive quarters.",
                invalidation=(
                    "Invalidation conditions: margin recovers above 32% within one quarter."
                ),
                decision_rule=(
                    "Halt expansion, initiate consolidation review. Owner: CFO. Review: within 30 days."
                ),
            ),
            Scenario(
                name="Deferral scenario",
                trigger=(
                    "Independent market research confirms window of 18+ months "
                    "and competitive entry costs drop more than 30%."
                ),
                invalidation=(
                    "Invalidation conditions: window estimate confirmed at less than 12 months "
                    "by any two independent sources."
                ),
                decision_rule=(
                    "Defer and revisit. Owner: CEO. Review: following independent research delivery."
                ),
            ),
        ),
        scope_limits=ScopeLimits(
            data_gaps=(
                "Proprietary competitor cost structure data was not available.",
                "Customer willingness-to-pay data was based on survey, not transactional evidence.",
                "Long-term regulatory trajectory in target market was not assessed.",
            ),
            adjacent_questions=(
                "Operational scaling requirements for rapid expansion.",
                "Team capacity and hiring timeline for expansion execution.",
                "Pricing strategy for the expanded market segment.",
            ),
            invalidating_assumptions=(
                "Market growth assumptions based on industry consensus projections.",
                "Window-constraint assumption based on single analyst estimate.",
                "Cost assumptions derived from comparable-market proxies, not direct data.",
            ),
        ),
        recommendations=minimal.recommendations,
        rendering_mode=rendering_mode,
        provenance_mode=provenance_mode,
        composite_score=82.0,
        gate_scores={f"R{i}": 4 if i in (4, 5) else 3 for i in range(1, 13)},
        backtrack_count=0,
        cost_usd=7.20,
    )


# ---------------------------------------------------------------------------
# FakeMAC — test double
# ---------------------------------------------------------------------------

_FIXTURE_LOOKUP: dict[str, ReasoningTrace] = {}


class FakeMAC:
    """Returns deterministic ReasoningTrace for use as a MACProtocol double.

    Usage::

        fake = FakeMAC()
        # Register custom fixture
        fake.register("My question", my_trace)
        # Or use defaults
        result = fake.deliberate(task_input)
    """

    def __init__(self, default_rendering_mode: RenderingMode = RenderingMode.POSITION_TO_HOLD) -> None:
        self._lookup: dict[str, ReasoningTrace] = {}
        self._default_mode = default_rendering_mode

    def register(self, raw_prompt: str, trace: ReasoningTrace) -> None:
        self._lookup[raw_prompt] = trace

    def deliberate(self, task: TaskInput) -> ReasoningTrace:
        """Return registered fixture or a minimal default trace."""
        if task.raw_prompt in self._lookup:
            return self._lookup[task.raw_prompt]
        return _make_minimal_trace(self._default_mode)


def make_minimal_trace(
    rendering_mode: RenderingMode = RenderingMode.POSITION_TO_HOLD,
    provenance_mode: ProvenanceMode = ProvenanceMode.FLEXIBLE,
) -> ReasoningTrace:
    return _make_minimal_trace(rendering_mode, provenance_mode)


def make_rich_trace(
    rendering_mode: RenderingMode = RenderingMode.POSITION_TO_HOLD,
    provenance_mode: ProvenanceMode = ProvenanceMode.FLEXIBLE,
) -> ReasoningTrace:
    return _make_rich_trace(rendering_mode, provenance_mode)
