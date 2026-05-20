"""
F-1.H1 import smoke tests.
Verifies that Pi-Mono public API is importable and that runtime/memory layers
maintain clean separation (no cross-layer internal imports).
"""

from pathlib import Path

import pytest

pytestmark = [pytest.mark.f1_absorption, pytest.mark.static]

# ---------------------------------------------------------------------------
# Root of the source tree (src/ layout)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parents[4]  # …/praxis/runtime
_SRC_ROOT = _REPO_ROOT / "src"


# ---------------------------------------------------------------------------
# Import smoke tests
# ---------------------------------------------------------------------------


def test_cost_repository_importable_from_pi_mono():
    """CostRepository must be importable from the public cost.storage surface."""
    from praxis.kernel.cost.storage.repository import CostRepository  # noqa: F401


def test_event_row_importable_from_pi_mono():
    """EventRow must be importable from the public cost.storage.schema surface."""
    from praxis.kernel.cost.storage.schema import EventRow  # noqa: F401


def test_event_row_has_event_id_pk():
    """EventRow's primary key must be the 'event_id' column."""
    from praxis.kernel.cost.storage.schema import EventRow

    pk_columns = list(EventRow.__table__.primary_key.columns.keys())
    assert pk_columns == ["event_id"], f"Expected primary key ['event_id'], got {pk_columns}"


# ---------------------------------------------------------------------------
# Negative dependency tests (static grep)
# ---------------------------------------------------------------------------


def test_runtime_has_no_pi_mono_internal_imports():
    """
    No file under src/praxis/kernel/runtime/ must import from
    praxis.kernel.cost._internal (the private Pi-Mono namespace).
    """
    runtime_src = _SRC_ROOT / "praxis" / "kernel" / "runtime"
    matches = _find_python_files_containing(runtime_src, "praxis.kernel.cost._internal")
    assert matches == [], (
        "Found forbidden praxis.kernel.cost._internal imports in runtime/:\n"
        + "\n".join(matches)
    )


def test_memory_src_has_no_cost_imports():
    """
    Stage 3 canary: no file under src/praxis/kernel/memory/ must import from
    praxis.kernel.cost (the cost layer must not bleed into the memory layer).
    """
    memory_src = _SRC_ROOT / "praxis" / "kernel" / "memory"
    matches = _find_python_files_containing(memory_src, "praxis.kernel.cost")
    assert matches == [], (
        "Found forbidden praxis.kernel.cost imports in memory/:\n" + "\n".join(matches)
    )


def _find_python_files_containing(root: Path, needle: str) -> list[str]:
    matches: list[str] = []
    if not root.exists():
        return matches
    for path in root.rglob("*.py"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if needle in line:
                matches.append(f"{path}:{line_number}:{line}")
    return matches
