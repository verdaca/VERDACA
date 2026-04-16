"""SSE streaming tests — test-strategy §4.9.

SHELL-T-SSE-INT-01: SSE receives cycle_start, cost_update, complete events
SHELL-T-SSE-INT-02: Client disconnect → cleanup, no resource leak
SHELL-T-SSE-INT-03: Unauthenticated SSE → 401
"""

from __future__ import annotations

import asyncio

import pytest

from api.events import SessionEvent, SessionEventBus
from api.middleware.auth import AuthError, AuthMiddleware
from tests.conftest import FakeClerkProvider


@pytest.fixture
def event_bus() -> SessionEventBus:
    return SessionEventBus()


class TestSSEStreaming:
    """SSE event bus tests."""

    @pytest.mark.shell_sse
    @pytest.mark.nightly_only
    async def test_sse_int_01_receives_events(self, event_bus: SessionEventBus):
        """SHELL-T-SSE-INT-01: subscriber receives cycle_start, cost_update, complete."""
        session_id = "sess-sse-1"
        received: list[SessionEvent] = []

        async def subscriber():
            async for event in event_bus.subscribe(session_id):
                received.append(event)

        task = asyncio.create_task(subscriber())

        # Give subscriber time to register
        await asyncio.sleep(0.01)

        # Publish events
        event_bus.publish(SessionEvent(type="cycle_start", session_id=session_id, data={"cycle": 1}))
        event_bus.publish(SessionEvent(type="cost_update", session_id=session_id, data={"cost": 1.50}))
        event_bus.publish(SessionEvent(type="complete", session_id=session_id, data={}))

        # Signal end
        event_bus.complete(session_id)
        await asyncio.wait_for(task, timeout=2.0)

        event_types = [e.type for e in received]
        assert "cycle_start" in event_types
        assert "cost_update" in event_types
        assert "complete" in event_types

    @pytest.mark.shell_sse
    @pytest.mark.nightly_only
    async def test_sse_int_02_client_disconnect_cleanup(self, event_bus: SessionEventBus):
        """SHELL-T-SSE-INT-02: Client disconnect → cleanup, no resource leak."""
        session_id = "sess-sse-2"

        async def short_subscriber():
            async for event in event_bus.subscribe(session_id):
                break  # disconnect after first event

        task = asyncio.create_task(short_subscriber())
        await asyncio.sleep(0.01)

        event_bus.publish(SessionEvent(type="cycle_start", session_id=session_id))
        await asyncio.wait_for(task, timeout=2.0)

        # After disconnect, subscriber count should be 0
        assert event_bus.subscriber_count == 0

    @pytest.mark.shell_sse
    @pytest.mark.critical
    def test_sse_int_03_unauthenticated_rejected(self, fake_clerk: FakeClerkProvider):
        """SHELL-T-SSE-INT-03: Unauthenticated SSE request → 401."""
        auth = AuthMiddleware(provider=fake_clerk)

        with pytest.raises(AuthError) as exc_info:
            auth.authenticate(None)  # no auth header
        assert exc_info.value.status_code == 401

    @pytest.mark.shell_sse
    async def test_event_json_serialization(self):
        """SessionEvent.json() produces valid JSON."""
        event = SessionEvent(
            type="cost_update",
            session_id="sess-1",
            data={"cost": 2.50},
        )
        import json
        parsed = json.loads(event.json())
        assert parsed["type"] == "cost_update"
        assert parsed["session_id"] == "sess-1"
        assert parsed["data"]["cost"] == 2.50

    @pytest.mark.shell_sse
    async def test_multiple_subscribers(self, event_bus: SessionEventBus):
        """Multiple subscribers each get all events."""
        session_id = "sess-multi"
        received_1: list[SessionEvent] = []
        received_2: list[SessionEvent] = []

        async def sub1():
            async for event in event_bus.subscribe(session_id):
                received_1.append(event)

        async def sub2():
            async for event in event_bus.subscribe(session_id):
                received_2.append(event)

        t1 = asyncio.create_task(sub1())
        t2 = asyncio.create_task(sub2())
        await asyncio.sleep(0.01)

        event_bus.publish(SessionEvent(type="test", session_id=session_id))
        event_bus.complete(session_id)

        await asyncio.wait_for(asyncio.gather(t1, t2), timeout=2.0)

        assert len(received_1) == 1
        assert len(received_2) == 1
