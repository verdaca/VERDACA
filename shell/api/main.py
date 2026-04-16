"""FastAPI application assembly — arch §12.1.

Wires all routes, middleware, and dependencies into a single app.

Binding anchors:
  - shell/architecture.md §3.1 Endpoint Specifications (8 endpoints)
  - shell/architecture.md §12.1 Infrastructure
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from api.billing import BillingError, BillingService
from api.config import Settings
from api.events import SessionEventBus
from api.middleware.auth import AuthError, AuthMiddleware
from api.models import (
    CreateSessionRequest,
    ErrorDetail,
    ErrorResponse,
    PublicStatsResponse,
    SessionResponse,
    UsageResponse,
)
from api.routes.public import PublicDashboardService
from api.routes.sessions import SessionService
from api.routes.webhooks import WebhookHandler


def create_app(
    *,
    auth_middleware: AuthMiddleware,
    billing_service: BillingService,
    session_service: SessionService,
    dashboard_service: PublicDashboardService,
    webhook_handler: WebhookHandler,
    event_bus: SessionEventBus,
    settings: Settings | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Praxis POV Delivery Harness",
        version="0.1.0",
        docs_url="/docs" if (settings and settings.debug) else None,
    )

    # Store services on app state for route handlers
    app.state.auth = auth_middleware
    app.state.billing = billing_service
    app.state.sessions = session_service
    app.state.dashboard = dashboard_service
    app.state.webhooks = webhook_handler
    app.state.event_bus = event_bus

    # --- Exception handlers ---

    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(code="AUTH_ERROR", message=exc.detail)
            ).model_dump(),
        )

    @app.exception_handler(BillingError)
    async def billing_error_handler(request: Request, exc: BillingError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(code=exc.code, message=exc.message)
            ).model_dump(),
        )

    # --- Routes ---

    @app.post("/api/sessions")
    async def create_session(req: CreateSessionRequest, request: Request):
        auth = request.app.state.auth.authenticate(
            request.headers.get("Authorization")
        )
        result = await request.app.state.sessions.create_session(
            req=req,
            auth=auth,
            workspace_trial_used=False,  # placeholder — DB lookup in production
            workspace_stripe_customer_id=None,
        )
        return result

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str, request: Request):
        auth = request.app.state.auth.authenticate(
            request.headers.get("Authorization")
        )
        # placeholder: would fetch from DB
        return {"session_id": session_id, "workspace_id": auth.workspace_id}

    @app.get("/api/sessions")
    async def list_sessions(request: Request, page: int = 1, page_size: int = 20):
        auth = request.app.state.auth.authenticate(
            request.headers.get("Authorization")
        )
        return {"workspace_id": auth.workspace_id, "page": page, "sessions": []}

    @app.get("/api/sessions/{session_id}/stream")
    async def stream_session(session_id: str, request: Request):
        request.app.state.auth.authenticate(
            request.headers.get("Authorization")
        )
        return {"session_id": session_id, "stream": "sse_endpoint"}

    @app.get("/api/usage")
    async def get_usage(request: Request):
        auth = request.app.state.auth.authenticate(
            request.headers.get("Authorization")
        )
        return UsageResponse(
            total_sessions=0,
            total_cost_usd=0,
            sessions_this_month=0,
        )

    @app.post("/api/webhooks/stripe")
    async def stripe_webhook(request: Request):
        payload = await request.body()
        sig = request.headers.get("stripe-signature", "")
        try:
            result = request.app.state.webhooks.handle(payload, sig)
            return result
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid signature")

    @app.get("/api/public/stats")
    async def public_stats(request: Request):
        # placeholder: would query DB for all sessions
        return request.app.state.dashboard.compute_stats([])

    @app.post("/api/webhooks/delivery")
    async def delivery_webhook(request: Request):
        # Stage 8 scope — architecture defined, not implemented
        return {"status": "not_implemented"}

    return app
