"""Stage 12 H#3.2 MAC-Ts for OIDC discovery and JWKS cache behavior."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from praxis.kernel.auth import idp
from praxis.kernel.auth.oidc import JwksCache, OidcMetadata, UnknownKeyError

CASSETTES_DIR = Path(__file__).parents[4] / "fixtures" / "vcr_cassettes"
ISSUER = "https://login.microsoftonline.com/stage12-tenant/v2.0"
JWKS_URI = "https://login.microsoftonline.com/stage12-tenant/discovery/v2.0/keys"


class _HttpResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class _QueuedAsyncClient:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = responses
        self.requests: list[str] = []

    async def __aenter__(self) -> _QueuedAsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, url: str, **_kwargs: object) -> _HttpResponse:
        self.requests.append(url)
        return _HttpResponse(self._responses.pop(0))


class _CassetteJwksCache(JwksCache):
    def __init__(self, responses: list[dict[str, Any]], ttl_seconds: int = 3600) -> None:
        super().__init__(ttl_seconds=ttl_seconds)
        self._responses = responses
        self.fetches: list[str] = []

    async def _fetch_jwks(self, jwks_uri: str) -> dict[str, Any]:
        self.fetches.append(jwks_uri)
        return self._responses.pop(0)


def _cassette_payload(name: str, index: int = 0) -> dict[str, Any]:
    cassette = yaml.safe_load((CASSETTES_DIR / name).read_text(encoding="utf-8"))
    body = cassette["interactions"][index]["response"]["body"]["string"]
    loaded = json.loads(body)
    assert isinstance(loaded, dict)
    return loaded


def _metadata() -> OidcMetadata:
    return OidcMetadata(
        issuer=ISSUER,
        jwks_uri=JWKS_URI,
        id_token_signing_alg_values_supported=("RS256",),
    )


def _discover_factory(metadata: OidcMetadata) -> Callable[..., Any]:
    async def _discover(_issuer: str, **_kwargs: object) -> OidcMetadata:
        return metadata

    return _discover


@pytest.mark.asyncio
async def test_M_T_AUTH_OIDC_DISCOVERY_HAPPY_01_parses_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _cassette_payload("oidc_discovery_entra.yaml")
    client = _QueuedAsyncClient([payload])
    monkeypatch.setattr(idp.httpx, "AsyncClient", lambda: client)

    metadata = await idp.discover(ISSUER)

    assert client.requests == [f"{ISSUER}/.well-known/openid-configuration"]
    assert metadata.issuer == ISSUER
    assert metadata.jwks_uri == JWKS_URI
    assert metadata.id_token_signing_alg_values_supported == ("RS256",)
    assert metadata.extra["token_endpoint"].endswith("/oauth2/v2.0/token")


@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_ROTATION_01_invalidation_fetches_rotated_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _cassette_payload("jwks_rotation.yaml", index=0)
    second = _cassette_payload("jwks_rotation.yaml", index=1)
    monkeypatch.setattr(idp, "discover", _discover_factory(_metadata()))
    cache = _CassetteJwksCache([first, second])

    key = await cache.get_key(ISSUER, "key-003")

    assert key["kid"] == "key-003"
    assert cache.fetches == [JWKS_URI, JWKS_URI]


@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_UNKNOWN_KID_01_raises_after_refetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _cassette_payload("jwks_valid.yaml")
    second = _cassette_payload("jwks_valid.yaml")
    monkeypatch.setattr(idp, "discover", _discover_factory(_metadata()))
    cache = _CassetteJwksCache([first, second])

    with pytest.raises(UnknownKeyError):
        await cache.get_key(ISSUER, "missing-kid")

    assert cache.fetches == [JWKS_URI, JWKS_URI]


@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_CACHE_TTL_RESPECTED_01_uses_stale_until_expiry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _cassette_payload("jwks_rotation.yaml", index=0)
    second = _cassette_payload("jwks_rotation.yaml", index=1)
    monotonic_values = [100.0, 105.0, 112.0, 112.0, 112.0]

    def fake_monotonic() -> float:
        if len(monotonic_values) > 1:
            return monotonic_values.pop(0)
        return monotonic_values[0]

    monkeypatch.setattr(idp, "discover", _discover_factory(_metadata()))
    monkeypatch.setattr("praxis.kernel.auth.oidc.time.monotonic", fake_monotonic)
    cache = _CassetteJwksCache([first, second], ttl_seconds=10)

    _, initial = await cache.get_or_fetch(ISSUER)
    _, within_ttl = await cache.get_or_fetch(ISSUER)
    _, after_expiry = await cache.get_or_fetch(ISSUER)

    assert [key["kid"] for key in initial["keys"]] == ["key-001"]
    assert [key["kid"] for key in within_ttl["keys"]] == ["key-001"]
    assert [key["kid"] for key in after_expiry["keys"]] == ["key-001", "key-003"]
    assert cache.fetches == [JWKS_URI, JWKS_URI]
