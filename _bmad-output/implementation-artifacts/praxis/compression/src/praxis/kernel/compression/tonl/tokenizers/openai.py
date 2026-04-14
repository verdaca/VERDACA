"""OpenAI tokenizer adapter — wraps tiktoken with heuristic fallback."""
from __future__ import annotations

import logging
from typing import ClassVar

from .generic import GenericTokenizer

logger = logging.getLogger(__name__)


class OpenAITokenizer:
    """Tokenizer adapter for OpenAI models via tiktoken."""

    name: ClassVar[str] = "openai"
    version: ClassVar[str] = "2026-04-12"

    def __init__(self, model: str = "gpt-4o") -> None:
        self._model = model
        self._enc: object | None = None
        self._fallback = GenericTokenizer()
        self._sdk_available: bool | None = None

    def _get_enc(self) -> object | None:
        if self._sdk_available is False:
            return None
        if self._enc is None:
            try:
                import tiktoken  # type: ignore[import-not-found]
                self._enc = tiktoken.encoding_for_model(self._model)
                self._sdk_available = True
            except (ImportError, KeyError):
                logger.warning("tiktoken not installed or model unknown; using heuristic")
                self._sdk_available = False
        return self._enc

    def count(self, text: str) -> int:
        enc = self._get_enc()
        if enc is None:
            return self._fallback.count(text)
        try:
            return len(enc.encode(text))  # type: ignore[union-attr]
        except Exception:
            logger.warning("tiktoken encode failed; using heuristic", exc_info=True)
            return self._fallback.count(text)

    def encode_bytes(self, text: str) -> bytes:
        enc = self._get_enc()
        if enc is None:
            return self._fallback.encode_bytes(text)
        try:
            token_ids = enc.encode(text)  # type: ignore[union-attr]
            return bytes(token_ids[:4096])  # truncate for large inputs
        except Exception:
            return self._fallback.encode_bytes(text)

    def byte_boundary_positions(self, text: str) -> list[int]:
        enc = self._get_enc()
        if enc is None:
            return self._fallback.byte_boundary_positions(text)
        try:
            encoded = text.encode("utf-8")
            token_ids = enc.encode(text)  # type: ignore[union-attr]
            # Approximate: distribute byte positions evenly across token boundaries
            if not token_ids:
                return []
            step = max(1, len(encoded) // len(token_ids))
            return [i * step for i in range(len(token_ids))]
        except Exception:
            return self._fallback.byte_boundary_positions(text)
