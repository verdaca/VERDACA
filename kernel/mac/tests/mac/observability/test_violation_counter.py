"""Violation counter tests — mac/test-strategy.md v0.3 §9.3 (S-Q2 bake-in).

Covers MAC-T-OBS-VIOLATION-01..04. The counter increments UNCONDITIONALLY
on :class:`LabelRegistryError`, reset by autouse fixture between tests.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.observability.counters import MacCounters
from praxis.kernel.mac.observability.emitter import (
    LabelRegistryError,
    MacTelemetryEmitter,
    VIOLATIONS_COUNTER,
)


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_violation_01_counter_increments_on_hard_fail() -> None:
    """MAC-T-OBS-VIOLATION-01 — a single hard-fail increments the counter by 1.

    Autouse ResetCounterFixture guarantees the counter starts at 0.
    """
    assert MacCounters.get(VIOLATIONS_COUNTER) == 0

    emitter = MacTelemetryEmitter()
    with pytest.raises(LabelRegistryError):
        emitter.emit(
            metric_name="mac.cycle.completed",
            metric_type="counter",
            value=1.0,
            labels={"bad_key": "x"},
        )

    assert MacCounters.get(VIOLATIONS_COUNTER) == 1


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_violation_02_reset_counter_fixture_clears_between_tests() -> None:
    """MAC-T-OBS-VIOLATION-02 — the autouse fixture clears the counter.

    If this test runs AFTER ``test_mac_t_obs_violation_01`` (which
    leaves counter == 1), the autouse reset fixture should have
    brought it back to 0 by the time this test begins. If the fixture
    doesn't fire, the counter is stale and this test fails.
    """
    assert MacCounters.get(VIOLATIONS_COUNTER) == 0


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_violation_03_counter_is_unconditional_not_bypassed() -> None:
    """MAC-T-OBS-VIOLATION-03 — the counter increment is NOT inside a
    try/except path that can be bypassed. Even when the caller catches
    :class:`LabelRegistryError`, the counter still reflects the violation.
    """
    emitter = MacTelemetryEmitter()

    # Caller catches — the counter should STILL increment.
    try:
        emitter.emit(
            metric_name="mac.cycle.completed",
            metric_type="counter",
            value=1.0,
            labels={"unknown_key_a": "x"},
        )
    except LabelRegistryError:
        pass

    assert MacCounters.get(VIOLATIONS_COUNTER) == 1

    # Second violation.
    try:
        emitter.emit(
            metric_name="mac.cycle.completed",
            metric_type="counter",
            value=1.0,
            labels={"unknown_key_b": "y"},
        )
    except LabelRegistryError:
        pass

    assert MacCounters.get(VIOLATIONS_COUNTER) == 2


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_violation_04_counter_unit_is_process_lifetime() -> None:
    """MAC-T-OBS-VIOLATION-04 — the counter is process-wide (not per-emitter).

    Two distinct MacTelemetryEmitter instances increment the same
    counter. The counter unit is ``violations per process lifetime``.
    """
    emitter_a = MacTelemetryEmitter()
    emitter_b = MacTelemetryEmitter()

    for e in (emitter_a, emitter_b):
        try:
            e.emit(
                metric_name="mac.cycle.completed",
                metric_type="counter",
                value=1.0,
                labels={"bogus": "x"},
            )
        except LabelRegistryError:
            pass

    assert MacCounters.get(VIOLATIONS_COUNTER) == 2
