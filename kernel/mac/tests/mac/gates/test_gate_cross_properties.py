"""Cross-gate property tests — mac/test-strategy.md v0.3 §3.14.

Covers MAC-T-GATE-PROP-01..06. Property-based tests over the full
(r7_raw, r8_raw) ∈ [1..5]² space for the Req-C + SQ-7 ordering —
this is the narrow Hypothesis test the step-3 team-lead constraint
authorized for step 4 (the cycle-level test-strategy v0.3 §4.6.2
narrowed to [3..5] to avoid backtrack interference; here we run the
full gate-engine [1..5]² space in isolation per test-strategy §3.14.4
property statement).
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from praxis.kernel.mac.cycle.iteration_controller import compute_final_scores
from praxis.kernel.mac.cycle.section_router import GATE_SECTION_ROUTES
from praxis.kernel.mac.gates.registry import GATE_CLASSES
from praxis.kernel.mac.testing.fakes.fake_llm_judge import FakeLLMJudge
from praxis.kernel.mac.gates.base import JudgeResponse


def _stub_judge(constant_score: int = 4) -> FakeLLMJudge:
    judge = FakeLLMJudge()
    return judge


def _fingerprint(payload: dict) -> str:
    return FakeLLMJudge._fingerprint(payload)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_prop_01_score_idempotency() -> None:
    """MAC-T-GATE-PROP-01 — compute_final_scores is idempotent: calling twice
    with identical inputs yields identical outputs (no mutation of the
    raw dict, no hidden state).
    """
    raw = {f"R{n}": 4 for n in range(1, 13)}
    a = compute_final_scores(raw, forge_degraded=False)
    b = compute_final_scores(raw, forge_degraded=False)
    assert a == b
    # Original raw dict not mutated.
    assert raw == {f"R{n}": 4 for n in range(1, 13)}


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_prop_02_section_routing_per_gate() -> None:
    """MAC-T-GATE-PROP-02 — every gate class has a matching
    ``GATE_SECTION_ROUTES`` entry.
    """
    for cls in GATE_CLASSES:
        assert cls.gate_id in GATE_SECTION_ROUTES
        # Spot check: instance returns same selectors as the constant table.
        instance = cls(judge=FakeLLMJudge())
        assert instance.section_selectors() == GATE_SECTION_ROUTES[cls.gate_id]


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@pytest.mark.f1_absorption
def test_mac_t_gate_prop_03_forge_degradation_monotonicity() -> None:
    """MAC-T-GATE-PROP-03 — for every gate ``G`` in FORGE_PENALTY_SET,
    ``G.effective(..., forge_degraded=True) <= G.effective(..., forge_degraded=False)``.
    Forge never INCREASES a score. Expressed via compute_final_scores
    per arch §6.3 SQ-7.
    """
    for r7_raw in range(1, 6):
        raw = {f"R{n}": 4 for n in range(1, 13)}
        raw["R7"] = r7_raw
        eff_no = compute_final_scores(raw, forge_degraded=False)
        eff_yes = compute_final_scores(raw, forge_degraded=True)
        assert eff_yes["R7"] <= eff_no["R7"]


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@given(
    r7_raw=st.integers(min_value=1, max_value=5),
    r8_raw=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=50, deadline=5000)
def test_mac_t_gate_prop_04_co_eval_cap_uses_raw_r7(r7_raw: int, r8_raw: int) -> None:
    """MAC-T-GATE-PROP-04 — Req-C Pair 1 property over full [1..5]².

    Per team-lead step-3 → step-4 constraint 2: the full [1..5]² space
    runs HERE at the gate engine level (isolated from backtrack
    interference), not at the cycle level. Invariant:

        R8_eff == min(R8_raw, R7_raw + 1)   (always uses RAW R7)
    """
    raw = {f"R{n}": 4 for n in range(1, 13)}
    raw["R7"] = r7_raw
    raw["R8"] = r8_raw
    eff = compute_final_scores(raw, forge_degraded=False)
    assert eff["R8"] == min(r8_raw, r7_raw + 1)
    # R7 effective is unchanged when not Forge-degraded.
    assert eff["R7"] == r7_raw


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
@given(
    r_value=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=25, deadline=5000)
def test_mac_t_gate_prop_05_score_range_invariant(r_value: int) -> None:
    """MAC-T-GATE-PROP-05 — every effective score is in [1, 5] EXCEPT
    suspended gates which are explicitly 0 (arch §6.5 Req-E).
    """
    raw = {f"R{n}": r_value for n in range(1, 13)}
    eff = compute_final_scores(raw, forge_degraded=False)
    for gate_id, score in eff.items():
        assert 1 <= score <= 5, f"{gate_id} out of range: {score}"


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_gate_prop_06_gate_registry_has_exactly_12_entries() -> None:
    """MAC-T-GATE-PROP-06 — arch §6.1: exactly 12 gates, R1..R12, no R13."""
    assert len(GATE_CLASSES) == 12
    gate_ids = {cls.gate_id for cls in GATE_CLASSES}
    assert gate_ids == {f"R{n}" for n in range(1, 13)}
    assert "R13" not in gate_ids
