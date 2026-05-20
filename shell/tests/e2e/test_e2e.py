"""E2E tests (Playwright stubs) — test-strategy §4.10.

SHELL-T-E2E-01: Golden path (signup → free trial → result)
SHELL-T-E2E-02: Paid session (trial consumed → Stripe → result)
SHELL-T-E2E-03: Mode routing (decision_framework → correct output)
SHELL-T-E2E-04: Public dashboard (metrics visible, no PII)
SHELL-T-E2E-05: Error handling (session fails → error, no charge)

These are Playwright E2E tests that require the full stack running.
They are marked nightly_only and are implemented as API-level integration
tests here, with full Playwright browser tests at Stage 7 launch.
"""

from __future__ import annotations

import pytest

from api.billing import BillingService
from api.events import SessionEventBus
from api.middleware.auth import AuthContext, AuthMiddleware, WorkspaceRole
from api.models import CreateSessionRequest, RenderingMode, SessionDepth
from api.routes.public import PublicDashboardService
from api.routes.sessions import SessionService
from tests.conftest import (
    FakeClerkProvider,
    FakeMemoryFacade,
    FakeSessionResult,
    FakeStripeClient,
    FakeStudioSession,
)


@pytest.fixture
def full_service_stack():
    """Wire up the full service stack for E2E-like tests."""
    clerk = FakeClerkProvider()
    stripe = FakeStripeClient()
    studio = FakeStudioSession()
    memory = FakeMemoryFacade()
    bus = SessionEventBus()
    from api.adapters.memory_adapter import ShellMemoryAdapter

    session_svc = SessionService(
        auth=AuthMiddleware(provider=clerk),
        billing=BillingService(stripe=stripe),
        event_bus=bus,
        studio=studio,
        memory_adapter=ShellMemoryAdapter(memory=memory),
    )
    dashboard_svc = PublicDashboardService(min_sessions=10)

    return {
        "clerk": clerk,
        "stripe": stripe,
        "studio": studio,
        "memory": memory,
        "bus": bus,
        "session_svc": session_svc,
        "dashboard_svc": dashboard_svc,
    }


def _auth(ws: str = "ws-1") -> AuthContext:
    return AuthContext(workspace_id=ws, user_id="u-1", role=WorkspaceRole.OWNER)


class TestE2EFlows:
    """End-to-end flow tests (API level — Playwright E2E in Stage 7 launch)."""

    @pytest.mark.shell_e2e
    @pytest.mark.nightly_only
    async def test_e2e_01_golden_path(self, full_service_stack):
        """SHELL-T-E2E-01: Signup → free trial → session → result."""
        svc = full_service_stack["session_svc"]
        auth = _auth()

        # Create session (free trial)
        req = CreateSessionRequest(
            question="What is the strategic impact of expanding into European markets for our SaaS product?",
            depth=SessionDepth.QUICK,
        )
        session = await svc.create_session(
            req=req, auth=auth,
            workspace_trial_used=False,
            workspace_stripe_customer_id=None,
        )
        assert session["payment_type"] == "trial"
        assert session["status"] == "pending"

        # Run session
        result = await svc.run_session_background(session)
        assert result["status"] == "completed"
        assert result["result_markdown"] is not None
        assert result["result_html"] is not None

    @pytest.mark.shell_e2e
    @pytest.mark.nightly_only
    async def test_e2e_02_paid_session(self, full_service_stack):
        """SHELL-T-E2E-02: Trial consumed → Stripe → paid deep session → result."""
        svc = full_service_stack["session_svc"]
        auth = _auth()

        req = CreateSessionRequest(
            question="Our core value proposition is under pricing pressure from a competitor 40% lower. What position should we hold?",
            depth=SessionDepth.DEEP,
        )
        session = await svc.create_session(
            req=req, auth=auth,
            workspace_trial_used=True,
            workspace_stripe_customer_id="cus_paid",
        )
        assert session["payment_type"] == "paid"

        result = await svc.run_session_background(session)
        assert result["status"] == "completed"
        assert full_service_stack["stripe"].created_intents[0]["amount"] == 14900

    @pytest.mark.shell_e2e
    @pytest.mark.nightly_only
    async def test_e2e_03_mode_routing(self, full_service_stack):
        """SHELL-T-E2E-03: decision_framework mode → correct template in Studio."""
        svc = full_service_stack["session_svc"]
        studio = full_service_stack["studio"]
        auth = _auth()

        req = CreateSessionRequest(
            question="The board wants European expansion based on 2 inbound leads. What entity-specific risks exist?",
            rendering_mode=RenderingMode.DECISION_FRAMEWORK,
        )
        session = await svc.create_session(
            req=req, auth=auth,
            workspace_trial_used=False,
            workspace_stripe_customer_id=None,
        )
        await svc.run_session_background(session)

        assert studio.invocations[0]["rendering_mode"] == "decision_framework"

    @pytest.mark.shell_e2e
    @pytest.mark.nightly_only
    async def test_e2e_04_public_dashboard(self, full_service_stack):
        """SHELL-T-E2E-04: Dashboard → metrics visible, no PII."""
        from datetime import datetime, timezone

        dashboard = full_service_stack["dashboard_svc"]
        sessions = [
            {
                "workspace_id": f"ws-{i}",
                "question": f"Secret question {i}",
                "status": "completed",
                "cost_usd": 2.50,
                "duration_seconds": 120.0,
                "started_at": datetime.now(timezone.utc),
            }
            for i in range(15)
        ]
        stats = dashboard.compute_stats(sessions)

        assert stats.total_sessions == 15
        assert stats.insufficient_data is False
        # No PII
        stats_str = str(stats.model_dump())
        assert "Secret question" not in stats_str
        assert "ws-" not in stats_str

    @pytest.mark.shell_e2e
    @pytest.mark.nightly_only
    async def test_e2e_05_error_no_charge(self, full_service_stack):
        """SHELL-T-E2E-05: Session fails → error displayed, no charge."""
        svc = full_service_stack["session_svc"]
        # Replace studio with one that fails
        full_service_stack["studio"]._result = FakeSessionResult(status="failed")

        class FailingStudio:
            async def invoke(self, **kwargs):
                raise RuntimeError("MAC engine crashed")

        svc._studio = FailingStudio()
        auth = _auth()

        req = CreateSessionRequest(
            question="What is the strategic impact of this decision on our portfolio allocation?",
        )
        session = await svc.create_session(
            req=req, auth=auth,
            workspace_trial_used=False,
            workspace_stripe_customer_id=None,
        )
        result = await svc.run_session_background(session)

        assert result["status"] == "failed"
        # No Stripe charge for trial session
        assert len(full_service_stack["stripe"].created_intents) == 0
