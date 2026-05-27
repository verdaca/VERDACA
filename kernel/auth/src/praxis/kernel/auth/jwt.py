"""JWT verification using OIDC metadata and JWKS."""

from __future__ import annotations

from typing import Any

from authlib.jose import JsonWebToken  # type: ignore[import-untyped]
from authlib.jose.errors import JoseError  # type: ignore[import-untyped]

from praxis.kernel.auth.claims import AuthClaims, validate_claims
from praxis.kernel.auth.oidc import OidcMetadata

_ALLOWED_ALGORITHMS: frozenset[str] = frozenset(
    {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}
)


class UnsupportedAlgorithmError(ValueError):
    pass


class JwtVerifier:
    def __init__(self, metadata: OidcMetadata, jwks: dict[str, Any]) -> None:
        safe_algs = [
            alg
            for alg in metadata.id_token_signing_alg_values_supported
            if alg in _ALLOWED_ALGORITHMS
        ]
        if not safe_algs:
            raise UnsupportedAlgorithmError(
                f"No safe algorithms in IdP discovery response for {metadata.issuer!r}. "
                f"Supported: {metadata.id_token_signing_alg_values_supported}"
            )
        self._jwt = JsonWebToken(safe_algs)
        self._jwks = jwks
        self._issuer = metadata.issuer

    def decode(self, token: str, audience: str) -> AuthClaims:
        claims = self._jwt.decode(token, self._jwks, claims_options={"aud": {"values": [audience]}})
        claims.validate()
        raw: dict[str, str] = {k: str(v) for k, v in claims.items()}
        return validate_claims(raw)


__all__ = ["JoseError", "JwtVerifier", "UnsupportedAlgorithmError"]
