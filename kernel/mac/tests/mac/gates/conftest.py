"""Shared gate-test fixtures.

Provides a :class:`FakeLLMJudge` builder that pre-populates the lookup
table for a given gate's unit + calibration-anchor fixtures. Each
``test_rN.py`` imports the helper to keep per-gate files short.
"""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from praxis.kernel.mac.gates.base import JudgeResponse
from praxis.kernel.mac.testing.fakes.fake_llm_judge import FakeLLMJudge


@pytest.fixture
def make_gate_judge():
    """Return a factory ``(gate_id, fixture_map) → (FakeLLMJudge, payload_for)``.

    ``fixture_map`` is a dict ``{fixture_id: score}``. The returned
    :class:`FakeLLMJudge` is pre-populated so calling
    ``gate.score(input_payload={"fixture_id": "X"})`` returns the
    scripted score.

    The second element ``payload_for`` is a helper that returns the
    correct input payload for a given ``fixture_id`` so tests don't
    hand-construct them.
    """

    def _factory(
        gate_id: str, fixture_map: Mapping[str, int]
    ) -> tuple[FakeLLMJudge, Any]:
        judge = FakeLLMJudge()
        for fixture_id, score in fixture_map.items():
            payload = {"fixture_id": fixture_id}
            fp = FakeLLMJudge._fingerprint(payload)
            judge.lookup_table[(gate_id, fp)] = JudgeResponse(
                score=score, rationale=f"{gate_id}:{fixture_id}"
            )

        def payload_for(fixture_id: str) -> dict[str, Any]:
            return {"fixture_id": fixture_id}

        return judge, payload_for

    return _factory
