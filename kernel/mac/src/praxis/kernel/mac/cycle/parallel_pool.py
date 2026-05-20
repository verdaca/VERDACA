"""Cycle 2 parallel reviewer pool — arch §5.4 + Tension #2 resolution.

Two classes share a protocol-compatible API:

  :class:`ParallelReviewerPool` — production path. Uses :func:`asyncio.gather`
  literally. ``MAC-T-CYCLE-PARALLEL-03`` verifies via
  ``inspect.getsource`` grep that ``asyncio.gather`` appears in the source.

  :class:`DeterministicReplayPool` — test fixture. Executes submissions in
  strict ``reviewer_index`` order (NOT wall-clock submission order),
  collects results in a deterministic tuple, advances a :class:`FrozenClock`
  between submissions. Used by ``MAC-T-CYCLE-PARALLEL-01/02``.

Both consume a list of awaitables and return an ordered tuple of results.
The contract is "sort by reviewer_index on output" — production and test
pools MUST agree on the final tuple key, differing only in whether the
underlying execution is concurrent (``gather``) or sequential (replay).

Binding anchors:
  - mac/architecture.md §5.4 Cycle 2 Parallelism
  - mac/test-strategy.md v0.3 §4.5 Deterministic Replay Pattern
  - runtime/test-strategy.md §6.4 Deterministic Async Replay (inherited pattern)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol, runtime_checkable


@runtime_checkable
class _ClockProtocol(Protocol):
    """Duck-typed clock used by :class:`DeterministicReplayPool`.

    :class:`praxis.kernel.mac.testing.fakes.frozen_clock.FrozenClock`
    satisfies this structurally. The Protocol exists to break a
    circular import chain via the gates subpackage.
    """

    def advance(self, seconds: int) -> None: ...


@dataclass(frozen=True)
class ReviewerSubmission:
    """Pair of ``(reviewer_index, coroutine_factory)``.

    The factory is a zero-arg callable that returns an awaitable. Using a
    factory (rather than a raw awaitable) lets the replay pool call it on
    demand in a deterministic order without materializing all coroutines
    up front.
    """

    reviewer_index: int
    factory: Callable[[], Awaitable[Any]]


class ParallelReviewerPool:
    """Production Cycle 2 parallelism via :func:`asyncio.gather`.

    ``submit_all`` dispatches all reviewer factories concurrently through
    ``asyncio.gather`` (the single reference to gather in the MAC
    codebase — ``MAC-T-CYCLE-PARALLEL-03`` grep-locks this), then sorts
    the results by ``reviewer_index`` so callers see a deterministic
    tuple regardless of which reviewer's coroutine completed first.
    """

    async def submit_all(
        self, submissions: list[ReviewerSubmission]
    ) -> tuple[tuple[int, Any], ...]:
        # Production code path uses real asyncio.gather.
        # MAC-T-CYCLE-PARALLEL-03 verifies via inspect.getsource.
        coroutines = [sub.factory() for sub in submissions]
        gathered = await asyncio.gather(*coroutines)
        paired = list(zip([s.reviewer_index for s in submissions], gathered))
        paired.sort(key=lambda p: p[0])
        return tuple(paired)


class DeterministicReplayPool:
    """Test-only replay pool per mac/test-strategy.md v0.3 §4.5.1.

    Executes submissions in strict ``reviewer_index`` order (NOT wall-clock
    submission order). Advances the injected :class:`FrozenClock` by 1
    simulated second between submissions to synchronize virtual time.
    Result tuple is sorted by ``reviewer_index`` — identical shape to
    :meth:`ParallelReviewerPool.submit_all` so tests can swap the pools
    without reshaping assertions.
    """

    def __init__(self, clock: _ClockProtocol) -> None:
        self._clock = clock

    async def submit_all(
        self, submissions: list[ReviewerSubmission]
    ) -> tuple[tuple[int, Any], ...]:
        # Deterministic replay: sort by reviewer_index BEFORE executing.
        ordered = sorted(submissions, key=lambda s: s.reviewer_index)
        results: list[tuple[int, Any]] = []
        for sub in ordered:
            result = await sub.factory()
            results.append((sub.reviewer_index, result))
            self._clock.advance(1)
        return tuple(results)


__all__ = (
    "DeterministicReplayPool",
    "ParallelReviewerPool",
    "ReviewerSubmission",
)
