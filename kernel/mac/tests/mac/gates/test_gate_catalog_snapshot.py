"""Gate catalog snapshot test — MAC-T-GATE-CATALOG-SNAPSHOT-01.

Arch §6.1 12-gate catalog is frozen. The YAML at
``tests/mac/gates/snapshots/gate_catalog_v0_1.yaml`` IS the contract.
Regeneration requires an arch §6.1 revision — not a fix-the-test hotpatch.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.mac.cycle.section_router import GATE_SECTION_ROUTES
from praxis.kernel.mac.gates.registry import GATE_CLASSES


_SNAPSHOT_PATH = Path(__file__).resolve().parent / "snapshots" / "gate_catalog_v0_1.yaml"


_EXPECTED_CATALOG = {
    "R1": {"name": "Epistemic Calibration", "priority": "Critical", "section": "FULL"},
    "R2": {"name": "Question Fidelity", "priority": "Critical", "section": "RECOMMENDATIONS"},
    "R3": {"name": "Falsifiability", "priority": "High", "section": "FULL"},
    "R4": {"name": "Steelman Completeness", "priority": "Critical", "section": "STEELMAN"},
    "R5": {"name": "Dissent Preservation", "priority": "Critical", "section": "DISSENT"},
    "R6": {"name": "Decision Relevance Density", "priority": "Medium", "section": "L1"},
    "R7": {"name": "Reasoning Traceability", "priority": "Critical", "section": "L2"},
    "R8": {"name": "Actionability Calibration", "priority": "High", "section": "RECOMMENDATIONS"},
    "R9": {"name": "Evidence Impartiality", "priority": "Medium", "section": "FINDINGS"},
    "R10": {"name": "Epistemic Scope Honesty", "priority": "High", "section": "FULL"},
    "R11": {"name": "Scenario Coverage", "priority": "High", "section": "L2"},
    "R12": {"name": "Internal Consistency", "priority": "High", "section": "FULL"},
}


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_gate_catalog_snapshot_01_byte_equality() -> None:
    """MAC-T-GATE-CATALOG-SNAPSHOT-01 — the 12-gate catalog matches the snapshot.

    Parses the committed YAML and asserts each row's ``name``,
    ``priority``, and ``section`` match the arch §6.1 values verbatim.
    ``GATE_SECTION_ROUTES`` is the single source of truth for the section
    column — if it drifts, this test catches the drift on the section
    field before ``MAC-T-CYCLE-SEC-02`` catches the binary snapshot.
    """
    assert _SNAPSHOT_PATH.exists()
    text = _SNAPSHOT_PATH.read_text(encoding="utf-8")

    # Minimal hand-parser to avoid a PyYAML dep at Tier 1. Each record is
    # 4 lines: "RN:", "  name: ...", "  priority: ...", "  section: ...".
    parsed: dict[str, dict[str, str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        if line.endswith(":") and not line.startswith(" "):
            current = line[:-1]
            parsed[current] = {}
        elif current is not None and line.startswith("  "):
            key, _, value = line.strip().partition(": ")
            parsed[current][key] = value

    assert parsed == _EXPECTED_CATALOG

    # Validate the section column matches GATE_SECTION_ROUTES for every row.
    section_rename = {
        ("FINDINGS",): "FINDINGS",
        ("RECOMMENDATIONS",): "RECOMMENDATIONS",
        ("STEELMAN",): "STEELMAN",
        ("DISSENT",): "DISSENT",
        ("FULL",): "FULL",
        ("L1",): "L1",
        ("L2",): "L2",
    }
    for gate_id, expected in _EXPECTED_CATALOG.items():
        selectors = GATE_SECTION_ROUTES[gate_id]
        canonical = tuple(s.value for s in selectors)
        assert section_rename[canonical] == expected["section"], gate_id

    # Exactly 12 gates in the registry (same invariant as MAC-T-NEG-GATE13-01).
    assert len(GATE_CLASSES) == 12
