"""Backtracking tests — mac/test-strategy.md v0.3 §4.4.

Covers ``MAC-T-CYCLE-BACKTRACK-01/02``. Backtrack fires AT MOST ONCE per
deliberation per arch §5.5 / §5.2 footnote.

Anchors:
  - mac/architecture.md §5.5 Backtracking on Critical Gate Failure
  - mac/architecture.md §5.2 footnote (second-consecutive-Critical → FAILED)
  - mac/architecture.md §5.3 Phase Runner (state threading)
  - mac/architecture.md §7.1 Req-F
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle import CycleScenario, IterationController, State


def _bad_r4(failed: int = 2) -> dict[str, int]:
    return {**{f"R{n}": 4 for n in range(1, 13)}, "R4": failed}


def _good_all() -> dict[str, int]:
    return {f"R{n}": 4 for n in range(1, 13)}


@pytest.mark.asyncio
@pytest.mark.critical
async def test_mac_t_cycle_backtrack_01_reuses_prior_cycle_artifacts() -> None:
    """MAC-T-CYCLE-BACKTRACK-01 — retry producer receives prior artifacts.

    When ``CYCLE_3_VERIFY`` fires ``BACKTRACK_SET`` (first Critical gate
    failure, ``backtrack_count == 0``) and re-enters ``CYCLE_1_PRODUCE``,
    the retry producer receives the prior-cycle reviewer critique AND
    the prior-cycle producer output via the scenario's
    ``prior_producer_output`` / ``prior_reviewer_critique`` fields.
    Step 3 exposes this as the ``retry_producer_input`` field on
    :class:`ControllerResult`.
    """
    ctrl = IterationController()
    result = await ctrl.run(
        CycleScenario(
            cycle_1_raw_scores=_bad_r4(),       # first pass fails R4
            cycle_2_raw_scores=_good_all(),     # retry succeeds
            prior_producer_output="cycle1-output-payload",
            prior_reviewer_critique="cycle1-reviewer-critique",
        )
    )

    # Backtrack fired and retry eventually succeeded.
    assert result.final_state == State.COMPLETE
    assert result.backtrack_count == 1

    # Prior artifacts were surfaced to the retry producer.
    assert result.retry_producer_input == (
        "cycle1-output-payload",
        "cycle1-reviewer-critique",
    )


@pytest.mark.asyncio
@pytest.mark.critical
async def test_mac_t_cycle_backtrack_02_fires_at_most_once() -> None:
    """MAC-T-CYCLE-BACKTRACK-02 — backtrack fires exactly once per task.

    Per arch §5.2 footnote (lines 555–557), ``BACKTRACK_SET`` is entered
    exactly once per task. After ``backtrack_count == 1``, a second
    Critical failure terminates to ``FAILED`` rather than re-entering
    ``BACKTRACK_SET``.

    Assert: ``state_transition_log.count(State.BACKTRACK_SET) == 1`` and
    ``final_state == State.FAILED``.
    """
    ctrl = IterationController()
    result = await ctrl.run(
        CycleScenario(
            cycle_1_raw_scores=_bad_r4(),  # first pass fails R4
            cycle_2_raw_scores=_bad_r4(),  # second pass also fails R4
        )
    )

    assert result.final_state == State.FAILED
    assert result.state_transition_log.count(State.BACKTRACK_SET) == 1
    assert result.backtrack_count == 1
    assert result.terminal_reason == "second_consecutive_critical_gate_failure"
