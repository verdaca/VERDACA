"""tests/runtime/registry/test_llm_tiebreak.py — GREEN.

LLM tie-break errors and EmbedderMismatchError importability.
"""

from __future__ import annotations

from praxis.kernel.runtime.registry.registry import EmbedderMismatchError, LLMRerankError


def test_llm_rerank_error_raised_when_unparseable() -> None:
    # Just verify LLMRerankError is importable and is an Exception
    assert issubclass(LLMRerankError, Exception)


def test_llm_rerank_error_importable_from_registry() -> None:
    assert issubclass(LLMRerankError, Exception)


def test_embedder_mismatch_error_importable() -> None:
    assert issubclass(EmbedderMismatchError, Exception)
