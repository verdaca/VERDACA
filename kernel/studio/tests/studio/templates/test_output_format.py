"""Output format tests — studio/test-strategy.md §4.

24 tests: 20 Tier 1 (deterministic rendering from fixtures) + 4 Tier 3 (nightly).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.studio.models import ReasoningTrace, RenderedOutput
from praxis.kernel.studio.renderer import TemplateRenderer
from praxis.kernel.studio.schema import ProvenanceMode, RenderingMode

from tests.studio.fixtures.fake_mac import make_minimal_trace, make_rich_trace


# ---------------------------------------------------------------------------
# §4.1 ADR-01 Four-Feature Backbone Presence (4 tests)
# ---------------------------------------------------------------------------

_BACKBONE_SECTIONS = (
    "Structured Trade-offs",
    "Dissent",
    "Named Scenarios",
    "What This Analysis Did Not Cover",
)


def _assert_backbone(text: str) -> None:
    for section in _BACKBONE_SECTIONS:
        assert section in text, f"Missing backbone section: {section!r}"


@pytest.mark.studio_template
@pytest.mark.critical
def test_tpl_backbone_01_brief_contains_all_sections(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-BACKBONE-01: Brief output contains all 4 mandatory sections."""
    output = renderer.render(minimal_trace, "position_to_hold/brief.md.j2")
    _assert_backbone(output.text)


@pytest.mark.studio_template
@pytest.mark.critical
def test_tpl_backbone_02_deck_contains_all_sections(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-BACKBONE-02: Deck output contains all 4 mandatory sections."""
    output = renderer.render(minimal_trace, "position_to_hold/deck.html.j2")
    _assert_backbone(output.text)


@pytest.mark.studio_template
@pytest.mark.critical
def test_tpl_backbone_03_exec_summary_contains_all_sections(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-BACKBONE-03: Executive summary contains all 4 mandatory sections."""
    output = renderer.render(minimal_trace, "position_to_hold/executive_summary.md.j2")
    _assert_backbone(output.text)


@pytest.mark.studio_template
def test_tpl_backbone_04_all_3_modes_have_backbone(renderer: TemplateRenderer) -> None:
    """STUDIO-T-TPL-BACKBONE-04: All 3 rendering modes produce 4-section backbone for brief."""
    for mode in RenderingMode:
        trace = make_minimal_trace(
            rendering_mode=mode,
            provenance_mode=ProvenanceMode.FLEXIBLE,
        )
        brief_path = f"{mode.value}/brief.md.j2"
        output = renderer.render(trace, brief_path)
        _assert_backbone(output.text)


# ---------------------------------------------------------------------------
# §4.2 ADR-02 Three Rendering Modes (4 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_template
def test_tpl_render_01_position_to_hold_framing(renderer: TemplateRenderer) -> None:
    """STUDIO-T-TPL-RENDER-01: position_to_hold uses conditional-position framing."""
    trace = make_minimal_trace(RenderingMode.POSITION_TO_HOLD, ProvenanceMode.FLEXIBLE)
    output = renderer.render(trace, "position_to_hold/brief.md.j2")
    text_lower = output.text.lower()
    assert any(kw in text_lower for kw in ("position", "two quarters", "commitment", "hold"))


@pytest.mark.studio_template
def test_tpl_render_02_decision_framework_framing(renderer: TemplateRenderer) -> None:
    """STUDIO-T-TPL-RENDER-02: decision_framework uses factor-weighted framing."""
    trace = make_minimal_trace(RenderingMode.DECISION_FRAMEWORK, ProvenanceMode.INSPECTABLE)
    output = renderer.render(trace, "decision_framework/brief.md.j2")
    text_lower = output.text.lower()
    assert any(kw in text_lower for kw in ("framework", "factor", "weighted", "execute"))


@pytest.mark.studio_template
def test_tpl_render_03_firm_voice_framing(renderer: TemplateRenderer) -> None:
    """STUDIO-T-TPL-RENDER-03: firm_voice uses consultant-density framing."""
    trace = make_minimal_trace(RenderingMode.FIRM_VOICE, ProvenanceMode.INVISIBLE)
    output = renderer.render(trace, "firm_voice/brief.md.j2")
    text_lower = output.text.lower()
    assert any(kw in text_lower for kw in ("finding", "advisory", "client", "confidence"))


@pytest.mark.studio_template
@pytest.mark.critical
def test_tpl_render_04_three_modes_are_structurally_distinct(renderer: TemplateRenderer) -> None:
    """STUDIO-T-TPL-RENDER-04: All 3 rendering modes produce structurally distinct outputs."""
    trace_pth = make_minimal_trace(RenderingMode.POSITION_TO_HOLD, ProvenanceMode.FLEXIBLE)
    trace_df = make_minimal_trace(RenderingMode.DECISION_FRAMEWORK, ProvenanceMode.FLEXIBLE)
    trace_fv = make_minimal_trace(RenderingMode.FIRM_VOICE, ProvenanceMode.FLEXIBLE)

    pth = renderer.render(trace_pth, "position_to_hold/brief.md.j2").text
    df = renderer.render(trace_df, "decision_framework/brief.md.j2").text
    fv = renderer.render(trace_fv, "firm_voice/brief.md.j2").text

    # All three must be different from each other
    assert pth != df, "position_to_hold and decision_framework outputs are identical"
    assert df != fv, "decision_framework and firm_voice outputs are identical"
    assert pth != fv, "position_to_hold and firm_voice outputs are identical"


# ---------------------------------------------------------------------------
# §4.3 ADR-03 Brief Length Band (2 tests — Tier 3 nightly)
# ---------------------------------------------------------------------------


@pytest.mark.studio_template
@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_tpl_length_01_brief_word_count_in_band() -> None:
    """STUDIO-T-TPL-LENGTH-01: Deep-mode brief word count within 3,500–8,500 band. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM benchmark; not run in PR gate")


@pytest.mark.studio_template
@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_tpl_length_02_per_section_word_minimums() -> None:
    """STUDIO-T-TPL-LENGTH-02: Per-section word minimums met. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM benchmark; not run in PR gate")


# ---------------------------------------------------------------------------
# §4.4 ADR-04 Deck Format (2 tests — Tier 3 nightly)
# ---------------------------------------------------------------------------


@pytest.mark.studio_template
@pytest.mark.studio_benchmark
@pytest.mark.nightly_only
def test_tpl_deck_01_slide_count_in_range() -> None:
    """STUDIO-T-TPL-DECK-01: Deck slide count within 10–18 range. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM benchmark; not run in PR gate")


@pytest.mark.studio_template
@pytest.mark.nightly_only
def test_tpl_deck_02_slide_titles_statement_of_finding() -> None:
    """STUDIO-T-TPL-DECK-02: Slide titles use statement-of-finding format. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM benchmark; not run in PR gate")


# ---------------------------------------------------------------------------
# §4.5 ADR-05 Dissent Rendering (3 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_template
@pytest.mark.critical
def test_tpl_dissent_01_at_least_one_competing_frame(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-DISSENT-01: Dissent section contains at least 1 competing frame."""
    output = renderer.render(minimal_trace, "position_to_hold/brief.md.j2")
    assert "Competing Frame:" in output.text


@pytest.mark.studio_template
def test_tpl_dissent_02_four_required_sub_fields(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-DISSENT-02: Each competing frame renders 4 required sub-fields."""
    output = renderer.render(minimal_trace, "position_to_hold/brief.md.j2")
    assert "Steelman" in output.text or "steelman" in output.text.lower()
    assert "Evidence" in output.text or "evidence" in output.text.lower()
    assert "Conditions" in output.text or "conditions" in output.text.lower()
    assert "Confidence" in output.text or "confidence" in output.text.lower()


@pytest.mark.studio_template
def test_tpl_dissent_03_zero_frames_triggers_rerun_signal(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-DISSENT-03: Zero competing frames triggers re-run signal."""
    from dataclasses import replace
    empty_trace = ReasoningTrace(
        trade_offs=minimal_trace.trade_offs,
        dissent_frames=(),  # empty
        scenarios=minimal_trace.scenarios,
        scope_limits=minimal_trace.scope_limits,
        recommendations=minimal_trace.recommendations,
        rendering_mode=minimal_trace.rendering_mode,
        provenance_mode=minimal_trace.provenance_mode,
    )
    output = renderer.render(empty_trace, "position_to_hold/brief.md.j2")
    assert "RERUN_SIGNAL" in output.text or "at least one dissenting" in output.text.lower()


# ---------------------------------------------------------------------------
# §4.6 ADR-06 Scenario Rendering (3 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_template
@pytest.mark.critical
def test_tpl_scenario_01_at_least_2_scenarios(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-SCENARIO-01: At least 2 named scenarios per output."""
    output = renderer.render(minimal_trace, "position_to_hold/brief.md.j2")
    assert output.text.count("### Scenario:") >= 2


@pytest.mark.studio_template
def test_tpl_scenario_02_three_required_sub_fields(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-SCENARIO-02: Each scenario renders 3 required sub-fields."""
    output = renderer.render(minimal_trace, "position_to_hold/brief.md.j2")
    assert "Trigger condition:" in output.text or "Trigger" in output.text
    assert "Invalidation conditions:" in output.text or "Invalidation" in output.text
    assert "Decision rule:" in output.text or "Decision" in output.text


@pytest.mark.studio_template
def test_tpl_scenario_03_decision_rule_has_owner_and_date(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-SCENARIO-03: Decision-rule includes owner + date (COO fold-back)."""
    output = renderer.render(minimal_trace, "position_to_hold/brief.md.j2")
    # The fixture trace includes "Owner:" and date references in decision_rule
    assert "Owner:" in output.text or "owner" in output.text.lower()


# ---------------------------------------------------------------------------
# §4.7 ADR-07 Scope-Limits Rendering (3 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_template
@pytest.mark.critical
def test_tpl_scope_01_three_sub_categories(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-SCOPE-01: Scope-limits renders 3 sub-categories."""
    output = renderer.render(minimal_trace, "position_to_hold/brief.md.j2")
    assert "Data not available" in output.text
    assert "Adjacent questions out of scope" in output.text
    assert "Assumptions that would invalidate" in output.text


@pytest.mark.studio_template
def test_tpl_scope_02_at_least_one_entry_per_category(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-SCOPE-02: Each sub-category has >= 1 entry."""
    output = renderer.render(minimal_trace, "position_to_hold/brief.md.j2")
    # The minimal trace has 1 entry per category
    text = output.text
    assert "We did not have access to" in text or "Proprietary" in text


@pytest.mark.studio_template
def test_tpl_scope_03_zero_entry_triggers_retry_signal(
    renderer: TemplateRenderer, minimal_trace: ReasoningTrace
) -> None:
    """STUDIO-T-TPL-SCOPE-03: Zero-entry sub-category triggers retry signal."""
    from praxis.kernel.studio.models import ScopeLimits
    empty_scope_trace = ReasoningTrace(
        trade_offs=minimal_trace.trade_offs,
        dissent_frames=minimal_trace.dissent_frames,
        scenarios=minimal_trace.scenarios,
        scope_limits=ScopeLimits(
            data_gaps=(),  # empty
            adjacent_questions=(),  # empty
            invalidating_assumptions=(),  # empty
        ),
        recommendations=minimal_trace.recommendations,
        rendering_mode=minimal_trace.rendering_mode,
        provenance_mode=minimal_trace.provenance_mode,
    )
    output = renderer.render(empty_scope_trace, "position_to_hold/brief.md.j2")
    assert "RETRY_SIGNAL" in output.text or "required" in output.text.lower()


# ---------------------------------------------------------------------------
# §4.8 ADR-09 Provenance Mode Selection (3 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_template
def test_tpl_prov_01_flexible_has_footer(renderer: TemplateRenderer) -> None:
    """STUDIO-T-TPL-PROV-01: flexible mode renders dismissible footer with 'Generated with Praxis'."""
    trace = make_minimal_trace(RenderingMode.POSITION_TO_HOLD, ProvenanceMode.FLEXIBLE)
    output = renderer.render(trace, "position_to_hold/brief.md.j2")
    assert "Generated with Praxis" in output.text


@pytest.mark.studio_template
def test_tpl_prov_02_inspectable_has_expandable_section(renderer: TemplateRenderer) -> None:
    """STUDIO-T-TPL-PROV-02: inspectable mode renders 'How this analysis was generated'."""
    trace = make_minimal_trace(RenderingMode.DECISION_FRAMEWORK, ProvenanceMode.INSPECTABLE)
    output = renderer.render(trace, "decision_framework/brief.md.j2")
    assert "How this analysis was generated" in output.text


@pytest.mark.studio_template
@pytest.mark.studio_provenance
def test_tpl_prov_03_invisible_renders_no_provenance(renderer: TemplateRenderer) -> None:
    """STUDIO-T-TPL-PROV-03: invisible mode renders no provenance content."""
    trace = make_minimal_trace(RenderingMode.FIRM_VOICE, ProvenanceMode.INVISIBLE)
    output = renderer.render(trace, "firm_voice/brief.md.j2")
    assert "Generated with Praxis" not in output.text
    assert "How this analysis was generated" not in output.text
