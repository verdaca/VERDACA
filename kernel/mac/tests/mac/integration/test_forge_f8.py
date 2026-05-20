"""Compression Forge F8 integration tests — mac/test-strategy.md v0.3 §6.4.

Covers ``MAC-T-INT-FORGE-F8-01/02``. Consumes Forge F8 only (F-2 TONL
deferred per arch §10.4 + test-strategy §11.3 reference).

Anchors:
  - mac/architecture.md §10.4 Compression Integration
  - compression/architecture.md §3.2 F8 reasoning preservation
  - mac/architecture.md §5.6 Forge Fallback Handling (behavioral)
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.integrations.compression import (
    MacCompressionAdapter,
    MacCompressionResult,
)


class _FakeForgeCompressor:
    """Protocol-compatible fake for CompressorProtocol.

    Returns an MacCompressionResult with controllable flags. Used by
    both F8-01 (reasoning_preserved=True path) and F8-02 (absorption
    boundary check).
    """

    def __init__(self, reasoning_preserved: bool) -> None:
        self._reasoning_preserved = reasoning_preserved

    async def compact_with_reasoning_preservation(
        self, payload: bytes
    ) -> MacCompressionResult:
        return MacCompressionResult(
            compressed_payload=payload,
            reasoning_preserved=self._reasoning_preserved,
        )


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
@pytest.mark.f1_absorption
async def test_mac_t_int_forge_f8_01_reasoning_preserved_flag_propagates() -> None:
    """MAC-T-INT-FORGE-F8-01 — ``reasoning_preserved`` flag propagates.

    ``MacCompressionAdapter.compress(payload)`` returns an
    :class:`MacCompressionResult` whose ``reasoning_preserved`` matches
    the upstream Compressor's flag. Both True and False paths.
    """
    # reasoning_preserved=True
    adapter_good = MacCompressionAdapter(compressor=_FakeForgeCompressor(True))
    result_good = await adapter_good.compress(b"some payload")
    assert result_good.reasoning_preserved is True

    # reasoning_preserved=False
    adapter_bad = MacCompressionAdapter(compressor=_FakeForgeCompressor(False))
    result_bad = await adapter_bad.compress(b"some payload")
    assert result_bad.reasoning_preserved is False


@pytest.mark.asyncio
@pytest.mark.critical
@pytest.mark.integration
@pytest.mark.f1_absorption
async def test_mac_t_int_forge_f8_02_f8_absorption_boundary() -> None:
    """MAC-T-INT-FORGE-F8-02 — F8 absorption boundary.

    The adapter re-wraps the compressor's output into a
    :class:`MacCompressionResult`. The payload round-trips (no
    transformation at the adapter boundary — MAC consumes the flag, not
    the compressed bytes). Absorption means: whatever the upstream
    compressor produces, MAC surfaces at the adapter seam without
    re-interpreting the bytes.
    """
    original_bytes = b"conversation history to be compacted"
    adapter = MacCompressionAdapter(compressor=_FakeForgeCompressor(True))
    result = await adapter.compress(original_bytes)

    assert result.compressed_payload == original_bytes
    assert result.reasoning_preserved is True
    assert result.reasoning_drift_detected is False
