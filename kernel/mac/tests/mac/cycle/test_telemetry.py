"""Cycle telemetry tests — mac/test-strategy.md v0.3 §4.6A.

Covers ``MAC-T-CYCLE-TELEMETRY-01/02/03``. Per-cycle Path B event
sequence, dedup-key uniqueness, and monotonic sequence semantics.

Anchors:
  - mac/architecture.md §5.2 state progression (normal path)
  - mac/architecture.md §11.2 Metric Catalog
  - mac/architecture.md §11.3 Linkage to Memory's TelemetryEvent (dedup key format)
  - mac/architecture.md §10.3 SQ-8 dedup namespace (``mac:`` prefix)
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.cycle import CycleScenario, IterationController, State
from praxis.kernel.mac.integrations.runtime import FakeOutbox, MacPathBEmitter


def _good_raw() -> dict[str, int]:
    return {f"R{n}": 4 for n in range(1, 13)}


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
async def test_mac_t_cycle_telemetry_01_per_cycle_event_sequence() -> None:
    """MAC-T-CYCLE-TELEMETRY-01 — per-cycle event sequence on normal path.

    A complete normal-path run emits the arch §5.2 state-progression
    sequence: ``[mac.cycle.started, mac.cycle.cycle_1_produce_entered,
    mac.cycle.cycle_2_review_entered, mac.cycle.cycle_3_verify_entered,
    mac.cycle.publish_entered, mac.cycle.complete]``.

    Strict sequence equality — order matters per test-strategy §4.6A.1.
    """
    outbox = FakeOutbox()
    emitter = MacPathBEmitter(outbox=outbox)
    ctrl = IterationController(path_b_emitter=emitter)

    await ctrl.run(CycleScenario(cycle_1_raw_scores=_good_raw()))

    event_names = [
        key.split(":")[2] if key.startswith("mac:") else ""
        for key in outbox.dedup_keys
    ]
    # The dedup key's event_type segment matches the emit call's event_type.
    expected = [
        "mac.cycle.started",
        "mac.cycle.cycle_1_produce_entered",
        "mac.cycle.cycle_2_review_entered",
        "mac.cycle.cycle_3_verify_entered",
        "mac.cycle.publish_entered",
        "mac.cycle.complete",
    ]
    assert event_names == expected


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_label_registry
async def test_mac_t_cycle_telemetry_02_dedup_keys_unique_within_cycle() -> None:
    """MAC-T-CYCLE-TELEMETRY-02 — every emitted dedup_key is unique.

    Within a single cycle run, all emitted events have distinct
    ``dedup_key`` values. The SQ-8 format guarantees this via the
    per-cycle monotonic sequence counter:
    ``"mac:" + cycle_id + ":" + event_type + ":" + monotonic_seq``.
    """
    outbox = FakeOutbox()
    emitter = MacPathBEmitter(outbox=outbox)
    ctrl = IterationController(path_b_emitter=emitter)

    await ctrl.run(CycleScenario(cycle_1_raw_scores=_good_raw()))

    assert len(outbox.dedup_keys) == len(set(outbox.dedup_keys))
    # SQ-8 prefix holds on every key.
    for key in outbox.dedup_keys:
        assert key.startswith("mac:"), f"SQ-8 mac: prefix missing on {key!r}"


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.mac_label_registry
async def test_mac_t_cycle_telemetry_03_monotonic_seq_is_sequential() -> None:
    """MAC-T-CYCLE-TELEMETRY-03 — monotonic_seq is ``0, 1, 2, ...`` without gaps.

    The ``monotonic_seq`` segment of each dedup key for a single cycle
    forms a gap-free ascending integer sequence per arch §11.3 +
    SQ-8 format.
    """
    outbox = FakeOutbox()
    emitter = MacPathBEmitter(outbox=outbox)
    ctrl = IterationController(path_b_emitter=emitter)

    await ctrl.run(CycleScenario(cycle_1_raw_scores=_good_raw()))

    seqs: list[int] = []
    for key in outbox.dedup_keys:
        # Format: "mac:{cycle_id}:{event_type}:{seq:05d}"
        parts = key.split(":")
        assert len(parts) == 4
        seqs.append(int(parts[3]))

    assert seqs == list(range(len(seqs)))
