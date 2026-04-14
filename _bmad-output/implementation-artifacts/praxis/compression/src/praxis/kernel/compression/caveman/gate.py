"""Caveman net-positive gate (architecture §3.4.3).

The gate prevents Caveman from being invoked when compression would cost MORE
tokens than it saves. Key predicate: downstream reads >= break_even_reads.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .boundary import classify_content
from .models import ContentType, Dialect

logger = logging.getLogger(__name__)

_WENYAN_DIALECTS: frozenset[Dialect] = frozenset({Dialect.WENYAN})


@dataclass(frozen=True)
class GateConfig:
    """Gate configuration (mirrors CompressionConfig.caveman.gate)."""

    min_tokens: int = 500
    break_even_reads: int = 3
    max_calibration_age_seconds: int = 7 * 24 * 3600
    prediction_error_median_threshold_pct: int = 30


@dataclass
class CalibrationSnapshot:
    """Nightly A/B harness refreshes this. Holds the break-even calibration."""

    refreshed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    savings_per_read_tokens: float = 200.0   # estimated tokens saved per downstream read
    compression_cost_tokens: float = 150.0   # estimated tokens spent per Caveman call
    prediction_error_pct_median: float = 0.0

    @property
    def age_seconds(self) -> float:
        return (datetime.now(UTC) - self.refreshed_at).total_seconds()

    def break_even_reads(self, extra_penalty: int = 0) -> float:
        """Return the minimum downstream reads needed for net-positive outcome."""
        if self.savings_per_read_tokens <= 0:
            return float("inf")
        return self.compression_cost_tokens / self.savings_per_read_tokens + extra_penalty


# Global calibration singleton (updated nightly by harness)
_calibration = CalibrationSnapshot()


def get_calibration() -> CalibrationSnapshot:
    return _calibration


def update_calibration(snapshot: CalibrationSnapshot) -> None:
    global _calibration
    _calibration = snapshot


def should_compress(
    text: str,
    dialect: Dialect,
    expected_downstream_reads: int,
    accept_wenyan: bool,
    *,
    config: GateConfig | None = None,
    calibration: CalibrationSnapshot | None = None,
) -> tuple[bool, str]:
    """Evaluate the net-positive gate.

    Returns:
        (True, "ok") if compression should proceed.
        (False, reason) if the gate denies.
    """
    cfg = config or GateConfig()
    cal = calibration or get_calibration()

    # 0. Calibration freshness (FMEA V.4)
    if cal.age_seconds > cfg.max_calibration_age_seconds:
        return False, "calibration_stale"

    # 1. Length floor
    token_count = max(1, len(text) // 4)
    if token_count < cfg.min_tokens:
        return False, f"below_min_length ({token_count} < {cfg.min_tokens})"

    # 2. Content type — must be prose-dominant
    content_type = classify_content(text)
    if content_type != ContentType.PROSE_DOMINANT:
        return False, f"content_type={content_type}"

    # 3. Downstream read predicate
    break_even = cal.break_even_reads()
    if expected_downstream_reads < break_even:
        return False, (
            f"below_break_even (need {break_even:.1f} reads, have {expected_downstream_reads})"
        )

    # 4. Wenyan gate
    if dialect in _WENYAN_DIALECTS and not accept_wenyan:
        return False, "wenyan_not_accepted"

    return True, "ok"
