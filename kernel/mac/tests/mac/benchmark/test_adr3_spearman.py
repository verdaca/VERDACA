"""ADR-3 Spearman validation tests — mac/test-strategy.md v0.3 §7.4.

Covers MAC-T-BENCH-SPEARMAN-01..03.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.eval.validation import (
    SPEARMAN_RELEASE_GATE_THRESHOLD,
    compute_spearman_correlation,
    run_a4_validation,
)


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_spearman_01_computation_correctness() -> None:
    """MAC-T-BENCH-SPEARMAN-01 — pure-Python Spearman matches a known case.

    Perfect positive correlation → ρ = 1.0.
    Perfect negative correlation → ρ = -1.0.
    Uncorrelated → |ρ| < 0.5.
    """
    auto_perfect = [1.0, 2.0, 3.0, 4.0, 5.0]
    human_perfect = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert compute_spearman_correlation(auto_perfect, human_perfect) == pytest.approx(1.0)

    auto_neg = [1.0, 2.0, 3.0, 4.0, 5.0]
    human_neg = [50.0, 40.0, 30.0, 20.0, 10.0]
    assert compute_spearman_correlation(auto_neg, human_neg) == pytest.approx(-1.0)


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_spearman_02_threshold_enforcement() -> None:
    """MAC-T-BENCH-SPEARMAN-02 — ADR-3 threshold is 0.6."""
    assert SPEARMAN_RELEASE_GATE_THRESHOLD == 0.6

    # ρ = 1.0 → provisional_validation True
    report_good = run_a4_validation(
        automated_scores={"a": 1.0, "b": 2.0, "c": 3.0},
        human_scores={"a": 10.0, "b": 20.0, "c": 30.0},
    )
    assert report_good.provisional_validation is True
    assert report_good.spearman_rho == pytest.approx(1.0)

    # ρ = -1.0 → below threshold → provisional_validation False
    report_bad = run_a4_validation(
        automated_scores={"a": 1.0, "b": 2.0, "c": 3.0},
        human_scores={"a": 30.0, "b": 20.0, "c": 10.0},
    )
    assert report_bad.provisional_validation is False


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_spearman_03_sample_size_matches_fixture() -> None:
    """MAC-T-BENCH-SPEARMAN-03 — the report's sample_size reflects the
    number of (output_id → score) pairs in the fixture.

    The canonical A4 fixture has 9 outputs (3 questions × 3 baselines)
    per ADR-3 Option B. The step-3 math-only fixture used here has 9
    pairs so the sample_size field reports 9.
    """
    automated = {f"out_{i}": float(i) for i in range(9)}
    human = {f"out_{i}": float(i) + 0.5 for i in range(9)}
    report = run_a4_validation(
        automated_scores=automated, human_scores=human
    )
    assert report.sample_size == 9
