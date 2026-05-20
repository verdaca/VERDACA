"""Praxis Runtime — Context7 MCP adapter (P0-4, Class A inert).

Architecture §6.1.4. Read-only library-docs retrieval. No state. No egress risk.
"""

from __future__ import annotations

from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.tools._base import ToolDescriptor

DESCRIPTOR: ToolDescriptor = next(t for t in TOOL_CATALOG if t.name == "context7-mcp")


class Context7McpAdapter:
    """Context7 library-docs MCP adapter. Class A inert — broad allowlist."""

    descriptor = DESCRIPTOR


__all__ = ["Context7McpAdapter", "DESCRIPTOR"]
