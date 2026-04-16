"""Benchmark composite scoring tests — mac/test-strategy.md v0.3 §7.2.

Covers MAC-T-BENCH-SCORING-01..04. SCORING-05 retired v0.3.

Anchors:
  - mac/architecture.md §9.4 Top-5 weighting
  - mac/benchmark-questions.md §6 Step 5 composite formula
  - mac/benchmark-questions.md §7 OQ-5 weights
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.eval.composite import (
    GATE_WEIGHTS,
    TOTAL_WEIGHT,
    composite_score,
)


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_scoring_01_top_5_weighting_composite_math() -> None:
    """MAC-T-BENCH-SCORING-01 — top-5 weighted composite math.

    Per benchmark §7 OQ-5: R1/R2/R4/R5/R7 = 2; rest = 1. Total = 17.
    Formula: ``composite = Σ(score × weight) / (active_weight × 5) × 100``.
    """
    # All 5s everywhere: composite should be 100.0.
    all_fives = {f"R{n}": 5 for n in range(1, 13)}
    assert composite_score(effective_scores=all_fives) == pytest.approx(100.0)

    # Mixed: top-5 gates at 4, others at 3.
    mixed = {f"R{n}": 3 for n in range(1, 13)}
    for g in ("R1", "R2", "R4", "R5", "R7"):
        mixed[g] = 4
    # numerator = 4*2*5 + 3*1*7 = 40 + 21 = 61
    # denominator = 17 * 5 = 85
    # 61/85 * 100 = 71.76470...
    assert composite_score(effective_scores=mixed) == pytest.approx(
        (61 / 85) * 100.0
    )


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_scoring_02_weight_unit_sum_is_17() -> None:
    """MAC-T-BENCH-SCORING-02 — total weight is exactly 17."""
    assert TOTAL_WEIGHT == 17
    assert sum(GATE_WEIGHTS.values()) == 17
    # 5 critical at weight 2 + 7 non-critical at weight 1 = 10 + 7 = 17.
    critical_weight_sum = sum(
        GATE_WEIGHTS[g] for g in ("R1", "R2", "R4", "R5", "R7")
    )
    assert critical_weight_sum == 10


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_scoring_03_max_composite_when_all_gates_5() -> None:
    """MAC-T-BENCH-SCORING-03 — max composite = 100 when all gates = 5."""
    all_fives = {f"R{n}": 5 for n in range(1, 13)}
    assert composite_score(effective_scores=all_fives) == 100.0


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_scoring_04_min_composite_when_all_gates_1() -> None:
    """MAC-T-BENCH-SCORING-04 — min composite = 20 when all gates = 1.

    All 1s: numerator = 1*17 = 17; denominator = 17*5 = 85; ratio = 0.2;
    composite = 20.0.
    """
    all_ones = {f"R{n}": 1 for n in range(1, 13)}
    assert composite_score(effective_scores=all_ones) == pytest.approx(20.0)


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_bench_scoring_req_e_suspension_adjusts_denominator() -> None:
    """Supplementary — Req-E suspension reduces denominator by suspended
    weight. Worked example from step-4 go signal:

      DomainClass.CONSENSUS → R5 suspended → active_weight = 17 - 2 = 15.
    """
    scores = {f"R{n}": 4 for n in range(1, 13)}
    scores["R5"] = 0  # suspended zeroed

    # With R5 suspended and active_weight=15:
    # numerator = 4*(17-2) = 60 (excluding R5)
    # denominator = 15 * 5 = 75
    # composite = 60/75 * 100 = 80.0
    result = composite_score(
        effective_scores=scores, suspended=frozenset({"R5"})
    )
    assert result == pytest.approx(80.0)
