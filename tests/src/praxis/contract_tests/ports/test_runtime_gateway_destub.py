"""Stage 14 implementation-finalization — de-stub of build_runtime_gateway.

Plain contract tests (NO ``@pytest.mark.no_waiver`` → the 14/9/23 pin is
unaffected; de-stubbing is wiring, not a new invariant). These cover the
production-profile gating of the runtime composition: at
``VERDACA_DEPLOY_PROFILE=production`` the real adapter is composed and boot
fails CLOSED if creds are absent; at any other profile the Tier-1 stub is kept
so the hermetic, credential-less integration path (webhook + onboarding tests)
stays green.

FROZEN: drives ``composition.py`` selectors only; no kernel edit, no
marker/pin change, ``nonce_store=InMemoryNonceStore`` untouched (O-9 deferred).

Task 1 — VirtualKeys: record → ENFORCE.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest

import praxis.composition.runtime_gateway as comp
from praxis.adapters.litellm.virtual_keys import LiteLLMVirtualKeyAdapter
from praxis.adapters.pi_mono_native import PiMonoNativeAdapter
from praxis.kernel.auth import AuthClaims
from praxis.kernel.gateway.policy import GatewayPolicy
from praxis.ports.cost_meter import BudgetScope, CostEvent, PricingTableMismatch
from praxis.ports.llm_proxy import LLMProxyPort
from praxis.ports.virtual_key import BudgetExhaustedError

# ─── profile-gated selector (3 branches) ──────────────────────────────────


def test_vkey_nonproduction_keeps_tier1_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERDACA_DEPLOY_PROFILE", raising=False)
    vk = comp._build_virtual_keys()
    assert type(vk).__name__ == "_DemoStubVirtualKeys"


def test_vkey_production_without_creds_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    monkeypatch.delenv("LITELLM_PROXY_URL", raising=False)
    monkeypatch.delenv("LITELLM_MASTER_KEY", raising=False)
    with pytest.raises(comp.ConfigurationError):
        comp._build_virtual_keys()


def test_vkey_production_with_creds_is_real_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    monkeypatch.setenv("LITELLM_PROXY_URL", "https://litellm.example.invalid")
    monkeypatch.setenv("LITELLM_MASTER_KEY", "sk-master")
    vk = comp._build_virtual_keys()
    assert isinstance(vk, LiteLLMVirtualKeyAdapter)


# ─── enforcement is REAL, not theater ─────────────────────────────────────


class _FakeResp:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.status_code = 200

    def json(self) -> dict[str, object]:
        return self._payload


class _OverBudgetAsyncClient:
    """Stands in for httpx.AsyncClient; /key/info reports spend >= max_budget."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    async def __aenter__(self) -> "_OverBudgetAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, url: str, **kwargs: object) -> _FakeResp:
        return _FakeResp({"info": {"spend": 12.0, "max_budget": 5.0, "token": "sk-x"}})


@pytest.mark.asyncio
async def test_stub_vkey_is_theater_never_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Baseline being replaced: the stub records and never rejects."""
    monkeypatch.delenv("VERDACA_DEPLOY_PROFILE", raising=False)
    stub = comp._build_virtual_keys()
    await stub.check_budget("user-1")  # no raise — the theater


@pytest.mark.asyncio
async def test_real_vkey_enforce_budget_rejects_over_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The de-stubbed path: GatewayPolicy.enforce_budget (called unconditionally
    by the auth-first spine) REJECTS an over-budget key via the real adapter."""
    monkeypatch.setattr(httpx, "AsyncClient", _OverBudgetAsyncClient)
    adapter = LiteLLMVirtualKeyAdapter(
        base_url="https://litellm.example.invalid", master_key="sk-master"
    )
    policy = GatewayPolicy(virtual_keys=adapter)
    claims = AuthClaims(_claims={"sub": "user-1"})
    with pytest.raises(BudgetExhaustedError):
        await policy.enforce_budget(claims)


# ─── Task 2 — LLM proxy: stub → real DIAL-backed litellm (profile-gated) ───


def test_llm_proxy_nonproduction_keeps_tier1_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERDACA_DEPLOY_PROFILE", raising=False)
    proxy = comp._build_llm_proxy()
    assert type(proxy).__name__ == "_DemoStubLLMProxy"


def test_llm_proxy_production_without_dial_key_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    monkeypatch.delenv("DIAL_API_KEY", raising=False)
    with pytest.raises(comp.ConfigurationError):
        comp._build_llm_proxy()


def test_llm_proxy_production_with_dial_key_is_real_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    monkeypatch.setenv("DIAL_API_KEY", "dial-test-key")
    proxy = comp._build_llm_proxy()
    # create_dial_llm_proxy returns a LiteLLMAdapter conforming to LLMProxyPort
    # (runtime_checkable); construction is network-free.
    assert isinstance(proxy, LLMProxyPort)
    assert type(proxy).__name__ != "_DemoStubLLMProxy"


# ─── Task 3 — Cost meter: stub → real pi_mono (O-8 EQUAL: key normalized) ──


def _scope() -> BudgetScope:
    return BudgetScope(
        scope_kind="user",
        scope_id="user-1",
        schema_version=1,
        correlation_id="cid-cost-1",
    )


def _azure_gpt4o_event(*, idempotency_key: str) -> CostEvent:
    return CostEvent(
        schema_version=1,
        correlation_id="cid-cost-1",
        idempotency_key=idempotency_key,
        provider="azure",  # DIAL_LITELLM_PROVIDER — the O-8 row absent from PRICING_TABLE
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=1000,
        occurred_at=datetime(2026, 5, 30, tzinfo=timezone.utc),
        scope=_scope(),
    )


def test_cost_meter_nonproduction_keeps_tier1_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERDACA_DEPLOY_PROFILE", raising=False)
    cm = comp._build_cost_meter()
    assert type(cm).__name__ == "_DemoStubCostMeter"


def test_cost_meter_production_is_decorated_real_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    cm = comp._build_cost_meter()
    assert type(cm).__name__ == "_DialKeyNormalizingCostMeter"


def test_undecorated_real_adapter_raises_on_azure_row() -> None:
    """The O-8 defect: the real PiMonoNativeAdapter has no ("azure","gpt-4o")
    row, so it raises PricingTableMismatch — why the demo stubbed cost."""
    with pytest.raises(PricingTableMismatch):
        PiMonoNativeAdapter().record(_azure_gpt4o_event(idempotency_key="azure-raw"))


def test_decorator_prices_azure_identically_to_openai_row() -> None:
    """O-8 EQUAL fix: the decorator prices ("azure","gpt-4o") via the
    ("openai","gpt-4o") row — same model, same list price — so the cost is
    byte-identical to recording the event as openai. No PRICING_TABLE edit."""
    azure_event = _azure_gpt4o_event(idempotency_key="azure-dec")
    decorated_cost = comp._DialKeyNormalizingCostMeter(PiMonoNativeAdapter()).record(
        azure_event
    ).cost_usd

    openai_event = azure_event.model_copy(
        update={"provider": "openai", "idempotency_key": "openai-ref"}
    )
    expected_cost = PiMonoNativeAdapter().record(openai_event).cost_usd

    assert decorated_cost == expected_cost


# ─── Task 4 — Memory: stub → Letta (Mem0 backing absent), profile-gated ────


def test_memory_nonproduction_keeps_tier1_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERDACA_DEPLOY_PROFILE", raising=False)
    mem = comp._build_memory()
    assert type(mem).__name__ == "_DemoStubMemory"


def test_memory_production_without_letta_env_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    monkeypatch.delenv("LETTA_API_KEY", raising=False)
    monkeypatch.delenv("LETTA_BASE_URL", raising=False)
    with pytest.raises(comp.ConfigurationError):
        comp._build_memory()


def test_memory_production_with_letta_env_is_real_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")
    monkeypatch.setenv("LETTA_API_KEY", "letta-test-key")
    monkeypatch.setenv("LETTA_BASE_URL", "http://localhost:8283")
    mem = comp._build_memory()
    # Letta SDK reads env at construction (no server contact); LettaAdapter wraps it.
    assert type(mem).__name__ == "LettaAdapter"
    assert type(mem).__name__ != "_DemoStubMemory"
