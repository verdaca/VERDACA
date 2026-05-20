"""Anthropic token extractor."""
from __future__ import annotations

from typing import Any, ClassVar

from ..errors import ProviderExtractionError
from ..models import LLMRequest, LLMResponse, ProviderName

_STOP_REASON_MAP = {
    "end_turn": "stop",
    "stop_sequence": "stop",
    "max_tokens": "length",
    "tool_use": "tool_use",
    "error": "error",
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


class AnthropicProvider:
    name: ClassVar[ProviderName] = ProviderName.ANTHROPIC

    @staticmethod
    def supported_models() -> list[str]:
        return [
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-haiku-4-5",
        ]

    @staticmethod
    def extract_tokens(request: LLMRequest, raw_response: Any) -> LLMResponse:
        try:
            usage = _get(raw_response, "usage")
            if usage is None:
                raise ProviderExtractionError("anthropic response missing 'usage'")

            input_tokens = int(_get(usage, "input_tokens", default=0) or 0)
            output_tokens = int(_get(usage, "output_tokens", default=0) or 0)
            cache_read = int(_get(usage, "cache_read_input_tokens", default=0) or 0)
            cache_write = int(
                _get(usage, "cache_creation_input_tokens", default=0) or 0
            )

            native_stop = _get(raw_response, "stop_reason", default="end_turn")
            stop_reason = _STOP_REASON_MAP.get(native_stop, "stop")

            error_message = _get(raw_response, "error_message", default=None)
            if stop_reason == "error" and not error_message:
                error_message = "anthropic error (no message provided)"

            finished_at = _get(raw_response, "finished_at")
            if finished_at is None:
                from datetime import UTC, datetime as _dt

                finished_at = _dt.now(UTC)

            return LLMResponse(
                request_id=request.request_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                finished_at=finished_at,
                stop_reason=stop_reason,  # type: ignore[arg-type]
                error_message=error_message,
            )
        except ProviderExtractionError:
            raise
        except Exception as exc:
            raise ProviderExtractionError(
                f"anthropic extraction failed: {exc}"
            ) from exc
