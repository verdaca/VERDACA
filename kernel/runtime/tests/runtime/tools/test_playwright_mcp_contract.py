"""tests/runtime/tools/test_playwright_mcp_contract.py — RED commit.

Contract tests for playwright-mcp. Architecture §6.1.5, §9.3 P2-cap on write.
"""

from __future__ import annotations

import pytest


def test_playwright_mcp_importable() -> None:
    from praxis.kernel.runtime.tools.playwright_mcp import PlaywrightMcpAdapter  # noqa: F401


def test_playwright_mcp_read_only_at_launch() -> None:
    """Write mode is P2-capped at launch per architecture §9.3."""
    from praxis.kernel.runtime.tools.playwright_mcp import DESCRIPTOR

    assert not DESCRIPTOR.write_mode_capable


def test_playwright_mcp_write_mode_raises_not_available() -> None:
    """Attempting write mode raises ToolCapabilityNotAvailable."""
    from praxis.kernel.runtime.tools._base import ToolCapabilityNotAvailable
    from praxis.kernel.runtime.tools.playwright_mcp import PlaywrightMcpAdapter

    adapter = PlaywrightMcpAdapter()
    with pytest.raises(ToolCapabilityNotAvailable):
        adapter.assert_write_mode_available()


def test_playwright_mcp_descriptor_blast_class_b() -> None:
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass
    from praxis.kernel.runtime.tools.playwright_mcp import DESCRIPTOR

    assert DESCRIPTOR.blast_class == ToolBlastRadiusClass.B
