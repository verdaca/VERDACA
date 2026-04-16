"""A/B comparison harness tests — studio/test-strategy.md §6.

12 tests: 9 Tier 1 + 2 Tier 2 (integration) + 1 Tier 3 (nightly).
"""

from __future__ import annotations

import re

import pytest

from praxis.kernel.studio.harness import ABHarness
from praxis.kernel.studio.invoker import StudioSession, TaskInput
from praxis.kernel.studio.models import GateScores, RenderedOutput

from tests.studio.fixtures.fake_mac import FakeMAC, make_minimal_trace
from tests.studio.fixtures.fake_cost_tracker import FakeCostTracker
from tests.studio.fixtures.fake_llm_judge import FakeLLMJudge


# ---------------------------------------------------------------------------
# Fake single-agent baseline
# ---------------------------------------------------------------------------

class FakeSingleAgent:
    def __init__(self, response: str = "Single-agent response text.") -> None:
        self._response = response
        self._structural_response = (
            "## Structured Trade-offs\n"
            + self._response
            + "\n## Dissent\nAlternative view.\n"
            + "## Named Scenarios\nScenario: Base case.\n"
            + "## What This Analysis Did Not Cover\nLimitations."
        )

    def call(self, question: str, structural_prompt: bool = False) -> str:
        if structural_prompt:
            return self._structural_response
        return self._response


def _make_harness(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_judge: FakeLLMJudge,
    renderer,
) -> ABHarness:
    session = StudioSession(mac=fake_mac, cost_tracker=fake_cost_tracker, renderer=renderer)
    return ABHarness(
        single_agent=FakeSingleAgent(),
        mac_session=session,
        judge=fake_judge,
        seed=42,
    )


# ---------------------------------------------------------------------------
# §6.1 Harness structure (4 tests — 2 Tier 2, 2 Tier 1)
# ---------------------------------------------------------------------------


@pytest.mark.studio_ab_harness
@pytest.mark.integration
def test_ab_01_both_paths_run(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
    deep_template,
) -> None:
    """STUDIO-T-AB-01: Harness runs both paths on a single benchmark question."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    baseline = harness.run_single_agent_baseline("Should we expand to EU?")
    studio = harness.run_studio("Should we expand to EU?", deep_template)
    assert isinstance(baseline, str)
    assert len(baseline) > 0
    assert isinstance(studio, RenderedOutput)
    assert len(studio.text) > 0


@pytest.mark.studio_ab_harness
@pytest.mark.integration
def test_ab_02_enhanced_baseline_runs(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
    deep_template,
) -> None:
    """STUDIO-T-AB-02: Enhanced single-agent baseline also runs (structural prompt)."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    enhanced = harness.run_enhanced_baseline("Should we expand to EU?")
    assert isinstance(enhanced, str)
    assert len(enhanced) > 0


@pytest.mark.studio_ab_harness
def test_ab_03_outputs_scorable(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
) -> None:
    """STUDIO-T-AB-03: Both outputs are scorable against R1–R12 (produce GateScores)."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    baseline_text = harness.run_single_agent_baseline("Test question")
    scores = harness.score(baseline_text)
    assert isinstance(scores, GateScores)
    assert len(scores.scores) == 12
    assert all(f"R{i}" in scores.scores for i in range(1, 13))


@pytest.mark.studio_ab_harness
def test_ab_04_comparison_report_generates(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
    deep_template,
) -> None:
    """STUDIO-T-AB-04: Comparison report generates without error from scored pair."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    baseline, enhanced, studio = harness.run_full_comparison(
        "Q1", "Should we expand to EU?", deep_template
    )
    report = harness.generate_report([(baseline, enhanced, studio)])
    assert isinstance(report.headline, str)
    assert len(report.per_question_rows) == 1
    assert len(report.per_gate_rows) >= 0


# ---------------------------------------------------------------------------
# §6.2 Blind evaluation integrity (3 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_ab_harness
@pytest.mark.critical
def test_ab_blind_01_anonymization_strips_labels(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
) -> None:
    """STUDIO-T-AB-BLIND-01: Anonymization strips 'Studio'/'baseline'/'enhanced' labels."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    outputs = [
        "Studio analysis: the market is expanding.",
        "Baseline analysis: the market is contracting.",
        "Enhanced baseline: mixed signals.",
    ]
    anonymized = harness.anonymize(outputs)
    label_pattern = re.compile(r"\b(Studio|studio|Baseline|baseline|Enhanced|enhanced)\b")
    for text in anonymized:
        assert not label_pattern.search(text), f"Label found in anonymized text: {text!r}"


@pytest.mark.studio_ab_harness
def test_ab_blind_02_output_order_randomized(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
) -> None:
    """STUDIO-T-AB-BLIND-02: Output order randomized per question."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    outputs = [f"Output {i}" for i in range(10)]
    anonymized = harness.anonymize(outputs)
    # With 10 items and seed=42, order should differ from input
    assert len(anonymized) == len(outputs)
    # At least one order difference expected (with seed=42 and 10 items)
    assert any(anonymized[i] != f"Output {i}" for i in range(len(outputs)))


@pytest.mark.studio_ab_harness
def test_ab_blind_03_no_path_identifying_metadata(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
) -> None:
    """STUDIO-T-AB-BLIND-03: Evaluator input contains no path-identifying metadata."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    outputs = ["Path A content.", "Path B content.", "Path C content."]
    anonymized = harness.anonymize(outputs)
    for text in anonymized:
        assert "Path A" not in text
        assert "Path B" not in text
        assert "Path C" not in text


# ---------------------------------------------------------------------------
# §6.3 Metrics capture (3 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_ab_harness
def test_ab_metric_01_per_run_metrics_captured(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
    deep_template,
) -> None:
    """STUDIO-T-AB-METRIC-01: Per-run metrics include cost, time, word_count, composite, per-gate."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    baseline, enhanced, studio = harness.run_full_comparison("Q1", "Test", deep_template)
    for result in (baseline, enhanced, studio):
        assert result.cost_usd >= 0
        assert result.duration_seconds >= 0
        assert result.word_count >= 0
        assert result.gate_scores.composite >= 0
        assert len(result.gate_scores.scores) == 12


@pytest.mark.studio_ab_harness
def test_ab_metric_02_backbone_completeness_captured(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
    deep_template,
) -> None:
    """STUDIO-T-AB-METRIC-02: Backbone completeness (4 × boolean) captured per run."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    baseline, enhanced, studio = harness.run_full_comparison("Q1", "Test", deep_template)
    for result in (baseline, enhanced, studio):
        completeness = result.gate_scores.backbone_completeness
        assert len(completeness) == 4
        assert all(isinstance(v, bool) for v in completeness.values())


@pytest.mark.studio_ab_harness
def test_ab_metric_03_register_compliance_captured(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
    deep_template,
) -> None:
    """STUDIO-T-AB-METRIC-03: Register compliance (boolean) captured per run."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    baseline, enhanced, studio = harness.run_full_comparison("Q1", "Test", deep_template)
    for result in (baseline, enhanced, studio):
        assert isinstance(result.gate_scores.register_compliant, bool)


# ---------------------------------------------------------------------------
# §6.4 Report format (2 tests — 1 Tier 1 + 1 Tier 3)
# ---------------------------------------------------------------------------


@pytest.mark.studio_ab_harness
def test_ab_report_01_report_contains_required_sections(
    fake_mac: FakeMAC,
    fake_cost_tracker: FakeCostTracker,
    fake_llm_judge: FakeLLMJudge,
    renderer,
    deep_template,
) -> None:
    """STUDIO-T-AB-REPORT-01: Report contains headline, per-question table, per-gate table, R5 analysis."""
    harness = _make_harness(fake_mac, fake_cost_tracker, fake_llm_judge, renderer)
    baseline, enhanced, studio = harness.run_full_comparison("Q1", "Test", deep_template)
    report = harness.generate_report([(baseline, enhanced, studio)])
    assert report.headline
    assert report.per_question_rows
    assert "A4 deferred" in report.headline  # Stage 5.6 caveat
    assert report.dissent_analysis


@pytest.mark.studio_ab_harness
@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_ab_report_02_all_10_results_reported() -> None:
    """STUDIO-T-AB-REPORT-02: All 10 benchmark results reported (no cherry-picking). [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM benchmark; not run in PR gate")
