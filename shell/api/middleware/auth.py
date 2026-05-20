"""Clerk JWT authentication middleware — arch §4.1–§4.3.

Validates Clerk JWTs via JWKS endpoint (production) or
FakeClerkProvider (tests). Extracts workspace_id and role
from token claims.

Binding anchors:
  - shell/architecture.md §4.1 Clerk Integration
  - shell/architecture.md §4.3 RBAC
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class WorkspaceRole(str, Enum):
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


@dataclass(frozen=True)
class AuthContext:
    """Decoded JWT claims for the current request."""

    workspace_id: str
    user_id: str
    role: WorkspaceRole


@runtime_checkable
class ClerkProviderProtocol(Protocol):
    """Interface for Clerk JWT validation."""

    def decode_jwt(self, token: str) -> dict[str, str] | None: ...


class AuthError(Exception):
    """Raised when authentication or authorization fails."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


# RBAC matrix per arch §4.3
_ROLE_PERMISSIONS: dict[WorkspaceRole, set[str]] = {
    WorkspaceRole.OWNER: {
        "create_session", "view_own", "view_team",
        "manage_billing", "manage_team",
    },
    WorkspaceRole.MEMBER: {
        "create_session", "view_own", "view_team",
    },
    WorkspaceRole.VIEWER: {
        "view_team",  # shared only
    },
}


class AuthMiddleware:
    """Validates Clerk JWTs and enforces RBAC.

    Production: validates via Clerk JWKS endpoint.
    Tests: uses FakeClerkProvider for test JWTs.
    """

    def __init__(self, provider: ClerkProviderProtocol) -> None:
        self._provider = provider

    def authenticate(self, authorization: str | None) -> AuthContext:
        """Extract and validate JWT from Authorization header.

        Returns AuthContext on success, raises AuthError on failure.
        """
        if not authorization:
            raise AuthError(401, "Missing Authorization header")

        parts = authorization.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthError(401, "Invalid Authorization header format")

        token = parts[1]
        if not token:
            raise AuthError(401, "Empty token")

        claims = self._provider.decode_jwt(token)
        if claims is None:
            raise AuthError(401, "Invalid or expired token")

        try:
            role = WorkspaceRole(claims.get("role", "viewer"))
        except ValueError:
            raise AuthError(401, "Invalid role in token")

        return AuthContext(
            workspace_id=claims["workspace_id"],
            user_id=claims.get("user_id", ""),
            role=role,
        )

    def authorize(self, auth: AuthContext, permission: str) -> None:
        """Check that the role has the required permission.

        Raises AuthError(403) if denied.
        """
        allowed = _ROLE_PERMISSIONS.get(auth.role, set())
        if permission not in allowed:
            raise AuthError(
                403,
                f"Role {auth.role.value!r} does not have permission {permission!r}",
            )
