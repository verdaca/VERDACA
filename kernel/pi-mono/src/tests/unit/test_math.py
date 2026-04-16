"""Unit tests for praxis.kernel.cost.math.compute_cost."""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, getcontext

import pytest

from praxis.kernel.cost import (
    CacheRetention,
    CostAmount,
    Currency,
    LLMResponse,
    ModelPricing,
    ProviderName,
    compute_cost,
)
from praxis.kernel.cost.math import QUANTUM

REQ_ID = "01JMATH00000000000000000S1"


def _resp(i: int, o: int, cr: int = 0, cw: int = 0) -> LLMResponse:
    return LLMResponse(
        request_id=REQ_ID,
        input_tokens=i,
        output_tokens=o,
        cache_read_tokens=cr,
        cache_write_tokens=cw,
        finished_at=datetime(2026, 4, 12, tzinfo=UTC),
        stop_reason="stop",
    )


def _pricing(
    inp: str = "3.0",
    out: str = "15.0",
    cr: str = "0.3",
    cw: str = "3.75",
) -> ModelPricing:
    return ModelPricing(
        provider=ProviderName.FAKE,
        model_id="fake-model-1",
        cache_retention_key=CacheRetention.NONE,
        currency=Currency.USD,
        input_rate=Decimal(inp),
        output_rate=Decimal(out),
        cache_read_rate=Decimal(cr),
        cache_write_rate=Decimal(cw),
        effective_from=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestComputeCost:
    def test_zero_tokens_zero_cost(self) -> None:
        cost = compute_cost(_resp(0, 0, 0, 0), _pricing())
        assert cost.input == Decimal("0")
        assert cost.output == Decimal("0")
        assert cost.cache_read == Decimal("0")
        assert cost.cache_write == Decimal("0")
        assert cost.total == Decimal("0")

    def test_input_only(self) -> None:
        cost = compute_cost(_resp(1_000_000, 0), _pricing(inp="3.0"))
        assert cost.input == Decimal("3.0000000000")
        assert cost.output == Decimal("0")
        assert cost.total == Decimal("3.0000000000")

    def test_output_only(self) -> None:
        cost = compute_cost(_resp(0, 1_000_000), _pricing(out="15.0"))
        assert cost.output == Decimal("15.0000000000")
        assert cost.total == Decimal("15.0000000000")

    def test_cache_read_only(self) -> None:
        cost = compute_cost(_resp(0, 0, 1_000_000, 0), _pricing(cr="0.3"))
        assert cost.cache_read == Decimal("0.3000000000")
        assert cost.total == Decimal("0.3000000000")

    def test_cache_write_only(self) -> None:
        cost = compute_cost(_resp(0, 0, 0, 1_000_000), _pricing(cw="3.75"))
        assert cost.cache_write == Decimal("3.7500000000")
        assert cost.total == Decimal("3.7500000000")

    def test_all_four_classes(self) -> None:
        cost = compute_cost(
            _resp(1000, 500, 200, 100),
            _pricing(inp="3.0", out="15.0", cr="0.3", cw="3.75"),
        )
        # 1000*3/1e6 + 500*15/1e6 + 200*0.3/1e6 + 100*3.75/1e6
        # = 0.003 + 0.0075 + 0.00006 + 0.000375
        # = 0.010935
        assert cost.input == Decimal("0.0030000000")
        assert cost.output == Decimal("0.0075000000")
        assert cost.cache_read == Decimal("0.0000600000")
        assert cost.cache_write == Decimal("0.0003750000")
        assert cost.total == Decimal("0.0109350000")

    def test_total_equals_sum_exact(self) -> None:
        cost = compute_cost(
            _resp(12345, 67890, 1111, 222),
            _pricing(inp="3.14", out="2.71", cr="0.33", cw="3.99"),
        )
        assert (
            cost.total
            == cost.input + cost.output + cost.cache_read + cost.cache_write
        )

    def test_large_tokens_one_billion(self) -> None:
        cost = compute_cost(_resp(1_000_000_000, 0), _pricing(inp="1.0"))
        assert cost.input == Decimal("1000.0000000000")
        assert cost.total == Decimal("1000.0000000000")

    def test_zero_input_rate_no_error(self) -> None:
        cost = compute_cost(_resp(1_000_000, 0), _pricing(inp="0"))
        assert cost.input == Decimal("0")
        assert cost.total == Decimal("0")

    def test_returns_decimal_types(self) -> None:
        cost = compute_cost(_resp(100, 50), _pricing())
        assert isinstance(cost.input, Decimal)
        assert isinstance(cost.output, Decimal)
        assert isinstance(cost.cache_read, Decimal)
        assert isinstance(cost.cache_write, Decimal)
        assert isinstance(cost.total, Decimal)

    def test_result_is_cost_amount(self) -> None:
        cost = compute_cost(_resp(100, 50), _pricing())
        assert isinstance(cost, CostAmount)
        assert cost.currency == Currency.USD

    def test_global_decimal_context_untouched(self) -> None:
        before = getcontext().prec
        compute_cost(_resp(1234, 5678, 9, 12), _pricing())
        assert getcontext().prec == before

    def test_banker_rounding_halfway(self) -> None:
        # Construct a value that ends in exactly ...5 at the 11th decimal place
        # token_count * rate / 1e6 must fall on the banker's boundary
        # 5 tokens * 0.00003 / 1e6 = 1.5e-10 → rounds to 2e-10 (even)
        pricing = _pricing(inp="0.00003", out="0", cr="0", cw="0")
        cost = compute_cost(_resp(5, 0), pricing)
        # 5 * 0.00003 / 1e6 = 1.5e-10 → banker's rounds to even → 2e-10
        assert cost.input == Decimal("2e-10").quantize(QUANTUM)
