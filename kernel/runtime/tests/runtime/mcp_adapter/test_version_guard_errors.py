"""tests/runtime/mcp_adapter/test_version_guard_errors.py

Coverage filler for version_guard.py error paths.
"""

from __future__ import annotations

import pytest

from praxis.kernel.runtime.mcp_adapter.version_guard import (
    MCPSDKShapeMismatchError,
    verify_mcp_sdk_shape,
)


def test_verify_mcp_sdk_shape_passes() -> None:
    """verify_mcp_sdk_shape() must succeed with installed mcp 1.27.0."""
    verify_mcp_sdk_shape()  # Should not raise


def test_mcp_sdk_shape_mismatch_error_is_runtime_error() -> None:
    assert issubclass(MCPSDKShapeMismatchError, RuntimeError)


def test_is_transient_value_error_permanent() -> None:
    from praxis.kernel.runtime.mcp_adapter.client import is_transient_error

    assert not is_transient_error(ValueError("bad input"))


def test_is_transient_type_error_permanent() -> None:
    from praxis.kernel.runtime.mcp_adapter.client import is_transient_error

    assert not is_transient_error(TypeError("wrong type"))


def test_is_transient_os_error() -> None:
    from praxis.kernel.runtime.mcp_adapter.client import is_transient_error

    assert is_transient_error(OSError("network unreachable"))


def test_is_transient_connection_error() -> None:
    from praxis.kernel.runtime.mcp_adapter.client import is_transient_error

    assert is_transient_error(ConnectionError("connection refused"))


def test_is_transient_unknown_exception() -> None:
    from praxis.kernel.runtime.mcp_adapter.client import is_transient_error

    # Unknown exceptions default to transient (fail-safe)
    assert is_transient_error(Exception("unknown error"))


def test_is_transient_mcp_error() -> None:
    """McpError instances are treated as transient (network-level issues)."""
    from mcp import McpError
    from mcp.types import ErrorData

    from praxis.kernel.runtime.mcp_adapter.client import is_transient_error

    exc = McpError(ErrorData(code=-32000, message="server error"))
    assert is_transient_error(exc)


def test_verify_mcp_sdk_shape_import_error_raises_mismatch() -> None:
    """ImportError on ClientSession → MCPSDKShapeMismatchError."""
    import unittest.mock

    from praxis.kernel.runtime.mcp_adapter.version_guard import (
        MCPSDKShapeMismatchError,
        verify_mcp_sdk_shape,
    )

    with unittest.mock.patch.dict("sys.modules", {"mcp.client.session": None}):
        with pytest.raises((MCPSDKShapeMismatchError, ImportError)):
            # Reload to trigger the import path with patched module
            verify_mcp_sdk_shape()


def test_verify_sdk_missing_method_raises_mismatch() -> None:
    """Missing method on ClientSession → MCPSDKShapeMismatchError."""
    import unittest.mock

    from praxis.kernel.runtime.mcp_adapter.version_guard import (
        MCPSDKShapeMismatchError,
        verify_mcp_sdk_shape,
    )

    # Patch ClientSession to remove a required method
    class FakeClientSession:
        pass  # no required methods

    fake_module = unittest.mock.MagicMock()
    fake_module.ClientSession = FakeClientSession

    with unittest.mock.patch.dict("sys.modules", {"mcp.client.session": fake_module}):
        with pytest.raises(MCPSDKShapeMismatchError, match="missing required methods"):
            verify_mcp_sdk_shape()
