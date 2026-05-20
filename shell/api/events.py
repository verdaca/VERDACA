"""SSE event bus for session progress streaming — arch §7.4.

In-memory pub/sub for session lifecycle events. Production would
use Redis pub/sub or similar for multi-process deployments.

Binding anchors:
  - shell/architecture.md §7.4 SSE Progress Streaming
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator


@dataclass(frozen=True)
class SessionEvent:
    """One SSE event for a session."""

    type: str  # cycle_start, cost_update, cycle_end, complete, error
    session_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def json(self) -> str:
        return json.dumps(asdict(self))


class SessionEventBus:
    """In-memory pub/sub for session SSE events."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[SessionEvent | None]]] = {}

    def publish(self, event: SessionEvent) -> None:
        """Publish an event to all subscribers for this session."""
        queues = self._subscribers.get(event.session_id, [])
        for queue in queues:
            queue.put_nowait(event)

    async def subscribe(self, session_id: str) -> AsyncIterator[SessionEvent]:
        """Subscribe to events for a session. Yields events until None sentinel."""
        queue: asyncio.Queue[SessionEvent | None] = asyncio.Queue()
        if session_id not in self._subscribers:
            self._subscribers[session_id] = []
        self._subscribers[session_id].append(queue)

        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
        finally:
            self._subscribers[session_id].remove(queue)
            if not self._subscribers[session_id]:
                del self._subscribers[session_id]

    def complete(self, session_id: str) -> None:
        """Send None sentinel to all subscribers, signaling end of stream."""
        queues = self._subscribers.get(session_id, [])
        for queue in queues:
            queue.put_nowait(None)

    @property
    def subscriber_count(self) -> int:
        return sum(len(q) for q in self._subscribers.values())
