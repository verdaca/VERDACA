"""Stage 14 Phase-0.6 O-6 — committed O-11 concurrency proof.

Ports the O-11 concurrency reasoning to a re-runnable, committed test (replacing
the earlier exit-code-42 side-channel proof, which is NOT the system of record).

Two invariants:

  (a) THE HAZARD — a CONTENDED ``asyncio.Lock`` acquire from a SECOND event loop
      raises ``RuntimeError: ... bound to a different event loop``. This is the
      exact failure mode the gateway's FROZEN loop-bound locks
      (``InMemoryNonceStore._lock``, ``JwksCache._lock``) hit when each request
      runs ``service._run_auth_first -> asyncio.run(...)`` on a FRESH loop and
      two such loops contend on the same persistent lock.

  (b) THE MITIGATION — ``TeamsWebhookApp.handle`` serializes the offloaded
      gateway execution with a server-loop ``anyio.Lock`` (``_exec_lock``) so at
      most ONE offload is in flight at a time (throughput = 1, asserted). With
      the offloads serialized, the frozen locks are only ever acquired
      uncontended (the proven-OK path), so the hazard in (a) never fires.

Plain contract tests (NO ``@pytest.mark.no_waiver`` → the 14/9/23 pin is
unaffected). FROZEN: drives existing components only; no kernel edit, no
marker/pin change. ``_exec_lock`` throughput = 1 is an asserted INVARIANT here,
not an assumption.
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable, Mapping
from typing import Any

import anyio
import httpx
import pytest

import praxis.adapters.channels.webhook_app.app as app_module
from praxis.adapters.channels.teams.webhook import WebhookResponse
from praxis.adapters.channels.webhook_app import TeamsWebhookApp, create_teams_app

# ─── (a) the hazard: contended cross-loop asyncio.Lock acquire raises ──────


def test_o11_contended_cross_loop_asyncio_lock_acquire_raises() -> None:
    """An ``asyncio.Lock`` bound to loop A raises when acquired (contended)
    from loop B — the proven O-11 failure the serialization avoids."""
    lock = asyncio.Lock()

    async def _bind_to_this_loop_via_contention() -> None:
        # First acquire: uncontended fast path (no loop binding yet).
        await lock.acquire()
        # Second acquire on a child task: CONTENDED, so Lock._get_loop() binds
        # the lock to THIS loop. Cancel the waiter so the loop can finish; the
        # loop binding persists on the (still-locked) lock object.
        waiter = asyncio.ensure_future(lock.acquire())
        await asyncio.sleep(0)  # let the waiter register + call _get_loop()
        waiter.cancel()
        try:
            await waiter
        except asyncio.CancelledError:
            pass

    loop_a = asyncio.new_event_loop()
    try:
        loop_a.run_until_complete(_bind_to_this_loop_via_contention())
    finally:
        loop_a.close()

    # The lock is still held AND bound to (now-closed) loop A. A contended
    # acquire from a DIFFERENT loop must raise.
    async def _acquire_from_other_loop() -> None:
        await lock.acquire()

    loop_b = asyncio.new_event_loop()
    try:
        with pytest.raises(RuntimeError, match="different event loop"):
            loop_b.run_until_complete(_acquire_from_other_loop())
    finally:
        loop_b.close()


# ─── (b) the mitigation: _exec_lock admits exactly one in-flight execution ──


class _FakeGateway:
    """Minimal gateway stand-in — handle() only reads ``.jwt_verifier``."""

    jwt_verifier = object()


@pytest.mark.asyncio
async def test_o11_exec_lock_serializes_to_one_in_flight_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two concurrent webhook requests → at most ONE offloaded execution runs
    at a time (throughput = 1), because handle() wraps the offload in
    ``_exec_lock``. This is the asserted invariant, not an assumption."""
    in_flight = 0
    max_in_flight = 0
    counter_lock = threading.Lock()

    def _instrumented_receive_webhook(
        body: bytes,
        headers: Mapping[str, str],
        *,
        secret: str,
        verifier: Any,
        dispatch: Callable[..., WebhookResponse],
        now: float | None = None,
    ) -> WebhookResponse:
        # Runs on an anyio worker thread (offloaded by handle()). Records peak
        # observed concurrency; sleeps to widen the overlap window if the
        # serialization were ever broken.
        nonlocal in_flight, max_in_flight
        with counter_lock:
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
        try:
            time.sleep(0.05)
        finally:
            with counter_lock:
                in_flight -= 1
        return WebhookResponse(status_code=200, payload={"ok": True})

    monkeypatch.setattr(app_module, "receive_webhook", _instrumented_receive_webhook)

    app_obj = TeamsWebhookApp()
    app_obj._gateway = _FakeGateway()  # type: ignore[assignment]
    app_obj._secret = "phase06-o11-secret"
    app_obj._exec_lock = anyio.Lock()  # binds to this (the test's) running loop
    app = create_teams_app(app_obj)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        body = b'{"type": "message"}'
        responses = await asyncio.gather(
            client.post("/webhooks/teams", content=body),
            client.post("/webhooks/teams", content=body),
            client.post("/webhooks/teams", content=body),
        )

    assert [r.status_code for r in responses] == [200, 200, 200]
    assert max_in_flight == 1, f"expected throughput=1, saw {max_in_flight} overlapping"
