"""Auth claim validation for gateway identity surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final

if TYPE_CHECKING:
    from praxis.kernel.auth.jwt import JwtVerifier


class ClaimsValidationError(ValueError):
    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"Required claims absent: {missing}")


class AuthenticationError(ValueError):
    """Raised when JWT verification fails (kid lookup, signature, audience, or claims schema).

    Stage 14 V3.A: typed surface for the CVE-class auth failure path. Replaces
    the prior pattern of leaking authlib JoseError or httpx errors through
    OidcPolicy.authenticate. Production callers catch this single type;
    GatewayCtxError wraps via service._auth_error.
    """


_REQUIRED_CLAIMS: frozenset[str] = frozenset({"sub", "iss", "aud", "iat", "exp"})


@final
@dataclass(frozen=True)
class AuthClaims:
    _claims: Mapping[str, str]

    def get(self, key: str) -> str | None:
        return self._claims.get(key)

    def require(self, key: str) -> str:
        try:
            return self._claims[key]
        except KeyError:
            raise ClaimsValidationError([key]) from None


def validate_claims(raw: Mapping[str, str]) -> AuthClaims:
    """Standalone validator for H#1.5 frozen auth-claims shape."""
    missing = [k for k in _REQUIRED_CLAIMS if k not in raw]
    if missing:
        raise ClaimsValidationError(missing)
    return AuthClaims(_claims=raw)


def extract_claims(
    token: str,
    verifier: JwtVerifier,
    audience: str,
    key: dict[str, Any],
) -> dict[str, str]:
    """Decode and validate a bearer token through an explicit JWT verifier.

    Stage 14 V3.A: parameterized audience + caller-provided signing key.
    Test-only: production paths verify via OidcPolicy.authenticate which
    resolves the signing key from JwksCache (kid-aware rotation). Direct
    callers MUST pre-resolve the key (typically via JwksCache.get_key).
    The previous hardcoded `_CHANNEL_ADAPTER_AUDIENCE` constant has been
    removed; channel layer threads audience from configured OidcPolicy.
    """
    return dict(verifier.decode(token, audience, key)._claims)


__all__ = [
    "AuthClaims",
    "AuthenticationError",
    "ClaimsValidationError",
    "extract_claims",
    "validate_claims",
]
