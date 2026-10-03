"""Streamable HTTP transport for the Verdaca MCP server.

Stage 14 Phase-0.5: ``main()`` now composes a live authenticated gateway via
``build_runtime_gateway`` (transport-neutral) and threads it into the FastMCP
server, and calls ``policy_health_check(policy=...)`` with the built policy so
the production vkey-REQUIRED fail-closed branch (``policy.py``) can fire at
startup. Prior to this the entrypoint ran ``gateway=None`` (finding O-3) and
``policy_health_check()`` no-args (finding F2), so the auth-first spine was
never reachable and the prod fail-closed never fired.
"""

from __future__ import annotations

import asyncio
import os

from mcp.server.fastmcp import FastMCP

from praxis.adapters.mcp_server.server import create_verdaca_mcp_server
from praxis.composition.runtime_gateway import (
    build_runtime_gateway,
    compose_auth_quartet,
    initialize_runtime_adapters,
)
from praxis.kernel.gateway.policy import policy_health_check, verify_bearer_token
from praxis.ports.gateway import GatewayPort

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 3000


def verify_bearer_authorization(authorization: str | None) -> bool:
    """Return whether E1's policy gate accepts the deployment bearer token."""

    return verify_bearer_token(authorization)


def create_mcp_http_server(*, gateway: GatewayPort | None = None) -> FastMCP:
    """Create a stateless FastMCP server for Streamable HTTP."""

    return create_verdaca_mcp_server(gateway=gateway, stateless_http=True)


def create_mcp_http_app(*, gateway: GatewayPort | None = None) -> object:
    """Return the Streamable HTTP ASGI app exposed at /mcp."""

    return create_mcp_http_server(gateway=gateway).streamable_http_app()


async def serve_http(*, gateway: GatewayPort | None = None) -> None:
    """Run Streamable HTTP using FastMCP's transport runner."""

    server = create_mcp_http_server(gateway=gateway)
    server.settings.host = os.environ.get("HOST", DEFAULT_HOST)
    server.settings.port = int(os.environ.get("PORT", str(DEFAULT_PORT)))
    await server.run_streamable_http_async()


async def _serve_composed() -> None:
    """Compose the live gateway, validate deploy posture, then serve.

    Phase-0.5: composition needs async OIDC discovery, so it runs inside the
    single ``asyncio.run`` started by ``main()``. ``policy_health_check`` is
    passed the SAME ``GatewayPolicy`` instance handed to the gateway, so a
    production deploy missing virtual_keys fails closed at startup
    (OperationalMisconfigurationError propagates out and aborts launch).
    """

    jwt_verifier, oidc_policy = await compose_auth_quartet()
    gateway, policy = build_runtime_gateway(jwt_verifier=jwt_verifier, oidc_policy=oidc_policy)
    # Post-composition lifecycle: init the real memory adapter's backend (Letta
    # system agent). No-op for Tier-1 stubs. F-14-LETTA-ONINIT-UNWIRED-01.
    initialize_runtime_adapters(gateway)
    policy_health_check(policy=policy)
    await serve_http(gateway=gateway)


def main() -> None:
    asyncio.run(_serve_composed())


if __name__ == "__main__":
    main()
