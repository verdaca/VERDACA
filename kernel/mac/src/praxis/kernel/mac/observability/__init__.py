"""MAC observability layer — arch §11.

Public surface:
  - :class:`LabelRegistryError` raised unconditionally on unknown label key/value
  - :class:`MacTelemetryEmitter` with SQ-2 hard-fail enforcement
  - :class:`MacCounters` process-wide counter registry (``mac.label_registry.violations``)
  - :data:`ALLOWED_MAC_LABEL_KEYS`, :data:`ALLOWED_LABEL_VALUES`, :data:`UNBOUNDED_KEYS`
"""

from __future__ import annotations

from praxis.kernel.mac.observability.counters import MacCounters
from praxis.kernel.mac.observability.emitter import (
    LabelRegistryError,
    MacTelemetryEmitter,
    TelemetryEvent,
)
from praxis.kernel.mac.observability.telemetry_labels import (
    ALLOWED_LABEL_VALUES,
    ALLOWED_MAC_LABEL_KEYS,
    UNBOUNDED_KEYS,
)

__all__ = (
    "ALLOWED_LABEL_VALUES",
    "ALLOWED_MAC_LABEL_KEYS",
    "LabelRegistryError",
    "MacCounters",
    "MacTelemetryEmitter",
    "TelemetryEvent",
    "UNBOUNDED_KEYS",
)
