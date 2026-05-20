"""Tenant-local telemetry sink — emits the full TelemetryEvent.

All seven ALLOWED_FIELDS are written to the tenant-local telemetry
backend (e.g., a local log or Prometheus push-gateway scoped to the
deployment).  No field projection: every allowed field flows through.

Architecture §6.5.C / §10.4.2.
"""

from __future__ import annotations

import logging

from praxis.kernel.memory.telemetry import TelemetryEvent

_log = logging.getLogger(__name__)


class TenantLocalSink:
    """Write full TelemetryEvent to tenant-local telemetry (stub)."""

    def emit(self, event: TelemetryEvent) -> None:
        """Emit the event.  Currently logs at DEBUG level (Stage 4 stub)."""
        _log.debug(
            "telemetry: %s %s=%s labels=%s",
            event.metric_name,
            event.metric_type,
            event.value,
            event.labels,
        )


__all__ = ["TenantLocalSink"]
