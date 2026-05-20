"""Gate registry — 12 gate evaluators, R1..R12.

The registry is the single place where all 12 gates are constructed
with a shared :class:`JudgeProtocol` instance. Callers iterate
``registry.gates()`` to score an output through every gate.

Binding anchor:
  - mac/architecture.md §6.1 12-Gate Catalog (R1..R12)
  - mac/test-strategy.md v0.3 §11.1 MAC-T-NEG-GATE13-01 (exactly 12 modules)
"""

from __future__ import annotations

from typing import Mapping

from praxis.kernel.mac.gates.base import GateEvaluator, JudgeProtocol
from praxis.kernel.mac.gates.r1 import R1Gate
from praxis.kernel.mac.gates.r2 import R2Gate
from praxis.kernel.mac.gates.r3 import R3Gate
from praxis.kernel.mac.gates.r4 import R4Gate
from praxis.kernel.mac.gates.r5 import R5Gate
from praxis.kernel.mac.gates.r6 import R6Gate
from praxis.kernel.mac.gates.r7 import R7Gate
from praxis.kernel.mac.gates.r8 import R8Gate
from praxis.kernel.mac.gates.r9 import R9Gate
from praxis.kernel.mac.gates.r10 import R10Gate
from praxis.kernel.mac.gates.r11 import R11Gate
from praxis.kernel.mac.gates.r12 import R12Gate


GATE_CLASSES: tuple[type[GateEvaluator], ...] = (
    R1Gate, R2Gate, R3Gate, R4Gate, R5Gate, R6Gate,
    R7Gate, R8Gate, R9Gate, R10Gate, R11Gate, R12Gate,
)
"""Tuple of all 12 gate classes in R1..R12 order. Used by
``MAC-T-NEG-GATE13-01`` to assert ``len(GATE_CLASSES) == 12`` at
collection time."""


class GateRegistry:
    """Holds 12 gate evaluator instances sharing a single
    :class:`JudgeProtocol`."""

    def __init__(self, judge: JudgeProtocol) -> None:
        self._gates: dict[str, GateEvaluator] = {
            cls.gate_id: cls(judge=judge) for cls in GATE_CLASSES
        }

    @property
    def gates(self) -> Mapping[str, GateEvaluator]:
        return self._gates

    def __len__(self) -> int:
        return len(self._gates)

    def __iter__(self):
        return iter(self._gates.values())

    def __getitem__(self, gate_id: str) -> GateEvaluator:
        return self._gates[gate_id]


__all__ = ("GATE_CLASSES", "GateRegistry")
