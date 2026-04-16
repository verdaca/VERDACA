"""R3 — Falsifiability gate (arch §6.1 row 3, quality-rubric.md §6 R3).

Priority: High. Section: FULL document.
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R3Gate(GateEvaluator):
    """R3 Falsifiability — monitorable, observable invalidation
    conditions per conclusion."""

    gate_id = "R3"


__all__ = ("R3Gate",)
