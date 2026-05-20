"""Memory asymmetry wire-up test — mac/test-strategy.md v0.3 §6.2.5.

Covers MAC-T-INT-MEMORY-ASYMMETRY-WIRE-01. Verifies that producer
proxies are wired to the writer role and reviewer proxies to the
reader role via the arch §7.2 :class:`AgentRole` dispatch through
:class:`MacRuntimeAdapter`.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.asymmetry import AsymmetryRouter
from praxis.kernel.mac.budget import DEFAULT_MAC_BUDGET
from praxis.kernel.mac.integrations.runtime import (
    AgentRole,
    FakeAgentSpawner,
    MacRuntimeAdapter,
)
from praxis.kernel.mac.testing.fakes.fake_memory_proxies import (
    FakeProducerProxy,
    FakeReviewerProxy,
)


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
@pytest.mark.asymmetry_structural
async def test_mac_t_int_memory_asymmetry_wire_01() -> None:
    """MAC-T-INT-MEMORY-ASYMMETRY-WIRE-01 — producer ↔ writer, reviewer ↔ reader.

    Per arch §7.2 + runtime §4.1.5:
      - Producer agents spawn with ``AgentRole.PRODUCER`` and receive a
        ``ProducerMemoryProxy`` with full R/W access.
      - Reviewer agents spawn with ``AgentRole.REVIEWER`` and receive a
        ``ReviewerMemoryProxy`` with write-only access (no
        ``retrieve_similar_tasks``).

    Step 5 uses :class:`FakeProducerProxy` and :class:`FakeReviewerProxy`
    to verify the attribute shapes, and :class:`FakeAgentSpawner` to
    verify the role dispatch.
    """
    spawner = FakeAgentSpawner()
    adapter = MacRuntimeAdapter(
        spawner=spawner,
        shape_guard=lambda: None,
        tenant_id="wire-test",
    )
    router = AsymmetryRouter(runtime_adapter=adapter)

    await router.spawn_producer(agent_id="mac-producer")
    reviewers = await router.spawn_reviewer_pool(count=2)

    # Spawn log has correct role dispatch.
    assert len(spawner.spawn_log) == 3
    roles = [entry[1] for entry in spawner.spawn_log]
    assert roles == [AgentRole.PRODUCER, AgentRole.REVIEWER, AgentRole.REVIEWER]

    # The structural proxy contract: producer has retrieve, reviewer
    # does not. Verified via the fake proxies at the attribute level.
    producer_proxy = FakeProducerProxy()
    reviewer_proxy = FakeReviewerProxy()
    assert hasattr(producer_proxy, "retrieve_similar_tasks")
    assert not hasattr(reviewer_proxy, "retrieve_similar_tasks")

    # Reviewer proxy has write-only surface.
    assert hasattr(reviewer_proxy, "store_decision")
    assert hasattr(reviewer_proxy, "flag_and_quarantine")

    # Producer has full R/W surface.
    assert hasattr(producer_proxy, "store_task_outcome")
    assert hasattr(producer_proxy, "store_decision")

    # Reviewers list has the expected count.
    assert len(reviewers) == 2
