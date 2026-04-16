"""FakeLLMJudge fake — test-strategy v0.3 §14.3.1 frozen interface contract.

Deterministic lookup-table backed judge. Tier 1 PR-gate tests use this
to drive gate evaluators without any LLM call.

Lookup key: ``(gate_id: str, fingerprint: str)`` where ``fingerprint`` is
the stable SHA256 of the canonical-JSON of the input payload.

The ``build_default_lookup_table`` helper produces a seed table from
:data:`CALIBRATION_ANCHORS` so gate calibration anchor tests can replay
the §5 score-2 / score-4 anchors without additional fixture setup.

Binding anchors:
  - mac/test-strategy.md v0.3 §14.3.1 FakeLLMJudge (frozen interface)
  - mac/architecture.md §6.4 Calibration Corpus (Req-D)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from praxis.kernel.mac.gates.base import JudgeResponse
from praxis.kernel.mac.gates.calibration_anchors import CALIBRATION_ANCHORS


@dataclass
class FakeLLMJudge:
    """Deterministic lookup-table backed judge.

    Raises ``KeyError`` on lookup miss — do NOT fall back to a real
    call (test-strategy v0.3 §16.5A pitfall #10: never use live LLMs
    in Tier 1). The test author's job is to populate the lookup
    table; a miss is a bug in the test, not a signal to upgrade to
    live.
    """

    lookup_table: dict[tuple[str, str], JudgeResponse] = field(default_factory=dict)
    call_log: list[tuple[str, str]] = field(default_factory=list)

    def score(self, *, gate_id: str, input_payload: Mapping[str, Any]) -> JudgeResponse:
        """Fingerprint the input and return the canned response."""
        fp = self._fingerprint(input_payload)
        key = (gate_id, fp)
        self.call_log.append(key)
        if key not in self.lookup_table:
            raise KeyError(
                f"FakeLLMJudge lookup miss: gate={gate_id}, fp={fp[:16]}... "
                f"Either regenerate the lookup table or provide the fixture. "
                f"Test-strategy v0.3 §16.5A pitfall #10: do NOT fall back to "
                f"a live LLM."
            )
        return self.lookup_table[key]

    def score_by_fixture(self, *, gate_id: str, output_id: str) -> int:
        """Simplified lookup by (gate_id, output_id) string pair.

        Used by :class:`HybridScoringHarness` at step 4 to simulate
        blind/open two-pass scoring with a single lookup interface.
        The fake treats ``output_id`` as the fingerprint directly,
        bypassing canonical-JSON hashing.
        """
        key = (gate_id, output_id)
        self.call_log.append(key)
        if key not in self.lookup_table:
            raise KeyError(
                f"FakeLLMJudge fixture lookup miss: ({gate_id!r}, {output_id!r})"
            )
        return self.lookup_table[key].score

    @staticmethod
    def _fingerprint(payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_default_lookup_table() -> dict[tuple[str, str], JudgeResponse]:
    """Seed table from benchmark §5 calibration anchors.

    Populates ``(gate_id, anchor_key)`` entries keyed on simple string
    tags (``"anchor_2"`` / ``"anchor_4"``) so calibration anchor tests
    can reference them without re-hashing the anchor text.
    """
    table: dict[tuple[str, str], JudgeResponse] = {}
    for gate_id, anchor in CALIBRATION_ANCHORS.items():
        table[(gate_id, "anchor_2")] = JudgeResponse(
            score=2, rationale=anchor.score_2_explanation
        )
        table[(gate_id, "anchor_4")] = JudgeResponse(
            score=4, rationale=anchor.score_4_explanation
        )
    return table


__all__ = ("FakeLLMJudge", "build_default_lookup_table")
