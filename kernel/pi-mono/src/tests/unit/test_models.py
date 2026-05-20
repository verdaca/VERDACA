"""Unit tests for Pydantic validators in praxis.kernel.cost.models."""
from __future__ import annotations

from datetime import UTC, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from praxis.kernel.cost import (
    CacheRetention,
    CostAmount,
    CostRecord,
    Currency,
    Filter,
    LLMRequest,
    LLMResponse,
    ModelPricing,
    ProviderName,
    TimeRange,
)


REQ_ID = "01JMDES00000000000000000S1"


class TestLLMRequest:
    def test_happy_path(self) -> None:
        req = LLMRequest(
            request_id=REQ_ID,
            provider=ProviderName.ANTHROPIC,
            model_id="claude-opus-4-6",
            started_at=datetime(2026, 4, 12, tzinfo=UTC),
        )
        assert req.request_id == REQ_ID

    def test_rejects_naive_datetime(self) -> None:
        with pytest.raises(ValidationError):
            LLMRequest(
                request_id=REQ_ID,
                provider=ProviderName.ANTHROPIC,
                model_id="claude-opus-4-6",
                started_at=datetime(2026, 4, 12),
            )

    def test_rejects_bad_ulid(self) -> None:
        with pytest.raises(ValidationError):
            LLMRequest(
                request_id="not-a-ulid",
                provider=ProviderName.ANTHROPIC,
                model_id="claude-opus-4-6",
                started_at=datetime(2026, 4, 12, tzinfo=UTC),
            )

    def test_tag_key_count_limit(self) -> None:
        tags = {f"k{i}": "v" for i in range(33)}
        with pytest.raises(ValidationError):
            LLMRequest(
                request_id=REQ_ID,
                provider=ProviderName.ANTHROPIC,
                model_id="claude-opus-4-6",
                started_at=datetime(2026, 4, 12, tzinfo=UTC),
                tags=tags,
            )

    def test_tag_value_length_limit(self) -> None:
        with pytest.raises(ValidationError):
            LLMRequest(
                request_id=REQ_ID,
                provider=ProviderName.ANTHROPIC,
                model_id="claude-opus-4-6",
                started_at=datetime(2026, 4, 12, tzinfo=UTC),
                tags={"k": "x" * 129},
            )


class TestLLMResponse:
    def test_negative_tokens_rejected(self) -> None:
        for field in (
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
        ):
            with pytest.raises(ValidationError):
                LLMResponse(
                    request_id=REQ_ID,
                    input_tokens=0 if field != "input_tokens" else -1,
                    output_tokens=0 if field != "output_tokens" else -1,
                    cache_read_tokens=0 if field != "cache_read_tokens" else -1,
                    cache_write_tokens=0 if field != "cache_write_tokens" else -1,
                    finished_at=datetime(2026, 4, 12, tzinfo=UTC),
                    stop_reason="stop",
                )

    def test_error_requires_message(self) -> None:
        with pytest.raises(ValidationError):
            LLMResponse(
                request_id=REQ_ID,
                input_tokens=0,
                output_tokens=0,
                finished_at=datetime(2026, 4, 12, tzinfo=UTC),
                stop_reason="error",
            )

    def test_error_with_message_ok(self) -> None:
        resp = LLMResponse(
            request_id=REQ_ID,
            input_tokens=0,
            output_tokens=0,
            finished_at=datetime(2026, 4, 12, tzinfo=UTC),
            stop_reason="error",
            error_message="transient failure",
        )
        assert resp.stop_reason == "error"


class TestCostAmount:
    def test_happy_path(self) -> None:
        cost = CostAmount(
            input=Decimal("1.0"),
            output=Decimal("2.0"),
            cache_read=Decimal("0.1"),
            cache_write=Decimal("0.5"),
            total=Decimal("3.6"),
        )
        assert cost.total == Decimal("3.6")

    def test_total_sum_invariant(self) -> None:
        with pytest.raises(ValidationError):
            CostAmount(
                input=Decimal("1.0"),
                output=Decimal("2.0"),
                cache_read=Decimal("0.1"),
                cache_write=Decimal("0.5"),
                total=Decimal("99.0"),
            )

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValidationError):
            CostAmount(
                input=Decimal("-1.0"),
                output=Decimal("2.0"),
                cache_read=Decimal("0.1"),
                cache_write=Decimal("0.5"),
                total=Decimal("1.6"),
            )

    def test_rejects_float_input(self) -> None:
        with pytest.raises(ValidationError):
            CostAmount(
                input=1.0,
                output=Decimal("0"),
                cache_read=Decimal("0"),
                cache_write=Decimal("0"),
                total=Decimal("1"),
            )


class TestModelPricing:
    def test_happy_path(self) -> None:
        p = ModelPricing(
            provider=ProviderName.ANTHROPIC,
            model_id="claude-opus-4-6",
            cache_retention_key=CacheRetention.NONE,
            currency=Currency.USD,
            input_rate=Decimal("15.0"),
            output_rate=Decimal("75.0"),
            cache_read_rate=Decimal("1.5"),
            cache_write_rate=Decimal("18.75"),
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert p.input_rate == Decimal("15.0")

    def test_rejects_negative_rate(self) -> None:
        with pytest.raises(ValidationError):
            ModelPricing(
                provider=ProviderName.ANTHROPIC,
                model_id="claude-opus-4-6",
                input_rate=Decimal("-1.0"),
                output_rate=Decimal("75.0"),
                cache_read_rate=Decimal("1.5"),
                cache_write_rate=Decimal("18.75"),
                effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            )

    def test_rejects_bad_effective_until(self) -> None:
        with pytest.raises(ValidationError):
            ModelPricing(
                provider=ProviderName.ANTHROPIC,
                model_id="claude-opus-4-6",
                input_rate=Decimal("15.0"),
                output_rate=Decimal("75.0"),
                cache_read_rate=Decimal("1.5"),
                cache_write_rate=Decimal("18.75"),
                effective_from=datetime(2026, 1, 1, tzinfo=UTC),
                effective_until=datetime(2025, 1, 1, tzinfo=UTC),
            )

    def test_rejects_float_rate(self) -> None:
        with pytest.raises(ValidationError):
            ModelPricing(
                provider=ProviderName.ANTHROPIC,
                model_id="claude-opus-4-6",
                input_rate=15.0,
                output_rate=Decimal("75.0"),
                cache_read_rate=Decimal("1.5"),
                cache_write_rate=Decimal("18.75"),
                effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            )


class TestTimeRange:
    def test_happy_path(self) -> None:
        tr = TimeRange(
            start=datetime(2026, 4, 1, tzinfo=UTC),
            end=datetime(2026, 4, 30, tzinfo=UTC),
        )
        assert tr.end > tr.start

    def test_rejects_end_before_start(self) -> None:
        with pytest.raises(ValidationError):
            TimeRange(
                start=datetime(2026, 4, 30, tzinfo=UTC),
                end=datetime(2026, 4, 1, tzinfo=UTC),
            )

    def test_rejects_equal_bounds(self) -> None:
        dt = datetime(2026, 4, 30, tzinfo=UTC)
        with pytest.raises(ValidationError):
            TimeRange(start=dt, end=dt)


class TestFilter:
    def test_empty_filter_ok(self) -> None:
        f = Filter()
        assert f.provider is None
