"""OIDC identity-provider discovery."""

from __future__ import annotations

import httpx

from praxis.kernel.auth.oidc import OidcMetadata

_DISCOVERY_SUFFIX = "/.well-known/openid-configuration"


async def discover(issuer: str) -> OidcMetadata:
    """SOLE public API. Caller determines which issuer to pass."""
    url = issuer.rstrip("/") + _DISCOVERY_SUFFIX
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, follow_redirects=True, timeout=10.0)
        resp.raise_for_status()
        doc = resp.json()
    return OidcMetadata(
        issuer=doc["issuer"],
        jwks_uri=doc["jwks_uri"],
        id_token_signing_alg_values_supported=doc.get(
            "id_token_signing_alg_values_supported", []
        ),
        extra={
            k: v
            for k, v in doc.items()
            if k not in {"issuer", "jwks_uri", "id_token_signing_alg_values_supported"}
        },
    )


__all__ = ["discover"]
