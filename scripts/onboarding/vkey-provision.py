#!/usr/bin/env python
"""Onboarding step 2 — issue a per-user virtual key with a conservative cap.

Calls ``LiteLLMVirtualKeyAdapter.create_virtual_key`` against the configured
LiteLLM proxy and prints the key prefix + how to revoke it. The budget cap is
deliberately conservative so a demo cannot run up unbounded spend.
"""

from __future__ import annotations

import asyncio
import os
import sys

from praxis.adapters.litellm.virtual_keys import LiteLLMVirtualKeyAdapter
from praxis.ports.virtual_key import VirtualKeyInfo, VirtualKeySpec, VirtualKeyPort

# Conservative defaults — a demo key, not a production allocation.
CONSERVATIVE_MAX_BUDGET_USD: float = 5.0
CONSERVATIVE_MAX_PARALLEL: int = 2
DEFAULT_DURATION: str = "30d"
DEFAULT_MODELS: tuple[str, ...] = ("gpt-4o",)


def conservative_spec(key_alias: str, *, models: list[str] | None = None) -> VirtualKeySpec:
    """Build a conservatively-capped VirtualKeySpec for a demo caller."""
    return VirtualKeySpec(
        key_alias=key_alias,
        max_budget=CONSERVATIVE_MAX_BUDGET_USD,
        max_parallel_requests=CONSERVATIVE_MAX_PARALLEL,
        allowed_models=list(models) if models else list(DEFAULT_MODELS),
        duration=DEFAULT_DURATION,
    )


async def provision(adapter: VirtualKeyPort, spec: VirtualKeySpec) -> VirtualKeyInfo:
    """Issue the virtual key via the port (adapter is injectable for testing)."""
    return await adapter.create_virtual_key(spec)


def _key_prefix(token: str) -> str:
    return f"{token[:8]}…" if len(token) > 8 else token


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    key_alias = args[0] if args else "verdaca-demo-user"

    base_url = os.environ.get("LITELLM_PROXY_URL")
    master_key = os.environ.get("LITELLM_MASTER_KEY")
    if not base_url or not master_key:
        print("ERROR: LITELLM_PROXY_URL and LITELLM_MASTER_KEY are required")
        return 1

    adapter = LiteLLMVirtualKeyAdapter(base_url=base_url, master_key=master_key)
    info = asyncio.run(provision(adapter, conservative_spec(key_alias)))
    print(
        f"provisioned vkey alias={info.key_alias} "
        f"prefix={_key_prefix(info.token)} max_budget=${info.max_budget}"
    )
    print(
        f"revoke: POST {base_url.rstrip('/')}/key/delete "
        f"(key_aliases=[{info.key_alias!r}]) with the master key"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
