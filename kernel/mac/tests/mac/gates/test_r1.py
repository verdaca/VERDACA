"""R1 Epistemic Calibration — mac/test-strategy.md v0.3 §3.2."""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.calibration_anchors import CALIBRATION_ANCHORS
from praxis.kernel.mac.gates.r1 import R1Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r1_01_unit_scoring(make_gate_judge) -> None:
    """R1-01 unit scoring with FakeLLMJudge."""
    judge, payload_for = make_gate_judge("R1", {"r1_mixed_calibration": 3})
    gate = R1Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r1_mixed_calibration")).score == 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 1 — §13.3.3 allow-list entry #4
def test_mac_t_gate_r1_02_calibration_anchor(make_gate_judge) -> None:
    """R1-02 calibration anchor — benchmark §5 R1 score-2 / score-4 bucketing."""
    judge, payload_for = make_gate_judge("R1", {"anchor_2": 2, "anchor_4": 4})
    gate = R1Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4
    # Anchors are SHA256-locked in calibration_anchors.py — spot check presence.
    assert "R1" in CALIBRATION_ANCHORS
    assert CALIBRATION_ANCHORS["R1"].gate_id == "R1"


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r1_03_section_routing() -> None:
    """R1-03 routing — arch §6.2: R1 → FULL."""
    judge, _ = ({"stub": 1}, None)
    gate = R1Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.FULL,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r1_04_domain_guard(make_gate_judge) -> None:
    """R1-04 domain guard — R1 is NOT suspended for any DomainClass
    (arch §6.5 only guards R5 and R11)."""
    from praxis.kernel.mac.gates.guards import gates_suspended_for

    for dc in DomainClass:
        assert "R1" not in gates_suspended_for(dc)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r1_05_forge_degradation_no_effect(make_gate_judge) -> None:
    """R1-05 Forge path — R1 is NOT in FORGE_PENALTY_SET (arch §6.3 SQ-7).

    Corrected anchor per Stage 5.3 preload Q1 disposition: arch §5.6 +
    §6.3 SQ-7 ordering (v0.3 test-strategy §3.2.5 has stale §12.5
    anchor).
    """
    # v0.3 test-strategy.md §3.2.5 has stale §12.5 SQ-7 anchor;
    # corrected anchor is arch §5.6 + §6.3 SQ-7 ordering
    from praxis.kernel.mac.cycle.iteration_controller import (
        FORGE_PENALTY_SET,
        compute_final_scores,
    )

    assert "R1" not in FORGE_PENALTY_SET
    raw = {f"R{n}": 4 for n in range(1, 13)}
    eff_no_forge = compute_final_scores(raw, forge_degraded=False)
    eff_forge = compute_final_scores(raw, forge_degraded=True)
    # R1 unchanged in both cases.
    assert eff_no_forge["R1"] == 4
    assert eff_forge["R1"] == 4
