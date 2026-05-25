"""Stage 11 gateway policy contract tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from praxis.contract_tests.ports.gateway_contract_fakes import (
    make_ctx,
    make_gateway_harness,
    make_intent,
)
from praxis.kernel.gateway import GatewayPolicy
from praxis.kernel.gateway.policy import verify_bearer_token
from praxis.ports.gateway_errors import GatewayCtxError


def test_M_T_GW_POLICY_USER_ALLOWLIST_01_default_empty_rejects_pre_call(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path, policy=GatewayPolicy())

    with pytest.raises(GatewayCtxError) as exc_info:
        harness.gateway.execute(make_intent(), make_ctx())

    assert exc_info.value.context_field == "policy:user_not_allowlisted"
    assert len(harness.llm.calls) == 0
    assert len(harness.cost.records) == 0


def test_M_T_GW_POLICY_USER_ALLOWLIST_01_explicit_allow_passes(tmp_path) -> None:
    harness = make_gateway_harness(
        tmp_path,
        policy=GatewayPolicy(allowed_user_ids=frozenset({"user-1"})),
    )

    result = harness.gateway.execute(make_intent(), make_ctx())

    assert result.session.status == "completed"
    assert len(harness.llm.calls) == 1


def test_M_T_GW_POLICY_BUDGET_CAP_01_over_cap_rejects_pre_call(tmp_path) -> None:
    harness = make_gateway_harness(
        tmp_path,
        consumed_usd=Decimal("5.00"),
        policy=GatewayPolicy(
            allowed_user_ids=frozenset({"user-1"}),
            per_user_budget_cap_usd=Decimal("1.00"),
        ),
    )

    with pytest.raises(GatewayCtxError) as exc_info:
        harness.gateway.execute(make_intent(), make_ctx())

    assert exc_info.value.context_field == "policy:user_budget_cap_exceeded"
    assert len(harness.cost.budget_checks) == 1
    assert len(harness.llm.calls) == 0
    assert len(harness.cost.records) == 0


def test_M_T_GW_POLICY_BUDGET_CAP_01_under_cap_passes(tmp_path) -> None:
    harness = make_gateway_harness(
        tmp_path,
        consumed_usd=Decimal("0.10"),
        policy=GatewayPolicy(
            allowed_user_ids=frozenset({"user-1"}),
            per_user_budget_cap_usd=Decimal("1.00"),
        ),
    )

    result = harness.gateway.execute(make_intent(), make_ctx())

    assert result.session.status == "completed"
    assert len(harness.llm.calls) == 1


def test_deployment_bearer_token_outer_gate(monkeypatch) -> None:
    monkeypatch.setenv("VERDACA_GATEWAY_BEARER_TOKEN", "expected-token")

    assert verify_bearer_token("Bearer expected-token") is True
    assert verify_bearer_token("Bearer wrong-token") is False
    assert verify_bearer_token(None) is False
