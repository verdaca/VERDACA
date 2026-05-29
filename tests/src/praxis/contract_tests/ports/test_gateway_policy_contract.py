"""Stage 11 gateway policy contract tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from praxis.contract_tests.ports.gateway_contract_fakes import (
    FakeVirtualKeys,
    make_ctx,
    make_gateway_harness,
    make_intent,
)
from praxis.kernel.auth import AuthClaims
from praxis.kernel.gateway import GatewayPolicy
from praxis.kernel.gateway.policy import (
    InvalidBearerError,
    OperationalMisconfigurationError,
    policy_health_check,
    verify_bearer_token,
)
from praxis.ports.gateway_errors import GatewayCtxError


class _FakeOidcPolicy:
    def __init__(self) -> None:
        self.tokens: list[str] = []

    async def authenticate(self, bearer_token: str) -> AuthClaims:
        self.tokens.append(bearer_token)
        return AuthClaims(_claims={"sub": "user-1", "iss": "issuer", "aud": "api://verdaca"})


def test_M_T_GW_POLICY_USER_ALLOWLIST_01_default_empty_rejects_pre_call(tmp_path) -> None:
    harness = make_gateway_harness(tmp_path, policy=GatewayPolicy())

    with pytest.raises(GatewayCtxError) as exc_info:
        harness.gateway.execute(make_intent(), make_ctx())

    assert exc_info.value.context_field == "auth:builtins.RuntimeError"
    assert len(harness.llm.calls) == 0
    assert len(harness.cost.records) == 0


def test_M_T_GW_POLICY_USER_ALLOWLIST_01_explicit_allow_passes(tmp_path) -> None:
    harness = make_gateway_harness(
        tmp_path,
        policy=GatewayPolicy(
            allowed_user_ids=frozenset({"user-1"}),
            virtual_keys=FakeVirtualKeys(),
        ),
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
            virtual_keys=FakeVirtualKeys(),
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
            virtual_keys=FakeVirtualKeys(),
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


def test_policy_health_check_warns_when_bearer_token_unset(monkeypatch, caplog) -> None:
    monkeypatch.delenv("VERDACA_GATEWAY_BEARER_TOKEN", raising=False)

    # Stage 14 B2: return type changed bool → None; side-effect-only callers
    # are backward-compatible. Assertion now verifies the implicit None return
    # plus the warning log.
    result = policy_health_check()

    assert result is None
    assert (
        "Bearer auth not configured (VERDACA_GATEWAY_BEARER_TOKEN unset): "
        "all requests will be rejected"
    ) in caplog.text


def test_M_T_POLICY_HEALTH_CHECK_PROD_FAIL_CLOSED_01_production_profile_none_vkey_raises(
    monkeypatch, caplog
) -> None:
    """Production profile + GatewayPolicy(virtual_keys=None) →
    OperationalMisconfigurationError (fail-closed at startup; catches
    Stage 13 V3.A contract violation early)."""
    monkeypatch.setenv("VERDACA_GATEWAY_BEARER_TOKEN", "set-to-isolate-vkey-check")
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "production")

    policy = GatewayPolicy()  # virtual_keys defaults to None

    with pytest.raises(OperationalMisconfigurationError, match="virtual_keys is None"):
        policy_health_check(policy=policy)


def test_M_T_POLICY_HEALTH_CHECK_DEV_WARNS_01_dev_profile_none_vkey_warns_only(
    monkeypatch, caplog
) -> None:
    """Dev profile (or unset) + GatewayPolicy(virtual_keys=None) → warning
    only, no raise. Operator gets visibility without blocking dev cycles."""
    monkeypatch.setenv("VERDACA_GATEWAY_BEARER_TOKEN", "set-to-isolate-vkey-check")
    monkeypatch.setenv("VERDACA_DEPLOY_PROFILE", "development")

    policy = GatewayPolicy()  # virtual_keys=None

    policy_health_check(policy=policy)  # Must NOT raise

    assert "vkey budget unenforced" in caplog.text


@pytest.mark.asyncio
async def test_M_T_AUTH_POLICY_OIDC_DELEGATE_01_authenticate_delegates_to_oidc_policy() -> None:
    oidc_policy = _FakeOidcPolicy()
    policy = GatewayPolicy(oidc_policy=oidc_policy)

    claims = await policy.authenticate("bearer-token", "tenant-1")

    assert claims.require("sub") == "user-1"
    assert oidc_policy.tokens == ["bearer-token"]


@pytest.mark.asyncio
async def test_M_T_AUTH_POLICY_EMPTY_BEARER_01_rejects_before_verifier() -> None:
    oidc_policy = _FakeOidcPolicy()
    policy = GatewayPolicy(oidc_policy=oidc_policy)

    with pytest.raises(InvalidBearerError, match="empty or missing"):
        await policy.authenticate("   ", "tenant-1")

    assert oidc_policy.tokens == []
