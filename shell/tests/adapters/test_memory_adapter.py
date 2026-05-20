"""ShellMemoryAdapter contract tests — test-strategy §4.2.

SHELL-T-ADAPT-CONTRACT-05: promote_entries() calls Memory.promote_task_entries()
SHELL-T-ADAPT-CONTRACT-06: promote_entries() passes workspace_id and task_signature
"""

from __future__ import annotations

import pytest

from api.adapters.memory_adapter import ShellMemoryAdapter
from tests.conftest import FakeMemoryFacade


@pytest.fixture
def memory_adapter(fake_memory: FakeMemoryFacade) -> ShellMemoryAdapter:
    return ShellMemoryAdapter(memory=fake_memory)


class TestShellMemoryAdapterContract:
    """C-4 adapter contract verification."""

    @pytest.mark.shell_adapt
    @pytest.mark.critical
    async def test_adapt_contract_05_calls_promote_task_entries(
        self, memory_adapter: ShellMemoryAdapter, fake_memory: FakeMemoryFacade
    ):
        """SHELL-T-ADAPT-CONTRACT-05: promote_entries() calls Memory.promote_task_entries()."""
        await memory_adapter.promote_entries(
            workspace_id="ws-test-1",
            session_id="sess-123",
            task_signature="strategic_analysis_q4",
        )

        assert len(fake_memory.promote_calls) == 1
        call = fake_memory.promote_calls[0]
        assert call["workspace_id"] == "ws-test-1"
        assert call["task_signature"] == "strategic_analysis_q4"
        assert call["confirmation_source"] == "session:sess-123"

    @pytest.mark.shell_adapt
    @pytest.mark.critical
    async def test_adapt_contract_06_passes_workspace_and_signature(
        self, memory_adapter: ShellMemoryAdapter, fake_memory: FakeMemoryFacade
    ):
        """SHELL-T-ADAPT-CONTRACT-06: passes workspace_id and task_signature."""
        ws = "ws-enterprise-42"
        sig = "pricing_strategy_2026q2"

        await memory_adapter.promote_entries(
            workspace_id=ws,
            session_id="sess-456",
            task_signature=sig,
        )

        assert len(fake_memory.promote_calls) == 1
        call = fake_memory.promote_calls[0]
        assert call["workspace_id"] == ws
        assert call["task_signature"] == sig

    @pytest.mark.shell_adapt
    async def test_confirmation_source_format(
        self, memory_adapter: ShellMemoryAdapter, fake_memory: FakeMemoryFacade
    ):
        """Confirmation source follows 'session:{session_id}' format per arch §10.3."""
        await memory_adapter.promote_entries(
            workspace_id="ws-1",
            session_id="01HXYZ_SESSION",
            task_signature="test_sig",
        )

        call = fake_memory.promote_calls[0]
        assert call["confirmation_source"].startswith("session:")
        assert "01HXYZ_SESSION" in call["confirmation_source"]

    @pytest.mark.shell_adapt
    async def test_multiple_promotions_tracked(
        self, memory_adapter: ShellMemoryAdapter, fake_memory: FakeMemoryFacade
    ):
        """Multiple promote_entries calls are all recorded."""
        for i in range(3):
            await memory_adapter.promote_entries(
                workspace_id=f"ws-{i}",
                session_id=f"sess-{i}",
                task_signature=f"sig-{i}",
            )

        assert len(fake_memory.promote_calls) == 3
