"""Verdaca MCP prompts."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(server: FastMCP) -> None:
    """Register prompt templates at [E2-H#7]."""

    raise NotImplementedError("[E2-H#7] prompt registration follows transport wiring")
