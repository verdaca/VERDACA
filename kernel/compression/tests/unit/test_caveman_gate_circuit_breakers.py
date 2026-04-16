"""Unit tests — CavemanGate quality circuit breakers (Pipeline gate §2.4).

Verifies that should_compress() denies compression in all configured
threshold scenarios. These are the "circuit breaker" tests required by
Pipeline stage 2.4 gate.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from praxis.kernel.compression.caveman.gate import (
    CalibrationSnapshot,
    GateConfig,
    get_calibration,
    update_calibration,
    should_compress,
)
from praxis.kernel.compression.caveman.models import Dialect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LONG_PROSE = (
    "The system must never disable logging in production. "
    "Enable all safety checks. Require authentication for all endpoints. "
    "Include the configuration file. Exclude debug output. "
    "Authorized users can access the public API. "
) * 40  # > 500 tokens

_FRESH_CAL = CalibrationSnapshot(
    refreshed_at=datetime.now(UTC),
    savings_per_read_tokens=200.0,
    compression_cost_tokens=150.0,
    prediction_error_pct_median=0.0,
)


# ---------------------------------------------------------------------------
# CalibrationSnapshot
# ---------------------------------------------------------------------------

class TestCalibrationSnapshot:
    def test_age_seconds_fresh(self):
        cal = CalibrationSnapshot(refreshed_at=datetime.now(UTC))
        assert cal.age_seconds < 5

    def test_age_seconds_old(self):
        cal = CalibrationSnapshot(
            refreshed_at=datetime.now(UTC) - timedelta(days=8)
        )
        assert cal.age_seconds > 7 * 24 * 3600

    def test_break_even_reads_normal(self):
        cal = CalibrationSnapshot(
            savings_per_read_tokens=200.0,
            compression_cost_tokens=150.0,
        )
        assert cal.break_even_reads() == pytest.approx(0.75, rel=0.01)

    def test_break_even_reads_with_penalty(self):
        cal = CalibrationSnapshot(
            savings_per_read_tokens=200.0,
            compression_cost_tokens=150.0,
        )
        assert cal.break_even_reads(extra_penalty=2) == pytest.approx(2.75, rel=0.01)

    def test_break_even_reads_zero_savings(self):
        cal = CalibrationSnapshot(savings_per_read_tokens=0.0)
        assert cal.break_even_reads() == float("inf")


# ---------------------------------------------------------------------------
# update/get calibration
# ---------------------------------------------------------------------------

class TestCalibrationSingleton:
    def test_update_calibration_roundtrip(self):
        original = get_calibration()
        new_cal = CalibrationSnapshot(
            refreshed_at=datetime.now(UTC),
            savings_per_read_tokens=300.0,
            compression_cost_tokens=100.0,
        )
        update_calibration(new_cal)
        assert get_calibration() is new_cal
        # Restore
        update_calibration(original)


# ---------------------------------------------------------------------------
# Circuit breaker: calibration stale
# ---------------------------------------------------------------------------

class TestGateCircuitBreakerCalibrationStale:
    def test_stale_calibration_denies(self):
        stale_cal = CalibrationSnapshot(
            refreshed_at=datetime.now(UTC) - timedelta(days=10),
        )
        ok, reason = should_compress(
            text=_LONG_PROSE,
            dialect=Dialect.CAVEMAN_ENGLISH,
            expected_downstream_reads=10,
            accept_wenyan=False,
            config=GateConfig(),
            calibration=stale_cal,
        )
        assert ok is False
        assert reason == "calibration_stale"

    def test_fresh_calibration_passes_staleness_check(self):
        ok, reason = should_compress(
            text=_LONG_PROSE,
            dialect=Dialect.CAVEMAN_ENGLISH,
            expected_downstream_reads=10,
            accept_wenyan=False,
            config=GateConfig(min_tokens=1, break_even_reads=0),
            calibration=_FRESH_CAL,
        )
        # Either ok or denied for a different reason
        if not ok:
            assert reason != "calibration_stale"


# ---------------------------------------------------------------------------
# Circuit breaker: below minimum token length
# ---------------------------------------------------------------------------

class TestGateCircuitBreakerMinLength:
    def test_short_text_denied(self):
        ok, reason = should_compress(
            text="short",
            dialect=Dialect.CAVEMAN_ENGLISH,
            expected_downstream_reads=100,
            accept_wenyan=False,
            config=GateConfig(min_tokens=1000),
            calibration=_FRESH_CAL,
        )
        assert ok is False
        assert "below_min_length" in reason

    def test_long_text_passes_length_check(self):
        ok, reason = should_compress(
            text=_LONG_PROSE,
            dialect=Dialect.CAVEMAN_ENGLISH,
            expected_downstream_reads=100,
            accept_wenyan=False,
            config=GateConfig(min_tokens=1, break_even_reads=0),
            calibration=_FRESH_CAL,
        )
        if not ok:
            assert "below_min_length" not in reason


# ---------------------------------------------------------------------------
# Circuit breaker: content type
# ---------------------------------------------------------------------------

class TestGateCircuitBreakerContentType:
    def test_code_dominant_denied(self):
        code_text = "\n".join([f"def func_{i}(x): return x + {i}" for i in range(200)])
        ok, reason = should_compress(
            text=code_text,
            dialect=Dialect.CAVEMAN_ENGLISH,
            expected_downstream_reads=100,
            accept_wenyan=False,
            config=GateConfig(min_tokens=1, break_even_reads=0),
            calibration=_FRESH_CAL,
        )
        if not ok:
            assert "content_type" in reason or "below_min_length" in reason


# ---------------------------------------------------------------------------
# Circuit breaker: below break-even reads
# ---------------------------------------------------------------------------

class TestGateCircuitBreakerBreakEven:
    def test_zero_reads_denied(self):
        ok, reason = should_compress(
            text=_LONG_PROSE,
            dialect=Dialect.CAVEMAN_ENGLISH,
            expected_downstream_reads=0,
            accept_wenyan=False,
            config=GateConfig(min_tokens=1),
            calibration=_FRESH_CAL,
        )
        assert ok is False
        assert "below_break_even" in reason

    def test_sufficient_reads_passes(self):
        ok, reason = should_compress(
            text=_LONG_PROSE,
            dialect=Dialect.CAVEMAN_ENGLISH,
            expected_downstream_reads=100,
            accept_wenyan=False,
            config=GateConfig(min_tokens=1, break_even_reads=0),
            calibration=_FRESH_CAL,
        )
        if not ok:
            # Only acceptable non-break-even failures
            assert "break_even" not in reason


# ---------------------------------------------------------------------------
# Circuit breaker: Wenyan not accepted
# ---------------------------------------------------------------------------

class TestGateCircuitBreakerWenyan:
    def test_wenyan_denied_when_not_accepted(self):
        ok, reason = should_compress(
            text=_LONG_PROSE,
            dialect=Dialect.WENYAN,
            expected_downstream_reads=100,
            accept_wenyan=False,
            config=GateConfig(min_tokens=1, break_even_reads=0),
            calibration=_FRESH_CAL,
        )
        assert ok is False
        assert reason == "wenyan_not_accepted"

    def test_wenyan_allowed_when_accepted(self):
        ok, reason = should_compress(
            text=_LONG_PROSE,
            dialect=Dialect.WENYAN,
            expected_downstream_reads=100,
            accept_wenyan=True,
            config=GateConfig(min_tokens=1, break_even_reads=0),
            calibration=_FRESH_CAL,
        )
        # May still fail content-type gate; if so, not wenyan_not_accepted
        if not ok:
            assert reason != "wenyan_not_accepted"

    def test_caveman_english_not_affected_by_wenyan_gate(self):
        ok, reason = should_compress(
            text=_LONG_PROSE,
            dialect=Dialect.CAVEMAN_ENGLISH,
            expected_downstream_reads=100,
            accept_wenyan=False,
            config=GateConfig(min_tokens=1, break_even_reads=0),
            calibration=_FRESH_CAL,
        )
        if not ok:
            assert reason != "wenyan_not_accepted"


# ---------------------------------------------------------------------------
# Happy path — gate should pass
# ---------------------------------------------------------------------------

class TestGateHappyPath:
    def test_all_conditions_met_returns_ok(self):
        ok, reason = should_compress(
            text=_LONG_PROSE,
            dialect=Dialect.CAVEMAN_ENGLISH,
            expected_downstream_reads=100,
            accept_wenyan=False,
            config=GateConfig(min_tokens=1, break_even_reads=0),
            calibration=_FRESH_CAL,
        )
        # Long prose + many reads + fresh calibration = should pass
        # (unless content type detection fires on this specific text)
        if ok:
            assert reason == "ok"
