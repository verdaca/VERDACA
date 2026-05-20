"""Composite score formula — benchmark-questions.md §6 Step 5 + §7 OQ-5.

Top-5 weighted composite with Req-E suspension-aware denominator.

Weights (benchmark §7 OQ-5):
  - R1, R2, R4, R5, R7 = 2 each (Critical, top-5)
  - R3, R6, R8, R9, R10, R11, R12 = 1 each
  - Total weight = 17 when no gates are suspended

Suspension-aware denominator (arch §9.4):
  When Req-E suspends a gate, its weight is removed from the total.
  ``active_weight = 17 - sum(suspended_weights)``. Formula::

      composite = Σ(effective_score × weight) / (active_weight × 5) × 100

Binding anchors:
  - mac/architecture.md §9.4 Top-5 weighting (OQ-5)
  - mac/benchmark-questions.md §6 Step 5 composite formula
  - mac/benchmark-questions.md §7 OQ-5 top-5 weighting rationale
"""

from __future__ import annotations

from typing import Mapping


GATE_WEIGHTS: Mapping[str, int] = {
    "R1": 2, "R2": 2, "R3": 1, "R4": 2, "R5": 2, "R6": 1,
    "R7": 2, "R8": 1, "R9": 1, "R10": 1, "R11": 1, "R12": 1,
}
"""Arch §9.4 + benchmark §7 OQ-5 weights. Critical (top-5) gates R1/R2/R4/R5/R7 = 2;
all others = 1. Total = 17."""


TOTAL_WEIGHT: int = sum(GATE_WEIGHTS.values())
"""17 when no gates are suspended."""


def composite_score(
    *,
    effective_scores: Mapping[str, int],
    suspended: frozenset[str] = frozenset(),
) -> float:
    """Return the 0–100 composite score with suspension-aware denominator.

    Per arch §9.4 suspended-gate caveat: suspended gates contribute 0
    to both numerator AND denominator — their weight is subtracted from
    the total so the percentage scale stays 0–100 regardless of how
    many guards fire.

    Raises :class:`ValueError` if all gates are suspended (denominator 0).
    """
    active_weight = 0
    numerator = 0
    for gate_id, score in effective_scores.items():
        if gate_id in suspended:
            continue
        weight = GATE_WEIGHTS[gate_id]
        numerator += score * weight
        active_weight += weight

    if active_weight == 0:
        raise ValueError("all gates suspended; composite denominator is zero")

    return (numerator / (active_weight * 5)) * 100.0


__all__ = ("GATE_WEIGHTS", "TOTAL_WEIGHT", "composite_score")
