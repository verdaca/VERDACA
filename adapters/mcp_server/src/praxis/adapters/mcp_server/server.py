"""FastMCP factory for Verdaca's inbound MCP server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from praxis.adapters.mcp_server.tools import register_tools
from praxis.ports.gateway import GatewayPort

SERVER_NAME = "verdaca-mcp"
SERVER_INSTRUCTIONS = " ".join(
    (
        "Verdaca helps decision owners get defensible recommendations with cited tradeoffs.",
        "Use verdaca_start_analysis for a new decision question.",
        "Use verdaca_estimate_cost before deeper deliberation.",
        "Use result and artifact tools to review prior decision work.",
    )
)


def create_verdaca_mcp_server(
    *,
    gateway: GatewayPort | None = None,
    stateless_http: bool = True,
) -> FastMCP:
    """Create a FastMCP server and register the E2-owned tool surface."""

    server = FastMCP(
        SERVER_NAME,
        instructions=SERVER_INSTRUCTIONS,
        stateless_http=stateless_http,
    )
    register_tools(server, gateway=gateway)
    return server
