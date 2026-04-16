"""Praxis Runtime — Tavily MCP adapter (P0-2, Class B).

Architecture §6.1.2. R57 mandatory CostEvent per call. Read-only.
"""

from __future__ import annotations

from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.tools._base import ToolDescriptor

DESCRIPTOR: ToolDescriptor = next(t for t in TOOL_CATALOG if t.name == "tavily-mcp")


class TavilyMcpAdapter:
    """Tavily search MCP adapter. Read-only. CostEvent emission on every call."""

    descriptor = DESCRIPTOR

    # R57: CostEvent must be emitted before returning any result
    requires_cost_event = True


__all__ = ["TavilyMcpAdapter", "DESCRIPTOR"]
