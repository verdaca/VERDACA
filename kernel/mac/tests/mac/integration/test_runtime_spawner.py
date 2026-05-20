"""Runtime spawner integration tests — mac/test-strategy.md v0.3 §6.3.1.

Covers ``MAC-T-INT-RUNTIME-SPAWNER-01``. Verifies that
:class:`MacRuntimeAdapter` routes every spawn through the
:class:`AgentRole` dispatch — producers get ``AgentRole.PRODUCER``,
reviewers get ``AgentRole.REVIEWER``. No direct proxy imports allowed.

Anchors:
  - mac/architecture.md §7.2 Binding to Runtime §4.1 Proxies
  - mac/architecture.md §10.3 Runtime Integration
  - runtime/architecture.md §4.1.5 _construct_memory_proxy (single-point)
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.budget import DEFAULT_MAC_BUDGET
from praxis.kernel.mac.integrations.runtime import (
    AgentRole,
    FakeAgentSpawner,
    MacRuntimeAdapter,
)


def _noop_shape_guard() -> None:
    return None


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_runtime_spawner_01_respects_mac_role_dispatch() -> None:
    """MAC-T-INT-RUNTIME-SPAWNER-01 — Runtime spawner respects MAC role.

    ``MacRuntimeAdapter.spawn_producer`` calls ``AgentSpawner.spawn`` with
    ``role=AgentRole.PRODUCER``, and ``spawn_reviewer`` calls it with
    ``role=AgentRole.REVIEWER``. No other role values are emitted. The
    test captures the spawn log on the FakeAgentSpawner and asserts the
    dispatch shape.

    This is the step-3 counterpart to arch §7.2's "MAC NEVER directly
    imports ProducerMemoryProxy or ReviewerMemoryProxy" invariant —
    step 5 adds the grep test that enforces it structurally, but step 3
    already establishes the behavioral contract.
    """
    spawner = FakeAgentSpawner()
    adapter = MacRuntimeAdapter(
        spawner=spawner,
        shape_guard=_noop_shape_guard,
        tenant_id="test-tenant",
    )

    await adapter.spawn_producer(agent_id="mac-producer", budget=DEFAULT_MAC_BUDGET)
    await adapter.spawn_reviewer(agent_id="mac-reviewer-1", budget=DEFAULT_MAC_BUDGET)
    await adapter.spawn_reviewer(agent_id="mac-reviewer-2", budget=DEFAULT_MAC_BUDGET)

    # 3 spawn calls captured.
    assert len(spawner.spawn_log) == 3

    # Role dispatch is exact.
    roles = [entry[1] for entry in spawner.spawn_log]
    assert roles == [AgentRole.PRODUCER, AgentRole.REVIEWER, AgentRole.REVIEWER]

    # Tenant ID propagates to every spawn.
    tenant_ids = [entry[2] for entry in spawner.spawn_log]
    assert all(t == "test-tenant" for t in tenant_ids)
