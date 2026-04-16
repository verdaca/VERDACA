"""Section router tests — mac/test-strategy.md v0.3 §4.7.

Covers ``MAC-T-CYCLE-SEC-01/02``. Arch §6.2 ``GATE_SECTION_ROUTES`` is
frozen — the binary snapshot at
``tests/mac/cycle/snapshots/gate_section_routes_v0_1.bin`` is the contract.

Anchors:
  - mac/architecture.md §6.1 12-Gate Catalog (R1..R12 names)
  - mac/architecture.md §6.2 GATE_SECTION_ROUTES + TRIZ-2 + TRIZ-3 properties
"""

from __future__ import annotations

from pathlib import Path

import pytest

from praxis.kernel.mac.cycle.section_router import (
    GATE_SECTION_ROUTES,
    SectionSelector,
    route_for,
    serialize_routes_to_binary,
)


_SNAPSHOT_PATH = (
    Path(__file__).resolve().parent / "snapshots" / "gate_section_routes_v0_1.bin"
)


@pytest.mark.critical
@pytest.mark.mac_gate_calibration
def test_mac_t_cycle_sec_01_section_router_invocation() -> None:
    """MAC-T-CYCLE-SEC-01 — section router returns the arch §6.2 routing.

    For each R1..R12 gate, :func:`route_for` returns the exact tuple
    defined in arch §6.2 ``GATE_SECTION_ROUTES``. Also asserts the two
    critical TRIZ properties from arch §6.2:

      - R6 receives L1 only (TRIZ-2 resolution)
      - R9 receives FINDINGS only (TRIZ-3 resolution;
        [STEELMAN] + [DISSENT] explicitly exempt)
    """
    expected: dict[str, tuple[SectionSelector, ...]] = {
        "R1": (SectionSelector.FULL,),
        "R2": (SectionSelector.RECOMMENDATIONS,),
        "R3": (SectionSelector.FULL,),
        "R4": (SectionSelector.STEELMAN,),
        "R5": (SectionSelector.DISSENT,),
        "R6": (SectionSelector.L1,),
        "R7": (SectionSelector.L2,),
        "R8": (SectionSelector.RECOMMENDATIONS,),
        "R9": (SectionSelector.FINDINGS,),
        "R10": (SectionSelector.FULL,),
        "R11": (SectionSelector.L2,),
        "R12": (SectionSelector.FULL,),
    }
    for gate_id, selectors in expected.items():
        assert route_for(gate_id) == selectors
        assert GATE_SECTION_ROUTES[gate_id] == selectors

    # TRIZ-2: R6 on L1 only.
    assert GATE_SECTION_ROUTES["R6"] == (SectionSelector.L1,)
    # TRIZ-3: R9 on FINDINGS only — STEELMAN + DISSENT exempt.
    assert GATE_SECTION_ROUTES["R9"] == (SectionSelector.FINDINGS,)
    assert SectionSelector.STEELMAN not in GATE_SECTION_ROUTES["R9"]
    assert SectionSelector.DISSENT not in GATE_SECTION_ROUTES["R9"]


@pytest.mark.critical
@pytest.mark.static
def test_mac_t_cycle_sec_02_gate_section_routes_byte_equality_snapshot() -> None:
    """MAC-T-CYCLE-SEC-02 — byte-equality snapshot of arch §6.2 routing table.

    Serialize ``GATE_SECTION_ROUTES`` via :func:`serialize_routes_to_binary`
    and compare byte-for-byte against the committed binary at
    ``tests/mac/cycle/snapshots/gate_section_routes_v0_1.bin``. Any drift
    fails this test — the binary IS the contract.
    """
    assert _SNAPSHOT_PATH.exists(), (
        f"Snapshot missing at {_SNAPSHOT_PATH}; regenerate via "
        f"serialize_routes_to_binary() per arch §6.2"
    )
    committed = _SNAPSHOT_PATH.read_bytes()
    serialized = serialize_routes_to_binary()
    assert committed == serialized, (
        "GATE_SECTION_ROUTES drifted from the ratified v0.1 snapshot. "
        "Fix: regenerate the snapshot ONLY if arch §6.2 has been "
        "intentionally revised (which requires a Stage 5 architecture "
        "revision — not a fix-the-test hotpatch)."
    )
