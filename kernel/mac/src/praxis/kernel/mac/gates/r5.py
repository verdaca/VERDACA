"""R5 — Dissent Preservation gate (arch §6.1 row 5, quality-rubric.md §6 R5).

Priority: Critical. Section: [DISSENT]. Co-eval pair: (R5, R4).
Guard: suspended when DomainClass == CONSENSUS (arch §6.5 Req-E).
Manufactured-dissent cap applied at compute_final_scores via Req-C Pair 2.
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R5Gate(GateEvaluator):
    """R5 Dissent Preservation — minority views with content depth;
    manufactured dissent detected (Req-C Pair 2 cap)."""

    gate_id = "R5"


__all__ = ("R5Gate",)
