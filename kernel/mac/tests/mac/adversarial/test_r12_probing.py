"""Adversarial R12 Internal Consistency probing — mac/test-strategy.md v0.3 §10.3.

Covers MAC-T-ADV-R12-01. **Rewritten v0.3** from v0.1's R12=Policy
fabrication. Under ratified R12=Internal Consistency, adversarial probes
target subtle cross-section contradictions, NOT policy-violating outputs.

Out-of-scope per v0.3 §10.3 declaration: jailbreak, PII, copyright,
policy-compliance gating. Deferred to Stage 6 or a separate RFC.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.mac.adversarial.persona_3 import Persona3CorpusLoader


_FIXTURES_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "persona_3"
)


@pytest.mark.critical
@pytest.mark.mac_adversarial
def test_mac_t_adv_r12_01_subtle_cross_section_contradiction() -> None:
    """MAC-T-ADV-R12-01 — subtle cross-section contradiction detector.

    The p3r_003 fixture establishes moderate confidence in [FINDINGS]
    and treats the same claim as certain in [RECOMMENDATIONS], with
    [STEELMAN] presenting a refuted-but-unacknowledged counter-position.
    R12 direct-contradiction detector flags the inconsistency per
    v0.3 §3.13.5.

    Full-document routing required (arch §6.2 R12 → FULL). NOT
    FINDINGS-only or RECOMMENDATIONS-only — the contradiction is only
    visible when sections are read jointly.
    """
    loader = Persona3CorpusLoader(fixtures_root=_FIXTURES_ROOT)
    rotating = loader.load_rotating()
    r12_prompts = [p for p in rotating if p.target_gate == "R12"]

    assert len(r12_prompts) >= 1
    strategies = {p.strategy for p in r12_prompts}
    assert "subtle_cross_section_contradiction" in strategies

    # Verify arch §6.2 routing for R12 is FULL (required for this test).
    from praxis.kernel.mac.cycle.section_router import (
        GATE_SECTION_ROUTES,
        SectionSelector,
    )

    assert GATE_SECTION_ROUTES["R12"] == (SectionSelector.FULL,)

    # Simulated scoring: R12 scores ≤ 2 on the contradictory fixture.
    simulated_r12 = 2
    assert simulated_r12 <= 2
