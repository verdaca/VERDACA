"""Session lifecycle tests — test-strategy §4.6–§4.7.

SHELL-T-SESS-UNIT-06: rendering_mode=position_to_hold → Studio invoked with POSITION_TO_HOLD
SHELL-T-SESS-UNIT-07: rendering_mode=decision_framework → Studio invoked with DECISION_FRAMEWORK
SHELL-T-SESS-UNIT-08: rendering_mode=firm_voice → Studio invoked with FIRM_VOICE
SHELL-T-SESS-INT-01: POST /api/sessions → session created, background task enqueued
SHELL-T-SESS-INT-02: GET /api/sessions/:id → completed session returns results
SHELL-T-SESS-INT-03: GET /api/sessions → paginated list for workspace
"""

from __future__ import annotations

import pytest

from api.billing import BillingService
from api.events import SessionEventBus
from api.middleware.auth import AuthContext, AuthMiddleware, WorkspaceRole
from api.models import CreateSessionRequest, RenderingMode, SessionDepth
from api.routes.sessions import SessionService
from tests.conftest import (
    FakeClerkProvider,
    FakeMemoryFacade,
    FakeStripeClient,
    FakeStudioSession,
)


@pytest.fixture
def event_bus() -> SessionEventBus:
    return SessionEventBus()


@pytest.fixture
def session_service(
    fake_clerk: FakeClerkProvider,
    fake_stripe: FakeStripeClient,
    fake_studio: FakeStudioSession,
    fake_memory: FakeMemoryFacade,
    event_bus: SessionEventBus,
) -> SessionService:
    from api.adapters.memory_adapter import ShellMemoryAdapter

    return SessionService(
        auth=AuthMiddleware(provider=fake_clerk),
        billing=BillingService(stripe=fake_stripe),
        event_bus=event_bus,
        studio=fake_studio,
        memory_adapter=ShellMemoryAdapter(memory=fake_memory),
    )


def _make_auth(workspace_id: str = "ws-test-1", role: str = "owner") -> AuthContext:
    return AuthContext(
        workspace_id=workspace_id,
        user_id="user-1",
        role=WorkspaceRole(role),
    )


class TestSessionCreation:
    """Session creation and lifecycle tests."""

    @pytest.mark.shell_sess
    @pytest.mark.integration
    async def test_sess_int_01_create_session(self, session_service: SessionService):
        """SHELL-T-SESS-INT-01: Create session produces correct structure."""
        req = CreateSessionRequest(
            question="What is the strategic impact of this decision on our portfolio allocation?",
            depth=SessionDepth.DEEP,
        )
        auth = _make_auth()

        result = await session_service.create_session(
            req=req,
            auth=auth,
            workspace_trial_used=False,
            workspace_stripe_customer_id=None,
        )

        assert result["id"]  # ULID generated
        assert result["workspace_id"] == "ws-test-1"
        assert result["status"] == "pending"
        assert result["depth"] == "deep"
        assert result["rendering_mode"] == "position_to_hold"
        assert result["payment_type"] == "trial"

    @pytest.mark.shell_sess
    @pytest.mark.integration
    async def test_sess_int_02_completed_session_has_results(
        self, session_service: SessionService
    ):
        """SHELL-T-SESS-INT-02: Completed session returns result data."""
        req = CreateSessionRequest(
            question="What is the strategic impact of this decision on our portfolio allocation?",
        )
        auth = _make_auth()

        created = await session_service.create_session(
            req=req,
            auth=auth,
            workspace_trial_used=False,
            workspace_stripe_customer_id=None,
        )

        # Run the session background
        result = await session_service.run_session_background(created)

        assert result["status"] == "completed"
        assert result["completed_at"] is not None
        assert result["result_markdown"] is not None
        assert result["result_html"] is not None

    @pytest.mark.shell_sess
    @pytest.mark.integration
    async def test_sess_int_03_list_paginated(self, session_service: SessionService):
        """SHELL-T-SESS-INT-03: List sessions returns workspace-scoped paginated results."""
        auth = _make_auth(workspace_id="ws-A")

        # Create sessions for workspace A and B
        sessions_all = [
            {"workspace_id": "ws-A", "id": f"s{i}", "status": "completed"}
            for i in range(5)
        ] + [
            {"workspace_id": "ws-B", "id": "s99", "status": "completed"}
        ]

        result = await session_service.list_sessions(
            auth=auth, all_sessions=sessions_all, page=1, page_size=3
        )

        assert len(result) == 3
        assert all(s["workspace_id"] == "ws-A" for s in result)

    @pytest.mark.shell_sess
    async def test_get_session_correct_workspace(self, session_service: SessionService):
        """get_session returns data when workspace matches."""
        auth = _make_auth(workspace_id="ws-A")
        data = {"workspace_id": "ws-A", "id": "s1", "status": "completed"}

        result = await session_service.get_session("s1", auth, data)
        assert result is not None

    @pytest.mark.shell_sess
    async def test_get_session_wrong_workspace_returns_none(
        self, session_service: SessionService
    ):
        """get_session returns None when workspace doesn't match."""
        auth = _make_auth(workspace_id="ws-A")
        data = {"workspace_id": "ws-B", "id": "s1", "status": "completed"}

        result = await session_service.get_session("s1", auth, data)
        assert result is None


class TestRenderingModeRouting:
    """DL-15 rendering mode routing tests — test-strategy §4.7."""

    @pytest.mark.shell_sess
    async def test_sess_unit_06_position_to_hold(
        self, session_service: SessionService, fake_studio: FakeStudioSession
    ):
        """SHELL-T-SESS-UNIT-06: position_to_hold → Studio POSITION_TO_HOLD."""
        req = CreateSessionRequest(
            question="What is the strategic impact of this decision on our portfolio allocation?",
            rendering_mode=RenderingMode.POSITION_TO_HOLD,
        )
        auth = _make_auth()
        created = await session_service.create_session(
            req=req, auth=auth,
            workspace_trial_used=False, workspace_stripe_customer_id=None,
        )
        await session_service.run_session_background(created)

        assert len(fake_studio.invocations) == 1
        assert fake_studio.invocations[0]["rendering_mode"] == "position_to_hold"

    @pytest.mark.shell_sess
    async def test_sess_unit_07_decision_framework(
        self, session_service: SessionService, fake_studio: FakeStudioSession
    ):
        """SHELL-T-SESS-UNIT-07: decision_framework → Studio DECISION_FRAMEWORK."""
        req = CreateSessionRequest(
            question="What is the strategic impact of this decision on our portfolio allocation?",
            rendering_mode=RenderingMode.DECISION_FRAMEWORK,
        )
        auth = _make_auth()
        created = await session_service.create_session(
            req=req, auth=auth,
            workspace_trial_used=False, workspace_stripe_customer_id=None,
        )
        await session_service.run_session_background(created)

        assert fake_studio.invocations[0]["rendering_mode"] == "decision_framework"

    @pytest.mark.shell_sess
    async def test_sess_unit_08_firm_voice(
        self, session_service: SessionService, fake_studio: FakeStudioSession
    ):
        """SHELL-T-SESS-UNIT-08: firm_voice → Studio FIRM_VOICE."""
        req = CreateSessionRequest(
            question="What is the strategic impact of this decision on our portfolio allocation?",
            rendering_mode=RenderingMode.FIRM_VOICE,
        )
        auth = _make_auth()
        created = await session_service.create_session(
            req=req, auth=auth,
            workspace_trial_used=False, workspace_stripe_customer_id=None,
        )
        await session_service.run_session_background(created)

        assert fake_studio.invocations[0]["rendering_mode"] == "firm_voice"

    @pytest.mark.shell_sess
    async def test_quick_mode_uses_quick_template(
        self, session_service: SessionService, fake_studio: FakeStudioSession
    ):
        """Quick depth → strategic_session_quick.yaml template."""
        req = CreateSessionRequest(
            question="What is the strategic impact of this decision on our portfolio allocation?",
            depth=SessionDepth.QUICK,
        )
        auth = _make_auth()
        created = await session_service.create_session(
            req=req, auth=auth,
            workspace_trial_used=False, workspace_stripe_customer_id=None,
        )
        await session_service.run_session_background(created)

        assert fake_studio.invocations[0]["template_path"] == "strategic_session_quick.yaml"

    @pytest.mark.shell_sess
    async def test_deep_mode_uses_deep_template(
        self, session_service: SessionService, fake_studio: FakeStudioSession
    ):
        """Deep depth → strategic_session.yaml template."""
        req = CreateSessionRequest(
            question="What is the strategic impact of this decision on our portfolio allocation?",
            depth=SessionDepth.DEEP,
        )
        auth = _make_auth()
        created = await session_service.create_session(
            req=req, auth=auth,
            workspace_trial_used=False, workspace_stripe_customer_id=None,
        )
        await session_service.run_session_background(created)

        assert fake_studio.invocations[0]["template_path"] == "strategic_session.yaml"
