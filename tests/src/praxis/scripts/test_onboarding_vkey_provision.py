"""Stage 14 Phase-1 [H#2] — vkey-provision.py onboarding test.

Plain test (NO ``@pytest.mark.no_waiver`` → pin 14/9/23 unaffected). Verifies
the provision step uses the LiteLLM virtual-key port with a CONSERVATIVE budget
cap, via an injected fake adapter (no live proxy).
"""

from __future__ import annotations

import asyncio
from types import ModuleType
from typing import Callable

import pytest

from praxis.ports.virtual_key import VirtualKeyInfo, VirtualKeySpec

LoadScript = Callable[[str, str], ModuleType]


class _FakeVKeyAdapter:
    """Records the spec it was asked to create; returns a canned VirtualKeyInfo."""

    def __init__(self) -> None:
        self.created: list[VirtualKeySpec] = []

    async def create_virtual_key(self, spec: VirtualKeySpec) -> VirtualKeyInfo:
        self.created.append(spec)
        return VirtualKeyInfo(
            key_alias=spec.key_alias,
            token="sk-demo-0123456789abcdef",
            spend=0.0,
            max_budget=spec.max_budget,
            is_over_budget=False,
        )


@pytest.fixture()
def vkey(load_onboarding_script: LoadScript) -> ModuleType:
    return load_onboarding_script("vkey-provision.py", "onboarding_vkey_provision")


def test_conservative_spec_has_a_low_budget_cap(vkey: ModuleType) -> None:
    spec = vkey.conservative_spec("verdaca-demo-user")
    assert spec.key_alias == "verdaca-demo-user"
    # "conservative" = a demo cap, not a production allocation.
    assert 0 < spec.max_budget <= 10.0
    assert spec.max_parallel_requests <= 4
    assert spec.allowed_models  # non-empty


def test_provision_calls_adapter_with_conservative_spec(vkey: ModuleType) -> None:
    adapter = _FakeVKeyAdapter()
    spec = vkey.conservative_spec("verdaca-demo-user")
    info = asyncio.run(vkey.provision(adapter, spec))

    assert adapter.created == [spec]
    assert info.key_alias == "verdaca-demo-user"
    assert info.max_budget == spec.max_budget
    assert info.max_budget <= 10.0


def test_key_prefix_truncates(vkey: ModuleType) -> None:
    assert vkey._key_prefix("sk-demo-0123456789").endswith("…")
    assert vkey._key_prefix("short") == "short"
