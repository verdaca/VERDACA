"""Gateway-owned policy gates for authorization and budget checks."""

from __future__ import annotations

import hmac
import os
from dataclasses import dataclass
from decimal import Decimal

from praxis.ports.cost_meter import BudgetScope, BudgetStatus, CostMeterPort
from praxis.ports.gateway_dto import ChannelContext, StartAnalysisRequest

_BEARER_PREFIX = "Bearer "
_DEPLOYMENT_TOKEN_ENV = "VERDACA_GATEWAY_BEARER_TOKEN"


@dataclass(frozen=True, slots=True, kw_only=True)
class GatewayPolicy:
    """MVP gateway policy configuration."""

    allowed_user_ids: frozenset[str] = frozenset()
    per_user_budget_cap_usd: Decimal | None = None
    per_workspace_budget_cap_usd: Decimal | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PolicyDecision:
    """Pre-call policy decision."""

    allowed: bool
    reason: str | None = None


def verify_bearer_token(token: str | None) -> bool:
    """Validate the deployment bearer token without exposing the configured secret."""
    # TODO(future-auth-stage, STAGE-11-DEBT-AUTH-01): replace deployment token with
    # OAuth/OIDC identity-provider validation and group mapping.
    expected = os.environ.get(_DEPLOYMENT_TOKEN_ENV)
    if expected is None or token is None:
        return False

    candidate = token.removeprefix(_BEARER_PREFIX)
    return hmac.compare_digest(candidate, expected)


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
    # TODO(future-auth-stage, STAGE-11-DEBT-LITELLM-VKEY-01): enforce model
    # allow-lists and budget policy with LiteLLM virtual keys once available.
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
    "evaluate_budget_cap",
    "evaluate_gateway_policy",
    "evaluate_safety",
    "evaluate_user_allowlist",
    "verify_bearer_token",
]
