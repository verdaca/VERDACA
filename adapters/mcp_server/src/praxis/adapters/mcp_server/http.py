"""Streamable HTTP transport for the Verdaca MCP server."""

from __future__ import annotations

import asyncio
import importlib
import os
from collections.abc import Callable
from typing import cast

from mcp.server.fastmcp import FastMCP

from praxis.adapters.mcp_server.server import create_verdaca_mcp_server
from praxis.ports.gateway import GatewayPort

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 3000


def _load_bearer_verifier() -> Callable[[str | None], None]:
    try:
        policy = importlib.import_module("praxis.kernel.gateway.policy")
        verifier = policy.verify_bearer_token
    except (ImportError, ModuleNotFoundError) as exc:
        raise NotImplementedError(
            "Bearer-token policy integration waits for E1 policy.py at [E1-H#2.4]"
        ) from exc
    except AttributeError as exc:
        raise NotImplementedError(
            "Bearer-token policy integration waits for E1 policy.py at [E1-H#2.4]"
        ) from exc
    return cast(Callable[[str | None], None], verifier)


def verify_bearer_authorization(authorization: str | None) -> None:
    """Call E1's policy gate when it exists."""

    _load_bearer_verifier()(authorization)


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
    asyncio.run(serve_http())


if __name__ == "__main__":
    main()
