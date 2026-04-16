"""R6 Decision Relevance Density — mac/test-strategy.md v0.3 §3.7."""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r6 import R6Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r6_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R6", {"r6_mixed_density": 3})
    gate = R6Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r6_mixed_density")).score == 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r6_02_calibration_anchor(make_gate_judge) -> None:
    """R6-02 — NOT no_waiver (R6 is priority Medium)."""
    judge, payload_for = make_gate_judge("R6", {"anchor_2": 2, "anchor_4": 4})
    gate = R6Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r6_03_section_routing_l1_only() -> None:
    """R6-03 — arch §6.2 TRIZ-2: R6 → L1 ONLY."""
    gate = R6Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.L1,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r6_04_domain_guard() -> None:
    for dc in DomainClass:
        assert "R6" not in gates_suspended_for(dc)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r6_05_l1_density_differential(make_gate_judge) -> None:
    """R6-05 — per v0.3 §3.7.5: L1 density differential. Lean L1 >
    padded L1 when L2 is identical (R6 is L1-only per TRIZ-2)."""
    judge, payload_for = make_gate_judge(
        "R6", {"lean_l1_identical_l2": 5, "padded_l1_identical_l2": 2}
    )
    gate = R6Gate(judge=judge)
    lean = gate.score(input_payload=payload_for("lean_l1_identical_l2")).score
    padded = gate.score(input_payload=payload_for("padded_l1_identical_l2")).score
    assert lean > padded
