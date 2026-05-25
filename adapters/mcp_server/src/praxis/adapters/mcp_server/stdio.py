"""Stdio transport for the Verdaca MCP server."""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from praxis.adapters.mcp_server.server import create_verdaca_mcp_server
from praxis.ports.gateway import GatewayPort


def create_stdio_server(*, gateway: GatewayPort | None = None) -> FastMCP:
    """Create the FastMCP server used by local MCP clients over stdio."""

    return create_verdaca_mcp_server(gateway=gateway, stateless_http=True)


async def serve_stdio(*, gateway: GatewayPort | None = None) -> None:
    """Run the MCP server over stdio."""

    await create_stdio_server(gateway=gateway).run_stdio_async()


def main() -> None:
    asyncio.run(serve_stdio())


if __name__ == "__main__":
    main()
