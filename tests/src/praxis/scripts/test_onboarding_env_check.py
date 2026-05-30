"""Stage 14 Phase-1 [H#2] — env-check.py onboarding test.

Plain test (NO ``@pytest.mark.no_waiver`` → the 14/9/23 pin is unaffected).
Verifies env-check validates the required Teams-path variables, returns a
helpful non-zero on a missing one, and treats SLACK_SIGNING_SECRET as optional
(Teams-only today; Slack is a named fast-follow).
"""

from __future__ import annotations

from types import ModuleType
from typing import Callable

import pytest

LoadScript = Callable[[str, str], ModuleType]

_COMPLETE_ENV = {
    "OIDC_ISSUER_URL": "http://127.0.0.1:9/idp",
    "OIDC_AUDIENCE": "api://verdaca",
    "VERDACA_ALLOWED_USER_IDS": "user-1",
    "TEAMS_WEBHOOK_SECRET": "teams-secret",
    "LITELLM_PROXY_URL": "http://127.0.0.1:9/litellm",
    "LITELLM_MASTER_KEY": "sk-master",
    "VERDACA_DEPLOY_PROFILE": "demo",
}


@pytest.fixture()
def env_check(load_onboarding_script: LoadScript) -> ModuleType:
    return load_onboarding_script("env-check.py", "onboarding_env_check")


def test_complete_env_passes(env_check: ModuleType) -> None:
    assert env_check.missing_required(_COMPLETE_ENV) == []
    assert env_check.main(_COMPLETE_ENV) == 0


def test_missing_required_var_fails_with_name(env_check: ModuleType) -> None:
    env = dict(_COMPLETE_ENV)
    del env["TEAMS_WEBHOOK_SECRET"]
    assert env_check.missing_required(env) == ["TEAMS_WEBHOOK_SECRET"]
    assert env_check.main(env) == 1


def test_empty_value_counts_as_missing(env_check: ModuleType) -> None:
    env = dict(_COMPLETE_ENV, OIDC_AUDIENCE="")
    assert "OIDC_AUDIENCE" in env_check.missing_required(env)


def test_slack_secret_is_optional_until_wired(env_check: ModuleType) -> None:
    # SLACK_SIGNING_SECRET absent from the complete env, yet the path passes.
    assert "SLACK_SIGNING_SECRET" not in _COMPLETE_ENV
    assert "SLACK_SIGNING_SECRET" in env_check.missing_optional(_COMPLETE_ENV)
    assert env_check.main(_COMPLETE_ENV) == 0
