"""Stage 13 strict runtime no_waiver and AST-gate inventory checks."""

from __future__ import annotations

import ast
from pathlib import Path

from praxis.contract_tests.test_stage12_no_waiver_count import STAGE_12_NO_WAIVER_IDS

ROOT = Path(__file__).parents[4]

STAGE_13_RUNTIME_NO_WAIVER_ADDS = frozenset(
    {
        "M-T-AUTH-VERIFIER-WIRED-AT-COMPOSITION-01",
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

PORTS_TEST_ROOT = ROOT / "tests" / "src" / "praxis" / "contract_tests" / "ports"

_STAGE13_ROOTS = (
    PORTS_TEST_ROOT / "test_gateway_composition_root.py",
    PORTS_TEST_ROOT / "test_nonce_store.py",
    PORTS_TEST_ROOT / "test_gateway_session_id_width.py",
    PORTS_TEST_ROOT / "test_ast_gates_stage13.py",
)


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


def collect_stage13_new_no_waiver_ids() -> set[str]:
    collected: set[str] = set()
    unknown: list[str] = []
    for path in _STAGE13_ROOTS:
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(module):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if not _has_no_waiver_marker(node):
                continue
            identifier = _canonical_id(node.name)
            if identifier is None:
                unknown.append(f"{path.relative_to(ROOT).as_posix()}::{node.name}")
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
