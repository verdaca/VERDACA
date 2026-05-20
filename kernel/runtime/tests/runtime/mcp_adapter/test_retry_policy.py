"""tests/runtime/mcp_adapter/test_retry_policy.py — GREEN."""

from __future__ import annotations

from praxis.kernel.runtime.mcp_adapter import transport
from praxis.kernel.runtime.mcp_adapter.client import is_transient_error
from praxis.kernel.runtime.tools._base import ToolNotAllowedError


def test_retry_policy_transient_classification() -> None:
    assert is_transient_error(TimeoutError("connection timeout"))


def test_retry_policy_permanent_classification() -> None:
    assert not is_transient_error(ToolNotAllowedError("not allowed"))


def test_retry_policy_importable() -> None:
    assert callable(is_transient_error)


def test_transport_module_importable() -> None:
    assert transport is not None
