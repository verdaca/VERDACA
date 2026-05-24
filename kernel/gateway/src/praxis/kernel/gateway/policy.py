"""Gateway-owned policy gates for authorization and budget checks."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from praxis.ports.cost_meter import BudgetScope, CostMeterPort
from praxis.ports.gateway_dto import ChannelContext, StartAnalysisRequest


@dataclass(frozen=True, slots=True, kw_only=True)
class GatewayPolicy:
    """MVP gateway policy configuration."""

    allowed_user_ids: frozenset[str] = frozenset()
    per_user_budget_cap_usd: Decimal | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PolicyDecision:
    """Pre-call policy decision."""

    allowed: bool
    reason: str | None = None


def evaluate_user_allowlist(
    intent: StartAnalysisRequest,
    policy: GatewayPolicy,
) -> PolicyDecision:
    """Reject all users by default unless explicitly allow-listed."""
    if intent.requester_user_id not in policy.allowed_user_ids:
        return PolicyDecision(allowed=False, reason="user_not_allowlisted")
    return PolicyDecision(allowed=True)


def evaluate_budget_cap(
    ctx: ChannelContext,
    policy: GatewayPolicy,
    cost_meter: CostMeterPort,
) -> PolicyDecision:
    """Check per-user budget before gateway execution burns LLM cost."""
    if policy.per_user_budget_cap_usd is None:
        return PolicyDecision(allowed=True)

    budget_status = cost_meter.budget_check(
        BudgetScope(
            scope_kind="user",
            scope_id=ctx.caller_id,
            schema_version=1,
            correlation_id=ctx.request_id,
        )
    )
    if budget_status.consumed_usd >= policy.per_user_budget_cap_usd:
        return PolicyDecision(allowed=False, reason="budget_cap_exceeded")
    return PolicyDecision(allowed=True)


__all__ = [
    "GatewayPolicy",
    "PolicyDecision",
    "evaluate_budget_cap",
    "evaluate_user_allowlist",
]
