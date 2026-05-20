"""Compression integration — arch §10.4 (Forge F8 only).

The MAC consumes the Compression layer ONLY via the Forge F8
``reasoning_preserved`` flag per arch §10.4 + compression/architecture.md
§3.2. F-2 TONL bead encoding is deferred to Stage 6 and MUST NOT be
imported or referenced — any future MAC code that imports TONL is a
build-time error (arch §10.4 + test-strategy.md v0.3 §11.3 reference).

Binding anchors:
  - mac/architecture.md §10.4 Compression Integration
  - compression/architecture.md §3.2 F8 reasoning preservation
  - mac/architecture.md §5.6 Forge Fallback Handling (behavioral)
  - mac/architecture.md §6.3 SQ-7 ordering (penalty last on R7_effective)
  - mac/test-strategy.md v0.3 §6.4 MAC-T-INT-FORGE-F8-01..02
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class MacCompressionResult:
    """MAC-side view of a compressor output, carrying the two flags from
    compression/architecture.md §3.2:

      - ``reasoning_preserved``: ``False`` triggers the arch §5.6 +
        §6.3 SQ-7 step-3 R7-penalty-last behavioral path.
      - ``reasoning_drift_detected``: ``True`` on schema drift
        (separate from the F8 fallback flag; reserved for step 3
        telemetry but not yet consumed by the cycle controller).
    """

    compressed_payload: bytes
    reasoning_preserved: bool
    reasoning_drift_detected: bool = False


@runtime_checkable
class CompressorProtocol(Protocol):
    """Shape of ``praxis.kernel.compression.forge.compactor.ForgeCompactor``
    (or any alternative compressor) that MAC consumes. MAC only uses
    :meth:`compact_with_reasoning_preservation`.
    """

    async def compact_with_reasoning_preservation(
        self, payload: bytes
    ) -> MacCompressionResult: ...


class MacCompressionAdapter:
    """MAC's interface to Compression. Consumes Forge F8 only.

    The cycle controller calls :meth:`compress` at the compaction boundary
    and inspects ``reasoning_preserved`` on the result. When the flag is
    ``False``, the controller sets ``state.forge_degraded=True`` and the
    Quality Gate Engine applies the R7 penalty per arch §6.3 SQ-7
    step 3 (AFTER Req-C caps, using raw R7 as the cap input).
    """

    def __init__(self, compressor: CompressorProtocol) -> None:
        self._compressor = compressor

    async def compress(self, payload: bytes) -> MacCompressionResult:
        return await self._compressor.compact_with_reasoning_preservation(payload)


__all__ = (
    "CompressorProtocol",
    "MacCompressionAdapter",
    "MacCompressionResult",
)
