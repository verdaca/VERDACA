"""FakeBenchmarkOutputs harness smoke tests — mac/test-strategy.md v0.3 §7.8.

Covers MAC-T-BENCH-FAKE-01..02.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.eval.composite import composite_score
from praxis.kernel.mac.testing.fakes.fake_benchmark_outputs import (
    build_default_benchmark_outputs,
)


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_fake_01_end_to_end_harness_run() -> None:
    """MAC-T-BENCH-FAKE-01 — full 30-item composite run completes.

    For each of 30 pre-scored outputs, compute the composite via the
    arch §9.4 top-5 formula. Assert all 30 scores are in the valid
    range [20.0, 100.0].
    """
    outputs = build_default_benchmark_outputs()
    composites: list[float] = []
    for output in outputs.all():
        c = composite_score(effective_scores=output.gate_scores)
        assert 20.0 <= c <= 100.0
        composites.append(c)

    assert len(composites) == 30


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_fake_02_lookup_table_completeness() -> None:
    """MAC-T-BENCH-FAKE-02 — lookup table has every (question, baseline) key."""
    outputs = build_default_benchmark_outputs()
    expected_keys = {
        (f"Q{n}", b)
        for n in range(1, 11)
        for b in ("vanilla", "enhanced", "mac")
    }
    assert set(outputs.outputs.keys()) == expected_keys
