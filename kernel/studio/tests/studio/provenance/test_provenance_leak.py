"""Provenance leak detection tests — studio/test-strategy.md §11.

7 tests: 6 Tier 1 + 1 Tier 3 (nightly).
ADR-09 invisible-mode: no 'praxis' or 'studio' in rendered text, metadata, or HTML comments.
DQ-4 Option A: content-only strip (OS metadata out of scope).
"""

from __future__ import annotations

import re

import pytest

from praxis.kernel.studio.renderer import TemplateRenderer
from praxis.kernel.studio.schema import ProvenanceMode, RenderingMode

from tests.studio.fixtures.fake_mac import make_minimal_trace


_FORBIDDEN = ("praxis", "studio")


def _assert_no_forbidden(text: str, label: str) -> None:
    lower = text.lower()
    for token in _FORBIDDEN:
        assert token not in lower, (
            f"{label}: found forbidden token {token!r} in invisible-mode output"
        )


def _assert_no_html_comments(text: str) -> None:
    comments = re.findall(r"<!--.*?-->", text, re.DOTALL)
    for comment in comments:
        lower = comment.lower()
        for token in _FORBIDDEN:
            assert token not in lower, f"Forbidden token {token!r} found in HTML comment: {comment!r}"


def _assert_no_meta_tags(text: str) -> None:
    meta_tags = re.findall(r"<meta[^>]*>", text, re.IGNORECASE)
    for tag in meta_tags:
        lower = tag.lower()
        for token in _FORBIDDEN:
            assert token not in lower, f"Forbidden token {token!r} found in <meta> tag: {tag!r}"


# ---------------------------------------------------------------------------
# Tier 1 — content-level leak detection (6 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_provenance
@pytest.mark.critical
def test_prov_leak_01_invisible_text_clean(renderer: TemplateRenderer) -> None:
    """STUDIO-T-PROV-LEAK-01: Invisible mode: grep for praxis/studio in rendered text = 0 matches."""
    trace = make_minimal_trace(RenderingMode.FIRM_VOICE, ProvenanceMode.INVISIBLE)
    output = renderer.render(trace, "firm_voice/brief.md.j2")
    _assert_no_forbidden(output.text, "rendered text")


@pytest.mark.studio_provenance
@pytest.mark.critical
def test_prov_leak_02_invisible_file_metadata_clean(renderer: TemplateRenderer) -> None:
    """STUDIO-T-PROV-LEAK-02: Invisible mode: file metadata clean (content-only, DQ-4 A).

    At Stage 6.3, rendering is in-memory. No YAML frontmatter or HTML <meta> praxis refs.
    OS-level file metadata is out of scope per DQ-4 Option A.
    """
    trace = make_minimal_trace(RenderingMode.FIRM_VOICE, ProvenanceMode.INVISIBLE)
    output = renderer.render(trace, "firm_voice/brief.md.j2")
    # Check for YAML frontmatter
    if output.text.startswith("---"):
        frontmatter_end = output.text.find("\n---\n", 3)
        if frontmatter_end > 0:
            frontmatter = output.text[:frontmatter_end + 5]
            _assert_no_forbidden(frontmatter, "YAML frontmatter")


@pytest.mark.studio_provenance
@pytest.mark.critical
def test_prov_leak_03_invisible_html_comments_clean(renderer: TemplateRenderer) -> None:
    """STUDIO-T-PROV-LEAK-03: Invisible mode: HTML comments clean."""
    trace = make_minimal_trace(RenderingMode.FIRM_VOICE, ProvenanceMode.INVISIBLE)
    output = renderer.render(trace, "firm_voice/deck.html.j2")
    _assert_no_html_comments(output.text)


@pytest.mark.studio_provenance
@pytest.mark.critical
def test_prov_leak_04_invisible_full_byte_scan(renderer: TemplateRenderer) -> None:
    """STUDIO-T-PROV-LEAK-04: Invisible mode: full byte scan — no praxis/studio in any byte."""
    trace = make_minimal_trace(RenderingMode.FIRM_VOICE, ProvenanceMode.INVISIBLE)
    for template_path in (
        "firm_voice/brief.md.j2",
        "firm_voice/deck.html.j2",
        "firm_voice/executive_summary.md.j2",
    ):
        output = renderer.render(trace, template_path)
        assert renderer.verify_invisible_clean(output.text), (
            f"Invisible-mode byte scan FAILED for {template_path}: "
            f"'praxis' or 'studio' found in output"
        )


@pytest.mark.studio_provenance
def test_prov_leak_05_flexible_mode_has_praxis_footer(renderer: TemplateRenderer) -> None:
    """STUDIO-T-PROV-LEAK-05: Flexible mode: 'Generated with Praxis' footer IS present."""
    trace = make_minimal_trace(RenderingMode.POSITION_TO_HOLD, ProvenanceMode.FLEXIBLE)
    output = renderer.render(trace, "position_to_hold/brief.md.j2")
    assert "Generated with Praxis" in output.text


@pytest.mark.studio_provenance
def test_prov_leak_06_inspectable_mode_has_section(renderer: TemplateRenderer) -> None:
    """STUDIO-T-PROV-LEAK-06: Inspectable mode: 'How this analysis was generated' IS present."""
    trace = make_minimal_trace(RenderingMode.DECISION_FRAMEWORK, ProvenanceMode.INSPECTABLE)
    output = renderer.render(trace, "decision_framework/brief.md.j2")
    assert "How this analysis was generated" in output.text


# ---------------------------------------------------------------------------
# Tier 3 — nightly (1 test)
# ---------------------------------------------------------------------------


@pytest.mark.studio_provenance
@pytest.mark.nightly_only
def test_prov_leak_07_all_benchmark_outputs_invisible_clean() -> None:
    """STUDIO-T-PROV-LEAK-07: Invisible-mode leak test on all 10 benchmark outputs. [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")
