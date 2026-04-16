"""Benchmark corpus tests — mac/test-strategy.md v0.3 §7.6.

Covers MAC-T-BENCH-CORPUS-01..02.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.testing.fakes.fake_benchmark_outputs import (
    QUESTION_IDS,
    BASELINES,
    build_default_benchmark_outputs,
)


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_corpus_01_exactly_10_questions_loaded() -> None:
    """MAC-T-BENCH-CORPUS-01 — the benchmark corpus has exactly 10 questions.

    Per benchmark-questions.md §2: Q1..Q10.
    """
    assert len(QUESTION_IDS) == 10
    assert set(QUESTION_IDS) == {f"Q{n}" for n in range(1, 11)}
    # And 3 baselines (vanilla / enhanced / mac).
    assert len(BASELINES) == 3
    assert set(BASELINES) == {"vanilla", "enhanced", "mac"}


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_corpus_02_question_text_byte_equality_spot_check() -> None:
    """MAC-T-BENCH-CORPUS-02 — fake outputs table has 30 pre-scored entries.

    Step 4 ships the FakeBenchmarkOutputs with a deterministic
    30-item lookup (10 questions × 3 baselines). The real benchmark
    question TEXT comparison happens at Tier 3 nightly vs real LLM
    outputs — step 4 only asserts the fixture cardinality and
    shape.
    """
    outputs = build_default_benchmark_outputs()
    assert len(outputs.outputs) == 30
    # Spot check a few entries.
    for q in ("Q1", "Q5", "Q10"):
        for b in ("vanilla", "enhanced", "mac"):
            entry = outputs.get(question_id=q, baseline=b)
            assert entry.question_id == q
            assert entry.baseline == b
            assert len(entry.gate_scores) == 12
