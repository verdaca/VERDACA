"""tests/runtime/spawner/test_budget_aggregation.py — RED commit.

ResourceBudget exhaustion cancels spawn trees.
Architecture §4.3, §9.8, S4.R-07.
"""

from __future__ import annotations

import pytest


def test_budget_exceeded_error_importable() -> None:
    from praxis.kernel.runtime.spawner.budgets import BudgetExceededError  # noqa: F401


def test_budget_token_check_raises_when_exceeded() -> None:
    from praxis.kernel.runtime.spawner.budgets import BudgetExceededError, ResourceBudget

    budget = ResourceBudget(
        max_tokens=100,
        max_wall_seconds=60.0,
        max_tool_calls=10,
        max_memory_writes=5,
    )
    with pytest.raises(BudgetExceededError):
        budget.check_tokens(consumed=101)


def test_budget_tool_call_check_raises_when_exceeded() -> None:
    from praxis.kernel.runtime.spawner.budgets import BudgetExceededError, ResourceBudget

    budget = ResourceBudget(
        max_tokens=1000,
        max_wall_seconds=60.0,
        max_tool_calls=5,
        max_memory_writes=5,
    )
    with pytest.raises(BudgetExceededError):
        budget.check_tool_calls(consumed=6)


def test_budget_within_limits_does_not_raise() -> None:
    from praxis.kernel.runtime.spawner.budgets import ResourceBudget

    budget = ResourceBudget(
        max_tokens=1000,
        max_wall_seconds=60.0,
        max_tool_calls=10,
        max_memory_writes=5,
    )
    # Should not raise
    budget.check_tokens(consumed=999)
    budget.check_tool_calls(consumed=9)


def test_budget_frozen_prevents_mutation() -> None:
    from praxis.kernel.runtime.spawner.budgets import ResourceBudget

    budget = ResourceBudget(
        max_tokens=1000,
        max_wall_seconds=60.0,
        max_tool_calls=10,
        max_memory_writes=5,
    )
    with pytest.raises((TypeError, AttributeError)):
        budget.max_tokens = 9999  # type: ignore[misc]
