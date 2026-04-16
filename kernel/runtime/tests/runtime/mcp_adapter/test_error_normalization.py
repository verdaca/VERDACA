"""tests/runtime/mcp_adapter/test_error_normalization.py — GREEN."""

from __future__ import annotations

from praxis.kernel.runtime.mcp_adapter.client import normalize_mcp_error
from praxis.kernel.runtime.tools._base import ToolInvocationError


def test_mcp_error_normalizes_to_tool_invocation_error() -> None:
    result = normalize_mcp_error(RuntimeError("internal MCP server error"))
    assert isinstance(result, ToolInvocationError)


def test_normalized_error_message_is_tenant_safe() -> None:
    result = normalize_mcp_error(RuntimeError("secret_credential xyz987 stack trace"))
    msg = str(result)
    # Raw exception message must not appear verbatim
    assert "secret_credential xyz987 stack trace" not in msg


def test_normalize_mcp_error_importable() -> None:
    assert callable(normalize_mcp_error)
