"""Streamable HTTP transport for the Verdaca MCP server."""

from __future__ import annotations

import asyncio
import os

from mcp.server.fastmcp import FastMCP

from praxis.adapters.mcp_server.server import create_verdaca_mcp_server
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


def main() -> None:
    policy_health_check()
    asyncio.run(serve_http())


if __name__ == "__main__":
    main()
