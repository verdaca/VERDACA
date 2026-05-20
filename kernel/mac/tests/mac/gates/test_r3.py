"""R3 Falsifiability — mac/test-strategy.md v0.3 §3.4."""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r3 import R3Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r3_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R3", {"r3_partial_falsifiable": 3})
    gate = R3Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r3_partial_falsifiable")).score == 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 3 — §13.3.3 allow-list entry #6
def test_mac_t_gate_r3_02_calibration_anchor(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R3", {"anchor_2": 2, "anchor_4": 4})
    gate = R3Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r3_03_section_routing() -> None:
    gate = R3Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.FULL,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r3_04_domain_guard() -> None:
    for dc in DomainClass:
        assert "R3" not in gates_suspended_for(dc)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r3_05_falsifiability_monotonicity(make_gate_judge) -> None:
    """R3-05 — per v0.3 §3.4.5: monotonicity property. More invalidation
    conditions → non-decreasing R3 score.
    """
    judge, payload_for = make_gate_judge(
        "R3",
        {
            "invalidation_count_0": 1,
            "invalidation_count_1": 2,
            "invalidation_count_3": 4,
            "invalidation_count_5": 5,
        },
    )
    gate = R3Gate(judge=judge)
    s0 = gate.score(input_payload=payload_for("invalidation_count_0")).score
    s1 = gate.score(input_payload=payload_for("invalidation_count_1")).score
    s3 = gate.score(input_payload=payload_for("invalidation_count_3")).score
    s5 = gate.score(input_payload=payload_for("invalidation_count_5")).score
    assert s0 <= s1 <= s3 <= s5
