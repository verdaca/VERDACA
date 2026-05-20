"""Praxis Runtime — tool adapter base types.

Defines the shared data model and error hierarchy for all P0/P1 tool adapters.

Architecture references:
  architecture.md §5.2 (ToolDescriptor, ToolBlastRadiusClass)
  architecture.md §5.6 (error hierarchy)
  architecture.md §6 (tool catalog — P0/P1/P2 classification)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ToolBlastRadiusClass(StrEnum):
    """Carson §5.6 blast-radius tiering — drives sandbox policy in §9."""

    A = "A"  # Inert — read-only, no egress beyond request
    B = "B"  # Scoped egress — read + network to known public APIs
    C = "C"  # Tenant data surface — read/write within tenant-scoped datastores
    D = "D"  # Destructive / escalation-capable — write to external state
    E = "E"  # Unbounded — sandbox-escape capable; NOT ADMITTED


class ToolPriority(StrEnum):
    """Launch priority tier from Carson §4."""

    P0 = "P0"  # Launch-binding — ships at Stage 4.3
    P1 = "P1"  # Strong candidates — ships at Stage 4.3 or deferred
    P2 = "P2"  # Deferred — NOT admitted at launch


# ---------------------------------------------------------------------------
# ToolDescriptor
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolDescriptor:
    """Metadata for a single tool in the Praxis tool library.

    Sourced from Carson's P0/P1 list (architecture §6).  New tools enter
    via the §5.4 intake protocol — never added here without that gate.
    """

    name: str
    mcp_server_id: str
    blast_class: ToolBlastRadiusClass
    priority: ToolPriority
    read_mode_capable: bool
    write_mode_capable: bool
    default_mode: str  # 'read-only' | 'write-only' | 'read-write'
    primary_caller_agents: tuple[str, ...]
    compliance_flags: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""


# ---------------------------------------------------------------------------
# Error hierarchy  (architecture §5.6)
# ---------------------------------------------------------------------------


class MCPAdapterError(Exception):
    """Base class for all MCP Tool Adapter errors."""


class UnknownToolError(MCPAdapterError):
    """Tool name not in the registry."""


class ToolNotAllowedError(MCPAdapterError):
    """Caller agent has no allowlist entry for this tool."""


class ToolCapabilityError(MCPAdapterError):
    """Caller requested a mode the tool does not support or agent is not granted."""


class ToolCapabilityNotAvailable(ToolCapabilityError):
    """Capability exists in theory but is P2-capped at launch."""


class ToolInputValidationError(MCPAdapterError):
    """Payload failed validation against the tool's input schema."""


class ToolInvocationError(MCPAdapterError):
    """MCP server returned an error or invocation failed at protocol level."""


class ToolResultValidationError(MCPAdapterError):
    """MCP server returned a result that failed validation against output schema."""


class ToolBudgetExceededError(MCPAdapterError):
    """The caller's resource budget was exhausted before or during this invocation."""


class SandboxNetworkDeniedError(MCPAdapterError):
    """Network egress denied by sandbox policy."""


class FileSystemAccessDeniedError(MCPAdapterError):
    """Filesystem access denied by denylist or workspace boundary."""


class SandboxEscapeAttemptError(MCPAdapterError):
    """Detected attempt to escape sandbox boundaries."""


__all__ = [
    "ToolBlastRadiusClass",
    "ToolPriority",
    "ToolDescriptor",
    "MCPAdapterError",
    "UnknownToolError",
    "ToolNotAllowedError",
    "ToolCapabilityError",
    "ToolCapabilityNotAvailable",
    "ToolInputValidationError",
    "ToolInvocationError",
    "ToolResultValidationError",
    "ToolBudgetExceededError",
    "SandboxNetworkDeniedError",
    "FileSystemAccessDeniedError",
    "SandboxEscapeAttemptError",
]
