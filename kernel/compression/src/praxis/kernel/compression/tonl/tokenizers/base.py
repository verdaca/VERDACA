"""Tokenizer Protocol — the interface every tokenizer adapter must satisfy."""
from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable


@runtime_checkable
class Tokenizer(Protocol):
    """Tokenizer adapter protocol (architecture §3.1.3)."""

    name: ClassVar[str]
    version: ClassVar[str]

    def count(self, text: str) -> int:
        """Return approximate token count for *text*."""
        ...

    def encode_bytes(self, text: str) -> bytes:
        """Return token byte sequence for *text*."""
        ...

    def byte_boundary_positions(self, text: str) -> list[int]:
        """Return byte positions of token boundaries in *text*.

        Enables TONL's tokenizer-aware character layout (architecture §3.1.3).
        """
        ...
