"""tests/runtime/spawner/test_cycle_detection.py — RED commit.

Cycle detection: A → B → A pattern raises CircularSpawnError.
Architecture §9.8, S4.R-07.
"""

from __future__ import annotations

import pytest


def test_a_to_b_to_a_raises_circular() -> None:
    from praxis.kernel.runtime.spawner.circular_guard import CircularSpawnError, CircularSpawnGuard

    guard = CircularSpawnGuard(max_recursion_per_agent=2)
    # A → B → A: agent-a appears at depth 0 and would appear again at depth 2
    with pytest.raises(CircularSpawnError):
        guard.check_spawn(
            agent_name="agent-a",
            spawn_depth=2,
            ancestor_chain=["agent-a", "agent-b"],
        )


def test_no_cycle_no_error() -> None:
    from praxis.kernel.runtime.spawner.circular_guard import CircularSpawnGuard

    guard = CircularSpawnGuard(max_recursion_per_agent=2)
    # Linear chain, no repeats
    guard.check_spawn(
        agent_name="agent-c",
        spawn_depth=2,
        ancestor_chain=["agent-a", "agent-b"],
    )


def test_agent_appearing_three_times_raises() -> None:
    """Same agent appearing >2 times in ancestry raises CircularSpawnError."""
    from praxis.kernel.runtime.spawner.circular_guard import CircularSpawnError, CircularSpawnGuard

    guard = CircularSpawnGuard(max_recursion_per_agent=2)
    # agent-a appears at positions 0, 2, and would appear again at 4
    with pytest.raises(CircularSpawnError):
        guard.check_spawn(
            agent_name="agent-a",
            spawn_depth=4,
            ancestor_chain=["agent-a", "agent-b", "agent-a", "agent-b"],
        )
