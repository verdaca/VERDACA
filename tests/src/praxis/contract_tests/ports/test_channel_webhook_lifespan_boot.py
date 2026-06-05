"""Stage 14 Phase-0.6 O-6 — Teams webhook lifespan/boot path test.

Folds MEDIUM ``F-14-V1-...-03``: the production boot path in
``create_teams_app`` (the Starlette lifespan that composes the gateway on
startup) previously carried ``# pragma: no cover - exercised in prod``. That
pragma is removed; this test exercises BOTH branches of the lifespan body
under a running loop, so the boot path is covered without a real OIDC fetch.

Plain contract tests (NO ``@pytest.mark.no_waiver`` → the 14/9/23 pin is
unaffected). Uses a duck-typed fake app (fake gateway + secret) so the lifespan
drives ``startup()`` deterministically without network — the point under test
is the lifespan WIRING (does it boot when not ready / no-op when ready), not
the OIDC construction, which the wiring-integration test already covers.

FROZEN: constructs/drives existing components only; no kernel/service.py /
nonce.py edit, no marker/pin change.
"""

from __future__ import annotations

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from praxis.adapters.channels.webhook_app import create_teams_app


class _FakeBootApp:
    """Duck-typed stand-in for TeamsWebhookApp (fake gateway + secret).

    Records ``startup()`` invocations and flips ``is_ready`` on boot so both
    lifespan branches are observable. ``handle`` is a stub — the lifespan tests
    never route a request through it.
    """

    def __init__(self, *, ready_at_start: bool) -> None:
        self._ready = ready_at_start
        self.startup_calls = 0

    @property
    def is_ready(self) -> bool:
        return self._ready

    async def startup(self) -> None:
        self.startup_calls += 1
        self._ready = True  # fake gateway + secret now "composed"

    async def handle(self, request: Request) -> Response:  # pragma: no cover - stub
        return JSONResponse({"status": "ignored"}, status_code=200)


@pytest.mark.asyncio
async def test_lifespan_boots_gateway_when_not_ready() -> None:
    """Not-ready → the production boot branch runs startup() exactly once."""
    obj = _FakeBootApp(ready_at_start=False)
    app = create_teams_app(obj)
    async with app.router.lifespan_context(app):
        assert obj.startup_calls == 1
        assert obj.is_ready
    # startup is not re-run on shutdown
    assert obj.startup_calls == 1


@pytest.mark.asyncio
async def test_lifespan_noops_when_already_ready() -> None:
    """Pre-booted (e.g. tests inject a ready object) → lifespan no-ops."""
    obj = _FakeBootApp(ready_at_start=True)
    app = create_teams_app(obj)
    async with app.router.lifespan_context(app):
        assert obj.startup_calls == 0
    assert obj.startup_calls == 0
