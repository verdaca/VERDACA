"""QualityGateEngine smoke test — arch §6.7.

Covers the engine's ``evaluate()`` path end-to-end with a
:class:`FakeLLMJudge` seeded with canned scores for all 12 gates. This
is a coverage-floor test for the engine module — not a MAC-T catalog
entry per v0.3 §3 (the engine is exercised indirectly via the per-gate
tests). Step 5 / step 6 will add additional engine tests as part of
the full wire-up.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.engine import QualityGateEngine, build_default_engine
from praxis.kernel.mac.gates.base import JudgeResponse
from praxis.kernel.mac.gates.registry import GateRegistry
from praxis.kernel.mac.task import DomainClass
from praxis.kernel.mac.testing.fakes.fake_llm_judge import FakeLLMJudge


class _DeterministicJudge:
    """Mini judge that returns a canned score for every gate_id, ignoring
    the payload fingerprint."""

    def __init__(self, score: int) -> None:
        self._score = score
        self.calls: list[tuple[str, dict]] = []

    def score(self, *, gate_id: str, input_payload: dict) -> JudgeResponse:
        self.calls.append((gate_id, dict(input_payload)))
        return JudgeResponse(score=self._score, rationale=f"{gate_id}: canned")


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_engine_evaluates_all_12_gates_and_applies_ordering() -> None:
    """Engine smoke — evaluate() returns 12-gate raw + effective scores.

    With all raw scores = 4 and forge_degraded=False, effective scores
    should equal raw (no Forge penalty) and R8 cap is trivially
    satisfied (min(4, 4+1) = 4).
    """
    judge = _DeterministicJudge(score=4)
    registry = GateRegistry(judge=judge)
    engine = QualityGateEngine(registry=registry)

    result = engine.evaluate(
        input_payload={"fixture_id": "smoke"},
        domain_class=DomainClass.CONTESTED,
        forge_degraded=False,
    )

    # All 12 gates called.
    assert len(judge.calls) == 12
    assert {call[0] for call in judge.calls} == {f"R{n}" for n in range(1, 13)}

    # Raw + effective populated.
    assert len(result.raw_scores) == 12
    assert len(result.effective_scores) == 12
    assert all(v == 4 for v in result.raw_scores.values())
    assert all(v == 4 for v in result.effective_scores.values())
    assert result.suspended == frozenset()


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_engine_applies_req_e_suspension_on_consensus() -> None:
    """Engine smoke — Req-E: DomainClass.CONSENSUS suspends R5."""
    judge = _DeterministicJudge(score=5)
    engine = build_default_engine(judge=judge)

    result = engine.evaluate(
        input_payload={"fixture_id": "smoke"},
        domain_class=DomainClass.CONSENSUS,
        forge_degraded=False,
    )
    assert "R5" in result.suspended
    assert result.effective_scores["R5"] == 0  # suspended gate is zeroed


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_engine_applies_forge_penalty_via_compute_final_scores() -> None:
    """Engine smoke — forge_degraded=True applies the R7 penalty via
    compute_final_scores (single source of truth per team-lead
    constraint 2). Engine delegates, does not re-implement.
    """
    judge = _DeterministicJudge(score=4)
    engine = build_default_engine(judge=judge)

    result = engine.evaluate(
        input_payload={"fixture_id": "smoke"},
        domain_class=DomainClass.CONTESTED,
        forge_degraded=True,
    )
    # R7 effective = 4 - 1 = 3
    assert result.effective_scores["R7"] == 3
    # R8 uses RAW R7 (4) for its cap: min(4, 4+1) = 4
    assert result.effective_scores["R8"] == 4
