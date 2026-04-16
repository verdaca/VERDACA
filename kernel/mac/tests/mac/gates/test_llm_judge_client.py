"""LLMJudgeClient.build_prompt() pure-logic test — arch §6.4.

Coverage-floor test exercising the non-excluded ``build_prompt`` helper.
``call_live()`` remains excluded per v0.3 §13.5 Tension #7 — PR-gate
tests never invoke it.
"""

from __future__ import annotations

from praxis.kernel.mac.gates.calibration_anchors import CALIBRATION_ANCHORS
from praxis.kernel.mac.judge.llm_judge_client import LLMJudgeClient


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_build_prompt_renders_calibration_anchors_for_every_gate() -> None:
    """For each R1..R12 gate, LLMJudgeClient.build_prompt() embeds the
    score-2 and score-4 anchor text + explanation from
    CALIBRATION_ANCHORS verbatim.
    """
    for gate_id in (f"R{n}" for n in range(1, 13)):
        prompt = LLMJudgeClient.build_prompt(
            gate_id=gate_id,
            section_key="[FINDINGS]",
            section_text="sample output text",
        )
        anchor = CALIBRATION_ANCHORS[gate_id]
        assert anchor.score_2_example in prompt
        assert anchor.score_4_example in prompt
        assert anchor.score_2_explanation in prompt
        assert anchor.score_4_explanation in prompt
        assert "Return JSON" in prompt


# Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
# Stage 5.3 preload Q3 disposition 2026-04-14
def test_llm_judge_client_can_be_instantiated() -> None:
    """Smoke — the client instantiates without touching call_live."""
    client = LLMJudgeClient(model="claude-opus-4-6")
    assert client is not None
