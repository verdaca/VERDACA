"""Unit tests — TONL async streaming encoder and decoder.

Covers: encode_stream, decode_stream — single-chunk and multi-chunk paths,
        round-trip invariant, list vs scalar decoded output.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
import pytest_asyncio

from praxis.kernel.compression.tonl.stream.encoder import encode_stream
from praxis.kernel.compression.tonl.stream.decoder import decode_stream
from praxis.kernel.compression.tonl.encode import encode
from praxis.kernel.compression.tonl.decode import decode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _aiter(items):
    for item in items:
        yield item


async def _collect_async(aiter):
    results = []
    async for item in aiter:
        results.append(item)
    return results


# ---------------------------------------------------------------------------
# encode_stream
# ---------------------------------------------------------------------------

class TestEncodeStream:
    @pytest.mark.asyncio
    async def test_single_item_list(self):
        source = _aiter([{"role": "user", "content": "hello"}])
        chunks = await _collect_async(encode_stream(source))
        assert len(chunks) == 1
        assert isinstance(chunks[0], str)

    @pytest.mark.asyncio
    async def test_multiple_items_encoded_as_list(self):
        items = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "world"},
            {"role": "user", "content": "bye"},
        ]
        source = _aiter(items)
        chunks = await _collect_async(encode_stream(source))
        assert len(chunks) == 1
        # Must decode back to the original list
        recovered = decode(chunks[0])
        assert recovered == items

    @pytest.mark.asyncio
    async def test_empty_stream_produces_empty_list(self):
        source = _aiter([])
        chunks = await _collect_async(encode_stream(source))
        assert len(chunks) == 1
        recovered = decode(chunks[0])
        assert recovered == []

    @pytest.mark.asyncio
    async def test_round_trip_preserves_decimal(self):
        items = [{"cost": Decimal("1.23")}, {"cost": Decimal("4.56")}]
        source = _aiter(items)
        chunks = await _collect_async(encode_stream(source))
        recovered = decode(chunks[0])
        assert recovered == items

    @pytest.mark.asyncio
    async def test_tokenizer_param_accepted(self):
        items = [{"a": 1}, {"a": 2}]
        source = _aiter(items)
        chunks = await _collect_async(encode_stream(source, tokenizer="generic"))
        assert len(chunks) == 1
        recovered = decode(chunks[0])
        assert recovered == items


# ---------------------------------------------------------------------------
# decode_stream
# ---------------------------------------------------------------------------

class TestDecodeStream:
    @pytest.mark.asyncio
    async def test_decode_list_payload_yields_items(self):
        items = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        encoded = encode(items)
        source = _aiter([encoded])
        decoded = await _collect_async(decode_stream(source))
        assert decoded == items

    @pytest.mark.asyncio
    async def test_decode_chunked_input(self):
        items = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "world"},
        ]
        encoded = encode(items)
        # Split into two chunks
        mid = len(encoded) // 2
        chunks = [encoded[:mid], encoded[mid:]]
        source = _aiter(chunks)
        decoded = await _collect_async(decode_stream(source))
        assert decoded == items

    @pytest.mark.asyncio
    async def test_decode_scalar_yields_single_item(self):
        payload = {"a": 1, "b": "text"}
        encoded = encode(payload)
        source = _aiter([encoded])
        decoded = await _collect_async(decode_stream(source))
        assert len(decoded) == 1
        assert decoded[0] == payload

    @pytest.mark.asyncio
    async def test_decode_empty_list(self):
        encoded = encode([])
        source = _aiter([encoded])
        decoded = await _collect_async(decode_stream(source))
        assert decoded == []

    @pytest.mark.asyncio
    async def test_round_trip_end_to_end(self):
        items = [
            {"role": "user", "content": "msg 1"},
            {"role": "assistant", "content": "msg 2"},
            {"role": "user", "content": "msg 3"},
        ]
        # encode → stream → decode → stream
        encoded_chunks = await _collect_async(encode_stream(_aiter(items)))
        decoded = await _collect_async(decode_stream(_aiter(encoded_chunks)))
        assert decoded == items

    @pytest.mark.asyncio
    async def test_round_trip_preserves_decimal(self):
        items = [{"cost": Decimal("9.99")}, {"cost": Decimal("0.01")}]
        encoded_chunks = await _collect_async(encode_stream(_aiter(items)))
        decoded = await _collect_async(decode_stream(_aiter(encoded_chunks)))
        assert decoded == items
