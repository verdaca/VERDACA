"""Stage 3 post-ratification addition — R53 field allowlist policy.

Authored during Stage 4.3 implementation per Stage 4.1 architecture
§9.1 claim and Q3 option (b) resolution. This file is purely additive:
no existing Stage 3 Memory code imports or references TelemetryEvent.
It exists as the canonical single-source-of-truth for the R53 field
allowlist shared across Memory, Runtime, and future cross-stage
telemetry emission surfaces.

Provenance: added 2026-04-13 during Stage 4.3 Amelia preload caught
the missing artifact. Binding condition #4 preserved because Stage 3
runtime behavior is unchanged. Pipeline.md F-5 (LOW, closed on add)
tracks this post-ratification addition.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TelemetryEvent(BaseModel):
    """R53-compliant telemetry event. Field set is the R53 allowlist.

    Frozen + extra='forbid' is the structural enforcement: adding a
    forbidden field (query content, result IDs, embeddings, tenant
    data values) is a ValidationError at construction time, not a
    runtime gate. This is the type Stage 4 Runtime imports via
    `from praxis.kernel.memory.telemetry import TelemetryEvent`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_name: str
    metric_type: Literal["counter", "gauge", "histogram"]
    value: float
    labels: dict[str, str]
    timestamp: datetime
    praxis_version: str
    tenant_hash: str


__all__ = ["TelemetryEvent"]
