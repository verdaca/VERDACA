"""Verdaca MCP resources.

Resource wiring blocks at [E2-H#6.5] until E1 surfaces [E1-H#2.3-COMPLETE].
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from praxis.ports.gateway import GatewayPort

RESOURCE_URIS: tuple[str, ...] = (
    "verdaca://methodology",
    "verdaca://templates",
    "verdaca://sessions/{session_id}/result/summary",
    "verdaca://sessions/{session_id}/result/transcript",
    "verdaca://sessions/{session_id}/artifacts/{artifact_id}",
)


def register_resources(server: FastMCP, *, gateway: GatewayPort) -> None:
    """Register Verdaca resources once the E1 GatewayPort implementation lands."""

    raise NotImplementedError("[E2-H#6.5] blocks on [E1-H#2.3-COMPLETE]")
