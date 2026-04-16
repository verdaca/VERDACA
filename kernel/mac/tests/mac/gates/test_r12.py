"""R12 Internal Consistency — mac/test-strategy.md v0.3 §3.13.

Contains R12-05 under the Q-1 v0.3 rename: the test function MUST be
named ``test_mac_t_gate_r12_05_direct_contradiction_detector`` (NOT the
v0.1 ``_hard_fail_policy`` name). Allow-list entry #13 uses this exact
nodeid.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r12 import R12Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r12_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R12", {"r12_minor_tension": 4})
    gate = R12Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r12_minor_tension")).score == 4


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r12_02_calibration_anchor(make_gate_judge) -> None:
    """R12-02 — NOT no_waiver (only R12-05 carries no_waiver for R12)."""
    judge, payload_for = make_gate_judge("R12", {"anchor_2": 2, "anchor_4": 4})
    gate = R12Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r12_03_section_routing() -> None:
    gate = R12Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.FULL,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r12_04_domain_guard() -> None:
    for dc in DomainClass:
        assert "R12" not in gates_suspended_for(dc)


# Allow-list entry #13: Q-1 v0.3 rename — function name is
# direct_contradiction_detector, NOT hard_fail_policy.
@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 12 — §13.3.3 allow-list entry #13
def test_mac_t_gate_r12_05_direct_contradiction_detector(make_gate_judge) -> None:
    """MAC-T-GATE-R12-05 — direct cross-section contradiction detector.

    Q-1 v0.3 rename: this function MUST be named
    ``test_mac_t_gate_r12_05_direct_contradiction_detector`` (NOT the
    v0.1 ``_hard_fail_policy`` name). The allow-list entry #13 in
    step 6's meta-test references this exact nodeid.

    Rule (test-strategy v0.3 §3.13.5 + quality-rubric.md §6 R12):
      - Fixture with cross-section contradiction → R12_eff ≤ 2
      - Fixture with no contradiction (negative control) → R12_eff ≥ 4
      - Rationale field flags the contradicting text spans
    """
    judge, payload_for = make_gate_judge(
        "R12",
        {
            "contradiction_findings_recs": 2,
            "consistent_analysis": 4,
        },
    )
    gate = R12Gate(judge=judge)

    bad = gate.score(input_payload=payload_for("contradiction_findings_recs"))
    good = gate.score(input_payload=payload_for("consistent_analysis"))

    assert bad.score <= 2
    assert good.score >= 4

    # Rationale carries gate_id + fixture_id so reviewers can trace.
    assert "R12" in bad.rationale
    assert "contradiction_findings_recs" in bad.rationale
