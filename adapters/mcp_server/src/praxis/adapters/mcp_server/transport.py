"""Adapter-local MCP transport protocol."""

from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable


@runtime_checkable
class MCPTransportPort(Protocol):
    """Transport runner owned by the inbound MCP adapter package."""

    API_VERSION: ClassVar[str] = "1.0.0"

    async def serve_stdio(self) -> None:
        """Serve the MCP server over stdio."""

    async def serve_http(self, *, stateless: bool = True) -> None:
        """Serve the MCP server over Streamable HTTP."""
