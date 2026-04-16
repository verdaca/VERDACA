"""R9 — Evidence Impartiality gate (arch §6.1 row 9, quality-rubric.md §6 R9).

Priority: Medium. Section: [FINDINGS] ONLY (TRIZ-3 resolution).
[STEELMAN] and [DISSENT] sections are explicitly exempt.
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R9Gate(GateEvaluator):
    """R9 Evidence Impartiality — conclusion strength proportional to
    findings evidence; STEELMAN/DISSENT exempt per arch §6.2 TRIZ-3."""

    gate_id = "R9"


__all__ = ("R9Gate",)
