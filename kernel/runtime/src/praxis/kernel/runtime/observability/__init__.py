"""Praxis Runtime observability — Q3 option (b) structural binding.

TelemetryEvent is IMPORTED from praxis.kernel.memory.telemetry and
re-exported here.  Stage 4 does NOT define its own TelemetryEvent.

The is-identity test in test_telemetry_event_import_identity.py verifies:
  praxis.kernel.runtime.observability.TelemetryEvent is
  praxis.kernel.memory.telemetry.TelemetryEvent

  (same object, not just same type — structural proof of single-source-of-truth)
"""

from praxis.kernel.memory.telemetry import TelemetryEvent  # re-export, NOT redefinition
from praxis.kernel.runtime.observability.emit import emit_metric
from praxis.kernel.runtime.observability.envelope import RuntimeTelemetryEnvelope

__all__ = [
    "TelemetryEvent",
    "RuntimeTelemetryEnvelope",
    "emit_metric",
]
