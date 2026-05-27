"""In-memory nonce replay protection."""

from __future__ import annotations

import asyncio


class NonceReplayError(ValueError):
    """Raised when a previously seen nonce is presented again."""


class NonceStore:
    """In-memory nonce replay protection."""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._lock = asyncio.Lock()

    async def check_and_mark(self, nonce: str) -> None:
        async with self._lock:
            if nonce in self._seen:
                raise NonceReplayError(nonce)
            self._seen.add(nonce)


__all__ = ["NonceReplayError", "NonceStore"]
