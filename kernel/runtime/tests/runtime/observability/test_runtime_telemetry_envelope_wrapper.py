"""RuntimeTelemetryEnvelope wrapper tests — Q3 option (b) structural claims.

Architecture §10.4 / §16.2: RuntimeTelemetryEnvelope is a WRAPPER that
composes TelemetryEvent, not a subclass.  to_telemetry_event() returns
an instance of the imported Memory TelemetryEvent type.

Test-strategy §6.5 (S4.R-05) + §10.4.1b.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from praxis.kernel.memory.telemetry import TelemetryEvent
from praxis.kernel.runtime.observability.envelope import RuntimeTelemetryEnvelope


@pytest.mark.critical
@pytest.mark.r53_structural
class TestRuntimeTelemetryEnvelopeWrapper:
    """§10.4.1b — wrapper composition, not subclass."""

    def test_envelope_composes_not_subclasses(self) -> None:
        """RuntimeTelemetryEnvelope must NOT be a subclass of TelemetryEvent."""
        assert not issubclass(RuntimeTelemetryEnvelope, TelemetryEvent), (
            "RuntimeTelemetryEnvelope is a subclass of TelemetryEvent — "
            "composition required, inheritance forbidden (Q3 option b)."
        )

    def test_envelope_to_telemetry_event_returns_memory_type(self) -> None:
        """to_telemetry_event() returns an instance of Memory's TelemetryEvent."""
        env = RuntimeTelemetryEnvelope(
            metric_name="runtime.test.counter",
            metric_type="counter",
            value=1.0,
            labels={"tenant_hash": "test-hash"},
            tenant_hash="test-hash",
        )
        event = env.to_telemetry_event()
        assert isinstance(event, TelemetryEvent), (
            f"to_telemetry_event() returned {type(event)}, expected TelemetryEvent"
        )

    def test_envelope_for_spawn_factory(self) -> None:
        """for_spawn() classmethod returns a correctly-wired envelope."""
        env = RuntimeTelemetryEnvelope.for_spawn(
            tenant_hash="test-hash",
            agent_name="bmad-agent-architect",
            role="producer",
            mode="subagent",
            duration_ms=123.4,
        )
        event = env.to_telemetry_event()
        assert event.metric_name == "runtime.agent.spawn.duration_ms"
        assert event.metric_type == "histogram"
        assert event.value == 123.4

    def test_envelope_for_tool_call_factory(self) -> None:
        """for_tool_call() classmethod returns a counter envelope."""
        env = RuntimeTelemetryEnvelope.for_tool_call(
            tenant_hash="test-hash",
            tool_name="fs_mcp",
            blast_class="class_a",
        )
        event = env.to_telemetry_event()
        assert "runtime" in event.metric_name
        assert event.metric_type == "counter"

    def test_envelope_for_asymmetry_hit_factory(self) -> None:
        """for_asymmetry_hit() classmethod returns a counter envelope."""
        env = RuntimeTelemetryEnvelope.for_asymmetry_hit(
            tenant_hash="test-hash",
            reviewer_agent_name="quinn",
            filtered_event_type="task_result",
            producer_sender_name="amelia",
        )
        event = env.to_telemetry_event()
        assert event.metric_name == "runtime.asymmetry.bus_filter.hit.count"
        assert event.metric_type == "counter"

    def test_envelope_for_manifest_heartbeat_factory(self) -> None:
        """for_manifest_heartbeat() classmethod returns a gauge envelope."""
        env = RuntimeTelemetryEnvelope.for_manifest_heartbeat(
            tenant_hash="test-hash",
            success_rate=1.0,
        )
        event = env.to_telemetry_event()
        assert event.metric_name == "runtime.manifest.heartbeat.success_rate"
        assert event.metric_type == "gauge"
        assert event.value == 1.0

    def test_to_telemetry_event_is_frozen(self) -> None:
        """The TelemetryEvent returned by to_telemetry_event() is immutable."""
        env = RuntimeTelemetryEnvelope(
            metric_name="runtime.test.gauge",
            metric_type="gauge",
            value=0.5,
            labels={"tenant_hash": "test-hash"},
            tenant_hash="test-hash",
        )
        event = env.to_telemetry_event()
        with pytest.raises((ValidationError, TypeError)):
            event.metric_name = "hostile.rename"  # type: ignore[misc]
