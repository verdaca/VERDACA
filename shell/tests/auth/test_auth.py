"""Authentication and RBAC tests — test-strategy §4.3.

SHELL-T-AUTH-UNIT-01: Valid JWT → request proceeds with workspace_id
SHELL-T-AUTH-UNIT-02: Missing JWT → 401
SHELL-T-AUTH-UNIT-03: Expired/invalid JWT → 401
SHELL-T-AUTH-UNIT-04: JWT for workspace A → cannot access workspace B
SHELL-T-AUTH-UNIT-05: Viewer role → cannot create sessions (403)
SHELL-T-AUTH-UNIT-06: Member role → can create sessions, cannot manage billing
"""

from __future__ import annotations

import pytest

from api.middleware.auth import AuthContext, AuthError, AuthMiddleware, WorkspaceRole
from tests.conftest import FakeClerkProvider


@pytest.fixture
def auth_middleware(fake_clerk: FakeClerkProvider) -> AuthMiddleware:
    return AuthMiddleware(provider=fake_clerk)


class TestAuthentication:
    """JWT validation tests."""

    @pytest.mark.shell_auth
    @pytest.mark.critical
    def test_auth_unit_01_valid_jwt(
        self, auth_middleware: AuthMiddleware, fake_clerk: FakeClerkProvider
    ):
        """SHELL-T-AUTH-UNIT-01: Valid JWT → workspace_id extracted."""
        token = fake_clerk.issue_jwt(workspace_id="ws-abc", role="owner")
        ctx = auth_middleware.authenticate(f"Bearer {token}")

        assert ctx.workspace_id == "ws-abc"
        assert ctx.role == WorkspaceRole.OWNER
        assert ctx.user_id == "user-test-1"

    @pytest.mark.shell_auth
    @pytest.mark.critical
    def test_auth_unit_02_missing_jwt(self, auth_middleware: AuthMiddleware):
        """SHELL-T-AUTH-UNIT-02: Missing JWT → 401."""
        with pytest.raises(AuthError) as exc_info:
            auth_middleware.authenticate(None)
        assert exc_info.value.status_code == 401

    @pytest.mark.shell_auth
    @pytest.mark.critical
    def test_auth_unit_02_empty_header(self, auth_middleware: AuthMiddleware):
        """SHELL-T-AUTH-UNIT-02: Empty Authorization header → 401."""
        with pytest.raises(AuthError) as exc_info:
            auth_middleware.authenticate("")
        assert exc_info.value.status_code == 401

    @pytest.mark.shell_auth
    @pytest.mark.critical
    def test_auth_unit_03_invalid_jwt(self, auth_middleware: AuthMiddleware):
        """SHELL-T-AUTH-UNIT-03: Invalid/expired JWT → 401."""
        with pytest.raises(AuthError) as exc_info:
            auth_middleware.authenticate("Bearer invalid-garbage-token")
        assert exc_info.value.status_code == 401

    @pytest.mark.shell_auth
    @pytest.mark.critical
    def test_auth_unit_03_malformed_bearer(self, auth_middleware: AuthMiddleware):
        """SHELL-T-AUTH-UNIT-03: Malformed bearer → 401."""
        with pytest.raises(AuthError) as exc_info:
            auth_middleware.authenticate("NotBearer sometoken")
        assert exc_info.value.status_code == 401

    @pytest.mark.shell_auth
    @pytest.mark.critical
    def test_auth_unit_04_workspace_isolation(
        self, auth_middleware: AuthMiddleware, fake_clerk: FakeClerkProvider
    ):
        """SHELL-T-AUTH-UNIT-04: JWT for workspace A → workspace A context only."""
        token_a = fake_clerk.issue_jwt(workspace_id="ws-A")
        token_b = fake_clerk.issue_jwt(workspace_id="ws-B")

        ctx_a = auth_middleware.authenticate(f"Bearer {token_a}")
        ctx_b = auth_middleware.authenticate(f"Bearer {token_b}")

        assert ctx_a.workspace_id == "ws-A"
        assert ctx_b.workspace_id == "ws-B"
        assert ctx_a.workspace_id != ctx_b.workspace_id


class TestRBAC:
    """Role-Based Access Control tests per arch §4.3."""

    @pytest.mark.shell_auth
    @pytest.mark.critical
    def test_auth_unit_05_viewer_cannot_create_session(
        self, auth_middleware: AuthMiddleware, fake_clerk: FakeClerkProvider
    ):
        """SHELL-T-AUTH-UNIT-05: Viewer → cannot create sessions (403)."""
        token = fake_clerk.issue_jwt(workspace_id="ws-1", role="viewer")
        ctx = auth_middleware.authenticate(f"Bearer {token}")

        with pytest.raises(AuthError) as exc_info:
            auth_middleware.authorize(ctx, "create_session")
        assert exc_info.value.status_code == 403

    @pytest.mark.shell_auth
    @pytest.mark.critical
    def test_auth_unit_06_member_can_create_cannot_billing(
        self, auth_middleware: AuthMiddleware, fake_clerk: FakeClerkProvider
    ):
        """SHELL-T-AUTH-UNIT-06: Member → can create sessions, cannot manage billing."""
        token = fake_clerk.issue_jwt(workspace_id="ws-1", role="member")
        ctx = auth_middleware.authenticate(f"Bearer {token}")

        # Can create sessions
        auth_middleware.authorize(ctx, "create_session")  # no raise

        # Cannot manage billing
        with pytest.raises(AuthError) as exc_info:
            auth_middleware.authorize(ctx, "manage_billing")
        assert exc_info.value.status_code == 403

    @pytest.mark.shell_auth
    def test_owner_has_all_permissions(
        self, auth_middleware: AuthMiddleware, fake_clerk: FakeClerkProvider
    ):
        """Owner role has all permissions per arch §4.3."""
        token = fake_clerk.issue_jwt(workspace_id="ws-1", role="owner")
        ctx = auth_middleware.authenticate(f"Bearer {token}")

        for perm in ["create_session", "view_own", "view_team", "manage_billing", "manage_team"]:
            auth_middleware.authorize(ctx, perm)  # no raise

    @pytest.mark.shell_auth
    def test_viewer_can_view_team(
        self, auth_middleware: AuthMiddleware, fake_clerk: FakeClerkProvider
    ):
        """Viewer can view_team (shared only) per arch §4.3."""
        token = fake_clerk.issue_jwt(workspace_id="ws-1", role="viewer")
        ctx = auth_middleware.authenticate(f"Bearer {token}")
        auth_middleware.authorize(ctx, "view_team")  # no raise
