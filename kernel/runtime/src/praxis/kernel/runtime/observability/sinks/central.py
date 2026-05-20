"""Central telemetry sink — field-projected emission.

Only a subset of the ALLOWED_FIELDS is forwarded to the central
observability backend.  This is the §6.5.C defense-in-depth posture:
even an allowlisted field that is sensitive in context is stripped
before crossing the tenant boundary to central infrastructure.

Projected fields (subset of ALLOWED_FIELDS):
  metric_name, metric_type, value, tenant_hash

Architecture §6.5.C / §10.4.2.
"""

from __future__ import annotations

import logging

from praxis.kernel.memory.telemetry import TelemetryEvent

_log = logging.getLogger(__name__)

# Projected fields forwarded to central sink (subset of ALLOWED_FIELDS).
# Labels are stripped — they may contain per-agent data that is tenant-specific.
_CENTRAL_PROJECTED_FIELDS = frozenset({"metric_name", "metric_type", "value", "tenant_hash"})


class CentralSink:
    """Write a field-projected subset to the central telemetry backend (stub)."""

    def emit(self, event: TelemetryEvent) -> None:
        """Project and emit.  Currently logs at DEBUG level (Stage 4 stub)."""
        projected = {
            "metric_name": event.metric_name,
            "metric_type": event.metric_type,
            "value": event.value,
            "tenant_hash": event.tenant_hash,
        }
        _log.debug("central-telemetry: %s", projected)


__all__ = ["CentralSink"]
