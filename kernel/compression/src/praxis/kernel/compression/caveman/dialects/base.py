"""Caveman dialect Protocol."""
from __future__ import annotations

from typing import Protocol


class Dialect(Protocol):
    """A compression dialect provides the system prompt for a given intensity."""

    name: str

    def system_prompt(self, intensity: str) -> str:
        """Return the system prompt to use for compression at *intensity*."""
        ...
