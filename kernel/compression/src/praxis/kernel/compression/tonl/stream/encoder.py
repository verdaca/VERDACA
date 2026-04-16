"""TONL streaming encoder — AsyncIterator[Any] → AsyncIterator[str].

P0 implementation: buffers the full input before encoding (not truly O(1)).
Streaming is the correct interface for large payloads; the P0 implementation
satisfies the API contract and will be replaced by a true streaming encoder in P1.
"""
from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator
from typing import Any

from ..encode import encode


async def encode_stream(
    source: AsyncIterable[Any],
    *,
    tokenizer: str | None = None,
) -> AsyncIterator[str]:
    """Encode an async stream of Python values to TONL text chunks.

    P0: buffers the entire source, then emits the encoded result as a single chunk.
    """
    items: list[Any] = []
    async for item in source:
        items.append(item)

    encoded = encode(items, tokenizer=tokenizer)
    yield encoded
