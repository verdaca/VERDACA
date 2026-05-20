"""Database models and session factory — arch §12.2.

SQLAlchemy 2.0 async models for workspaces and sessions tables.

Binding anchors:
  - shell/architecture.md §12.2 Database Schema (Postgres)
  - shell/architecture.md §9 Multi-Tenant Isolation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String, ForeignKey("workspaces.id"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    depth: Mapped[str] = mapped_column(
        String, nullable=False
    )
    rendering_mode: Mapped[str] = mapped_column(
        String, nullable=False, default="position_to_hold"
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    result_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint("depth IN ('quick', 'deep')", name="ck_session_depth"),
        Index("idx_sessions_workspace", "workspace_id"),
        Index("idx_sessions_status", "workspace_id", "status"),
    )


def create_engine(database_url: str):
    return create_async_engine(database_url, echo=False)


def create_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
