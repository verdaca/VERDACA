"""R12 — Internal Consistency gate (arch §6.1 row 12, quality-rubric.md §6 R12).

Priority: High. Section: FULL document.
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R12Gate(GateEvaluator):
    """R12 Internal Consistency — premises in findings not denied in
    conclusions. T1 direct-contradiction detector + T3 implicit check."""

    gate_id = "R12"


__all__ = ("R12Gate",)
