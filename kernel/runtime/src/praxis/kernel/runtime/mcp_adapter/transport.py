"""Praxis Runtime MCP Adapter — transport helpers.

Architecture references:
  architecture.md §5.1 (stdio and HTTP client transports)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MCPTransportKind(StrEnum):
    """Supported MCP transport kinds."""

    STDIO = "stdio"
    HTTP = "http"


@dataclass(frozen=True)
class StdioTransportConfig:
    """Configuration for a subprocess-stdio MCP server."""

    command: str
    args: tuple[str, ...] = ()
    env: dict[str, str] | None = None


@dataclass(frozen=True)
class HttpTransportConfig:
    """Configuration for an HTTP MCP server."""

    base_url: str
    headers: dict[str, str] | None = None


def make_stdio_params(config: StdioTransportConfig) -> Any:
    """Return a StdioServerParameters instance for the mcp SDK."""
    from mcp import StdioServerParameters

    return StdioServerParameters(
        command=config.command,
        args=list(config.args),
        env=config.env or {},
    )


__all__ = [
    "MCPTransportKind",
    "StdioTransportConfig",
    "HttpTransportConfig",
    "make_stdio_params",
]
