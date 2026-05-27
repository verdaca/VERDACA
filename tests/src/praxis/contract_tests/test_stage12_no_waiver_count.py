"""Stage 12 strict no_waiver allow-list equality check."""

from __future__ import annotations

import ast
from pathlib import Path

STAGE_12_NO_WAIVER_IDS = frozenset(
    {
        "M-T-TEAMS-WEBHOOK-HMAC-TAMPERED-01",
        "M-T-SLACK-WEBHOOK-SIGNING-TAMPERED-01",
        "M-T-TEAMS-CHANNEL-ADAPTER-PORT-CONTRACT-01",
        "M-T-SLACK-CHANNEL-ADAPTER-PORT-CONTRACT-01",
        "M-T-AUTH-JWT-ALG-PIN-01",
        "M-T-AUTH-NONCE-REPLAY-BLOCK-01",
        "M-T-AUTH-CLAIMS-SCHEMA-01",
        "M-T-VKEY-BUDGET-EXHAUSTED-01",
        "M-T-AUTH-KERNEL-NO-ADAPTER-IMPORT-01",
    }
)
RATIFIED_COUNT = 9

_EXPECTED_PREFIXES = {
    "test_" + mac_t_id.replace("-", "_"): mac_t_id for mac_t_id in STAGE_12_NO_WAIVER_IDS
}

_STAGE12_TEST_ROOTS = (
    Path("tests/src/praxis/adapters/channels"),
    Path("tests/src/praxis/adapters/litellm"),
    Path("tests/src/praxis/kernel/auth"),
    Path("tests/src/praxis/contract_tests/test_stage12_ast_gates.py"),
)


def _has_no_waiver_marker(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Attribute) and decorator.attr == "no_waiver":
            value = decorator.value
            if isinstance(value, ast.Attribute) and value.attr == "mark":
                if isinstance(value.value, ast.Name) and value.value.id == "pytest":
                    return True
    return False


def _canonical_stage12_id(function_name: str) -> str | None:
    for prefix, mac_t_id in _EXPECTED_PREFIXES.items():
        if function_name.startswith(prefix):
            return mac_t_id
    return None


def _is_stage12_test_path(path: Path) -> bool:
    normalized = Path(path.as_posix())
    for root in _STAGE12_TEST_ROOTS:
        if root.suffix:
            if normalized == root:
                return True
            continue
        if normalized == root or root in normalized.parents:
            return True
    return False


def collect_stage12_no_waiver_ids() -> set[str]:
    collected: set[str] = set()
    unknown: list[str] = []
    for path in Path("tests/src/praxis").rglob("test_*.py"):
        if not _is_stage12_test_path(path):
            continue
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(module):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if not _has_no_waiver_marker(node):
                continue
            mac_t_id = _canonical_stage12_id(node.name)
            if mac_t_id is None:
                unknown.append(f"{path.as_posix()}::{node.name}")
            else:
                collected.add(mac_t_id)
    if unknown:
        raise AssertionError("Unratified Stage 12 no_waiver tests:\n" + "\n".join(unknown))
    return collected


def test_stage12_no_waiver_allowlist_has_exactly_nine_entries() -> None:
    assert len(STAGE_12_NO_WAIVER_IDS) == RATIFIED_COUNT


def test_stage12_no_waiver_inventory_matches_allowlist() -> None:
    assert collect_stage12_no_waiver_ids() == STAGE_12_NO_WAIVER_IDS
