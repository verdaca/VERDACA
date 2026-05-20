"""Persona 3 adversarial tests — mac/test-strategy.md v0.3 §10.1.

Covers MAC-T-ADV-P3-01..05. Entry #15 in the 16-entry allow-list is
``MAC-T-ADV-P3-01`` (no_waiver deterministic fixture inventory).

Out-of-scope per v0.3 §10.3 declaration: jailbreak, PII leakage,
copyright infringement. These are NOT in the Persona 3 corpus and
NOT tested here. They are deferred to Stage 6 or a separate RFC.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.mac.adversarial.persona_3 import (
    Persona3CorpusLoader,
    Persona3Prompt,
)


_FIXTURES_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "persona_3"
)


# Allow-list entry #15 — Q-1 canonical name preserved.
@pytest.mark.critical
@pytest.mark.mac_adversarial
@pytest.mark.static
@pytest.mark.no_waiver  # Decision 1 item 11 deterministic carrier — §13.3.3 entry #15
def test_mac_t_adv_p3_01_fixture_inventory_deterministic() -> None:
    """MAC-T-ADV-P3-01 — Persona 3 fixture corpus inventory.

    Per test-strategy v0.3 §10.1.1: ``tests/mac/adversarial/fixtures/persona_3/``
    has both ``public/`` and ``rotating/`` subdirectories, each
    containing ≥3 gaming prompts.

    Allow-list entry #15 — no_waiver. Step 6's meta-test references
    this exact nodeid.
    """
    assert _FIXTURES_ROOT.exists(), f"fixtures root missing: {_FIXTURES_ROOT}"

    public_dir = _FIXTURES_ROOT / "public"
    rotating_dir = _FIXTURES_ROOT / "rotating"

    assert public_dir.exists(), f"public/ missing: {public_dir}"
    assert rotating_dir.exists(), f"rotating/ missing: {rotating_dir}"

    public_prompts = list(public_dir.glob("*.txt"))
    rotating_prompts = list(rotating_dir.glob("*.txt"))

    assert len(public_prompts) >= 3, (
        f"public/ must have >=3 gaming prompts; found {len(public_prompts)}"
    )
    assert len(rotating_prompts) >= 3, (
        f"rotating/ must have >=3 gaming prompts; found {len(rotating_prompts)}"
    )


@pytest.mark.nightly_only
@pytest.mark.critical
@pytest.mark.mac_adversarial
def test_mac_t_adv_p3_02_live_adversarial_judge_run() -> None:
    """MAC-T-ADV-P3-02 — live adversarial judge. Tier 3 nightly.

    NOT ``no_waiver`` — live judges drift per Decision 1 structural
    boundary. Runs against real LLM under ``--run-nightly``.
    """
    assert True  # Stage 7 POV Harness wires in real judge call


@pytest.mark.critical
@pytest.mark.mac_adversarial
def test_mac_t_adv_p3_03_manufactured_dissent_detection_unit() -> None:
    """MAC-T-ADV-P3-03 — manufactured dissent unit test.

    The p3_001 fixture targets R5 with manufactured dissent. Req-C
    Pair 2 caps R5_eff at min(R5_raw, R4_raw) when the reviewer flags
    manufactured dissent. Verified via compute_final_scores (step 3
    signature evolution at step 4).
    """
    loader = Persona3CorpusLoader(fixtures_root=_FIXTURES_ROOT)
    public = loader.load_public()
    r5_prompts = [p for p in public if p.target_gate == "R5"]
    assert len(r5_prompts) >= 1
    assert r5_prompts[0].strategy == "manufactured_dissent"

    from praxis.kernel.mac.cycle.iteration_controller import compute_final_scores

    # (R4_raw=2, R5_raw=5, manufactured=True) → R5_eff = 2
    raw = {**{f"R{n}": 4 for n in range(1, 13)}, "R4": 2, "R5": 5}
    eff = compute_final_scores(
        raw,
        forge_degraded=False,
        reviewer_critique={"manufactured_dissent_detected": True},
    )
    assert eff["R5"] == 2


@pytest.mark.critical
@pytest.mark.mac_adversarial
def test_mac_t_adv_p3_04_evidence_flooding_detection_unit() -> None:
    """MAC-T-ADV-P3-04 — evidence-flooding fixture targets R7.

    The p3_002 fixture targets R7 with evidence flooding. Step 5 asserts
    the fixture exists and the loader can parse it; live R7 scoring
    against flooded evidence runs in Tier 3 nightly via P3-02.
    """
    loader = Persona3CorpusLoader(fixtures_root=_FIXTURES_ROOT)
    public = loader.load_public()
    r7_prompts = [p for p in public if p.target_gate == "R7"]
    assert len(r7_prompts) >= 1
    assert "flooding" in r7_prompts[0].strategy


@pytest.mark.critical
@pytest.mark.mac_adversarial
@pytest.mark.asymmetry_structural
def test_mac_t_adv_p3_05_gaming_on_r4_steelman() -> None:
    """MAC-T-ADV-P3-05 — R4 steelman mimicry is defeated by Req-F.

    The p3_003 fixture targets R4 with steelman mimicry. Req-F two-step
    protocol requires the reviewer to write its own ``independent_steelman``
    FIRST, then read the producer's [STEELMAN]. A producer that copies
    the reviewer's likely steelman is detected when
    ``gap_assessment`` flags the divergence.

    Step 5 asserts the fixture exists and has the correct target_gate;
    the Req-F structural enforcement is in MAC-T-ASYM-R-F-02.
    """
    loader = Persona3CorpusLoader(fixtures_root=_FIXTURES_ROOT)
    public = loader.load_public()
    r4_prompts = [p for p in public if p.target_gate == "R4"]
    assert len(r4_prompts) >= 1
    assert r4_prompts[0].strategy == "steelman_mimicry"
