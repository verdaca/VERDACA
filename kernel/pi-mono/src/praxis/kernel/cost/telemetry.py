"""Observability hooks — OpenTelemetry spans and Prometheus counters.

This module is the ONLY place in praxis.kernel.cost where `float()` is allowed —
specifically for the Prometheus boundary. Authoritative numbers live in the DB
as Decimal; metrics are approximations for observability.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

try:
    from prometheus_client import Counter, Gauge, Histogram

    _PROM_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PROM_AVAILABLE = False


@dataclass(frozen=True)
class TelemetryConfig:
    enabled: bool = True
    namespace: str = "praxis_cost"


if _PROM_AVAILABLE:
    _records_counter = Counter(
        "praxis_cost_records_total",
        "Total cost records written",
        labelnames=("provider", "model_id", "stop_reason"),
    )
    _usd_counter = Counter(
        "praxis_cost_usd_total",
        "Total cost in USD (Decimal→float; authoritative value in DB)",
        labelnames=("provider", "model_id"),
    )
    _latency_hist = Histogram(
        "praxis_cost_track_latency_seconds",
        "track_cost latency",
        labelnames=("provider",),
        buckets=(1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1),
    )
    _outbox_gauge = Gauge(
        "praxis_cost_outbox_undelivered",
        "Undelivered events in the outbox",
    )
else:  # pragma: no cover
    _records_counter = None
    _usd_counter = None
    _latency_hist = None
    _outbox_gauge = None


def record_track_cost(
    provider: str,
    model_id: str,
    stop_reason: str,
    cost_total_usd: Decimal,
    latency_seconds: float,
) -> None:
    if not _PROM_AVAILABLE:
        return
    assert _records_counter is not None
    assert _usd_counter is not None
    assert _latency_hist is not None
    _records_counter.labels(provider, model_id, stop_reason).inc()
    # METRICS BOUNDARY: approximate for observability; authoritative Decimal in cost_records
    _usd_counter.labels(provider, model_id).inc(float(cost_total_usd))
    _latency_hist.labels(provider).observe(latency_seconds)


def set_outbox_gauge(value: int) -> None:
    if not _PROM_AVAILABLE:
        return
    assert _outbox_gauge is not None
    _outbox_gauge.set(value)
