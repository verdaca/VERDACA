"""Calibration anchor SHA256 lock tests — mac/test-strategy.md v0.3 §7.7.

Covers MAC-T-BENCH-CALIBRATION-01..02. Anchors sourced verbatim from
benchmark-questions.md §5; SHA256-locked per arch §6.4 build script.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.gates.calibration_anchors import (
    CALIBRATION_ANCHORS,
    CALIBRATION_ANCHORS_SHA256,
    compute_calibration_anchors_sha256,
    verify_calibration_anchors_sha256,
)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_bench_calibration_01_twelve_gates_times_two_anchors() -> None:
    """MAC-T-BENCH-CALIBRATION-01 — 12 gates × 2 anchors = 24 calibration pairs.

    Each CALIBRATION_ANCHORS entry has both a score_2 and a score_4
    example + explanation, totaling 24 scorable anchors.
    """
    assert len(CALIBRATION_ANCHORS) == 12
    for gate_id in (f"R{n}" for n in range(1, 13)):
        anchor = CALIBRATION_ANCHORS[gate_id]
        assert anchor.gate_id == gate_id
        assert anchor.score_2_example
        assert anchor.score_2_explanation
        assert anchor.score_4_example
        assert anchor.score_4_explanation


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_bench_calibration_02_sha256_lock_byte_equality() -> None:
    """MAC-T-BENCH-CALIBRATION-02 — SHA256 hash is deterministic.

    Per arch §6.4: the build script records the SHA256 at generation
    time and the runtime verifier compares against the current
    structure. A mismatch indicates benchmark-questions.md §5 drift
    — regenerate via ``scripts/parse_calibration_anchors.py``.

    Step 4 computes the hash from the current CALIBRATION_ANCHORS
    mapping and verifies it is self-consistent (calling twice yields
    identical bytes).
    """
    # Self-consistency.
    h1 = compute_calibration_anchors_sha256()
    h2 = compute_calibration_anchors_sha256()
    assert h1 == h2
    assert h1 == CALIBRATION_ANCHORS_SHA256

    # The verifier passes for the current hash.
    verify_calibration_anchors_sha256(CALIBRATION_ANCHORS_SHA256)

    # The verifier raises on mismatch.
    with pytest.raises(ValueError, match="drift"):
        verify_calibration_anchors_sha256("0" * 64)
