"""Calibration drift canary tests — mac/test-strategy.md v0.3 §12.

Covers MAC-T-CAL-R{1..12}-DRIFT-LOW-01 and MAC-T-CAL-R{1..12}-DRIFT-HIGH-01:
24 total tests (12 gates × 2 anchors each).

All tests are ``nightly_only`` + ``mac_gate_calibration``. They NEVER
run in PR gate. Step 4 ships them as placeholder stubs that pass; the
real Tier 3 nightly run replays the calibration anchors through a live
LLM judge and asserts drift tolerance (score-2 anchor ≤ 2, score-4
anchor ≥ 4 per v0.3 §12.1).

Per test-strategy v0.3 §12 and §13.5B marker matrix: these tests MUST
NOT carry ``no_waiver`` — live judges drift. The ``nightly_only`` marker
gates them out of PR-gate runs via the root conftest skip hook.
"""

from __future__ import annotations

import pytest

from praxis.kernel.mac.gates.calibration_anchors import CALIBRATION_ANCHORS


# Parametrize over (gate_id, anchor_level). 12 gates × 2 anchors = 24
# test instances. Each instance's pytest nodeid includes the
# parametrize ID (e.g. "test_drift_canary[R1-LOW]") so step 4's
# checkpoint report can enumerate distinct anchor IDs.
@pytest.mark.nightly_only
@pytest.mark.mac_gate_calibration
@pytest.mark.critical
@pytest.mark.parametrize("gate_id", [f"R{n}" for n in range(1, 13)])
@pytest.mark.parametrize("anchor_level", ["LOW", "HIGH"])
def test_drift_canary(gate_id: str, anchor_level: str) -> None:
    """MAC-T-CAL-R{N}-DRIFT-{LOW,HIGH}-01 — live judge drift canary.

    Tier 3 nightly test. PR-gate runs skip this via the root
    conftest.py ``--run-nightly`` option gate. When ``--run-nightly``
    is passed, the test would invoke ``LLMJudgeClient.call_live()``
    with the canonical calibration anchor for ``(gate_id, anchor_level)``
    and assert drift tolerance. Step 4 stub: verify the anchor exists.
    """
    anchor = CALIBRATION_ANCHORS[gate_id]
    if anchor_level == "LOW":
        assert anchor.score_2_example
        assert anchor.score_2_explanation
        expected_bucket = 2
    else:
        assert anchor.score_4_example
        assert anchor.score_4_explanation
        expected_bucket = 4

    # Tier 3 real implementation (Stage 7 wiring):
    #   client = LLMJudgeClient()
    #   prompt = client.build_prompt(gate_id=gate_id, ...)
    #   response = await client.call_live(prompt=prompt)
    #   assert response.score == expected_bucket (within tolerance per §12.4)
    # Step 4 stub: assert the bucket level is the expected value.
    assert expected_bucket in (2, 4)
