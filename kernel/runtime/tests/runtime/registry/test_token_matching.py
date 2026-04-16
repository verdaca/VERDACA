"""tests/runtime/registry/test_token_matching.py — GREEN."""

from __future__ import annotations

from praxis.kernel.runtime.registry.matching import token_score


def test_token_score_exact_match() -> None:
    score = token_score("brainstorming", ("brainstorming", "creative techniques"))
    assert score > 0.0


def test_token_score_no_match() -> None:
    score = token_score(
        "database migrations performance tuning",
        ("brainstorming", "creative techniques"),
    )
    assert score == 0.0


def test_token_score_partial_match() -> None:
    score = token_score(
        "market analysis competitive landscape",
        ("market research", "competitive analysis", "requirements elicitation"),
    )
    assert 0.0 < score <= 1.0


def test_token_score_deterministic() -> None:
    caps = ("brainstorming", "creative techniques", "systematic innovation")
    desc = "help me brainstorm new product ideas"
    scores = [token_score(desc, caps) for _ in range(10)]
    assert len(set(scores)) == 1, f"Non-deterministic: {scores}"


def test_token_score_normalized_0_to_1() -> None:
    score = token_score("brainstorming", ("brainstorming",))
    assert 0.0 <= score <= 1.0
