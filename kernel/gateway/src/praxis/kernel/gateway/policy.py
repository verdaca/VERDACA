"""Gateway-owned policy gates for authorization and budget checks."""

from __future__ import annotations

import logging
import os
import secrets
from dataclasses import dataclass
from decimal import Decimal

from praxis.kernel.auth import AuthClaims, JwksCache, JwtVerifier
from praxis.ports.cost_meter import BudgetScope, BudgetStatus, CostMeterPort
from praxis.ports.gateway import GatewayPort
from praxis.ports.gateway_dto import AnalysisResult, ChannelContext, StartAnalysisRequest
from praxis.ports.virtual_key import VirtualKeyPort

_BEARER_PREFIX = "Bearer "
_DEPLOYMENT_TOKEN_ENV = "VERDACA_GATEWAY_BEARER_TOKEN"
_LOGGER = logging.getLogger(__name__)


class UnknownTenantError(ValueError):
    """Raised when no IdP issuer is configured for a tenant."""


@dataclass(frozen=True, slots=True, kw_only=True)
class GatewayPolicy:
    """Gateway policy configuration and Stage 12 auth orchestration."""

    allowed_user_ids: frozenset[str] = frozenset()
    per_user_budget_cap_usd: Decimal | None = None
    per_workspace_budget_cap_usd: Decimal | None = None
    gateway: GatewayPort | None = None
    virtual_keys: VirtualKeyPort | None = None
    jwks_cache: JwksCache | None = None
    tenant_idp_map: dict[str, str] | None = None
    expected_audience: str | None = None

    async def authenticate(self, bearer_token: str, tenant_id: str) -> AuthClaims:
        """Validate a tenant-scoped bearer token through kernel auth primitives."""
        if self.jwks_cache is None or self.expected_audience is None:
            raise RuntimeError("GatewayPolicy auth dependencies are not configured")
        issuer = (self.tenant_idp_map or {}).get(tenant_id)
        if issuer is None:
            raise UnknownTenantError(tenant_id)

        metadata, jwks = await self.jwks_cache.get_or_fetch(issuer)
        verifier = JwtVerifier(metadata, jwks)
        try:
            return verifier.decode(bearer_token, audience=self.expected_audience)
        except Exception as exc:
            if not _is_jose_error(exc):
                raise
            metadata, jwks = await self.jwks_cache.invalidate(issuer)
            verifier = JwtVerifier(metadata, jwks)
            return verifier.decode(bearer_token, audience=self.expected_audience)

    async def enforce_budget(self, claims: AuthClaims) -> None:
        """Enforce virtual-key budget for the authenticated subject."""
        if self.virtual_keys is None:
            raise RuntimeError("GatewayPolicy virtual-key dependency is not configured")
        await self.virtual_keys.check_budget(claims._claims["sub"])

    async def execute(self, intent: StartAnalysisRequest, ctx: ChannelContext) -> AnalysisResult:
        """Authenticate, enforce virtual-key budget, then delegate to GatewayPort."""
        if self.gateway is None:
            raise RuntimeError("GatewayPolicy gateway dependency is not configured")
        claims = await self.authenticate(ctx.rate_limit_token or "", intent.workspace_id)
        await self.enforce_budget(claims)
        return self.gateway.execute(intent, ctx)


@dataclass(frozen=True, slots=True, kw_only=True)
class PolicyDecision:
    """Pre-call policy decision."""

    allowed: bool
    reason: str | None = None


def verify_bearer_token(token: str | None) -> bool:
    """Validate the deployment bearer token without exposing the configured secret."""
    expected = os.environ.get(_DEPLOYMENT_TOKEN_ENV)
    if expected is None or token is None:
        return False

    candidate = token.removeprefix(_BEARER_PREFIX)
    return secrets.compare_digest(candidate, expected)


def policy_health_check() -> bool:
    """Warn at startup when deployment bearer auth is not configured."""
    if os.environ.get(_DEPLOYMENT_TOKEN_ENV) is None:
        _LOGGER.warning(
            "Bearer auth not configured (%s unset): all requests will be rejected",
            _DEPLOYMENT_TOKEN_ENV,
        )
        return False
    return True


def evaluate_user_allowlist(
    intent: StartAnalysisRequest,
    policy: GatewayPolicy,
) -> PolicyDecision:
    """Reject all users by default unless explicitly allow-listed."""
    if intent.requester_user_id not in policy.allowed_user_ids:
        return PolicyDecision(allowed=False, reason="user_not_allowlisted")
    return PolicyDecision(allowed=True)


def evaluate_budget_cap(
    intent: StartAnalysisRequest,
    ctx: ChannelContext,
    policy: GatewayPolicy,
    cost_meter: CostMeterPort,
) -> PolicyDecision:
    """Check user/workspace budget before gateway execution burns LLM cost."""
    user_decision = _evaluate_scope_cap(
        cost_meter.budget_check(
            BudgetScope(
                scope_kind="user",
                scope_id=ctx.caller_id,
                schema_version=1,
                correlation_id=ctx.request_id,
            )
        ),
        policy.per_user_budget_cap_usd,
        "user_budget_cap_exceeded",
    )
    if not user_decision.allowed:
        return user_decision

    return _evaluate_scope_cap(
        cost_meter.budget_check(
            BudgetScope(
                scope_kind="workspace",
                scope_id=intent.workspace_id,
                schema_version=1,
                correlation_id=ctx.request_id,
            )
        ),
        policy.per_workspace_budget_cap_usd,
        "workspace_budget_cap_exceeded",
    )


def evaluate_safety(intent: StartAnalysisRequest) -> PolicyDecision:
    """MVP deterministic pre-call safety gate."""
    if not intent.question.strip():
        return PolicyDecision(allowed=False, reason="empty_question")
    return PolicyDecision(allowed=True)


def evaluate_gateway_policy(
    intent: StartAnalysisRequest,
    ctx: ChannelContext,
    policy: GatewayPolicy,
    cost_meter: CostMeterPort,
) -> PolicyDecision:
    """Evaluate all inner gateway policy gates before downstream calls."""
    for decision in (
        evaluate_user_allowlist(intent, policy),
        evaluate_budget_cap(intent, ctx, policy, cost_meter),
        evaluate_safety(intent),
    ):
        if not decision.allowed:
            return decision
    return PolicyDecision(allowed=True)


def _is_jose_error(exc: Exception) -> bool:
    module = type(exc).__module__.lower()
    name = type(exc).__name__
    return "jose" in module or name.endswith("JoseError")


def _evaluate_scope_cap(
    status: BudgetStatus,
    cap_usd: Decimal | None,
    reason: str,
) -> PolicyDecision:
    if cap_usd is None:
        return PolicyDecision(allowed=True)
    if status.consumed_usd >= cap_usd:
        return PolicyDecision(allowed=False, reason=reason)
    return PolicyDecision(allowed=True)


__all__ = [
    "GatewayPolicy",
    "PolicyDecision",
    "UnknownTenantError",
    "evaluate_budget_cap",
    "evaluate_gateway_policy",
    "evaluate_safety",
    "evaluate_user_allowlist",
    "policy_health_check",
    "verify_bearer_token",
]
