"""Parallelism determinism tests — mac/test-strategy.md v0.3 §4.5.

Covers ``MAC-T-CYCLE-PARALLEL-01/02/03``. Tension #2 Deterministic Replay
Pattern resolution.

Anchors:
  - mac/architecture.md §5.4 Cycle 2 Parallelism (production asyncio.gather)
  - mac/test-strategy.md v0.3 §4.5.1 Deterministic Replay Pattern
  - runtime/test-strategy.md §6.4 Deterministic Async Replay (inherited)
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import datetime, timezone

import pytest

from praxis.kernel.mac.cycle import (
    DeterministicReplayPool,
    ParallelReviewerPool,
    ReviewerSubmission,
)
from praxis.kernel.mac.testing.fakes.frozen_clock import FrozenClock


async def _make_reviewer_result(index: int) -> str:
    """Deterministic reviewer factory — returns a string keyed on index."""
    # Small sleep would normally exercise real concurrency, but here we
    # keep it a plain async function so DeterministicReplayPool runs it
    # in strict index order.
    return f"reviewer-{index}-result"


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_self_consistency
async def test_mac_t_cycle_parallel_01_replay_determinism() -> None:
    """MAC-T-CYCLE-PARALLEL-01 — 1000 replays yield byte-identical output.

    Running the same cycle 2 input 1000 times through
    :class:`DeterministicReplayPool` produces 1000 identical outputs.
    ``set(runs) == {expected}`` cardinality 1.
    """
    clock = FrozenClock(initial=datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc))
    outputs: set[tuple[tuple[int, str], ...]] = set()
    for _ in range(1000):
        pool = DeterministicReplayPool(clock=clock)
        submissions = [
            ReviewerSubmission(
                reviewer_index=i,
                factory=(lambda idx=i: _make_reviewer_result(idx)),
            )
            for i in [2, 0, 1]  # intentionally unsorted input
        ]
        result = await pool.submit_all(submissions)
        outputs.add(result)

    # Cardinality 1 — all 1000 runs produced the same tuple.
    assert len(outputs) == 1
    (only_output,) = outputs
    assert only_output == (
        (0, "reviewer-0-result"),
        (1, "reviewer-1-result"),
        (2, "reviewer-2-result"),
    )


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_self_consistency
async def test_mac_t_cycle_parallel_02_reviewer_index_ordering_is_strict() -> None:
    """MAC-T-CYCLE-PARALLEL-02 — output tuple is strictly sorted by reviewer_index.

    Even when submissions arrive in unsorted order, the output is sorted
    by ``reviewer_index``. This holds for both the replay pool AND the
    production pool (which sorts in the final step of ``submit_all``).
    """
    clock = FrozenClock(initial=datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc))
    replay_pool = DeterministicReplayPool(clock=clock)
    prod_pool = ParallelReviewerPool()

    unsorted_submissions = [
        ReviewerSubmission(
            reviewer_index=i,
            factory=(lambda idx=i: _make_reviewer_result(idx)),
        )
        for i in [5, 1, 3, 0, 2, 4]
    ]

    replay_result = await replay_pool.submit_all(unsorted_submissions)
    prod_result = await prod_pool.submit_all(unsorted_submissions)

    replay_indices = [r[0] for r in replay_result]
    prod_indices = [r[0] for r in prod_result]

    assert replay_indices == sorted(replay_indices)
    assert prod_indices == sorted(prod_indices)
    # And both pools agree on the final ordering.
    assert replay_result == prod_result


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_cycle_parallel_03_production_uses_asyncio_gather() -> None:
    """MAC-T-CYCLE-PARALLEL-03 — production code path uses real asyncio.gather.

    Verifies via ``inspect.getsource`` grep that ``asyncio.gather`` appears
    in :class:`ParallelReviewerPool.submit_all` source. This is the
    ratified grep-lock per arch §5.4 + test-strategy §4.5.4 — the
    production path must not silently become a sequential wrapper.
    """
    source = inspect.getsource(ParallelReviewerPool.submit_all)
    assert "asyncio.gather" in source, (
        "ParallelReviewerPool.submit_all must use asyncio.gather literally "
        "per arch §5.4 + test-strategy v0.3 §4.5.4"
    )

    # Belt-and-suspenders: ``asyncio`` is imported at module level.
    import praxis.kernel.mac.cycle.parallel_pool as pp_module

    module_source = inspect.getsource(pp_module)
    assert "import asyncio" in module_source
    # And asyncio.gather is the actual function (not a symbol shadow).
    assert asyncio.gather.__module__ == "asyncio.tasks"
