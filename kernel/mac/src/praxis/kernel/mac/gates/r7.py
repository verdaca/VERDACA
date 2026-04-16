"""R7 — Reasoning Traceability gate (arch §6.1 row 7, quality-rubric.md §6 R7).

Priority: Critical. Section: L2 main body. Co-eval pair: (R8, R7).
Forge penalty target per arch §6.3 SQ-7 step 3 (penalty applied LAST,
after Req-C R8 cap computed from RAW R7).
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R7Gate(GateEvaluator):
    """R7 Reasoning Traceability — logic chain followable; inference
    markers; logical validity. Sole member of FORGE_PENALTY_SET."""

    gate_id = "R7"


__all__ = ("R7Gate",)
