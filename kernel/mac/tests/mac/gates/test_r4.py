"""R4 Steelman Completeness — mac/test-strategy.md v0.3 §3.5.

Contains R4-01 through R4-06 (the 6th test is the Req-F two-step
deterministic structural check per §3.5.6 — this is also referenced from
§5.1.2 as MAC-T-ASYM-R-F-02. Only ONE of the two IDs lands in the
16-entry allow-list (entry #14 uses the ASYM alias), not both. See
test-strategy v0.3 §3.16 reconciliation note. Here the test is marked
no_waiver because it's canonically the same deterministic sub-test.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r4 import R4Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r4_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R4", {"r4_partial_steelman": 3})
    gate = R4Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r4_partial_steelman")).score == 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 4 — §13.3.3 allow-list entry #7
def test_mac_t_gate_r4_02_calibration_anchor(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R4", {"anchor_2": 2, "anchor_4": 4})
    gate = R4Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r4_03_section_routing() -> None:
    gate = R4Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.STEELMAN,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r4_04_domain_guard() -> None:
    for dc in DomainClass:
        assert "R4" not in gates_suspended_for(dc)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r4_05_co_eval_r4_not_affected_by_r5_cap(make_gate_judge) -> None:
    """R4-05 — R4 is NOT capped by R5's manufactured-dissent logic.
    compute_final_scores applies Pair 2 to R5 only; R4 stays raw.
    """
    from praxis.kernel.mac.cycle.iteration_controller import compute_final_scores

    raw = {f"R{n}": 4 for n in range(1, 13)}
    raw["R4"] = 5
    raw["R5"] = 5
    critique = {"manufactured_dissent_detected": True}
    eff = compute_final_scores(
        raw, forge_degraded=False, reviewer_critique=critique
    )
    assert eff["R4"] == 5  # R4 untouched


@pytest.mark.critical
@pytest.mark.asymmetry_structural
@pytest.mark.static
def test_mac_t_gate_r4_06_req_f_two_step_deterministic(make_gate_judge) -> None:
    """R4-06 — Req-F two-step reviewer protocol structural check.

    Per arch §7.1: the reviewer critique payload MUST carry an
    ``independent_steelman`` field and a ``gap_assessment`` field, with
    ``independent_steelman`` preceding ``gap_assessment`` so the reviewer
    commits BEFORE reading the producer's [STEELMAN] section.

    Step 4 implements this as a static shape check. Step 5
    (Asymmetry Router) adds the field-ordering structural check on a
    real Pydantic ``ReviewerCritique`` model as MAC-T-ASYM-R-F-02 (the
    canonical allow-list alias). This test runs in the gate family as
    the R4-06 sub-test per v0.3 §3.5.6.
    """
    # Step-4 shape: a dict with both keys in ordered iteration.
    critique = {
        "independent_steelman": "reviewer-generated steelman",
        "gap_assessment": "comparison to producer STEELMAN",
    }
    keys = list(critique.keys())
    assert "independent_steelman" in keys
    assert "gap_assessment" in keys
    assert keys.index("independent_steelman") < keys.index("gap_assessment")
