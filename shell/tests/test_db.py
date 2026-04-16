"""Database model tests — verify ORM models have correct schema."""

from __future__ import annotations

import pytest

from api.db import Base, Session, Workspace, _utcnow


class TestDatabaseModels:

    def test_workspace_table_name(self):
        assert Workspace.__tablename__ == "workspaces"

    def test_session_table_name(self):
        assert Session.__tablename__ == "sessions"

    def test_workspace_columns(self):
        cols = {c.name for c in Workspace.__table__.columns}
        assert cols == {"id", "name", "stripe_customer_id", "trial_used", "created_at"}

    def test_session_columns(self):
        cols = {c.name for c in Session.__table__.columns}
        expected = {
            "id", "workspace_id", "question", "context", "depth",
            "rendering_mode", "status", "cost_usd", "stripe_payment_intent_id",
            "result_markdown", "result_html", "started_at", "completed_at",
        }
        assert cols == expected

    def test_session_depth_check_constraint(self):
        """Session has CHECK constraint on depth."""
        constraints = [c.name for c in Session.__table__.constraints if hasattr(c, "name") and c.name]
        assert "ck_session_depth" in constraints

    def test_session_indexes(self):
        """Session has workspace and status indexes per arch §12.2."""
        index_names = {idx.name for idx in Session.__table__.indexes}
        assert "idx_sessions_workspace" in index_names
        assert "idx_sessions_status" in index_names

    def test_session_workspace_fk(self):
        """Session.workspace_id has FK to workspaces.id."""
        fks = list(Session.__table__.foreign_keys)
        assert len(fks) == 1
        assert "workspaces.id" in str(fks[0].target_fullname)

    def test_utcnow_returns_utc(self):
        from datetime import timezone
        dt = _utcnow()
        assert dt.tzinfo is not None
        assert dt.tzinfo == timezone.utc

    def test_base_declarative(self):
        """Base is a proper DeclarativeBase."""
        from sqlalchemy.orm import DeclarativeBase
        assert issubclass(Base, DeclarativeBase)

    def test_create_engine_callable(self):
        """create_engine is importable and callable."""
        from api.db import create_engine
        assert callable(create_engine)

    def test_create_session_factory_callable(self):
        """create_session_factory is importable and callable."""
        from api.db import create_session_factory
        assert callable(create_session_factory)
