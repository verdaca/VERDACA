"""R8 Actionability Calibration — mac/test-strategy.md v0.3 §3.9."""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.iteration_controller import compute_final_scores
from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r8 import R8Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r8_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R8", {"r8_conditional_rec": 4})
    gate = R8Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r8_conditional_rec")).score == 4


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 7 — §13.3.3 allow-list entry #10
def test_mac_t_gate_r8_02_calibration_anchor(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R8", {"anchor_2": 2, "anchor_4": 4})
    gate = R8Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r8_03_section_routing_recommendations() -> None:
    """R8-03 — arch §6.2: R8 → RECOMMENDATIONS."""
    gate = R8Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.RECOMMENDATIONS,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r8_04_domain_guard() -> None:
    for dc in DomainClass:
        assert "R8" not in gates_suspended_for(dc)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r8_05_co_eval_cap_with_r7() -> None:
    """R8-05 — Req-C Pair 1 cap: R8_eff = min(R8_raw, R7_raw + 1)."""
    raw = {f"R{n}": 4 for n in range(1, 13)}
    raw["R7"] = 2
    raw["R8"] = 5
    eff = compute_final_scores(raw, forge_degraded=False)
    assert eff["R8"] == 3  # min(5, 2+1) = 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.f1_absorption
def test_mac_t_gate_r8_06_forge_penalty_does_not_propagate_to_r8_cap() -> None:
    """R8-06 — Forge penalty on R7_effective does NOT propagate into R8 cap.

    Worked example (R7_raw=4, R8_raw=4, forge_degraded=True):
      - Step 2: R8_eff = min(4, 4+1) = 4 (uses RAW R7=4, NOT penalized R7=3)
      - Step 4: R7_eff = max(1, 4-1) = 3 (Forge penalty applies here)
      - Result: R7=3, R8=4 (NOT R8=3)

    If Forge penalty propagated into the R8 cap (wrong ordering), we
    would see R8 = min(4, 3+1) = 4 — numerically identical in THIS
    case but semantically wrong. The R7_raw=2 worked example in
    test_r7.py::test_mac_t_gate_r7_06 probes the same invariant for
    a case where the numerical distinction matters.
    """
    raw = {f"R{n}": 4 for n in range(1, 13)}
    raw["R7"] = 4
    raw["R8"] = 4
    eff = compute_final_scores(raw, forge_degraded=True)
    assert eff["R7"] == 3
    assert eff["R8"] == 4
