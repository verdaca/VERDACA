"""Label registry hard-fail tests — mac/test-strategy.md v0.3 §9.1.

Covers MAC-T-OBS-LABEL-REG-01..04. SQ-2 hard-fail discipline enforced
at :class:`MacTelemetryEmitter`.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.observability.counters import MacCounters
from praxis.kernel.mac.observability.emitter import (
    LabelRegistryError,
    MacTelemetryEmitter,
    VIOLATIONS_COUNTER,
)
from praxis.kernel.mac.observability.telemetry_labels import (
    ALLOWED_LABEL_VALUES,
    ALLOWED_MAC_LABEL_KEYS,
    UNBOUNDED_KEYS,
)


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_label_reg_01_registry_loads_with_allowlist() -> None:
    """MAC-T-OBS-LABEL-REG-01 — registry constants are frozen and non-empty."""
    assert isinstance(ALLOWED_MAC_LABEL_KEYS, frozenset)
    assert len(ALLOWED_MAC_LABEL_KEYS) > 0
    assert "cycle_id" in ALLOWED_MAC_LABEL_KEYS
    assert "gate_id" in ALLOWED_MAC_LABEL_KEYS
    assert "R1" in ALLOWED_LABEL_VALUES["gate_id"]
    assert "R12" in ALLOWED_LABEL_VALUES["gate_id"]
    # R13 is NOT in the registry — arch §3.5 deferred per SQ-3.
    assert "R13" not in ALLOWED_LABEL_VALUES["gate_id"]


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_label_reg_02_hard_fail_on_unknown_key() -> None:
    """MAC-T-OBS-LABEL-REG-02 — SQ-2 hard reject on unknown label key.

    Header / placeholder function. The actual body assertions live in
    the sibling function ``test_mac_t_obs_label_reg_02b_hard_fail_unknown_key_raises_and_increments``
    below — this placeholder exists only to anchor the canonical
    MAC-T-OBS-LABEL-REG-02 nodeid for downstream auditing.

    **no_waiver discipline note:** this test is NOT in the ratified
    16-entry ``NO_WAIVER_ALLOWLIST``. Arch §12.2 designates the SQ-2
    label-registry hard-fail *runtime behavior* as non-waivable — that
    is a CODE invariant (the ``LabelRegistryError`` raise path cannot
    be bypassed), NOT a test-marker authority. The 16-entry allow-list
    is the sole authority for ``no_waiver`` markers. Step 5.5
    Alignment Review may add this test if Murat ratifies a v0.4
    amendment; until then it is ``critical + mac_label_registry``,
    NOT ``no_waiver``.
    """


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_label_reg_02b_hard_fail_unknown_key_raises_and_increments() -> None:
    """MAC-T-OBS-LABEL-REG-02 body — unknown label key raises
    LabelRegistryError and increments the violations counter
    unconditionally (SQ-2 + S-Q2 bake-in)."""
    emitter = MacTelemetryEmitter()
    initial = MacCounters.get(VIOLATIONS_COUNTER)

    with pytest.raises(LabelRegistryError, match="unknown label key"):
        emitter.emit(
            metric_name="mac.cycle.completed",
            metric_type="counter",
            value=1.0,
            labels={"nonexistent_key": "x"},
        )

    # Counter incremented BEFORE the raise (not after, not in except).
    assert MacCounters.get(VIOLATIONS_COUNTER) == initial + 1


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_label_reg_03_known_labels_validate_successfully() -> None:
    """MAC-T-OBS-LABEL-REG-03 — known labels with valid values pass."""
    emitter = MacTelemetryEmitter()
    initial = MacCounters.get(VIOLATIONS_COUNTER)

    emitter.emit(
        metric_name="mac.cycle.completed",
        metric_type="counter",
        value=1.0,
        labels={
            "cycle_id": "01HX000000000000000000000A",  # unbounded, ok
            "cycle_phase": "produce",  # bounded, in allowlist
            "gate_id": "R4",  # bounded, R4 in allowlist
            "outcome": "pass",  # bounded, ok
        },
    )

    # Counter NOT incremented on happy path.
    assert MacCounters.get(VIOLATIONS_COUNTER) == initial
    assert len(emitter.events) == 1


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_label_reg_04_registry_is_immutable_at_runtime() -> None:
    """MAC-T-OBS-LABEL-REG-04 — ALLOWED_MAC_LABEL_KEYS is a frozenset."""
    assert isinstance(ALLOWED_MAC_LABEL_KEYS, frozenset)
    assert isinstance(UNBOUNDED_KEYS, frozenset)
    # Attempting to mutate raises.
    with pytest.raises(AttributeError):
        ALLOWED_MAC_LABEL_KEYS.add("new_key")  # type: ignore[attr-defined]


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_label_reg_05_rejects_unknown_value_for_bounded_key() -> None:
    """Supplementary — unknown value for bounded key (``gate_id=R99``)
    raises LabelRegistryError (SQ-2 covers both key and value paths).
    """
    emitter = MacTelemetryEmitter()
    with pytest.raises(LabelRegistryError, match="unknown label value"):
        emitter.emit(
            metric_name="mac.gate.score",
            metric_type="gauge",
            value=4.0,
            labels={"gate_id": "R99"},  # R99 not in {R1..R12}
        )
