"""Phase-B conftest — honesty fixtures for the ports contract-test suite.

Provides ``require_production_profile``: any test whose name carries a live
marker (``_live_`` / ``_smoke_`` / ``_real_backend_``) consumes this fixture so
it cannot silently pass against the Tier-1 stubs.

What this fixture DOES: it issues a ``pytest.skip`` when
``VERDACA_DEPLOY_PROFILE != production`` — an env-gate. Live tests SKIP in
dev/CI (correct: a skip, not a hard error, is the right outcome when the
production profile/creds are absent) and only execute in a staging env where
the profile is explicitly set.

What this fixture does NOT do (and does not claim to): it does not inspect a
composed gateway or assert any adapter is non-stub — it cannot see a gateway
generically. The "this test really exercised a real adapter, not a
``_DemoStub*``" guarantee is delivered by the POSITIVE STUB ASSERTIONS inside
the individual tests (honesty control #5 — e.g. the ``isinstance(...,
_DemoStubVirtualKeys)`` / ``type(...).__name__ != "_DemoStub*"`` checks in the
hermetic and live tests), NOT here.

Naming convention (ENFORCED by the name-scan meta-test in
``test_stage14_live_smoke.py``):
  - ``*_live_*`` / ``*_smoke_*`` / ``*_real_backend_*`` → the test MUST consume
    this fixture, OR carry a ``@pytest.mark.skip``/``skipif`` marker, OR be in
    the documented runtime-skip exemption set. A new live test added with none
    of these fails the name-scan (closes the rogue-unregistered-live-test gap).
  - ``*_COMPOSES_*`` / ``*_FAILS_CLOSED_*`` / ``*_MECHANISM_*`` → hermetic by
    convention; run at any profile.
  - ``*_against_local_stub_*`` → hermetic (local OIDC stub); profile unset is fine.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture()
def require_production_profile() -> None:
    """Env-gate for live/smoke tests: ``pytest.skip`` unless
    ``VERDACA_DEPLOY_PROFILE=production``. So a live test SKIPS in dev/CI and
    can never silently pass against the Tier-1 stubs. (It does NOT itself assert
    adapter-is-not-stub — that is the per-test positive-stub assertion's job.)"""
    profile = os.environ.get("VERDACA_DEPLOY_PROFILE", "").lower()
    if profile != "production":
        pytest.skip(
            "O-LIVE-SMOKE: TRANSIENT-CREDS — VERDACA_DEPLOY_PROFILE=production "
            "required for live/smoke tests — "
            "flip:set VERDACA_DEPLOY_PROFILE=production in the staging env"
        )
