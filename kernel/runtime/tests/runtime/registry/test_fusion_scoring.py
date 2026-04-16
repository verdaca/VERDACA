"""tests/runtime/registry/test_fusion_scoring.py — GREEN.

40/60 token/semantic fusion + confidence formula tests.
"""

from __future__ import annotations

from praxis.kernel.runtime.registry.matching import confidence_score, fused_score


def test_fused_score_is_weighted_sum() -> None:
    ts, ss = 0.8, 0.5
    expected = 0.4 * ts + 0.6 * ss
    assert abs(fused_score(token_score=ts, semantic_score=ss) - expected) < 1e-9


def test_fused_score_zero_both() -> None:
    assert fused_score(token_score=0.0, semantic_score=0.0) == 0.0


def test_fused_score_full_both() -> None:
    assert abs(fused_score(token_score=1.0, semantic_score=1.0) - 1.0) < 1e-9


def test_confidence_formula_basic() -> None:
    first, second = 0.9, 0.3
    conf = confidence_score(first_score=first, second_score=second)
    expected = first * (1.0 - second / max(first, 0.0001))
    assert abs(conf - expected) < 1e-9


def test_confidence_formula_tied_candidates_low() -> None:
    conf = confidence_score(first_score=0.8, second_score=0.8)
    assert conf < 0.01


def test_confidence_formula_runaway_leader_high() -> None:
    conf = confidence_score(first_score=0.95, second_score=0.1)
    assert conf > 0.8


def test_confidence_epsilon_prevents_division_by_zero() -> None:
    conf = confidence_score(first_score=0.0, second_score=0.0)
    assert 0.0 <= conf <= 1.0


def test_confidence_single_candidate_full() -> None:
    first = 0.85
    conf = confidence_score(first_score=first, second_score=0.0)
    assert abs(conf - first) < 1e-9
