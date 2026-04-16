"""R7 Reasoning Traceability — mac/test-strategy.md v0.3 §3.8."""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle.iteration_controller import (
    FORGE_PENALTY_SET,
    compute_final_scores,
)
from praxis.kernel.mac.cycle.section_router import SectionSelector
from praxis.kernel.mac.gates.guards import gates_suspended_for
from praxis.kernel.mac.gates.r7 import R7Gate
from praxis.kernel.mac.task import DomainClass


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r7_01_unit_scoring(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R7", {"r7_partial_traceability": 3})
    gate = R7Gate(judge=judge)
    assert gate.score(input_payload=payload_for("r7_partial_traceability")).score == 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.no_waiver  # Decision 1 item 6 — §13.3.3 allow-list entry #9
def test_mac_t_gate_r7_02_calibration_anchor(make_gate_judge) -> None:
    judge, payload_for = make_gate_judge("R7", {"anchor_2": 2, "anchor_4": 4})
    gate = R7Gate(judge=judge)
    assert gate.score(input_payload=payload_for("anchor_2")).score <= 2
    assert gate.score(input_payload=payload_for("anchor_4")).score >= 4


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_r7_03_section_routing() -> None:
    gate = R7Gate(judge=type("J", (), {"score": lambda **_: None})())
    assert gate.section_selectors() == (SectionSelector.L2,)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_r7_04_domain_guard() -> None:
    for dc in DomainClass:
        assert "R7" not in gates_suspended_for(dc)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.f1_absorption
def test_mac_t_gate_r7_05_forge_degradation_penalty_applies_last() -> None:
    """R7-05 — Forge penalty applies LAST (arch §6.3 SQ-7 step 3).

    Note: v0.3 test-strategy §3.8.5 has stale §12.5 SQ-7 anchor;
    corrected anchor is arch §5.6 + §6.3 SQ-7 ordering.
    """
    # v0.3 test-strategy.md §3.8.5 has stale §12.5 SQ-7 anchor;
    # corrected anchor is arch §5.6 + §6.3 SQ-7 ordering
    assert "R7" in FORGE_PENALTY_SET

    raw = {f"R{n}": 4 for n in range(1, 13)}
    eff_no_forge = compute_final_scores(raw, forge_degraded=False)
    eff_forge = compute_final_scores(raw, forge_degraded=True)
    assert eff_no_forge["R7"] == 4
    assert eff_forge["R7"] == 3


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.f1_absorption
def test_mac_t_gate_r7_06_co_eval_worked_example_uses_raw_r7() -> None:
    """R7-06 — Worked example (R7_raw=2, R8_raw=4) → R8_eff=3.

    The Req-C Pair 1 cap uses RAW R7 (not effective). With R7_raw=2,
    R8_eff = min(4, 2+1) = 3. R7 unchanged (no Forge).
    """
    raw = {f"R{n}": 4 for n in range(1, 13)}
    raw["R7"] = 2
    raw["R8"] = 4
    eff = compute_final_scores(raw, forge_degraded=False)
    assert eff["R7"] == 2
    assert eff["R8"] == 3  # min(4, 2+1) = 3
