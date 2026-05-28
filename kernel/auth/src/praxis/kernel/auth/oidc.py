"""OIDC metadata and JWKS cache primitives."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

import httpx

from praxis.kernel.auth.claims import AuthClaims

if TYPE_CHECKING:
    from praxis.kernel.auth.jwt import JwtVerifier


@dataclass(frozen=True)
class OidcMetadata:
    issuer: str
    jwks_uri: str
    id_token_signing_alg_values_supported: tuple[str, ...]
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class _CacheEntry:
    metadata: OidcMetadata
    jwks: dict[str, Any]
    fetched_at: float


class UnknownKeyError(KeyError):
    """Raised when a JWKS does not contain a requested key id."""


class OidcPolicy:
    """Tenant OIDC verifier with an explicit JwtVerifier dependency."""

    def __init__(self, *, verifier: JwtVerifier, audience: str) -> None:
        self._verifier = verifier
        self._audience = audience

    async def authenticate(self, bearer_token: str) -> AuthClaims:
        return self._verifier.decode(bearer_token, audience=self._audience)


class JwksCache:
    """TTL-based JWKS cache with explicit invalidation for rotation."""

    def __init__(
        self,
        ttl_seconds: int = 3600,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._ttl = ttl_seconds
        self._httpx_client = httpx_client
        self._owned_httpx_client: httpx.AsyncClient | None = None
        self._store: dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get_or_fetch(self, issuer: str) -> tuple[OidcMetadata, dict[str, Any]]:
        entry = self._store.get(issuer)
        if entry is not None and self._is_fresh(entry):
            return entry.metadata, entry.jwks
        return await self._refresh(issuer)

    async def invalidate(self, issuer: str) -> tuple[OidcMetadata, dict[str, Any]]:
        from praxis.kernel.auth.idp import discover

        async with self._lock:
            self._store.pop(issuer, None)
            metadata = await discover(issuer, httpx_client=self._client())
            jwks = await self._fetch_jwks(metadata.jwks_uri)
            self._store[issuer] = _CacheEntry(
                metadata=metadata,
                jwks=jwks,
                fetched_at=time.monotonic(),
            )
            return metadata, jwks

    async def get_key(self, issuer: str, kid: str) -> dict[str, Any]:
        metadata, jwks = await self.get_or_fetch(issuer)
        key = _find_key(jwks, kid)
        if key is not None:
            return key

        metadata, jwks = await self.invalidate(metadata.issuer)
        key = _find_key(jwks, kid)
        if key is None:
            raise UnknownKeyError(kid)
        return key

    async def _refresh(self, issuer: str) -> tuple[OidcMetadata, dict[str, Any]]:
        from praxis.kernel.auth.idp import discover

        async with self._lock:
            entry = self._store.get(issuer)
            if entry is not None and self._is_fresh(entry):
                return entry.metadata, entry.jwks

            metadata = await discover(issuer, httpx_client=self._client())
            jwks = await self._fetch_jwks(metadata.jwks_uri)
            self._store[issuer] = _CacheEntry(
                metadata=metadata,
                jwks=jwks,
                fetched_at=time.monotonic(),
            )
            return metadata, jwks

    async def _fetch_jwks(self, jwks_uri: str) -> dict[str, Any]:
        resp = await self._client().get(jwks_uri, timeout=10.0)
        resp.raise_for_status()
        jwks = cast(dict[str, Any], resp.json())
        return jwks

    def _is_fresh(self, entry: _CacheEntry) -> bool:
        return (time.monotonic() - entry.fetched_at) < self._ttl

    def _client(self) -> httpx.AsyncClient:
        if self._httpx_client is not None:
            return self._httpx_client
        if self._owned_httpx_client is None:
            self._owned_httpx_client = httpx.AsyncClient()
        return self._owned_httpx_client


def _find_key(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    for key in jwks.get("keys", []):
        if isinstance(key, dict) and key.get("kid") == kid:
            return key
    return None


__all__ = ["JwksCache", "OidcMetadata", "OidcPolicy", "UnknownKeyError"]
