"""Auth claim validation for gateway identity surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from praxis.kernel.auth.jwt import JwtVerifier


class ClaimsValidationError(ValueError):
    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"Required claims absent: {missing}")


_REQUIRED_CLAIMS: frozenset[str] = frozenset({"sub", "iss", "aud", "iat", "exp"})
_CHANNEL_ADAPTER_AUDIENCE = "verdaca-channel-adapter"


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


def extract_claims(token: str, verifier: JwtVerifier) -> dict[str, str]:
    """Decode and validate a bearer token through an explicit JWT verifier."""
    return dict(verifier.decode(token, audience=_CHANNEL_ADAPTER_AUDIENCE)._claims)


__all__ = ["AuthClaims", "ClaimsValidationError", "extract_claims", "validate_claims"]
