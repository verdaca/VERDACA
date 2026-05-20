"""MCP shape guard integration test — mac/test-strategy.md v0.3 §6.3.2.

Covers ``MAC-T-INT-RUNTIME-MCP-SHAPE-GUARD-01``. MAC inherits Runtime's
``verify_mcp_sdk_shape()`` verbatim; it does NOT re-implement the guard.

Anchors:
  - mac/architecture.md §10.3 Runtime Integration (MCP pin + shape guard)
  - runtime/architecture.md §5 MCP pin + shape guard (mcp>=1.9.0)
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.integrations.runtime import (
    FakeAgentSpawner,
    MacRuntimeAdapter,
)


class _ShapeGuardFailed(Exception):
    pass


def _failing_shape_guard() -> None:
    raise _ShapeGuardFailed("simulated MCP SDK shape mismatch")


def _passing_shape_guard() -> None:
    return None


@pytest.mark.critical
@pytest.mark.integration
def test_mac_t_int_runtime_mcp_shape_guard_01_passes_when_guard_returns() -> None:
    """MAC-T-INT-RUNTIME-MCP-SHAPE-GUARD-01 — shape guard call is delegated to Runtime.

    ``MacRuntimeAdapter.verify_mcp_sdk_shape`` calls the injected shape
    guard callable and propagates any exception the guard raises. The
    MAC does NOT translate; whatever Runtime's guard raises, MAC
    re-raises.

    Two assertions:
      (a) when the guard returns successfully, the adapter method
          returns None without error.
      (b) when the guard raises, the adapter method propagates the
          same exception class (not wrapped, not translated).
    """
    spawner = FakeAgentSpawner()
    passing_adapter = MacRuntimeAdapter(
        spawner=spawner, shape_guard=_passing_shape_guard
    )
    # (a) Passing guard → no raise.
    passing_adapter.verify_mcp_sdk_shape()

    # (b) Failing guard → raise propagates.
    failing_adapter = MacRuntimeAdapter(
        spawner=spawner, shape_guard=_failing_shape_guard
    )
    with pytest.raises(_ShapeGuardFailed, match="simulated MCP SDK"):
        failing_adapter.verify_mcp_sdk_shape()
