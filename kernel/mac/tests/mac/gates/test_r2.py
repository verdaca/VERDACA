"""R2 Question Fidelity — mac/test-strategy.md v0.3 §3.3."""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r2 import R2Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r2_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R2", {"r2_tangent": 2})
    gate = R2Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r2_tangent")).score == 2


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 2 — §13.3.3 allow-list entry #5
def test_mac_t_gate_r2_02_calibration_anchor(make_gate_judge) -> None:
    """R2-02 — benchmark §5 R2 OR-logic + meta-evaluation anchors."""
    judge, payload_for = make_gate_judge("R2", {"anchor_2": 2, "anchor_4": 4})
    gate = R2Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r2_03_section_routing() -> None:
    """R2-03 — arch §6.2: R2 → RECOMMENDATIONS."""
    gate = R2Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.RECOMMENDATIONS,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r2_04_domain_guard() -> None:
    for dc in DomainClass:
        assert "R2" not in gates_suspended_for(dc)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r2_05_question_fidelity_or_logic_and_meta_eval(make_gate_judge) -> None:
    """R2-05 — OR-logic: stated-question OR named-reformulation both pass.
    5/5 tier is meta-evaluation (explicit reframing). Uses FakeLLMJudge
    scripted per-fixture to simulate each branch.
    """
    judge, payload_for = make_gate_judge(
        "R2",
        {
            "stated_verbatim": 4,
            "named_reformulation": 4,
            "tangent_unnamed": 2,
            "meta_evaluation": 5,
        },
    )
    gate = R2Gate(judge=judge)
    assert gate.score(input_payload=payload_for("stated_verbatim")).score >= 3
    assert gate.score(input_payload=payload_for("named_reformulation")).score >= 3
    assert gate.score(input_payload=payload_for("tangent_unnamed")).score <= 2
    assert gate.score(input_payload=payload_for("meta_evaluation")).score == 5
