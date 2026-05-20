"""Dedup namespace tests — mac/test-strategy.md v0.3 §9.2.

Covers MAC-T-OBS-DEDUP-01..03. Distinct from the §4.6A cycle-level
dedup tests (which run against MacPathBEmitter from step 3) — these
§9.2 tests are observability-layer dedup-key format checks.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.integrations.runtime import FakeOutbox, MacPathBEmitter


@pytest.mark.critical
@pytest.mark.mac_label_registry
@pytest.mark.asyncio
async def test_mac_t_obs_dedup_01_key_format() -> None:
    """MAC-T-OBS-DEDUP-01 — dedup_key format: mac:{cycle_id}:{event_type}:{seq:05d}."""
    outbox = FakeOutbox()
    emitter = MacPathBEmitter(outbox=outbox)

    key = await emitter.emit(
        cycle_id="01HX000000000000000000000A",
        event_type="gate_pass",
        payload={"gate_id": "R1"},
    )

    # Format: mac:{cycle_id}:{event_type}:{seq}
    parts = key.split(":")
    assert len(parts) == 4
    assert parts[0] == "mac"
    assert parts[1] == "01HX000000000000000000000A"
    assert parts[2] == "gate_pass"
    assert parts[3] == "00000"


@pytest.mark.critical
@pytest.mark.mac_label_registry
@pytest.mark.asyncio
async def test_mac_t_obs_dedup_02_monotonic_seq_increments_per_cycle() -> None:
    """MAC-T-OBS-DEDUP-02 — seq counter increments monotonically per cycle_id."""
    outbox = FakeOutbox()
    emitter = MacPathBEmitter(outbox=outbox)

    for i in range(5):
        await emitter.emit(
            cycle_id="01HX000000000000000000000A",
            event_type="gate_pass",
            payload={"gate_id": f"R{i+1}"},
        )

    seqs = [int(k.split(":")[3]) for k in outbox.dedup_keys]
    assert seqs == [0, 1, 2, 3, 4]


@pytest.mark.critical
@pytest.mark.mac_label_registry
@pytest.mark.asyncio
async def test_mac_t_obs_dedup_03_no_cross_cycle_collisions() -> None:
    """MAC-T-OBS-DEDUP-03 — different cycle_ids produce disjoint key spaces."""
    outbox = FakeOutbox()
    emitter = MacPathBEmitter(outbox=outbox)

    # Two different cycles, both emitting 3 events each.
    for cycle in ("01HXAAAA", "01HXBBBB"):
        for i in range(3):
            await emitter.emit(
                cycle_id=cycle,
                event_type="gate_pass",
                payload={},
            )

    # All 6 dedup keys are unique.
    assert len(set(outbox.dedup_keys)) == 6
    # Per-cycle seqs both start at 0.
    cycle_a_seqs = [
        int(k.split(":")[3]) for k in outbox.dedup_keys if "01HXAAAA" in k
    ]
    cycle_b_seqs = [
        int(k.split(":")[3]) for k in outbox.dedup_keys if "01HXBBBB" in k
    ]
    assert cycle_a_seqs == [0, 1, 2]
    assert cycle_b_seqs == [0, 1, 2]
