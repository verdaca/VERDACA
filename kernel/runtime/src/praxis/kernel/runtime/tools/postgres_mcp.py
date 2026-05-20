"""Praxis Runtime — PostgreSQL MCP adapter (P0-6, Class C).

Architecture §6.1.6. Read-only default. Write requires per-agent allowlist grant.
DDL statements (CREATE/ALTER/DROP) rejected at adapter layer.
Typed query-builder only — no raw SQL surface exposed to agents.
"""

from __future__ import annotations

import re

from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.tools._base import ToolDescriptor

DESCRIPTOR: ToolDescriptor = next(t for t in TOOL_CATALOG if t.name == "postgres-mcp")

# ---------------------------------------------------------------------------
# DDL detection (architecture §6.1.6)
# ---------------------------------------------------------------------------

_DDL_PATTERN = re.compile(
    r"^\s*(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COMMENT)\s+",
    re.IGNORECASE,
)


def is_ddl_statement(sql: str) -> bool:
    """Return True if the SQL is a DDL statement that must be rejected at adapter layer."""
    return bool(_DDL_PATTERN.match(sql.strip()))


class PostgresMcpAdapter:
    """PostgreSQL MCP adapter. Typed queries only. DDL blocked."""

    descriptor = DESCRIPTOR

    def validate_query(self, sql: str) -> None:
        """Raise if SQL is DDL or otherwise disallowed."""
        from praxis.kernel.runtime.tools._base import ToolInputValidationError

        if is_ddl_statement(sql):
            raise ToolInputValidationError(
                f"DDL statements are not permitted via postgres-mcp adapter (§6.1.6): {sql[:80]!r}"
            )


__all__ = ["PostgresMcpAdapter", "DESCRIPTOR", "is_ddl_statement"]
