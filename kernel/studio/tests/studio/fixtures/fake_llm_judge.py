"""FakeLLMJudge — deterministic R1–R12 scorer from a fixture lookup table.

Binding: studio/test-strategy.md §14.1, following MAC test-strategy §14.3.1 pattern.
"""

from __future__ import annotations

from praxis.kernel.studio.models import GateScores


def _default_gate_scores(
    r4: int = 4,
    r5: int = 4,
    default: int = 3,
) -> dict[str, int]:
    scores = {f"R{i}": default for i in range(1, 13)}
    scores["R4"] = r4
    scores["R5"] = r5
    return scores


def _compute_composite(scores: dict[str, int]) -> float:
    """Replicate studio composite formula: Σ(score × weight) / Σ(weight) × 20."""
    weights = {f"R{i}": 2 if i in (4, 5) else 1 for i in range(1, 13)}
    weighted_sum = sum(scores.get(gid, 0) * w for gid, w in weights.items())
    total_weight = sum(weights.values())
    return (weighted_sum / total_weight) * 20 if total_weight > 0 else 0.0


class FakeLLMJudge:
    """Returns deterministic GateScores from a fixture lookup table.

    Falls back to a default fixture (all R4/R5=4, others=3) when no
    specific fixture is registered for the prompt.

    Usage::

        judge = FakeLLMJudge()
        judge.register_output("my prompt text", scores={"R4": 4, "R5": 4, ...})
        scores = judge.score("my prompt text")
    """

    def __init__(self, default_r4: int = 4, default_r5: int = 4, default_score: int = 3) -> None:
        self._lookup: dict[int, GateScores] = {}  # hash(text) → GateScores
        self._default_r4 = default_r4
        self._default_r5 = default_r5
        self._default_score = default_score

    def register_output(self, text: str, scores: dict[str, int] | None = None) -> None:
        resolved = _default_gate_scores(
            r4=self._default_r4, r5=self._default_r5, default=self._default_score
        )
        if scores:
            resolved.update(scores)
        composite = _compute_composite(resolved)
        self._lookup[hash(text)] = GateScores(
            scores=resolved,
            composite=composite,
            backbone_completeness={
                "trade_offs": True,
                "dissent": True,
                "scenarios": True,
                "scope_limits": True,
            },
            register_compliant=True,
        )

    def score(self, output_text: str) -> GateScores:
        """Return registered scores or a default fixture."""
        key = hash(output_text)
        if key in self._lookup:
            return self._lookup[key]
        scores = _default_gate_scores(
            r4=self._default_r4, r5=self._default_r5, default=self._default_score
        )
        composite = _compute_composite(scores)
        return GateScores(
            scores=scores,
            composite=composite,
            backbone_completeness={
                "trade_offs": True,
                "dissent": True,
                "scenarios": True,
                "scope_limits": True,
            },
            register_compliant=True,
        )
