"""Quality gate configuration tests — studio/test-strategy.md §5.

8 tests — all Tier 1, studio_schema markers.
"""

from __future__ import annotations

import pytest

from praxis.kernel.studio.schema import WorkflowTemplate


@pytest.mark.studio_schema
@pytest.mark.critical
def test_gate_01_all_12_gates_activated(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-GATE-01: Studio template activates all 12 gates (R1–R12)."""
    gate_ids = {g.gate_id for g in deep_template.quality_gates}
    expected = {f"R{i}" for i in range(1, 13)}
    assert gate_ids == expected


@pytest.mark.studio_schema
@pytest.mark.critical
def test_gate_02_r4_min_score_is_4(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-GATE-02: R4 min_score is 4 (elevated per arch §5.2)."""
    r4 = next(g for g in deep_template.quality_gates if g.gate_id == "R4")
    assert r4.min_score == 4


@pytest.mark.studio_schema
@pytest.mark.critical
def test_gate_03_r5_min_score_is_4(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-GATE-03: R5 min_score is 4 (elevated per arch §5.2)."""
    r5 = next(g for g in deep_template.quality_gates if g.gate_id == "R5")
    assert r5.min_score == 4


@pytest.mark.studio_schema
def test_gate_04_r4_weight_override_is_2(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-GATE-04: R4 weight_override is 2 (2× per arch §5.2)."""
    r4 = next(g for g in deep_template.quality_gates if g.gate_id == "R4")
    assert r4.weight_override == 2


@pytest.mark.studio_schema
def test_gate_05_r5_weight_override_is_2(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-GATE-05: R5 weight_override is 2 (2× per arch §5.2)."""
    r5 = next(g for g in deep_template.quality_gates if g.gate_id == "R5")
    assert r5.weight_override == 2


@pytest.mark.studio_schema
def test_gate_06_non_elevated_gates(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-GATE-06: All non-R4/R5 gates have min_score=3 and no weight_override."""
    for gate in deep_template.quality_gates:
        if gate.gate_id in ("R4", "R5"):
            continue
        assert gate.min_score == 3, f"{gate.gate_id}: expected min_score=3, got {gate.min_score}"
        assert gate.weight_override is None, f"{gate.gate_id}: expected no weight_override"


@pytest.mark.studio_schema
def test_gate_07_r13_not_present(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-GATE-07: R13 is NOT present (deferred per arch §5.2)."""
    gate_ids = {g.gate_id for g in deep_template.quality_gates}
    assert "R13" not in gate_ids


@pytest.mark.studio_schema
def test_gate_08_adr01_gate_alignment(deep_template: WorkflowTemplate) -> None:
    """STUDIO-T-GATE-08: R1+R4+R5+R6+R9 collectively enforce ADR-01 (arch §5.3)."""
    adr01_gates = {"R1", "R4", "R5", "R6", "R9"}
    gate_ids = {g.gate_id for g in deep_template.quality_gates}
    assert adr01_gates.issubset(gate_ids)
