"""Cycle budget enforcement tests — mac/test-strategy.md v0.3 §4.3.

Covers ``MAC-T-CYCLE-BUDGET-01/02/03``. All three anchor on arch §5.7
ResourceBudget Defaults + runtime §4.3 ResourceBudget (citation repaired
at v0.3 §4.3 from the v0.1 ``§5.3 budget`` drift).

Anchors:
  - mac/architecture.md §5.7 ResourceBudget Defaults
  - runtime/architecture.md §4.3 ResourceBudget (inherited semantics)
  - mac/architecture.md §5.2 terminal transition footnote (lines 555–557)
  - mac/architecture.md §10.1 Pi-Mono Integration
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from praxis.kernel.mac.budget import BudgetExceededError, ResourceBudget
from praxis.kernel.mac.cycle import CycleScenario, IterationController, State
from praxis.kernel.mac.integrations.pi_mono import (
    FakeCostTracker,
    MacCostHook,
)
from praxis.kernel.mac.testing.fakes.frozen_clock import FrozenClock


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_cycle_budget_01_token_budget_halt() -> None:
    """MAC-T-CYCLE-BUDGET-01 — token budget halt transitions to FAILED.

    When cumulative token usage exceeds ``ResourceBudget.max_tokens``,
    the budget check raises ``BudgetExceededError``. The Iteration
    Controller catches this at the cycle boundary and transitions to
    ``State.FAILED`` per arch §5.2 footnote terminal transition.
    """
    tiny_budget = ResourceBudget(
        max_tokens=1000,
        max_wall_seconds=900.0,
        max_tool_calls=200,
        max_memory_writes=100,
    )
    ctrl = IterationController(budget=tiny_budget)
    raw = {f"R{n}": 4 for n in range(1, 13)}

    result = await ctrl.run(
        CycleScenario(cycle_1_raw_scores=raw, tokens_per_cycle=50_000)
    )

    assert result.final_state == State.FAILED
    assert result.terminal_reason == "budget_exceeded"
    assert result.total_tokens >= 50_000


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.wall_clock
async def test_mac_t_cycle_budget_02_wall_clock_halt() -> None:
    """MAC-T-CYCLE-BUDGET-02 — wall-clock budget halt.

    Using ``FrozenClock`` to advance virtual time past
    ``ResourceBudget.max_wall_seconds``, assert the budget check raises
    ``BudgetExceededError`` and the controller transitions to
    ``State.FAILED`` at the next cycle boundary.
    """
    tight_budget = ResourceBudget(
        max_tokens=400_000,
        max_wall_seconds=30.0,  # tight deadline
        max_tool_calls=200,
        max_memory_writes=100,
    )
    clock = FrozenClock(initial=datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc))
    ctrl = IterationController(budget=tight_budget, clock=clock)
    raw = {f"R{n}": 4 for n in range(1, 13)}

    result = await ctrl.run(
        CycleScenario(
            cycle_1_raw_scores=raw,
            wall_seconds_per_cycle=60.0,  # exceeds 30s deadline after cycle 1
            tokens_per_cycle=10_000,
        )
    )

    assert result.final_state == State.FAILED
    assert result.terminal_reason == "budget_exceeded"
    assert result.elapsed_seconds >= 30.0


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_cycle_budget_03_pi_mono_cost_tracker_integration() -> None:
    """MAC-T-CYCLE-BUDGET-03 — Pi-Mono ``CostTracker.track_cost`` integration.

    The ``MacCostHook`` wraps ``CostTracker.track_cost`` per arch §10.1.
    Every LLM call emits one CostEvent via the hook. Assert that the
    hook's ``total_cost`` matches the sum of per-call costs when invoked
    multiple times with the canonical ``request_id`` format
    ``f"mac:{cycle_id}:{cycle_phase}:{call_seq}"``.
    """
    tracker = FakeCostTracker()
    hook = MacCostHook(cost_tracker=tracker)

    await hook.emit_cycle_cost(
        cycle_id="01HX000000000000000000000A",
        cycle_phase="produce",
        call_seq=0,
        model="claude-opus-4-6",
        prompt_tokens=1000,
        completion_tokens=500,
        usd_cost=0.45,
    )
    await hook.emit_cycle_cost(
        cycle_id="01HX000000000000000000000A",
        cycle_phase="review",
        call_seq=0,
        model="claude-opus-4-6",
        prompt_tokens=800,
        completion_tokens=400,
        usd_cost=0.30,
    )

    # Per-call costs sum correctly.
    assert tracker.total_cost_usd == pytest.approx(0.75)
    assert tracker.total_tokens == 1000 + 500 + 800 + 400

    # request_id format matches arch §10.1 line 1522 verbatim.
    assert tracker.events[0][0].request_id == "mac:01HX000000000000000000000A:produce:0"
    assert tracker.events[1][0].request_id == "mac:01HX000000000000000000000A:review:0"


def test_resource_budget_defaults_match_arch_5_7() -> None:
    """Coverage-floor check — default ResourceBudget matches arch §5.7 values.

    Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
    Stage 5.3 preload Q3 disposition 2026-04-14.
    """
    budget = ResourceBudget()
    assert budget.max_tokens == 400_000
    assert budget.max_wall_seconds == 900.0
    assert budget.max_tool_calls == 200
    assert budget.max_memory_writes == 100


def test_resource_budget_check_tool_calls_and_memory_writes() -> None:
    """Coverage-floor check — check_tool_calls and check_memory_writes boundaries.

    Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
    Stage 5.3 preload Q3 disposition 2026-04-14.
    """
    budget = ResourceBudget(
        max_tokens=1000,
        max_wall_seconds=10.0,
        max_tool_calls=5,
        max_memory_writes=3,
    )
    budget.check_tool_calls(5)  # exactly at ceiling — ok
    with pytest.raises(BudgetExceededError, match="tool-call"):
        budget.check_tool_calls(6)

    budget.check_memory_writes(3)
    with pytest.raises(BudgetExceededError, match="memory-write"):
        budget.check_memory_writes(4)
