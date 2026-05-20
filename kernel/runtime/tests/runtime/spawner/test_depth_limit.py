"""tests/runtime/spawner/test_depth_limit.py — RED commit.

Spawn depth limit enforcement. Architecture §9.8, S4.R-07.
Default max_spawn_depth = 8; depth 9 raises MaxSpawnDepthExceededError.
"""

from __future__ import annotations

import pytest


def test_circular_guard_importable() -> None:
    from praxis.kernel.runtime.spawner.circular_guard import (  # noqa: F401
        CircularSpawnError,
        CircularSpawnGuard,
        MaxSpawnDepthExceededError,
    )


def test_depth_limit_default_is_8() -> None:
    from praxis.kernel.runtime.spawner.circular_guard import CircularSpawnGuard

    guard = CircularSpawnGuard()
    assert guard.max_depth == 8


def test_depth_8_succeeds() -> None:
    from uuid import uuid4

    from praxis.kernel.runtime.spawner.circular_guard import CircularSpawnGuard

    guard = CircularSpawnGuard(max_depth=8)
    spawn_ids = [uuid4() for _ in range(9)]

    # Build an 8-deep chain (depth 0..7, depth 8 would be the 9th = index 8)
    # check_spawn at depth 8 (= 9 nodes in chain including root) should succeed
    for depth in range(8):
        guard.check_spawn(
            agent_name=f"agent-{depth}",
            spawn_depth=depth,
            ancestor_chain=[f"agent-{i}" for i in range(depth)],
        )


def test_depth_9_raises() -> None:
    from praxis.kernel.runtime.spawner.circular_guard import (
        CircularSpawnGuard,
        MaxSpawnDepthExceededError,
    )

    guard = CircularSpawnGuard(max_depth=8)
    with pytest.raises(MaxSpawnDepthExceededError):
        guard.check_spawn(
            agent_name="agent-deep",
            spawn_depth=9,
            ancestor_chain=[f"agent-{i}" for i in range(9)],
        )


def test_configurable_max_depth() -> None:
    from praxis.kernel.runtime.spawner.circular_guard import (
        CircularSpawnGuard,
        MaxSpawnDepthExceededError,
    )

    guard = CircularSpawnGuard(max_depth=3)
    with pytest.raises(MaxSpawnDepthExceededError):
        guard.check_spawn(
            agent_name="agent-deep",
            spawn_depth=4,
            ancestor_chain=["a", "b", "c", "d"],
        )
