#!/usr/bin/env python
"""Onboarding step 3 — verify gateway policy posture before first traffic.

Builds a ``GatewayPolicy`` from the current env (allow-list + virtual-key
presence) and runs ``policy_health_check(policy=...)`` — the Stage 14 B2
contract. Exit 0 = healthy; exit 1 = fail-closed fired (read the diagnostic;
usually ``VERDACA_DEPLOY_PROFILE=production`` with no virtual_keys configured).
"""

from __future__ import annotations

import os

from praxis.adapters.litellm.virtual_keys import LiteLLMVirtualKeyAdapter
from praxis.kernel.gateway.policy import (
    GatewayPolicy,
    OperationalMisconfigurationError,
    policy_health_check,
)
from praxis.ports.virtual_key import VirtualKeyPort


def build_policy(
    *,
    allowed_user_ids: list[str],
    virtual_keys: VirtualKeyPort | None,
) -> GatewayPolicy:
    """Assemble a GatewayPolicy reflecting the operator's current config."""
    return GatewayPolicy(
        allowed_user_ids=frozenset(allowed_user_ids),
        virtual_keys=virtual_keys,
    )


def run_smoke(policy: GatewayPolicy) -> tuple[bool, str]:
    """Run the health check; return (healthy, message). Reads the deploy
    profile from the process environment (per ``policy_health_check``)."""
    try:
        policy_health_check(policy=policy)
    except OperationalMisconfigurationError as exc:
        return False, f"fail-closed: {exc}"
    return True, "policy-smoke: health check passed"


def main() -> int:
    allowed = [
        uid.strip()
        for uid in os.environ.get("VERDACA_ALLOWED_USER_IDS", "").split(",")
        if uid.strip()
    ]
    base_url = os.environ.get("LITELLM_PROXY_URL")
    master_key = os.environ.get("LITELLM_MASTER_KEY")
    # Construction is network-free; presence is what the health check inspects.
    virtual_keys: VirtualKeyPort | None = (
        LiteLLMVirtualKeyAdapter(base_url=base_url, master_key=master_key)
        if base_url and master_key
        else None
    )

    healthy, message = run_smoke(
        build_policy(allowed_user_ids=allowed, virtual_keys=virtual_keys)
    )
    print(message)
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
