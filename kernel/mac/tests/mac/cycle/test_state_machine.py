"""Cycle state-machine tests — mac/test-strategy.md v0.3 §4.2.

Covers ``MAC-T-CYCLE-STATE-01/02/04/05``. STATE-03 retired v0.3.

Anchors:
  - mac/architecture.md §5.2 State Machine (9 states, linear, single backtrack)
  - mac/architecture.md §5.2 terminal transitions footnote (lines 555–557)
  - mac/architecture.md §5.6 Forge Fallback Handling (behavioral, not state)
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle import (
    ALLOWED_TRANSITIONS,
    CycleScenario,
    InvalidStateTransitionError,
    IterationController,
    State,
    TERMINAL_STATES,
)


def _good_raw_scores() -> dict[str, int]:
    """Return a raw-score vector with every gate at 4 (above critical floor)."""
    return {f"R{n}": 4 for n in range(1, 13)}


def _bad_raw_scores(failed_gate: str = "R4") -> dict[str, int]:
    """Return a raw-score vector where ``failed_gate`` is 2 (below critical)."""
    scores = _good_raw_scores()
    scores[failed_gate] = 2
    return scores


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_self_consistency
async def test_mac_t_cycle_state_01_reachability_of_both_terminals() -> None:
    """MAC-T-CYCLE-STATE-01 — arch §5.2 terminal reachability.

    Drive the controller through a normal-path scenario (all Critical gates
    >= 3) and assert ``State.COMPLETE`` is reached. Then drive it through
    a second-consecutive-Critical scenario and assert ``State.FAILED`` is
    reached. Both arch §5.2 terminals are reachable.
    """
    # Path A: normal completion → COMPLETE
    ctrl_a = IterationController()
    good_scores = _good_raw_scores()
    result_a = await ctrl_a.run(CycleScenario(cycle_1_raw_scores=good_scores))
    assert result_a.final_state == State.COMPLETE
    assert State.COMPLETE in TERMINAL_STATES

    # Path B: second-consecutive-Critical → FAILED
    ctrl_b = IterationController()
    bad_scores = _bad_raw_scores("R4")
    result_b = await ctrl_b.run(
        CycleScenario(
            cycle_1_raw_scores=bad_scores,
            cycle_2_raw_scores=bad_scores,  # same failure on retry
        )
    )
    assert result_b.final_state == State.FAILED
    assert State.FAILED in TERMINAL_STATES


@pytest.mark.critical
@pytest.mark.mac_self_consistency
def test_mac_t_cycle_state_02_no_invalid_transitions() -> None:
    """MAC-T-CYCLE-STATE-02 — no transition outside ALLOWED_TRANSITIONS fires.

    Directly probe the controller's private ``_transition`` method with
    every possible ``(from, to)`` pair from ``State × State``, asserting
    that only the allowed edges succeed and every other pair raises
    ``InvalidStateTransitionError``. This exhaustively validates the
    guard rail that the Hypothesis stateful test relies on at step 4+.
    """
    for src in State:
        for dst in State:
            ctrl = IterationController()
            ctrl._state = src  # type: ignore[attr-defined]
            edge_is_allowed = (src, dst) in ALLOWED_TRANSITIONS
            if edge_is_allowed:
                ctrl._transition(dst)  # type: ignore[attr-defined]
                assert ctrl.state == dst
            else:
                with pytest.raises(InvalidStateTransitionError):
                    ctrl._transition(dst)  # type: ignore[attr-defined]


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_self_consistency
async def test_mac_t_cycle_state_04_second_consecutive_critical_fails() -> None:
    """MAC-T-CYCLE-STATE-04 — arch §5.2 footnote second-consecutive-Critical path.

    In cycle 1, a Critical gate (R4 Steelman Completeness per arch §6.1)
    scores raw 2, triggering ``BACKTRACK_SET`` and re-entry to Cycle 1
    with ``backtrack_count = 1``. In the retry pass, the SAME (or another)
    Critical gate again scores raw 2, and because ``backtrack_count == 1``
    the controller transitions to ``FAILED`` rather than backtracking
    again.
    """
    ctrl = IterationController()
    bad_r4 = _bad_raw_scores("R4")
    result = await ctrl.run(
        CycleScenario(
            cycle_1_raw_scores=bad_r4,
            cycle_2_raw_scores=bad_r4,  # still failing on retry
        )
    )

    assert result.final_state == State.FAILED
    assert result.backtrack_count == 1
    assert result.terminal_reason == "second_consecutive_critical_gate_failure"

    # Verify backtrack actually fired between the two CYCLE_3_VERIFY visits.
    log = result.state_transition_log
    assert log.count(State.BACKTRACK_SET) == 1
    assert log.count(State.CYCLE_3_VERIFY) == 2

    # Critical architectural property: this is NOT a hard-fail short-circuit.
    # Both cycles run to CYCLE_3_VERIFY before the terminal transition fires.
    # There is no early exit from cycle 1 on R11 or R12 score 1 — those gates
    # are priority High, NOT hard-fail per arch §6.1.
    assert log.count(State.CYCLE_1_PRODUCE) == 2
    assert log.count(State.CYCLE_2_REVIEW) == 2


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_self_consistency
@pytest.mark.f1_absorption
async def test_mac_t_cycle_state_05_forge_degradation_behavioral_path() -> None:
    """MAC-T-CYCLE-STATE-05 — arch §5.6 behavioral Forge-degradation integration.

    When the compressor signals ``reasoning_preserved=False``, the controller
    does NOT transition to a dedicated "fallback" state. Instead it proceeds
    through arch §5.2 normal states and the Quality Gate Engine applies the
    R7 penalty per arch §6.3 SQ-7 step 3 (penalty to ``R7_effective`` only,
    AFTER Req-C caps).

    This is the CYCLE-LEVEL behavioral complement to the gate-unit test
    ``MAC-T-GATE-R7-05`` (step 4 §3.8.5). Here we assert the full 3-cycle
    pipeline enforces the ordering, not just the gate evaluator in isolation.
    """
    ctrl = IterationController()
    raw = _good_raw_scores()  # all gates start at 4
    result = await ctrl.run(
        CycleScenario(
            cycle_1_raw_scores=raw,
            forge_degraded=True,
        )
    )

    # Normal path — no fabricated FORGE_FALLBACK state.
    assert result.final_state in (State.COMPLETE, State.FAILED)
    assert result.final_state == State.COMPLETE
    assert result.forge_degraded is True

    # R7_effective reflects the penalty applied AFTER Req-C caps.
    assert result.final_scores is not None
    assert result.final_scores["R7"] == 3  # raw 4 minus Forge penalty

    # Critical ordering property: R8 cap is computed from RAW R7 (pre-Forge),
    # not penalized R7. raw R7=4 → R8 cap = min(R8_raw, 4+1) = min(4, 5) = 4.
    assert result.final_scores["R8"] == 4

    # Telemetry observation: forge_degradation_detected event emitted.
    event_names = [name for name, _ in result.emitted_events]
    assert "mac.cycle.forge_degradation_detected" in event_names
