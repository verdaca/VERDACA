"""Praxis Runtime — Filesystem MCP adapter (P0-1, Class C).

Architecture §6.1.1, §9.5 Class C, §9.6 secret isolation.
Denylist enforcement: .env, .ssh/*, credentials.*, **/secrets/**.
"""

from __future__ import annotations

import fnmatch
import re

# Re-import the canonical descriptor from the catalog for identity
from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.tools._base import (
    ToolDescriptor,
)

DESCRIPTOR: ToolDescriptor = next(t for t in TOOL_CATALOG if t.name == "fs-mcp")

# ---------------------------------------------------------------------------
# Denylist enforcement (architecture §9.6)
# ---------------------------------------------------------------------------

_DENYLIST_PATTERNS = [
    ".env",
    ".env.*",
    ".ssh/*",
    ".ssh",
    "credentials.*",
    "credentials",
    "**/secrets/**",
    "**/secrets/*",
    "secrets/**",
    "secrets/*",
    "*/secrets/*",
    "*/secrets/**",
]

_DENYLIST_REGEX = re.compile(
    r"(^|\/)("
    r"\.env($|[./])"
    r"|\.ssh[/\\]"
    r"|credentials\."
    r"|secrets[/\\]"
    r"|[^/]*secrets[/\\]"
    r")",
    re.IGNORECASE,
)


def is_path_denied(path: str) -> bool:
    """Return True if the path matches the filesystem denylist per §9.6.

    Checked before any MCP client call; defense-in-depth at adapter layer.
    """
    normalized = path.replace("\\", "/").lstrip("/")

    # Direct matches
    if normalized in (".env",):
        return True

    # Regex-based check
    if _DENYLIST_REGEX.search(normalized):
        return True

    # Glob-based checks
    for pattern in _DENYLIST_PATTERNS:
        if fnmatch.fnmatch(normalized, pattern):
            return True
        # Check against just the filename
        filename = normalized.split("/")[-1]
        if fnmatch.fnmatch(filename, pattern):
            return True

    # Specific file name checks
    low = normalized.lower()
    if any(
        low == name or low.endswith("/" + name)
        for name in (".env", "credentials.json", "credentials.yaml", ".ssh")
    ):
        return True

    # Pattern: any path segment is "secrets"
    parts = normalized.split("/")
    if "secrets" in parts:
        return True

    # .ssh directory
    if ".ssh" in parts or any(p.startswith(".ssh") for p in parts):
        return True

    # .env file or .env.* variants
    if parts and (parts[-1] == ".env" or parts[-1].startswith(".env")):
        return True

    # credentials.* files
    if parts and parts[-1].startswith("credentials."):
        return True

    return False


class FsMcpAdapter:
    """Filesystem MCP tool adapter — enforces denylist at pre-invocation layer."""

    descriptor = DESCRIPTOR

    def pre_invoke_check(self, path: str, mode: str) -> None:
        """Raise FileSystemAccessDeniedError if path is denied."""
        from praxis.kernel.runtime.tools._base import FileSystemAccessDeniedError

        if is_path_denied(path):
            raise FileSystemAccessDeniedError(
                f"Access denied: path {path!r} matches filesystem denylist (§9.6)"
            )


__all__ = ["FsMcpAdapter", "DESCRIPTOR", "is_path_denied"]
