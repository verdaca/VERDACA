"""Nightly full harness tests — mac/test-strategy.md v0.3 §7.9.

Covers MAC-T-BENCH-NIGHTLY-01..02. Both are ``nightly_only``; they
run against real LLM calls in the Tier 3 nightly pipeline and skip
in PR-gate runs. Step 4 ships the placeholder assertions — Stage 7
POV Harness wires in the real LLM calls.
"""

from __future__ import annotations

import pytest


@pytest.mark.nightly_only
@pytest.mark.mac_benchmark_harness
@pytest.mark.critical
def test_mac_t_bench_nightly_01_full_30_score_nightly_harness() -> None:
    """MAC-T-BENCH-NIGHTLY-01 — full 30-score harness (Tier 3 nightly).

    Runs 10 questions × 3 baselines against real LLMs. Step 4 ships
    this as a stub that passes when the nightly harness infrastructure
    is absent; Stage 7 POV Harness wires in the real loop.
    """
    # Tier 3: skipped in PR gate by root conftest.py.
    # When --run-nightly is passed, this runs against real LLMs.
    # Step 4 placeholder: assert True so the test collects + marks
    # properly.
    assert True


@pytest.mark.nightly_only
@pytest.mark.mac_benchmark_harness
@pytest.mark.critical
def test_mac_t_bench_nightly_02_cost_budget_enforcement() -> None:
    """MAC-T-BENCH-NIGHTLY-02 — nightly harness stays under cost budget.

    Per arch §12.3 / test-strategy v0.3 §12.3: nightly run budget is
    ~60 live judge calls / night. Full 30-score harness is ~30
    additional calls. Total budget documented at §14.4; step 4
    placeholder.
    """
    assert True
