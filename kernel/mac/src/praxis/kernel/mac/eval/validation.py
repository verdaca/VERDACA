"""ADR-3 A4 Spearman validation — benchmark-questions.md §3 ADR-3.

The A4 release-gate test replays a pre-scored fixture
``andrey_scores_rc1.yaml`` against the Spearman correlation
computation and asserts the math matches the known ρ. The manual
Andrey-in-the-loop scoring step is OUT OF BAND — the automated test
only verifies math against fixture data.

Spearman ≥ 0.6 is the arch §9.6 / ADR-3 provisional-validation
threshold. Below 0.6 is NOT a pass/fail gate per ADR-3 — it triggers
a documented caveat in the 5.6 pre-sales report.

Binding anchors:
  - mac/architecture.md §9.6 ADR-3 A4 Validation
  - mac/benchmark-questions.md §3 ADR-3 Option B (single evaluator, 3 questions)
  - mac/benchmark-questions.md §6 Step 6 A4 validation protocol
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


SPEARMAN_RELEASE_GATE_THRESHOLD: float = 0.6
"""ADR-3 ratified threshold (benchmark-questions.md §3 ADR-3 line 336)."""


@dataclass(frozen=True)
class A4ValidationReport:
    """Result of running the Spearman correlation between automated and
    human scores on the A4 sample."""

    spearman_rho: float
    sample_size: int
    provisional_validation: bool
    """True iff ``spearman_rho >= SPEARMAN_RELEASE_GATE_THRESHOLD``."""


def compute_spearman_correlation(
    automated: list[float], human: list[float]
) -> float:
    """Return Spearman's ρ between two equal-length score lists.

    Pure-Python implementation — avoids pulling in SciPy for a
    one-formula test. The algorithm: convert each list to its rank
    vector (average rank on ties), then compute Pearson correlation
    on the ranks. This matches SciPy's ``spearmanr`` up to tie
    handling at the float level.
    """
    if len(automated) != len(human):
        raise ValueError(
            f"automated and human score lists must have equal length; "
            f"got {len(automated)} and {len(human)}"
        )
    if len(automated) < 2:
        raise ValueError("need at least 2 observations for Spearman correlation")

    ranks_a = _average_ranks(automated)
    ranks_h = _average_ranks(human)

    n = len(automated)
    mean_a = sum(ranks_a) / n
    mean_h = sum(ranks_h) / n

    cov = sum((a - mean_a) * (h - mean_h) for a, h in zip(ranks_a, ranks_h))
    var_a = sum((a - mean_a) ** 2 for a in ranks_a)
    var_h = sum((h - mean_h) ** 2 for h in ranks_h)

    denominator = (var_a * var_h) ** 0.5
    if denominator == 0:
        return 0.0
    return cov / denominator


def _average_ranks(values: list[float]) -> list[float]:
    """Return the average-ranks vector of ``values`` (1-indexed).

    Average ranks handle ties by assigning each tied element the mean
    of their positions in the sorted order.
    """
    indexed = sorted(enumerate(values), key=lambda p: p[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        # Find run of equal values.
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0  # 1-indexed
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def run_a4_validation(
    *,
    automated_scores: Mapping[str, float],
    human_scores: Mapping[str, float],
) -> A4ValidationReport:
    """Run the full A4 validation on paired (output_id → score) maps.

    Both maps must share the same key set. The report's
    ``provisional_validation`` field is True iff ρ meets the
    :data:`SPEARMAN_RELEASE_GATE_THRESHOLD`.
    """
    if set(automated_scores) != set(human_scores):
        raise ValueError(
            "automated and human score maps must share the same output IDs; "
            f"automated={sorted(automated_scores)}, human={sorted(human_scores)}"
        )

    keys = sorted(automated_scores)
    auto_list = [automated_scores[k] for k in keys]
    human_list = [human_scores[k] for k in keys]

    rho = compute_spearman_correlation(auto_list, human_list)
    return A4ValidationReport(
        spearman_rho=rho,
        sample_size=len(keys),
        provisional_validation=rho >= SPEARMAN_RELEASE_GATE_THRESHOLD,
    )


__all__ = (
    "A4ValidationReport",
    "SPEARMAN_RELEASE_GATE_THRESHOLD",
    "compute_spearman_correlation",
    "run_a4_validation",
)
