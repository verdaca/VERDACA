"""Tenant isolation tests — test-strategy §4.5.

SHELL-T-TENANT-UNIT-01: TenantScopedSession injects workspace_id on every query
SHELL-T-TENANT-UNIT-02: Direct session query without TenantScopedSession → test rejects

Note: integration tests (SHELL-T-TENANT-INT-01..03) require DB and are in the
integration test suite. These unit tests verify the TenantScopedSession API
behavior using mocks.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.middleware.tenant import TenantScopedSession


class TestTenantScopedSessionUnit:
    """Unit tests for TenantScopedSession."""

    @pytest.mark.shell_tenant
    @pytest.mark.critical
    def test_tenant_unit_01_workspace_id_injection(self):
        """SHELL-T-TENANT-UNIT-01: TenantScopedSession stores workspace_id."""
        mock_session = MagicMock()
        scoped = TenantScopedSession(session=mock_session, workspace_id="ws-abc")
        assert scoped.workspace_id == "ws-abc"

    @pytest.mark.shell_tenant
    @pytest.mark.critical
    async def test_tenant_unit_01_add_rejects_wrong_workspace(self):
        """SHELL-T-TENANT-UNIT-01: add() rejects records with wrong workspace_id."""
        mock_session = MagicMock()
        scoped = TenantScopedSession(session=mock_session, workspace_id="ws-abc")

        class FakeRecord:
            workspace_id = "ws-xyz"

        with pytest.raises(ValueError, match="Cannot add record"):
            await scoped.add(FakeRecord())

    @pytest.mark.shell_tenant
    @pytest.mark.critical
    async def test_tenant_unit_01_add_accepts_correct_workspace(self):
        """SHELL-T-TENANT-UNIT-01: add() accepts records with matching workspace_id."""
        mock_session = MagicMock()
        scoped = TenantScopedSession(session=mock_session, workspace_id="ws-abc")

        class FakeRecord:
            workspace_id = "ws-abc"

        await scoped.add(FakeRecord())
        mock_session.add.assert_called_once()

    @pytest.mark.shell_tenant
    @pytest.mark.critical
    def test_tenant_unit_02_direct_access_rejected(self):
        """SHELL-T-TENANT-UNIT-02: Direct session access is NOT exposed.

        TenantScopedSession wraps AsyncSession. The underlying session
        should not be publicly accessible — callers must use query()/get().
        """
        mock_session = MagicMock()
        scoped = TenantScopedSession(session=mock_session, workspace_id="ws-abc")

        # _session is private (convention)
        assert not hasattr(scoped, "session"), (
            "TenantScopedSession must not expose raw 'session' attribute"
        )
        # But _session exists for internal use
        assert hasattr(scoped, "_session")

    @pytest.mark.shell_tenant
    async def test_commit_delegates(self):
        """commit() delegates to underlying session."""
        mock_session = AsyncMock()
        scoped = TenantScopedSession(session=mock_session, workspace_id="ws-1")
        await scoped.commit()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.shell_tenant
    async def test_flush_delegates(self):
        """flush() delegates to underlying session."""
        mock_session = AsyncMock()
        scoped = TenantScopedSession(session=mock_session, workspace_id="ws-1")
        await scoped.flush()
        mock_session.flush.assert_awaited_once()
