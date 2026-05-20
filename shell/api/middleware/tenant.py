"""TenantScopedSession — arch §9.1.

Wraps SQLAlchemy AsyncSession to inject workspace_id filter
on every query. Direct table access bypassing this wrapper
is forbidden — enforced by test coverage.

Binding anchors:
  - shell/architecture.md §9.1 Query Layer Enforcement
  - shell/architecture.md §9.2 Isolation Rules
  - shell/architecture.md §9.3 Cross-Workspace Prevention
"""

from __future__ import annotations

from typing import Any, Sequence, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T", bound=DeclarativeBase)


class TenantScopedSession:
    """Wraps SQLAlchemy AsyncSession to inject workspace_id filter
    on every query. Direct table access bypassing this wrapper
    is forbidden — enforced by test coverage."""

    def __init__(self, session: AsyncSession, workspace_id: str) -> None:
        self._session = session
        self._workspace_id = workspace_id

    @property
    def workspace_id(self) -> str:
        return self._workspace_id

    async def query(self, model: type[T], **filters: Any) -> Sequence[T]:
        """Query with automatic workspace_id injection."""
        stmt = select(model).filter_by(
            workspace_id=self._workspace_id,
            **filters,
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get(self, model: type[T], id: str) -> T | None:
        """Get a single record by ID, scoped to workspace."""
        results = await self.query(model, id=id)
        return results[0] if results else None

    async def add(self, instance: Any) -> None:
        """Add an instance (must already have workspace_id set)."""
        if hasattr(instance, "workspace_id"):
            if instance.workspace_id != self._workspace_id:
                raise ValueError(
                    f"Cannot add record for workspace {instance.workspace_id!r} "
                    f"via session scoped to {self._workspace_id!r}"
                )
        self._session.add(instance)

    async def commit(self) -> None:
        await self._session.commit()

    async def refresh(self, instance: Any) -> None:
        await self._session.refresh(instance)

    async def flush(self) -> None:
        await self._session.flush()

    async def count(self, model: type[T], **filters: Any) -> int:
        """Count records matching filters, scoped to workspace."""
        from sqlalchemy import func
        stmt = (
            select(func.count())
            .select_from(model)
            .filter_by(workspace_id=self._workspace_id, **filters)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
