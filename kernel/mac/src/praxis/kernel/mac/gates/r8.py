"""R8 — Actionability Calibration gate (arch §6.1 row 8, quality-rubric.md §6 R8).

Priority: High. Section: [RECOMMENDATIONS]. Co-eval pair: (R8, R7).
Req-C Pair 1 (arch §6.3 SQ-4 Option b): R8_eff = min(R8_raw, R7_raw + 1)
using RAW R7 (not R7_effective). Forge penalty does NOT propagate into
this cap — step 3's compute_final_scores owns the ordering.
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R8Gate(GateEvaluator):
    """R8 Actionability Calibration — specific actionable
    recommendations; 'further analysis' without conditional fails."""

    gate_id = "R8"


__all__ = ("R8Gate",)
