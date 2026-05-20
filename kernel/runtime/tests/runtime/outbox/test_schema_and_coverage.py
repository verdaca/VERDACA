"""Coverage tests for outbox/schema.py and outbox/drain_loop edge cases."""

from __future__ import annotations

import pytest


def test_outbox_schema_exports_event_row() -> None:
    """outbox/schema.py re-exports EventRow from Pi-Mono."""
    from praxis.kernel.runtime.outbox.schema import EventRow

    assert EventRow.__tablename__ == "events_outbox"


def test_outbox_schema_event_row_is_pi_mono_class() -> None:
    """The re-exported EventRow is identical to Pi-Mono's original."""
    from praxis.kernel.cost.storage.schema import EventRow as PiMonoEventRow
    from praxis.kernel.runtime.outbox.schema import EventRow as RuntimeEventRow

    assert RuntimeEventRow is PiMonoEventRow


@pytest.mark.asyncio
async def test_drain_once_returns_zero_for_empty_buffer() -> None:
    """drain_once with empty buffer returns 0 drained events."""
    from unittest.mock import MagicMock

    from praxis.kernel.memory._internal.audit import AuditBuffer
    from praxis.kernel.runtime.outbox.drain_loop import drain_once
    from praxis.kernel.runtime.outbox.path_b import PositionBasedDrainAdapter

    # Use a mock cost_repo — no DB needed when buffer is empty
    mock_repo = MagicMock()

    buf = AuditBuffer()
    adapter = PositionBasedDrainAdapter(buf)

    result = await drain_once(
        cost_repo=mock_repo,
        drain_adapter=adapter,
        manifest_tenant_hash="test-tenant",
    )
    assert result == 0
    # session() should NOT be called when there are no events
    mock_repo.session.assert_not_called()
