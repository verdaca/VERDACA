"""OIDC identity-provider discovery."""

from __future__ import annotations

from typing import Any, cast

import httpx

from praxis.kernel.auth.oidc import OidcMetadata

_DISCOVERY_SUFFIX = "/.well-known/openid-configuration"


async def discover(
    issuer: str,
    httpx_client: httpx.AsyncClient | None = None,
) -> OidcMetadata:
    """SOLE public API. Caller determines issuer; inject a client for production pooling."""
    url = issuer.rstrip("/") + _DISCOVERY_SUFFIX
    if httpx_client is None:
        async with httpx.AsyncClient() as client:
            return await _fetch_discovery(url, client)
    return await _fetch_discovery(url, httpx_client)


async def _fetch_discovery(url: str, client: httpx.AsyncClient) -> OidcMetadata:
    resp = await client.get(url, follow_redirects=True, timeout=10.0)
    resp.raise_for_status()
    doc = cast(dict[str, Any], resp.json())
    return OidcMetadata(
        issuer=doc["issuer"],
        jwks_uri=doc["jwks_uri"],
        id_token_signing_alg_values_supported=tuple(
            doc.get("id_token_signing_alg_values_supported", [])
        ),
        extra={
            k: v
            for k, v in doc.items()
            if k not in {"issuer", "jwks_uri", "id_token_signing_alg_values_supported"}
        },
    )


__all__ = ["discover"]
