"""OQ-TS-9 allow-list meta-test — mac/test-strategy.md v0.3 §13.3 (Decision 2).

**This is the cross-stage ``no_waiver`` discipline enforcer.** It walks
the full pytest collection at test execution time, gathers every test
node carrying ``@pytest.mark.no_waiver``, and asserts the set is
exactly equal to :data:`NO_WAIVER_ALLOWLIST` minus any entries that
live outside the local collection scope (cross-tree Runtime entries —
see :data:`CROSS_TREE_ALLOWLIST` below).

**Self-referential bootstrap (v0.3 §13.3.4):** this meta-test carries
``@pytest.mark.no_waiver`` itself and is entry #16 in the allow-list.
Without the self-reference, a PR could strip ``no_waiver`` from this
function and the meta-test would still pass (because allow-list
enforcement would be disabled), but the other 15 entries would be
unenforced — silent weakening. With the self-reference, stripping
``no_waiver`` makes the meta-test NOT collect as ``no_waiver``, BUT
entry #16 is expected to be present, so ``missing == {entry_16}``
and the meta-test fails. The self-reference is a fixed-point — the
meta-test is its own enforcer.

**Cross-tree note (constraint #9 from step-6 go signal):** entries
#1–#3 reference ``tests/runtime/...`` paths that live in the praxis-
runtime monorepo, not in the MAC monorepo. When this meta-test runs
within the MAC pytest session, those tests are NOT in
``request.session.items``. The local enforcement skips them; full
cross-tree enforcement happens at deployment time when MAC + Runtime
are co-installed. The entries are documented here for audit
completeness.

**PENDING AUDIT (entries #2 and #3):** the two OTEL exporter entries
are tagged ``provisionally_grandfathered`` per v0.3 §13.3.5 — added
by Amelia at Stage 4.3 without Pipeline ratification. Audit
resolution is **Andrey's decision at 5.5 Alignment Review** — not
Amelia's, not Murat's, not Winston's. **No agent is authorized to
remove the provisional tag without Andrey's explicit ratification.**

Binding anchors:
  - mac/test-strategy.md v0.3 §13.3 OQ-TS-9 Allow-List Meta-Test
  - mac/test-strategy.md v0.3 §13.3.2 Implementation target (this file)
  - mac/test-strategy.md v0.3 §13.3.3 Allow-list contents enumerated
  - mac/test-strategy.md v0.3 §13.3.4 Self-referential bootstrap property
  - mac/test-strategy.md v0.3 §13.3.5 Retroactive Inventory (3 Runtime entries)
  - mac/test-strategy.md v0.3 §13.3.6 Meta-test spec
"""

from __future__ import annotations

import pytest


# =============================================================================
# 16-entry NO_WAIVER_ALLOWLIST — verbatim transcription from v0.3 §13.3.2
# =============================================================================
#
# DO NOT add, remove, or reorder entries without explicit team-lead
# ratification + a v0.4 test-strategy amendment + Murat re-ratification.
# The 16-entry count is locked per §13.3.3.1 Option 1 ratification
# 2026-04-14. Adding a 17th entry is OUT OF SCOPE for any Amelia
# session — it requires the full ratification chain.
#
# Q-1 rename (entries #12 and #13): v0.3 ratified the function name
# change from ``test_mac_t_gate_r{11,12}_05_hard_fail_*`` to
# ``test_mac_t_gate_r11_05_scenario_coverage_property`` /
# ``test_mac_t_gate_r12_05_direct_contradiction_detector``. Canonical
# allow-list IDs ``MAC-T-GATE-R11-05`` / ``MAC-T-GATE-R12-05`` are
# preserved; only the Python nodeid strings change.
# =============================================================================


NO_WAIVER_ALLOWLIST: frozenset[str] = frozenset({
    # --- Entry 1 — Runtime ratified (cross-tree; not in MAC monorepo collection) ---
    "tests/runtime/outbox/test_path_a_atomicity.py::test_f13_c1_xmin_identity_proof",

    # --- Entries 2, 3 — Runtime R53 structural privacy enforcement (RATIFIED at 5.5 Alignment Review 2026-04-15) ---
    # Audit complete. Both tests are pure Pydantic validator assertions with zero
    # external state, enforcing R53 (forbidden TelemetryEvent fields `query_content`
    # and `embedding` rejected at construction). Runtime arch §6.1.8 + §9.10 + §10.5
    # classify otel-exporter-mcp as Class-A blast radius + R53 structural control +
    # S4.R-05 no-waiver. Tests meet Stage 5.2 Decision 1 "deterministic invariants
    # only" criterion unambiguously. Added to allow-list at Stage 4.3 by Amelia;
    # ratification ceremony completed at Stage 5.5 per mac/alignment-review.md §8.
    "tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 41>",  # ratified 2026-04-15
    "tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 62>",  # ratified 2026-04-15

    # --- Entries 4–13 — 10 MAC gate calibration / structural tests (Decision 1) ---
    "tests/mac/gates/test_r1.py::test_mac_t_gate_r1_02_calibration_anchor",                       # entry #4
    "tests/mac/gates/test_r2.py::test_mac_t_gate_r2_02_calibration_anchor",                       # entry #5
    "tests/mac/gates/test_r3.py::test_mac_t_gate_r3_02_calibration_anchor",                       # entry #6
    "tests/mac/gates/test_r4.py::test_mac_t_gate_r4_02_calibration_anchor",                       # entry #7
    "tests/mac/gates/test_r5.py::test_mac_t_gate_r5_02_calibration_anchor",                       # entry #8
    "tests/mac/gates/test_r7.py::test_mac_t_gate_r7_02_calibration_anchor",                       # entry #9
    "tests/mac/gates/test_r8.py::test_mac_t_gate_r8_02_calibration_anchor",                       # entry #10
    "tests/mac/gates/test_r11.py::test_mac_t_gate_r11_02_calibration_anchor",                     # entry #11
    "tests/mac/gates/test_r11.py::test_mac_t_gate_r11_05_scenario_coverage_property",             # entry #12 (Q-1 rename)
    "tests/mac/gates/test_r12.py::test_mac_t_gate_r12_05_direct_contradiction_detector",          # entry #13 (Q-1 rename)

    # --- Entries 14, 15 — 2 MAC split deterministic carriers (Decision 1 items 9 + 11) ---
    "tests/mac/asymmetry/test_req_f.py::test_mac_t_asym_r_f_02_field_ordering_deterministic",     # entry #14
    "tests/mac/adversarial/test_persona_3.py::test_mac_t_adv_p3_01_fixture_inventory_deterministic",  # entry #15

    # --- Entry 16 — self-reference (bootstrap self-enclosure, v0.3 §13.3.4) ---
    "tests/static/runtime/test_no_waiver_inventory.py::test_mac_t_meta_no_waiver_inv_01_allowlist_check",
})
"""The 16 ratified ``no_waiver`` test nodeids per v0.3 §13.3.2.
**RATIFIED 2026-04-14 via §13.3.3.1 Option 1.** Do not modify."""


CROSS_TREE_ALLOWLIST: frozenset[str] = frozenset({
    # Entries 1–3 live in the praxis-runtime monorepo, not the MAC
    # monorepo. They are not collected when this meta-test runs within
    # MAC's pytest scope. Full cross-tree enforcement happens at
    # deployment-time pytest collection across both monorepos.
    "tests/runtime/outbox/test_path_a_atomicity.py::test_f13_c1_xmin_identity_proof",
    "tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 41>",
    "tests/runtime/tools/test_otel_exporter_mcp_contract.py::<function at line 62>",
})
"""Subset of :data:`NO_WAIVER_ALLOWLIST` whose tests live OUTSIDE the
MAC monorepo. The meta-test enforces the LOCAL subset
(``NO_WAIVER_ALLOWLIST - CROSS_TREE_ALLOWLIST``) against the local
pytest collection. Cross-tree enforcement is verified at deployment
time when MAC + Runtime are co-installed."""


LOCAL_ALLOWLIST: frozenset[str] = NO_WAIVER_ALLOWLIST - CROSS_TREE_ALLOWLIST
"""The 13 ``no_waiver`` test nodeids that MUST be present in the
local MAC pytest collection (entries #4–#16)."""


def _normalize_nodeid(nodeid: str) -> str:
    """Convert pytest's platform-native nodeid to canonical
    forward-slash form for comparison against :data:`NO_WAIVER_ALLOWLIST`.
    """
    return nodeid.replace("\\", "/")


@pytest.mark.no_waiver  # entry #16 — self-referential bootstrap (v0.3 §13.3.4)
@pytest.mark.critical
@pytest.mark.static
def test_mac_t_meta_no_waiver_inv_01_allowlist_check(request: pytest.FixtureRequest) -> None:
    """MAC-T-META-NO-WAIVER-INV-01 — allow-list enforcement at session time.

    Walks ``request.session.items`` for every test carrying the
    ``no_waiver`` marker, computes the local-collection set, and
    asserts it equals :data:`LOCAL_ALLOWLIST`.

    On unauthorized addition: ``unauthorized = collected - LOCAL_ALLOWLIST``
    is non-empty → AssertionError lists the offending nodeids.

    On silent removal: ``missing = LOCAL_ALLOWLIST - collected`` is
    non-empty → AssertionError lists the missing entries.

    Self-referential lock: this test's own nodeid is entry #16. If a
    PR strips ``@pytest.mark.no_waiver`` from this function, the
    function no longer collects as ``no_waiver``, ``collected`` is
    missing entry #16, and the test fails. The meta-test is its own
    enforcer.
    """
    collected_no_waiver_ids: set[str] = set()
    for item in request.session.items:
        if item.get_closest_marker("no_waiver") is not None:
            collected_no_waiver_ids.add(_normalize_nodeid(item.nodeid))

    unauthorized = collected_no_waiver_ids - LOCAL_ALLOWLIST
    missing = LOCAL_ALLOWLIST - collected_no_waiver_ids

    errors: list[str] = []
    if unauthorized:
        errors.append(
            "Unauthorized no_waiver tests (not in 16-entry allow-list "
            "per v0.3 §13.3.2):\n  - "
            + "\n  - ".join(sorted(unauthorized))
        )
    if missing:
        errors.append(
            "Allow-list entries missing from local pytest collection "
            "(silent removal? function rename without allow-list update?):\n  - "
            + "\n  - ".join(sorted(missing))
        )

    if errors:
        raise AssertionError(
            "OQ-TS-9 allow-list meta-test FAILED:\n\n"
            + "\n\n".join(errors)
            + "\n\nResolution path:\n"
            + "  - For unauthorized additions: remove the @pytest.mark.no_waiver\n"
            + "    decorator OR request team-lead ratification + v0.4 amendment.\n"
            + "  - For silent removals: restore the test or update the allow-list\n"
            + "    in the SAME PR per v0.3 §13.3.7 Operational Procedures."
        )


# Sanity check — a regular non-no_waiver test that verifies the
# allow-list constants themselves. This test does NOT carry no_waiver
# (it's not in the 16-entry ratified set); it's a coverage-floor
# check on the constants.
def test_no_waiver_allowlist_has_exactly_sixteen_entries() -> None:
    """Coverage-floor test, no MAC-T ID; flagged for 5.4 Quinn QA review per
    Stage 5.3 preload Q3 disposition 2026-04-14.
    """
    assert len(NO_WAIVER_ALLOWLIST) == 16, (
        f"NO_WAIVER_ALLOWLIST must have exactly 16 entries per v0.3 §13.3.3.1 "
        f"Option 1 ratification; got {len(NO_WAIVER_ALLOWLIST)}"
    )
    assert len(CROSS_TREE_ALLOWLIST) == 3
    assert len(LOCAL_ALLOWLIST) == 13
    # Local + cross-tree partition the full allow-list with no overlap.
    assert NO_WAIVER_ALLOWLIST == LOCAL_ALLOWLIST | CROSS_TREE_ALLOWLIST
    assert LOCAL_ALLOWLIST.isdisjoint(CROSS_TREE_ALLOWLIST)
