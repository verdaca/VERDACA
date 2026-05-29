"""Stage 13 + Stage 14 OIDC policy construction MAC-Ts.

Stage 13 (existing): 2 TypeError MAC-Ts for OidcPolicy/extract_claims signature.
Stage 14 B1 (new):
  - 6 JWKS MAC-Ts (1 @no_waiver: M-T-AUTH-JWKS-ROTATION-INVARIANT-01)
  - 2 AUDIENCE MAC-Ts (no @no_waiver per Murat R3 lock — risk 5 < 7 floor)
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from typing import Any

import httpx
import pytest

from praxis.kernel.auth import OidcPolicy, extract_claims
from praxis.kernel.auth.claims import AuthClaims, AuthenticationError
from praxis.kernel.auth.jwt import JwtVerifier
from praxis.kernel.auth.oidc import (
    JwksCache,
    OidcMetadata,
    _CacheEntry,
)

ISSUER = "https://issuer.example.invalid"
JWKS_URI = "https://issuer.example.invalid/keys"
AUDIENCE = "api://verdaca"


# ─── Helpers ──────────────────────────────────────────────────────────────


def _metadata() -> OidcMetadata:
    return OidcMetadata(
        issuer=ISSUER,
        jwks_uri=JWKS_URI,
        id_token_signing_alg_values_supported=("RS256",),
    )


def _jwks_with_kids(*kids: str) -> dict[str, Any]:
    """Return a minimal JWKS dict with one entry per kid."""
    return {
        "keys": [
            {"kid": k, "kty": "RSA", "alg": "RS256", "n": "stub-n", "e": "AQAB"}
            for k in kids
        ]
    }


def _bearer_with_kid(
    kid: str,
    *,
    audience: str = AUDIENCE,
    sub: str = "user-1",
) -> str:
    """Construct a 3-segment bearer token with given kid in header.

    Payload is well-formed for required-claims validation; signature is dummy
    (B1 tests stub verifier.decode so signature is not actually verified).
    """
    header = {"alg": "RS256", "kid": kid, "typ": "JWT"}
    payload = {
        "sub": sub,
        "iss": ISSUER,
        "aud": audience,
        "iat": 1700000000,
        "exp": 1800000000,
        "nonce": f"test-nonce-{kid}",
    }

    def _b64(obj: dict[str, Any]) -> str:
        return (
            base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode())
            .rstrip(b"=")
            .decode()
        )

    sig_b64 = base64.urlsafe_b64encode(b"sig").rstrip(b"=").decode()
    return f"{_b64(header)}.{_b64(payload)}.{sig_b64}"


def _parse_bearer_payload(token: str) -> dict[str, Any]:
    """Parse JWT payload segment for test assertions (no signature verification)."""
    _, payload_segment, _ = token.split(".", 2)
    padding = "=" * (-len(payload_segment) % 4)
    decoded = base64.urlsafe_b64decode(payload_segment + padding)
    parsed = json.loads(decoded)
    assert isinstance(parsed, dict)
    return parsed


def _prepopulate_cache(
    cache: JwksCache,
    metadata: OidcMetadata,
    jwks: dict[str, Any],
    *,
    fetched_at: float | None = None,
) -> None:
    """Inject a cache entry without triggering _refresh."""
    cache._store[metadata.issuer] = _CacheEntry(
        metadata=metadata,
        jwks=jwks,
        fetched_at=fetched_at if fetched_at is not None else time.monotonic(),
    )


class _StubbedJwksCache(JwksCache):
    """Real JwksCache subclass with stubbed _fetch_jwks; mirrors Stage 12 cassette pattern."""

    def __init__(
        self,
        jwks_responses: list[dict[str, Any]] | None = None,
        *,
        fetch_raises: Exception | None = None,
        fetch_sleep_seconds: float = 0.0,
        ttl_seconds: int = 3600,
    ) -> None:
        super().__init__(ttl_seconds=ttl_seconds)
        self._jwks_responses = list(jwks_responses or [])
        self._fetch_raises = fetch_raises
        self._fetch_sleep_seconds = fetch_sleep_seconds
        self.fetch_calls: list[str] = []

    async def _fetch_jwks(self, jwks_uri: str) -> dict[str, Any]:
        self.fetch_calls.append(jwks_uri)
        if self._fetch_sleep_seconds > 0:
            await asyncio.sleep(self._fetch_sleep_seconds)
        if self._fetch_raises is not None:
            raise self._fetch_raises
        if not self._jwks_responses:
            raise AssertionError("Stub exhausted: no more JWKS responses queued")
        return self._jwks_responses.pop(0)


async def _stub_discover(_issuer: str, **_kwargs: object) -> OidcMetadata:
    return _metadata()


def _patch_discover(monkeypatch: pytest.MonkeyPatch) -> None:
    from praxis.kernel.auth import idp as _idp_module

    monkeypatch.setattr(_idp_module, "discover", _stub_discover)


def _patch_verifier_decode(
    monkeypatch: pytest.MonkeyPatch,
    *,
    audience_check: bool = False,
) -> list[tuple[str, str, dict[str, Any]]]:
    """Monkeypatch JwtVerifier.decode to return canned AuthClaims; record calls.

    audience_check=True: raise AuthenticationError when token aud != audience param.
    """
    calls: list[tuple[str, str, dict[str, Any]]] = []

    def fake_decode(
        self: JwtVerifier,
        token: str,
        audience: str,
        key: dict[str, Any],
    ) -> AuthClaims:
        calls.append((token, audience, key))
        if audience_check:
            payload = _parse_bearer_payload(token)
            if payload.get("aud") != audience:
                raise AuthenticationError(
                    f"audience mismatch: token aud={payload.get('aud')!r}, expected {audience!r}"
                )
        return AuthClaims(
            _claims={
                "sub": "user-1",
                "iss": ISSUER,
                "aud": audience,
                "iat": "1700000000",
                "exp": "1800000000",
                "nonce": "test-nonce-1",
            }
        )

    monkeypatch.setattr(JwtVerifier, "decode", fake_decode)
    return calls


# ─── Stage 13 existing tests (signature TypeError; preserved) ─────────────


def test_M_T_AUTH_OIDC_POLICY_VERIFIER_REQUIRED_01_missing_verifier_raises_typeerror() -> None:
    with pytest.raises(TypeError):
        OidcPolicy(audience="api://verdaca")  # type: ignore[call-arg]


def test_M_T_AUTH_EXTRACT_CLAIMS_VERIFIER_REQUIRED_01_missing_verifier_raises_typeerror() -> None:
    with pytest.raises(TypeError):
        extract_claims("token-string")  # type: ignore[call-arg]


# ─── Stage 14 JWKS bundle (6 MAC-Ts; 1 @no_waiver) ────────────────────────


@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_CACHE_HIT_01_authenticate_uses_cached_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bearer with cached kid → no JWKS HTTP fetch."""
    _patch_verifier_decode(monkeypatch)
    verifier = JwtVerifier(_metadata())
    cache = _StubbedJwksCache()
    _prepopulate_cache(cache, _metadata(), _jwks_with_kids("key-001"))
    policy = OidcPolicy(verifier=verifier, audience=AUDIENCE, jwks_cache=cache)

    result = await policy.authenticate(_bearer_with_kid("key-001"))

    assert result.require("sub") == "user-1"
    assert cache.fetch_calls == []


@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_CACHE_MISS_01_authenticate_triggers_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bearer with uncached kid → triggers _fetch_jwks once."""
    _patch_verifier_decode(monkeypatch)
    _patch_discover(monkeypatch)
    verifier = JwtVerifier(_metadata())
    cache = _StubbedJwksCache(jwks_responses=[_jwks_with_kids("key-001")])
    policy = OidcPolicy(verifier=verifier, audience=AUDIENCE, jwks_cache=cache)

    result = await policy.authenticate(_bearer_with_kid("key-001"))

    assert result.require("sub") == "user-1"
    assert cache.fetch_calls == [JWKS_URI]


@pytest.mark.no_waiver
@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_ROTATION_INVARIANT_01_rotated_key_resolves_via_invalidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rotated signing key (new kid) → invalidate + refetch surfaces it."""
    _patch_verifier_decode(monkeypatch)
    _patch_discover(monkeypatch)
    verifier = JwtVerifier(_metadata())
    cache = _StubbedJwksCache(jwks_responses=[_jwks_with_kids("key-001", "key-rotated")])
    _prepopulate_cache(cache, _metadata(), _jwks_with_kids("key-001"))
    policy = OidcPolicy(verifier=verifier, audience=AUDIENCE, jwks_cache=cache)

    result = await policy.authenticate(_bearer_with_kid("key-rotated"))

    assert result.require("sub") == "user-1"
    # First get_or_fetch served from prepopulated cache (no fetch).
    # _find_key miss triggers invalidate → 1 fetch returning rotated jwks.
    assert cache.fetch_calls == [JWKS_URI]


@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_FETCH_FAIL_RAISES_01_no_static_key_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """JWKS HTTP endpoint failure → typed AuthenticationError; no static-key fallback."""
    _patch_verifier_decode(monkeypatch)
    _patch_discover(monkeypatch)
    verifier = JwtVerifier(_metadata())
    cache = _StubbedJwksCache(fetch_raises=httpx.HTTPError("jwks endpoint 500"))
    policy = OidcPolicy(verifier=verifier, audience=AUDIENCE, jwks_cache=cache)

    with pytest.raises(AuthenticationError):
        await policy.authenticate(_bearer_with_kid("key-001"))


@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_CONCURRENT_REFETCH_01_asyncio_lock_serializes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two concurrent authenticate calls needing JWKS refresh → exactly 1 _fetch_jwks."""
    _patch_verifier_decode(monkeypatch)
    _patch_discover(monkeypatch)
    verifier = JwtVerifier(_metadata())
    cache = _StubbedJwksCache(
        jwks_responses=[_jwks_with_kids("key-001")],
        fetch_sleep_seconds=0.05,
    )
    policy = OidcPolicy(verifier=verifier, audience=AUDIENCE, jwks_cache=cache)

    results = await asyncio.gather(
        policy.authenticate(_bearer_with_kid("key-001")),
        policy.authenticate(_bearer_with_kid("key-001")),
    )

    assert all(r.require("sub") == "user-1" for r in results)
    assert len(cache.fetch_calls) == 1, (
        f"asyncio.Lock should serialize; observed fetches: {cache.fetch_calls}"
    )


@pytest.mark.asyncio
async def test_M_T_AUTH_JWKS_TTL_EXPIRY_01_refresh_past_ttl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cache entry past TTL → next get_or_fetch triggers _refresh + _fetch_jwks."""
    _patch_verifier_decode(monkeypatch)
    _patch_discover(monkeypatch)
    verifier = JwtVerifier(_metadata())
    cache = _StubbedJwksCache(
        jwks_responses=[_jwks_with_kids("key-001")],
        ttl_seconds=10,
    )
    # Pre-populate with stale fetched_at (20 seconds in the past per monotonic clock).
    stale_time = time.monotonic() - 30
    _prepopulate_cache(cache, _metadata(), _jwks_with_kids("key-old"), fetched_at=stale_time)
    policy = OidcPolicy(verifier=verifier, audience=AUDIENCE, jwks_cache=cache)

    result = await policy.authenticate(_bearer_with_kid("key-001"))

    assert result.require("sub") == "user-1"
    assert cache.fetch_calls == [JWKS_URI]


# ─── Stage 14 AUDIENCE bundle (2 MAC-Ts; NO @no_waiver per Murat lock) ────


@pytest.mark.asyncio
async def test_M_T_AUTH_AUDIENCE_SINGLE_DECODE_INVARIANT_01_decode_called_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One authenticate() invocation → exactly one verifier.decode() call
    (audience validation single-sited at JwtVerifier.decode)."""
    decode_calls = _patch_verifier_decode(monkeypatch)
    verifier = JwtVerifier(_metadata())
    cache = _StubbedJwksCache()
    _prepopulate_cache(cache, _metadata(), _jwks_with_kids("key-001"))
    policy = OidcPolicy(verifier=verifier, audience=AUDIENCE, jwks_cache=cache)

    await policy.authenticate(_bearer_with_kid("key-001"))

    assert len(decode_calls) == 1


@pytest.mark.asyncio
async def test_M_T_AUTH_AUDIENCE_CRAFTED_TOKEN_REJECT_01_mismatched_aud_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bearer with audience claim != configured audience → AuthenticationError."""
    _patch_verifier_decode(monkeypatch, audience_check=True)
    verifier = JwtVerifier(_metadata())
    cache = _StubbedJwksCache()
    _prepopulate_cache(cache, _metadata(), _jwks_with_kids("key-001"))
    policy = OidcPolicy(verifier=verifier, audience=AUDIENCE, jwks_cache=cache)

    crafted_bearer = _bearer_with_kid("key-001", audience="https://attacker.example/api")

    with pytest.raises(AuthenticationError, match="audience mismatch"):
        await policy.authenticate(crafted_bearer)
