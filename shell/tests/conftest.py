"""Shared pytest fixtures for Shell tests — test-strategy §5.1.

All fixtures are function-scoped for isolation.

Binding: shell/test-strategy.md §5.1–§5.2.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from api.models import (
    CreateSessionRequest,
    RenderingMode,
    SessionDepth,
    SessionResponse,
    SessionStatus,
)


# ---------------------------------------------------------------------------
# FakeClerkProvider — test-strategy §5.1
# ---------------------------------------------------------------------------

class FakeClerkProvider:
    """Issues test JWTs with configurable workspace_id and role.

    Not a real JWT — returns a token string that the FakeAuthMiddleware
    can decode. Production uses real Clerk JWKS validation.
    """

    def __init__(self, secret: str = "test-secret") -> None:
        self._secret = secret

    def issue_jwt(
        self,
        workspace_id: str = "ws-test-1",
        user_id: str = "user-test-1",
        role: str = "owner",
    ) -> str:
        """Encode workspace_id, user_id, role as a |-delimited test token."""
        return f"test|{workspace_id}|{user_id}|{role}"

    def decode_jwt(self, token: str) -> dict[str, str] | None:
        """Decode a test token. Returns None if format is invalid."""
        parts = token.split("|")
        if len(parts) != 4 or parts[0] != "test":
            return None
        return {
            "workspace_id": parts[1],
            "user_id": parts[2],
            "role": parts[3],
        }


# ---------------------------------------------------------------------------
# FakeStripeClient — test-strategy §5.1
# ---------------------------------------------------------------------------

class FakeStripeClient:
    """Stubs PaymentIntent creation with configurable success/failure."""

    def __init__(self, *, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self.created_intents: list[dict[str, Any]] = []
        self.webhook_events: list[dict[str, Any]] = []

    async def create_payment_intent(
        self, *, amount: int, currency: str, customer: str
    ) -> dict[str, Any]:
        intent = {
            "id": f"pi_test_{len(self.created_intents) + 1}",
            "amount": amount,
            "currency": currency,
            "customer": customer,
            "status": "failed" if self._should_fail else "succeeded",
        }
        self.created_intents.append(intent)
        return intent

    def verify_webhook_signature(self, payload: bytes, sig_header: str, secret: str) -> dict:
        """Verify webhook signature. In test mode, accept 'valid-sig' only."""
        if sig_header != "valid-sig":
            raise ValueError("Invalid signature")
        import json
        return json.loads(payload)


# ---------------------------------------------------------------------------
# FakeStudioSession — test-strategy §5.1
# ---------------------------------------------------------------------------

@dataclass
class FakeSessionResult:
    """Canned session result without running MAC."""

    status: str = "completed"
    cost_events: list[dict[str, Any]] = field(default_factory=list)
    task_signature: str = "test-task-sig"
    markdown: str = "# Test Result\n\nAnalysis complete."
    html: str = "<h1>Test Result</h1><p>Analysis complete.</p>"
    cost_usd: float = 2.50
    duration_seconds: float = 120.0


class FakeStudioSession:
    """Returns canned SessionResult without running MAC."""

    def __init__(self, *, result: FakeSessionResult | None = None) -> None:
        self._result = result or FakeSessionResult()
        self.invocations: list[dict[str, Any]] = []

    async def invoke(
        self,
        *,
        template_path: str,
        question: str,
        context: str | None,
        rendering_mode: str,
    ) -> FakeSessionResult:
        self.invocations.append({
            "template_path": template_path,
            "question": question,
            "context": context,
            "rendering_mode": rendering_mode,
        })
        return self._result


# ---------------------------------------------------------------------------
# FakeCostTracker — test-strategy §5.1
# ---------------------------------------------------------------------------

@dataclass
class FakeCostRecord:
    request_id: str
    session_id: str
    cost_usd: float = 0.0


class FakeCostTracker:
    """Records track_cost calls for assertion."""

    def __init__(self) -> None:
        self._events: list[tuple[Any, Any]] = []

    async def track_cost(self, request: Any, response: Any) -> FakeCostRecord:
        self._events.append((request, response))
        return FakeCostRecord(
            request_id=request.request_id,
            session_id=getattr(request, "session_id", ""),
            cost_usd=0.0,
        )

    @property
    def events(self) -> list[tuple[Any, Any]]:
        return list(self._events)

    def reset(self) -> None:
        self._events.clear()


# ---------------------------------------------------------------------------
# FakeMemoryFacade — test-strategy §5.2 (C-4 contract verification)
# ---------------------------------------------------------------------------

class FakeMemoryFacade:
    """Captures calls to promote_task_entries for contract assertion.

    The REAL Memory facade exposes promote_task_entries().
    This fake verifies that ShellMemoryAdapter calls the correct method
    name with the correct signature — the C-4 debt resolution check.
    """

    def __init__(self) -> None:
        self.promote_calls: list[dict[str, str]] = []

    async def promote_task_entries(
        self,
        *,
        workspace_id: str,
        task_signature: str,
        confirmation_source: str,
    ) -> None:
        self.promote_calls.append({
            "workspace_id": workspace_id,
            "task_signature": task_signature,
            "confirmation_source": confirmation_source,
        })


# ---------------------------------------------------------------------------
# Convenience fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_clerk() -> FakeClerkProvider:
    return FakeClerkProvider(secret="test-secret")


@pytest.fixture
def fake_stripe() -> FakeStripeClient:
    return FakeStripeClient()


@pytest.fixture
def fake_stripe_failing() -> FakeStripeClient:
    return FakeStripeClient(should_fail=True)


@pytest.fixture
def fake_studio() -> FakeStudioSession:
    return FakeStudioSession()


@pytest.fixture
def fake_cost_tracker() -> FakeCostTracker:
    return FakeCostTracker()


@pytest.fixture
def fake_memory() -> FakeMemoryFacade:
    return FakeMemoryFacade()


@pytest.fixture
def auth_headers(fake_clerk: FakeClerkProvider) -> dict[str, str]:
    """JWT headers for default test workspace."""
    return {
        "Authorization": f"Bearer {fake_clerk.issue_jwt(workspace_id='ws-test-1', role='owner')}"
    }


@pytest.fixture
def auth_headers_ws2(fake_clerk: FakeClerkProvider) -> dict[str, str]:
    """JWT headers for a second workspace (isolation tests)."""
    return {
        "Authorization": f"Bearer {fake_clerk.issue_jwt(workspace_id='ws-test-2', role='owner')}"
    }


@pytest.fixture
def auth_headers_viewer(fake_clerk: FakeClerkProvider) -> dict[str, str]:
    """JWT headers for a viewer role (RBAC tests)."""
    return {
        "Authorization": f"Bearer {fake_clerk.issue_jwt(workspace_id='ws-test-1', role='viewer')}"
    }


@pytest.fixture
def auth_headers_member(fake_clerk: FakeClerkProvider) -> dict[str, str]:
    """JWT headers for a member role (RBAC tests)."""
    return {
        "Authorization": f"Bearer {fake_clerk.issue_jwt(workspace_id='ws-test-1', role='member')}"
    }
