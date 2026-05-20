"""S4.R-01 Layer 1 — static mypy --strict asymmetry enforcement.

Architecture §9.1.1 / §11.1.3: the FIRST line of defense against a
developer accidentally calling a producer method on a reviewer proxy is
the IDE/mypy type-checker.  These tests verify that mypy --strict emits
a specific 'has no attribute' error on synthesised fixture files that
deliberately violate ReviewerMemoryProtocol narrowing.

Test-strategy §11.1.3 / TC-03.  Fixture catalogue mirrors §11.1.3 table.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixture catalogue (path relative to repo root, error regex)
# ---------------------------------------------------------------------------

MYPY_FIXTURES = [
    ("reviewer_retrieve_similar_tasks_violation.py", r"has no attribute.*retrieve_similar_tasks"),
    ("reviewer_retrieve_decisions_violation.py", r"has no attribute.*retrieve_decisions"),
    ("reviewer_retrieve_facts_violation.py", r"has no attribute.*retrieve_facts"),
    ("reviewer_store_task_outcome_violation.py", r"has no attribute.*store_task_outcome"),
    ("reviewer_store_fact_violation.py", r"has no attribute.*store_fact"),
    ("reviewer_delete_violation.py", r"has no attribute.*delete"),
    ("reviewer_export_violation.py", r"has no attribute.*export"),
    ("reviewer_health_violation.py", r"has no attribute.*health"),
]

_RUNTIME_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = _RUNTIME_ROOT / "tests" / "fixtures" / "type_level"


@pytest.mark.critical
@pytest.mark.static
@pytest.mark.parametrize("fixture_name,expected_error_regex", MYPY_FIXTURES)
def test_mypy_strict_rejects_asymmetry_violation(
    fixture_name: str, expected_error_regex: str
) -> None:
    """§11.1.3 — mypy --strict catches the violation at dev time.

    The test passes iff mypy exits non-zero AND the output contains the
    expected 'has no attribute' error for the specific method.
    """
    fixture_path = FIXTURE_DIR / fixture_name
    import os
    import sys

    env = {**os.environ, "MYPYPATH": str((_RUNTIME_ROOT / "src").resolve())}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--strict",
            "--python-version=3.12",
            "--ignore-missing-imports",
            str(fixture_path),
        ],
        capture_output=True,
        text=True,
        cwd=_RUNTIME_ROOT,
        env=env,
    )
    assert result.returncode != 0, (
        f"mypy --strict UNEXPECTEDLY PASSED on {fixture_name} — "
        f"type-level asymmetry enforcement is broken. stdout: {result.stdout}"
    )
    combined = result.stdout + result.stderr
    assert re.search(expected_error_regex, combined), (
        f"mypy error did not match expected regex.\n"
        f"Expected: {expected_error_regex!r}\n"
        f"Got: {combined}"
    )
