"""Praxis Runtime — Playwright MCP adapter (P0-5, Class B read / Class D write P2-capped).

Architecture §6.1.5. Write mode is P2-capped at launch per §9.3.
Any write-mode call raises ToolCapabilityNotAvailable.
"""

from __future__ import annotations

from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.tools._base import ToolCapabilityNotAvailable, ToolDescriptor

DESCRIPTOR: ToolDescriptor = next(t for t in TOOL_CATALOG if t.name == "playwright-mcp")


class PlaywrightMcpAdapter:
    """Playwright MCP adapter. Read-only at launch. Write mode P2-capped."""

    descriptor = DESCRIPTOR

    def assert_write_mode_available(self) -> None:
        """Raise ToolCapabilityNotAvailable — write mode is P2-capped at launch."""
        raise ToolCapabilityNotAvailable(
            "playwright-mcp write mode (form submission with credentials) is P2-capped "
            "per architecture §9.3. Available in Stage 5+ when destructive-op approval "
            "workflow ships."
        )


__all__ = ["PlaywrightMcpAdapter", "DESCRIPTOR"]
