"""R5 Dissent Preservation — mac/test-strategy.md v0.3 §3.6."""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.iteration_controller import compute_final_scores
from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r5 import R5Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r5_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R5", {"r5_partial_dissent": 3})
    gate = R5Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r5_partial_dissent")).score == 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 5 — §13.3.3 allow-list entry #8
def test_mac_t_gate_r5_02_calibration_anchor(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R5", {"anchor_2": 2, "anchor_4": 4})
    gate = R5Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r5_03_section_routing() -> None:
    gate = R5Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.DISSENT,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r5_04_domain_guard_consensus_suspends() -> None:
    """R5-04 — arch §6.5 Req-E: DomainClass.CONSENSUS suspends R5."""
    assert "R5" in gates_suspended_for(DomainClass.CONSENSUS)
    assert "R5" not in gates_suspended_for(DomainClass.CONTESTED)
    assert "R5" not in gates_suspended_for(DomainClass.DIAGNOSTIC)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r5_05_manufactured_dissent_cap_via_req_c_pair_2() -> None:
    """R5-05 — Req-C Pair 2 cap: when reviewer flags manufactured
    dissent, R5_eff = min(R5_raw, R4_raw). Uses the step-3 compute_final_scores
    evolved signature.

    Worked examples per step-4 go signal:
      - (R4_raw=5, R5_raw=5, manufactured=True) → R5_eff = min(5, 5) = 5
      - (R4_raw=2, R5_raw=5, manufactured=True) → R5_eff = min(5, 2) = 2
    """
    critique = {"manufactured_dissent_detected": True}

    # Case A: strong R4 — cap is not tight.
    raw_a = {f"R{n}": 4 for n in range(1, 13)}
    raw_a["R4"] = 5
    raw_a["R5"] = 5
    eff_a = compute_final_scores(
        raw_a, forge_degraded=False, reviewer_critique=critique
    )
    assert eff_a["R5"] == 5  # min(5, 5) = 5

    # Case B: weak R4 — cap clamps R5 hard.
    raw_b = {f"R{n}": 4 for n in range(1, 13)}
    raw_b["R4"] = 2
    raw_b["R5"] = 5
    eff_b = compute_final_scores(
        raw_b, forge_degraded=False, reviewer_critique=critique
    )
    assert eff_b["R5"] == 2  # min(5, 2) = 2

    # Case C: no manufactured dissent signal — no cap applied.
    no_critique = {"manufactured_dissent_detected": False}
    eff_c = compute_final_scores(
        raw_b, forge_degraded=False, reviewer_critique=no_critique
    )
    assert eff_c["R5"] == 5  # R5 untouched
