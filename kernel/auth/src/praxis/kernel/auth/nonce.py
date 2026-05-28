"""SQLite nonce replay protection."""

from __future__ import annotations

import asyncio
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar


class NonceReplayError(ValueError):
    """Raised when a previously seen nonce is presented again."""


class NonceStore:
    """SQLite-backed nonce replay protection with lazy TTL eviction."""

    persistent: ClassVar[bool] = True

    def __init__(
        self,
        *,
        db_path: str | Path,
        ttl_seconds: int = 600,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._db_path = Path(db_path)
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._lock = asyncio.Lock()
        self._conn = sqlite3.connect(self._db_path, timeout=5.0, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nonces (
                nonce TEXT PRIMARY KEY NOT NULL,
                expires_at REAL NOT NULL
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_nonces_expires_at ON nonces (expires_at)"
        )
        self._conn.execute("DELETE FROM nonces WHERE expires_at <= ?", (self._clock(),))

    async def check_and_mark(self, nonce: str) -> None:
        async with self._lock:
            now = self._clock()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute("DELETE FROM nonces WHERE expires_at <= ?", (now,))
                self._conn.execute(
                    "INSERT INTO nonces (nonce, expires_at) VALUES (?, ?)",
                    (nonce, now + self._ttl_seconds),
                )
            except sqlite3.IntegrityError as exc:
                self._conn.execute("ROLLBACK")
                raise NonceReplayError(
                    "Token replay detected: nonce has already been used"
                ) from exc
            except sqlite3.Error:
                self._conn.execute("ROLLBACK")
                raise
            else:
                self._conn.execute("COMMIT")

    async def close(self) -> None:
        self._conn.close()


class InMemoryNonceStore:
    """In-memory nonce replay protection for tests and fakes."""

    persistent: ClassVar[bool] = False

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._lock = asyncio.Lock()

    async def check_and_mark(self, nonce: str) -> None:
        async with self._lock:
            if nonce in self._seen:
                raise NonceReplayError("Token replay detected: nonce has already been used")
            self._seen.add(nonce)

    async def close(self) -> None:
        return None


__all__ = ["InMemoryNonceStore", "NonceReplayError", "NonceStore"]
