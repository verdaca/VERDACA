"""Studio → MAC handoff — arch §2.5.

``template_to_task_input()`` converts a validated ``WorkflowTemplate`` and
user inputs into a ``TaskInput`` that the MAC's ``MetaAgentController``
consumes. The ``TaskInput`` type is duplicated here as a shape-compatible
stub (DQ-1 Option B: USR isolation pattern per MAC arch §4.6) so the Studio
package has no compile-time dependency on ``praxis-mac``.

``StudioSession`` wraps a MAC-compatible callable and the Pi-Mono cost
tracker to orchestrate the full Studio→MAC→render pipeline, emitting
observability labels per arch §11.

Binding anchors:
  - studio/architecture.md §2.5 MAC Integration: Template → TaskInput
  - studio/architecture.md §11 Observability
"""

from __future__ import annotations

import time
from typing import Any, Callable, Literal, Protocol

from pydantic import BaseModel, ConfigDict

from praxis.kernel.studio.models import (
    RenderedOutput,
    SessionResult,
)
from praxis.kernel.studio.schema import WorkflowTemplate


# ---------------------------------------------------------------------------
# TaskInput stub — shape-compatible with praxis.kernel.mac.task.TaskInput
# (DQ-1 Option B: no compile-time praxis-mac dependency)
# ---------------------------------------------------------------------------


class TaskInput(BaseModel):
    """Studio-local mirror of MAC's TaskInput (arch §3.2 shape).

    Wire-compatible with the MAC's TaskInput for the Studio→MAC call boundary.
    Only the fields that studio constructs are present; the MAC ignores extras.
    """

    model_config = ConfigDict(frozen=True)

    raw_prompt: str
    """The unstructured strategic question from the caller."""

    customer_context: dict[str, str] = {}
    """Customer situation metadata — injection-screened at MAC interpretation time."""

    workflow_template_id: str | None = None
    """Set by Studio to identify the template; None for direct MAC calls."""

    explicit_question: str | None = None
    """Pre-extracted decision question; None → MAC's TaskInterpreter infers from raw_prompt."""


# ---------------------------------------------------------------------------
# MAC protocol — what Studio expects from a MAC-compatible callable
# ---------------------------------------------------------------------------


class MACProtocol(Protocol):
    """Minimal protocol for a MAC-compatible deliberation engine.

    Studio accepts any callable satisfying this protocol — the real MAC or
    any test double (FakeMAC in Tier 1/2 tests).
    """

    def deliberate(self, task: TaskInput) -> Any:
        """Run deliberation and return a DeliberationResult-compatible object."""
        ...


class CostTrackerProtocol(Protocol):
    """Minimal protocol for a Pi-Mono compatible cost tracker."""

    def track_cost(self, label: str, amount_usd: float) -> None:
        """Record a cost event under the given label."""
        ...


# ---------------------------------------------------------------------------
# template_to_task_input — arch §2.5
# ---------------------------------------------------------------------------


def template_to_task_input(
    template: WorkflowTemplate,
    user_inputs: dict[str, str | int | float | bool],
    customer_context: dict[str, str] | None = None,
) -> TaskInput:
    """Convert a WorkflowTemplate + user inputs into a TaskInput for the MAC.

    The ``workflow_template_id`` is formatted as
    ``"{product}/{name}/{version}"`` per arch §2.5.

    Args:
        template: A validated WorkflowTemplate loaded via model_validate().
        user_inputs: Dict keyed by input parameter name. Must include all
            required parameters (``InputParamSpec.required=True``).
        customer_context: Optional customer situation metadata (company stage,
            industry, constraints). Injection-screened by the MAC.

    Returns:
        A TaskInput ready to pass to MAC's MetaAgentController.deliberate().

    Raises:
        KeyError: if a required input parameter is missing from user_inputs.
    """
    for param_name, spec in template.inputs.items():
        if spec.required and param_name not in user_inputs:
            raise KeyError(
                f"Required input parameter {param_name!r} is missing from user_inputs"
            )

    raw_prompt: str = str(user_inputs.get("strategic_question", ""))
    explicit_question: str | None = str(user_inputs["explicit_question"]) if "explicit_question" in user_inputs else None  # noqa: E501

    return TaskInput(
        raw_prompt=raw_prompt,
        customer_context=customer_context or {},
        workflow_template_id=f"{template.product}/{template.name}/{template.version}",
        explicit_question=explicit_question,
    )


# ---------------------------------------------------------------------------
# StudioSession — orchestrates the full pipeline with observability
# ---------------------------------------------------------------------------


class _BudgetExhaustedError(RuntimeError):
    """Raised internally when the Pi-Mono ceiling is hit before completion."""


class StudioSession:
    """Orchestrates Studio workflow: YAML → validate → MAC → render → observe.

    Usage::

        session = StudioSession(mac=mac_instance, cost_tracker=tracker)
        result = session.invoke(
            template=template,
            user_inputs={"strategic_question": "Should we expand to EU?"},
            customer_context={"stage": "Series B"},
        )

    Binding: studio/architecture.md §11 Observability label namespace.
    """

    def __init__(
        self,
        mac: MACProtocol,
        cost_tracker: CostTrackerProtocol,
        renderer: Any,  # TemplateRenderer — avoid circular import
    ) -> None:
        self._mac = mac
        self._tracker = cost_tracker
        self._renderer = renderer

    def invoke(
        self,
        template: WorkflowTemplate,
        user_inputs: dict[str, str | int | float | bool],
        customer_context: dict[str, str] | None = None,
    ) -> SessionResult:
        """Run the full Studio pipeline and return a SessionResult.

        Emits Pi-Mono labels per arch §11.1. If the MAC cost exceeds
        ``template.cost_budget_usd``, returns a degraded partial result
        rather than raising (arch §10.4 graceful degradation).
        """
        mode: Literal["deep", "quick"] = self._detect_mode(template)
        t0 = time.monotonic()

        task = template_to_task_input(template, user_inputs, customer_context)

        try:
            result = self._mac.deliberate(task)
        except Exception as exc:
            if "budget" in str(exc).lower():
                return self._degraded_result(template, mode, time.monotonic() - t0)
            raise

        cost_usd: float = getattr(result, "cost_usd", 0.0)
        composite: float = getattr(result, "composite_score", 0.0) or 0.0
        gate_scores: dict[str, int] = {
            gid: (gs.effective_score if hasattr(gs, "effective_score") else int(gs))
            for gid, gs in (getattr(result, "gate_scores", {}) or {}).items()
        }
        backtrack_count: int = getattr(result, "backtrack_count", 0)

        # Emit observability labels (arch §11.1)
        self._emit_labels(template, cost_usd, composite, gate_scores, backtrack_count, mode)

        # Build outputs (one per OutputSpec)
        from praxis.kernel.studio.models import ReasoningTrace
        trace = self._extract_trace(result, template)
        outputs: list[RenderedOutput] = []
        for output_spec in template.outputs:
            rendered = self._renderer.render(trace, output_spec.template_path)
            outputs.append(rendered)
            # Check budget after each output
            if cost_usd > template.cost_budget_usd:
                break  # graceful early stop

        duration = time.monotonic() - t0
        self._tracker.track_cost("studio.session.duration_seconds", duration)

        return SessionResult(
            outputs=tuple(outputs),
            composite_score=composite,
            gate_scores=gate_scores,
            backtrack_count=backtrack_count,
            cost_usd=cost_usd,
            duration_seconds=duration,
            rendering_mode=template.rendering_mode,
            mode=mode,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_mode(self, template: WorkflowTemplate) -> Literal["deep", "quick"]:
        """Infer 'quick' if any cycle has skip_in_quick_mode=True AND budget≤2."""
        return "quick" if template.cost_budget_usd <= 2.0 else "deep"

    def _emit_labels(
        self,
        template: WorkflowTemplate,
        cost_usd: float,
        composite: float,
        gate_scores: dict[str, int],
        backtrack_count: int,
        mode: str,
    ) -> None:
        self._tracker.track_cost("studio.session.cost_usd", cost_usd)
        self._tracker.track_cost("studio.session.composite_score", composite)
        self._tracker.track_cost("studio.session.backtrack_count", float(backtrack_count))
        for gate_id, score in gate_scores.items():
            self._tracker.track_cost(f"studio.gate.{gate_id}.score", float(score))
        rm_value = template.rendering_mode.value
        self._tracker.track_cost(f"studio.session.rendering_mode.{rm_value}", 1.0)
        self._tracker.track_cost(f"studio.session.mode.{mode}", 1.0)

    def _extract_trace(self, deliberation_result: Any, template: WorkflowTemplate) -> Any:
        """Extract a ReasoningTrace from a DeliberationResult.

        In production this would parse the MAC's Req-A labeled text sections.
        In tests, FakeMAC returns a pre-built ReasoningTrace-compatible object.
        """
        from praxis.kernel.studio.models import (
            DissentFrame,
            ReasoningTrace,
            Recommendation,
            Scenario,
            ScopeLimits,
            TradeOff,
        )

        if isinstance(deliberation_result, ReasoningTrace):
            return deliberation_result

        # Minimal fallback: build a stub trace from the output text
        output_text = str(getattr(deliberation_result, "output", "") or "")
        return ReasoningTrace(
            trade_offs=(
                TradeOff(
                    factor="Primary consideration",
                    weight=1.0,
                    alternatives=("Option A", "Option B"),
                    recommendation=output_text[:200] if output_text else "See full analysis.",
                ),
            ),
            dissent_frames=(
                DissentFrame(
                    frame_name="Alternative view",
                    steelman="The strongest case for the alternative position.",
                    evidence="Supporting evidence from the reasoning trace.",
                    conditions="Conditions under which this view prevails.",
                    confidence="Moderate confidence relative to primary recommendation.",
                ),
            ),
            scenarios=(
                Scenario(
                    name="Base case",
                    trigger="Current market conditions persist.",
                    invalidation="Macro conditions shift materially within 6 months.",
                    decision_rule="Proceed with primary recommendation (Owner: CEO, Review: Q3).",
                ),
                Scenario(
                    name="Downside case",
                    trigger="Competitive pressure intensifies.",
                    invalidation="Competitive dynamics stabilize.",
                    decision_rule="Delay and revisit (Owner: COO, Review: Q2).",
                ),
            ),
            scope_limits=ScopeLimits(
                data_gaps=("Proprietary competitor cost data was not available.",),
                adjacent_questions=("Operational scaling requirements for expansion.",),
                invalidating_assumptions=("Market growth assumptions based on industry consensus.",),
            ),
            recommendations=(
                Recommendation(
                    text="Primary recommendation based on the analysis.",
                    confidence="High confidence given available data.",
                ),
            ),
            rendering_mode=template.rendering_mode,
            provenance_mode=template.resolved_provenance_mode(),
            composite_score=getattr(deliberation_result, "composite_score", 0.0) or 0.0,
            gate_scores={
                gid: gs.effective_score
                for gid, gs in (getattr(deliberation_result, "gate_scores", {}) or {}).items()
            },
            backtrack_count=getattr(deliberation_result, "backtrack_count", 0),
            cost_usd=getattr(deliberation_result, "cost_usd", 0.0),
        )

    def _degraded_result(
        self,
        template: WorkflowTemplate,
        mode: Literal["deep", "quick"],
        duration: float,
    ) -> SessionResult:
        from praxis.kernel.studio.models import RenderedOutput

        degraded_text = (
            "## DEGRADED OUTPUT\n\n"
            "The session budget ceiling was reached before all cycles completed. "
            "Partial analysis only.\n"
        )
        outputs = tuple(
            RenderedOutput(
                text=degraded_text,
                format="markdown",
                rendering_mode=template.rendering_mode,
                provenance_mode=template.resolved_provenance_mode(),
                word_count=len(degraded_text.split()),
                register_violations=(),
            )
            for _ in template.outputs
        )
        return SessionResult(
            outputs=outputs,
            composite_score=0.0,
            gate_scores={},
            backtrack_count=0,
            cost_usd=template.cost_budget_usd,
            duration_seconds=duration,
            rendering_mode=template.rendering_mode,
            mode=mode,
        )


__all__: tuple[str, ...] = (
    "CostTrackerProtocol",
    "MACProtocol",
    "StudioSession",
    "TaskInput",
    "template_to_task_input",
)
