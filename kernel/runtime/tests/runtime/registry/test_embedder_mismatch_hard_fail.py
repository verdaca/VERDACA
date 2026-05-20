"""tests/runtime/registry/test_embedder_mismatch_hard_fail.py — GREEN."""

from __future__ import annotations

import pytest

from praxis.kernel.runtime.registry.embedder import DeterministicTestEmbedder
from praxis.kernel.runtime.registry.registry import AgentRegistry, EmbedderMismatchError


def test_embedder_mismatch_raises_at_init() -> None:
    embedder = DeterministicTestEmbedder(seed=42, dimension=32, model_id="model-A")
    with pytest.raises(EmbedderMismatchError):
        AgentRegistry(
            catalog={},
            embedder=embedder,
            expected_embedding_model_id="model-B",
        )


def test_embedder_match_does_not_raise() -> None:
    embedder = DeterministicTestEmbedder(seed=42, dimension=32, model_id="model-A")
    registry = AgentRegistry(
        catalog={},
        embedder=embedder,
        expected_embedding_model_id="model-A",
    )
    assert registry is not None


def test_no_expected_model_id_no_raise() -> None:
    embedder = DeterministicTestEmbedder(seed=42, dimension=32, model_id="any-model")
    # No expected_embedding_model_id → no check
    registry = AgentRegistry(catalog={}, embedder=embedder)
    assert registry is not None
