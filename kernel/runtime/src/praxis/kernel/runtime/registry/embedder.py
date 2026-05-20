"""Praxis Runtime registry — Embedder abstraction.

The Embedder Protocol abstracts over the embedding model used by the Registry.
The concrete implementation is injected at Runtime init; the test harness uses
DeterministicTestEmbedder which generates seeded pseudo-random vectors.

Architecture references:
  architecture.md §3.5 (Embedder Protocol, embedding model consistency)
  architecture.md §9.4 (R14 manifest embedding_model_id cross-check)
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol, runtime_checkable


@runtime_checkable
class Embedder(Protocol):
    """Abstract embedding function. Concrete implementation injected at Runtime init."""

    def embed(self, text: str) -> list[float]:
        """Return a fixed-dimensional embedding vector for the input text."""
        ...

    @property
    def model_id(self) -> str:
        """Stable model identifier, e.g. 'voyage-3' or 'text-embedding-3-small'."""
        ...

    @property
    def dimension(self) -> int:
        """Vector dimensionality; used for sanity checks."""
        ...


class DeterministicTestEmbedder:
    """Seeded pseudo-random embedder for deterministic test fixtures.

    Uses a hash of the text + seed to generate a consistent unit-norm vector.
    Same text → same vector, always. Different seeds → different spaces.

    NOT for production use. Semantic similarity is meaningless; only the
    determinism and interface contract matter in tests.
    """

    def __init__(
        self,
        seed: int = 42,
        dimension: int = 64,
        model_id: str = "test-embedder-v1",
    ) -> None:
        self._seed = seed
        self._dimension = dimension
        self._model_id = model_id

    def embed(self, text: str) -> list[float]:
        """Generate a deterministic unit-norm vector from text + seed."""
        # Hash text + seed to get a deterministic byte sequence
        h = hashlib.sha256(f"{self._seed}:{text}".encode()).digest()
        # Extend to the required dimension by cycling the hash
        raw: list[float] = []
        while len(raw) < self._dimension:
            for byte in h:
                raw.append(float(byte) - 128.0)
                if len(raw) >= self._dimension:
                    break
            # Use next hash block for longer dimensions
            h = hashlib.sha256(h).digest()
        raw = raw[: self._dimension]

        # Normalize to unit vector
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimension(self) -> int:
        return self._dimension


__all__ = ["Embedder", "DeterministicTestEmbedder"]
