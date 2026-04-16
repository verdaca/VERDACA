"""A4 Andrey-in-the-loop Spearman release-gate test.

Covers MAC-T-BENCH-A4-01..02. Both are ``release_gate``; they run
ONLY on release-candidate tag pushes via ``--run-release``. Manual
scoring step is out-of-band per benchmark §3 ADR-3; this test verifies
only the Spearman math against the pre-scored fixture.

Anchors:
  - mac/architecture.md §9.6 ADR-3 A4 Validation
  - mac/benchmark-questions.md §3 ADR-3 Option B
  - mac/test-strategy.md v0.3 §7.10
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.mac.eval.validation import (
    SPEARMAN_RELEASE_GATE_THRESHOLD,
    run_a4_validation,
)


_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "mac"
    / "benchmark"
    / "fixtures"
    / "andrey_scores_rc1.yaml"
)


def _parse_yaml_fixture(text: str) -> tuple[dict[str, float], dict[str, float], float]:
    """Minimal hand-parser for the andrey_scores fixture (no PyYAML dep)."""
    automated: dict[str, float] = {}
    human: dict[str, float] = {}
    expected: float = 0.0
    current: str | None = None
    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue
        if stripped == "automated_scores:":
            current = "automated"
            continue
        if stripped == "human_scores:":
            current = "human"
            continue
        if stripped.startswith("expected_spearman_rho:"):
            expected = float(stripped.split(":")[1].strip())
            current = None
            continue
        if current and stripped.startswith("  "):
            key, _, value = stripped.strip().partition(": ")
            if current == "automated":
                automated[key] = float(value)
            elif current == "human":
                human[key] = float(value)
    return automated, human, expected


@pytest.mark.release_gate
@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_a4_01_release_gate_spearman_fixture_verification() -> None:
    """MAC-T-BENCH-A4-01 — Spearman ρ matches expected value on the fixture.

    The fixture is a deterministic 9-pair set with a known ρ ≈ 1.0.
    The test asserts our pure-Python Spearman implementation returns
    a value within tolerance of the recorded ``expected_spearman_rho``.
    """
    assert _FIXTURE_PATH.exists(), (
        f"A4 fixture missing at {_FIXTURE_PATH}; regenerate via benchmark §3 ADR-3 Option B"
    )
    text = _FIXTURE_PATH.read_text(encoding="utf-8")
    automated, human, expected = _parse_yaml_fixture(text)

    assert len(automated) == 9
    assert len(human) == 9
    assert set(automated.keys()) == set(human.keys())

    report = run_a4_validation(automated_scores=automated, human_scores=human)
    assert report.spearman_rho == pytest.approx(expected, abs=0.01)
    # ρ = 1.0 > 0.6 → provisional_validation True.
    assert report.provisional_validation is True


@pytest.mark.release_gate
@pytest.mark.critical
@pytest.mark.mac_benchmark_harness
def test_mac_t_bench_a4_02_a4_fixture_schema_validation() -> None:
    """MAC-T-BENCH-A4-02 — fixture schema is well-formed.

    Three sections: automated_scores, human_scores, expected_spearman_rho.
    The sets of keys in automated_scores and human_scores must match
    exactly (one-to-one pairing).
    """
    text = _FIXTURE_PATH.read_text(encoding="utf-8")
    automated, human, expected = _parse_yaml_fixture(text)

    # Pairing invariant.
    assert set(automated.keys()) == set(human.keys())
    # Threshold is meaningful only if expected is a float in [-1, 1].
    assert -1.0 <= expected <= 1.0
    # And the fixture should be designed to pass the threshold.
    assert expected >= SPEARMAN_RELEASE_GATE_THRESHOLD
