"""tests/runtime/mcp_adapter/test_sdk_version_guard.py — GREEN.

OQ-TS-11 resolution: mcp 1.27.0 structural shape verified.
"""

from __future__ import annotations

import mcp
import mcp.client.session
from mcp import McpError, StdioServerParameters
from mcp.client.session import ClientSession

from praxis.kernel.runtime.mcp_adapter.version_guard import verify_mcp_sdk_shape


def test_mcp_package_importable() -> None:
    assert mcp is not None


def test_client_session_importable() -> None:
    assert ClientSession is not None


def test_client_session_has_call_tool() -> None:
    assert hasattr(ClientSession, "call_tool") and callable(ClientSession.call_tool)


def test_client_session_has_list_tools() -> None:
    assert hasattr(ClientSession, "list_tools")


def test_client_session_has_initialize() -> None:
    assert hasattr(ClientSession, "initialize")


def test_stdio_transport_importable() -> None:
    assert StdioServerParameters is not None


def test_mcp_error_importable() -> None:
    assert issubclass(McpError, Exception)


def test_version_guard_module_importable() -> None:
    assert callable(verify_mcp_sdk_shape)


def test_version_guard_passes_with_real_sdk() -> None:
    # Should not raise — mcp 1.27.0 is structurally aligned
    verify_mcp_sdk_shape()
