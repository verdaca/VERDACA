"""T7.6 Deliberation surface — Governance & Decision-Quality (T7) tier.

Literature source: Ma et al. (2025) human-AI deliberation + Lee et al. (2025)
critical-thinking survey (verdaca-literature-review.md §"Assessment Approaches
to Carry Forward for Murat", row "Human users accept AI recommendations
passively"). The lever the literature identifies: a decision surface must
EXPOSE alternatives, uncertainty, evidence, and disagreement so the human
inspects before accepting — rather than passively rubber-stamping.

Verdaca operationalization: a gateway ``AnalysisResult`` must surface the four
deliberation affordances on its frozen DTO seam:
    1. alternatives / tradeoffs  → ``cited_tradeoffs``
    2. uncertainty / disagreement → ``dissent_frames``
    3. evidence                   → ``artifacts`` (queryable refs)
    4. a stated recommendation    → ``recommendation`` (the thing to contest)

PASS: all four affordances present and well-typed on the real AnalysisResult.
CONDITIONAL: 3/4 present (documented degradation, surfaced as a finding).

Hermetic: drives the real ``VerdacaGatewayService.execute`` via the Stage 11
contract fakes — no live LLM, no creds. Plain tests (NO @pytest.mark.no_waiver:
the 14/9/23 pin is a ratification artifact, untouched here).
"""

from __future__ import annotations

from praxis.contract_tests.ports.gateway_contract_fakes import (
    make_ctx,
    make_gateway_harness,
    make_intent,
)
from praxis.ports.gateway_dto import AnalysisResult, ArtifactRef


def _execute(tmp_path: object) -> AnalysisResult:
    harness = make_gateway_harness(tmp_path)  # type: ignore[arg-type]
    return harness.gateway.execute(make_intent(), make_ctx())


def test_T7_6_DELIBERATION_alternatives_surface_present(tmp_path) -> None:
    """Affordance 1 (Ma/Lee): the result exposes alternatives/tradeoffs the
    human can weigh, not a single take-it-or-leave-it answer."""
    result = _execute(tmp_path)
    assert isinstance(result.cited_tradeoffs, tuple)
    assert len(result.cited_tradeoffs) >= 1
    assert all(isinstance(item, str) and item for item in result.cited_tradeoffs)


def test_T7_6_DELIBERATION_uncertainty_disagreement_surface_present(tmp_path) -> None:
    """Affordance 2 (Ma/Lee): a dissent/uncertainty channel exists on the DTO
    seam. The field is contractually present (a tuple) so a deliberative
    backend can populate it; emptiness is the no-dissent case, not a missing
    affordance."""
    result = _execute(tmp_path)
    assert hasattr(result, "dissent_frames")
    assert isinstance(result.dissent_frames, tuple)
    assert all(isinstance(frame, str) for frame in result.dissent_frames)


def test_T7_6_DELIBERATION_evidence_surface_inspectable(tmp_path) -> None:
    """Affordance 3 (Ma/Lee): evidence is inspectable — artifacts carry
    resolvable refs so the human can drill into what backed the call before
    accepting."""
    result = _execute(tmp_path)
    assert isinstance(result.artifacts, tuple)
    assert len(result.artifacts) >= 1
    for artifact in result.artifacts:
        assert isinstance(artifact, ArtifactRef)
        assert artifact.uri
        assert artifact.session_id == result.session.session_id


def test_T7_6_DELIBERATION_recommendation_is_contestable(tmp_path) -> None:
    """Affordance 4 (Ma/Lee): there is a concrete recommendation to contest.
    A deliberation surface needs a stated position; an empty one gives the
    human nothing to push back on."""
    result = _execute(tmp_path)
    assert isinstance(result.recommendation, str)
    assert result.recommendation.strip()


def test_T7_6_DELIBERATION_all_four_affordances_present_pass_criterion(tmp_path) -> None:
    """PASS criterion: all four deliberation affordances present at once on a
    single real AnalysisResult. CONDITIONAL (3/4) would be a documented
    degradation finding — this asserts the full PASS."""
    result = _execute(tmp_path)
    affordances = {
        "alternatives": bool(result.cited_tradeoffs),
        "uncertainty_channel": hasattr(result, "dissent_frames")
        and isinstance(result.dissent_frames, tuple),
        "evidence": bool(result.artifacts),
        "recommendation": bool(result.recommendation.strip()),
    }
    missing = [name for name, present in affordances.items() if not present]
    assert not missing, f"deliberation affordances missing (CONDITIONAL/FAIL): {missing}"
