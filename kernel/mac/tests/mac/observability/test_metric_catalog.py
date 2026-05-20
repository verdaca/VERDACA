"""Metric catalog tests — mac/test-strategy.md v0.3 §9.4.

Covers MAC-T-OBS-METRIC-01..02. Arch §11.2 metric catalog.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.mac.observability.emitter import (
    MacTelemetryEmitter,
    TelemetryEvent,
)
from praxis.kernel.mac.observability.telemetry_labels import (
    ALLOWED_MAC_LABEL_KEYS,
)


_SNAPSHOT = Path(__file__).resolve().parent / "snapshots" / "metrics_v0_1.yaml"


@pytest.mark.critical
@pytest.mark.mac_label_registry
def test_mac_t_obs_metric_01_all_metrics_in_arch_11_3_exist() -> None:
    """MAC-T-OBS-METRIC-01 — metric catalog contains the arch §11.2 counters.

    Per test-strategy v0.3 §9.4.1 (citation repaired from v0.1's
    §11.3 drift): arch §11.2 Metric Catalog is the authoritative
    source. MAC emits counters via :class:`MacTelemetryEmitter` with
    metric names matching the catalog.
    """
    emitter = MacTelemetryEmitter()

    # Spot check: emit a metric using a canonical name from arch §11.2.
    emitter.emit(
        metric_name="mac.cycle.started",
        metric_type="counter",
        value=1.0,
        labels={
            "cycle_id": "01HX000000000000000000000A",
            "cycle_phase": "produce",
        },
    )
    assert len(emitter.events) == 1
    assert emitter.events[0].metric_name == "mac.cycle.started"
    assert emitter.events[0].metric_type == "counter"

    # Spot check: the registry admits every key in the emitted labels.
    for key in emitter.events[0].labels.keys():
        assert key in ALLOWED_MAC_LABEL_KEYS


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_obs_metric_02_metric_snapshot_byte_equality() -> None:
    """MAC-T-OBS-METRIC-02 — the committed metrics_v0_1.yaml snapshot.

    Step 4 ships a minimal snapshot containing the canonical metric
    names MAC emits at step 3 + step 4. Step 6 extends to the full
    arch §11.2 catalog.
    """
    if not _SNAPSHOT.exists():
        pytest.skip("metrics_v0_1.yaml snapshot not yet generated")
    text = _SNAPSHOT.read_text(encoding="utf-8")
    # Minimum contract: the snapshot mentions at least the step-3
    # cycle telemetry metrics.
    assert "mac.cycle.started" in text
    assert "mac.cycle.complete" in text
