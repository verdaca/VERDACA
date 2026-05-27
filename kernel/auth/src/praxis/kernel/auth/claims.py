"""Auth claim validation for gateway identity surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final


class ClaimsValidationError(ValueError):
    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"Required claims absent: {missing}")


_REQUIRED_CLAIMS: frozenset[str] = frozenset({"sub", "iss", "aud", "iat", "exp"})


@final
@dataclass(frozen=True)
class AuthClaims:
    _claims: Mapping[str, str]


def validate_claims(raw: Mapping[str, str]) -> AuthClaims:
    """Standalone validator for H#1.5 frozen auth-claims shape."""
    missing = [k for k in _REQUIRED_CLAIMS if k not in raw]
    if missing:
        raise ClaimsValidationError(missing)
    return AuthClaims(_claims=raw)


__all__ = ["AuthClaims", "ClaimsValidationError", "validate_claims"]
