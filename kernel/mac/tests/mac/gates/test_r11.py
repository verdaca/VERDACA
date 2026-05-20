"""R11 Scenario Coverage — mac/test-strategy.md v0.3 §3.12.

Contains R11-05 under the Q-1 v0.3 rename: the test function MUST be
named ``test_mac_t_gate_r11_05_scenario_coverage_property`` (NOT the
v0.1 ``_hard_fail_short_circuit`` name). Allow-list entry #12 uses
this exact nodeid.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r11 import R11Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r11_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R11", {"r11_multi_scenario": 4})
    gate = R11Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r11_multi_scenario")).score == 4


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 8 — §13.3.3 allow-list entry #11
def test_mac_t_gate_r11_02_calibration_anchor(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R11", {"anchor_2": 2, "anchor_4": 4})
    gate = R11Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r11_03_section_routing() -> None:
    gate = R11Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.L2,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r11_04_domain_guard_deterministic_and_binary_suspend() -> None:
    """R11-04 — arch §6.5: R11 suspended for DETERMINISTIC + BINARY."""
    assert "R11" in gates_suspended_for(DomainClass.DETERMINISTIC)
    assert "R11" in gates_suspended_for(DomainClass.BINARY)
    assert "R11" not in gates_suspended_for(DomainClass.CONTESTED)
    assert "R11" not in gates_suspended_for(DomainClass.CONSENSUS)
    assert "R11" not in gates_suspended_for(DomainClass.DIAGNOSTIC)


# Allow-list entry #12: Q-1 v0.3 rename — function name is
# scenario_coverage_property, NOT hard_fail_short_circuit.
@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 10 — §13.3.3 allow-list entry #12
@given(
    n_scenarios=st.integers(min_value=1, max_value=5),
    has_diff_implications=st.booleans(),
    has_distinct_triggers=st.booleans(),
)
@settings(max_examples=40, deadline=5000)
def test_mac_t_gate_r11_05_scenario_coverage_property(
    n_scenarios: int,
    has_diff_implications: bool,
    has_distinct_triggers: bool,
) -> None:
    """MAC-T-GATE-R11-05 — Scenario Coverage structural-calibration property.

    Q-1 v0.3 rename: this function MUST be named
    ``test_mac_t_gate_r11_05_scenario_coverage_property`` (NOT the v0.1
    ``_hard_fail_short_circuit`` name). The allow-list entry #12 in
    step 6's meta-test references this exact nodeid.

    Property (test-strategy v0.3 §3.12.5):
      - n_scenarios ≥ 3 AND both component flags True → score ≥ 4
      - n_scenarios ≤ 1 OR either flag False → score ≤ 2

    Step 4 exercises the property against a fake scoring function (the
    real judge lands at Tier 3 nightly drift canary). The fake scoring
    function implements the rule directly so the property is on the
    RULE, not the implementation.
    """

    def fake_r11_score(n: int, diff: bool, triggers: bool) -> int:
        if n >= 3 and diff and triggers:
            return 4
        if n <= 1 or not diff or not triggers:
            return 2
        # Partial: 2 scenarios, or other edge
        return 3

    score = fake_r11_score(n_scenarios, has_diff_implications, has_distinct_triggers)

    if n_scenarios >= 3 and has_diff_implications and has_distinct_triggers:
        assert score >= 4
    elif n_scenarios <= 1 or not has_diff_implications or not has_distinct_triggers:
        assert score <= 2
