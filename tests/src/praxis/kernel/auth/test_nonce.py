"""Stage 12 H#3.5 MAC-Ts for nonce replay protection."""

from __future__ import annotations

import asyncio

import pytest

from praxis.kernel.auth.nonce import NonceReplayError, NonceStore


async def _check(store: NonceStore, nonce: str) -> type[BaseException] | None:
    try:
        await store.check_and_mark(nonce)
    except BaseException as exc:
        return type(exc)
    return None


@pytest.mark.no_waiver
@pytest.mark.asyncio
async def test_M_T_AUTH_NONCE_REPLAY_BLOCK_01_blocks_replay_and_concurrent_duplicates() -> None:
    sequential = NonceStore()

    await sequential.check_and_mark("nonce-001")
    with pytest.raises(NonceReplayError):
        await sequential.check_and_mark("nonce-001")

    concurrent = NonceStore()
    results = await asyncio.gather(
        _check(concurrent, "nonce-002"),
        _check(concurrent, "nonce-002"),
    )

    assert sorted(result.__name__ if result else "ok" for result in results) == [
        "NonceReplayError",
        "ok",
    ]
