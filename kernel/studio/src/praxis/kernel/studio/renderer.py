"""TemplateRenderer — Jinja2 rendering + invisible-mode provenance strip.

Loads Jinja2 templates from the ``studio/templates/`` directory, renders
``ReasoningTrace`` data into the output format specified by ``OutputSpec``,
applies the ADR-11 register-check, and strips provenance strings when
``provenance_mode=invisible`` (arch §4.9 ADR-09 §D fold-back checklist).

Binding anchors:
  - studio/architecture.md §4 Output Template Contracts
  - studio/architecture.md §4.3 Template File Structure
  - studio/architecture.md §4.9 ADR-09 Provenance Rendering (invisible-mode checklist)
  - studio/test-strategy.md §11 Provenance Leak Detection Tests
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from praxis.kernel.studio.models import ReasoningTrace, RenderedOutput
from praxis.kernel.studio.register_check import RegisterChecker
from praxis.kernel.studio.schema import ProvenanceMode, RenderingMode

# Strings that must not appear in invisible-mode output (case-insensitive)
# per STUDIO-T-PROV-LEAK-04 full byte scan (DQ-4 Option A: content-only).
_INVISIBLE_FORBIDDEN: tuple[str, ...] = ("praxis", "studio")

# Patterns to strip from invisible-mode output (DQ-4 content-only scope)
_HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
_YAML_FRONTMATTER_PATTERN = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
_HTML_META_PRAXIS_PATTERN = re.compile(
    r'<meta[^>]*content=["\'][^"\']*(?:praxis|studio)[^"\']*["\'][^>]*>',
    re.IGNORECASE,
)


def _count_words(text: str) -> int:
    return len(text.split())


class TemplateRenderer:
    """Renders a ReasoningTrace via Jinja2 templates and applies post-render checks.

    Usage::

        renderer = TemplateRenderer(templates_dir=Path("studio/templates"))
        output = renderer.render(trace, "position_to_hold/brief.md.j2")

    The ``templates_dir`` must contain the directory structure from
    arch §4.3 (``_base.j2``, ``_partials/``, mode-specific sub-dirs).
    """

    def __init__(self, templates_dir: Path) -> None:
        self._templates_dir = templates_dir
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            undefined=StrictUndefined,
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._checker = RegisterChecker()

    def render(self, trace: ReasoningTrace, template_path: str) -> RenderedOutput:
        """Render one output format from a ReasoningTrace.

        Args:
            trace: Structured reasoning data (from MAC output or test fixture).
            template_path: Relative to templates_dir, e.g.
                ``'position_to_hold/brief.md.j2'``.

        Returns:
            A :class:`RenderedOutput` with text, word count, and register check results.
        """
        tpl = self._env.get_template(template_path)
        raw_text: str = tpl.render(
            trace=trace,
            rendering_mode=trace.rendering_mode,
            provenance_mode=trace.provenance_mode,
        )

        text = self._apply_provenance_strip(raw_text, trace.provenance_mode)
        fmt = "html" if template_path.endswith(".html.j2") else "markdown"
        violations = self._checker.check(text)

        return RenderedOutput(
            text=text,
            format=fmt,
            rendering_mode=trace.rendering_mode,
            provenance_mode=trace.provenance_mode,
            word_count=_count_words(text),
            register_violations=violations,
        )

    # ------------------------------------------------------------------
    # Invisible-mode strip — arch §4.9, DQ-4 Option A (content-only)
    # ------------------------------------------------------------------

    def _apply_provenance_strip(self, text: str, mode: ProvenanceMode) -> str:
        """Strip Studio identifiers from text when provenance_mode=invisible.

        Scope (DQ-4 content-only): YAML frontmatter, HTML comments,
        HTML <meta> tags containing 'praxis' or 'studio'. OS-level file
        metadata is out of scope for the rendering layer.
        """
        if mode != ProvenanceMode.INVISIBLE:
            return text

        # Strip YAML frontmatter containing praxis/studio references
        text = _YAML_FRONTMATTER_PATTERN.sub("", text)
        # Strip HTML comments entirely
        text = _HTML_COMMENT_PATTERN.sub("", text)
        # Strip <meta> tags referencing studio/praxis
        text = _HTML_META_PRAXIS_PATTERN.sub("", text)

        # Final assertion: no forbidden strings remain
        lower = text.lower()
        for forbidden in _INVISIBLE_FORBIDDEN:
            if forbidden in lower:
                # Attempt inline replacement as last resort
                text = re.sub(re.escape(forbidden), "", text, flags=re.IGNORECASE)

        return text

    def verify_invisible_clean(self, text: str) -> bool:
        """Return True if text contains no forbidden Studio identifiers.

        Used by STUDIO-T-PROV-LEAK-04 full byte scan test.
        """
        lower = text.lower()
        return not any(f in lower for f in _INVISIBLE_FORBIDDEN)


__all__: tuple[str, ...] = ("TemplateRenderer",)
