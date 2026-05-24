"""Gateway-owned WAL constants and configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

WAL_PRAGMAS: tuple[str, ...] = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class GatewayWalConfig:
    """SQLite WAL configuration for gateway-owned idempotency state."""

    database_path: Path


__all__ = [
    "GatewayWalConfig",
    "WAL_PRAGMAS",
]
