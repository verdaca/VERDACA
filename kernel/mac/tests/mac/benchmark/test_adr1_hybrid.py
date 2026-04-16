"""ADR-1 hybrid blind/open scoring tests — mac/test-strategy.md v0.3 §7.3.

Covers MAC-T-BENCH-ADR1-01..03.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.eval.scoring import (
    BLIND_GATES,
    OPEN_GATES,
    HybridScoringHarness,
)


def _fake_blind(*, gate_id: str, output_id: str) -> int:
    """Pass 1 blind scorer — returns a deterministic score per gate."""
    return {"R1": 4, "R2": 4, "R3": 3, "R4": 5, "R6": 3,
            "R7": 4, "R8": 3, "R9": 3, "R10": 3, "R11": 3, "R12": 4}[gate_id]


def _fake_open(*, gate_id: str, output_id: str, task_context) -> int:
    """Pass 2 open scorer — R5 only, returns 4 when task_context has
    ``manufactured_dissent=False`` else 2."""
    assert gate_id == "R5"
    if task_context.get("manufactured_dissent_detected", False):
        return 2
    return 4


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_adr1_01_pass_1_is_blind_to_producer_identity() -> None:
    """MAC-T-BENCH-ADR1-01 — Pass 1 scores R1/R2/R3/R4/R6..R12 without
    task context. Blind gate set excludes R5.
    """
    assert "R5" not in BLIND_GATES
    assert BLIND_GATES == frozenset(
        {"R1", "R2", "R3", "R4", "R6", "R7", "R8", "R9", "R10", "R11", "R12"}
    )
    assert len(BLIND_GATES) == 11


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_adr1_02_pass_2_is_open_for_r5_only() -> None:
    """MAC-T-BENCH-ADR1-02 — Pass 2 open set is exactly {R5}."""
    assert OPEN_GATES == frozenset({"R5"})


@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_adr1_03_pass_1_and_pass_2_merge_correctly() -> None:
    """MAC-T-BENCH-ADR1-03 — merged scores contain all 12 R1..R12 gates."""
    harness = HybridScoringHarness(blind_scorer=_fake_blind, open_scorer=_fake_open)
    record = harness.score_output(
        output_id="test-output",
        task_context={"manufactured_dissent_detected": False},
    )
    merged = record.merged_scores
    for n in range(1, 13):
        assert f"R{n}" in merged
    # R5 came from Pass 2.
    assert merged["R5"] == 4  # no manufactured dissent → 4
    # Non-R5 came from Pass 1.
    assert merged["R1"] == 4
    assert merged["R7"] == 4

    # With manufactured dissent signal, R5 drops to 2.
    record_bad = harness.score_output(
        output_id="test-output",
        task_context={"manufactured_dissent_detected": True},
    )
    assert record_bad.merged_scores["R5"] == 2
