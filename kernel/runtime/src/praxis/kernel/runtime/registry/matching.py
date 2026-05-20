"""Praxis Runtime registry — matching algorithm primitives.

Architecture §3.3 (matching pipeline: token → semantic → fusion → confidence)
Architecture §3.4 (confidence semantics: score ≠ confidence)

Scoring functions are pure functions with no side effects; all deterministic.
"""

from __future__ import annotations

import math
import re

from praxis.kernel.runtime.registry.embedder import Embedder

# Stopwords for token scoring — common English words that carry no capability signal
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "me",
        "my",
        "i",
        "we",
        "our",
        "you",
        "your",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "help",
        "need",
        "want",
        "some",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)*")


def _tokenize(text: str) -> list[str]:
    """Lowercase tokenize, strip stopwords."""
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


def token_score(query: str, capabilities: tuple[str, ...]) -> float:
    """Exact-match token score per architecture §3.3 step 2.

    Count query tokens that appear in capabilities (as substrings of any cap
    token or whole match), normalize by total query token count.

    Returns 0.0 if query has no meaningful tokens.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0

    # Build capability token set (all tokens from all capabilities)
    cap_token_set: set[str] = set()
    for cap in capabilities:
        cap_token_set.update(_tokenize(cap))
        # Also add the raw capability string for multi-word matching
        cap_token_set.add(cap.lower().strip())

    matches = sum(1 for t in query_tokens if t in cap_token_set)
    return matches / len(query_tokens)


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0
    raw = dot / (norm_a * norm_b)
    # Clamp to [0, 1] — cosine can be negative for opposite vectors; we map to [0, 1]
    return (raw + 1.0) / 2.0


def semantic_score(query: str, capability_text: str, embedder: Embedder) -> float:
    """Semantic similarity score per architecture §3.3 step 3.

    Embeds both query and capability_text, returns cosine similarity
    normalized to [0, 1].
    """
    query_vec = embedder.embed(query)
    cap_vec = embedder.embed(capability_text)
    raw = _cosine_similarity(query_vec, cap_vec)
    return max(0.0, min(1.0, raw))


def fused_score(*, token_score: float, semantic_score: float) -> float:
    """40/60 weighted fusion per architecture §3.3 step 4.

    score = 0.4 × token_score + 0.6 × semantic_score
    """
    return 0.4 * token_score + 0.6 * semantic_score


_EPSILON = 0.0001  # ε per architecture §3.4 formula


def confidence_score(*, first_score: float, second_score: float) -> float:
    """Confidence formula per architecture §3.4.

    confidence = score × (1 - second / max(first, ε))

    High score + no close competitor → high confidence.
    High score + tied competitor → low confidence.
    """
    denominator = max(first_score, _EPSILON)
    conf = first_score * (1.0 - second_score / denominator)
    return max(0.0, min(1.0, conf))


__all__ = [
    "token_score",
    "semantic_score",
    "fused_score",
    "confidence_score",
]
