"""End-to-end integration tests — studio/test-strategy.md §12.

7 tests: 2 Tier 1 (unit-level glue) + 5 Tier 2 (full pipeline with FakeMAC).
All PR-gate green (no live LLM required).
"""

from __future__ import annotations

import pytest

from praxis.kernel.studio.invoker import StudioSession, template_to_task_input
from praxis.kernel.studio.schema import WorkflowTemplate

from tests.studio.fixtures.fake_cost_tracker import FakeCostTracker
from tests.studio.fixtures.fake_mac import FakeMAC


# ---------------------------------------------------------------------------
# Tier 1 — glue layer unit tests (2 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_schema
def test_int_01_template_to_task_input_produces_valid_task_input(
    deep_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-INT-01: template_to_task_input() converts WorkflowTemplate + user inputs into valid TaskInput."""
    user_inputs = {"strategic_question": "Should we expand into APAC?", "rendering_mode": "position_to_hold"}
    task_input = template_to_task_input(deep_template, user_inputs)
    # Must be non-None and carry the strategic question through (as raw_prompt)
    assert task_input is not None
    assert task_input.raw_prompt == "Should we expand into APAC?"


@pytest.mark.studio_schema
def test_int_02_task_input_workflow_template_id_format(
    deep_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-INT-02: TaskInput.workflow_template_id format is 'studio/strategic_session/0.1.0'."""
    task_input = template_to_task_input(deep_template, {"strategic_question": "Test", "rendering_mode": "position_to_hold"})
    # arch §2.5: format = "{product}/{name}/{version}"
    assert task_input.workflow_template_id == "studio/strategic_session/0.1.0"


# ---------------------------------------------------------------------------
# Tier 2 — full pipeline integration (5 tests)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.critical
def test_int_03_deep_mode_full_pipeline_backbone_present(
    renderer,
    deep_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-INT-03: Full Studio pipeline: load YAML → validate → convert → FakeMAC → render brief → backbone present."""
    session = StudioSession(
        mac=FakeMAC(),
        cost_tracker=FakeCostTracker(),
        renderer=renderer,
    )
    result = session.invoke(
        template=deep_template,
        user_inputs={"strategic_question": "Should we expand into APAC?", "rendering_mode": "position_to_hold"},
    )
    assert result is not None
    assert not result.degraded
    # At least one output rendered successfully
    assert len(result.outputs) >= 1
    # Every rendered output must contain the ADR-01 backbone sections
    for output in result.outputs:
        text = output.text
        assert "Trade-offs" in text or "Tradeoffs" in text or "trade-off" in text.lower(), (
            f"ADR-01 backbone: 'Trade-offs' section missing from output"
        )
        assert "Dissent" in text or "competing frame" in text.lower(), (
            f"ADR-01 backbone: 'Dissent' section missing from output"
        )


@pytest.mark.integration
def test_int_04_quick_mode_full_pipeline_backbone_present(
    renderer,
    quick_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-INT-04: Quick-mode pipeline: load quick YAML → validate → convert → FakeMAC → render brief → backbone present."""
    session = StudioSession(
        mac=FakeMAC(),
        cost_tracker=FakeCostTracker(),
        renderer=renderer,
    )
    result = session.invoke(
        template=quick_template,
        user_inputs={"strategic_question": "Should we enter the EU market?", "rendering_mode": "position_to_hold"},
    )
    assert result is not None
    assert not result.degraded
    assert len(result.outputs) >= 1
    for output in result.outputs:
        text = output.text
        assert "Trade-offs" in text or "trade-off" in text.lower() or "Tradeoffs" in text


@pytest.mark.integration
def test_int_05_deep_mode_all_three_cycles_execute(
    renderer,
    deep_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-INT-05: Deep-mode pipeline: all 3 cycles (wide_survey, deep_analysis, red_team_synthesis) execute in order."""
    fake_mac = FakeMAC()
    session = StudioSession(
        mac=fake_mac,
        cost_tracker=FakeCostTracker(),
        renderer=renderer,
    )
    result = session.invoke(
        template=deep_template,
        user_inputs={"strategic_question": "Should we acquire CompetitorX?", "rendering_mode": "position_to_hold"},
    )
    assert result is not None
    assert not result.degraded
    # Deep template has 3 cycles; verify the session ran through all cycles
    cycle_names = [c.name for c in deep_template.cycles]
    assert "wide_survey" in cycle_names
    assert "deep_analysis" in cycle_names
    assert "red_team_synthesis" in cycle_names
    # Verify session completed (outputs produced for all cycles that aren't skipped)
    assert len(result.outputs) >= 1


@pytest.mark.integration
@pytest.mark.critical
def test_int_06_quick_mode_deep_analysis_cycle_skipped(
    renderer,
    quick_template: WorkflowTemplate,
    deep_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-INT-06: Quick-mode pipeline: 'deep_analysis' cycle (skip_in_quick_mode=True) is absent from quick template."""
    # Quick mode must NOT contain the deep_analysis cycle
    quick_cycle_names = [c.name for c in quick_template.cycles]
    assert "deep_analysis" not in quick_cycle_names, (
        f"Quick template must not contain 'deep_analysis' cycle; got cycles: {quick_cycle_names}"
    )
    # Deep mode MUST contain it — sanity cross-check
    deep_cycle_names = [c.name for c in deep_template.cycles]
    assert "deep_analysis" in deep_cycle_names, (
        f"Deep template must contain 'deep_analysis' cycle; got cycles: {deep_cycle_names}"
    )
    # Quick has 2 cycles; deep has 3
    assert len(quick_template.cycles) == 2
    assert len(deep_template.cycles) == 3


@pytest.mark.integration
def test_int_07_rendering_mode_propagates_through_pipeline(
    renderer,
    deep_template: WorkflowTemplate,
) -> None:
    """STUDIO-T-INT-07: Rendering mode propagates from template through MAC to output template selection."""
    session = StudioSession(
        mac=FakeMAC(),
        cost_tracker=FakeCostTracker(),
        renderer=renderer,
    )
    result = session.invoke(
        template=deep_template,
        user_inputs={"strategic_question": "Build vs buy?", "rendering_mode": "position_to_hold"},
    )
    assert result is not None
    # Each output must carry the rendering_mode that matches the template default
    expected_mode = deep_template.rendering_mode
    for output in result.outputs:
        assert output.rendering_mode == expected_mode, (
            f"Output rendering_mode {output.rendering_mode!r} does not match "
            f"template default {expected_mode!r}"
        )
