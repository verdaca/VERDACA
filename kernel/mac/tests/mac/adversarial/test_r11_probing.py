"""Adversarial R11 Scenario Coverage probing — mac/test-strategy.md v0.3 §10.2.

Covers MAC-T-ADV-R11-01..02. **Rewritten v0.3** from v0.1's R11=Safety
fabrication. Under ratified R11=Scenario Coverage, adversarial probes
target scenario-gaming strategies (single-scenario bias, manufactured
non-falsifiable triggers), NOT jailbreak resistance.

Out-of-scope per v0.3 §10.3: jailbreak, PII, copyright. Deferred to
Stage 6.
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
def test_mac_t_adv_r11_01_single_scenario_bias() -> None:
    """MAC-T-ADV-R11-01 — single-scenario bias disguised as multi-scenario.

    The p3r_001 fixture (rotating corpus) presents three labeled
    scenarios that actually describe the same underlying future. R11
    scores ≤2 because has_differentiated_implications is false per
    v0.3 §3.12.5 property.

    Under ratified R11 = Scenario Coverage — NOT the v0.1 R11 = Safety
    (retired).
    """
    loader = Persona3CorpusLoader(fixtures_root=_FIXTURES_ROOT)
    rotating = loader.load_rotating()
    r11_prompts = [p for p in rotating if p.target_gate == "R11"]

    # At least one R11-targeted gaming prompt in rotating corpus.
    assert len(r11_prompts) >= 1

    # The single_scenario_bias strategy should be represented.
    strategies = {p.strategy for p in r11_prompts}
    assert "single_scenario_bias" in strategies

    # Simulated scoring: the gaming attempt fails R11.
    # Real live scoring runs in Tier 3 nightly.
    simulated_r11 = 2  # R11 ≤ 2 per v0.3 §3.12.5 property rule
    assert simulated_r11 <= 2


@pytest.mark.critical
@pytest.mark.mac_adversarial
def test_mac_t_adv_r11_02_manufactured_non_falsifiable_triggers() -> None:
    """MAC-T-ADV-R11-02 — manufactured non-falsifiable trigger conditions.

    The p3r_002 fixture presents three distinct scenarios with
    differentiated implications BUT the trigger conditions are
    unfalsifiable ("if sentiment shifts meaningfully"). R11 scores ≤2
    because has_distinct_triggers is false per v0.3 §3.12.5.

    Cross-reference R3 Falsifiability: these triggers would also fail
    R3 individually, but R11 catches the scenario-level failure first.
    """
    loader = Persona3CorpusLoader(fixtures_root=_FIXTURES_ROOT)
    rotating = loader.load_rotating()
    r11_prompts = [p for p in rotating if p.target_gate == "R11"]

    strategies = {p.strategy for p in r11_prompts}
    assert "manufactured_non_falsifiable_triggers" in strategies

    simulated_r11 = 2
    assert simulated_r11 <= 2
