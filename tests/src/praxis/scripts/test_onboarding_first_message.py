"""Stage 14 Phase-1 [H#2] — first-message.py onboarding test.

Plain test (NO ``@pytest.mark.no_waiver`` → pin 14/9/23 unaffected). Drives the
onboarding first-message smoke through the REAL composed runtime gateway
(``compose_auth_quartet`` → ``build_runtime_gateway``) against a LOCAL OIDC
stub (real RS256 + JWKS), proving the auth-first traversal:

  (a) a valid token → an ``AnalysisResult`` comes back (bearer →
      OidcPolicy.authenticate → nonce → budget gate → execute → memory →
      LLM-stub all ran);
  (b) the SAME token replayed → the second call raises (nonce replay rejection
      is genuinely in the traversal — the reused nonce is the only difference).

The LLM/cost/memory/vkey/nonce backing are Tier-1 demo stubs wired by
``build_runtime_gateway``; the auth-first spine runs for real. Synchronous test
on purpose: ``gateway.execute`` runs its own ``asyncio.run`` internally, so it
must be called with no running loop.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import ModuleType
from typing import Any, Callable

import pytest
from authlib.jose import JsonWebKey
from authlib.jose import jwt as jose_jwt

from praxis.ports.gateway_dto import AnalysisResult
from praxis.ports.gateway_errors import GatewayCtxError

LoadScript = Callable[[str, str], ModuleType]

AUDIENCE = "api://verdaca"
KID = "phase1-h2-onboarding-stub-key"


@pytest.fixture()
def first_message(load_onboarding_script: LoadScript) -> ModuleType:
    return load_onboarding_script("first-message.py", "onboarding_first_message")


@pytest.fixture()
def oidc_stub() -> Iterator[tuple[str, Any]]:
    """Serve a real OIDC discovery doc + JWKS so compose_auth_quartet→discover()
    runs end-to-end without a commercial IdP."""
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


def _set_env(monkeypatch: pytest.MonkeyPatch, issuer: str) -> None:
    monkeypatch.setenv("OIDC_ISSUER_URL", issuer)
    monkeypatch.setenv("OIDC_AUDIENCE", AUDIENCE)
    monkeypatch.setenv("VERDACA_ALLOWED_USER_IDS", "user-1")


def test_valid_token_traverses_auth_first_spine(
    first_message: ModuleType,
    oidc_stub: tuple[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issuer, key = oidc_stub
    _set_env(monkeypatch, issuer)

    gateway = first_message.compose_from_env()
    token = _mint_token(key, issuer, nonce="onboard-nonce-valid-1")
    intent, ctx = first_message.build_request(
        question="Which buyer path?",
        user_id="user-1",
        workspace_id="tenant-1",
        bearer_token=token,
    )
    outcome = first_message.run_first_message(gateway, intent, ctx)

    assert isinstance(outcome.result, AnalysisResult)
    assert outcome.result.recommendation  # LLM stub produced content end-to-end
    assert outcome.elapsed_ms >= 0.0


def test_replayed_nonce_is_rejected(
    first_message: ModuleType,
    oidc_stub: tuple[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issuer, key = oidc_stub
    _set_env(monkeypatch, issuer)

    gateway = first_message.compose_from_env()
    token = _mint_token(key, issuer, nonce="onboard-nonce-replay-1")

    intent1, ctx1 = first_message.build_request(
        question="first", user_id="user-1", workspace_id="tenant-1", bearer_token=token
    )
    first_outcome = first_message.run_first_message(gateway, intent1, ctx1)
    assert isinstance(first_outcome.result, AnalysisResult)

    # Same token (same nonce), fresh request → replay rejection is in the path.
    # The service wraps NonceReplayError into a GatewayCtxError on the auth leg.
    intent2, ctx2 = first_message.build_request(
        question="second", user_id="user-1", workspace_id="tenant-1", bearer_token=token
    )
    with pytest.raises(GatewayCtxError) as exc_info:
        first_message.run_first_message(gateway, intent2, ctx2)
    assert "NonceReplay" in exc_info.value.context_field


def test_missing_bearer_env_returns_nonzero(
    first_message: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("VERDACA_SMOKE_BEARER", raising=False)
    assert first_message.main([]) == 1
