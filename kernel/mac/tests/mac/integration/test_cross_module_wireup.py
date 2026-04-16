"""Cross-module wire-up tests — mac/test-strategy.md v0.3 §6.4A.

Covers ``MAC-T-INT-WIREUP-01/02``. WIREUP-03 (``Bootstrap-then-cycle
ordering``) is deferred to step 6 per the corrected distribution table
from the preload report §5 (WIREUP-03 requires the bootstrap loader to
exist, which lands in step 6 §8).

Anchors:
  - mac/architecture.md §2.2 Public Surface
  - mac/architecture.md §5 3-Cycle Iteration Controller
  - mac/architecture.md §10 Integration Contracts
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from praxis.kernel.mac.budget import DEFAULT_MAC_BUDGET
from praxis.kernel.mac.cycle import CycleScenario, IterationController, State
from praxis.kernel.mac.integrations.pi_mono import FakeCostTracker, MacCostHook
from praxis.kernel.mac.integrations.runtime import (
    AgentRole,
    FakeAgentSpawner,
    FakeOutbox,
    MacPathBEmitter,
    MacRuntimeAdapter,
)
from praxis.kernel.mac.testing.fakes.frozen_clock import FrozenClock


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_wireup_01_full_pipeline_smoke_test() -> None:
    """MAC-T-INT-WIREUP-01 — full pipeline smoke test.

    Stand up a MAC pipeline with all step-3 integrations wired:

      - :class:`IterationController` with a :class:`FrozenClock` + Path B emitter
      - :class:`MacRuntimeAdapter` with a :class:`FakeAgentSpawner`
      - :class:`MacCostHook` with a :class:`FakeCostTracker`

    Run a complete normal-path deliberation and assert:
      1. The controller reaches ``State.COMPLETE``.
      2. The spawn log recorded producer + reviewer spawns with correct roles.
      3. The cost tracker recorded cost events for each phase.
      4. The Path B outbox recorded the full arch §5.2 state progression.
    """
    # Wire up all integrations.
    clock = FrozenClock(initial=datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc))
    outbox = FakeOutbox()
    emitter = MacPathBEmitter(outbox=outbox)
    spawner = FakeAgentSpawner()
    runtime_adapter = MacRuntimeAdapter(
        spawner=spawner,
        shape_guard=lambda: None,
        tenant_id="smoke-test-tenant",
    )
    cost_tracker = FakeCostTracker()
    cost_hook = MacCostHook(cost_tracker=cost_tracker)

    # Simulate the cross-module wire-up a real Stage 5.3 caller would do:
    #  - shape guard runs at boot
    runtime_adapter.verify_mcp_sdk_shape()

    #  - producer + reviewer spawn through the adapter
    await runtime_adapter.spawn_producer(
        agent_id="mac-producer", budget=DEFAULT_MAC_BUDGET
    )
    await runtime_adapter.spawn_reviewer(
        agent_id="mac-reviewer-0", budget=DEFAULT_MAC_BUDGET
    )

    #  - a cost event per simulated LLM call
    for phase, seq, cost in (
        ("produce", 0, 0.50),
        ("review", 0, 0.30),
    ):
        await cost_hook.emit_cycle_cost(
            cycle_id="01HX000000000000000000000A",
            cycle_phase=phase,
            call_seq=seq,
            model="claude-opus-4-6",
            prompt_tokens=1000,
            completion_tokens=500,
            usd_cost=cost,
        )

    #  - the iteration controller walks the state machine
    ctrl = IterationController(clock=clock, path_b_emitter=emitter)
    raw_good = {f"R{n}": 4 for n in range(1, 13)}
    result = await ctrl.run(CycleScenario(cycle_1_raw_scores=raw_good))

    # Controller terminates in COMPLETE.
    assert result.final_state == State.COMPLETE

    # Spawn log has 2 entries in correct role order.
    assert len(spawner.spawn_log) == 2
    assert spawner.spawn_log[0][1] == AgentRole.PRODUCER
    assert spawner.spawn_log[1][1] == AgentRole.REVIEWER

    # Cost tracker has 2 events with total 0.80.
    assert len(cost_tracker.events) == 2
    assert cost_tracker.total_cost_usd == pytest.approx(0.80)

    # Path B outbox recorded the full arch §5.2 normal-path sequence.
    event_types = [key.split(":")[2] for key in outbox.dedup_keys]
    assert event_types == [
        "mac.cycle.started",
        "mac.cycle.cycle_1_produce_entered",
        "mac.cycle.cycle_2_review_entered",
        "mac.cycle.cycle_3_verify_entered",
        "mac.cycle.publish_entered",
        "mac.cycle.complete",
    ]


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_int_wireup_02_multi_tenant_isolation() -> None:
    """MAC-T-INT-WIREUP-02 — multi-tenant isolation.

    Two :class:`MacRuntimeAdapter` instances with different ``tenant_id``
    values emit spawn events to distinct tenant namespaces. The shared
    :class:`FakeAgentSpawner` receives calls from both but the
    ``tenant_id`` field on each entry is preserved. This is the
    adapter-level isolation contract — the real Memory deployment
    manifest at step 6 enforces the database-level isolation.
    """
    shared_spawner = FakeAgentSpawner()
    adapter_a = MacRuntimeAdapter(
        spawner=shared_spawner,
        shape_guard=lambda: None,
        tenant_id="tenant-a",
    )
    adapter_b = MacRuntimeAdapter(
        spawner=shared_spawner,
        shape_guard=lambda: None,
        tenant_id="tenant-b",
    )

    await adapter_a.spawn_producer(agent_id="producer-a", budget=DEFAULT_MAC_BUDGET)
    await adapter_b.spawn_producer(agent_id="producer-b", budget=DEFAULT_MAC_BUDGET)
    await adapter_a.spawn_reviewer(agent_id="reviewer-a", budget=DEFAULT_MAC_BUDGET)
    await adapter_b.spawn_reviewer(agent_id="reviewer-b", budget=DEFAULT_MAC_BUDGET)

    # Four spawn entries, two per tenant.
    tenant_a_entries = [e for e in shared_spawner.spawn_log if e[2] == "tenant-a"]
    tenant_b_entries = [e for e in shared_spawner.spawn_log if e[2] == "tenant-b"]
    assert len(tenant_a_entries) == 2
    assert len(tenant_b_entries) == 2

    # No cross-contamination: tenant-a's agent IDs never appear with tenant-b.
    for entry in tenant_a_entries:
        assert entry[0].endswith("-a")
    for entry in tenant_b_entries:
        assert entry[0].endswith("-b")
