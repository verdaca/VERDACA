"""Quality Gate Engine subpackage — arch §6."""

from __future__ import annotations

from praxis.kernel.mac.gates.base import GateEvaluator, JudgeProtocol, JudgeResponse
from praxis.kernel.mac.gates.calibration_anchors import (
    CALIBRATION_ANCHORS,
    CALIBRATION_ANCHORS_SHA256,
    CalibrationAnchor,
    compute_calibration_anchors_sha256,
    verify_calibration_anchors_sha256,
)
from praxis.kernel.mac.gates.guards import DEFAULT_GUARD_MAP, gates_suspended_for
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
from praxis.kernel.mac.gates.registry import GATE_CLASSES, GateRegistry

__all__ = (
    "CALIBRATION_ANCHORS",
    "CALIBRATION_ANCHORS_SHA256",
    "CalibrationAnchor",
    "DEFAULT_GUARD_MAP",
    "GATE_CLASSES",
    "GateEvaluator",
    "GateRegistry",
    "JudgeProtocol",
    "JudgeResponse",
    "R1Gate", "R2Gate", "R3Gate", "R4Gate", "R5Gate", "R6Gate",
    "R7Gate", "R8Gate", "R9Gate", "R10Gate", "R11Gate", "R12Gate",
    "compute_calibration_anchors_sha256",
    "gates_suspended_for",
    "verify_calibration_anchors_sha256",
)
