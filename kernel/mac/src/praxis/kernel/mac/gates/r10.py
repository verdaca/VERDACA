"""R10 — Epistemic Scope Honesty gate (arch §6.1 row 10, quality-rubric.md §6 R10).

Priority: High. Section: FULL document.
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R10Gate(GateEvaluator):
    """R10 Epistemic Scope Honesty — specific exclusion AND specific
    blind spot — both required, no boilerplate."""

    gate_id = "R10"


__all__ = ("R10Gate",)
