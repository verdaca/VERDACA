"""MAC telemetry emitter — arch §11.1 SQ-2 hard-fail enforcement.

The emitter is the ONLY path MAC events take into the Memory
TelemetryEvent envelope. Every emit runs the SQ-2 label registry check
FIRST. Unknown label keys or values raise :class:`LabelRegistryError`
(subclass of ``ValueError``). The
``mac.label_registry.violations`` counter increments UNCONDITIONALLY
before the raise — not inside try/except, not after. This is the S-Q2
ratified semantics per test-strategy v0.3 §9.3.

**Why unconditional:** the counter is a production observability signal.
If a bug introduces an unregistered label, the counter captures that
fact even in handled-exception paths. Suppressing the increment via
try/except would make the bug invisible to dashboards.

Binding anchors:
  - mac/architecture.md §11.1 Telemetry Label Cardinality Registry (SQ-2)
  - mac/architecture.md §11.3 Linkage to Memory's TelemetryEvent
  - mac/test-strategy.md v0.3 §9.1 LABEL-REG-01..04
  - mac/test-strategy.md v0.3 §9.3 VIOLATION-01..04 (S-Q2)
  - mac/test-strategy.md v0.3 §9.4 METRIC-01..02
"""

from __future__ import annotations

from dataclasses import dataclass, field

from praxis.kernel.mac.observability.counters import MacCounters
from praxis.kernel.mac.observability.telemetry_labels import (
    ALLOWED_LABEL_VALUES,
    ALLOWED_MAC_LABEL_KEYS,
)


VIOLATIONS_COUNTER: str = "mac.label_registry.violations"
"""The arch §11.2 counter name. Increments once per :class:`LabelRegistryError`
raised by the emitter."""


class LabelRegistryError(ValueError):
    """Raised unconditionally on any label key/value not in the SQ-2 registry.

    Subclass of :class:`ValueError` so callers catching ``ValueError``
    still catch this — MAC does NOT want callers to ignore the error
    silently. The increment of :data:`VIOLATIONS_COUNTER` happens
    BEFORE the raise, in the same method, NOT in a try/except.
    """


@dataclass(frozen=True)
class TelemetryEvent:
    """MAC-local mirror of ``praxis.kernel.memory.telemetry.TelemetryEvent``.

    Shape-compatible with the Memory envelope per arch §11.3. Step 6
    rebinds to the Memory canonical type; at step 4 the local mirror
    keeps MAC isolated from the Memory import chain.
    """

    metric_name: str
    metric_type: str  # "counter" | "gauge" | "histogram"
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    tenant_hash: str = ""


class MacTelemetryEmitter:
    """Wraps the Memory TelemetryEvent sink with SQ-2 registry enforcement.

    Every :meth:`emit` call:

      1. Validates each label key against :data:`ALLOWED_MAC_LABEL_KEYS`.
         Unknown key → increment counter, raise LabelRegistryError.
      2. For bounded keys, validates the value against
         :data:`ALLOWED_LABEL_VALUES`. Unknown value → increment counter,
         raise LabelRegistryError.
      3. If validation passes, constructs :class:`TelemetryEvent` and
         dispatches to the injected sink.
    """

    def __init__(self, sink: "TelemetrySink | None" = None) -> None:
        self._sink = sink
        self._events: list[TelemetryEvent] = []

    @property
    def events(self) -> list[TelemetryEvent]:
        return list(self._events)

    def emit(
        self,
        *,
        metric_name: str,
        metric_type: str,
        value: float,
        labels: dict[str, str],
        tenant_hash: str = "",
    ) -> None:
        # SQ-2 hard-fail: validate labels FIRST. On violation, increment
        # the counter unconditionally and THEN raise. This ordering is
        # ratified per test-strategy v0.3 §9.3 S-Q2 bake-in.
        for key, val in labels.items():
            if key not in ALLOWED_MAC_LABEL_KEYS:
                MacCounters.increment(VIOLATIONS_COUNTER)
                raise LabelRegistryError(
                    f"unknown label key: {key!r}"
                )
            if key in ALLOWED_LABEL_VALUES and val not in ALLOWED_LABEL_VALUES[key]:
                MacCounters.increment(VIOLATIONS_COUNTER)
                raise LabelRegistryError(
                    f"unknown label value for {key!r}: {val!r}"
                )

        event = TelemetryEvent(
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            labels=dict(labels),
            tenant_hash=tenant_hash,
        )
        self._events.append(event)
        if self._sink is not None:
            self._sink.send(event)


class TelemetrySink:
    """Minimal sink protocol for :class:`MacTelemetryEmitter` injection."""

    def send(self, event: TelemetryEvent) -> None:  # pragma: no cover
        raise NotImplementedError


__all__ = (
    "LabelRegistryError",
    "MacTelemetryEmitter",
    "TelemetryEvent",
    "TelemetrySink",
    "VIOLATIONS_COUNTER",
)
