"""MAC evaluation harness — arch §9 + benchmark-questions.md §6."""

from __future__ import annotations

from praxis.kernel.mac.eval.baselines import (
    BASELINE_ENHANCED_PROMPT,
    BASELINE_VANILLA_PROMPT,
)
from praxis.kernel.mac.eval.composite import (
    GATE_WEIGHTS,
    TOTAL_WEIGHT,
    composite_score,
)
from praxis.kernel.mac.eval.scoring import HybridScoringHarness
from praxis.kernel.mac.eval.validation import (
    A4ValidationReport,
    SPEARMAN_RELEASE_GATE_THRESHOLD,
    compute_spearman_correlation,
    run_a4_validation,
)

__all__ = (
    "A4ValidationReport",
    "BASELINE_ENHANCED_PROMPT",
    "BASELINE_VANILLA_PROMPT",
    "GATE_WEIGHTS",
    "HybridScoringHarness",
    "SPEARMAN_RELEASE_GATE_THRESHOLD",
    "TOTAL_WEIGHT",
    "composite_score",
    "compute_spearman_correlation",
    "run_a4_validation",
)
