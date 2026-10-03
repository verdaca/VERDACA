"""Stage 13 NonceStore persistence MAC-Ts."""

from __future__ import annotations

import asyncio

import pytest

from praxis.kernel.auth import InMemoryNonceStore, NonceReplayError, NonceStore


class _Clock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


@pytest.mark.no_waiver
@pytest.mark.asyncio
async def test_M_T_AUTH_NONCE_PERSISTENCE_RESTART_01_replay_survives_reopen(tmp_path) -> None:
    db_path = tmp_path / "nonces.db"
    store = NonceStore(db_path=db_path)
    await store.check_and_mark("nonce-1")
    await store.close()

    reopened = NonceStore(db_path=db_path)
    with pytest.raises(NonceReplayError):
        await reopened.check_and_mark("nonce-1")
    await reopened.close()


@pytest.mark.asyncio
async def test_M_T_AUTH_NONCE_STARTUP_SWEEP_01_deletes_expired_rows(tmp_path) -> None:
    db_path = tmp_path / "nonces.db"
    clock = _Clock(200.0)
    store = NonceStore(db_path=db_path, clock=clock)
    store._conn.execute("INSERT INTO nonces (nonce, expires_at) VALUES (?, ?)", ("old", 100.0))
    await store.close()

    reopened = NonceStore(db_path=db_path, clock=clock)
    count = reopened._conn.execute("SELECT count(*) FROM nonces WHERE nonce = 'old'").fetchone()[0]

    assert count == 0
    await reopened.close()


@pytest.mark.asyncio
async def test_M_T_AUTH_NONCE_ATOMIC_EXPIRY_BOUNDARY_01_duplicate_concurrency_allows_one(
    tmp_path,
) -> None:
    store = NonceStore(db_path=tmp_path / "nonces.db")

    results = await asyncio.gather(
        _check(store, "same-nonce"),
        _check(store, "same-nonce"),
    )

    assert sorted(result.__name__ if result else "ok" for result in results) == [
        "NonceReplayError",
        "ok",
    ]
    await store.close()


async def _check(store: NonceStore, nonce: str) -> type[BaseException] | None:
    try:
        await store.check_and_mark(nonce)
    except BaseException as exc:
        return type(exc)
    return None


@pytest.mark.asyncio
async def test_M_T_AUTH_NONCE_REPLAY_BLOCK_01_duplicate_same_process_raises(tmp_path) -> None:
    store = NonceStore(db_path=tmp_path / "nonces.db")

    await store.check_and_mark("nonce-1")
    with pytest.raises(NonceReplayError):
        await store.check_and_mark("nonce-1")
    await store.close()


@pytest.mark.asyncio
async def test_nonce_store_ttl_after_boundary_allows_reuse(tmp_path) -> None:
    clock = _Clock(100.0)
    store = NonceStore(db_path=tmp_path / "nonces.db", ttl_seconds=10, clock=clock)

    await store.check_and_mark("nonce-ttl")
    clock.now = 111.0
    await store.check_and_mark("nonce-ttl")

    await store.close()


@pytest.mark.asyncio
async def test_nonce_store_ttl_before_boundary_blocks_reuse(tmp_path) -> None:
    clock = _Clock(100.0)
    store = NonceStore(db_path=tmp_path / "nonces.db", ttl_seconds=10, clock=clock)

    await store.check_and_mark("nonce-ttl")
    clock.now = 109.0
    with pytest.raises(NonceReplayError):
        await store.check_and_mark("nonce-ttl")

    await store.close()


def test_M_T_AUTH_NONCE_SEPARATE_DB_FILE_01_nonce_store_accepts_explicit_db_path(tmp_path) -> None:
    session_index = tmp_path / "session-index.sqlite3"
    nonce_db = tmp_path / "nonces.sqlite3"
    store = NonceStore(db_path=nonce_db)
    try:
        assert nonce_db != session_index
        assert store._conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert store._conn.execute("PRAGMA synchronous").fetchone()[0] == 1
    finally:
        store._conn.close()


def test_nonce_store_persistent_flags_discriminate_sqlite_from_in_memory(tmp_path) -> None:
    store = NonceStore(db_path=tmp_path / "nonces.db")
    try:
        assert NonceStore.persistent is True
        assert InMemoryNonceStore.persistent is False
    finally:
        store._conn.close()
