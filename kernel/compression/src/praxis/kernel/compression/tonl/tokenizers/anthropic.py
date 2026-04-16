"""Anthropic tokenizer adapter — wraps anthropic SDK count_tokens with heuristic fallback."""
from __future__ import annotations

import logging
from typing import ClassVar

from .generic import GenericTokenizer

logger = logging.getLogger(__name__)


class AnthropicTokenizer:
    """Tokenizer adapter for Claude models.

    Falls back to GenericTokenizer if the anthropic SDK is not installed or
    the count_tokens call fails (network unavailable, etc.).
    """

    name: ClassVar[str] = "anthropic"
    version: ClassVar[str] = "2026-04-12"

    def __init__(self, model: str = "claude-opus-4-6") -> None:
        self._model = model
        self._client: object | None = None
        self._fallback = GenericTokenizer()
        self._sdk_available: bool | None = None

    def _get_client(self) -> object | None:
        if self._sdk_available is False:
            return None
        if self._client is None:
            try:
                import anthropic  # type: ignore[import-not-found]
                self._client = anthropic.Anthropic()
                self._sdk_available = True
            except ImportError:
                logger.warning("anthropic SDK not installed; using heuristic tokenizer")
                self._sdk_available = False
        return self._client

    def count(self, text: str) -> int:
        client = self._get_client()
        if client is None:
            return self._fallback.count(text)
        try:
            import anthropic  # type: ignore[import-not-found]
            response = client.messages.count_tokens(  # type: ignore[attr-defined]
                model=self._model,
                messages=[{"role": "user", "content": text}],
            )
            return response.input_tokens
        except Exception:
            logger.warning("anthropic count_tokens failed; using heuristic", exc_info=True)
            return self._fallback.count(text)

    def encode_bytes(self, text: str) -> bytes:
        return text.encode("utf-8")

    def byte_boundary_positions(self, text: str) -> list[int]:
        return self._fallback.byte_boundary_positions(text)
