"""Session API routes — arch §3.1, §7.1–§7.4.

POST /api/sessions       — Start a new Studio session
GET  /api/sessions/:id   — Session status + results
GET  /api/sessions       — List user's sessions (paginated)
GET  /api/sessions/:id/stream — SSE stream of progress events
GET  /api/usage          — User's usage stats

Binding anchors:
  - shell/architecture.md §3.1 Endpoint Specifications
  - shell/architecture.md §7.1–§7.4 Session Lifecycle
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import ulid

from api.billing import BillingService, WorkspaceBillingState
from api.events import SessionEvent, SessionEventBus
from api.middleware.auth import AuthContext, AuthMiddleware, AuthError
from api.middleware.tenant import TenantScopedSession
from api.models import (
    CreateSessionRequest,
    ErrorDetail,
    ErrorResponse,
    RenderingMode,
    SessionResponse,
    SessionStatus,
    UsageResponse,
)


class SessionService:
    """Handles session lifecycle logic (arch §7.1–§7.3).

    Decoupled from FastAPI for testability — routes call this service.
    """

    def __init__(
        self,
        *,
        auth: AuthMiddleware,
        billing: BillingService,
        event_bus: SessionEventBus,
        studio: Any = None,
        cost_adapter: Any = None,
        memory_adapter: Any = None,
    ) -> None:
        self._auth = auth
        self._billing = billing
        self._event_bus = event_bus
        self._studio = studio
        self._cost_adapter = cost_adapter
        self._memory_adapter = memory_adapter

    def authenticate(self, authorization: str | None) -> AuthContext:
        return self._auth.authenticate(authorization)

    async def create_session(
        self,
        req: CreateSessionRequest,
        auth: AuthContext,
        workspace_trial_used: bool,
        workspace_stripe_customer_id: str | None,
    ) -> dict[str, Any]:
        """Create a session, handling billing authorization.

        Returns a dict with session fields. The caller is responsible
        for DB persistence and background task scheduling.
        """
        self._auth.authorize(auth, "create_session")

        billing_state = WorkspaceBillingState(
            trial_used=workspace_trial_used,
            stripe_customer_id=workspace_stripe_customer_id,
        )
        payment = await self._billing.authorize_session(
            workspace_billing=billing_state,
            depth=req.depth.value,
        )

        session_id = str(ulid.ULID())
        now = datetime.now(timezone.utc)

        return {
            "id": session_id,
            "workspace_id": auth.workspace_id,
            "question": req.question,
            "context": req.context,
            "depth": req.depth.value,
            "rendering_mode": req.rendering_mode.value,
            "status": SessionStatus.PENDING.value,
            "cost_usd": None,
            "stripe_payment_intent_id": payment.get("payment_intent_id"),
            "started_at": now,
            "completed_at": None,
            "result_url": None,
            "payment_type": payment["payment_type"],
            "consume_trial": payment["payment_type"] == "trial",
        }

    async def get_session(
        self,
        session_id: str,
        auth: AuthContext,
        session_data: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        """Get session by ID, scoped to workspace."""
        if session_data is None:
            return None
        if session_data.get("workspace_id") != auth.workspace_id:
            return None
        return session_data

    async def list_sessions(
        self,
        auth: AuthContext,
        all_sessions: list[dict[str, Any]],
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """List sessions for workspace, paginated."""
        workspace_sessions = [
            s for s in all_sessions
            if s.get("workspace_id") == auth.workspace_id
        ]
        start = (page - 1) * page_size
        return workspace_sessions[start:start + page_size]

    async def run_session_background(
        self, session_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a session in the background (arch §7.3).

        In production this invokes Studio, tracks cost via adapter,
        and promotes memory entries. Here we define the lifecycle
        contract that tests verify.
        """
        session_id = session_data["id"]

        # Update to RUNNING
        session_data["status"] = SessionStatus.RUNNING.value
        self._event_bus.publish(SessionEvent(
            type="cycle_start",
            session_id=session_id,
            data={"cycle": 1, "total_cycles": 3},
        ))

        try:
            # Invoke Studio (if available)
            if self._studio is not None:
                template = (
                    "strategic_session_quick.yaml"
                    if session_data["depth"] == "quick"
                    else "strategic_session.yaml"
                )
                result = await self._studio.invoke(
                    template_path=template,
                    question=session_data["question"],
                    context=session_data["context"],
                    rendering_mode=session_data["rendering_mode"],
                )

                session_data["result_markdown"] = result.markdown
                session_data["result_html"] = result.html
                session_data["cost_usd"] = result.cost_usd

                # C-4: promote memory entries
                if self._memory_adapter and result.status == "completed":
                    await self._memory_adapter.promote_entries(
                        workspace_id=session_data["workspace_id"],
                        session_id=session_id,
                        task_signature=result.task_signature,
                    )

            session_data["status"] = SessionStatus.COMPLETED.value
            session_data["completed_at"] = datetime.now(timezone.utc)

            self._event_bus.publish(SessionEvent(
                type="complete",
                session_id=session_id,
                data={"cost_usd": session_data.get("cost_usd")},
            ))

        except Exception as exc:
            session_data["status"] = SessionStatus.FAILED.value
            self._event_bus.publish(SessionEvent(
                type="error",
                session_id=session_id,
                data={"error": str(exc)},
            ))

        finally:
            self._event_bus.complete(session_id)

        return session_data
