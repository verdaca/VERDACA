"""Stage 13 strict runtime no_waiver and AST-gate inventory checks."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from praxis.contract_tests.test_stage12_no_waiver_count import STAGE_12_NO_WAIVER_IDS

ROOT = Path(__file__).parents[4]

STAGE_13_RUNTIME_NO_WAIVER_ADDS = frozenset(
    {
        "M-T-GATEWAY-EXECUTE-AUTH-FIRST-01",
        "M-T-AUTH-NONCE-PERSISTENCE-RESTART-01",
        "M-T-SESSION-ID-ENTROPY-FLOOR-01",
        "M-T-NO-BARE-EXCEPT-AUTH-CRYPTO-01",
    }
)
STAGE_13_RUNTIME_NO_WAIVER_IDS = STAGE_12_NO_WAIVER_IDS | STAGE_13_RUNTIME_NO_WAIVER_ADDS
STAGE_13_AST_GATE_IDS = frozenset(
    {
        "gate_a_extract_claims_no_none_default",
        "gate_b_oidc_policy_verifier_required",
        "gate_c_build_gateway_full_deps",
        "gate_d_nonce_store_sqlite_invariants",
        "gate_e_session_id_min_width",
        "gate_f_close_memo_tracking_symmetry",
    }
)
RUNTIME_RATIFIED_COUNT = 13
AST_GATE_RATIFIED_COUNT = 6
TOTAL_ENFORCED_MARKERS = 19

CONTRACT_TESTS_ROOT = ROOT / "tests" / "src" / "praxis" / "contract_tests"

PRE_STAGE13_MARKER_PATHS: frozenset[Path] = frozenset(
    {
        CONTRACT_TESTS_ROOT / "test_stage12_ast_gates.py",
        CONTRACT_TESTS_ROOT / "ports" / "test_compaction_contract.py",
        CONTRACT_TESTS_ROOT / "ports" / "test_cost_meter_contract.py",
        CONTRACT_TESTS_ROOT / "ports" / "test_llm_proxy_contract.py",
        CONTRACT_TESTS_ROOT / "ports" / "test_memory_contract.py",
        CONTRACT_TESTS_ROOT / "ports" / "test_serialization_contract.py",
        CONTRACT_TESTS_ROOT / "ports" / "test_session_index_port_contract.py",
        CONTRACT_TESTS_ROOT / "ports" / "test_skill_telemetry_port_contract.py",
        CONTRACT_TESTS_ROOT / "ports" / "test_versioned_state_contract.py",
    }
)

EXCLUSIONS: frozenset[Path] = PRE_STAGE13_MARKER_PATHS


def _format_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _is_excluded(path: Path) -> bool:
    resolved = path.resolve()
    for excluded in EXCLUSIONS:
        try:
            if resolved == excluded.resolve():
                return True
        except (OSError, RuntimeError):
            continue
    return False


def _has_no_waiver_marker(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Attribute) and decorator.attr == "no_waiver":
            value = decorator.value
            if isinstance(value, ast.Attribute) and value.attr == "mark":
                if isinstance(value.value, ast.Name) and value.value.id == "pytest":
                    return True
    return False


def _canonical_id(function_name: str) -> str | None:
    if function_name.startswith("test_"):
        possible_gate = function_name.removeprefix("test_")
        if possible_gate in STAGE_13_AST_GATE_IDS:
            return possible_gate
    for mac_t_id in STAGE_13_RUNTIME_NO_WAIVER_ADDS:
        prefix = "test_" + mac_t_id.replace("-", "_")
        if function_name.startswith(prefix):
            return mac_t_id
    return None


def collect_stage13_new_no_waiver_ids(
    test_tree_root: Path = CONTRACT_TESTS_ROOT,
) -> set[str]:
    collected: set[str] = set()
    unknown: list[str] = []
    for path in sorted(test_tree_root.rglob("test_*.py")):
        if _is_excluded(path):
            continue
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(module):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if not _has_no_waiver_marker(node):
                continue
            identifier = _canonical_id(node.name)
            if identifier is None:
                unknown.append(f"{_format_path(path)}::{node.name}")
            else:
                collected.add(identifier)
    if unknown:
        raise AssertionError("Unratified Stage 13 no_waiver tests:\n" + "\n".join(unknown))
    return collected


def test_stage13_runtime_no_waiver_allowlist_has_exactly_thirteen_entries() -> None:
    assert len(STAGE_13_RUNTIME_NO_WAIVER_IDS) == RUNTIME_RATIFIED_COUNT


def test_stage13_ast_gate_allowlist_has_exactly_six_entries() -> None:
    assert len(STAGE_13_AST_GATE_IDS) == AST_GATE_RATIFIED_COUNT


def test_stage13_new_no_waiver_inventory_matches_runtime_and_gate_additions() -> None:
    observed = collect_stage13_new_no_waiver_ids()

    assert observed == STAGE_13_RUNTIME_NO_WAIVER_ADDS | STAGE_13_AST_GATE_IDS
    assert len(STAGE_13_RUNTIME_NO_WAIVER_IDS) + len(STAGE_13_AST_GATE_IDS) == (
        TOTAL_ENFORCED_MARKERS
    )


def test_M_T_STAGE13_NO_WAIVER_DISCOVERY_DRIFT_01_synthetic_marker_raises(
    tmp_path: Path,
) -> None:
    drift_file = tmp_path / "test_synthetic_drift.py"
    drift_file.write_text(
        "import pytest\n"
        "\n"
        "\n"
        "@pytest.mark.no_waiver\n"
        "def test_M_T_SYNTHETIC_UNRATIFIED_01_drift_canary() -> None:\n"
        "    pass\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="Unratified Stage 13 no_waiver tests"):
        collect_stage13_new_no_waiver_ids(test_tree_root=tmp_path)
