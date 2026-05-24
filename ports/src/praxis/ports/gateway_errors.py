"""Gateway port error specializations."""

from __future__ import annotations

from dataclasses import dataclass

from praxis.ports.common import ContractViolation


@dataclass(kw_only=True)
class GatewayCtxError(ContractViolation):
    """Gateway caller context is absent, malformed, or rejected."""

    context_field: str


class AuthClaimsAccessError(Exception):
    """Raised when AuthClaims is accessed without an explicit unwrap."""


__all__ = [
    "AuthClaimsAccessError",
    "GatewayCtxError",
]
