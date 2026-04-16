"""R2 — Question Fidelity gate (arch §6.1 row 2, quality-rubric.md §6 R2).

Priority: Critical. Section: [RECOMMENDATIONS].
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R2Gate(GateEvaluator):
    """R2 Question Fidelity — stated question OR named reformulation
    answered; 5/5 = meta-evaluation."""

    gate_id = "R2"


__all__ = ("R2Gate",)
