"""R4 — Steelman Completeness gate (arch §6.1 row 4, quality-rubric.md §6 R4).

Priority: Critical. Section: [STEELMAN]. Co-eval pair: (R5, R4).
Req-F two-step reviewer protocol (arch §7.1) feeds the R4 scoring.
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator


class R4Gate(GateEvaluator):
    """R4 Steelman Completeness — strongest counterarguments at full
    fidelity; two-step judge protocol per Req-F."""

    gate_id = "R4"


__all__ = ("R4Gate",)
