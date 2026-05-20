"""tests/runtime/tools/test_context7_mcp_contract.py — RED commit.

Contract tests for context7-mcp. Architecture §6.1.4. Class A inert.
"""

from __future__ import annotations


def test_context7_mcp_importable() -> None:
    from praxis.kernel.runtime.tools.context7_mcp import Context7McpAdapter  # noqa: F401


def test_context7_mcp_descriptor_blast_class_a() -> None:
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass
    from praxis.kernel.runtime.tools.context7_mcp import DESCRIPTOR

    assert DESCRIPTOR.blast_class == ToolBlastRadiusClass.A


def test_context7_mcp_read_only_no_write() -> None:
    from praxis.kernel.runtime.tools.context7_mcp import DESCRIPTOR

    assert DESCRIPTOR.read_mode_capable
    assert not DESCRIPTOR.write_mode_capable
