"""LLM judge client — production Tier 3 gateway.

``LLMJudgeClient.call_live()`` is the real-LLM entry point invoked with
a live ``LLMProxyPort`` only by the nightly drift canary (§12) and the
release-gate A4 harness. PR-gate gate judging never takes the live
path — it uses :class:`FakeLLMJudge`; ``call_live``'s own request-
mapping and reply-parsing logic is unit-tested at PR-gate time via a
mocked ``LLMProxyPort``.

**Coverage exclusion:** ``call_live()`` is excluded from coverage
measurement per test-strategy v0.3 §13.5 Tension #7 resolution and
the pi-mono/test-strategy.md §7 generated-file precedent. Exclusion is
enforced by the in-method ``# pragma: no cover`` on the ``call_live``
definition line. Rationale: the live LLM call is exercised only by
Tier 3 nightly / Tier 4 release tests, never from PR-gate tests; the
method stays coverage-excluded under the ratified §13.5 policy
regardless of the mock-driven PR-gate logic test, keeping the ≥90%
coverage floor honest.

The :meth:`build_prompt` helper is NOT excluded — it is pure logic
that composes the judge prompt from the gate definition + calibration
anchors, and Tier 1 tests can exercise it.

Binding anchors:
  - mac/architecture.md §6.4 Calibration Corpus (Req-D judge prompts)
  - mac/test-strategy.md v0.3 §13.5.1 Coverage exclusion
  - pi-mono/test-strategy.md §7 generated-file precedent
"""

from __future__ import annotations

import json
import uuid

from praxis.kernel.mac.gates.base import JudgeResponse
from praxis.kernel.mac.gates.calibration_anchors import (
    CALIBRATION_ANCHORS,
    CalibrationAnchor,
)
from praxis.ports.common import Message
from praxis.ports.llm_proxy import LLMProxyPort, LLMRequest

# Pinned judge model. Exact routing identifier is confirmed when DIAL routing lands.
_JUDGE_MODEL = "claude-opus-4-6"
_SCHEMA_VERSION = 1
_PROVIDER = "anthropic"


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

    def __init__(self, llm_proxy: LLMProxyPort, *, model: str = _JUDGE_MODEL) -> None:
        self._llm_proxy = llm_proxy
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
        """Invoke the real LLM via LLMProxyPort. **Tier 3 nightly / Tier 4 release only.**

        Builds an :class:`LLMRequest` carrying the composed judge
        *prompt* as a single user-role :class:`Message`, calls the sync
        :meth:`LLMProxyPort.call`, and parses the model's JSON reply
        (``{"score": <int 1-5>, "rationale": "<one sentence>"}``) into a
        :class:`JudgeResponse`.

        Excluded from coverage measurement per test-strategy v0.3 §13.5
        Tension #7 resolution. The PR-gate suite never reaches this
        line with a live port — only the nightly drift canary and
        release-gate A4 harness exercise it, and both are opt-in via
        ``--run-nightly`` and ``--run-release`` respectively.

        Malformed model output (non-JSON, or a missing ``score`` /
        ``rationale`` key) propagates as ``json.JSONDecodeError`` /
        ``KeyError``; ``LLMProxyPort`` failures propagate as their
        ``VerdacaPortError`` subclasses. No score-range validation or
        error remapping is performed here — an unhandled failure is the
        correct signal to the Tier 3/4 harness.
        """
        correlation_id = uuid.uuid4().hex
        request = LLMRequest(
            schema_version=_SCHEMA_VERSION,
            correlation_id=correlation_id,
            idempotency_key=uuid.uuid4().hex,
            provider=_PROVIDER,
            model=self._model,
            messages=[
                Message(
                    schema_version=_SCHEMA_VERSION,
                    correlation_id=correlation_id,
                    role="user",
                    content=prompt,
                ),
            ],
            max_tokens=max_tokens,
            temperature=0.0,
            compression_hint="none",
        )
        # LLMProxyPort.call() is sync (ADR-9.1.2-6 §3 idempotency table);
        # called directly from async call_live() — same pattern as
        # Caveman's HaikuProvider.compress().
        response = self._llm_proxy.call(request)
        parsed = json.loads(response.content)
        return JudgeResponse(score=parsed["score"], rationale=parsed["rationale"])


__all__ = ("LLMJudgeClient",)
