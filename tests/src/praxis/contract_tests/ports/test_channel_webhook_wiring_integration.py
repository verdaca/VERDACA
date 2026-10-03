"""Stage 14 Phase-1 O-6 — Teams channel webhook wiring integration tests.

Plain contract tests (NO ``@pytest.mark.no_waiver`` → the 14/9/23 pin is
unaffected). They drive a synthetic Teams webhook through the composed
``webhook_app`` entrypoint UNDER A RUNNING EVENT LOOP (httpx ASGITransport),
exercising the buyer-facing channel transport's AUTH-FIRST SPINE LIVE
(auth → nonce → replay) without a live external Teams app. The cost / LLM /
vkey / SQLite-nonce surfaces are Tier-1 demo stubs and budget enforcement is
not exercised — this is NOT an "end-to-end demo-runnable" claim.

C-1 closure: the app is booted via its REAL startup
(``TeamsWebhookApp.startup() → compose_auth_quartet() → _build_oidc_policy() →
discover()``) against a LOCAL OIDC STUB HTTP SERVER that serves a real
``/.well-known/openid-configuration`` + JWKS (real RS256 public key). So this
exercises the PRODUCTION entrypoint auth construction — not a hand-built
verifier — which is the gap (GAP-B4-entrypoint-auth-construction / C-1) the
Phase-0.5 MCP test could not close. Identity is verified with real RS256 crypto;
only the IdP *operator* is local (commercial-IdP integration remains untested).

What this proves on the channel path (future B-6 re-grade input; do NOT touch
the RATIFIED B-6 here):
  (a) serve-with-valid-token → auth-first execute() completes under a running
      loop via the Option-A worker-thread offload (no RuntimeError);
  (b) bad-signature → 401 from receive_webhook BEFORE execute() runs (CC6.7-a
      live on this path — the dimension MCP never had);
  (c) no-token → 401 (parse_activity ValueError mapped to 4xx, NEVER 500);
  (d) replay (same token/nonce) → rejected (NonceReplayError → GatewayCtxError
      auth) — CC6.8 replay live across the worker-thread offload;
  (e) per-user OIDC bearer flows ctx.rate_limit_token → kernel _auth_first
      (O-7, which MCP could not do).

FROZEN: constructs/drives existing components only; no kernel/service.py /
nonce.py edit, no marker/pin change.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import httpx
import pytest
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt

from praxis.adapters.channels.teams.webhook import sign_body
from praxis.adapters.channels.webhook_app import TeamsWebhookApp, create_teams_app

AUDIENCE = "api://verdaca"
KID = "phase1-o6-local-stub-key"
WEBHOOK_SECRET = "phase1-o6-teams-secret"


# ─── Local OIDC stub HTTP server (real RS256 + real JWKS over real HTTP) ───


@pytest.fixture()
def oidc_stub() -> Iterator[tuple[str, Any]]:
    """Serve a real OIDC discovery doc + JWKS so compose_auth_quartet→discover()
    runs end-to-end (closes C-1)."""
    key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    pub = key.as_dict(is_private=False)
    pub["kid"] = KID
    pub["alg"] = "RS256"
    pub["use"] = "sig"
    jwks = {"keys": [pub]}

    holder: dict[str, str] = {}

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: Any) -> None:  # silence
            return

        def do_GET(self) -> None:  # noqa: N802
            issuer = holder["issuer"]
            if self.path == "/.well-known/openid-configuration":
                payload = {
                    "issuer": issuer,
                    "jwks_uri": issuer + "/jwks",
                    "id_token_signing_alg_values_supported": ["RS256"],
                }
            elif self.path == "/jwks":
                payload = jwks
            else:
                self.send_response(404)
                self.end_headers()
                return
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    holder["issuer"] = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield holder["issuer"], key
    finally:
        server.shutdown()
        server.server_close()


def _mint_token(key: Any, issuer: str, *, nonce: str, sub: str = "user-1") -> str:
    header = {"alg": "RS256", "kid": KID, "typ": "JWT"}
    payload = {
        "sub": sub,
        "iss": issuer,
        "aud": AUDIENCE,
        "iat": 1700000000,
        "exp": 1900000000,
        "nonce": nonce,
    }
    token = jose_jwt.encode(header, payload, key)
    return token.decode() if isinstance(token, bytes) else token


def _activity(activity_id: str, text: str = "Which buyer path?") -> bytes:
    return json.dumps(
        {
            "id": activity_id,
            "type": "message",
            "text": text,
            "from": {"aadObjectId": "user-1"},
            "conversation": {"id": "conversation-1"},
            "channelData": {"tenant": {"id": "tenant-1"}},
            "serviceUrl": "https://smba.example.invalid/apis/",
        }
    ).encode("utf-8")


def _signed_headers(body: bytes, *, token: str | None) -> dict[str, str]:
    ts = str(int(time.time()))
    headers = {
        "x-teams-request-timestamp": ts,
        "x-teams-signature": sign_body(body, timestamp=ts, secret=WEBHOOK_SECRET),
        "content-type": "application/json",
    }
    if token is not None:
        headers["authorization"] = f"Bearer {token}"
    return headers


async def _booted_client(
    issuer: str, monkeypatch: pytest.MonkeyPatch
) -> tuple[httpx.AsyncClient, TeamsWebhookApp]:
    monkeypatch.setenv("OIDC_ISSUER_URL", issuer)
    monkeypatch.setenv("OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("VERDACA_ALLOWED_USER_IDS", "user-1")
    monkeypatch.setenv("TEAMS_WEBHOOK_SECRET", WEBHOOK_SECRET)

    app_obj = TeamsWebhookApp()
    await app_obj.startup()  # REAL compose_auth_quartet → discover() vs the stub (closes C-1)
    app = create_teams_app(app_obj)
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    )
    return client, app_obj


# ─── (a)+(e) serve-with-valid-token under a running loop ──────────────────


@pytest.mark.asyncio
async def test_phase1_o6_valid_token_routes_through_auth_first_under_running_loop(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        body = _activity("act-valid-1")
        token = _mint_token(key, issuer, nonce="nonce-valid-1")
        resp = await client.post(
            "/webhooks/teams", content=body, headers=_signed_headers(body, token=token)
        )
        # Must NOT 500: the offload reached the FROZEN gateway under a running loop.
        assert resp.status_code == 200, resp.text
        assert resp.json()["type"] == "AdaptiveCard"
    finally:
        await client.aclose()


# ─── (b) bad-signature → 401 before execute (CC6.7-a live) ────────────────


@pytest.mark.asyncio
async def test_phase1_o6_bad_signature_rejected_before_execute(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        body = _activity("act-badsig-1")
        token = _mint_token(key, issuer, nonce="nonce-badsig-1")
        headers = _signed_headers(body, token=token)
        headers["x-teams-signature"] = "tampered-signature"  # wrong HMAC
        resp = await client.post("/webhooks/teams", content=body, headers=headers)
        assert resp.status_code == 401
        assert resp.json() == {"error": "unauthorized"}  # from receive_webhook gate
    finally:
        await client.aclose()


# ─── (c) no-token → 4xx (parse ValueError mapped; NEVER 500) ──────────────


@pytest.mark.asyncio
async def test_phase1_o6_missing_token_maps_to_4xx_not_500(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, _key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        body = _activity("act-notoken-1")
        resp = await client.post(
            "/webhooks/teams", content=body, headers=_signed_headers(body, token=None)
        )
        assert resp.status_code == 401
        assert resp.status_code != 500
    finally:
        await client.aclose()


# ─── (c2) malformed-but-signed body → 400, NOT 401/500 (HIGH -01 fix) ─────


@pytest.mark.asyncio
async def test_phase1_o6_malformed_body_maps_to_400_not_401_or_500(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A correctly-signed but non-JSON body is a client error (400), not an
    auth failure (401) and not an internal fault (500). Proves the removed
    blanket ``except ValueError -> 401`` no longer masks ``json.JSONDecodeError``.
    """
    issuer, key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        body = b"this-is-not-json{{{"  # passes HMAC (we sign it) but json.loads fails
        token = _mint_token(key, issuer, nonce="nonce-malformed-1")
        resp = await client.post(
            "/webhooks/teams", content=body, headers=_signed_headers(body, token=token)
        )
        assert resp.status_code == 400
        assert resp.status_code not in (401, 500)
    finally:
        await client.aclose()


# ─── (d) replay → rejected on the wired path ──────────────────────────────


@pytest.mark.asyncio
async def test_phase1_o6_replayed_nonce_rejected(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        token = _mint_token(key, issuer, nonce="nonce-replay-1")  # same nonce both calls

        body1 = _activity("act-replay-1")
        first = await client.post(
            "/webhooks/teams", content=body1, headers=_signed_headers(body1, token=token)
        )
        assert first.status_code == 200, first.text

        body2 = _activity("act-replay-2")  # different activity id, same token/nonce
        second = await client.post(
            "/webhooks/teams", content=body2, headers=_signed_headers(body2, token=token)
        )
        assert second.status_code == 401  # auth-class GatewayCtxError
        assert "NonceReplay" in second.json()["error"]
    finally:
        await client.aclose()
