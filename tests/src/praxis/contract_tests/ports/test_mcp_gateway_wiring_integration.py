"""Stage 14 Phase-0.5 — MCP gateway-wiring integration tests.

Plain contract tests (NO ``@pytest.mark.no_waiver`` → the 14/9/23 pin is
unaffected). These run UNDER A RUNNING EVENT LOOP to replicate FastMCP's
sync-tool dispatch on the loop thread (``func_metadata.py:95``) — the exact
condition the existing *synchronous* composition-root test cannot reproduce,
which is why the O-3/Risk-1 bug ("RuntimeError before execute() is reached")
went undetected until Phase-0.5.

What these prove:
  (a) the Option A bridge — ``anyio.to_thread.run_sync(gateway.execute, …)`` —
      does NOT RuntimeError under a running loop (the frozen
      ``service.py:_run_auth_first`` ``asyncio.run`` guard fires on the worker
      thread, as designed);
  (b) reject-without-token → GatewayCtxError(context_field startswith "auth");
  (c) a per-user OIDC dev token (real RS256, verified against a local OIDC stub
      with a real JWKS) flows through to the auth quartet — the VERIFIED
      per-user identity reaches ``_auth_first`` and execute() completes;
  (d) replay of a seen nonce is rejected (NonceReplayError) on the in-memory
      store (O-9 Option A — CC6.8-a/b/d run live);
  (e) policy_health_check(policy=...) fails closed at production posture when
      virtual_keys is None (STEP 3 / CC6.1-e / CC7.1-b);
  (f) O-7 RESOLUTION: the MCP ``build_channel_context`` produces a
      ChannelContext whose ``rate_limit_token`` is None, so the MCP tool
      closure path carries NO bearer — per-user OIDC auth cannot flow through
      the MCP transport (verdict (b): rate_limit_token IS the auth-identity
      carrier, not a separate rate-limit field).

D-2 honesty line: auth is exercised against a LOCAL OIDC stub (real RS256 +
real JWKS/kid lookup). Commercial-IdP (Entra/Okta/Auth0) integration is
config-only and untested here.

FROZEN: these tests construct and drive existing kernel classes only; no
kernel/service.py/nonce.py edit, no marker/pin change.
"""

from __future__ import annotations

import time
from typing import Any

import anyio
import pytest
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt

from praxis.adapters.mcp_server.composition import build_runtime_gateway
from praxis.adapters.mcp_server.tools import build_channel_context
from praxis.kernel.auth import OidcPolicy
from praxis.kernel.auth.jwt import JwtVerifier
from praxis.kernel.auth.oidc import JwksCache, OidcMetadata, _CacheEntry
from praxis.kernel.gateway.policy import (
    GatewayPolicy,
    OperationalMisconfigurationError,
    policy_health_check,
)
from praxis.ports.gateway_dto import (
    AuthClaims,
    CallerKind,
    ChannelContext,
    ChannelKind,
    StartAnalysisRequest,
)
from praxis.ports.gateway_errors import GatewayCtxError

ISSUER = "https://issuer.local.invalid"
AUDIENCE = "api://verdaca"
KID = "phase05-local-stub-key"


# ─── Local OIDC stub: real RS256 keypair + real JWKS ──────────────────────


def _local_oidc(monkeypatch: pytest.MonkeyPatch) -> tuple[JwtVerifier, OidcPolicy, Any]:
    """Build a real verifier + OidcPolicy backed by a local in-memory JWKS.

    Real RS256 crypto, real JwksCache.get_key kid-lookup; only the IdP
    *operator* is local (no network). Mirrors the cassette pattern in
    test_oidc_policy_construction.py.
    """
    key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    pub = key.as_dict(is_private=False)
    pub["kid"] = KID
    pub["alg"] = "RS256"
    pub["use"] = "sig"
    metadata = OidcMetadata(
        issuer=ISSUER,
        jwks_uri=ISSUER + "/keys",
        id_token_signing_alg_values_supported=("RS256",),
    )
    verifier = JwtVerifier(metadata)
    cache = JwksCache()
    # Pre-populate the cache so get_key resolves the kid without a network fetch.
    cache._store[ISSUER] = _CacheEntry(  # noqa: SLF001 — test seeds real cache entry
        metadata=metadata,
        jwks={"keys": [pub]},
        fetched_at=time.monotonic(),
    )
    oidc_policy = OidcPolicy(verifier=verifier, audience=AUDIENCE, jwks_cache=cache)
    return verifier, oidc_policy, key


def _mint_token(key: Any, *, nonce: str, sub: str = "user-1", audience: str = AUDIENCE) -> str:
    header = {"alg": "RS256", "kid": KID, "typ": "JWT"}
    payload = {
        "sub": sub,
        "iss": ISSUER,
        "aud": audience,
        "iat": 1700000000,
        "exp": 1900000000,
        "nonce": nonce,
    }
    token = jose_jwt.encode(header, payload, key)
    return token.decode() if isinstance(token, bytes) else token


def _compose(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> tuple[Any, GatewayPolicy, Any]:
    monkeypatch.setenv("OIDC_ISSUER_URL", ISSUER)
    monkeypatch.setenv("OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("VERDACA_ALLOWED_USER_IDS", "user-1")
    monkeypatch.setenv("VERDACA_SESSION_INDEX_DB", str(tmp_path / "sidx.sqlite3"))
    verifier, oidc_policy, key = _local_oidc(monkeypatch)
    gateway, policy = build_runtime_gateway(jwt_verifier=verifier, oidc_policy=oidc_policy)
    return gateway, policy, key


def _ctx(*, request_id: str, token: str | None) -> ChannelContext:
    return ChannelContext(
        caller_id="user-1",
        caller_kind=CallerKind.HUMAN,
        auth_claims=AuthClaims(_claims={"sub": "user-1"}),
        channel=ChannelKind.CLAUDE_DESKTOP,
        channel_session_id="session-1",
        request_id=request_id,
        rate_limit_token=token,
    )


def _intent(idempotency_key: str) -> StartAnalysisRequest:
    return StartAnalysisRequest(
        question="Which buyer path?",
        requester_user_id="user-1",
        workspace_id="ws-1",
        idempotency_key=idempotency_key,
    )


# ─── (a)+(c) per-user token flows through the spine under a running loop ──


@pytest.mark.asyncio
async def test_phase05_valid_dev_token_routes_through_auth_first_under_running_loop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """A real per-user RS256 token presented under a RUNNING loop traverses the
    auth quartet via the Option A offload and execute() completes — the frozen
    asyncio.run guard fires on the worker thread (no RuntimeError)."""
    gateway, policy, key = _compose(monkeypatch, tmp_path)
    token = _mint_token(key, nonce="nonce-valid-1")

    # Sanity: we ARE under a running loop (replicates FastMCP dispatch).
    import asyncio

    assert asyncio.get_running_loop() is not None

    result = await anyio.to_thread.run_sync(
        gateway.execute, _intent("idem-valid-1"), _ctx(request_id="r1", token=token)
    )

    assert result.session.status == "completed"
    # The VERIFIED per-user subject reached the budget gate (vkey stub records
    # the authenticated principal's sub) — proves identity flowed into _auth_first.
    assert policy.virtual_keys.checked == ["user-1"]


# ─── (b) reject-without-token ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_phase05_reject_without_token_raises_auth_ctx_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """No bearer on the context → GatewayCtxError at the auth step, before any
    downstream work."""
    gateway, _policy, _key = _compose(monkeypatch, tmp_path)

    with pytest.raises(GatewayCtxError) as exc_info:
        await anyio.to_thread.run_sync(
            gateway.execute, _intent("idem-missing"), _ctx(request_id="r2", token=None)
        )

    assert exc_info.value.context_field.startswith("auth")


# ─── (d) replay rejected on the in-memory store (O-9 CC6.8-a/b/d live) ────


@pytest.mark.asyncio
async def test_phase05_replayed_nonce_rejected_on_inmemory_store(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """First presentation completes; replaying the same nonce is rejected —
    NonceReplayError surfaces through the GatewayCtxError auth wrap. CC6.8
    replay rejection runs LIVE across worker threads on InMemoryNonceStore."""
    gateway, _policy, key = _compose(monkeypatch, tmp_path)
    token = _mint_token(key, nonce="nonce-replay-1")

    first = await anyio.to_thread.run_sync(
        gateway.execute, _intent("idem-replay-1"), _ctx(request_id="r3", token=token)
    )
    assert first.session.status == "completed"

    with pytest.raises(GatewayCtxError) as exc_info:
        await anyio.to_thread.run_sync(
            gateway.execute, _intent("idem-replay-2"), _ctx(request_id="r4", token=token)
        )

    assert exc_info.value.context_field.startswith("auth")
    assert "NonceReplay" in exc_info.value.context_field


# ─── (e) policy_health_check prod fail-closed (STEP 3 / CC6.1-e, CC7.1-b) ─


def test_phase05_policy_health_check_prod_fail_closed_without_vkey(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """At production posture, a policy with virtual_keys=None makes the
    entrypoint's policy_health_check(policy=...) raise — production cannot
    start unkeyed (the STEP 3 wiring closes F2/CC7.1-b/CC6.1-e)."""
    monkeypatch.setenv("VERDACA_GATEWAY_BEARER_TOKEN", "isolate-vkey-check")
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")

    policy = GatewayPolicy()  # virtual_keys defaults to None

    with pytest.raises(OperationalMisconfigurationError, match="virtual_keys is None"):
        policy_health_check(policy=policy)


# ─── (f) O-7 resolution: MCP closure path carries NO bearer ───────────────


def test_phase05_O7_mcp_build_channel_context_has_no_bearer_token() -> None:
    """O-7 verdict (b): rate_limit_token IS the auth-identity carrier (consumed
    by service.py:_bearer_token → oidc_policy.authenticate), and the MCP
    build_channel_context does NOT populate it. So a verdaca_start_analysis
    tool call carries no per-user OIDC bearer — per-user auth cannot flow
    through the MCP transport. (Channels populate it via events.py; MCP does
    not, and the MCP tool signatures expose no bearer/Context parameter.)

    This pins O-7 as a real gap rather than a flag; advisor escalation item.
    """
    ctx = build_channel_context(
        requester_user_id="user-1",
        request_id="req-1",
        channel_session_id="session-1",
    )

    assert ctx.rate_limit_token is None
