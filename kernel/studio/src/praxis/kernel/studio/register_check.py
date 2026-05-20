"""Register-check utility — ADR-11 muted operator-realism enforcement.

The register contract (Mary §A.1) requires that all Studio customer-facing
copy use a wry, specific, hedged, risk-aware register — uninterested in
performing, no founder-Twitter caricature, no dramatic-stakes language.

``RegisterChecker`` detects four categories of drift markers in rendered text.
The curated drift marker list satisfies OQ-TS-S3 (Amelia 6.3 initial list;
Quinn 6.4 validates against nightly outputs).

Binding anchors:
  - studio/architecture.md §4.10 ADR-11 Register Contract
  - studio/test-strategy.md §10 Register-Check Tests
  - studio/register_guide.md (Mary §A.1 register note verbatim)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class ViolationCategory(str, Enum):
    EXCLAMATION = "exclamation_mark"
    DRAMATIC_VERB = "dramatic_stakes_verb"
    URGENCY_ADVERB = "urgency_performing_adverb"
    CONDESCENDING = "condescending_pattern"


@dataclass(frozen=True)
class RegisterViolation:
    """One detected register-drift instance."""

    category: ViolationCategory
    matched_text: str
    context: str
    """Up to 80 characters of surrounding context for diagnosis."""


# ---------------------------------------------------------------------------
# Drift marker catalogs (OQ-TS-S3 initial list — Quinn 6.4 validates)
# ---------------------------------------------------------------------------

# Exclamation marks in analytical text — any "!" not in a URL path (preceded by /)
_EXCLAMATION_PATTERN = re.compile(r"(?<![/])!")

# Dramatic-stakes verbs — founder-Twitter caricature vocabulary
_DRAMATIC_VERBS: frozenset[str] = frozenset(
    {
        "revolutionize",
        "disrupt",
        "transform",
        "unprecedented",
        "game-changing",
        "game changer",
        "paradigm shift",
        "breakthrough",
        "explosive",
        "skyrocket",
        "rocket",
        "dominate",
        "crush",
        "obliterate",
        "destroy",
        "massive",
        "enormous",
        "incredible",
        "amazing",
        "phenomenal",
        "spectacular",
        "unstoppable",
    }
)
_DRAMATIC_VERB_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(v) for v in _DRAMATIC_VERBS) + r")\b",
    re.IGNORECASE,
)

# Urgency-performing adverbs — urgency in non-risk contexts
# "critical" is flagged unless it appears immediately after "risk", "failure", "error", "issue"
_URGENCY_ADVERBS: frozenset[str] = frozenset(
    {"urgently", "immediately", "asap", "right away", "as soon as possible"}
)
_URGENCY_ADVERB_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(a) for a in _URGENCY_ADVERBS) + r")\b",
    re.IGNORECASE,
)
# "critical" only flags when NOT preceded by a risk-domain word
_CRITICAL_PATTERN = re.compile(r"\bcritical\b", re.IGNORECASE)
_RISK_DOMAIN_BEFORE = re.compile(
    r"\b(risk|failure|error|issue|concern|vulnerability|defect)\b\s+\w+\s*$",
    re.IGNORECASE,
)

# Condescending patterns — talking down to the reader
_CONDESCENDING: frozenset[str] = frozenset(
    {
        "obviously",
        "clearly you",
        "as anyone knows",
        "it goes without saying",
        "needless to say",
        "of course you",
        "simply put",
        "just do",
        "just implement",
        "just use",
    }
)
_CONDESCENDING_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in _CONDESCENDING) + r")\b",
    re.IGNORECASE,
)

_CONTEXT_WINDOW = 40  # chars on each side of the match


def _extract_context(text: str, match: re.Match[str]) -> str:
    start = max(0, match.start() - _CONTEXT_WINDOW)
    end = min(len(text), match.end() + _CONTEXT_WINDOW)
    return text[start:end].replace("\n", " ")


class RegisterChecker:
    """ADR-11 register-drift detector.

    Usage::

        checker = RegisterChecker()
        violations = checker.check(rendered_text)
        if violations:
            # handle drift
    """

    def check(self, text: str) -> tuple[RegisterViolation, ...]:
        """Scan ``text`` for all register-drift markers.

        Returns a tuple of :class:`RegisterViolation` instances. Empty tuple
        means PASS.
        """
        violations: list[RegisterViolation] = []
        violations.extend(self._check_exclamations(text))
        violations.extend(self._check_dramatic_verbs(text))
        violations.extend(self._check_urgency_adverbs(text))
        violations.extend(self._check_condescending(text))
        return tuple(violations)

    def is_compliant(self, text: str) -> bool:
        """Return True if no drift markers are found."""
        return len(self.check(text)) == 0

    # ------------------------------------------------------------------
    # Per-category checks
    # ------------------------------------------------------------------

    def _check_exclamations(self, text: str) -> list[RegisterViolation]:
        results: list[RegisterViolation] = []
        for m in _EXCLAMATION_PATTERN.finditer(text):
            results.append(
                RegisterViolation(
                    category=ViolationCategory.EXCLAMATION,
                    matched_text="!",
                    context=_extract_context(text, m),
                )
            )
        return results

    def _check_dramatic_verbs(self, text: str) -> list[RegisterViolation]:
        results: list[RegisterViolation] = []
        for m in _DRAMATIC_VERB_PATTERN.finditer(text):
            results.append(
                RegisterViolation(
                    category=ViolationCategory.DRAMATIC_VERB,
                    matched_text=m.group(),
                    context=_extract_context(text, m),
                )
            )
        return results

    def _check_urgency_adverbs(self, text: str) -> list[RegisterViolation]:
        results: list[RegisterViolation] = []
        for m in _URGENCY_ADVERB_PATTERN.finditer(text):
            results.append(
                RegisterViolation(
                    category=ViolationCategory.URGENCY_ADVERB,
                    matched_text=m.group(),
                    context=_extract_context(text, m),
                )
            )
        # Check "critical" in non-risk context
        for m in _CRITICAL_PATTERN.finditer(text):
            preceding = text[max(0, m.start() - 60) : m.start()]
            if not _RISK_DOMAIN_BEFORE.search(preceding):
                results.append(
                    RegisterViolation(
                        category=ViolationCategory.URGENCY_ADVERB,
                        matched_text=m.group(),
                        context=_extract_context(text, m),
                    )
                )
        return results

    def _check_condescending(self, text: str) -> list[RegisterViolation]:
        results: list[RegisterViolation] = []
        for m in _CONDESCENDING_PATTERN.finditer(text):
            results.append(
                RegisterViolation(
                    category=ViolationCategory.CONDESCENDING,
                    matched_text=m.group(),
                    context=_extract_context(text, m),
                )
            )
        return results


__all__: tuple[str, ...] = (
    "RegisterChecker",
    "RegisterViolation",
    "ViolationCategory",
)
