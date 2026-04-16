"""Asymmetry router coverage-floor tests.

Not part of the v0.3 §5 MAC-T catalog — these tests exist solely to
satisfy the ≥95% coverage floor on ``asymmetry.py`` by exercising the
reviewer_count validation branch and the ``aggregate_critiques``
helper paths that the MAC-T tests don't reach.

Per Stage 5.3 preload Q3 disposition (2026-04-14): no MAC-T IDs, no
``no_waiver`` markers, not in the 16-entry allow-list.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.asymmetry import AsymmetryRouter, ReviewerCritique
from praxis.kernel.mac.integrations.runtime import (
    FakeAgentSpawner,
    MacRuntimeAdapter,
)


def _noop_guard() -> None:
    return None


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_spawn_reviewer_pool_rejects_invalid_counts() -> None:
    """``spawn_reviewer_pool`` raises ValueError for count < 1 or > 3 per arch §4.3."""
    adapter = MacRuntimeAdapter(
        spawner=FakeAgentSpawner(), shape_guard=_noop_guard
    )
    router = AsymmetryRouter(runtime_adapter=adapter)

    import asyncio

    with pytest.raises(ValueError, match="reviewer_count must be in"):
        asyncio.run(router.spawn_reviewer_pool(count=0))

    with pytest.raises(ValueError, match="reviewer_count must be in"):
        asyncio.run(router.spawn_reviewer_pool(count=4))


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_aggregate_critiques_empty_list_returns_empty_shape() -> None:
    """``aggregate_critiques([])`` returns a sentinel shape with
    ``reviewer_count == 0`` and empty lists.
    """
    result = AsymmetryRouter.aggregate_critiques([])
    assert result["reviewer_count"] == 0
    assert result["critiques"] == []
    assert result["all_raised_concerns"] == ()
    assert result["manufactured_dissent_detected"] is False


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_aggregate_critiques_collects_concerns_across_reviewers() -> None:
    """``aggregate_critiques`` concatenates ``raised_concerns`` from all
    critiques in input order.
    """
    critique_a = ReviewerCritique(
        independent_steelman="A's steelman text",
        gap_assessment="A's gap assessment",
        raised_concerns=("concern_1", "concern_2"),
        reviewer_id="reviewer-0",
    )
    critique_b = ReviewerCritique(
        independent_steelman="B's steelman text",
        gap_assessment="B's gap assessment",
        raised_concerns=("concern_3",),
        reviewer_id="reviewer-1",
    )

    result = AsymmetryRouter.aggregate_critiques([critique_a, critique_b])
    assert result["reviewer_count"] == 2
    assert len(result["critiques"]) == 2
    assert result["all_raised_concerns"] == ("concern_1", "concern_2", "concern_3")
    # Critique dicts preserve input order.
    assert result["critiques"][0]["reviewer_id"] == "reviewer-0"
    assert result["critiques"][1]["reviewer_id"] == "reviewer-1"
