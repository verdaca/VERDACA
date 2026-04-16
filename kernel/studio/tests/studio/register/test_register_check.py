"""Register-check tests — studio/test-strategy.md §10.

6 tests: 5 Tier 1 + 1 Tier 3 (nightly).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.studio.register_check import RegisterChecker, ViolationCategory


_CORPUS_DIR = Path(__file__).parent.parent / "fixtures" / "register_corpus"


@pytest.fixture(scope="module")
def checker() -> RegisterChecker:
    return RegisterChecker()


# ---------------------------------------------------------------------------
# Tier 1 — register drift detection (5 tests)
# ---------------------------------------------------------------------------


@pytest.mark.studio_register
def test_reg_01_detects_exclamation_marks(checker: RegisterChecker) -> None:
    """STUDIO-T-REG-01: Register-check detects exclamation marks in analytical text."""
    text = (_CORPUS_DIR / "bad_exclamation_marks.md").read_text(encoding="utf-8")
    violations = checker.check(text)
    exclamation_violations = [v for v in violations if v.category == ViolationCategory.EXCLAMATION]
    assert len(exclamation_violations) > 0, "Expected exclamation mark violations"


@pytest.mark.studio_register
def test_reg_02_detects_dramatic_verbs(checker: RegisterChecker) -> None:
    """STUDIO-T-REG-02: Register-check detects dramatic-stakes verbs."""
    text = (_CORPUS_DIR / "bad_dramatic_verbs.md").read_text(encoding="utf-8")
    violations = checker.check(text)
    dramatic_violations = [v for v in violations if v.category == ViolationCategory.DRAMATIC_VERB]
    assert len(dramatic_violations) > 0, "Expected dramatic verb violations"


@pytest.mark.studio_register
def test_reg_03_detects_urgency_adverbs(checker: RegisterChecker) -> None:
    """STUDIO-T-REG-03: Register-check detects urgency-performing adverbs."""
    text = (_CORPUS_DIR / "bad_urgency_adverbs.md").read_text(encoding="utf-8")
    violations = checker.check(text)
    urgency_violations = [v for v in violations if v.category == ViolationCategory.URGENCY_ADVERB]
    assert len(urgency_violations) > 0, "Expected urgency adverb violations"


@pytest.mark.studio_register
def test_reg_04_detects_condescending_patterns(checker: RegisterChecker) -> None:
    """STUDIO-T-REG-04: Register-check detects condescending patterns."""
    condescending_text = "Obviously the right answer is to expand immediately."
    violations = checker.check(condescending_text)
    cond_violations = [v for v in violations if v.category == ViolationCategory.CONDESCENDING]
    assert len(cond_violations) > 0, "Expected condescending pattern violation for 'obviously'"


@pytest.mark.studio_register
@pytest.mark.critical
def test_reg_05_passes_on_muted_register(checker: RegisterChecker) -> None:
    """STUDIO-T-REG-05: Register-check PASSES on known-good muted register fixture."""
    text = (_CORPUS_DIR / "good_muted_register.md").read_text(encoding="utf-8")
    violations = checker.check(text)
    assert len(violations) == 0, (
        f"Expected no violations in muted register fixture, got: "
        f"{[v.matched_text for v in violations]}"
    )


# ---------------------------------------------------------------------------
# Tier 3 — nightly benchmark outputs
# ---------------------------------------------------------------------------


@pytest.mark.studio_register
@pytest.mark.nightly_only
def test_reg_06_all_benchmark_outputs_pass_register() -> None:
    """STUDIO-T-REG-06: Register-check passes on all 10 benchmark outputs (nightly). [NIGHTLY]"""
    pytest.skip("Tier 3 — nightly live LLM; not run in PR gate")
