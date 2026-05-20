"""Praxis Runtime — Subprocess MCP adapter (P0-7b, Class D).

Architecture §6.1.7b. The ONLY admitted Class D tool at launch.
Narrow per-binary allowlist: pytest/ruff/mypy/python/pip/npm test/node ONLY.
Tight agent allowlist: Amelia/Barry/Quinn ONLY.
"""

from __future__ import annotations

from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.tools._base import ToolDescriptor

DESCRIPTOR: ToolDescriptor = next(t for t in TOOL_CATALOG if t.name == "subprocess-mcp")

# ---------------------------------------------------------------------------
# Per-binary allowlist (architecture §6.1.7b)
# ---------------------------------------------------------------------------

_BINARY_ALLOWLIST: frozenset[str] = frozenset(
    {
        "pytest",
        "ruff",
        "mypy",
        "python",
        "python3",
        "pip",
        "pip3",
        "npm",
        "node",
    }
)

# ---------------------------------------------------------------------------
# Per-agent allowlist — only Amelia, Barry, Quinn (architecture §6.1.7b)
# ---------------------------------------------------------------------------

SUBPROCESS_AGENT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "bmad-agent-dev",  # Amelia
        "bmad-agent-quick-flow-solo-dev",  # Barry
        "bmad-agent-qa",  # Quinn
    }
)


def is_binary_allowed(binary: str) -> bool:
    """Return True if the binary is in the narrow per-binary allowlist."""
    return binary.strip().lower() in _BINARY_ALLOWLIST


class SubprocessMcpAdapter:
    """Subprocess MCP adapter. Class D, narrow allowlist."""

    descriptor = DESCRIPTOR
    agent_allowlist = SUBPROCESS_AGENT_ALLOWLIST

    def check_binary_allowed(self, binary: str) -> None:
        """Raise ToolNotAllowedError if binary is not in the allowlist."""
        from praxis.kernel.runtime.tools._base import ToolNotAllowedError

        if not is_binary_allowed(binary):
            raise ToolNotAllowedError(
                f"subprocess-mcp: binary {binary!r} not in allowlist {sorted(_BINARY_ALLOWLIST)}. "
                "Architecture §6.1.7b: only pytest/ruff/mypy/python/pip/npm/node admitted."
            )

    def check_agent_allowed(self, agent_name: str) -> None:
        """Raise ToolNotAllowedError if agent is not in the narrow agent allowlist."""
        from praxis.kernel.runtime.tools._base import ToolNotAllowedError

        if agent_name not in SUBPROCESS_AGENT_ALLOWLIST:
            raise ToolNotAllowedError(
                f"subprocess-mcp: agent {agent_name!r} not in agent allowlist. "
                "Only Amelia (bmad-agent-dev), Barry (bmad-agent-quick-flow-solo-dev), "
                "and Quinn (bmad-agent-qa) may invoke subprocess."
            )


__all__ = [
    "SubprocessMcpAdapter",
    "DESCRIPTOR",
    "SUBPROCESS_AGENT_ALLOWLIST",
    "is_binary_allowed",
]
