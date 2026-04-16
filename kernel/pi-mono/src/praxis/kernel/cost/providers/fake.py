"""Deterministic test provider. Used in property tests and stress tests."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from ..models import LLMRequest, LLMResponse, ProviderName


class FakeProvider:
    name: ClassVar[ProviderName] = ProviderName.FAKE

    @staticmethod
    def supported_models() -> list[str]:
        return ["fake-model-1", "fake-model-2"]

    @staticmethod
    def extract_tokens(request: LLMRequest, raw_response: Any) -> LLMResponse:
        if not isinstance(raw_response, dict):
            raise TypeError("FakeProvider expects a dict raw_response")
        return LLMResponse(
            request_id=request.request_id,
            input_tokens=int(raw_response.get("input_tokens", 0)),
            output_tokens=int(raw_response.get("output_tokens", 0)),
            cache_read_tokens=int(raw_response.get("cache_read_tokens", 0)),
            cache_write_tokens=int(raw_response.get("cache_write_tokens", 0)),
            finished_at=raw_response.get("finished_at", datetime.now(UTC)),
            stop_reason=raw_response.get("stop_reason", "stop"),
            error_message=raw_response.get("error_message"),
        )
