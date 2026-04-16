"""emit_metric — runtime telemetry emission entry point.

Accepts a RuntimeTelemetryEnvelope, converts it to a TelemetryEvent
via to_telemetry_event() (which enforces R53 via Pydantic's extra='forbid'),
then routes to the configured sinks.

Architecture §6.5 / §10.4.  Sink wiring is deployment-time configuration;
default is tenant_local only (central sink is opt-in).
"""

from __future__ import annotations

from praxis.kernel.runtime.observability.envelope import RuntimeTelemetryEnvelope
from praxis.kernel.runtime.observability.sinks.tenant_local import TenantLocalSink

_default_sink = TenantLocalSink()


def emit_metric(envelope: RuntimeTelemetryEnvelope) -> None:
    """Emit a telemetry event to the configured sinks.

    R53 enforcement fires at this point: ``envelope.to_telemetry_event()``
    constructs a frozen Pydantic model with ``extra='forbid'``.  Any
    forbidden field raises ValidationError before the event reaches the sink.
    """
    event = envelope.to_telemetry_event()
    _default_sink.emit(event)


__all__ = ["emit_metric"]
