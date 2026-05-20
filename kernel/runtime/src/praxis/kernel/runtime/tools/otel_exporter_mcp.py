"""Praxis Runtime — OpenTelemetry Exporter MCP adapter (P0-8, Class A).

THIS IS THE R53 ENFORCEMENT POINT.

Architecture §6.1.8, §9.10, §10.5.
All telemetry emission goes through this module. The R53 field allowlist
is enforced at TelemetryEvent construction time via Pydantic extra='forbid'.

Q3 option (b) structural binding: TelemetryEvent is IMPORTED from
praxis.kernel.memory.telemetry, NOT redefined here. The is-identity
test in test_telemetry_event_import_identity.py enforces this.

S4.R-05 no-waiver: a breach here compromises every other tool's R53.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Q3 option (b): IMPORT, do not redefine. The is-identity guard in
# tests/runtime/observability/test_telemetry_event_import_identity.py
# verifies this is the same object as memory.telemetry.TelemetryEvent.
from praxis.kernel.memory.telemetry import TelemetryEvent  # re-export
from praxis.kernel.runtime.loader.catalog import TOOL_CATALOG
from praxis.kernel.runtime.observability import RuntimeTelemetryEnvelope
from praxis.kernel.runtime.tools._base import ToolDescriptor

DESCRIPTOR: ToolDescriptor = next(t for t in TOOL_CATALOG if t.name == "otel-exporter-mcp")


def build_telemetry_event(
    *,
    metric_name: str,
    metric_type: str,
    value: float,
    labels: dict[str, str],
    praxis_version: str,
    tenant_hash: str,
    **kwargs: Any,  # forbidden extra fields → Pydantic ValidationError
) -> TelemetryEvent:
    """Build a TelemetryEvent with R53 allowlist enforcement.

    Any field not in the 7-field allowlist (metric_name, metric_type, value,
    labels, timestamp, praxis_version, tenant_hash) will raise a Pydantic
    ValidationError at construction time because TelemetryEvent has
    extra='forbid'.

    This is the structural R53 enforcement — not a runtime check, a schema.
    """
    # TelemetryEvent(extra='forbid') raises ValidationError on any extra kwarg.
    # We pass **kwargs through so forbidden fields like query_content, embedding,
    # result_ids will hit the Pydantic gate rather than being silently swallowed.
    return TelemetryEvent(
        metric_name=metric_name,
        metric_type=metric_type,  # type: ignore[arg-type]
        value=value,
        labels=labels,
        timestamp=datetime.now(timezone.utc),
        praxis_version=praxis_version,
        tenant_hash=tenant_hash,
        **kwargs,
    )


class OtelExporterMcpAdapter:
    """OTel exporter MCP adapter — R53 enforcement point."""

    descriptor = DESCRIPTOR

    def emit(
        self,
        envelope: RuntimeTelemetryEnvelope,
    ) -> TelemetryEvent:
        """Emit a telemetry event through the R53 gate.

        Uses RuntimeTelemetryEnvelope.to_telemetry_event() at the emission
        boundary per Q3 option (b) discipline.
        """
        return envelope.to_telemetry_event()


__all__ = [
    "OtelExporterMcpAdapter",
    "DESCRIPTOR",
    "TelemetryEvent",
    "build_telemetry_event",
]
