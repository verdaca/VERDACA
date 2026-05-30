"""Channel webhook ASGI entrypoint — Teams + Slack on ONE composed gateway.

Stands up the buyer-facing transport with the AUTH-FIRST SPINE LIVE: composes a
single real authenticated gateway (Phase-0.5 `build_runtime_gateway`) and serves
inbound Teams AND Slack webhooks on the SAME gateway instance, driving the
FROZEN `execute()` spine via the Option-A worker-thread offload.

Two routes, one gateway, one lock:
  - POST /webhooks/teams — Teams Activity, HMAC-SHA256 (`x-teams-signature`).
  - POST /webhooks/slack — Slack event, `v0` scheme (`x-slack-signature`);
    the `url_verification` challenge is echoed inline by Slack's
    `receive_webhook` (after the signature check, before dispatch).
Both routes share the ONE `_exec_lock` — the gateway holds frozen loop-bound
`asyncio.Lock`s, so a second lock would re-open O-11 (see below).

Scope of this demo-branch transport (precise — NOT "end-to-end demo-runnable"):
  - LIVE spine: inbound signature verify (CC6.7-a) → per-user OIDC ingress (O-7)
    → real RS256/JWKS verification → nonce replay (CC6.8). I.e. the
    auth → nonce → budget-gate → replay spine executes for real.
  - Tier-1 DEMO STUBS (dev/test) or REAL adapters (production profile) per
    `build_runtime_gateway`'s profile gate; budget ENFORCEMENT wired but not
    exercised on the demo path.
  - F-14-H1-SLACK-NOT-YET-WIRED-OVERCLAIM-01: RESOLVED-BY-WIRING — Slack is now
    served; the runbook §4/§8 caveat flips at H#9.

────────────────────────────────────────────────────────────────────────────
O-11 — CONCURRENCY SEAM (load-bearing; serialized here)
────────────────────────────────────────────────────────────────────────────
The Option-A bridge offloads each request to an anyio worker thread that runs
the FROZEN `service._run_auth_first → asyncio.run(...)` — i.e. a FRESH event
loop per request. The gateway holds loop-bound `asyncio.Lock`s
(`InMemoryNonceStore._lock`, `JwksCache._lock`). Under CONCURRENT offloads an
uncontended acquire is fine (fast path skips the loop check), but a CONTENDED
acquire across two distinct per-request loops raises
`RuntimeError: Lock is bound to a different event loop` (proven empirically).

Mitigation (adapter-layer; FROZEN untouched): serialize gateway execution with
ONE server-loop `anyio.Lock` shared across BOTH routes so offloads never
overlap → the frozen locks are only ever acquired uncontended, and cross-request
replay detection is preserved (shared store, serialized access). Cost:
throughput = 1 in-flight gateway execution — acceptable for a Champion demo,
flagged for production (O-11 persistent-loop fix deferred to Stage-14.x).

FROZEN: this module only constructs/calls existing components — no change to
`service.py`, `nonce.py`, the auth path, `build_gateway`, the channel adapters'
signatures, the no_waiver markers, or the 14/9/23 pin.
"""

from __future__ import annotations

import functools
import json
import logging
from collections.abc import Callable, Mapping
from typing import Any

import anyio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from praxis.adapters.channels.slack.adapter import SlackAdapter
from praxis.adapters.channels.slack.events import parse_event
from praxis.adapters.channels.slack.webhook import ConfigurationError as SlackConfigError
from praxis.adapters.channels.slack.webhook import (
    load_signing_secret,
)
from praxis.adapters.channels.slack.webhook import (
    receive_webhook as slack_receive_webhook,
)
from praxis.adapters.channels.teams.adapter import TeamsAdapter
from praxis.adapters.channels.teams.events import parse_activity
from praxis.adapters.channels.teams.webhook import (
    WebhookResponse,
    load_webhook_secret,
    receive_webhook,
)
from praxis.composition.runtime_gateway import (
    build_runtime_gateway,
    compose_auth_quartet,
)
from praxis.kernel.gateway.policy import policy_health_check
from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_errors import GatewayCtxError

_LOGGER = logging.getLogger(__name__)
_TEAMS_WEBHOOK_PATH = "/webhooks/teams"
_SLACK_WEBHOOK_PATH = "/webhooks/slack"

# Type of the per-channel event parser (parse_activity / parse_event).
_ParseFn = Callable[..., Any]
# Type of the per-channel inbound receiver (teams/slack receive_webhook).
_ReceiveFn = Callable[..., WebhookResponse]
# Type of the per-channel result renderer (adaptive card / Block Kit).
_RenderFn = Callable[[Any], Mapping[str, Any]]


class AuthRequiredError(Exception):
    """Channel-ingress auth failure (missing/invalid bearer at the event parse).

    The event parsers (`parse_activity` / `parse_event`) raise a bare
    `ValueError` for a missing bearer / required claims. The adapter wraps that
    at the call site into this typed error so the handler maps it to 401 WITHOUT
    a blanket `except ValueError` that would also swallow malformed-body or
    internal `ValueError`s (the HIGH `-01` mismap). Deliberately NOT a
    `ValueError` subclass so the JSONDecodeError/UnicodeDecodeError (400) and
    propagate-to-500 branches stay disjoint. Parser internals untouched
    (PARSE-ACTIVITY named debt stays active → merge-gate).
    """


def _ctx_status(exc: GatewayCtxError) -> int:
    """Map a GatewayCtxError to a 4xx (never 500)."""
    field = getattr(exc, "context_field", "") or ""
    if field.startswith("auth"):
        return 401
    if field.startswith("policy"):
        return 403
    if field.startswith("budget"):
        return 402
    return 400


def _maybe_load_slack_secret() -> str | None:
    """Slack secret is CONDITIONAL — a deployment may serve Teams-only. Return
    None when SLACK_SIGNING_SECRET is unset (the /webhooks/slack route then
    503s) rather than failing the boot of a Teams-only deployment."""
    try:
        return load_signing_secret()  # env SLACK_SIGNING_SECRET
    except SlackConfigError:
        return None


class WebhookApp:
    """Composes ONE runtime gateway and serves inbound Teams and/or Slack webhooks.

    One gateway + one server-loop ``_exec_lock`` are SHARED across both routes
    (a second lock would re-open O-11). Each channel brings its own inbound
    signature scheme, secret, event parser, and result renderer.
    """

    def __init__(self) -> None:
        self._gateway: GatewayPort | None = None
        # D-O6-5: no outbound post on this demo path (the _dispatch_post_result
        # seam would block the worker thread under the offload).
        self._teams_adapter = TeamsAdapter(post_results=False)
        self._slack_adapter = SlackAdapter(post_results=False)
        # `_secret` is the Teams secret (name preserved for the O-11 test which
        # seeds it directly); `_slack_secret` is conditional (None ⇒ 503).
        self._secret: str | None = None
        self._slack_secret: str | None = None
        # O-11: ONE server-loop serialization lock, shared by both routes.
        # Created lazily so it binds to the server's running loop.
        self._exec_lock: anyio.Lock | None = None

    @property
    def is_ready(self) -> bool:
        return self._gateway is not None

    async def startup(self) -> None:
        """Compose the ONE gateway via the REAL Phase-0.5 construction path.

        `compose_auth_quartet()` runs `_build_oidc_policy()→discover()` (a real
        httpx fetch of the issuer's discovery doc + JWKS) — exercising the
        production entrypoint auth construction (closes finding C-1 on the
        channel path).
        """
        jwt_verifier, oidc_policy = await compose_auth_quartet()
        gateway, policy = build_runtime_gateway(
            jwt_verifier=jwt_verifier, oidc_policy=oidc_policy
        )
        # STEP-3 parity with the MCP entrypoint: prod posture fail-closed.
        policy_health_check(policy=policy)
        self._secret = load_webhook_secret()  # env TEAMS_WEBHOOK_SECRET (fail-closed)
        self._slack_secret = _maybe_load_slack_secret()  # conditional
        self._exec_lock = anyio.Lock()
        self._gateway = gateway

    async def _handle(
        self,
        request: Request,
        *,
        secret: str | None,
        receive: _ReceiveFn,
        parse: _ParseFn,
        adapter: Any,
        render: _RenderFn,
    ) -> Response:
        """Shared per-channel handler: signature-verify + offload + auth-first
        execute under the SHARED _exec_lock, with the common error taxonomy."""
        if self._gateway is None or secret is None or self._exec_lock is None:
            return JSONResponse({"error": "gateway not initialized"}, status_code=503)

        body = await request.body()
        headers = {k.lower(): v for k, v in request.headers.items()}
        auth_header = headers.get("authorization")
        gateway = self._gateway

        def _dispatch(payload: Mapping[str, Any], verifier: Any) -> WebhookResponse:
            # Runs on the worker thread (called by receive). The parser stores
            # the per-request bearer in ctx.rate_limit_token (O-7 ingress).
            try:
                event = parse(
                    payload, authorization_header=auth_header, verifier=verifier
                )
            except ValueError as exc:
                # Missing bearer / required claims → typed auth error → 401.
                raise AuthRequiredError(str(exc)) from exc
            if event is None:  # non-actionable event (e.g. non-mention) → ignore
                return WebhookResponse(status_code=200, payload={"status": "ignored"})
            result = adapter.execute(event.intent, event.ctx, gateway)
            return WebhookResponse(status_code=200, payload=render(result))

        # O-11: serialize gateway execution on the server loop so per-request
        # offload loops never CONTEND on the gateway's FROZEN loop-bound
        # asyncio.Locks (a contended cross-loop acquire raises RuntimeError —
        # see the module docstring + the committed O-11 proof test). ONE lock
        # for BOTH routes.
        async with self._exec_lock:
            try:
                response = await anyio.to_thread.run_sync(
                    functools.partial(
                        receive,
                        body,
                        headers,
                        secret=secret,
                        verifier=gateway.jwt_verifier,
                        dispatch=_dispatch,
                    )
                )
            except GatewayCtxError as exc:
                # auth / nonce / budget / policy failures from execute() → 4xx.
                return JSONResponse(
                    {"error": exc.context_field}, status_code=_ctx_status(exc)
                )
            except AuthRequiredError as exc:
                # Missing/invalid bearer at channel ingress → 401.
                return JSONResponse({"error": str(exc)}, status_code=401)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                # Malformed (but correctly-signed) body is a client error → 400.
                return JSONResponse({"error": str(exc)}, status_code=400)
            # Any other ValueError is an internal fault and is deliberately NOT
            # caught here: it propagates to a 500 (HIGH -01 fix).

        return JSONResponse(dict(response.payload), status_code=response.status_code)

    async def handle(self, request: Request) -> Response:
        """POST /webhooks/teams. ``receive_webhook`` is the module-global Teams
        receiver (resolved at call time so the O-11 test can monkeypatch it)."""
        return await self._handle(
            request,
            secret=self._secret,
            receive=receive_webhook,
            parse=parse_activity,
            adapter=self._teams_adapter,
            render=self._teams_adapter.result_to_adaptive_card,
        )

    async def handle_slack(self, request: Request) -> Response:
        """POST /webhooks/slack. Slack's receiver echoes the url_verification
        challenge inline (200, before dispatch); the rest mirrors Teams."""
        return await self._handle(
            request,
            secret=self._slack_secret,
            receive=slack_receive_webhook,
            parse=parse_event,
            adapter=self._slack_adapter,
            render=self._slack_adapter.result_to_block_kit,
        )


# Backward-compatible alias: the app composes one gateway and (via
# create_teams_app) can still serve Teams alone.
TeamsWebhookApp = WebhookApp


def _lifespan_factory(obj: WebhookApp):
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(_app: Starlette):
        # Production boot path: composes the gateway on startup when no ready
        # object was injected. Covered by the lifespan/boot test.
        if not obj.is_ready:
            await obj.startup()
        yield

    return lifespan


def create_teams_app(app_obj: WebhookApp | None = None) -> Starlette:
    """Build a Starlette app exposing POST /webhooks/teams ONLY (Teams-only
    deployment / backward compatibility). Use ``create_webhook_app`` to serve
    both channels on one gateway."""
    obj = app_obj or WebhookApp()
    return Starlette(
        routes=[Route(_TEAMS_WEBHOOK_PATH, obj.handle, methods=["POST"])],
        lifespan=_lifespan_factory(obj),
    )


def create_webhook_app(app_obj: WebhookApp | None = None) -> Starlette:
    """Build a Starlette app exposing BOTH POST /webhooks/teams and
    POST /webhooks/slack on ONE composed gateway (the same WebhookApp instance,
    one shared _exec_lock). Tests may pass a pre-booted object in."""
    obj = app_obj or WebhookApp()
    return Starlette(
        routes=[
            Route(_TEAMS_WEBHOOK_PATH, obj.handle, methods=["POST"]),
            Route(_SLACK_WEBHOOK_PATH, obj.handle_slack, methods=["POST"]),
        ],
        lifespan=_lifespan_factory(obj),
    )


__all__ = [
    "AuthRequiredError",
    "TeamsWebhookApp",
    "WebhookApp",
    "create_teams_app",
    "create_webhook_app",
]
