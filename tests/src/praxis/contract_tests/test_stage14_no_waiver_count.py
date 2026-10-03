"""Stage 14 strict runtime no_waiver and cumulative AST-gate inventory checks.

Builds on Stage 13's tree-walk discovery; recognizes Stage 13 + Stage 14 markers
as canonical. Stage 14 NEW: 1 runtime marker (M-T-AUTH-JWKS-ROTATION-INVARIANT-01)
+ 3 AST gates (A-S14, B-S14, C-S14). Cumulative AST gates = 9 (Stage 13 A-F
preserved + Stage 14 A-S14/B-S14/C-S14). Canonical pin: 14 / 3 NEW / 23.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

from praxis.contract_tests.test_stage13_no_waiver_count import (
    CONTRACT_TESTS_ROOT,
    PRE_STAGE13_MARKER_PATHS,
    STAGE_13_AST_GATE_IDS,
    STAGE_13_RUNTIME_NO_WAIVER_ADDS,
    STAGE_13_RUNTIME_NO_WAIVER_IDS,
    _format_path,
    _has_no_waiver_marker,
)

STAGE_14_RUNTIME_NO_WAIVER_ADDS: Final[frozenset[str]] = frozenset(
    {
        "M-T-AUTH-JWKS-ROTATION-INVARIANT-01",
    }
)
STAGE_14_RUNTIME_NO_WAIVER_IDS: Final[frozenset[str]] = (
    STAGE_13_RUNTIME_NO_WAIVER_IDS | STAGE_14_RUNTIME_NO_WAIVER_ADDS
)
STAGE_14_AST_GATE_IDS: Final[frozenset[str]] = frozenset(
    {
        "gate_a_s14_jwks_wired_in_oidc_policy",
        "gate_b_s14_no_double_decode_and_no_channel_audience_literal",
        "gate_c_s14_no_waiver_constant_pin",
    }
)
STAGE_14_CUMULATIVE_AST_GATE_IDS: Final[frozenset[str]] = (
    STAGE_13_AST_GATE_IDS | STAGE_14_AST_GATE_IDS
)

STAGE14_RUNTIME_NO_WAIVER_COUNT: Final[int] = 14
STAGE14_AST_GATE_COUNT_NEW: Final[int] = 3
STAGE14_CUMULATIVE_AST_GATE_COUNT: Final[int] = 9
TOTAL_ENFORCED_MARKERS: Final[int] = 23

# Stage 14 walks the entire contract_tests/ subtree (subtracting Stage 9-12
# baselines only). Stage 14 marker files (test_oidc_policy_construction.py
# extension + test_ast_gates_stage14.py + this enforcer) ARE walked here.
EXCLUSIONS: Final[frozenset[Path]] = PRE_STAGE13_MARKER_PATHS

# Functions that ARE @pytest.mark.no_waiver in the enforcer file itself
# (this file) — must be skipped to avoid self-reference recursion.
SELF_REF_FILE: Final[Path] = (
    CONTRACT_TESTS_ROOT / "test_stage14_no_waiver_count.py"
)


def _is_excluded(path: Path) -> bool:
    resolved = path.resolve()
    for excluded in EXCLUSIONS:
        try:
            if resolved == excluded.resolve():
                return True
        except (OSError, RuntimeError):
            continue
    try:
        if resolved == SELF_REF_FILE.resolve():
            return True
    except (OSError, RuntimeError):
        pass
    return False


def _canonical_id(function_name: str) -> str | None:
    """Extended canonicalizer covering Stage 13 + Stage 14 markers."""
    if function_name.startswith("test_"):
        possible_gate = function_name.removeprefix("test_")
        if possible_gate in STAGE_14_CUMULATIVE_AST_GATE_IDS:
            return possible_gate
    cumulative_runtime_adds = (
        STAGE_13_RUNTIME_NO_WAIVER_ADDS | STAGE_14_RUNTIME_NO_WAIVER_ADDS
    )
    for mac_t_id in cumulative_runtime_adds:
        prefix = "test_" + mac_t_id.replace("-", "_")
        if function_name.startswith(prefix):
            return mac_t_id
    return None


def collect_stage14_runtime_no_waiver_ids(
    test_tree_root: Path = CONTRACT_TESTS_ROOT,
) -> set[str]:
    """Tree-walk contract_tests/ recognizing Stage 13 + Stage 14 markers."""
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
        raise AssertionError(
            "Unratified Stage 13/14 no_waiver tests:\n" + "\n".join(unknown)
        )
    return collected


def test_stage14_runtime_no_waiver_allowlist_has_exactly_fourteen_entries() -> None:
    assert len(STAGE_14_RUNTIME_NO_WAIVER_IDS) == STAGE14_RUNTIME_NO_WAIVER_COUNT


def test_stage14_cumulative_ast_gate_count_is_nine() -> None:
    assert (
        len(STAGE_14_CUMULATIVE_AST_GATE_IDS) == STAGE14_CUMULATIVE_AST_GATE_COUNT
    )


def test_stage14_new_ast_gate_count_is_three() -> None:
    assert len(STAGE_14_AST_GATE_IDS) == STAGE14_AST_GATE_COUNT_NEW


def test_stage14_total_enforced_markers_is_twenty_three() -> None:
    assert (
        STAGE14_RUNTIME_NO_WAIVER_COUNT + STAGE14_CUMULATIVE_AST_GATE_COUNT
        == TOTAL_ENFORCED_MARKERS
    )


def test_stage14_new_no_waiver_inventory_matches_runtime_and_gate_additions() -> None:
    observed = collect_stage14_runtime_no_waiver_ids()

    expected = (
        STAGE_13_RUNTIME_NO_WAIVER_ADDS
        | STAGE_14_RUNTIME_NO_WAIVER_ADDS
        | STAGE_13_AST_GATE_IDS
        | STAGE_14_AST_GATE_IDS
    )
    assert observed == expected


def test_M_T_STAGE14_NO_WAIVER_DISCOVERY_DRIFT_01_synthetic_marker_raises(
    tmp_path: Path,
) -> None:
    """Synthetic drift canary: an unratified @no_waiver marker in scanned scope
    must surface as AssertionError (preserves Stage 13 V2.D drift-detection)."""
    drift_file = tmp_path / "test_synthetic_stage14_drift.py"
    drift_file.write_text(
        "import pytest\n"
        "\n"
        "\n"
        "@pytest.mark.no_waiver\n"
        "def test_M_T_SYNTHETIC_STAGE14_UNRATIFIED_01_drift_canary() -> None:\n"
        "    pass\n",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="Unratified Stage 13/14 no_waiver tests"):
        collect_stage14_runtime_no_waiver_ids(test_tree_root=tmp_path)
