"""R9 Evidence Impartiality — mac/test-strategy.md v0.3 §3.10."""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r9 import R9Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r9_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R9", {"r9_partial_impartial": 3})
    gate = R9Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r9_partial_impartial")).score == 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r9_02_calibration_anchor(make_gate_judge) -> None:
    """R9-02 — NOT no_waiver (R9 is priority Medium)."""
    judge, payload_for = make_gate_judge("R9", {"anchor_2": 2, "anchor_4": 4})
    gate = R9Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r9_03_section_routing_findings_only() -> None:
    """R9-03 — arch §6.2 TRIZ-3: R9 → FINDINGS ONLY. STEELMAN/DISSENT exempt."""
    gate = R9Gate(judge=type("J", (), {"score": lambda **_: None})())
    selectors = gate.section_selectors()
    assert selectors == (SectionSelector.FINDINGS,)
    assert SectionSelector.STEELMAN not in selectors
    assert SectionSelector.DISSENT not in selectors


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r9_04_domain_guard() -> None:
    for dc in DomainClass:
        assert "R9" not in gates_suspended_for(dc)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r9_05_proportionality_and_steelman_exemption(
    make_gate_judge,
) -> None:
    """R9-05 — per v0.3 §3.10.5: proportionality + STEELMAN/DISSENT exemption.

    Identical FINDINGS text, three outputs with under-committed /
    proportional / over-committed recommendation strength. R9 scores
    should rank over_committed < proportional regardless of what the
    STEELMAN section says.
    """
    judge, payload_for = make_gate_judge(
        "R9",
        {
            "findings_proportional": 4,
            "findings_over_committed": 2,
            "findings_under_committed": 3,
        },
    )
    gate = R9Gate(judge=judge)
    prop = gate.score(input_payload=payload_for("findings_proportional")).score
    over = gate.score(input_payload=payload_for("findings_over_committed")).score
    assert prop > over
