"""MAC result containers — arch §2.5 DeliberationResult Output Contract.

Both :class:`GateScore` and :class:`DeliberationResult` are frozen Pydantic
models returned across the MAC public surface. They are populated by the
Quality Gate Engine (step 4) and the Iteration Controller (step 3)
respectively; step 1 defines them to pin the shape early so the
:class:`DeliberationState` field types are stable.

Binding anchors:
  - mac/architecture.md §2.5 DeliberationResult Output Contract
  - mac/architecture.md §6.1 12-Gate Catalog (R1..R12, ratified names)
  - mac/architecture.md §6.5 Domain Guard Conditions (Req-E)
  - mac/architecture.md §9.4 Top-5 weighting (composite-score denominator)
  - mac/architecture.md §5.6 Forge Fallback Handling (forge_degraded flag)
"""

from __future__ import annotations

from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field

from praxis.kernel.mac.task import TaskSignature


EvaluatedSection = Literal[
    "FINDINGS",
    "RECOMMENDATIONS",
    "STEELMAN",
    "DISSENT",
    "SCENARIOS",
    "L1",
    "L2",
    "FULL",
]
"""The Req-B routing section identifiers (arch §6.2 ``GATE_SECTION_ROUTES``).
Frozen literal so the Gate Engine cannot emit a section name outside this
set."""


class GateScore(BaseModel):
    """Per-gate score emitted by the Quality Gate Engine at Cycle 3.

    The engine runs in three ordered passes per arch §6.3 (raw → Req-C caps
    using RAW R7 → Forge penalty LAST → Req-E suspensions). The resulting
    ``effective_score`` is what the composite-score formula consumes; the
    ``raw_score`` is preserved for telemetry so the §9.3 violation counter
    and step 4 gate tests can reproduce the pre-cap value.
    """

    model_config = ConfigDict(frozen=True)

    gate_id: str = Field(pattern=r"^R(?:[1-9]|1[0-2])$")
    """``"R1"`` through ``"R12"``. R13 is deferred per arch §3.5 SQ-3."""

    raw_score: int = Field(ge=1, le=5)
    """1..5 from Tier 1+2+3 gate evaluation, pre-cap, pre-penalty."""

    effective_score: int = Field(ge=0, le=5)
    """Post-Req-C cap, post-Forge penalty, post-Req-E suspension. Zero only
    when ``suspended=True`` (suspended gates contribute 0 to the composite
    numerator AND subtract their weight from the denominator; see arch §9.4)."""

    weight: int = Field(ge=1, le=2)
    """1 or 2 per the OQ-5 top-5 weighting (arch §9.4): R1/R2/R4/R5/R7 = 2,
    all others = 1. Total weight sums to 17 when no gates are suspended."""

    suspended: bool = False
    """``True`` when the arch §6.5 Req-E domain guard fired for this
    ``(gate_id, DomainClass)`` pair."""

    rationale: str
    """Judge prompt rationale (Tier 3). Short, one-sentence form produced by
    the gate evaluator; used for R12 direct-contradiction detector text
    spans at step 4."""

    evaluated_section: EvaluatedSection
    """Req-B routing trace — which Req-A section(s) fed this gate's
    evaluation. Must match the arch §6.2 ``GATE_SECTION_ROUTES`` value for
    ``gate_id`` (enforced by ``MAC-T-CYCLE-SEC-02`` snapshot test at step 3)."""


class DeliberationResult(BaseModel):
    """Public output of :meth:`MetaAgentController.deliberate`.

    Frozen at construction; the Iteration Controller builds it exactly once
    per deliberation at the ``publish`` → ``complete`` transition, or at
    the ``failed`` terminal with reduced fields. Callers inspect
    ``composite_score`` against their own PASS threshold (arch §13.3
    OQ-MAC-6 is a Stage 6 concern).
    """

    model_config = ConfigDict(frozen=True)

    cycle_id: str
    """ULID matching :attr:`DeliberationState.cycle_id`."""

    task_signature: TaskSignature
    """The signature used as the retrieval/publish key."""

    output: object | None
    """Final Cycle-3-passed producer output, Req-A labeled. ``None`` when
    the deliberation terminated to ``failed`` with ``output=None`` per
    arch §2.6 Failure Recovery. Typed as ``object`` at step 1 to avoid a
    step-3 circular import; wired to ``ProducerOutput`` at step 3."""

    gate_scores: Mapping[str, GateScore]
    """12 entries keyed by ``"R1"``..``"R12"``. Empty or partial when the
    deliberation terminated before Cycle 3 completed."""

    composite_score: float | None = Field(default=None, ge=0.0, le=100.0)
    """0–100 per benchmark-questions.md §6 step 5 composite formula:
    ``Σ(gate_score × gate_weight) / (active_weight × 5) × 100``.
    ``None`` on failure terminations."""

    backtrack_count: int = Field(default=0, ge=0, le=1)
    """How many times the Iteration Controller re-entered Cycle 1. Capped
    at 1 per arch §5.5."""

    bootstrap_seeds_used: tuple[str, ...] = ()
    """Entry IDs retrieved from the gold-standard corpus during Cycle 1
    seeding. Populated via the sidecar ``mac_bootstrap_metadata`` join at
    step 6. Empty tuple when no bootstrap hits fired."""

    cost_usd: float = Field(default=0.0, ge=0.0)
    """Sum of :class:`CostEvent` amounts emitted via
    ``CostTracker.track_cost`` across all cycles. Wired at step 3."""

    duration_seconds: float = Field(default=0.0, ge=0.0)
    """Wall-clock elapsed from ``interpret`` entry to terminal state."""

    forge_degraded: bool = False
    """True when ``CompressionForge.compress()`` returned
    ``reasoning_preserved=False`` at any cycle boundary, triggering the
    arch §5.6 + §6.3 SQ-7 step-3 R7-penalty-last ordering."""

    final_phase: Literal["complete", "failed"] = "complete"
    """Which terminal state the controller reached. ``"failed"`` is reached
    via either ``BudgetExceededError`` from Runtime or second-consecutive
    Critical gate failure at ``cycle_3_verify`` with ``backtrack_count==1``
    (arch §5.2 terminal transition footnote)."""


__all__: tuple[str, ...] = (
    "DeliberationResult",
    "EvaluatedSection",
    "GateScore",
)
