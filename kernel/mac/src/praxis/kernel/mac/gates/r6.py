"""R6 — Decision Relevance Density gate (arch §6.1 row 6, quality-rubric.md §6 R6).

Priority: Medium. Section: L1 only (TRIZ-2 resolution).
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R6Gate(GateEvaluator):
    """R6 Decision Relevance Density — L1 layer dense; key findings
    prioritized. L1-only routing per arch §6.2 TRIZ-2 resolution."""

    gate_id = "R6"


__all__ = ("R6Gate",)
