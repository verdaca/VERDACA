"""R1 — Epistemic Calibration gate (arch §6.1 row 1, quality-rubric.md §6 R1).

Priority: Critical. Section: FULL document.
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R1Gate(GateEvaluator):
    """R1 Epistemic Calibration — claims labeled by evidential basis;
    confidence proportional; risks entity-specific."""

    gate_id = "R1"


__all__ = ("R1Gate",)
