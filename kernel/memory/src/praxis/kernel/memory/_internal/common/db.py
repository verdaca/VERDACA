"""SQLAlchemy engine factory for the Memory module.

NR-SC-R2 strawman implementation — values from nfr-report.md.
Pending Winston §4.2 ratification in architecture.md v1.1.
If Winston diverges, this module requires one-line refactor.

Scope: this module is the ONE place in the Memory codebase that constructs a
SQLAlchemy `Engine`. Everything downstream (Beads port, Mem0 adapter, Atelier
decision store, pgvector collection access, migrations) reuses the engine
returned by `create_memory_engine()` so a single pool sizing decision applies
to every Memory-layer database call.

This module lives under `_internal/` and is therefore unreachable from
application code per NR-S-R1 (ruff TID251 + grep tripwire). The facade in
`praxis.kernel.memory` is the only legal caller.
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine

# --- NR-SC-R2 pool parameters ------------------------------------------------
# Source: nfr-report.md §7.1 NR-SC-R2, ratified by Andrey 2026-04-12.
# DO NOT CHANGE without an architecture.md v1.1 amendment. These values are
# the strawman from Murat's NFR analysis; Winston's §4.2 amendment (parallel
# track) will codify them. If Winston diverges, refactor to match.
POOL_SIZE: int = 10
MAX_OVERFLOW: int = 15
POOL_PRE_PING: bool = True
POOL_RECYCLE_SECONDS: int = 3600


def create_memory_engine(url: str) -> Engine:
    """Construct the Memory module's SQLAlchemy engine with NR-SC-R2 pool config.

    Parameters
    ----------
    url:
        A SQLAlchemy URL string. Production uses the Postgres URL assembled
        from the deployment manifest; tests pass an in-memory SQLite URL.

    Returns
    -------
    sqlalchemy.Engine
        Configured engine. Callers share this instance across the Memory
        module to ensure a single pool per process (single-tenant invariant).
    """
    return create_engine(
        url,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_pre_ping=POOL_PRE_PING,
        pool_recycle=POOL_RECYCLE_SECONDS,
    )
