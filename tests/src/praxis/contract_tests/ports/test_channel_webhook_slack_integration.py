"""Stage 14 Day-2 — Slack webhook_app route integration tests.

Plain contract tests (NO ``@pytest.mark.no_waiver`` → the 14/9/23 pin is
unaffected). They drive a synthetic Slack event through the composed
``webhook_app`` ``POST /webhooks/slack`` route UNDER A RUNNING EVENT LOOP (httpx
ASGITransport), against a LOCAL OIDC STUB (real RS256 + JWKS). The app is built
with ``create_webhook_app`` — ONE composed gateway + ONE ``_exec_lock`` serving
both /webhooks/teams and /webhooks/slack.

What this proves on the Slack path (mirrors the Teams O-6 tests):
  (a) valid v0-signed + valid bearer → 200 + Slack Block Kit; auth-first
      execute() ran under the worker-thread offload;
  (b) bad signature → 401 from receive_webhook BEFORE execute() (v0 live);
  (c) url_verification challenge → 200 echoing the challenge (inline, before
      dispatch — Slack's receive_webhook handles it after the signature check);
  (d) replay (same token/nonce) → 401 (NonceReplayError → GatewayCtxError auth);
  (e) no-token → 401 (parse_event ValueError → AuthRequiredError, never 500);
      malformed-but-signed body → 400 (never 500).

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

from praxis.adapters.channels.slack.webhook import sign_body
from praxis.adapters.channels.webhook_app import WebhookApp, create_webhook_app

AUDIENCE = "api://verdaca"
KID = "day2-slack-local-stub-key"
TEAMS_SECRET = "day2-teams-secret"  # startup loads it fail-closed; set so boot succeeds
SLACK_SECRET = "day2-slack-signing-secret"


# ─── Local OIDC stub (real RS256 + real JWKS over real HTTP) ──────────────


@pytest.fixture()
def oidc_stub() -> Iterator[tuple[str, Any]]:
    key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
    pub = key.as_dict(is_private=False)
    pub["kid"] = KID
    pub["alg"] = "RS256"
    pub["use"] = "sig"
    jwks = {"keys": [pub]}
    holder: dict[str, str] = {}

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: Any) -> None:
            return

        def do_GET(self) -> None:  # noqa: N802
            issuer = holder["issuer"]
            if self.path == "/.well-known/openid-configuration":
                payload: dict[str, Any] = {
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


def _app_mention(ts: str, text: str = "Which buyer path?") -> bytes:
    return json.dumps(
        {
            "type": "event_callback",
            "team_id": "T1",
            "event": {
                "type": "app_mention",
                "user": "user-1",
                "channel": "C1",
                "text": text,
                "ts": ts,
            },
        }
    ).encode("utf-8")


def _signed_headers(body: bytes, *, token: str | None) -> dict[str, str]:
    ts = str(int(time.time()))
    headers = {
        "x-slack-request-timestamp": ts,
        "x-slack-signature": sign_body(body, timestamp=ts, secret=SLACK_SECRET),
        "content-type": "application/json",
    }
    if token is not None:
        headers["authorization"] = f"Bearer {token}"
    return headers


async def _booted_client(
    issuer: str, monkeypatch: pytest.MonkeyPatch
) -> tuple[httpx.AsyncClient, WebhookApp]:
    monkeypatch.setenv("OIDC_ISSUER_URL", issuer)
    monkeypatch.setenv("OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("VERDACA_ALLOWED_USER_IDS", "user-1")
    monkeypatch.setenv("TEAMS_WEBHOOK_SECRET", TEAMS_SECRET)
    monkeypatch.setenv("SLACK_SIGNING_SECRET", SLACK_SECRET)

    app_obj = WebhookApp()
    await app_obj.startup()  # REAL compose_auth_quartet → discover() vs the stub
    app = create_webhook_app(app_obj)  # ONE gateway, both routes
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    )
    return client, app_obj


# ─── (a) valid signed + valid bearer → 200 + Block Kit ────────────────────


@pytest.mark.asyncio
async def test_slack_valid_token_routes_through_auth_first(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        body = _app_mention("1700000000.000100")
        token = _mint_token(key, issuer, nonce="slack-nonce-valid-1")
        resp = await client.post(
            "/webhooks/slack", content=body, headers=_signed_headers(body, token=token)
        )
        assert resp.status_code == 200, resp.text
        assert "blocks" in resp.json()  # Slack Block Kit, not AdaptiveCard
    finally:
        await client.aclose()


# ─── (b) bad signature → 401 before execute ───────────────────────────────


@pytest.mark.asyncio
async def test_slack_bad_signature_rejected_before_execute(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        body = _app_mention("1700000000.000200")
        token = _mint_token(key, issuer, nonce="slack-nonce-badsig-1")
        headers = _signed_headers(body, token=token)
        headers["x-slack-signature"] = "v0=deadbeef"  # wrong v0 digest
        resp = await client.post("/webhooks/slack", content=body, headers=headers)
        assert resp.status_code == 401
        assert resp.json() == {"error": "unauthorized"}
    finally:
        await client.aclose()


# ─── (c) url_verification challenge → 200 echoes challenge (before auth) ───


@pytest.mark.asyncio
async def test_slack_url_verification_challenge_echoed(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, _key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        body = json.dumps(
            {"type": "url_verification", "challenge": "challenge-abc-123"}
        ).encode("utf-8")
        # Signed (v0) but NO bearer — the challenge is echoed before dispatch.
        resp = await client.post(
            "/webhooks/slack", content=body, headers=_signed_headers(body, token=None)
        )
        assert resp.status_code == 200
        assert resp.json() == {"challenge": "challenge-abc-123"}
    finally:
        await client.aclose()


# ─── (d) replay (same nonce) → 401 ────────────────────────────────────────


@pytest.mark.asyncio
async def test_slack_replayed_nonce_rejected(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        token = _mint_token(key, issuer, nonce="slack-nonce-replay-1")

        first = await client.post(
            "/webhooks/slack",
            content=_app_mention("1700000000.000300"),
            headers=_signed_headers(_app_mention("1700000000.000300"), token=token),
        )
        assert first.status_code == 200, first.text

        body2 = _app_mention("1700000000.000400")  # different event, same token/nonce
        second = await client.post(
            "/webhooks/slack", content=body2, headers=_signed_headers(body2, token=token)
        )
        assert second.status_code == 401
        assert "NonceReplay" in second.json()["error"]
    finally:
        await client.aclose()


# ─── (e) no-token → 401 ; malformed-but-signed → 400 (never 500) ──────────


@pytest.mark.asyncio
async def test_slack_missing_token_maps_to_401(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, _key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        body = _app_mention("1700000000.000500")
        resp = await client.post(
            "/webhooks/slack", content=body, headers=_signed_headers(body, token=None)
        )
        assert resp.status_code == 401
        assert resp.status_code != 500
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_slack_malformed_body_maps_to_400_not_500(
    oidc_stub: tuple[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    issuer, key = oidc_stub
    client, _app = await _booted_client(issuer, monkeypatch)
    try:
        body = b"not-json-at-all{{{"  # correctly signed, but not JSON
        token = _mint_token(key, issuer, nonce="slack-nonce-malformed-1")
        resp = await client.post(
            "/webhooks/slack", content=body, headers=_signed_headers(body, token=token)
        )
        assert resp.status_code == 400
        assert resp.status_code not in (401, 500)
    finally:
        await client.aclose()
