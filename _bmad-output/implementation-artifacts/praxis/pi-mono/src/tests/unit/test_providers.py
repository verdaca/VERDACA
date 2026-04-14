"""Unit tests for provider token extractors."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from praxis.kernel.cost import (
    LLMRequest,
    ProviderExtractionError,
    ProviderName,
)
from praxis.kernel.cost.providers import (
    AnthropicProvider,
    FakeProvider,
    GoogleProvider,
    OpenAIProvider,
    get_provider,
    registered_providers,
)

REQ_ID = "01JPRVT00000000000000000S1"


def _req(provider: ProviderName, model_id: str = "m") -> LLMRequest:
    return LLMRequest(
        request_id=REQ_ID,
        provider=provider,
        model_id=model_id,
        started_at=datetime(2026, 4, 12, tzinfo=UTC),
    )


class TestAnthropicProvider:
    def test_simple_response(self) -> None:
        raw = {
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 500,
            },
            "finished_at": datetime(2026, 4, 12, 14, 1, tzinfo=UTC),
        }
        resp = AnthropicProvider.extract_tokens(_req(ProviderName.ANTHROPIC), raw)
        assert resp.input_tokens == 1000
        assert resp.output_tokens == 500
        assert resp.cache_read_tokens == 0
        assert resp.cache_write_tokens == 0
        assert resp.stop_reason == "stop"

    def test_with_short_cache(self) -> None:
        raw = {
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_creation_input_tokens": 200,
                "cache_read_input_tokens": 300,
            },
            "finished_at": datetime(2026, 4, 12, 14, 1, tzinfo=UTC),
        }
        resp = AnthropicProvider.extract_tokens(_req(ProviderName.ANTHROPIC), raw)
        assert resp.input_tokens == 100
        assert resp.cache_write_tokens == 200
        assert resp.cache_read_tokens == 300

    def test_stop_reason_max_tokens(self) -> None:
        raw = {
            "stop_reason": "max_tokens",
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "finished_at": datetime(2026, 4, 12, tzinfo=UTC),
        }
        resp = AnthropicProvider.extract_tokens(_req(ProviderName.ANTHROPIC), raw)
        assert resp.stop_reason == "length"

    def test_stop_reason_tool_use(self) -> None:
        raw = {
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "finished_at": datetime(2026, 4, 12, tzinfo=UTC),
        }
        resp = AnthropicProvider.extract_tokens(_req(ProviderName.ANTHROPIC), raw)
        assert resp.stop_reason == "tool_use"

    def test_missing_usage_raises(self) -> None:
        raw = {"stop_reason": "end_turn"}
        with pytest.raises(ProviderExtractionError):
            AnthropicProvider.extract_tokens(_req(ProviderName.ANTHROPIC), raw)


class TestOpenAIProvider:
    def test_cached_tokens_subtracted(self) -> None:
        raw = {
            "stop_reason": "stop",
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 500,
                "input_tokens_details": {"cached_tokens": 300},
            },
            "finished_at": datetime(2026, 4, 12, tzinfo=UTC),
        }
        resp = OpenAIProvider.extract_tokens(_req(ProviderName.OPENAI), raw)
        assert resp.input_tokens == 700  # fresh = 1000 - 300 cached
        assert resp.cache_read_tokens == 300
        assert resp.cache_write_tokens == 0

    def test_no_cached_details_path(self) -> None:
        raw = {
            "stop_reason": "stop",
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "finished_at": datetime(2026, 4, 12, tzinfo=UTC),
        }
        resp = OpenAIProvider.extract_tokens(_req(ProviderName.OPENAI), raw)
        assert resp.input_tokens == 100
        assert resp.cache_read_tokens == 0

    def test_cached_exceeds_input_raises(self) -> None:
        raw = {
            "usage": {
                "input_tokens": 100,
                "output_tokens": 0,
                "input_tokens_details": {"cached_tokens": 200},
            },
            "finished_at": datetime(2026, 4, 12, tzinfo=UTC),
        }
        with pytest.raises(ProviderExtractionError):
            OpenAIProvider.extract_tokens(_req(ProviderName.OPENAI), raw)


class TestGoogleProvider:
    def test_camel_case(self) -> None:
        raw = {
            "finishReason": "STOP",
            "usage": {
                "inputTokens": 1000,
                "outputTokens": 500,
                "cacheReadInputTokens": 200,
                "cacheWriteInputTokens": 100,
            },
            "finishedAt": datetime(2026, 4, 12, tzinfo=UTC),
        }
        resp = GoogleProvider.extract_tokens(_req(ProviderName.GOOGLE), raw)
        assert resp.input_tokens == 1000
        assert resp.output_tokens == 500
        assert resp.cache_read_tokens == 200
        assert resp.cache_write_tokens == 100

    def test_snake_case(self) -> None:
        raw = {
            "finish_reason": "STOP",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
                "cache_read_input_tokens": 2,
                "cache_write_input_tokens": 1,
            },
            "finished_at": datetime(2026, 4, 12, tzinfo=UTC),
        }
        resp = GoogleProvider.extract_tokens(_req(ProviderName.GOOGLE), raw)
        assert resp.input_tokens == 10
        assert resp.cache_read_tokens == 2
        assert resp.cache_write_tokens == 1

    def test_safety_stop_is_error(self) -> None:
        raw = {
            "finishReason": "SAFETY",
            "usage": {"inputTokens": 0, "outputTokens": 0},
            "finishedAt": datetime(2026, 4, 12, tzinfo=UTC),
        }
        resp = GoogleProvider.extract_tokens(_req(ProviderName.GOOGLE), raw)
        assert resp.stop_reason == "error"
        assert resp.error_message is not None


class TestFakeProvider:
    def test_deterministic(self) -> None:
        raw = {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_tokens": 10,
            "cache_write_tokens": 5,
            "finished_at": datetime(2026, 4, 12, tzinfo=UTC),
            "stop_reason": "stop",
        }
        r1 = FakeProvider.extract_tokens(_req(ProviderName.FAKE), raw)
        r2 = FakeProvider.extract_tokens(_req(ProviderName.FAKE), raw)
        assert r1 == r2


class TestRegistry:
    def test_lookup_by_name(self) -> None:
        assert get_provider(ProviderName.ANTHROPIC) is AnthropicProvider
        assert get_provider(ProviderName.OPENAI) is OpenAIProvider
        assert get_provider(ProviderName.GOOGLE) is GoogleProvider
        assert get_provider(ProviderName.FAKE) is FakeProvider

    def test_registered_providers_includes_all(self) -> None:
        names = registered_providers()
        assert ProviderName.ANTHROPIC in names
        assert ProviderName.OPENAI in names
        assert ProviderName.GOOGLE in names
        assert ProviderName.FAKE in names
