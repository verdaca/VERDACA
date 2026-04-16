"""R10 Epistemic Scope Honesty — mac/test-strategy.md v0.3 §3.11."""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r10 import R10Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r10_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R10", {"r10_partial_scope": 3})
    gate = R10Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r10_partial_scope")).score == 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r10_02_calibration_anchor(make_gate_judge) -> None:
    """R10-02 — NOT no_waiver."""
    judge, payload_for = make_gate_judge("R10", {"anchor_2": 2, "anchor_4": 4})
    gate = R10Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r10_03_section_routing() -> None:
    gate = R10Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.FULL,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r10_04_domain_guard() -> None:
    for dc in DomainClass:
        assert "R10" not in gates_suspended_for(dc)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r10_05_2_squared_property_plus_boilerplate(
    make_gate_judge,
) -> None:
    """R10-05 — per v0.3 §3.11.5: 2² property over
    ``(has_specific_exclusion, has_specific_blindspot)``.

    Both components required per quality-rubric.md §6 R10 "boilerplate
    fails". Rule: score high iff both are present; boilerplate always
    fails regardless of presence claims.
    """
    judge, payload_for = make_gate_judge(
        "R10",
        {
            "both_present": 4,
            "only_exclusion": 2,
            "only_blindspot": 2,
            "neither": 1,
            "boilerplate_claiming_both": 2,
        },
    )
    gate = R10Gate(judge=judge)
    assert gate.score(input_payload=payload_for("both_present")).score >= 4
    assert gate.score(input_payload=payload_for("only_exclusion")).score <= 2
    assert gate.score(input_payload=payload_for("only_blindspot")).score <= 2
    assert gate.score(input_payload=payload_for("neither")).score == 1
    # Boilerplate claiming both fails per rubric §6 R10.
    assert gate.score(input_payload=payload_for("boilerplate_claiming_both")).score <= 2
