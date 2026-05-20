"""
Tests for the backoff function from praxis.kernel.runtime.jobs.retry.
All pure unit tests — no DB or Docker required.
"""

from datetime import timedelta

from praxis.kernel.runtime.jobs.retry import backoff

# ---------------------------------------------------------------------------
# Backoff property tests
# ---------------------------------------------------------------------------


def test_backoff_increases_with_retry_count():
    b0 = backoff(0).total_seconds()
    b3 = backoff(3).total_seconds()
    b8 = backoff(8).total_seconds()
    assert b0 < b3 < b8


def test_backoff_capped_at_exponent_8():
    b8 = backoff(8).total_seconds()
    b20 = backoff(20).total_seconds()
    # The exponent is capped at 8, so b8 and b20 should be in the same ballpark.
    # Allow for jitter: the ratio should stay within [0.5, 2.0].
    ratio = b20 / b8
    assert 0.5 <= ratio <= 2.0, (
        f"backoff(20)={b20:.2f}s is not in the same ballpark as backoff(8)={b8:.2f}s "
        f"(ratio={ratio:.2f})"
    )


def test_backoff_includes_jitter():
    results = {backoff(3).total_seconds() for _ in range(20)}
    assert len(results) > 1, (
        "backoff(3) returned identical values 20 times — jitter appears to be missing"
    )


def test_backoff_returns_timedelta():
    result = backoff(0)
    assert isinstance(result, timedelta), f"Expected timedelta, got {type(result)}"


def test_backoff_minimum_base():
    # base_seconds=1, jitter is typically multiplied in [0.75, 1.25] range
    # so the absolute minimum for retry 0 should be >= 0.75 seconds
    samples = [backoff(0).total_seconds() for _ in range(30)]
    assert all(s >= 0.75 for s in samples), (
        f"Some backoff(0) samples fell below 0.75s: min={min(samples):.3f}s"
    )
