"""Stage-9 no_waiver inventory lock.

DO NOT add/remove/reorder without team-lead ratification, a test-strategy
amendment, and Murat re-ratification.

An entry is a no_waiver-bearing test FUNCTION. Parametrized functions contribute
one entry; trailing [param] variants are normalized in the inventory match.
Cross-regime summing is forbidden: the MAC 16-entry regime is separate.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Pytest node IDs are relative to the praxis-contract-tests root (`tests/`),
# so this lock intentionally uses `src/...` paths.
MEMORY_CONTRACT = "src/praxis/contract_tests/ports/test_memory_contract.py"
SERIALIZATION_CONTRACT = "src/praxis/contract_tests/ports/test_serialization_contract.py"
COMPACTION_CONTRACT = "src/praxis/contract_tests/ports/test_compaction_contract.py"
SESSION_INDEX_CONTRACT = (
    "src/praxis/contract_tests/ports/test_session_index_port_contract.py"
)
SKILL_TELEMETRY_CONTRACT = (
    "src/praxis/contract_tests/ports/test_skill_telemetry_port_contract.py"
)

PROMO_01 = f"{MEMORY_CONTRACT}::test_M_T_MEM_PROMO_01_threshold_violation"
PROMO_02 = (
    f"{MEMORY_CONTRACT}::test_M_T_MEM_PROMO_02_idempotent_promotion_durable"
)
PROMO_03 = f"{MEMORY_CONTRACT}::test_M_T_MEM_PROMO_03_otel_span_attribute_set"
PROMO_04 = f"{MEMORY_CONTRACT}::test_M_T_MEM_PROMO_04_revocation_slo"
SER_EVO_01 = (
    f"{SERIALIZATION_CONTRACT}::test_M_T_SER_EVO_01_can_decode_version_forward"
)
SER_FUZZ_01 = f"{SERIALIZATION_CONTRACT}::test_M_T_SER_FUZZ_01_fuzz_roundtrip"
COMP_BUDGET_01 = (
    f"{COMPACTION_CONTRACT}::test_M_T_COMP_BUDGET_UNREACHABLE_01_lossless_overflow"
)
COMP_PRESERVED_01 = (
    f"{COMPACTION_CONTRACT}::"
    "test_M_T_COMP_PRESERVED_EVICTED_01_preserved_span_invariant"
)
COMP_DETERM_01 = (
    f"{COMPACTION_CONTRACT}::test_M_T_COMP_DETERM_VIOLATION_01_caller_raised_shape"
)

STAGE9_NO_WAIVER_ALLOWLIST: frozenset[str] = frozenset(
    {
        PROMO_01,
        PROMO_02,
        PROMO_03,
        PROMO_04,
        SER_EVO_01,
        SER_FUZZ_01,
        COMP_BUDGET_01,
        COMP_PRESERVED_01,
        COMP_DETERM_01,
    }
)

SESSIONIDX_LIST_01 = (
    f"{SESSION_INDEX_CONTRACT}::"
    "test_M_T_SESSIONIDX_LIST_01_returns_records_for_empty_and_populated_store"
)
SESSIONIDX_GET_01 = (
    f"{SESSION_INDEX_CONTRACT}::"
    "test_M_T_SESSIONIDX_GET_01_known_id_returns_record_with_dto_fields"
)
SESSIONIDX_SEARCH_01 = (
    f"{SESSION_INDEX_CONTRACT}::"
    "test_M_T_SESSIONIDX_SEARCH_01_keyword_uses_fts5_and_returns_scored_excerpts"
)
SKILLTEL_EMIT_01 = (
    f"{SKILL_TELEMETRY_CONTRACT}::"
    "test_M_T_SKILLTEL_EMIT_01_record_invocation_returns_stable_observation_id"
)

STAGE10_DELTA_NO_WAIVER_ALLOWLIST: frozenset[str] = frozenset(
    {
        SESSIONIDX_LIST_01,
        SESSIONIDX_GET_01,
        SESSIONIDX_SEARCH_01,
        SKILLTEL_EMIT_01,
    }
)

STAGE10_NO_WAIVER_ALLOWLIST: frozenset[str] = frozenset(
    {*STAGE9_NO_WAIVER_ALLOWLIST, *STAGE10_DELTA_NO_WAIVER_ALLOWLIST}
)

STAGE10_INVENTORY_CONTRACTS: tuple[str, ...] = (
    MEMORY_CONTRACT,
    SERIALIZATION_CONTRACT,
    COMPACTION_CONTRACT,
    SESSION_INDEX_CONTRACT,
    SKILL_TELEMETRY_CONTRACT,
)

EXPECTED_PARAM_VARIANTS: dict[str, frozenset[str]] = {
    PROMO_02: frozenset(
        {
            f"{PROMO_02}[mem0]",
            f"{PROMO_02}[letta]",
        }
    )
}


def collect_no_waiver_nodeids() -> set[str]:
    """Collect the full contract-test tree when this file is run standalone."""
    tests_root = Path(__file__).resolve().parents[4]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "src/praxis/contract_tests/ports",
            "--collect-only",
            "-q",
            "-m",
            "no_waiver",
        ],
        cwd=tests_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.startswith("src/") and "::" in line
    }


def strip_param(nodeid: str) -> str:
    """Strip one trailing pytest [param] suffix without touching earlier '['."""
    return nodeid.rsplit("[", 1)[0]


def is_stage10_inventory_nodeid(nodeid: str) -> bool:
    return any(nodeid.startswith(contract) for contract in STAGE10_INVENTORY_CONTRACTS)


def test_stage9_no_waiver_allowlist_cardinality() -> None:
    assert len(STAGE9_NO_WAIVER_ALLOWLIST) == 9


@pytest.mark.parametrize(
    ("nodeid", "expected"),
    [
        (
            "tests/src/praxis/contract_tests/ports/test_x.py::test_plain",
            "tests/src/praxis/contract_tests/ports/test_x.py::test_plain",
        ),
        (
            "tests/src/praxis/contract_tests/ports/test_x.py::test_param[mem0]",
            "tests/src/praxis/contract_tests/ports/test_x.py::test_param",
        ),
        ("a/b[x]/t.py::test_f[mem0]", "a/b[x]/t.py::test_f"),
    ],
)
def test_strip_param(nodeid: str, expected: str) -> None:
    assert strip_param(nodeid) == expected


def test_stage9_no_waiver_inventory_matches_allowlist(request: pytest.FixtureRequest) -> None:
    observed = {
        item.nodeid
        for item in request.session.items
        if item.get_closest_marker("no_waiver") is not None
    } or collect_no_waiver_nodeids()
    normalized = {
        strip_param(nodeid) for nodeid in observed if is_stage10_inventory_nodeid(nodeid)
    }

    assert normalized & STAGE9_NO_WAIVER_ALLOWLIST == STAGE9_NO_WAIVER_ALLOWLIST

    for base_nodeid, expected_variants in EXPECTED_PARAM_VARIANTS.items():
        actual_variants = {
            nodeid for nodeid in observed if strip_param(nodeid) == base_nodeid
        }
        assert actual_variants == expected_variants


def test_stage10_no_waiver_inventory_matches_allowlist(request: pytest.FixtureRequest) -> None:
    observed = {
        item.nodeid
        for item in request.session.items
        if item.get_closest_marker("no_waiver") is not None
    } or collect_no_waiver_nodeids()
    normalized = {
        strip_param(nodeid) for nodeid in observed if is_stage10_inventory_nodeid(nodeid)
    }

    assert len(STAGE10_NO_WAIVER_ALLOWLIST) <= 13
    assert len(STAGE10_DELTA_NO_WAIVER_ALLOWLIST) <= 4
    assert STAGE9_NO_WAIVER_ALLOWLIST <= STAGE10_NO_WAIVER_ALLOWLIST
    assert all("::test_M_T_" in nodeid for nodeid in STAGE10_NO_WAIVER_ALLOWLIST)
    assert normalized == STAGE10_NO_WAIVER_ALLOWLIST
