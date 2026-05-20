"""tests/runtime/registry/test_semantic_matching.py — GREEN."""

from __future__ import annotations

from praxis.kernel.runtime.registry.embedder import DeterministicTestEmbedder
from praxis.kernel.runtime.registry.matching import semantic_score


def test_semantic_score_same_text_is_1() -> None:
    embedder = DeterministicTestEmbedder(seed=42, dimension=32)
    text = "brainstorming and creative innovation"
    score = semantic_score(text, text, embedder)
    assert abs(score - 1.0) < 0.05


def test_semantic_score_deterministic() -> None:
    embedder = DeterministicTestEmbedder(seed=42, dimension=32)
    query = "help me think through a strategic pivot"
    cap = "business model innovation strategic disruption"
    scores = [semantic_score(query, cap, embedder) for _ in range(5)]
    assert len(set(scores)) == 1


def test_semantic_score_normalized_0_to_1() -> None:
    embedder = DeterministicTestEmbedder(seed=42, dimension=32)
    score = semantic_score("some query", "some capability text", embedder)
    assert 0.0 <= score <= 1.0


def test_deterministic_embedder_embed_returns_list() -> None:
    embedder = DeterministicTestEmbedder(seed=42, dimension=32)
    vec = embedder.embed("hello world")
    assert isinstance(vec, list)
    assert len(vec) == 32
