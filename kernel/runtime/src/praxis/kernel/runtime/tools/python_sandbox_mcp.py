"""Praxis Runtime — Python Sandbox MCP adapter (P0-7a, Class C).

Architecture §6.1.7a. Containerized Python execution.
No network by default. CPU/memory/wall-time bounded by ResourceBudget.
"""

from __future__ import annotations

from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.tools._base import ToolDescriptor

DESCRIPTOR: ToolDescriptor = next(t for t in TOOL_CATALOG if t.name == "python-sandbox-mcp")


class PythonSandboxMcpAdapter:
    """Python sandbox MCP adapter. Containerized, no network by default."""

    descriptor = DESCRIPTOR

    # Network is disabled by default; opt-in per call with deployment operator grant
    network_enabled_by_default: bool = False


__all__ = ["PythonSandboxMcpAdapter", "DESCRIPTOR"]
