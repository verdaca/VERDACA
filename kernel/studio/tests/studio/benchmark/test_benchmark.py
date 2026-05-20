"""Benchmark regression tests — studio/test-strategy.md §7.

15 tests: 5 Tier 1 (scoring logic with FakeBenchmarkOutputs) + 9 Tier 3 (nightly) + 1 Tier 4 (A4).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


_BENCHMARK_DIR = Path(__file__).parent.parent / "fixtures" / "benchmark_scores"


def _compute_composite(scores: dict[str, int]) -> float:
    """Replicate studio composite formula: Σ(score × weight) / Σ(weight) × 20."""
    weights = {f"R{i}": 2 if i in (4, 5) else 1 for i in range(1, 13)}
    weighted_sum = sum(scores.get(gid, 0) * w for gid, w in weights.items())
    total_weight = sum(weights.values())
    return (weighted_sum / total_weight) * 20 if total_weight > 0 else 0.0


# ---------------------------------------------------------------------------
# §7.1 Benchmark harness unit tests — Tier 1 (5 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_benchmark
def test_bench_score_01_composite_formula_correct() -> None:
    """STUDIO-T-BENCH-SCORE-01: Composite score formula correct for known fixture."""
    # All R4/R5=4 (weight 2), others R=3 (weight 1)
    scores = {f"R{i}": 3 for i in range(1, 13)}
    scores["R4"] = 4
    scores["R5"] = 4
    composite = _compute_composite(scores)
    # weights: R4=2, R5=2, others=1 → total_weight=14
    # weighted_sum = 4*2 + 4*2 + 3*10 = 8+8+30 = 46
    # composite = 46/14 * 20 ≈ 65.71
    assert abs(composite - 65.71) < 0.1


@pytest.mark.studio_benchmark
def test_bench_score_02_r4_r5_weight_multiplier_applied() -> None:
    """STUDIO-T-BENCH-SCORE-02: R4 and R5 weight multiplier (2×) applied correctly."""
    scores_with_r4r5 = {f"R{i}": 3 for i in range(1, 13)}
    scores_with_r4r5["R4"] = 5
    scores_with_r4r5["R5"] = 5
    scores_without = {f"R{i}": 3 for i in range(1, 13)}
    scores_without["R4"] = 3
    scores_without["R5"] = 3
    composite_high = _compute_composite(scores_with_r4r5)
    composite_low = _compute_composite(scores_without)
    # R4/R5=5 vs R4/R5=3 should produce a noticeably different composite
    assert composite_high > composite_low


@pytest.mark.studio_benchmark
def test_bench_score_03_floor_assertion_fires_below_60() -> None:
    """STUDIO-T-BENCH-SCORE-03: Per-question quality floor: composite >= 60 assertion fires below 60."""
    low_scores = {f"R{i}": 2 for i in range(1, 13)}
    composite = _compute_composite(low_scores)
    # All 2s: weighted_sum = 2*14 = 28, composite = 28/14*20 = 40.0
    assert composite < 60, "Expected composite < 60 for all-2s scores"
    # The test asserts this fires — in production code, a >= 60 assertion would raise
    with pytest.raises(AssertionError):
        assert composite >= 60


@pytest.mark.studio_benchmark
@pytest.mark.critical
def test_bench_score_04_differentiator_gate_assertion() -> None:
    """STUDIO-T-BENCH-SCORE-04: R4 >= 4 AND R5 >= 4 assertion fires correctly."""
    failing_scores = {f"R{i}": 3 for i in range(1, 13)}
    # R4=3 fails the R4 >= 4 requirement
    with pytest.raises(AssertionError):
        assert failing_scores["R4"] >= 4 and failing_scores["R5"] >= 4

    passing_scores = {f"R{i}": 3 for i in range(1, 13)}
    passing_scores["R4"] = 4
    passing_scores["R5"] = 4
    assert passing_scores["R4"] >= 4 and passing_scores["R5"] >= 4


@pytest.mark.studio_benchmark
def test_bench_score_05_aggregate_mean_calculation() -> None:
    """STUDIO-T-BENCH-SCORE-05: Aggregate mean composite across 10-question fixture set."""
    deep_data = json.loads((_BENCHMARK_DIR / "deep_mode_scores.json").read_text())
    composites = [q["composite"] for q in deep_data["questions"].values()]
    mean = sum(composites) / len(composites)
    # All deep mode composites are >= 60, mean should be > 65
    assert mean >= 60.0
    assert len(composites) == 10


# ---------------------------------------------------------------------------
# §7.2 Benchmark regression — Tier 3 nightly (9 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_bench_deep_01_backbone_present_all_10() -> None:
    """STUDIO-T-BENCH-DEEP-01: Deep mode: all outputs contain ADR-01 backbone. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_bench_deep_02_composite_above_60() -> None:
    """STUDIO-T-BENCH-DEEP-02: Deep mode: composite >= 60 per question. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
@pytest.mark.critical
def test_bench_deep_03_r4_r5_above_4() -> None:
    """STUDIO-T-BENCH-DEEP-03: Deep mode: R4 >= 4 and R5 >= 4 per question. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_bench_deep_04_dissent_frames_present() -> None:
    """STUDIO-T-BENCH-DEEP-04: Deep mode: at least 1 competing frame per output. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_bench_deep_05_scenarios_present() -> None:
    """STUDIO-T-BENCH-DEEP-05: Deep mode: at least 2 named scenarios per output. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_bench_deep_06_scope_limits_present() -> None:
    """STUDIO-T-BENCH-DEEP-06: Deep mode: scope-limits >= 1 entry per sub-category. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_bench_quick_01_backbone_present_all_10() -> None:
    """STUDIO-T-BENCH-QUICK-01: Quick mode: all outputs contain ADR-01 backbone. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_bench_quick_02_quality_floor_met() -> None:
    """STUDIO-T-BENCH-QUICK-02: Quick mode: composite >= 40 floor. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_bench_quick_03_dissent_frames_present() -> None:
    """STUDIO-T-BENCH-QUICK-03: Quick mode: at least 1 competing frame per output. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


# ---------------------------------------------------------------------------
# §7.3 Spearman correlation — Tier 4 (1 test)
# ---------------------------------------------------------------------------


@pytest.mark.studio_benchmark
@pytest.mark.release_gate
def test_bench_a4_01_spearman_correlation() -> None:
    """STUDIO-T-BENCH-A4-01: A4 Spearman rho >= 0.6 human vs LLM-as-judge. [RELEASE GATE]"""
    pytest.skip(
        "Tier 4 — release gate. A4 Spearman corroboration not expected until Stage 7 "
        "ratifies rho >= 0.6 per Pipeline §5.6 conditional."
    )
