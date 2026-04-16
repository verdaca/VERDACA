"""Praxis Runtime MCP Adapter — SDK shape regression guard.

Verifies that the installed mcp SDK exposes the structural shape required
by architecture §5.3. Called at Runtime init; if the shape check fails,
the Runtime hard-fails rather than silently mis-behaving.

Architecture references:
  architecture.md §5.1 (Official Python SDK + version pinning)
  architecture.md §5.3 (MCPToolAdapter SDK usage)
  test-strategy §10.1 (SDK version guard test spec)
"""

from __future__ import annotations

_REQUIRED_SESSION_METHODS = (
    "call_tool",
    "list_tools",
    "initialize",
    "send_ping",
)


class MCPSDKShapeMismatchError(RuntimeError):
    """Raised when the mcp SDK's public shape diverges from architecture §5.3."""


def verify_mcp_sdk_shape() -> None:
    """Assert that the installed mcp SDK exposes required ClientSession methods.

    Called at Runtime init and during test_sdk_version_guard.py.
    Raises MCPSDKShapeMismatchError if any required symbol is missing.
    """
    try:
        from mcp.client.session import ClientSession
    except ImportError as exc:
        raise MCPSDKShapeMismatchError(
            "mcp.client.session.ClientSession not importable. "
            "Ensure 'mcp' is installed. OQ-TS-11 blocker."
        ) from exc

    missing = [m for m in _REQUIRED_SESSION_METHODS if not hasattr(ClientSession, m)]
    if missing:
        raise MCPSDKShapeMismatchError(
            f"mcp ClientSession missing required methods: {missing}. "
            "The installed mcp version may be incompatible with architecture §5.3."
        )

    # Verify StdioServerParameters (needed by transport.py)
    try:
        from mcp import StdioServerParameters  # noqa: F401
    except ImportError as exc:
        raise MCPSDKShapeMismatchError("mcp.StdioServerParameters not importable.") from exc


__all__ = ["verify_mcp_sdk_shape", "MCPSDKShapeMismatchError"]
