"""tests/runtime/registry/test_matching_monotonicity.py — GREEN.

Hypothesis property: adding query tokens that match capability tokens
monotonically increases token_score, never decreases.
"""

from __future__ import annotations

import hypothesis
from hypothesis import given, settings
from hypothesis import strategies as st

from praxis.kernel.runtime.registry.matching import token_score


@settings(
    max_examples=200,
    suppress_health_check=[hypothesis.HealthCheck.filter_too_much],
)
@given(
    base_query=st.text(min_size=1, max_size=50),
    matching_token=st.from_regex(r"[a-z]{2,15}", fullmatch=True),
)
def test_adding_matching_token_does_not_decrease_score(
    base_query: str, matching_token: str
) -> None:
    """S4.3-PROP-003 — monotonicity property (architecture §3.3)."""
    caps = (matching_token.lower(),)
    base = token_score(base_query.lower(), caps)
    enriched = token_score(f"{base_query} {matching_token}".lower(), caps)
    assert enriched >= base - 1e-9, (
        f"Adding matching token decreased score: {base:.4f} → {enriched:.4f}"
    )
