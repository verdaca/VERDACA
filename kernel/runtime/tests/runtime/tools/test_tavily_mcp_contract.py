"""tests/runtime/tools/test_tavily_mcp_contract.py — RED commit.

Contract tests for tavily-mcp. Architecture §6.1.2, R57 mandatory CostEvent.
"""

from __future__ import annotations


def test_tavily_mcp_importable() -> None:
    from praxis.kernel.runtime.tools.tavily_mcp import TavilyMcpAdapter  # noqa: F401


def test_tavily_mcp_descriptor_blast_class_b() -> None:
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass
    from praxis.kernel.runtime.tools.tavily_mcp import DESCRIPTOR

    assert DESCRIPTOR.blast_class == ToolBlastRadiusClass.B


def test_tavily_mcp_read_only_no_write() -> None:
    from praxis.kernel.runtime.tools.tavily_mcp import DESCRIPTOR

    assert DESCRIPTOR.read_mode_capable
    assert not DESCRIPTOR.write_mode_capable


def test_tavily_mcp_r57_compliance_flag() -> None:
    from praxis.kernel.runtime.tools.tavily_mcp import DESCRIPTOR

    assert "R57" in DESCRIPTOR.compliance_flags
