"""Property tests for the §5.3 multiplicative decision-scoring function.

The architecture §5.3 says sub-functions are pure with property tests
asserting monotonicity in each factor and invariance for QUARANTINED →
0. This file is that test.

Invariants under test:

1. **Quarantined → zero.** state_weight=0 → score=0 regardless of any
   other factor. This is the single most important invariant — it's the
   structural guarantee the retrieval code relies on to filter
   quarantined entries without an explicit state check.

2. **Monotonic in each factor.** Holding all other factors fixed,
   increasing any one factor never decreases the score. Tested over
   four factors: semantic_similarity, confidence, importance,
   recency_weight. state_weight isn't monotonic in the usual sense
   (it's 0 or 1) so it gets its own invariant above.

3. **Range discipline.** Inputs outside [0, 1] raise ValueError. Caller
   can't accidentally pass 1.5 or -0.2 without a loud failure.

4. **Bounded output.** For legal inputs in [0, 1], score is in [0, 1].
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from praxis.kernel.memory._internal.atelier.scoring import (
    STATE_WEIGHT_ACTIVE,
    STATE_WEIGHT_QUARANTINED,
    score_decision,
)

# Bounded unit floats — exclude NaN, keep within [0, 1].
_unit = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


# =============================================================================
# Invariant 1 — Quarantined → zero
# =============================================================================


@given(
    sim=_unit,
    conf=_unit,
    imp=_unit,
    rec=_unit,
)
def test_quarantined_state_forces_score_to_zero(
    sim: float, conf: float, imp: float, rec: float
) -> None:
    """No legal input combination can rescue a QUARANTINED entry from 0."""
    score = score_decision(
        semantic_similarity=sim,
        state_weight=STATE_WEIGHT_QUARANTINED,
        confidence=conf,
        importance=imp,
        recency_weight=rec,
    )
    assert score == 0.0


# =============================================================================
# Invariant 2 — Monotonic in each factor
# =============================================================================


@given(
    sim_a=_unit,
    sim_b=_unit,
    conf=_unit,
    imp=_unit,
)
def test_monotonic_in_semantic_similarity(
    sim_a: float, sim_b: float, conf: float, imp: float
) -> None:
    if sim_a > sim_b:
        sim_a, sim_b = sim_b, sim_a
    s_low = score_decision(
        semantic_similarity=sim_a,
        state_weight=STATE_WEIGHT_ACTIVE,
        confidence=conf,
        importance=imp,
    )
    s_high = score_decision(
        semantic_similarity=sim_b,
        state_weight=STATE_WEIGHT_ACTIVE,
        confidence=conf,
        importance=imp,
    )
    assert s_low <= s_high


@given(
    sim=_unit,
    conf_a=_unit,
    conf_b=_unit,
    imp=_unit,
)
def test_monotonic_in_confidence(sim: float, conf_a: float, conf_b: float, imp: float) -> None:
    if conf_a > conf_b:
        conf_a, conf_b = conf_b, conf_a
    s_low = score_decision(
        semantic_similarity=sim,
        state_weight=STATE_WEIGHT_ACTIVE,
        confidence=conf_a,
        importance=imp,
    )
    s_high = score_decision(
        semantic_similarity=sim,
        state_weight=STATE_WEIGHT_ACTIVE,
        confidence=conf_b,
        importance=imp,
    )
    assert s_low <= s_high


@given(
    sim=_unit,
    conf=_unit,
    imp_a=_unit,
    imp_b=_unit,
)
def test_monotonic_in_importance(sim: float, conf: float, imp_a: float, imp_b: float) -> None:
    if imp_a > imp_b:
        imp_a, imp_b = imp_b, imp_a
    s_low = score_decision(
        semantic_similarity=sim,
        state_weight=STATE_WEIGHT_ACTIVE,
        confidence=conf,
        importance=imp_a,
    )
    s_high = score_decision(
        semantic_similarity=sim,
        state_weight=STATE_WEIGHT_ACTIVE,
        confidence=conf,
        importance=imp_b,
    )
    assert s_low <= s_high


@given(
    sim=_unit,
    conf=_unit,
    imp=_unit,
    rec_a=_unit,
    rec_b=_unit,
)
def test_monotonic_in_recency_weight(
    sim: float, conf: float, imp: float, rec_a: float, rec_b: float
) -> None:
    if rec_a > rec_b:
        rec_a, rec_b = rec_b, rec_a
    s_low = score_decision(
        semantic_similarity=sim,
        state_weight=STATE_WEIGHT_ACTIVE,
        confidence=conf,
        importance=imp,
        recency_weight=rec_a,
    )
    s_high = score_decision(
        semantic_similarity=sim,
        state_weight=STATE_WEIGHT_ACTIVE,
        confidence=conf,
        importance=imp,
        recency_weight=rec_b,
    )
    assert s_low <= s_high


# =============================================================================
# Invariant 3 — Range discipline
# =============================================================================


@pytest.mark.parametrize(
    "kwargs",
    [
        {"semantic_similarity": 1.5},
        {"semantic_similarity": -0.1},
        {"state_weight": 2.0},
        {"confidence": -0.01},
        {"importance": 1.1},
        {"recency_weight": 5.0},
    ],
)
def test_out_of_range_inputs_raise_value_error(kwargs: dict[str, float]) -> None:
    base = {
        "semantic_similarity": 0.5,
        "state_weight": STATE_WEIGHT_ACTIVE,
        "confidence": 0.5,
        "importance": 0.5,
        "recency_weight": 1.0,
    }
    base.update(kwargs)
    with pytest.raises(ValueError):
        score_decision(**base)  # type: ignore[arg-type]


# =============================================================================
# Invariant 4 — Bounded output in [0, 1]
# =============================================================================


@given(
    sim=_unit,
    conf=_unit,
    imp=_unit,
    rec=_unit,
)
def test_score_always_in_unit_interval(sim: float, conf: float, imp: float, rec: float) -> None:
    score = score_decision(
        semantic_similarity=sim,
        state_weight=STATE_WEIGHT_ACTIVE,
        confidence=conf,
        importance=imp,
        recency_weight=rec,
    )
    assert 0.0 <= score <= 1.0
