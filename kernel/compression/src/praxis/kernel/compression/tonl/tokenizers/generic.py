"""Generic (heuristic) tokenizer — fallback when no SDK is available."""
from __future__ import annotations

from typing import ClassVar


class GenericTokenizer:
    """Heuristic tokenizer using ~4 chars/token approximation.

    Used when provider SDK libraries are absent (offline tests, CI without
    external deps). Never used in production when a real tokenizer is available.
    """

    name: ClassVar[str] = "generic"
    version: ClassVar[str] = "heuristic-1.0"

    # Anthropic's rule-of-thumb: 1 token ≈ 4 English characters
    _CHARS_PER_TOKEN: float = 4.0

    def count(self, text: str) -> int:
        return max(1, round(len(text) / self._CHARS_PER_TOKEN))

    def encode_bytes(self, text: str) -> bytes:
        # No real token IDs — return UTF-8 bytes as a proxy
        return text.encode("utf-8")

    def byte_boundary_positions(self, text: str) -> list[int]:
        # Approximate: every 4-char boundary is a token boundary
        encoded = text.encode("utf-8")
        step = max(1, round(self._CHARS_PER_TOKEN))
        return list(range(0, len(encoded), step))
