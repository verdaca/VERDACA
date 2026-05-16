"""Caveman Haiku provider — routes compression calls through LLMProxyPort.

Pins to claude-haiku-4-5 (cheapest agentic-grade model) per architecture §3.4.2 V-C2.
Consumes a Verdaca LLMProxyPort by caller-DI rather than constructing an LLM SDK
directly, so engineers can drive Caveman via their own keys. The api_base / routing
target is configured by the caller-supplied port; not handled here.
"""
from __future__ import annotations

import uuid

from praxis.ports.common import Message
from praxis.ports.llm_proxy import LLMProxyPort, LLMRequest

from .errors import CavemanProviderError

# Pinned model (architecture V-C2: cheapest agentic-grade model for compression cost floor).
# Exact routing identifier is confirmed when DIAL routing lands.
HAIKU_MODEL = "claude-haiku-4-5"
_MAX_OUTPUT_TOKENS = 8096
_SCHEMA_VERSION = 1
_PROVIDER = "anthropic"


class HaikuProvider:
    """Caveman compression provider — consumes a Verdaca LLMProxyPort."""

    def __init__(self, llm_proxy: LLMProxyPort, model: str = HAIKU_MODEL) -> None:
        self._llm_proxy = llm_proxy
        self._model = model

    async def compress(
        self,
        text: str,
        system_prompt: str,
    ) -> tuple[str, int, int]:
        """Call Haiku (via LLMProxyPort) to compress *text*.

        Returns:
            (compressed_text, input_tokens, output_tokens)

        Raises:
            CavemanProviderError on proxy/port failure.
        """
        correlation_id = uuid.uuid4().hex
        request = LLMRequest(
            schema_version=_SCHEMA_VERSION,
            correlation_id=correlation_id,
            idempotency_key=uuid.uuid4().hex,
            provider=_PROVIDER,
            model=self._model,
            messages=[
                Message(
                    schema_version=_SCHEMA_VERSION,
                    correlation_id=correlation_id,
                    role="system",
                    content=system_prompt,
                ),
                Message(
                    schema_version=_SCHEMA_VERSION,
                    correlation_id=correlation_id,
                    role="user",
                    content=text,
                ),
            ],
            max_tokens=_MAX_OUTPUT_TOKENS,
            temperature=0.0,
            compression_hint="none",
        )
        try:
            # LLMProxyPort.call() is sync (ADR-9.1.2-6 §3 idempotency table);
            # called directly from async compress() — same pattern as the prior
            # sync Anthropic client call.
            response = self._llm_proxy.call(request)
        except Exception as exc:
            raise CavemanProviderError(f"Haiku LLMProxy call failed: {exc}") from exc
        return (
            response.content,
            response.input_tokens,
            response.output_tokens,
        )

    async def compress_with_fix(
        self,
        original: str,
        compressed: str,
        errors: list[str],
        system_prompt: str,
    ) -> tuple[str, int, int]:
        """Targeted-fix retry — ask Haiku to repair specific validation errors."""
        fix_prompt = (
            f"Here is the original text:\n---\n{original}\n---\n\n"
            f"Here is your compressed version:\n---\n{compressed}\n---\n\n"
            f"These errors were detected: {', '.join(errors)}.\n\n"
            "Return a corrected version that preserves the original wherever it differs "
            "from what you produced. Do NOT recompress the whole text — fix only the issues."
        )
        return await self.compress(fix_prompt, system_prompt)
