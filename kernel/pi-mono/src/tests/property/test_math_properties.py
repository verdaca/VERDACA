"""Property-based tests for compute_cost (Hypothesis).

Covers Winston §9.2 P1-P5 and Murat's P12-P15 extensions. These are the
primary guards against M1 (float contamination) and M2 (rounding drift).
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from praxis.kernel.cost import (
    CacheRetention,
    Currency,
    LLMResponse,
    ModelPricing,
    ProviderName,
    compute_cost,
)
from praxis.kernel.cost.math import QUANTUM

REQ_ID = "01JPRP000000000000000000S1"


token_strategy = st.integers(min_value=0, max_value=10_000_000)

rate_strategy = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("1000"),
    places=10,
    allow_nan=False,
    allow_infinity=False,
)


@st.composite
def llm_response(draw: st.DrawFn) -> LLMResponse:
    return LLMResponse(
        request_id=REQ_ID,
        input_tokens=draw(token_strategy),
        output_tokens=draw(token_strategy),
        cache_read_tokens=draw(token_strategy),
        cache_write_tokens=draw(token_strategy),
        finished_at=datetime(2026, 4, 12, tzinfo=UTC),
        stop_reason="stop",
    )


@st.composite
def pricing(draw: st.DrawFn) -> ModelPricing:
    return ModelPricing(
        provider=ProviderName.FAKE,
        model_id="fake-model-1",
        cache_retention_key=CacheRetention.NONE,
        currency=Currency.USD,
        input_rate=draw(rate_strategy),
        output_rate=draw(rate_strategy),
        cache_read_rate=draw(rate_strategy),
        cache_write_rate=draw(rate_strategy),
        effective_from=datetime(2026, 1, 1, tzinfo=UTC),
    )


@given(pricing=pricing())
@settings(max_examples=200, deadline=None)
def test_P1_zero_tokens_zero_cost(pricing: ModelPricing) -> None:
    resp = LLMResponse(
        request_id=REQ_ID,
        input_tokens=0,
        output_tokens=0,
        cache_read_tokens=0,
        cache_write_tokens=0,
        finished_at=datetime(2026, 4, 12, tzinfo=UTC),
        stop_reason="stop",
    )
    cost = compute_cost(resp, pricing)
    assert cost.total == Decimal("0")


@given(resp=llm_response(), pricing=pricing())
@settings(max_examples=500, deadline=None)
def test_P2_cost_non_negative(resp: LLMResponse, pricing: ModelPricing) -> None:
    cost = compute_cost(resp, pricing)
    assert cost.input >= Decimal("0")
    assert cost.output >= Decimal("0")
    assert cost.cache_read >= Decimal("0")
    assert cost.cache_write >= Decimal("0")
    assert cost.total >= Decimal("0")


@given(resp=llm_response(), pricing=pricing())
@settings(max_examples=1000, deadline=None)
def test_P3_total_equals_sum_exact(
    resp: LLMResponse, pricing: ModelPricing
) -> None:
    cost = compute_cost(resp, pricing)
    expected = cost.input + cost.output + cost.cache_read + cost.cache_write
    assert cost.total == expected
    assert isinstance(cost.total, Decimal)


@given(
    resp=llm_response(),
    pricing=pricing(),
    k=st.integers(min_value=1, max_value=1000),
)
@settings(max_examples=200, deadline=None)
def test_P4_linearity_in_tokens(
    resp: LLMResponse, pricing: ModelPricing, k: int
) -> None:
    scaled = LLMResponse(
        request_id=REQ_ID,
        input_tokens=resp.input_tokens * k,
        output_tokens=resp.output_tokens * k,
        cache_read_tokens=resp.cache_read_tokens * k,
        cache_write_tokens=resp.cache_write_tokens * k,
        finished_at=datetime(2026, 4, 12, tzinfo=UTC),
        stop_reason="stop",
    )
    single = compute_cost(resp, pricing)
    scaled_cost = compute_cost(scaled, pricing)
    # Each of 4 components may round once during the unscaled computation; the
    # scaled computation also rounds once. When multiplied by k, the unscaled
    # rounding error amplifies by k. Tolerance: (4k + 1) * QUANTUM, bounded above.
    tolerance = Decimal(4 * k + 1) * QUANTUM
    assert abs(scaled_cost.total - k * single.total) <= tolerance


@given(
    resp_list=st.lists(llm_response(), min_size=3, max_size=10),
    pricing=pricing(),
)
@settings(max_examples=100, deadline=None)
def test_P5_aggregation_associative(
    resp_list: list[LLMResponse], pricing: ModelPricing
) -> None:
    totals = [compute_cost(r, pricing).total for r in resp_list]
    forward = sum(totals, Decimal("0"))
    reverse = sum(reversed(totals), Decimal("0"))
    assert forward == reverse


@given(resp=llm_response(), pricing=pricing())
@settings(max_examples=300, deadline=None)
def test_P15_total_tokens_invariant(
    resp: LLMResponse, pricing: ModelPricing
) -> None:
    assert (
        resp.input_tokens
        + resp.output_tokens
        + resp.cache_read_tokens
        + resp.cache_write_tokens
        >= 0
    )
    cost = compute_cost(resp, pricing)
    assert isinstance(cost.input, Decimal)
    assert isinstance(cost.output, Decimal)
    assert isinstance(cost.cache_read, Decimal)
    assert isinstance(cost.cache_write, Decimal)
