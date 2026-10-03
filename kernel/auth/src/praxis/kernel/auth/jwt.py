"""JWT verification using OIDC metadata and caller-provided signing keys.

Stage 14 V3.A: removed static `self._jwks` fallback (CVE-class fix per
F-13-V3-JWKS-NOT-INTEGRATED-01). `decode` now requires a `key` argument,
typically resolved by `OidcPolicy.authenticate` via `JwksCache.get_key`
(kid-aware rotation). `JoseError` (signature/audience/claims failure)
is wrapped as the typed `AuthenticationError` from `praxis.kernel.auth.claims`.
"""

from __future__ import annotations

from typing import Any

from authlib.jose import JsonWebToken  # type: ignore[import-untyped]
from authlib.jose.errors import JoseError  # type: ignore[import-untyped]

from praxis.kernel.auth.claims import AuthClaims, AuthenticationError, validate_claims
from praxis.kernel.auth.oidc import OidcMetadata

_ALLOWED_ALGORITHMS: frozenset[str] = frozenset(
    {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}
)


class UnsupportedAlgorithmError(ValueError):
    pass


class JwtVerifier:
    """JWT verifier with externalised key resolution.

    The signing key MUST be supplied at decode time by the caller (typically
    `OidcPolicy.authenticate` after `JwksCache.get_key`). There is no
    persistent JWKS state on the verifier — rotation handling lives in the
    cache layer per Stage 14 V3.A contract.
    """

    # Class attribute alias for the documented FQN access pattern
    # `JwtVerifier.AuthenticationError`. The canonical type lives in claims.py.
    AuthenticationError = AuthenticationError

    def __init__(self, metadata: OidcMetadata) -> None:
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
        self._issuer = metadata.issuer

    @property
    def issuer(self) -> str:
        return self._issuer

    def decode(self, token: str, audience: str, key: dict[str, Any]) -> AuthClaims:
        """Verify signature + audience using the caller-supplied key.

        Raises `AuthenticationError` on any authlib failure (signature,
        audience mismatch, required-claims schema). No static-key fallback.
        """
        try:
            claims = self._jwt.decode(
                token, key, claims_options={"aud": {"values": [audience]}}
            )
            claims.validate()
        except JoseError as exc:
            raise AuthenticationError(str(exc)) from exc
        raw: dict[str, str] = {k: str(v) for k, v in claims.items()}
        return validate_claims(raw)


__all__ = [
    "AuthenticationError",
    "JoseError",
    "JwtVerifier",
    "UnsupportedAlgorithmError",
]
