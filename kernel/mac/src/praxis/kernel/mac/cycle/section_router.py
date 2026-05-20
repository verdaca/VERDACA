"""Section-aware gate router — arch §6.2 Req-B routing.

The :data:`GATE_SECTION_ROUTES` mapping is the single source of truth for
how each R1–R12 gate projects its evaluation against the producer output.
Frozen per arch §6.2; any change is a Stage 5 architecture revision and
requires regenerating ``gate_section_routes_v0_1.bin`` via
:func:`serialize_routes_to_binary`.

Critical Req-B properties (arch §6.2):
  - R6 receives L1 only — TRIZ-2 resolution
  - R9 receives FINDINGS only — TRIZ-3 resolution (STEELMAN + DISSENT exempt)
  - R2, R8 receive RECOMMENDATIONS — arch §6.2

Binding anchors:
  - mac/architecture.md §6.1 12-Gate Catalog (R1..R12 ratified names)
  - mac/architecture.md §6.2 GATE_SECTION_ROUTES + TRIZ-2 + TRIZ-3
  - mac/architecture.md §6.3 Req-C co-eval pairs (reference)
  - mac/quality-rubric.md §6 (upstream authority)
"""

from __future__ import annotations

from enum import Enum
from typing import Mapping


class SectionSelector(str, Enum):
    """The eight Req-B routing targets per arch §6.2 ``GATE_SECTION_ROUTES``.

    ``FULL`` is the whole document; ``L1`` is the executive summary layer;
    ``L2`` is the main analysis body; the others are labeled Req-A sections
    (arch §3.3).
    """

    FULL = "FULL"
    L1 = "L1"
    L2 = "L2"
    FINDINGS = "FINDINGS"
    RECOMMENDATIONS = "RECOMMENDATIONS"
    STEELMAN = "STEELMAN"
    DISSENT = "DISSENT"
    SCENARIOS = "SCENARIOS"


# =============================================================================
# The frozen routing table (arch §6.2)
# =============================================================================
#
# FROZEN. Any change requires a Stage 5 architecture revision.
# Byte-equality snapshot at tests/mac/cycle/snapshots/gate_section_routes_v0_1.bin
# is the contract; MAC-T-CYCLE-SEC-02 enforces equality at PR-gate time.
#
# Critical Req-B properties (arch §6.2):
#   - R6 → L1 ONLY (TRIZ-2 resolution)
#   - R9 → FINDINGS ONLY (TRIZ-3 resolution; [STEELMAN] + [DISSENT] explicitly exempt)
# =============================================================================


GATE_SECTION_ROUTES: Mapping[str, tuple[SectionSelector, ...]] = {
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
"""Per arch §6.2 (lines 702–715) GATE_SECTION_ROUTES verbatim. Do NOT edit
without a corresponding arch §6.2 revision + snapshot regeneration."""


def serialize_routes_to_binary() -> bytes:
    """Generate the byte-equality snapshot for ``MAC-T-CYCLE-SEC-02``.

    The binary format is deterministic: UTF-8 encoding of the gate IDs in
    R1..R12 order, each followed by a ``|``-delimited list of selector
    values and a newline. This keeps the snapshot human-readable on
    inspection while still supporting byte-equality comparison.
    """
    lines: list[str] = []
    for n in range(1, 13):
        gate_id = f"R{n}"
        selectors = GATE_SECTION_ROUTES[gate_id]
        selector_str = "|".join(s.value for s in selectors)
        lines.append(f"{gate_id}={selector_str}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def route_for(gate_id: str) -> tuple[SectionSelector, ...]:
    """Return the section selectors for ``gate_id``.

    Raises ``KeyError`` if ``gate_id`` is not in R1..R12 (R13 is deferred
    per arch §3.5 / SQ-3).
    """
    return GATE_SECTION_ROUTES[gate_id]


__all__: tuple[str, ...] = (
    "GATE_SECTION_ROUTES",
    "SectionSelector",
    "route_for",
    "serialize_routes_to_binary",
)
