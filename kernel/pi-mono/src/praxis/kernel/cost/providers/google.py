"""Google Gemini token extractor. Handles camelCase and snake_case variants."""
from __future__ import annotations

from typing import Any, ClassVar

from ..errors import ProviderExtractionError
from ..models import LLMRequest, LLMResponse, ProviderName

_STOP_REASON_MAP = {
    "STOP": "stop",
    "MAX_TOKENS": "length",
    "SAFETY": "error",
    "RECITATION": "error",
    "TOOL_USE": "tool_use",
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


def _get_any(source: Any, candidates: list[str], default: Any = None) -> Any:
    for key in candidates:
        val = _get(source, key, default=None)
        if val is not None:
            return val
    return default


class GoogleProvider:
    name: ClassVar[ProviderName] = ProviderName.GOOGLE

    @staticmethod
    def supported_models() -> list[str]:
        return [
            "gemini-3.1-pro",
            "gemini-3.1-flash",
        ]

    @staticmethod
    def extract_tokens(request: LLMRequest, raw_response: Any) -> LLMResponse:
        try:
            usage = _get(raw_response, "usage", "usageMetadata", "usage_metadata")
            if usage is None:
                raise ProviderExtractionError("google response missing usage block")

            input_tokens = int(
                _get_any(usage, ["inputTokens", "input_tokens", "promptTokenCount"], 0)
                or 0
            )
            output_tokens = int(
                _get_any(
                    usage,
                    ["outputTokens", "output_tokens", "candidatesTokenCount"],
                    0,
                )
                or 0
            )
            cache_read = int(
                _get_any(
                    usage,
                    ["cacheReadInputTokens", "cache_read_input_tokens", "cachedContentTokenCount"],
                    0,
                )
                or 0
            )
            cache_write = int(
                _get_any(
                    usage,
                    ["cacheWriteInputTokens", "cache_write_input_tokens"],
                    0,
                )
                or 0
            )

            native_stop = _get(raw_response, "finishReason", "finish_reason", default="STOP")
            stop_reason = _STOP_REASON_MAP.get(native_stop, "stop")

            error_message = _get(raw_response, "errorMessage", "error_message", default=None)
            if stop_reason == "error" and not error_message:
                error_message = f"google safety/recitation: {native_stop}"

            finished_at = _get(raw_response, "finished_at", "finishedAt")
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
            raise ProviderExtractionError(f"google extraction failed: {exc}") from exc
