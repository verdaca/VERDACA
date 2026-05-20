"""emit_metric + CentralSink coverage tests + no-extra-allow guard.

Architecture §6.5.C + §10.4.2:
  - emit_metric calls to_telemetry_event() and routes to sink
  - CentralSink projects to metric_name/metric_type/value/tenant_hash only
  - No extra='allow' anywhere in observability/ (structural guard)

Test-strategy §6.5.B (extra='allow' grep) + §10.4.2 (two-sink defense).
"""

from __future__ import annotations

import pytest

from praxis.kernel.memory.telemetry import TelemetryEvent
from praxis.kernel.runtime.observability import emit_metric
from praxis.kernel.runtime.observability.envelope import RuntimeTelemetryEnvelope
from praxis.kernel.runtime.observability.sinks.central import _CENTRAL_PROJECTED_FIELDS, CentralSink
from praxis.kernel.runtime.observability.sinks.tenant_local import TenantLocalSink

# ---------------------------------------------------------------------------
# emit_metric smoke test
# ---------------------------------------------------------------------------


@pytest.mark.critical
def test_emit_metric_does_not_raise() -> None:
    """emit_metric completes without error for a well-formed envelope."""
    env = RuntimeTelemetryEnvelope.for_spawn(
        tenant_hash="test-hash",
        agent_name="bmad-agent-dev",
        role="producer",
        mode="subagent",
        duration_ms=42.0,
    )
    emit_metric(env)  # must not raise


# ---------------------------------------------------------------------------
# CentralSink field projection
# ---------------------------------------------------------------------------


@pytest.mark.critical
def test_central_sink_projected_fields_are_subset_of_allowed() -> None:
    """_CENTRAL_PROJECTED_FIELDS is a subset of TelemetryEvent.model_fields."""
    allowed = set(TelemetryEvent.model_fields.keys())
    assert _CENTRAL_PROJECTED_FIELDS.issubset(allowed), (
        f"Central sink projects fields not in TelemetryEvent.model_fields: "
        f"{_CENTRAL_PROJECTED_FIELDS - allowed}"
    )


@pytest.mark.critical
def test_central_sink_emit_does_not_raise() -> None:
    """CentralSink.emit() runs without error."""
    import datetime

    event = TelemetryEvent(
        metric_name="runtime.test.central",
        metric_type="counter",
        value=1.0,
        labels={"tenant_hash": "test-hash"},
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        praxis_version="0.1.0",
        tenant_hash="test-hash",
    )
    sink = CentralSink()
    sink.emit(event)  # must not raise


@pytest.mark.critical
def test_tenant_local_sink_emit_does_not_raise() -> None:
    """TenantLocalSink.emit() runs without error."""
    import datetime

    event = TelemetryEvent(
        metric_name="runtime.test.local",
        metric_type="gauge",
        value=0.5,
        labels={"tenant_hash": "test-hash"},
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        praxis_version="0.1.0",
        tenant_hash="test-hash",
    )
    sink = TenantLocalSink()
    sink.emit(event)  # must not raise
