"""tests/runtime/tools/test_python_sandbox_mcp_contract.py — RED commit.

Contract tests for python-sandbox-mcp. Architecture §6.1.7a. Class C.
"""

from __future__ import annotations


def test_python_sandbox_mcp_importable() -> None:
    from praxis.kernel.runtime.tools.python_sandbox_mcp import PythonSandboxMcpAdapter  # noqa: F401


def test_python_sandbox_mcp_descriptor_blast_class_c() -> None:
    from praxis.kernel.runtime.tools._base import ToolBlastRadiusClass
    from praxis.kernel.runtime.tools.python_sandbox_mcp import DESCRIPTOR

    assert DESCRIPTOR.blast_class == ToolBlastRadiusClass.C


def test_python_sandbox_mcp_network_denied_by_default() -> None:
    """Network egress is denied by default per architecture §6.1.7a."""
    from praxis.kernel.runtime.tools.python_sandbox_mcp import PythonSandboxMcpAdapter

    adapter = PythonSandboxMcpAdapter()
    assert not adapter.network_enabled_by_default


def test_python_sandbox_mcp_r57_compliance() -> None:
    from praxis.kernel.runtime.tools.python_sandbox_mcp import DESCRIPTOR

    assert "R57" in DESCRIPTOR.compliance_flags
