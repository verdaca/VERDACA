"""Dialect-specific helpers. Isolates SQLite vs Postgres differences."""
from __future__ import annotations

from typing import Any

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .schema import CostRecordRow


async def dialect_specific_upsert(
    session: AsyncSession,
    row_values: dict[str, Any],
) -> CostRecordRow:
    """Insert a cost record idempotently on request_id.

    Uses ON CONFLICT DO NOTHING + RETURNING on Postgres, or a SELECT-then-INSERT
    wrapped in a BEGIN IMMEDIATE transaction on SQLite.
    """
    bind = session.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(CostRecordRow).values(**row_values)
        stmt = stmt.on_conflict_do_nothing(index_elements=["request_id"]).returning(
            CostRecordRow
        )
        result = await session.execute(stmt)
        inserted = result.scalar_one_or_none()
        if inserted is not None:
            return inserted
        existing = await _fetch_by_request_id(session, row_values["request_id"])
        if existing is None:
            raise RuntimeError("upsert: neither inserted nor found existing row")
        return existing

    stmt = insert(CostRecordRow).values(**row_values).prefix_with("OR IGNORE")
    await session.execute(stmt)
    existing = await _fetch_by_request_id(session, row_values["request_id"])
    if existing is None:
        raise RuntimeError("upsert: post-insert lookup failed")
    return existing


async def _fetch_by_request_id(session: AsyncSession, request_id: str) -> CostRecordRow | None:
    from sqlalchemy import select

    result = await session.execute(
        select(CostRecordRow).where(CostRecordRow.request_id == request_id)
    )
    return result.scalar_one_or_none()
