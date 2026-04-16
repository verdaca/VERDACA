"""Gate evaluator base class — arch §6.1 / §6.3.

Every gate R1..R12 is a thin subclass of :class:`GateEvaluator`. The
evaluator calls :meth:`FakeLLMJudgeProtocol.score` with a ``(gate_id,
input_payload)`` tuple and returns the raw integer score.

**Critical design invariant:** gates return RAW scores only. SQ-7 Forge
ordering (arch §6.3) and Req-C co-evaluation caps (arch §6.3 Pairs 1+2)
are applied by :func:`compute_final_scores` in
``praxis.kernel.mac.cycle.iteration_controller``. The gate engine and
individual gate files do NOT re-implement SQ-7 ordering.

**Critical design invariant (team-lead step-4 constraint 2):** no gate
file redefines :data:`CRITICAL_GATES` or :data:`FORGE_PENALTY_SET`. The
source of truth is ``praxis.kernel.mac.cycle.iteration_controller``.
Gates that need criticality information import it.

Binding anchors:
  - mac/architecture.md §6.1 12-Gate Catalog
  - mac/architecture.md §6.3 Req-C + SQ-7 ordering (NOT re-implemented here)
  - mac/quality-rubric.md §6 (gate definitions)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from praxis.kernel.mac.cycle.section_router import SectionSelector, route_for


@dataclass(frozen=True)
class JudgeResponse:
    """Minimal judge response — one raw score + a short rationale."""

    score: int
    rationale: str


@runtime_checkable
class JudgeProtocol(Protocol):
    """Shape of the judge (fake or real) that gate evaluators consume.

    The real production judge (``LLMJudgeClient``) satisfies this at
    step 6 / Stage 7; at step 4 :class:`FakeLLMJudge` is the only
    implementation.
    """

    def score(self, *, gate_id: str, input_payload: dict[str, Any]) -> JudgeResponse: ...


class GateEvaluator:
    """Base class for all 12 gate evaluators.

    Subclasses set the ``gate_id`` class attribute. The ``score()``
    method dispatches to the injected judge with the gate's ratified
    section selector (per arch §6.2 ``GATE_SECTION_ROUTES``).
    """

    gate_id: str = ""  # subclasses override

    def __init__(self, judge: JudgeProtocol) -> None:
        self._judge = judge

    def section_selectors(self) -> tuple[SectionSelector, ...]:
        """Return the arch §6.2 routing tuple for this gate."""
        return route_for(self.gate_id)

    def score(self, *, input_payload: dict[str, Any]) -> JudgeResponse:
        """Return the RAW judge score. No Req-C cap, no Forge penalty.

        Post-processing (ordering, caps, suspensions) happens at the
        cycle level via :func:`compute_final_scores`.
        """
        return self._judge.score(
            gate_id=self.gate_id, input_payload=input_payload
        )


__all__ = ("GateEvaluator", "JudgeProtocol", "JudgeResponse")
