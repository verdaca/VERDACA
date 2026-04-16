"""Forge-degradation ordering tests — mac/test-strategy.md v0.3 §4.6.

Covers ``MAC-T-CYCLE-FORGE-01/02/03``. SQ-7 three-step ordering enforced
at the cycle level.

Anchors:
  - mac/architecture.md §6.3 SQ-7 ordering
  - mac/architecture.md §5.6 Forge Fallback Handling
  - test-strategy.md v0.3 §4.6 Forge-Degradation Ordering (Tension #4)
  - mac/test-strategy.md v0.3 §3.2.5 R1 Forge-degradation path anchor
    (v0.3 surviving §12.5 citation — see preload Q1 disposition)
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from praxis.kernel.mac.cycle import (
    CycleScenario,
    IterationController,
    State,
    compute_final_scores,
)


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_self_consistency
@pytest.mark.f1_absorption
async def test_mac_t_cycle_forge_01_sq7_worked_example() -> None:
    """MAC-T-CYCLE-FORGE-01 — the arch §6.3 SQ-7 worked example at cycle level.

    With ``(R7_raw=4, R8_raw=4, forge_degraded=True)``, assert the final
    effective scores are ``R7_eff=3, R8_eff=4`` per arch §6.3 three-step
    ordering:

      1. Raw scores R7=4, R8=4
      2. Req-C cap using RAW R7: R8_eff = min(4, 4+1) = 4 (no cap fires)
      3. Forge penalty LAST on R7_effective only: R7_eff = max(1, 4-1) = 3

    Result: R7=3, R8=4. Critically NOT R8=3 — if Forge penalty propagated
    into the R8 cap (step 2 using post-penalty R7), we would see R8=min(4,
    3+1)=4 which HAPPENS to be the same here but for different reasons;
    the property test below proves the distinction for other inputs.

    Note on anchor: v0.3 test-strategy §3.2.5 and §15.3A still carry a
    stale ``§12.5 SQ-7`` citation. Per Stage 5.3 preload Q1 disposition
    (2026-04-14), the corrected anchor is arch §5.6 + §6.3 SQ-7 ordering.
    """
    # v0.3 test-strategy.md §3.2.5 has stale §12.5 SQ-7 anchor;
    # corrected anchor is arch §5.6 + §6.3 SQ-7 ordering
    ctrl = IterationController()
    raw = {f"R{n}": 4 for n in range(1, 13)}
    result = await ctrl.run(
        CycleScenario(cycle_1_raw_scores=raw, forge_degraded=True)
    )

    assert result.final_state == State.COMPLETE
    assert result.final_scores is not None
    assert result.final_scores["R7"] == 3
    assert result.final_scores["R8"] == 4


@pytest.mark.critical
@pytest.mark.mac_self_consistency
@pytest.mark.f1_absorption
@given(
    r7_raw=st.integers(min_value=3, max_value=5),
    r8_raw=st.integers(min_value=3, max_value=5),
    forge_degraded=st.booleans(),
)
@settings(max_examples=50, deadline=5000)
def test_mac_t_cycle_forge_02_ordering_property(
    r7_raw: int, r8_raw: int, forge_degraded: bool
) -> None:
    """MAC-T-CYCLE-FORGE-02 — property test over (r7_raw, r8_raw, forge_degraded).

    Hypothesis over ``(r7_raw ∈ [3..5], r8_raw ∈ [3..5], forge_degraded ∈
    {True, False})`` — the non-critical subspace where neither R7 nor R8
    triggers backtracking. For each input, the final effective scores
    must match the 3-step SQ-7 algorithm, NOT any interleaved ordering.

    Invariant (arch §6.3 SQ-7):
      - R8_eff == min(r8_raw, r7_raw + 1)            ← always uses RAW R7
      - R7_eff == r7_raw                              ← when not degraded
      - R7_eff == max(1, r7_raw - 1)                  ← when degraded

    Note: the test narrows to raw ∈ [3..5] to avoid Critical-gate
    failure paths that would trigger backtracking and confuse the
    per-gate assertion. The full [1..5]² space is covered at the
    step-4 `MAC-T-GATE-PROP-04` Hypothesis test on the gate engine.
    """
    # v0.3 test-strategy.md §3.2.5 has stale §12.5 SQ-7 anchor;
    # corrected anchor is arch §5.6 + §6.3 SQ-7 ordering
    raw = {f"R{n}": 4 for n in range(1, 13)}
    raw["R7"] = r7_raw
    raw["R8"] = r8_raw
    effective = compute_final_scores(raw, forge_degraded=forge_degraded)

    # R8 always uses RAW R7 for its cap.
    assert effective["R8"] == min(r8_raw, r7_raw + 1)

    # R7 effective: raw minus Forge penalty if degraded, floored at 1.
    if forge_degraded:
        assert effective["R7"] == max(1, r7_raw - 1)
    else:
        assert effective["R7"] == r7_raw


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
@pytest.mark.f1_absorption
async def test_mac_t_cycle_forge_03_telemetry_on_fallback() -> None:
    """MAC-T-CYCLE-FORGE-03 — Forge fallback emits telemetry.

    When Forge fallback triggers, a ``mac.cycle.forge_degradation_detected``
    event is emitted in the event sequence. Step 3 doesn't yet implement
    the full ``[forge_degradation_detected, forge_fallback_triggered,
    forge_single_pass_started]`` triad — step 4 refines this when the
    Quality Gate Engine's Forge penalty pass lands. Here we assert only
    the detection event.
    """
    ctrl = IterationController()
    raw = {f"R{n}": 4 for n in range(1, 13)}
    result = await ctrl.run(
        CycleScenario(cycle_1_raw_scores=raw, forge_degraded=True)
    )

    event_names = [name for name, _ in result.emitted_events]
    assert "mac.cycle.forge_degradation_detected" in event_names
