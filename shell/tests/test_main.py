"""FastAPI app wiring tests — verify create_app + endpoint registration."""

from __future__ import annotations

import json

import pytest
from httpx import ASGITransport, AsyncClient

from api.billing import BillingService
from api.events import SessionEventBus
from api.main import create_app
from api.middleware.auth import AuthMiddleware
from api.routes.public import PublicDashboardService
from api.routes.sessions import SessionService
from api.routes.webhooks import WebhookHandler
from tests.conftest import (
    FakeClerkProvider,
    FakeMemoryFacade,
    FakeStripeClient,
    FakeStudioSession,
)


@pytest.fixture
def app_components():
    clerk = FakeClerkProvider()
    stripe = FakeStripeClient()
    studio = FakeStudioSession()
    memory = FakeMemoryFacade()
    bus = SessionEventBus()
    from api.adapters.memory_adapter import ShellMemoryAdapter

    auth = AuthMiddleware(provider=clerk)
    billing = BillingService(stripe=stripe)
    session_svc = SessionService(
        auth=auth, billing=billing, event_bus=bus,
        studio=studio, memory_adapter=ShellMemoryAdapter(memory=memory),
    )
    dashboard = PublicDashboardService(min_sessions=10)
    webhooks = WebhookHandler(billing=billing, webhook_secret="whsec_test")

    return {
        "clerk": clerk, "stripe": stripe, "auth": auth,
        "billing": billing, "session_svc": session_svc,
        "dashboard": dashboard, "webhooks": webhooks, "bus": bus,
    }


@pytest.fixture
def app(app_components):
    return create_app(
        auth_middleware=app_components["auth"],
        billing_service=app_components["billing"],
        session_service=app_components["session_svc"],
        dashboard_service=app_components["dashboard"],
        webhook_handler=app_components["webhooks"],
        event_bus=app_components["bus"],
    )


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestAppRoutes:
    """Verify all 8 endpoints are registered and respond correctly."""

    async def test_public_stats_no_auth(self, client: AsyncClient):
        """GET /api/public/stats — no auth required."""
        r = await client.get("/api/public/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_sessions" in data
        assert data["insufficient_data"] is True

    async def test_create_session_no_auth_401(self, client: AsyncClient):
        """POST /api/sessions without auth → 401."""
        r = await client.post("/api/sessions", json={
            "question": "What is the strategic impact of this decision on our portfolio allocation?",
        })
        assert r.status_code == 401

    async def test_create_session_with_auth(self, client: AsyncClient, app_components):
        """POST /api/sessions with valid auth → 200."""
        token = app_components["clerk"].issue_jwt(workspace_id="ws-1", role="owner")
        r = await client.post(
            "/api/sessions",
            json={"question": "What is the strategic impact of this decision on our portfolio allocation?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["workspace_id"] == "ws-1"

    async def test_get_session_no_auth_401(self, client: AsyncClient):
        """GET /api/sessions/:id without auth → 401."""
        r = await client.get("/api/sessions/test-id")
        assert r.status_code == 401

    async def test_get_session_with_auth(self, client: AsyncClient, app_components):
        """GET /api/sessions/:id with auth → 200."""
        token = app_components["clerk"].issue_jwt(workspace_id="ws-1", role="owner")
        r = await client.get(
            "/api/sessions/test-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    async def test_list_sessions_no_auth_401(self, client: AsyncClient):
        """GET /api/sessions without auth → 401."""
        r = await client.get("/api/sessions")
        assert r.status_code == 401

    async def test_list_sessions_with_auth(self, client: AsyncClient, app_components):
        """GET /api/sessions with auth → 200."""
        token = app_components["clerk"].issue_jwt(workspace_id="ws-1", role="owner")
        r = await client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    async def test_stream_session_no_auth_401(self, client: AsyncClient):
        """GET /api/sessions/:id/stream without auth → 401."""
        r = await client.get("/api/sessions/test-id/stream")
        assert r.status_code == 401

    async def test_usage_no_auth_401(self, client: AsyncClient):
        """GET /api/usage without auth → 401."""
        r = await client.get("/api/usage")
        assert r.status_code == 401

    async def test_usage_with_auth(self, client: AsyncClient, app_components):
        """GET /api/usage with auth → 200."""
        token = app_components["clerk"].issue_jwt(workspace_id="ws-1", role="owner")
        r = await client.get(
            "/api/usage",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    async def test_stripe_webhook_invalid_sig(self, client: AsyncClient):
        """POST /api/webhooks/stripe with bad sig → 403."""
        r = await client.post(
            "/api/webhooks/stripe",
            content=json.dumps({"type": "test"}).encode(),
            headers={"stripe-signature": "bad-sig"},
        )
        assert r.status_code == 403

    async def test_stripe_webhook_valid_sig(self, client: AsyncClient):
        """POST /api/webhooks/stripe with valid sig → 200."""
        payload = json.dumps({"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_1"}}})
        r = await client.post(
            "/api/webhooks/stripe",
            content=payload.encode(),
            headers={"stripe-signature": "valid-sig"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "processed"

    async def test_delivery_webhook(self, client: AsyncClient):
        """POST /api/webhooks/delivery → not_implemented (Stage 8)."""
        r = await client.post("/api/webhooks/delivery")
        assert r.status_code == 200
        assert r.json()["status"] == "not_implemented"


class TestWebhookHandler:
    """WebhookHandler unit tests."""

    def test_ignored_event_type(self, app_components):
        """Unknown event type → ignored."""
        handler = app_components["webhooks"]
        payload = json.dumps({"type": "charge.refunded"}).encode()
        result = handler.handle(payload, "valid-sig")
        assert result["status"] == "ignored"

    def test_payment_failed_event(self, app_components):
        """payment_intent.payment_failed → processed."""
        handler = app_components["webhooks"]
        payload = json.dumps({
            "type": "payment_intent.payment_failed",
            "data": {"object": {"id": "pi_fail"}},
        }).encode()
        result = handler.handle(payload, "valid-sig")
        assert result["status"] == "processed"
        assert result["payment_intent_id"] == "pi_fail"
