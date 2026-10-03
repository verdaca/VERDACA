"""Stage 14 Phase-1 [H#2] — policy-smoke.py onboarding test.

Plain test (NO ``@pytest.mark.no_waiver`` → pin 14/9/23 unaffected). Verifies
policy-smoke passes on a healthy policy and fail-closes when
``VERDACA_DEPLOY_PROFILE=production`` is set with no virtual_keys configured
(the Stage 14 B2 contract).
"""

from __future__ import annotations

from types import ModuleType
from typing import Any, Callable

import pytest

from praxis.ports.virtual_key import VirtualKeyInfo, VirtualKeySpec

LoadScript = Callable[[str, str], ModuleType]


class _FakeVKeys:
    """Presence-only VirtualKeyPort stand-in (health check inspects None-ness)."""

    async def create_virtual_key(self, spec: VirtualKeySpec) -> VirtualKeyInfo:  # pragma: no cover
        raise NotImplementedError

    async def get_key_info(self, key_alias: str) -> VirtualKeyInfo:  # pragma: no cover
        raise NotImplementedError

    async def check_budget(self, key_alias: str) -> None:  # pragma: no cover
        raise NotImplementedError

    async def get_spend_logs(self, key_alias: str) -> list[dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError


@pytest.fixture()
def policy_smoke(load_onboarding_script: LoadScript) -> ModuleType:
    return load_onboarding_script("policy-smoke.py", "onboarding_policy_smoke")


def test_passes_when_vkeys_present_even_at_production(
    policy_smoke: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    policy = policy_smoke.build_policy(
        allowed_user_ids=["user-1"], virtual_keys=_FakeVKeys()
    )
    healthy, message = policy_smoke.run_smoke(policy)
    assert healthy, message


def test_fail_closed_under_production_without_vkeys(
    policy_smoke: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    policy = policy_smoke.build_policy(allowed_user_ids=["user-1"], virtual_keys=None)
    healthy, message = policy_smoke.run_smoke(policy)
    assert not healthy
    assert "fail-closed" in message


def test_warns_but_passes_when_not_production(
    policy_smoke: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "demo")
    policy = policy_smoke.build_policy(allowed_user_ids=["user-1"], virtual_keys=None)
    healthy, message = policy_smoke.run_smoke(policy)
    assert healthy, message
