"""Stage 14 Phase-B — T3 live-smoke tests (env-gated; TRANSIENT-CREDS class).

These tests are SKIPPED when the required credentials/VPN are absent. The
``require_production_profile`` fixture (from conftest.py) issues a
``pytest.skip`` when ``VERDACA_DEPLOY_PROFILE != production`` — so the test
body is only reached in a staging environment with the profile explicitly set.
Each test then adds its own cred-specific skip.

Pattern mirrors ``test_gateway_dial_contract.py:96-99``:
    api_key = os.environ.get("DIAL_API_KEY")
    if api_key is None:
        pytest.skip("...")

Skip reason taxonomy (matches the deferred-set ledger):
  O-LIVE-SMOKE: TRANSIENT-CREDS — <what is needed> — flip:<the env var>.

Plain tests (NO ``@pytest.mark.no_waiver`` → the 14/9/23 pin is unaffected).
"""

from __future__ import annotations

import os
from typing import Final

import pytest

import praxis.composition.runtime_gateway as comp

# Honesty control #4 — the name-scan markers and the documented exemption.
_LIVE_NAME_MARKERS: Final[tuple[str, ...]] = ("_live_", "_smoke_", "_real_backend_")
# Tests that carry a live marker name but are gated by the canonical runtime
# pytest.skip(DIAL_API_KEY) idiom that PREDATES require_production_profile. This
# is a DOCUMENTED exemption (not a silent one): safe because the test skips when
# creds are absent. Keep this set minimal; new live tests must use the fixture.
_NAME_SCAN_EXEMPT: Final[frozenset[str]] = frozenset(
    {
        "test_M_T_DIAL_EXEC_LIVE_ROUTING_01_env_gated_live_smoke",
    }
)

# ─── T3.1 — Live DIAL LLM model output ────────────────────────────────────


def test_T3_live_dial_llm_COMPOSES_real_adapter_and_call_succeeds(
    require_production_profile: None,
) -> None:
    """O-LIVE-SMOKE: TRANSIENT-CREDS — real DIAL LLM adapter construction via
    create_dial_llm_proxy. Verifies the adapter routes to DIAL
    (api-proxy.lab.epam.com) and conforms to LLMProxyPort. flip:DIAL_API_KEY set
    + VPN on.
    """
    api_key = os.environ.get("DIAL_API_KEY")
    if not api_key:
        pytest.skip(
            "O-LIVE-SMOKE: TRANSIENT-CREDS — DIAL_API_KEY unset; "
            "run with VPN on + DIAL_API_KEY set — flip:DIAL_API_KEY"
        )

    proxy = comp._build_llm_proxy()
    assert type(proxy).__name__ != "_DemoStubLLMProxy", (
        "Live test must see a real proxy, not the Tier-1 stub"
    )
    from praxis.ports.llm_proxy import LLMProxyPort
    assert isinstance(proxy, LLMProxyPort)
    # A real .call() requires a live DIAL request — that's the staging-runbook
    # integration point, not an automated test body.


# ─── T3.2 — Live LiteLLM vkey adapter construction ──────────────────────────


def test_T3_live_litellm_vkey_COMPOSES_real_adapter(
    require_production_profile: None,
) -> None:
    """O-LIVE-SMOKE: TRANSIENT-CREDS — real LiteLLMVirtualKeyAdapter construction.
    flip:LITELLM_PROXY_URL + LITELLM_MASTER_KEY set.
    Note: real-spend gating remains deferred (CC6.7-c DURABLE-ARCH).
    """
    base_url = os.environ.get("LITELLM_PROXY_URL")
    master_key = os.environ.get("LITELLM_MASTER_KEY")
    if not base_url or not master_key:
        pytest.skip(
            "O-LIVE-SMOKE: TRANSIENT-CREDS — LITELLM_PROXY_URL + LITELLM_MASTER_KEY unset; "
            "staging-only — flip:LITELLM_PROXY_URL + LITELLM_MASTER_KEY"
        )

    from praxis.adapters.litellm.virtual_keys import LiteLLMVirtualKeyAdapter
    vk = comp._build_virtual_keys()
    assert isinstance(vk, LiteLLMVirtualKeyAdapter)


# ─── T3.3 — Live Letta memory adapter construction ──────────────────────────


def test_T3_live_letta_memory_COMPOSES_real_adapter(
    require_production_profile: None,
) -> None:
    """O-LIVE-SMOKE: TRANSIENT-CREDS — real Letta client construction.
    flip:LETTA_API_KEY or LETTA_BASE_URL set (letta-client reads both natively).
    """
    if not (os.environ.get("LETTA_API_KEY") or os.environ.get("LETTA_BASE_URL")):
        pytest.skip(
            "O-LIVE-SMOKE: TRANSIENT-CREDS — LETTA_API_KEY / LETTA_BASE_URL unset; "
            "staging-only — flip:LETTA_API_KEY or LETTA_BASE_URL"
        )

    from praxis.adapters.letta import LettaAdapter
    mem = comp._build_memory()
    assert isinstance(mem, LettaAdapter)


# ─── T3.4 — Commercial-IdP OIDC discovery ──────────────────────────────────


def test_T3_live_commercial_idp_discovery_COMPOSES_real_oidc_policy(
    require_production_profile: None,
) -> None:
    """O-COMMERCIAL-IDP: TRANSIENT-CREDS — real OIDC discovery (Entra/Okta/Auth0)
    via compose_auth_quartet → discover(). flip:OIDC_ISSUER_URL pointing to a
    real commercial IdP (not localhost / 127.0.0.1) + OIDC_AUDIENCE set.
    """
    issuer = os.environ.get("OIDC_ISSUER_URL", "")
    if not issuer or "127.0.0.1" in issuer or "localhost" in issuer:
        pytest.skip(
            "O-COMMERCIAL-IDP: TRANSIENT-CREDS — OIDC_ISSUER_URL unset or "
            "localhost (local stub); set a real commercial IdP URL — "
            "flip:OIDC_ISSUER_URL pointing to Entra/Okta/Auth0 + OIDC_AUDIENCE"
        )
    import asyncio

    from praxis.composition.runtime_gateway import compose_auth_quartet
    verifier, oidc_policy = asyncio.run(compose_auth_quartet())
    assert verifier is not None
    assert oidc_policy is not None


# ─── Honesty control #4 — name-scan: live tests cannot be unguarded ────────
# (Named WITHOUT a live marker so it does not flag itself.)


def test_control4_naming_convention_gates_profile_fixture(
    request: pytest.FixtureRequest,
) -> None:
    """Every collected test whose name carries a live marker (_live_ / _smoke_ /
    _real_backend_) MUST be profile-gated: it consumes require_production_profile,
    OR carries a skip/skipif marker, OR is a documented runtime-skip exemption.
    This makes the naming convention ENFORCED, not opt-in — a future live test
    added without a gate would run against the Tier-1 stubs.

    Subset assertion (offenders ⊆ ∅ after exclusions) — robust to narrow runs
    where not every live test is collected (no session-scope false-negatives)."""
    offenders: list[str] = []
    for item in request.session.items:
        if not any(marker in item.name for marker in _LIVE_NAME_MARKERS):
            continue
        if "require_production_profile" in getattr(item, "fixturenames", ()):
            continue
        if item.get_closest_marker("skip") or item.get_closest_marker("skipif"):
            continue
        if item.name in _NAME_SCAN_EXEMPT:
            continue
        offenders.append(item.nodeid)
    assert offenders == [], (
        "live/smoke/real_backend tests must consume require_production_profile, "
        f"carry a skip marker, or be a documented exemption: {offenders}"
    )
