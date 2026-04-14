"""OpenAI token extractor.

The OpenAI Responses API reports `input_tokens` as fresh + cached combined.
Extractor subtracts cached_tokens to recover the fresh count (the #1 porting
trap per Winston §5.2.2).
"""
from __future__ import annotations

from typing import Any, ClassVar

from ..errors import ProviderExtractionError
from ..models import LLMRequest, LLMResponse, ProviderName

_STOP_REASON_MAP = {
    "stop": "stop",
    "length": "length",
    "tool_calls": "tool_use",
    "function_call": "tool_use",
    "content_filter": "error",
}


def _get(source: Any, *keys: str, default: Any = None) -> Any:
    for key in keys:
        if isinstance(source, dict):
            if key in source:
                return source[key]
        else:
            if hasattr(source, key):
                return getattr(source, key)
    return default


class OpenAIProvider:
    name: ClassVar[ProviderName] = ProviderName.OPENAI

    @staticmethod
    def supported_models() -> list[str]:
        return [
            "gpt-5-preview",
            "gpt-5",
            "gpt-4o",
        ]

    @staticmethod
    def extract_tokens(request: LLMRequest, raw_response: Any) -> LLMResponse:
        try:
            usage = _get(raw_response, "usage")
            if usage is None:
                raise ProviderExtractionError("openai response missing 'usage'")

            details = _get(usage, "input_tokens_details", default={}) or {}
            cached = int(_get(details, "cached_tokens", default=0) or 0)

            raw_input = int(_get(usage, "input_tokens", default=0) or 0)
            input_tokens = raw_input - cached
            if input_tokens < 0:
                raise ProviderExtractionError(
                    f"openai: cached_tokens {cached} > input_tokens {raw_input}"
                )

            output_tokens = int(_get(usage, "output_tokens", default=0) or 0)

            native_stop = _get(raw_response, "stop_reason", "finish_reason", default="stop")
            stop_reason = _STOP_REASON_MAP.get(native_stop, "stop")

            error_message = _get(raw_response, "error_message", default=None)
            if stop_reason == "error" and not error_message:
                error_message = f"openai content filter: {native_stop}"

            finished_at = _get(raw_response, "finished_at")
            if finished_at is None:
                from datetime import UTC, datetime as _dt

                finished_at = _dt.now(UTC)

            return LLMResponse(
                request_id=request.request_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cached,
                cache_write_tokens=0,
                finished_at=finished_at,
                stop_reason=stop_reason,  # type: ignore[arg-type]
                error_message=error_message,
            )
        except ProviderExtractionError:
            raise
        except Exception as exc:
            raise ProviderExtractionError(f"openai extraction failed: {exc}") from exc
