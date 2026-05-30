"""Teams channel webhook ASGI entrypoint (Stage 14 Phase-0.6 O-6 salvage).

Stands up the Teams buyer-facing transport with the AUTH-FIRST SPINE LIVE:
composes a real authenticated gateway (Phase-0.5 `build_runtime_gateway`) and
serves inbound Teams webhooks, driving the FROZEN `execute()` spine via the
Option-A worker-thread offload.

Scope of this demo-branch transport (precise — NOT "end-to-end demo-runnable"):
  - LIVE spine: inbound HMAC (CC6.7-a) → per-user OIDC ingress (O-7) → real
    RS256/JWKS verification → nonce replay (CC6.8). I.e. the
    auth → nonce → budget-gate → replay spine executes for real.
  - Tier-1 DEMO STUBS (NOT exercised): cost meter, LLM proxy, virtual-key
    issuance, SQLite-backed nonce store.
  - Budget ENFORCEMENT is wired into the spine but NOT exercised on this path.
  - This is a salvaged local demo-branch transport (Phase-0.6), NOT a
    production deployment and NOT a chartered Phase-1 deliverable.

What this pays over the MCP transport (Phase-0.5):
  - per-user OIDC auth flows for real: `parse_activity` sets
    `ctx.rate_limit_token = bearer`, which the FROZEN `service._bearer_token`
    consumes → `oidc_policy.authenticate` (this is O-7, unreachable on MCP).
  - inbound webhook HMAC signature verification runs live (CC6.7-a) — a
    dimension MCP never had (`webhook_resolver={}` there).

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
a server-loop `anyio.Lock` so offloads never overlap → the frozen locks are
only ever acquired uncontended (the proven-OK path), and cross-request replay
detection is preserved (shared store, serialized access). Cost: throughput = 1
in-flight gateway execution — acceptable for a Champion demo, flagged for
production. A real-deploy fix (a single persistent gateway event loop, or
thread-confined per-request stores) touches frozen/architectural surface and is
deferred. See B-6 follow-ups.

FROZEN: this module only constructs/calls existing components — no change to
`service.py`, `nonce.py`, the auth path, `build_gateway`, the channel adapters'
signatures, the no_waiver markers, or the 14/9/23 pin.
"""

from __future__ import annotations

import functools
import json
import logging
from collections.abc import Mapping
from typing import Any

import anyio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from praxis.adapters.channels.teams.adapter import TeamsAdapter
from praxis.adapters.channels.teams.events import parse_activity
from praxis.adapters.channels.teams.webhook import (
    WebhookResponse,
    load_webhook_secret,
    receive_webhook,
)
from praxis.adapters.mcp_server.composition import (
    build_runtime_gateway,
    compose_auth_quartet,
)
from praxis.kernel.gateway.policy import policy_health_check
from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_errors import GatewayCtxError

_LOGGER = logging.getLogger(__name__)
_TEAMS_WEBHOOK_PATH = "/webhooks/teams"


class AuthRequiredError(Exception):
    """Channel-ingress auth failure (missing/invalid bearer at `parse_activity`).

    Folds F-14-V1-PARSE-ACTIVITY-BARE-VALUEERROR-02: `parse_activity` raises a
    bare `ValueError` for a missing bearer / required claims. The adapter wraps
    that at the call site into this typed error so `handle()` can map it to a
    401 WITHOUT a blanket `except ValueError` that would also swallow malformed-
    body or internal `ValueError`s (the HIGH `-01` mismap). Deliberately NOT a
    `ValueError` subclass so the JSONDecodeError/UnicodeDecodeError (400) and
    propagate-to-500 branches stay disjoint. `parse_activity` internals are
    untouched (PARSE-ACTIVITY named debt stays active → merge-gate).
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


class TeamsWebhookApp:
    """Composes a runtime gateway and serves the Teams inbound webhook."""

    def __init__(self) -> None:
        self._gateway: GatewayPort | None = None
        # D-O6-5: no outbound post on this demo path (the _dispatch_post_result
        # seam would block the worker thread under the offload). post_results
        # stays False; the live-demo blocking-post is a flagged follow-up.
        self._adapter = TeamsAdapter(post_results=False)
        self._secret: str | None = None
        # O-11: server-loop serialization of gateway execution. Created lazily on
        # first use so it binds to the server's running loop, not construction.
        self._exec_lock: anyio.Lock | None = None

    @property
    def is_ready(self) -> bool:
        return self._gateway is not None

    async def startup(self) -> None:
        """Compose the gateway via the REAL Phase-0.5 construction path.

        `compose_auth_quartet()` runs `_build_oidc_policy()→discover()` (a real
        httpx fetch of the issuer's discovery doc + JWKS). Booting through this
        path — rather than injecting a pre-built verifier — exercises the
        production entrypoint auth construction (closes finding C-1 on the
        channel path).
        """
        jwt_verifier, oidc_policy = await compose_auth_quartet()
        gateway, policy = build_runtime_gateway(
            jwt_verifier=jwt_verifier, oidc_policy=oidc_policy
        )
        # STEP-3 parity with the MCP entrypoint: prod posture fail-closed.
        policy_health_check(policy=policy)
        self._secret = load_webhook_secret()  # env TEAMS_WEBHOOK_SECRET
        self._exec_lock = anyio.Lock()
        self._gateway = gateway

    async def handle(self, request: Request) -> Response:
        if self._gateway is None or self._secret is None or self._exec_lock is None:
            return JSONResponse({"error": "gateway not initialized"}, status_code=503)

        body = await request.body()
        headers = {k.lower(): v for k, v in request.headers.items()}
        auth_header = headers.get("authorization")
        gateway = self._gateway

        def _dispatch(
            activity: Mapping[str, Any], verifier: Any
        ) -> WebhookResponse:
            # Runs on the worker thread (called by receive_webhook). Reads the
            # per-request bearer from the captured HTTP Authorization header;
            # parse_activity stores it in ctx.rate_limit_token (O-7 ingress).
            try:
                event = parse_activity(
                    activity, authorization_header=auth_header, verifier=verifier
                )
            except ValueError as exc:
                # Missing bearer / required claims (parse_activity's bare
                # ValueError) → typed auth error → 401 in handle(). Folds -02;
                # keeps the auth-failure branch disjoint from malformed-body
                # (400) and internal-fault (500).
                raise AuthRequiredError(str(exc)) from exc
            if event is None:  # non-message activity → ignore
                return WebhookResponse(status_code=200, payload={"status": "ignored"})
            result = self._adapter.execute(event.intent, event.ctx, gateway)
            return WebhookResponse(
                status_code=200, payload=self._adapter.result_to_adaptive_card(result)
            )

        # O-11: serialize gateway execution on the server loop so the offloaded
        # per-request asyncio.run() loops never CONTEND on the gateway's FROZEN
        # loop-bound asyncio.Locks (a contended cross-loop acquire raises
        # RuntimeError — see module docstring + the committed O-11 proof test).
        async with self._exec_lock:
            try:
                response = await anyio.to_thread.run_sync(
                    functools.partial(
                        receive_webhook,
                        body,
                        headers,
                        secret=self._secret,
                        verifier=gateway.jwt_verifier,
                        dispatch=_dispatch,
                    )
                )
            except GatewayCtxError as exc:
                # auth / nonce / budget / policy failures from the offloaded
                # execute() → 4xx, never 500.
                return JSONResponse(
                    {"error": exc.context_field}, status_code=_ctx_status(exc)
                )
            except AuthRequiredError as exc:
                # Missing/invalid bearer at channel ingress (typed, from
                # _dispatch wrapping parse_activity) → 401.
                return JSONResponse({"error": str(exc)}, status_code=401)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                # Malformed (but correctly-signed) request body is a client
                # error, NOT an auth failure → 400, never masked as 401/500.
                return JSONResponse({"error": str(exc)}, status_code=400)
            # Any other ValueError is an internal fault and is deliberately NOT
            # caught here: it propagates to a 500 (HIGH -01 fix — do not mask
            # internal faults as 401).

        return JSONResponse(dict(response.payload), status_code=response.status_code)


def create_teams_app(app_obj: TeamsWebhookApp | None = None) -> Starlette:
    """Build the Starlette app exposing POST /webhooks/teams.

    Production: the lifespan runs `startup()` (composes the gateway). Tests may
    instead `await app_obj.startup()` directly (e.g. against a local OIDC stub)
    and pass the ready object in — the lifespan then no-ops.
    """
    obj = app_obj or TeamsWebhookApp()

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(_app: Starlette):
        # Production boot path: composes the gateway on app startup when no
        # ready object was injected. Covered by the lifespan/boot test (-03 fold)
        # — the prod-only `# pragma: no cover` is removed now that it is exercised.
        if not obj.is_ready:
            await obj.startup()
        yield

    return Starlette(
        routes=[Route(_TEAMS_WEBHOOK_PATH, obj.handle, methods=["POST"])],
        lifespan=lifespan,
    )


__all__ = ["AuthRequiredError", "TeamsWebhookApp", "create_teams_app"]
