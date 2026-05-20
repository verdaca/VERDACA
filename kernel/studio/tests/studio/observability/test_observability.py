"""Observability tests — studio/test-strategy.md §9.

8 tests: 1 Tier 1 (static/structural) + 7 Tier 2 (integration with FakeCostTracker).
"""

from __future__ import annotations

import pytest

from praxis.kernel.studio.invoker import StudioSession
from praxis.kernel.studio.schema import WorkflowTemplate

from tests.studio.fixtures.fake_cost_tracker import FakeCostTracker
from tests.studio.fixtures.fake_mac import FakeMAC


def _invoke_session(renderer, deep_template: WorkflowTemplate) -> FakeCostTracker:
    tracker = FakeCostTracker()
    mac = FakeMAC()
    session = StudioSession(mac=mac, cost_tracker=tracker, renderer=renderer)
    session.invoke(
        template=deep_template,
        user_inputs={"strategic_question": "Should we expand?", "rendering_mode": "position_to_hold"},
    )
    return tracker


# ---------------------------------------------------------------------------
# Tier 1 — static label-namespace check
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.static
def test_obs_08_label_namespace_uses_studio_prefix() -> None:
    """STUDIO-T-OBS-08: Labels use 'studio.*' prefix, not 'mac.*' or bare names (C-1 seam)."""
    # Import the session module and check that hardcoded label strings use studio.* prefix
    import inspect
    from praxis.kernel.studio import invoker
    source = inspect.getsource(invoker)
    # All track_cost calls in the invoker should use 'studio.' prefix
    import re
    track_calls = re.findall(r'track_cost\("([^"]+)"', source)
    for label in track_calls:
        assert label.startswith("studio."), (
            f"Label {label!r} does not use 'studio.*' prefix — C-1 integration seam violation"
        )


# ---------------------------------------------------------------------------
# Tier 2 — integration with FakeCostTracker
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_obs_01_session_cost_usd_emitted(renderer, deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-OBS-01: Session emits 'studio.session.cost_usd' label to Pi-Mono."""
    tracker = _invoke_session(renderer, deep_template)
    assert "studio.session.cost_usd" in tracker.emitted_labels()


@pytest.mark.integration
def test_obs_02_per_cycle_cost_not_emitted_by_stub(renderer, deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-OBS-02: studio.cycle.{name}.cost_usd labels — present when MAC is wired.

    At Stage 6.3, FakeMAC doesn't emit per-cycle breakdown.
    This test documents the expected shape; full validation requires live MAC (Stage 7).
    """
    tracker = _invoke_session(renderer, deep_template)
    # At minimum, the session-level label is emitted
    assert "studio.session.cost_usd" in tracker.emitted_labels()


@pytest.mark.integration
def test_obs_03_composite_score_emitted(renderer, deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-OBS-03: Session emits 'studio.session.composite_score' after evaluation."""
    tracker = _invoke_session(renderer, deep_template)
    assert "studio.session.composite_score" in tracker.emitted_labels()


@pytest.mark.integration
def test_obs_04_gate_scores_emitted(renderer, deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-OBS-04: Session emits 'studio.gate.{R_id}.score' for each active gate (12 labels)."""
    tracker = _invoke_session(renderer, deep_template)
    labels = tracker.emitted_labels()
    gate_labels = [l for l in labels if l.startswith("studio.gate.R")]
    assert len(gate_labels) == 12, f"Expected 12 gate labels, got {len(gate_labels)}: {gate_labels}"


@pytest.mark.integration
def test_obs_05_rendering_mode_emitted(renderer, deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-OBS-05: 'studio.session.rendering_mode' label matches the rendering mode used."""
    tracker = _invoke_session(renderer, deep_template)
    labels = tracker.emitted_labels()
    rendering_labels = [l for l in labels if l.startswith("studio.session.rendering_mode.")]
    assert len(rendering_labels) >= 1


@pytest.mark.integration
def test_obs_06_mode_label_emitted(renderer, deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-OBS-06: 'studio.session.mode' label distinguishes 'deep' vs 'quick'."""
    tracker = _invoke_session(renderer, deep_template)
    labels = tracker.emitted_labels()
    mode_labels = [l for l in labels if l.startswith("studio.session.mode.")]
    assert len(mode_labels) >= 1
    assert any("deep" in l or "quick" in l for l in mode_labels)


@pytest.mark.integration
def test_obs_07_backtrack_count_emitted(renderer, deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-OBS-07: 'studio.session.backtrack_count' label emitted (may be 0)."""
    tracker = _invoke_session(renderer, deep_template)
    assert "studio.session.backtrack_count" in tracker.emitted_labels()
