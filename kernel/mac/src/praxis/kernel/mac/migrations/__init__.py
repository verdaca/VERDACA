"""MAC-owned schema migrations.

MAC owns its own migration namespace, distinct from Stage 3 Memory's
migrations. The first migration (``0001_mac_bootstrap_metadata``)
creates the sidecar table ``mac_bootstrap_metadata`` per arch §8.1
Option Y ratification. Stage 3 Memory schema is FROZEN — this
sidecar table is the MAC-local artifact that satisfies SQ-6 without
reopening Memory.

Binding anchors:
  - mac/architecture.md §8.1 Option Y Ratification
  - mac/architecture.md §13.2 Rejected Alternatives (Option X)
  - mac/test-strategy.md v0.3 §8.1 MAC-T-BOOT-MIGRATION-01..03
"""

from __future__ import annotations

from praxis.kernel.mac.migrations.mac_bootstrap_metadata_0001 import (
    CREATE_TABLE_SQL,
    DROP_TABLE_SQL,
    MIGRATION_ID,
    MIGRATION_NAME,
    REQUIRED_COLUMNS,
    upgrade,
)

__all__ = (
    "CREATE_TABLE_SQL",
    "DROP_TABLE_SQL",
    "MIGRATION_ID",
    "MIGRATION_NAME",
    "REQUIRED_COLUMNS",
    "upgrade",
)
