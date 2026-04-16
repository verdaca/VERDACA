"""Rollup queries over CostRecord. Thin wrapper over repository aggregation."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from .models import AggregationScope, CostSummary, Filter
from .storage import CostRepository


class Aggregator:
    def __init__(self, repo: CostRepository, clock: Callable[[], datetime]) -> None:
        self._repo = repo
        self._clock = clock

    async def summary(
        self,
        filter_: Filter,
        scope: AggregationScope,
        scope_id: str,
    ) -> CostSummary:
        return await self._repo.summary(filter_, scope, scope_id, self._clock())
