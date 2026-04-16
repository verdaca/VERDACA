"""FakeCompressor fake — test-strategy v0.3 §14.3.4 frozen interface contract.

Transcribed verbatim from the ratified test-strategy interface contract.
Docstring references arch §5.6 behavioral Forge fallback, NOT a
fabricated ``State.FORGE_FALLBACK`` (v0.1 drift retired at v0.3 §4.1).

Binding anchors:
  - mac/test-strategy.md v0.3 §14.3.4 FakeCompressor (frozen interface)
  - mac/architecture.md §5.6 Forge Fallback Handling (behavioral, not state)
  - mac/architecture.md §6.3 SQ-7 ordering (penalty applied last on R7_effective)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompressionResult:
    """Compressor output carrying the Forge F8 ``reasoning_preserved`` flag
    (arch §10.4 / compression/architecture.md §3.2)."""

    compressed: bytes
    reasoning_preserved: bool


class FakeCompressor:
    """Deterministic compressor — exercises the Forge-degradation behavioral
    path per arch §5.6 + §6.3 SQ-7 step 3.

    Given a fixture payload, ``force_degradation=True`` returns
    ``reasoning_preserved=False`` to drive the MAC Iteration Controller into
    the R7-penalty-last path (no fabricated state transition; cycle proceeds
    through arch §5.2 normal states with ``R7_effective`` reduced by 1 after
    Req-C caps).
    """

    def __init__(self, force_degradation: bool = False) -> None:
        self._force = force_degradation

    def compress(self, payload: bytes) -> CompressionResult:
        return CompressionResult(
            compressed=payload,  # no-op compression for tests
            reasoning_preserved=not self._force,
        )


__all__ = ("CompressionResult", "FakeCompressor")
