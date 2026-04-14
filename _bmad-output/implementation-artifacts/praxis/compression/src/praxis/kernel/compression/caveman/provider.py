"""Caveman Haiku provider — wraps the Anthropic SDK for compression calls.

Pins to claude-haiku-4-5 (cheapest agentic-grade model) per architecture §3.4.2 V-C2.
"""
from __future__ import annotations

import logging

from .errors import CavemanProviderError

logger = logging.getLogger(__name__)

# Pinned model (architecture V-C2: cheapest agentic-grade model for compression cost floor)
HAIKU_MODEL = "claude-haiku-4-5-20251001"
_MAX_OUTPUT_TOKENS = 8096


class HaikuProvider:
    """Thin Anthropic SDK wrapper for Caveman compression calls."""

    def __init__(self, model: str = HAIKU_MODEL) -> None:
        self._model = model
        self._client: object | None = None

    def _get_client(self) -> object:
        if self._client is None:
            try:
                import anthropic  # type: ignore[import-not-found]
                self._client = anthropic.Anthropic()
            except ImportError as exc:
                raise CavemanProviderError(
                    "anthropic SDK not installed; cannot run Caveman compression"
                ) from exc
        return self._client

    async def compress(
        self,
        text: str,
        system_prompt: str,
    ) -> tuple[str, int, int]:
        """Call Haiku to compress *text*.

        Returns:
            (compressed_text, input_tokens, output_tokens)

        Raises:
            CavemanProviderError on API failure.
        """
        client = self._get_client()
        try:
            # Note: using sync client for simplicity (P0); async client in P1
            response = client.messages.create(  # type: ignore[union-attr]
                model=self._model,
                max_tokens=_MAX_OUTPUT_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": text}],
            )
            compressed = response.content[0].text
            return (
                compressed,
                response.usage.input_tokens,
                response.usage.output_tokens,
            )
        except Exception as exc:
            raise CavemanProviderError(f"Haiku API call failed: {exc}") from exc

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
