"""Q3 option (b) — no parallel TelemetryEvent or RuntimeTelemetryEvent types.

Architecture §9.1 / §10.4 / §16.2 / §16.4 rule 2:
  - No `class TelemetryEvent` under runtime/
  - No `class RuntimeTelemetryEvent` under runtime/

Verified via AST scan over all .py files in src/praxis/kernel/runtime/.
Test-strategy §6.5.B (AST structural guard).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

RUNTIME_SRC = Path("src/praxis/kernel/runtime")


@pytest.mark.critical
@pytest.mark.r53_structural
@pytest.mark.static
def test_no_telemetry_event_class_definition_in_runtime() -> None:
    """AST scan: no `class TelemetryEvent` defined anywhere under runtime/.

    If this test fails, someone redefined TelemetryEvent in Stage 4,
    breaking the single-source-of-truth invariant (Q3 option b).
    """
    violations = []
    for py_file in RUNTIME_SRC.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "TelemetryEvent":
                violations.append(f"{py_file}:{node.lineno}")
    assert violations == [], (
        "class TelemetryEvent found under runtime/: "
        f"{violations}. Q3 option (b) violated — Stage 4 must not redefine this type."
    )


@pytest.mark.critical
@pytest.mark.r53_structural
@pytest.mark.static
def test_no_runtime_telemetry_event_class_definition() -> None:
    """AST scan: no `class RuntimeTelemetryEvent` anywhere under runtime/.

    This parallel type is explicitly prohibited by §16.4 rule 2.
    """
    violations = []
    for py_file in RUNTIME_SRC.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "RuntimeTelemetryEvent":
                violations.append(f"{py_file}:{node.lineno}")
    assert violations == [], (
        f"class RuntimeTelemetryEvent found under runtime/: {violations}. §16.4 rule 2 violated."
    )


@pytest.mark.critical
@pytest.mark.r53_structural
@pytest.mark.static
def test_no_extra_allow_in_runtime_observability() -> None:
    """Grep: no extra='allow' in any observability/*.py file.

    extra='allow' on a Pydantic model in the observability path would
    weaken R53 from structural to trusted (§6.5.B).
    """
    obs_path = RUNTIME_SRC / "observability"
    if not obs_path.exists():
        pytest.skip("observability/ not yet created — test will be RED until impl lands")
    violations = []
    for py_file in obs_path.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for spelling in ('extra="allow"', "extra='allow'"):
            if spelling in content:
                violations.append(f"{py_file}: contains {spelling!r}")
    assert violations == [], (
        f"extra='allow' found in observability/: {violations}. "
        f"R53 structural enforcement weakened — §6.5.B violated."
    )
