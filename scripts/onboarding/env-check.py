#!/usr/bin/env python
"""Onboarding step 1 — verify required environment variables are present.

Exits non-zero naming the first batch of missing required variables. Slack's
signing secret is OPTIONAL until the Slack channel route is served by
``webhook_app`` (Teams-only today; Slack is a named fast-follow), so its
absence does NOT fail the 5-minute path — it is reported as a note.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

# Required for the Teams 5-minute path (compose + transport + vkey provisioning).
REQUIRED: dict[str, str] = {
    "OIDC_ISSUER_URL": "IdP issuer for OIDC discovery",
    "OIDC_AUDIENCE": "expected token audience",
    "VERDACA_ALLOWED_USER_IDS": "deny-by-default caller allow-list (comma/space separated)",
    "TEAMS_WEBHOOK_SECRET": "Teams inbound HMAC-SHA256 secret",
    "LITELLM_PROXY_URL": "LiteLLM proxy base URL",
    "LITELLM_MASTER_KEY": "LiteLLM master key (issues scoped virtual keys)",
    "VERDACA_DEPLOY_PROFILE": "deploy profile ('production' => fail-closed vkey check)",
}

# Not required for the Teams path today.
OPTIONAL: dict[str, str] = {
    "SLACK_SIGNING_SECRET": (
        "Slack signing secret — optional until the Slack route is wired "
        "(Teams-only today; Slack is a named fast-follow)"
    ),
    "VERDACA_GATEWAY_BEARER_TOKEN": "gateway bearer — warn-only if unset",
}


def missing_required(environ: Mapping[str, str]) -> list[str]:
    """Return required variable names that are absent or empty."""
    return [name for name in REQUIRED if not environ.get(name)]


def missing_optional(environ: Mapping[str, str]) -> list[str]:
    """Return optional variable names that are absent or empty."""
    return [name for name in OPTIONAL if not environ.get(name)]


def main(environ: Mapping[str, str] | None = None) -> int:
    env = os.environ if environ is None else environ
    for name in missing_optional(env):
        print(f"note: {name} unset — {OPTIONAL[name]}")
    missing = missing_required(env)
    if missing:
        print("ERROR: missing required environment variables:")
        for name in missing:
            print(f"  - {name}: {REQUIRED[name]}")
        return 1
    print("env-check: all required variables present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
