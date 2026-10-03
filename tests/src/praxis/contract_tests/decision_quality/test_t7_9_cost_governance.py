"""T7.9 Cost governance — Governance & Decision-Quality (T7) tier.

Literature source: Chen, Zaharia & Zou (2023) FrugalGPT
(verdaca-literature-review.md §"Assessment Approaches to Carry Forward for
Murat", row "Costs exceed budget or route to the wrong model"). The lever:
per-subject/per-key budgets must be ENFORCED (reject when exhausted) and every
invocation's cost must be RECORDED for a final cost summary.

Verdaca operationalization, asserted at two seams:
    1. Enforcement — an over-budget virtual key REJECTS via
       ``BudgetExhaustedError`` on the auth-first spine
       (``GatewayPolicy.enforce_budget`` → ``VirtualKeyPort.check_budget``).
       Direct (port-level) and end-to-end (through ``gateway.execute``, where
       it surfaces as a wrapped ``GatewayCtxError(auth:...BudgetExhaustedError)``
       BEFORE any LLM cost is burned).
    2. Accounting — a within-budget run RECORDS exactly one cost event on the
       ledger and emits a non-null ``cost_usd`` on the result (the FrugalGPT
       "final cost summary").

PASS: over-budget rejects (no LLM call, no cost burned) AND within-budget
records cost + emits a summary. Deterministic — no live backend, no creds.
Plain tests (NO @pytest.mark.no_waiver; 14/9/23 pin untouched).
"""

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
from praxis.kernel.gateway.policy import GatewayPolicy
from praxis.ports.gateway_errors import GatewayCtxError
from praxis.ports.virtual_key import BudgetExhaustedError


class _OverBudgetVirtualKeys:
    """VirtualKeyPort fake that REJECTS every check_budget — models a key that
    has reached its FrugalGPT spend cap. Records calls for assertion."""

    def __init__(self) -> None:
        self.checked: list[str] = []

    async def check_budget(self, key_alias: str) -> None:
        self.checked.append(key_alias)
        raise BudgetExhaustedError(f"virtual key {key_alias!r} is over budget")


def _policy(virtual_keys: object) -> GatewayPolicy:
    return GatewayPolicy(
        allowed_user_ids=frozenset({"user-1"}),
        virtual_keys=virtual_keys,  # type: ignore[arg-type]
    )


# ── Enforcement (FrugalGPT budget cap) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_T7_9_COST_over_budget_key_rejects_at_port(tmp_path) -> None:
    """Port-level: enforce_budget on an over-budget key raises
    BudgetExhaustedError (mirrors the destub over-budget path)."""
    adapter = _OverBudgetVirtualKeys()
    policy = _policy(adapter)
    claims = AuthClaims(_claims={"sub": "user-1"})
    with pytest.raises(BudgetExhaustedError):
        await policy.enforce_budget(claims)
    assert adapter.checked == ["user-1"]


def test_T7_9_COST_over_budget_key_rejects_before_llm_cost_burned(tmp_path) -> None:
    """End-to-end: an over-budget key rejects on the auth-first spine, so
    execute() raises and NO LLM call / NO cost record is produced — budget
    enforcement happens before spend, per FrugalGPT."""
    over_budget = _OverBudgetVirtualKeys()
    harness = make_gateway_harness(tmp_path, policy=_policy(over_budget))

    with pytest.raises(GatewayCtxError) as exc_info:
        harness.gateway.execute(make_intent(), make_ctx())

    assert exc_info.value.context_field.startswith("auth:")
    assert "BudgetExhaustedError" in exc_info.value.context_field
    # Nothing was spent: enforcement precedes the LLM call + cost record.
    assert harness.llm.calls == []
    assert harness.cost.records == []


# ── Accounting (per-invocation cost recorded + summary emitted) ─────────────


def test_T7_9_COST_within_budget_records_exactly_one_cost_event(tmp_path) -> None:
    """A within-budget run records exactly one cost ledger event scoped to the
    session — the per-invocation accounting FrugalGPT requires."""
    harness = make_gateway_harness(tmp_path, policy=_policy(FakeVirtualKeys()))

    result = harness.gateway.execute(make_intent(), make_ctx())

    assert len(harness.cost.records) == 1
    recorded = harness.cost.records[0]
    assert recorded.scope.scope_kind == "session"
    assert recorded.scope.scope_id == result.session.session_id
    assert recorded.input_tokens == 11
    assert recorded.output_tokens == 7


def test_T7_9_COST_result_emits_cost_summary(tmp_path) -> None:
    """Final cost summary: the AnalysisResult carries a non-null Decimal
    cost_usd derived from the ledger entry (FrugalGPT cost-summary lever)."""
    harness = make_gateway_harness(tmp_path, policy=_policy(FakeVirtualKeys()))

    result = harness.gateway.execute(make_intent(), make_ctx())

    assert result.cost_usd is not None
    assert isinstance(result.cost_usd, Decimal)
    assert result.cost_usd == Decimal("0.0123")
