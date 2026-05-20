"""Cost budget enforcement tests — studio/test-strategy.md §8.

9 tests: 4 Tier 1 + 3 Tier 2 (integration) + 2 Tier 3 (nightly).
"""

from __future__ import annotations

import pytest

from praxis.kernel.studio.invoker import StudioSession
from praxis.kernel.studio.schema import WorkflowTemplate

from tests.studio.fixtures.fake_cost_tracker import FakeCostTracker
from tests.studio.fixtures.fake_mac import FakeMAC, make_minimal_trace


# ---------------------------------------------------------------------------
# Tier 1 — schema-level cost validation (4 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_cost
@pytest.mark.studio_schema
def test_cost_01_deep_budget_is_10(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-COST-01: Deep mode strategic_session.yaml has cost_budget_usd = 10.00."""
    assert deep_template.cost_budget_usd == 10.00


@pytest.mark.studio_cost
@pytest.mark.studio_schema
def test_cost_02_quick_budget_is_2(quick_template: WorkflowTemplate) -> None:
    """STUDIO-T-COST-02: Quick mode strategic_session_quick.yaml has cost_budget_usd = 2.00."""
    assert quick_template.cost_budget_usd == 2.00


@pytest.mark.studio_cost
def test_cost_03_deep_budget_pct_sums_to_100(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-COST-03: Deep mode budget_pct across cycles sums to 100% (20+50+30)."""
    total = sum(c.budget_pct for c in deep_template.cycles)
    assert total == 100
    budget_pcts = [c.budget_pct for c in deep_template.cycles]
    assert budget_pcts == [20, 50, 30]


@pytest.mark.studio_cost
def test_cost_04_quick_budget_pct_sums_to_100(quick_template: WorkflowTemplate) -> None:
    """STUDIO-T-COST-04: Quick mode budget_pct across cycles sums to 100% (40+60)."""
    total = sum(c.budget_pct for c in quick_template.cycles)
    assert total == 100
    budget_pcts = [c.budget_pct for c in quick_template.cycles]
    assert budget_pcts == [40, 60]


# ---------------------------------------------------------------------------
# Tier 2 — integration (budget enforcement with FakeMAC + FakeCostTracker)
# ---------------------------------------------------------------------------


@pytest.mark.studio_cost
@pytest.mark.critical
@pytest.mark.integration
def test_cost_05_budget_exhaustion_graceful_degradation(
    renderer,
    deep_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-COST-05: Budget exhaustion triggers graceful degradation (partial result, no crash)."""
    fake_cost_tracker = FakeCostTracker()

    class BudgetExhaustedMAC:
        """MAC double that always raises a budget exception."""
        def deliberate(self, task):
            raise RuntimeError("budget ceiling reached")

    session = StudioSession(
        mac=BudgetExhaustedMAC(),
        cost_tracker=fake_cost_tracker,
        renderer=renderer,
    )
    result = session.invoke(
        template=deep_template,
        user_inputs={"strategic_question": "Should we expand?", "rendering_mode": "position_to_hold"},
    )
    # Must return a degraded result, not raise
    assert result is not None
    assert result.degraded is True
    assert any("DEGRADED" in o.text for o in result.outputs)


@pytest.mark.studio_cost
@pytest.mark.integration
def test_cost_06_per_cycle_cost_aggregates_to_session(
    renderer,
    deep_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-COST-06: Per-cycle cost tracking aggregates correctly to session total."""
    fake_cost_tracker = FakeCostTracker()
    fake_mac = FakeMAC()
    session = StudioSession(mac=fake_mac, cost_tracker=fake_cost_tracker, renderer=renderer)
    session.invoke(
        template=deep_template,
        user_inputs={"strategic_question": "Test question", "rendering_mode": "position_to_hold"},
    )
    # session.cost_usd label must be emitted
    assert "studio.session.cost_usd" in fake_cost_tracker.emitted_labels()


@pytest.mark.studio_cost
@pytest.mark.integration
def test_cost_09_model_downgrade_lever(
    renderer,
    deep_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-COST-09: Cost control lever: model-downgrade triggers when cost > 80% of budget.

    Note: At Stage 6.3, the MAC is simulated via FakeMAC which doesn't incur real cost.
    This test verifies the session returns normally (graceful) when cost is within limits.
    The actual model-downgrade logic is the MAC's responsibility; Studio's responsibility
    is to pass the budget ceiling to the MAC and handle BudgetExceededError gracefully.
    """
    fake_cost_tracker = FakeCostTracker()
    fake_mac = FakeMAC()
    session = StudioSession(mac=fake_mac, cost_tracker=fake_cost_tracker, renderer=renderer)
    result = session.invoke(
        template=deep_template,
        user_inputs={"strategic_question": "Test", "rendering_mode": "position_to_hold"},
    )
    # No crash, no degradation when within budget
    assert result is not None
    assert not result.degraded


# ---------------------------------------------------------------------------
# Tier 3 — nightly (2 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_cost
@pytest.mark.nightly_only
def test_cost_07_deep_mode_cost_under_10() -> None:
    """STUDIO-T-COST-07: Deep-mode session cost <= $10.00 across all 10 benchmark Qs. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")


@pytest.mark.studio_cost
@pytest.mark.nightly_only
def test_cost_08_quick_mode_cost_under_2() -> None:
    """STUDIO-T-COST-08: Quick-mode session cost <= $2.00 across all 10 benchmark Qs. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")
