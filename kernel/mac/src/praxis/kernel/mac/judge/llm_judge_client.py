"""LLM judge client — production Tier 3 gateway.

``LLMJudgeClient.call_live()`` is the real-LLM entry point invoked only
by the nightly drift canary (§12) and release-gate A4 harness. Tier 1
PR-gate tests NEVER call it — they use :class:`FakeLLMJudge`.

**Coverage exclusion:** ``call_live()`` is excluded from coverage
measurement per test-strategy v0.3 §13.5 Tension #7 resolution and
the pi-mono/test-strategy.md §7 generated-file precedent. The omit
entry in ``pyproject.toml [tool.coverage.run] omit`` is uncommented at
step 4 (this step). Rationale: the method is exclusively exercised
by Tier 3 nightly tests, never from PR-gate tests; excluding it
keeps the ≥90% coverage floor honest.

The :meth:`build_prompt` helper is NOT excluded — it is pure logic
that composes the judge prompt from the gate definition + calibration
anchors, and Tier 1 tests can exercise it.

Binding anchors:
  - mac/architecture.md §6.4 Calibration Corpus (Req-D judge prompts)
  - mac/test-strategy.md v0.3 §13.5.1 Coverage exclusion
  - pi-mono/test-strategy.md §7 generated-file precedent
"""

from __future__ import annotations

from praxis.kernel.mac.gates.base import JudgeResponse
from praxis.kernel.mac.gates.calibration_anchors import (
    CALIBRATION_ANCHORS,
    CalibrationAnchor,
)


_JUDGE_PROMPT_TEMPLATE: str = """\
You are evaluating {gate_id} ({gate_name}) on a 1-5 scale per the rubric.

Calibration anchors for this gate:
- Score 2/5 example: "{score_2_example}"
  Why score 2: {score_2_explanation}
- Score 4/5 example: "{score_4_example}"
  Why score 4: {score_4_explanation}

The output to evaluate (section: {section_key}):
\"\"\"
{section_text}
\"\"\"

Return JSON: {{"score": <int 1-5>, "rationale": "<one sentence>"}}
"""


class LLMJudgeClient:
    """Production LLM judge client.

    Only instantiated at Tier 3 nightly / Tier 4 release-gate time.
    Tier 1 PR-gate tests use :class:`FakeLLMJudge` and NEVER construct
    this class.
    """

    def __init__(self, *, model: str = "claude-opus-4-6") -> None:
        self._model = model

    @staticmethod
    def build_prompt(
        *,
        gate_id: str,
        section_key: str,
        section_text: str,
        anchor: CalibrationAnchor | None = None,
    ) -> str:
        """Render the canonical Req-D judge prompt for a (gate, section) pair.

        Pure logic — no LLM call. Exercised by Tier 1 unit tests. The
        calibration anchor defaults to the canonical
        :data:`CALIBRATION_ANCHORS` entry for the gate.
        """
        resolved_anchor = anchor or CALIBRATION_ANCHORS[gate_id]
        gate_name_lookup = {
            "R1": "Epistemic Calibration",
            "R2": "Question Fidelity",
            "R3": "Falsifiability",
            "R4": "Steelman Completeness",
            "R5": "Dissent Preservation",
            "R6": "Decision Relevance Density",
            "R7": "Reasoning Traceability",
            "R8": "Actionability Calibration",
            "R9": "Evidence Impartiality",
            "R10": "Epistemic Scope Honesty",
            "R11": "Scenario Coverage",
            "R12": "Internal Consistency",
        }
        return _JUDGE_PROMPT_TEMPLATE.format(
            gate_id=gate_id,
            gate_name=gate_name_lookup[gate_id],
            score_2_example=resolved_anchor.score_2_example,
            score_2_explanation=resolved_anchor.score_2_explanation,
            score_4_example=resolved_anchor.score_4_example,
            score_4_explanation=resolved_anchor.score_4_explanation,
            section_key=section_key,
            section_text=section_text,
        )

    async def call_live(  # pragma: no cover -- excluded per test-strategy v0.3 §13.5
        self,
        *,
        prompt: str,
        max_tokens: int = 512,
    ) -> JudgeResponse:
        """Invoke the real LLM. **Tier 3 nightly / Tier 4 release only.**

        Excluded from coverage measurement per test-strategy v0.3 §13.5
        Tension #7 resolution. The PR-gate suite never reaches this
        line — only the nightly drift canary and release-gate A4
        harness exercise it, and both are opt-in via ``--run-nightly``
        and ``--run-release`` respectively.

        Step 4 ships a NotImplementedError stub. Stage 7 POV Harness
        wires in the real ``anthropic`` SDK call with proper
        rate-limiting + retry.
        """
        del prompt, max_tokens
        raise NotImplementedError(
            "LLMJudgeClient.call_live is a Tier 3/4 gateway; not implemented at step 4. "
            "PR-gate tests must use FakeLLMJudge."
        )


__all__ = ("LLMJudgeClient",)
