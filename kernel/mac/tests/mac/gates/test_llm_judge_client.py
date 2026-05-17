"""LLMJudgeClient unit tests — arch §6.4.

Covers the pure-logic ``build_prompt`` helper and ``call_live``'s
LLMProxyPort request-mapping + JSON-reply parsing, driven by a mocked
LLMProxyPort. No real API calls are made. ``call_live`` is excluded
from *coverage measurement* per test-strategy v0.3 §13.5 Tension #7
(it is the real-LLM gateway); this mock-driven test still validates
its logic without a live call.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from praxis.kernel.mac.gates.base import JudgeResponse
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
    """Smoke — the client instantiates with an injected LLMProxyPort
    without touching call_live.
    """
    client = LLMJudgeClient(MagicMock())
    assert client is not None


async def test_call_live_routes_through_llm_proxy_and_parses_response() -> None:
    """call_live builds an LLMRequest, calls LLMProxyPort.call(), and
    parses the model's JSON reply into a JudgeResponse.
    """
    response = MagicMock()
    response.content = '{"score": 4, "rationale": "Solid steelman coverage."}'
    proxy = MagicMock()
    proxy.call.return_value = response

    result = await LLMJudgeClient(proxy).call_live(
        prompt="evaluate this output", max_tokens=256
    )

    assert result == JudgeResponse(score=4, rationale="Solid steelman coverage.")
    req = proxy.call.call_args.args[0]
    assert req.provider == "anthropic"
    assert req.model == "claude-opus-4-6"
    assert req.max_tokens == 256
    assert req.temperature == 0.0
    assert req.compression_hint == "none"
    assert [(m.role, m.content) for m in req.messages] == [
        ("user", "evaluate this output"),
    ]
