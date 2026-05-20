"""Cost Meter port contract tests — 8 MAC-Ts.

Per `test-strategy.md` v0.2 §2.2.5 — 8 binding `M-T-COST-*` MAC-Ts. Each
test below embeds its MAC-T ID in the function name; docstrings quote
the §2.2.5 assertion language verbatim for auditability.

Discipline (per Stage 9.4.4 Phase B.2 hand-off):
- Stay strictly within the 8-ID scope. No 9th test, no parametrized
  expansion, no opportunistic coverage.
- Test the public `CostMeterPort` Protocol surface via the adapter
  (single-adapter; Pi-Mono is in-tree-native — no substitute, NO
  parametric `[mem0, letta]`-style fixture).
- No `@pytest.mark.no_waiver` — Cost-meter has zero entries in the
  22-entry allow-list per `test-strategy.md` v0.2 §6.1 + advisor §3.1.
- M-T-COST-PARITY-01 uses pre-captured snapshot fixture at
  `tests/fixtures/pi_mono_parity_vectors.json` per Q-9.4.4-2 disposition
  (S9 advisor lock). Snapshot regeneration is Andrey-approved manual
  act per S12.

Runner invocation contract (per Q-9.4.4-6 = Option α):

    PYTHONPATH='adapters/pi_mono_native/src' uv run \\
        --package praxis-contract-tests pytest \\
        tests/src/praxis/contract_tests/ports/test_cost_meter_contract.py -v

Post-Cleo (workspace registration landed): naked `pytest` works.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from praxis.adapters.pi_mono_native import PiMonoNativeAdapter
from praxis.adapters.pi_mono_native.adapter import PRICING_TABLE_VERSION
from praxis.ports.cost_meter import (
    BudgetScope,
    CostEvent,
    CostLedgerEntry,
    CostQuery,
    CostReport,
    PricingTableMismatch,
)


_TEST_CORRELATION_ID = "test-correlation-cost-contract"


# Test-only payload constructors (per sibling test_versioned_state_contract.py:50-72
# + test_memory_contract.py `_entry` pattern).


def _scope(kind: str = "session", scope_id: str = "test-session-1") -> BudgetScope:
    return BudgetScope(
        schema_version=1,
        correlation_id=_TEST_CORRELATION_ID,
        idempotency_key=None,
        scope_kind=kind,  # type: ignore[arg-type]
        scope_id=scope_id,
    )


def _event(
    *,
    provider: str = "anthropic",
    model: str = "claude-opus-4-7",
    input_tokens: int = 1000,
    output_tokens: int = 500,
    idempotency_key: str = "test-event-key",
    scope: BudgetScope | None = None,
    correlation_id: str = _TEST_CORRELATION_ID,
) -> CostEvent:
    return CostEvent(
        schema_version=1,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        occurred_at=datetime(2026, 5, 8, tzinfo=timezone.utc),
        scope=scope or _scope(),
    )


@pytest.fixture
def adapter() -> PiMonoNativeAdapter:
    a = PiMonoNativeAdapter(
        budget_limits={"workspace:test-workspace": Decimal("10.00")},
        warning_threshold_fraction=0.8,
        default_correlation_id=_TEST_CORRELATION_ID,
    )
    a.on_init()
    return a


# ===========================================================================
# §2.2.5 MAC-Ts — 8 tests (zero @pytest.mark.no_waiver per advisor §3.1)
# ===========================================================================


def test_M_T_COST_RECORD_01_record_happy(adapter: PiMonoNativeAdapter) -> None:
    """`record(CostEvent(provider, model, input_tokens, output_tokens, ...))`
    Returns `CostLedgerEntry`; `cost_usd` is `Decimal` (not float);
    `ledger_id` is ULID-shaped; `pricing_table_version` on breakdown.
    Verbatim per test-strategy.md v0.2 §2.2.5."""
    event = _event(
        provider="anthropic",
        model="claude-opus-4-7",
        input_tokens=1000,
        output_tokens=500,
        idempotency_key="record-01",
    )
    entry = adapter.record(event)
    assert isinstance(entry, CostLedgerEntry)
    assert isinstance(entry.cost_usd, Decimal)
    assert not isinstance(entry.cost_usd, float)
    assert isinstance(entry.ledger_id, str)
    assert len(entry.ledger_id) > 0
    assert entry.cost_breakdown.pricing_table_version == PRICING_TABLE_VERSION


def test_M_T_COST_QUERY_01_query_aggregate(adapter: PiMonoNativeAdapter) -> None:
    """`query(CostQuery(scope))` against N ledger entries — Returns
    `CostReport`; aggregated `Decimal` sum matches sum-of-records."""
    scope = _scope("session", "agg-test")
    individual_costs: list[Decimal] = []
    for i in range(5):
        entry = adapter.record(
            _event(idempotency_key=f"agg-{i}", scope=scope, input_tokens=100 * (i + 1))
        )
        individual_costs.append(entry.cost_usd)
    report = adapter.query(
        CostQuery(
            schema_version=1,
            correlation_id=_TEST_CORRELATION_ID,
            idempotency_key=None,
            scope=scope,
        )
    )
    assert isinstance(report, CostReport)
    assert len(report.entries) == 5
    assert report.total_usd == sum(individual_costs, Decimal("0"))


def test_M_T_COST_BUDGET_OK_01_under_threshold(
    adapter: PiMonoNativeAdapter,
) -> None:
    """`budget_check(scope)` with `consumed < limit` — Returns
    `BudgetStatus(status="ok")`; `remaining_usd > 0`."""
    scope = BudgetScope(
        schema_version=1,
        correlation_id=_TEST_CORRELATION_ID,
        idempotency_key=None,
        scope_kind="workspace",
        scope_id="test-workspace",
    )
    # Tiny event well under $10 limit + 80% warn band ($8).
    adapter.record(
        _event(input_tokens=10, output_tokens=5, scope=scope, idempotency_key="budget-ok")
    )
    status = adapter.budget_check(scope)
    assert status.status == "ok"
    assert status.remaining_usd is not None
    assert status.remaining_usd > Decimal("0")


def test_M_T_COST_BUDGET_EXCEEDED_01_over_threshold(
    adapter: PiMonoNativeAdapter,
) -> None:
    """`budget_check(scope)` with `consumed > limit` — Returns
    `BudgetStatus(status="exceeded")`; downstream caller raises
    `BudgetExceeded`."""
    scope = BudgetScope(
        schema_version=1,
        correlation_id=_TEST_CORRELATION_ID,
        idempotency_key=None,
        scope_kind="workspace",
        scope_id="test-workspace",
    )
    # Limit is $10. Opus 4.7 input=$15/M; 1M tokens = $15 > $10 limit.
    adapter.record(
        _event(
            input_tokens=1_000_000,
            output_tokens=0,
            scope=scope,
            idempotency_key="budget-exceed",
        )
    )
    status = adapter.budget_check(scope)
    assert status.status == "exceeded"


def test_M_T_COST_PARITY_01_decimal_formula_parity(
    adapter: PiMonoNativeAdapter,
) -> None:
    """Parity test: N synthetic CostEvent → in-tree math vs snapshot fixture.

    Per Q-9.4.4-5 amended (S2 disposition): formula-parity, NOT byte-parity
    vs TS source. Fixture stores Decimal-derived expected values computed
    using same formula. Snapshot regeneration is Andrey-approved manual
    act per S12. ParityDrift raised with `(snapshot_hash, current_hash)`
    if drift detected — this test confirms parity, not divergence.
    """
    fixture_path = (
        Path(__file__).resolve().parents[5]
        / "tests"
        / "fixtures"
        / "pi_mono_parity_vectors.json"
    )
    assert fixture_path.exists(), f"parity fixture missing: {fixture_path}"
    vectors = json.loads(fixture_path.read_text(encoding="utf-8"))
    for vec in vectors["vectors"]:
        event = _event(
            provider=vec["provider"],
            model=vec["model"],
            input_tokens=vec["input_tokens"],
            output_tokens=vec["output_tokens"],
            idempotency_key=f"parity-{vec['id']}",
            scope=_scope("session", f"parity-{vec['id']}"),
        )
        entry = adapter.record(event)
        expected = Decimal(vec["expected_cost_usd"])
        assert entry.cost_usd == expected, (
            f"Parity drift on vector {vec['id']}: "
            f"expected {expected}, got {entry.cost_usd}"
        )


def test_M_T_COST_PRICING_MISMATCH_01_unknown_provider_model(
    adapter: PiMonoNativeAdapter,
) -> None:
    """`record()` with unknown `(provider, model)` — Raises
    `PricingTableMismatch`; `provider`, `model`, `pricing_table_version`
    set."""
    event = _event(
        provider="unknown-vendor",
        model="unknown-model",
        idempotency_key="pricing-mismatch",
    )
    with pytest.raises(PricingTableMismatch) as exc_info:
        adapter.record(event)
    assert exc_info.value.provider == "unknown-vendor"
    assert exc_info.value.model == "unknown-model"
    assert exc_info.value.pricing_table_version == PRICING_TABLE_VERSION


def test_M_T_COST_IDEMPOTENT_01_dedup_on_key(
    adapter: PiMonoNativeAdapter,
) -> None:
    """`record()` with duplicate `idempotency_key` — Returns same
    `CostLedgerEntry`; single record. Replay-storm safety per
    ADR-9.1.2-5 §3.1 idempotency profile."""
    event = _event(idempotency_key="dedup-key-1")
    entry_a = adapter.record(event)
    entry_b = adapter.record(event)
    assert entry_a.ledger_id == entry_b.ledger_id
    report = adapter.query(
        CostQuery(
            schema_version=1,
            correlation_id=_TEST_CORRELATION_ID,
            idempotency_key=None,
            scope=event.scope,
        )
    )
    assert len(report.entries) == 1


def test_M_T_COST_SCOPE_01_no_cross_scope_leakage(
    adapter: PiMonoNativeAdapter,
) -> None:
    """`query()` across session/user/workspace scopes — Correct
    aggregation per scope; no cross-scope leakage."""
    session_scope = _scope("session", "scope-test-session")
    user_scope = _scope("user", "scope-test-user")
    workspace_scope = _scope("workspace", "scope-test-workspace-2")
    adapter.record(_event(scope=session_scope, idempotency_key="scope-s"))
    adapter.record(_event(scope=user_scope, idempotency_key="scope-u"))
    adapter.record(_event(scope=workspace_scope, idempotency_key="scope-w"))
    for s in (session_scope, user_scope, workspace_scope):
        report = adapter.query(
            CostQuery(
                schema_version=1,
                correlation_id=_TEST_CORRELATION_ID,
                idempotency_key=None,
                scope=s,
            )
        )
        assert len(report.entries) == 1
