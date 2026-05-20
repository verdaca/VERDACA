"""FakeBenchmarkOutputs fake — test-strategy v0.3 §14.3.5 frozen interface contract.

30-item lookup table: 10 benchmark questions × 3 baselines (vanilla,
enhanced, mac). Used by §7 scoring-harness tests to exercise the
composite formula and ADR-1 hybrid pass logic without any LLM call.

Binding anchors:
  - mac/test-strategy.md v0.3 §14.3.5 FakeBenchmarkOutputs (frozen interface)
  - mac/benchmark-questions.md §6 scoring protocol
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


BASELINES: tuple[str, ...] = ("vanilla", "enhanced", "mac")
"""Arch §9.3 three-baseline tuple."""


QUESTION_IDS: tuple[str, ...] = tuple(f"Q{n}" for n in range(1, 11))
"""Benchmark-questions.md §2 question IDs — Q1..Q10."""


@dataclass(frozen=True)
class PreScoredOutput:
    """A pre-scored benchmark output with the 12 gate scores already
    computed. Used in §7 tests to exercise the composite / ADR-1 / ADR-3
    logic without calling any LLM.
    """

    question_id: str
    baseline: str
    text: str
    gate_scores: dict[str, int]


@dataclass
class FakeBenchmarkOutputs:
    """30-item lookup table (10 questions × 3 baselines)."""

    outputs: dict[tuple[str, str], PreScoredOutput] = field(default_factory=dict)

    def get(self, *, question_id: str, baseline: str) -> PreScoredOutput:
        key = (question_id, baseline)
        if key not in self.outputs:
            raise KeyError(f"FakeBenchmarkOutputs miss: {key}")
        return self.outputs[key]

    def all(self) -> list[PreScoredOutput]:
        return list(self.outputs.values())


def build_default_benchmark_outputs() -> FakeBenchmarkOutputs:
    """Seed the fake with deterministic 30-item outputs.

    Assigns monotonically-increasing scores per baseline so the
    composite math tests can assert predictable relative ordering:
    MAC > enhanced > vanilla by ~1 point per gate.
    """
    outputs: dict[tuple[str, str], PreScoredOutput] = {}
    for q_id in QUESTION_IDS:
        for baseline_idx, baseline in enumerate(BASELINES):
            # vanilla: all 3; enhanced: all 4; mac: all 5 — neat separations
            base_score = 3 + baseline_idx
            gate_scores = {f"R{n}": base_score for n in range(1, 13)}
            outputs[(q_id, baseline)] = PreScoredOutput(
                question_id=q_id,
                baseline=baseline,
                text=f"{baseline}-baseline-output-for-{q_id}",
                gate_scores=gate_scores,
            )
    return FakeBenchmarkOutputs(outputs=outputs)


__all__ = (
    "BASELINES",
    "FakeBenchmarkOutputs",
    "PreScoredOutput",
    "QUESTION_IDS",
    "build_default_benchmark_outputs",
)
