"""Stage 12 H#3.5 MAC-Ts for nonce replay protection."""

from __future__ import annotations

import asyncio

import pytest

from praxis.kernel.auth.nonce import InMemoryNonceStore, NonceReplayError, NonceStore


async def _check(store: NonceStore, nonce: str) -> type[BaseException] | None:
    try:
        await store.check_and_mark(nonce)
    except BaseException as exc:
        return type(exc)
    return None


@pytest.mark.no_waiver
@pytest.mark.asyncio
async def test_M_T_AUTH_NONCE_REPLAY_BLOCK_01_blocks_replay_and_concurrent_duplicates(
    tmp_path,
) -> None:
    sequential = NonceStore(db_path=tmp_path / "sequential-nonces.db")

    await sequential.check_and_mark("nonce-001")
    with pytest.raises(NonceReplayError):
        await sequential.check_and_mark("nonce-001")
    await sequential.close()

    concurrent = NonceStore(db_path=tmp_path / "concurrent-nonces.db")
    results = await asyncio.gather(
        _check(concurrent, "nonce-002"),
        _check(concurrent, "nonce-002"),
    )

    assert sorted(result.__name__ if result else "ok" for result in results) == [
        "NonceReplayError",
        "ok",
    ]
    await concurrent.close()


@pytest.mark.asyncio
async def test_in_memory_nonce_store_marks_non_persistent() -> None:
    store = InMemoryNonceStore()

    await store.check_and_mark("nonce-memory")

    assert InMemoryNonceStore.persistent is False
