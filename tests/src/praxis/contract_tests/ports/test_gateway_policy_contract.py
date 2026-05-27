"""Stage 11 gateway policy contract tests."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

import praxis.kernel.gateway.policy as policy_module
from praxis.contract_tests.ports.gateway_contract_fakes import (
    make_ctx,
    make_gateway_harness,
    make_intent,
)
from praxis.kernel.auth import AuthClaims, OidcMetadata
from praxis.kernel.gateway import GatewayPolicy
from praxis.kernel.gateway.policy import policy_health_check, verify_bearer_token
from praxis.ports.gateway_errors import GatewayCtxError

JoseError = type("JoseError", (Exception,), {"__module__": "authlib.jose.errors"})


class _FakeJwksCache:
    def __init__(self) -> None:
        self.get_calls: list[str] = []
        self.invalidate_calls: list[str] = []

    async def get_or_fetch(self, issuer: str) -> tuple[OidcMetadata, dict[str, Any]]:
        self.get_calls.append(issuer)
        return _metadata(issuer), {"keys": ["stale"]}

    async def invalidate(self, issuer: str) -> tuple[OidcMetadata, dict[str, Any]]:
        self.invalidate_calls.append(issuer)
        return _metadata(issuer), {"keys": ["fresh"]}


class _RetryVerifier:
    attempts = 0

    def __init__(self, metadata: OidcMetadata, jwks: dict[str, Any]) -> None:
        self.metadata = metadata
        self.jwks = jwks

    def decode(self, token: str, audience: str) -> AuthClaims:
        _RetryVerifier.attempts += 1
        if _RetryVerifier.attempts == 1:
            raise JoseError("stale key")
        assert token == "bearer-token"
        assert audience == "api://verdaca"
        assert self.jwks == {"keys": ["fresh"]}
        return AuthClaims(_claims={"sub": "user-1", "iss": self.metadata.issuer, "aud": audience})


def _metadata(issuer: str) -> OidcMetadata:
    return OidcMetadata(
        issuer=issuer,
        jwks_uri=f"{issuer}/keys",
        id_token_signing_alg_values_supported=["RS256"],
    )


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


def test_policy_health_check_warns_when_bearer_token_unset(monkeypatch, caplog) -> None:
    monkeypatch.delenv("VERDACA_GATEWAY_BEARER_TOKEN", raising=False)

    assert policy_health_check() is False
    assert "auth misconfigured - all requests will reject" in caplog.text


@pytest.mark.asyncio
async def test_M_T_AUTH_POLICY_RETRY_ON_JOSE_ERROR_01_invalidates_jwks_once(
    monkeypatch,
) -> None:
    jwks_cache = _FakeJwksCache()
    _RetryVerifier.attempts = 0
    monkeypatch.setattr(policy_module, "JwtVerifier", _RetryVerifier)
    policy = GatewayPolicy(
        jwks_cache=jwks_cache,
        tenant_idp_map={"tenant-1": "https://issuer.example.invalid"},
        expected_audience="api://verdaca",
    )

    claims = await policy.authenticate("bearer-token", "tenant-1")

    assert claims._claims["sub"] == "user-1"
    assert jwks_cache.get_calls == ["https://issuer.example.invalid"]
    assert jwks_cache.invalidate_calls == ["https://issuer.example.invalid"]
    assert _RetryVerifier.attempts == 2
