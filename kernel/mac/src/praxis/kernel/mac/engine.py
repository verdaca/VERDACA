"""Quality Gate Engine — arch §6.7 public surface.

The engine drives all 12 gates via a :class:`GateRegistry`, then hands
the raw scores to :func:`compute_final_scores` in
``praxis.kernel.mac.cycle.iteration_controller`` for Req-C / SQ-7 /
Req-E post-processing. The engine itself is thin — it does NOT
re-implement the ordering.

Binding anchors:
  - mac/architecture.md §6.7 Quality Gate Engine Public Surface
  - mac/architecture.md §6.3 Req-C + SQ-7 ordering (delegated to cycle controller)
  - mac/architecture.md §6.5 Req-E domain guards (via ``gates_suspended_for``)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from praxis.kernel.mac.cycle.iteration_controller import compute_final_scores
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.registry import GATE_CLASSES, GateRegistry
from praxis.kernel.mac.task import DomainClass


@dataclass(frozen=True)
class EngineResult:
    """Output of :meth:`QualityGateEngine.evaluate`.

    ``raw_scores`` and ``effective_scores`` are both dict[gate_id, int]
    — the engine preserves both so telemetry can compare pre/post-cap
    values.
    """

    raw_scores: dict[str, int]
    effective_scores: dict[str, int]
    suspended: frozenset[str]


class QualityGateEngine:
    """Cycle 3 verifier. Stateless across calls.

    Constructs a :class:`GateRegistry`, scores the input through each
    gate to produce raw scores, then applies the SQ-7 ordering +
    Req-E suspensions via :func:`compute_final_scores`.
    """

    def __init__(self, registry: GateRegistry) -> None:
        self._registry = registry

    def evaluate(
        self,
        *,
        input_payload: dict[str, Any],
        domain_class: DomainClass,
        forge_degraded: bool = False,
        reviewer_critique: Mapping[str, Any] | None = None,
        workflow_guard_override: dict[DomainClass, frozenset[str]] | None = None,
    ) -> EngineResult:
        """Score the input through all 12 gates and apply post-processing.

        Flow (arch §6.7):
          1. Call each gate's ``score()`` to get raw R1..R12.
          2. Delegate to :func:`compute_final_scores` for SQ-7 ordering
             + Req-C Pair 1 (R8 cap) + Req-C Pair 2 (R5 manufactured-dissent
             cap).
          3. Apply Req-E suspensions via :func:`gates_suspended_for`.
        """
        raw: dict[str, int] = {}
        for gate in self._registry:
            response = gate.score(input_payload=input_payload)
            raw[gate.gate_id] = response.score

        suspended = gates_suspended_for(
            domain_class, workflow_override=workflow_guard_override
        )

        effective = compute_final_scores(
            raw,
            forge_degraded=forge_degraded,
            reviewer_critique=reviewer_critique,
            suspended=suspended,
        )

        return EngineResult(
            raw_scores=raw,
            effective_scores=effective,
            suspended=suspended,
        )


def build_default_engine(judge: Any) -> QualityGateEngine:
    """Convenience factory — build an engine with the default 12-gate registry."""
    registry = GateRegistry(judge=judge)
    return QualityGateEngine(registry=registry)


__all__ = (
    "EngineResult",
    "GATE_CLASSES",
    "QualityGateEngine",
    "build_default_engine",
)
