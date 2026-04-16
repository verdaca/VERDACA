"""Event streaming over the transactional outbox."""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from sqlalchemy import select

from .models import CostEvent, Filter
from .storage import CostRepository
from .storage.schema import EventRow


class EventStream:
    def __init__(self, repo: CostRepository) -> None:
        self._repo = repo

    async def stream(
        self,
        filter_: Filter,
        from_event_id: str | None,
        poll_interval_ms: int,
    ) -> AsyncIterator[CostEvent]:
        cursor = from_event_id or ""
        while True:
            async with self._repo.session() as session:
                stmt = select(EventRow).where(EventRow.event_id > cursor).order_by(
                    EventRow.event_id
                )
                result = await session.execute(stmt)
                rows = result.scalars().all()
                for row in rows:
                    event = CostEvent.model_validate(row.payload)
                    if self._matches(event, filter_):
                        yield event
                    cursor = row.event_id
                    row.delivered_at = row.delivered_at or row.emitted_at
                await session.commit()
            if not rows:
                await asyncio.sleep(poll_interval_ms / 1000)

    @staticmethod
    def _matches(event: CostEvent, filter_: Filter) -> bool:
        if event.record is None:
            return True
        rec = event.record
        if filter_.provider is not None and rec.provider != filter_.provider:
            return False
        if filter_.model_id is not None and rec.model_id != filter_.model_id:
            return False
        if filter_.session_id is not None and rec.session_id != filter_.session_id:
            return False
        if filter_.workflow_id is not None and rec.workflow_id != filter_.workflow_id:
            return False
        if filter_.agent is not None and rec.agent != filter_.agent:
            return False
        if filter_.stop_reason is not None and rec.stop_reason != filter_.stop_reason:
            return False
        if filter_.time_range is not None:
            if not (
                filter_.time_range.start <= rec.started_at < filter_.time_range.end
            ):
                return False
        if filter_.tag_match:
            for k, v in filter_.tag_match.items():
                if rec.tags.get(k) != v:
                    return False
        return True
