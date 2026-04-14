"""TONL streaming decoder — AsyncIterator[str] → AsyncIterator[Any].

P0 implementation: buffers chunks until a complete TONL document is received,
then decodes and yields individual items.
"""
from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator
from typing import Any

from ..decode import decode


async def decode_stream(source: AsyncIterable[str]) -> AsyncIterator[Any]:
    """Decode an async stream of TONL text chunks to Python values.

    P0: accumulates all chunks, decodes the complete document, then yields items.
    """
    chunks: list[str] = []
    async for chunk in source:
        chunks.append(chunk)

    full_text = "".join(chunks)
    decoded = decode(full_text)

    if isinstance(decoded, list):
        for item in decoded:
            yield item
    else:
        yield decoded
