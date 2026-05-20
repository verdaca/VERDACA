"""ADR-1 hybrid scoring harness — benchmark-questions.md §3 ADR-1.

Pass 1 is BLIND: R1/R2/R3/R4/R6/R7/R8/R9/R10/R11/R12 scored without
task context (random-ID mapping per benchmark §6 Step 3).

Pass 2 is OPEN for R5 only: task context provided so the judge can
detect manufactured dissent (positions not in the task context) per
Req-C Pair 2 cap.

Binding anchors:
  - mac/architecture.md §9.5 ADR-1 Hybrid Scoring
  - mac/benchmark-questions.md §3 ADR-1 + §6 Step 3/4 (two-pass protocol)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


BLIND_GATES: frozenset[str] = frozenset(
    {"R1", "R2", "R3", "R4", "R6", "R7", "R8", "R9", "R10", "R11", "R12"}
)
"""Pass 1 blind gate set — all R1..R12 except R5 (which runs in Pass 2 with
task context for manufactured-dissent detection)."""


OPEN_GATES: frozenset[str] = frozenset({"R5"})
"""Pass 2 open gate set — only R5 (Dissent Preservation) needs task
context to run its Req-C Pair 2 manufactured-dissent cap."""


@dataclass(frozen=True)
class HybridScoreRecord:
    """Output of a single (question, output) scoring pass."""

    pass_1_blind_scores: dict[str, int]
    pass_2_open_scores: dict[str, int]

    @property
    def merged_scores(self) -> dict[str, int]:
        """Merge Pass 1 + Pass 2 into a single dict[gate_id, score]."""
        merged = dict(self.pass_1_blind_scores)
        merged.update(self.pass_2_open_scores)
        return merged


@dataclass
class HybridScoringHarness:
    """ADR-1 two-pass scorer.

    Callers provide a :class:`JudgeProtocol` for blind Pass 1 and a
    (potentially different) one for open Pass 2. At step 4 both passes
    use the same :class:`FakeLLMJudge` with different lookup keys to
    simulate blind vs open scoring.
    """

    blind_scorer: Any
    """Callable ``(gate_id, output_id) → score`` for Pass 1. Step 4's
    :class:`FakeLLMJudge` satisfies this via its
    ``score_by_fixture`` method."""

    open_scorer: Any
    """Callable ``(gate_id, output_id, task_context) → score`` for Pass 2."""

    def score_output(
        self,
        *,
        output_id: str,
        task_context: Mapping[str, Any],
    ) -> HybridScoreRecord:
        """Run both passes and return a merged record."""
        pass_1: dict[str, int] = {}
        for gate_id in sorted(BLIND_GATES):
            pass_1[gate_id] = self.blind_scorer(gate_id=gate_id, output_id=output_id)

        pass_2: dict[str, int] = {}
        for gate_id in sorted(OPEN_GATES):
            pass_2[gate_id] = self.open_scorer(
                gate_id=gate_id,
                output_id=output_id,
                task_context=task_context,
            )

        return HybridScoreRecord(
            pass_1_blind_scores=pass_1,
            pass_2_open_scores=pass_2,
        )


__all__ = (
    "BLIND_GATES",
    "HybridScoreRecord",
    "HybridScoringHarness",
    "OPEN_GATES",
)
