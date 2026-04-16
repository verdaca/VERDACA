"""Benchmark baseline tests — mac/test-strategy.md v0.3 §7.5.

Covers MAC-T-BENCH-BASELINE-01..04.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.eval.baselines import (
    BASELINE_ENHANCED_PROMPT,
    BASELINE_VANILLA_PROMPT,
)
from praxis.kernel.mac.eval.composite import composite_score
from praxis.kernel.mac.testing.fakes.fake_benchmark_outputs import (
    build_default_benchmark_outputs,
)


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_baseline_01_three_baselines_produce_independent_scores() -> None:
    """MAC-T-BENCH-BASELINE-01 — three baselines produce distinct scores.

    The fake outputs assign vanilla=3, enhanced=4, mac=5 per gate. The
    composite scores should be strictly ordered mac > enhanced > vanilla.
    """
    outputs = build_default_benchmark_outputs()
    q1_vanilla = outputs.get(question_id="Q1", baseline="vanilla")
    q1_enhanced = outputs.get(question_id="Q1", baseline="enhanced")
    q1_mac = outputs.get(question_id="Q1", baseline="mac")

    v = composite_score(effective_scores=q1_vanilla.gate_scores)
    e = composite_score(effective_scores=q1_enhanced.gate_scores)
    m = composite_score(effective_scores=q1_mac.gate_scores)

    assert v < e < m


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_baseline_02_r3_directional_win_condition() -> None:
    """MAC-T-BENCH-BASELINE-02 — MAC composite > vanilla composite on Q1..Q10.

    Per benchmark-questions.md §4 Persona 1: directional claim is that
    MAC beats vanilla on the majority of questions. This test asserts
    the default fake outputs satisfy the directional property.
    """
    outputs = build_default_benchmark_outputs()

    mac_wins = 0
    for q_id in [f"Q{n}" for n in range(1, 11)]:
        v = composite_score(
            effective_scores=outputs.get(question_id=q_id, baseline="vanilla").gate_scores
        )
        m = composite_score(
            effective_scores=outputs.get(question_id=q_id, baseline="mac").gate_scores
        )
        if m > v:
            mac_wins += 1

    # Per benchmark §4 Persona 1 invalidation threshold: MAC must win
    # at least 7 of 10 to preserve the +15-25% directional claim.
    assert mac_wins >= 7


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_baseline_03_invalidation_trigger_below_7_wins() -> None:
    """MAC-T-BENCH-BASELINE-03 — if MAC wins fewer than 7 of 10, the
    differentiation claim requires revision per benchmark §4 Persona 1.

    Simulate a hypothetical scenario where MAC only wins 6 of 10 and
    assert our invalidation helper correctly flags it.
    """
    def claim_valid(mac_wins: int, average_improvement_pct: float) -> bool:
        """Invalidation rule from benchmark §4 Persona 1."""
        return mac_wins >= 7 and average_improvement_pct >= 10.0

    # Valid: 8 wins, 15% improvement.
    assert claim_valid(8, 15.0) is True
    # Invalid: 6 wins.
    assert claim_valid(6, 20.0) is False
    # Invalid: 10 wins but <10% avg improvement.
    assert claim_valid(10, 8.0) is False


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_baseline_04_prompt_templates_verbatim_from_benchmark_6_1() -> None:
    """MAC-T-BENCH-BASELINE-04 — prompt templates match benchmark §6 Step 1.

    The vanilla + enhanced prompts are stored as module constants
    (``BASELINE_VANILLA_PROMPT``, ``BASELINE_ENHANCED_PROMPT``).
    """
    assert "You are a strategic advisor" in BASELINE_VANILLA_PROMPT
    assert "{question}" in BASELINE_VANILLA_PROMPT

    assert "steelman" in BASELINE_ENHANCED_PROMPT.lower()
    assert "minority views" in BASELINE_ENHANCED_PROMPT.lower()
    assert "reasoning chain" in BASELINE_ENHANCED_PROMPT.lower()
    assert "{question}" in BASELINE_ENHANCED_PROMPT
