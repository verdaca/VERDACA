"""Praxis Runtime MCP Adapter — client wrapper.

Wraps mcp.client.session.ClientSession with:
- Error normalization (raw MCP errors → tenant-safe ToolInvocationError)
- Transient vs permanent error classification for retry policy (architecture §5.7)

Architecture references:
  architecture.md §5.3 (MCPToolAdapter)
  architecture.md §5.6 (error hierarchy)
  architecture.md §5.7 (retry policy: transient vs permanent)
"""

from __future__ import annotations

from praxis.kernel.runtime.tools._base import (
    MCPAdapterError,
    ToolCapabilityError,
    ToolInputValidationError,
    ToolInvocationError,
    ToolNotAllowedError,
    ToolResultValidationError,
)

# ---------------------------------------------------------------------------
# Error normalization (architecture §5.6)
# ---------------------------------------------------------------------------


def normalize_mcp_error(exc: Exception) -> ToolInvocationError:
    """Normalize raw MCP errors into tenant-safe ToolInvocationError.

    Raw server-side stack traces and internal state must never reach the
    agent's LLM context. This function produces a sanitized error that
    preserves enough information for debugging while stripping sensitive content.
    """
    # Produce a sanitized message — omit raw exception message to avoid
    # accidentally leaking server internals or credential fragments
    return ToolInvocationError(f"MCP tool invocation failed: {type(exc).__name__}")


# ---------------------------------------------------------------------------
# Transient error classification (architecture §5.7)
# ---------------------------------------------------------------------------


_PERMANENT_ERROR_TYPES = (
    ToolNotAllowedError,
    ToolCapabilityError,
    ToolInputValidationError,
    ToolResultValidationError,
    ValueError,
    TypeError,
    AttributeError,
    KeyError,
    NotImplementedError,
)

_TRANSIENT_ERROR_TYPES = (
    TimeoutError,
    ConnectionError,
    OSError,
)


def is_transient_error(exc: Exception) -> bool:
    """Return True if the error is a transient backend issue that warrants retry.

    Architecture §5.7: transient errors (network timeouts, 5xx, 429s) retry
    with exponential backoff up to 3 times. Permanent errors (4xx, validation
    failures, allowlist denials) fail immediately without retry.
    """
    if isinstance(exc, _PERMANENT_ERROR_TYPES):
        return False
    if isinstance(exc, MCPAdapterError):
        return False

    # Check mcp SDK error types without hard-importing (may not be available)
    try:
        from mcp import McpError

        if isinstance(exc, McpError):
            # McpError can be transient (network) or permanent (protocol)
            # Conservative: treat as transient so callers can retry
            return True
    except ImportError:
        pass

    if isinstance(exc, _TRANSIENT_ERROR_TYPES):
        return True

    # Default: treat unknown exceptions as transient (fail-safe)
    return True


__all__ = ["normalize_mcp_error", "is_transient_error"]
