"""Pure scoring functions for Atelier decision retrieval (§5.3).

Multiplicative form per Req #43 — if any factor is zero, the total is
zero. QUARANTINED records therefore contribute zero to any retrieval,
which is the structural guarantee the architecture relies on (§5.3
"state_weight hard-gates QUARANTINED via multiplication-by-zero").

Phase 3B-iii uses the formula minus the `recency_decay` term because
Andrey's scope rules defer TTL / last_accessed_at tracking to Stage 5.
The scoring function signature still accepts the factor slot so the
Stage 5 integration can fill it in without changing call sites.

All functions are pure (no side effects) and defined over plain floats
so property tests via Hypothesis work out of the box. See
`tests/memory/atelier/test_scoring.py`.
"""

from __future__ import annotations

# Per §5.3:
#   alpha_c ≈ 0.5 (confidence exponent — MAC-graded)
#   alpha_i ≈ 0.3 (importance exponent — author-assessed; gentler)
ALPHA_C: float = 0.5
ALPHA_I: float = 0.3


# State weights (§5.3)
STATE_WEIGHT_ACTIVE: float = 1.0
STATE_WEIGHT_QUARANTINED: float = 0.0


def score_decision(
    *,
    semantic_similarity: float,
    state_weight: float,
    confidence: float,
    importance: float,
    recency_weight: float = 1.0,
) -> float:
    """Combine retrieval signals into a single score per §5.3.

    Parameters
    ----------
    semantic_similarity
        Cosine similarity between query and entry, in [0, 1].
    state_weight
        1.0 for ACTIVE, 0.0 for QUARANTINED. Multiplicative gate.
    confidence
        Decision-maker's confidence at capture time, in [0, 1].
    importance
        Author-assessed importance, in [0, 1]. Gentler lever than
        confidence (see alpha_i < alpha_c in architecture §5.3).
    recency_weight
        Optional recency decay factor in [0, 1]; Phase 3B-iii defaults
        to 1.0 because last_accessed_at tracking is Stage 5 work.

    Returns
    -------
    float
        Combined retrieval score. Zero iff any multiplicative factor is
        zero. Monotonically non-decreasing in each factor.

    Raises
    ------
    ValueError
        If any factor is outside [0, 1]. Defensive because the scoring
        function is the single point where all signals meet — silent
        out-of-range values would propagate into misranked results.
    """
    for name, value in (
        ("semantic_similarity", semantic_similarity),
        ("state_weight", state_weight),
        ("confidence", confidence),
        ("importance", importance),
        ("recency_weight", recency_weight),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name}={value!r} must be in [0, 1] (§5.3 invariant)")

    return (  # type: ignore[no-any-return]  # F-9.5-MYPY-SCORING-PREEXISTING-01
        semantic_similarity
        * state_weight
        * recency_weight
        * (confidence**ALPHA_C)
        * (importance**ALPHA_I)
    )


__all__ = [
    "ALPHA_C",
    "ALPHA_I",
    "STATE_WEIGHT_ACTIVE",
    "STATE_WEIGHT_QUARANTINED",
    "score_decision",
]
