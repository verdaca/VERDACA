"""Stage 11 gateway DIAL execution contract tests."""

from __future__ import annotations

import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from praxis.contract_tests.ports.gateway_contract_fakes import (
    CountingSqliteSessionIndex,
    FakeCompaction,
    FakeCostMeter,
    FakeMemory,
    FakeOidcPolicy,
    FakeVirtualKeys,
    make_auth_quartet,
    make_ctx,
    make_intent,
)
from praxis.kernel.gateway import (
    DIAL_API_BASE,
    DIAL_API_VERSION,
    DIAL_LITELLM_MODEL,
    DIAL_LITELLM_PROVIDER,
    GatewayPolicy,
    GatewayWalConfig,
    GatewayWalStore,
    VerdacaGatewayService,
    create_dial_llm_proxy,
)


def _completion_response() -> MagicMock:
    usage = MagicMock()
    usage.model_dump.return_value = {"prompt_tokens": 13, "completion_tokens": 8}
    choice = MagicMock()
    choice.finish_reason = "stop"
    choice.message.content = "Route confirmed."
    response = MagicMock()
    response.id = "dial-response-1"
    response.choices = [choice]
    response.usage = usage
    return response


def _dial_gateway(tmp_path, *, api_key: str | None = "test-key") -> VerdacaGatewayService:
    jwt_verifier, _oidc_policy, nonce_store, webhook_resolver = make_auth_quartet()
    oidc_policy = FakeOidcPolicy()
    return VerdacaGatewayService(
        llm_proxy=create_dial_llm_proxy(api_key=api_key),
        memory=FakeMemory(),
        cost_meter=FakeCostMeter(consumed_usd=Decimal("0")),
        compaction=FakeCompaction(),
        session_index=CountingSqliteSessionIndex(tmp_path / "session-index.sqlite3"),
        channel_adapters={},
        jwt_verifier=jwt_verifier,
        oidc_policy=oidc_policy,
        nonce_store=nonce_store,
        webhook_resolver=webhook_resolver,
        wal_store=GatewayWalStore(
            GatewayWalConfig(database_path=tmp_path / "gateway-idempotency.sqlite3")
        ),
        policy=GatewayPolicy(
            allowed_user_ids=frozenset({"user-1"}),
            oidc_policy=oidc_policy,
            virtual_keys=FakeVirtualKeys(),
        ),
    )


def test_M_T_DIAL_EXEC_ROUTING_01_gateway_uses_pinned_litellm_call_args(tmp_path) -> None:
    gateway = _dial_gateway(tmp_path)

    with patch("praxis.adapters.litellm.adapter.litellm.completion") as mock_completion:
        mock_completion.return_value = _completion_response()
        gateway.execute(make_intent(), make_ctx())

    kwargs = mock_completion.call_args.kwargs
    assert kwargs["model"] == f"{DIAL_LITELLM_PROVIDER}/{DIAL_LITELLM_MODEL}"
    assert kwargs["api_key"] == "test-key"
    assert kwargs["api_base"] == DIAL_API_BASE


def test_M_T_DIAL_EXEC_API_VERSION_01_gateway_sets_dial_api_version(tmp_path) -> None:
    gateway = _dial_gateway(tmp_path)

    with patch("praxis.adapters.litellm.adapter.litellm.completion") as mock_completion:
        mock_completion.return_value = _completion_response()
        gateway.execute(make_intent(), make_ctx())

    assert mock_completion.call_args.kwargs["api_version"] == DIAL_API_VERSION


def test_M_T_DIAL_EXEC_LIVE_ROUTING_01_env_gated_live_smoke(tmp_path) -> None:
    api_key = os.environ.get("DIAL_API_KEY")
    if api_key is None:
        pytest.skip("DIAL_API_KEY unset; advisor runs VPN-on smoke manually")

    gateway = _dial_gateway(tmp_path, api_key=api_key)
    result = gateway.execute(make_intent(idempotency_key="dial-live-smoke"), make_ctx())

    assert result.session.status == "completed"
    assert result.recommendation
